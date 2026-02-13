"""Espin GUI - floating recording window with frosted glass UI."""

import os
import subprocess
import sys
import threading
import time
from typing import Optional

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
_PARENT = os.path.dirname(_SCRIPT_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from objc import super as objc_super

from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSTextField,
    NSMenu,
    NSMenuItem,
    NSAlert,
    NSPanel,
    NSFloatingWindowLevel,
    NSBorderlessWindowMask,
    NSBackingStoreBuffered,
    NSMakeRect,
    NSMakePoint,
    NSView,
    NSRectFill,
    NSBezierPath,
    NSGradient,
    NSButtLineCapStyle,
    NSRoundLineJoinStyle,
    NSFont,
    NSColor,
    NSVisualEffectView,
    NSViewWidthSizable,
    NSViewHeightSizable,
)
from Foundation import NSObject, NSTimer

from espin.state import EspinState
from espin.hotkey import HotkeyListener
from espin.audio import AudioRecorder
from espin.asr import ASREngine
from espin.injector import Injector

MAX_RECORDING_SECONDS = 30
SOUND_START = "/System/Library/Sounds/Ping.aiff"
SOUND_STOP = "/System/Library/Sounds/Pop.aiff"
MIN_TRANSCRIBE_SECONDS = 0.65

# Common short-clip Whisper hallucinations we never want to inject.
HALLUCINATION_GUARDRAILS = {
    "thanks for watching",
    "thank you for watching",
    "thanks for listening",
    "thank you for listening",
}

WINDOW_W = 276
WINDOW_H = 44
MARGIN = 12
CORNER_RADIUS = 23
WAVEFORM_POINTS = 40
LEVEL_BAR_HISTORY_MAX = WAVEFORM_POINTS

METER_DISPLAY_GAIN = 6.0
METER_SMOOTH_SAMPLES = 5

# NSVisualEffectView constants
VE_STATE_ACTIVE = 1
VE_MATERIAL_HUD = 13
VE_BLEND_BEHIND = 0


def _play_sound(path: str) -> None:
    if os.path.exists(path):
        subprocess.Popen(
            ["afplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


class EspinAppDelegate(NSObject):

    def init(self):
        self = objc_super(EspinAppDelegate, self).init()
        if self is None:
            return None
        self._current_level = 0.0
        self._rms_history = []
        self._rms_lock = threading.Lock()
        self._level_bar_history = []
        self._recording_start_time = None
        self._label = None
        self._dot_view = None
        self._bar_view = None
        self._window = None
        self._timer = None
        self._tick_count = 0
        self._hotkey_watchdog_counter = 0

        self.state = EspinState()
        self.audio = AudioRecorder(on_level=self._on_audio_level)
        self.asr = ASREngine()
        self.asr.ensure_model()
        print("[ASR] Loading model into memory…", file=sys.stderr)
        self.asr._load_model()
        print("[ESPIN] Ready — press Ctrl+Option+Space to start recording.", file=sys.stderr)
        self.injector = Injector()
        self.hotkey = HotkeyListener(on_toggle=self._on_hotkey_toggle)
        return self

    def _on_audio_level(self, rms):
        self._current_level = rms
        with self._rms_lock:
            self._rms_history.append(rms)
            if len(self._rms_history) > METER_SMOOTH_SAMPLES:
                self._rms_history.pop(0)

    def _on_hotkey_toggle(self):
        print(f"[HOTKEY] Toggle pressed, state={'idle' if self.state.is_idle else 'recording'}", file=sys.stderr)
        if self.state.is_idle:
            self._start_recording()
        else:
            # Ignore stop if recording started less than 1s ago (keyboard bounce guard)
            if self._recording_start_time and (time.time() - self._recording_start_time) < 1.0:
                print("[HOTKEY] Ignoring stop — too soon after start (bounce?)", file=sys.stderr)
                return
            threading.Thread(target=self._stop_recording, daemon=True).start()

    def _start_recording(self):
        print("[REC] Starting recording...", file=sys.stderr)
        if not self.state.start_recording():
            print("[REC] State transition failed", file=sys.stderr)
            return
        if not self.audio.start():
            print("[REC] Audio start failed", file=sys.stderr)
            self.state.cancel()
            return
        print("[REC] Recording started", file=sys.stderr)
        self._recording_start_time = time.time()
        self._level_bar_history = []
        self._tick_count = 0
        _play_sound(SOUND_START)
        self.performSelectorOnMainThread_withObject_waitUntilDone_("showWindow:", None, False)
        self.performSelectorOnMainThread_withObject_waitUntilDone_("refreshUI:", None, False)

    def showWindow_(self, sender):
        if self._window is not None:
            self._window.orderFrontRegardless()

    def refreshUI_(self, sender):
        self._update_ui()

    def _stop_recording(self):
        if self.state.is_idle:
            return
        self.audio.stop()
        _play_sound(SOUND_STOP)
        audio_len = self.audio.audio_length
        audio = self.audio.get_recent_audio(audio_len)
        print(f"[REC] Stopped. Audio: {len(audio)/16000:.2f}s ({len(audio)} samples)", file=sys.stderr)
        if audio_len < MIN_TRANSCRIBE_SECONDS or len(audio) < 1600:
            print(f"[REC] Too short ({audio_len:.2f}s), skipping ASR", file=sys.stderr)
            self.state.stop()
            self._hide_window()
            return
        try:
            print("[ASR] Transcribing...", file=sys.stderr)
            hypothesis = self.asr.transcribe(audio)
            print(f"[ASR] Result: '{hypothesis}'", file=sys.stderr)
        except Exception as e:
            print(f"[ASR] Error: {e}", file=sys.stderr)
            hypothesis = ""
        self.state.stop()
        cleaned = hypothesis.strip()
        lowered = cleaned.lower().rstrip(".!? ")
        if cleaned and lowered in HALLUCINATION_GUARDRAILS and audio_len < 2.0:
            print(f"[ASR] Dropping likely hallucination: '{cleaned}'", file=sys.stderr)
            cleaned = ""

        if cleaned:
            self.injector.type_text(cleaned)
        else:
            print("[ASR] Empty result, nothing to inject", file=sys.stderr)
        self._hide_window()

    def _format_time(self, seconds):
        return f"{int(seconds // 60)}:{int(seconds % 60):02d}"

    def _meter_rms(self):
        with self._rms_lock:
            snap = list(self._rms_history)
        if not snap:
            return min(self._current_level * METER_DISPLAY_GAIN, 1.0)
        smoothed = sum(snap) / len(snap)
        return min(smoothed * METER_DISPLAY_GAIN, 1.0)

    def _hide_window(self):
        if self._window is None:
            return
        self._window.performSelectorOnMainThread_withObject_waitUntilDone_("orderOut:", None, False)

    def _update_ui(self):
        self._tick_count += 1
        self._hotkey_watchdog_counter += 1

        # Every ~4 seconds, make sure the hotkey listener is still alive.
        if self._hotkey_watchdog_counter >= 20:
            self._hotkey_watchdog_counter = 0
            if not self.hotkey.is_healthy():
                print("[HOTKEY] Listener not healthy; restarting...", file=sys.stderr)
                try:
                    self.hotkey.stop()
                except Exception:
                    pass
                self.hotkey.start()

        if not self.state.is_recording:
            return

        elapsed = (
            time.time() - self._recording_start_time
            if self._recording_start_time
            else 0
        )
        if elapsed >= MAX_RECORDING_SECONDS:
            threading.Thread(target=self._stop_recording, daemon=True).start()
        if self._label is not None:
            self._label.setStringValue_(self._format_time(elapsed))

        # Pulse the recording dot (toggle every 3 ticks ≈ 0.6s)
        if self._dot_view is not None:
            visible = (self._tick_count // 3) % 2 == 0
            self._dot_view.setAlphaValue_(1.0 if visible else 0.3)

        level = self._meter_rms()
        self._level_bar_history.append(level)
        if len(self._level_bar_history) > LEVEL_BAR_HISTORY_MAX:
            self._level_bar_history.pop(0)
        if self._bar_view is not None:
            self._bar_view.setLevels_(list(self._level_bar_history))
            self._bar_view.setNeedsDisplay_(True)
            self._bar_view.displayIfNeeded()

    def applicationDidFinishLaunching_(self, notification):
        from AppKit import NSScreen

        frame = NSScreen.mainScreen().visibleFrame()
        x = frame.origin.x + (frame.size.width - WINDOW_W) * 0.5
        y = frame.origin.y + frame.size.height - WINDOW_H - MARGIN
        window_frame = NSMakeRect(x, y, WINDOW_W, WINDOW_H)

        self._window = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            window_frame,
            NSBorderlessWindowMask,
            NSBackingStoreBuffered,
            False,
        )
        self._window.setLevel_(NSFloatingWindowLevel)
        self._window.setOpaque_(False)
        self._window.setBackgroundColor_(NSColor.clearColor())
        self._window.setTitle_("Espin")
        self._window.setFloatingPanel_(True)
        self._window.setHasShadow_(True)
        self._window.setHidesOnDeactivate_(False)
        self._window.setDelegate_(self)

        content_rect = NSMakeRect(0, 0, WINDOW_W, WINDOW_H)

        # Right-click handler as content view (transparent)
        content = RightClickView.alloc().initWithFrame_(content_rect)
        content.setWantsLayer_(True)
        content.layer().setCornerRadius_(CORNER_RADIUS)
        content.layer().setMasksToBounds_(True)

        # Frosted glass background (NSVisualEffectView with HUD material)
        vibrancy = NSVisualEffectView.alloc().initWithFrame_(content_rect)
        vibrancy.setMaterial_(VE_MATERIAL_HUD)
        vibrancy.setState_(VE_STATE_ACTIVE)
        vibrancy.setBlendingMode_(VE_BLEND_BEHIND)
        vibrancy.setWantsLayer_(True)
        vibrancy.layer().setCornerRadius_(CORNER_RADIUS)
        vibrancy.layer().setMasksToBounds_(True)
        vibrancy.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        content.addSubview_(vibrancy)

        # Dark tint overlay to keep the palette cohesive and less "milky gray"
        tint = GlassTintView.alloc().initWithFrame_(content_rect)
        tint.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        content.addSubview_(tint)

        # --- Layout: [dot] [timer] [waveform] ---
        pad_l = 16
        pad_r = 14

        # Pulsing red recording dot
        dot_size = 10
        dot_y = (WINDOW_H - dot_size) / 2.0
        self._dot_view = RecordingDotView.alloc().initWithFrame_(
            NSMakeRect(pad_l, dot_y, dot_size, dot_size)
        )
        content.addSubview_(self._dot_view)

        # Timer label
        timer_x = pad_l + dot_size + 8
        timer_w = 40
        label_h = 18
        label_y = (WINDOW_H - label_h) / 2.0
        self._label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(timer_x, label_y, timer_w, label_h)
        )
        self._label.setEditable_(False)
        self._label.setSelectable_(False)
        self._label.setBezeled_(False)
        self._label.setDrawsBackground_(False)
        self._label.setFont_(NSFont.monospacedDigitSystemFontOfSize_weight_(13, 0.4))
        self._label.setTextColor_(NSColor.colorWithCalibratedWhite_alpha_(0.94, 0.95))
        self._label.setStringValue_("0:00")
        content.addSubview_(self._label)

        # Waveform
        wave_x = timer_x + timer_w + 6
        wave_pad_y = 8
        wave_rect = NSMakeRect(
            wave_x, wave_pad_y,
            WINDOW_W - wave_x - pad_r,
            WINDOW_H - 2 * wave_pad_y,
        )
        self._bar_view = LevelWaveformView.alloc().initWithFrame_(wave_rect)
        self._bar_view.setOpaque_(False)
        content.addSubview_(self._bar_view)

        self._window.setContentView_(content)
        self._window.orderOut_(None)

        self._timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.2, self, "timerTick:", None, True
        )
        self.hotkey.start()

    def timerTick_(self, sender):
        self._update_ui()

    def applicationWillTerminate_(self, notification):
        if self._timer is not None:
            self._timer.invalidate()
        self.hotkey.stop()
        if self.audio.is_recording:
            self.audio.stop()

    def showContextMenu(self):
        menu = NSMenu.alloc().init()
        toggle = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Toggle Recording", "menuToggle:", ""
        )
        toggle.setTarget_(self)
        menu.addItem_(toggle)
        menu.addItem_(NSMenuItem.separatorItem())
        about = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("About Espin", "menuAbout:", "")
        about.setTarget_(self)
        menu.addItem_(about)
        menu.addItem_(NSMenuItem.separatorItem())
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit Espin", "menuQuit:", "q")
        quit_item.setTarget_(self)
        menu.addItem_(quit_item)

        from AppKit import NSEvent
        loc = NSEvent.mouseLocation()
        menu.popUpMenuPositioningItem_atLocation_inView_(None, loc, None)

    def menuToggle_(self, sender):
        self._on_hotkey_toggle()

    def menuAbout_(self, sender):
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Espin")
        alert.setInformativeText_(
            "Local voice-to-text for macOS.\n\n"
            "Ctrl+Option+Space → start/stop recording.\n"
            "Right-click window for menu.\nCtrl+C in terminal to quit."
        )
        alert.addButtonWithTitle_("OK")
        alert.runModal()

    def menuQuit_(self, sender):
        NSApplication.sharedApplication().terminate_(self)


class RecordingDotView(NSView):
    """Pulsing red recording indicator dot."""

    def initWithFrame_(self, frame):
        self = objc_super(RecordingDotView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.setWantsLayer_(True)
        return self

    def drawRect_(self, rect):
        NSColor.clearColor().set()
        NSRectFill(rect)
        b = self.bounds()
        dot_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.37, 0.34, 1.0)

        # Soft glow behind the dot
        glow = NSBezierPath.bezierPathWithOvalInRect_(
            NSMakeRect(b.origin.x - 2, b.origin.y - 2,
                       b.size.width + 4, b.size.height + 4)
        )
        NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.37, 0.34, 0.22).set()
        glow.fill()

        circle = NSBezierPath.bezierPathWithOvalInRect_(b)
        dot_color.set()
        circle.fill()


class LevelWaveformView(NSView):
    """Smooth mirrored waveform with gradient fill and glow stroke."""

    def init(self):
        self = objc_super(LevelWaveformView, self).init()
        if self is None:
            return None
        self._levels = []
        return self

    def initWithFrame_(self, frame):
        self = objc_super(LevelWaveformView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._levels = []
        return self

    def setLevels_(self, levels):
        self._levels = list(levels) if levels else []

    def drawRect_(self, rect):
        bounds = self.bounds()
        w = bounds.size.width
        h = bounds.size.height
        mid_y = h * 0.5
        margin = 2.0

        NSColor.clearColor().set()
        NSRectFill(rect)

        levels = self._levels
        n = len(levels)
        if n < 2:
            # Idle: thin horizontal center line
            idle_path = NSBezierPath.bezierPath()
            idle_path.moveToPoint_(NSMakePoint(margin, mid_y))
            idle_path.lineToPoint_(NSMakePoint(w - margin, mid_y))
            idle_path.setLineWidth_(1.0)
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.48, 0.66, 0.9, 0.24).set()
            idle_path.stroke()
            return

        draw_w = w - 2 * margin
        amplitude = (h - 4) * 0.5

        # Build mirrored points: waveform goes up and down from center
        points_top = []
        points_bot = []
        for i in range(n):
            x = margin + (i / (n - 1)) * draw_w
            lvl = min(1.0, max(0.0, levels[i]))
            dy = lvl * amplitude
            points_top.append((x, mid_y + dy))
            points_bot.append((x, mid_y - dy))

        def _catmull_rom(path, pts, i):
            p0 = pts[i - 1] if i > 0 else pts[0]
            p1 = pts[i]
            p2 = pts[i + 1]
            p3 = pts[i + 2] if i + 2 < len(pts) else pts[i + 1]
            t = 6.0
            path.curveToPoint_controlPoint1_controlPoint2_(
                NSMakePoint(p2[0], p2[1]),
                NSMakePoint(p1[0] + (p2[0] - p0[0]) / t, p1[1] + (p2[1] - p0[1]) / t),
                NSMakePoint(p2[0] - (p3[0] - p1[0]) / t, p2[1] - (p3[1] - p1[1]) / t),
            )

        # Top half path (left → right)
        top_path = NSBezierPath.bezierPath()
        top_path.moveToPoint_(NSMakePoint(points_top[0][0], points_top[0][1]))
        for i in range(n - 1):
            _catmull_rom(top_path, points_top, i)

        # Bottom half path (right → left, mirrored)
        bot_path = NSBezierPath.bezierPath()
        bot_path.moveToPoint_(NSMakePoint(points_bot[-1][0], points_bot[-1][1]))
        points_bot_rev = list(reversed(points_bot))
        for i in range(n - 1):
            _catmull_rom(bot_path, points_bot_rev, i)

        # Combined fill path: top left→right, line to bottom-right, bottom right→left, close
        fill_path = NSBezierPath.bezierPath()
        fill_path.moveToPoint_(NSMakePoint(points_top[0][0], points_top[0][1]))
        for i in range(n - 1):
            _catmull_rom(fill_path, points_top, i)
        fill_path.lineToPoint_(NSMakePoint(points_bot[-1][0], points_bot[-1][1]))
        for i in range(n - 1):
            _catmull_rom(fill_path, points_bot_rev, i)
        fill_path.closePath()

        # Gradient fill: muted midnight blue palette
        c1 = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.10, 0.16, 0.30, 0.62)
        c2 = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.19, 0.36, 0.63, 0.70)
        c3 = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.34, 0.58, 0.80, 0.74)
        gradient = NSGradient.alloc().initWithColors_([c1, c2, c3])
        gradient.drawInBezierPath_angle_(fill_path, 90.0)

        # Glow stroke (wider, translucent)
        for stroke_path_pts in (points_top, list(reversed(points_bot))):
            glow_path = NSBezierPath.bezierPath()
            glow_path.moveToPoint_(NSMakePoint(stroke_path_pts[0][0], stroke_path_pts[0][1]))
            for i in range(len(stroke_path_pts) - 1):
                _catmull_rom(glow_path, stroke_path_pts, i)
            glow_path.setLineWidth_(2.6)
            glow_path.setLineCapStyle_(NSButtLineCapStyle)
            glow_path.setLineJoinStyle_(NSRoundLineJoinStyle)
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.42, 0.66, 0.9, 0.19).set()
            glow_path.stroke()

        # Crisp stroke on top
        for stroke_path_pts in (points_top, list(reversed(points_bot))):
            line = NSBezierPath.bezierPath()
            line.moveToPoint_(NSMakePoint(stroke_path_pts[0][0], stroke_path_pts[0][1]))
            for i in range(len(stroke_path_pts) - 1):
                _catmull_rom(line, stroke_path_pts, i)
            line.setLineWidth_(1.2)
            line.setLineCapStyle_(NSButtLineCapStyle)
            line.setLineJoinStyle_(NSRoundLineJoinStyle)
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.58, 0.78, 0.94, 0.78).set()
            line.stroke()


class GlassTintView(NSView):
    """Dark tint layer over vibrancy for a cohesive premium look."""

    def drawRect_(self, rect):
        NSColor.clearColor().set()
        NSRectFill(rect)
        b = self.bounds()

        # Base dark glass tint
        bg = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            b, CORNER_RADIUS, CORNER_RADIUS
        )
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.06, 0.09, 0.15, 0.52).set()
        bg.fill()

        # Subtle top highlight gradient for depth
        top_band = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            b, CORNER_RADIUS, CORNER_RADIUS
        )
        grad = NSGradient.alloc().initWithStartingColor_endingColor_(
            NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.10),
            NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.01),
        )
        grad.drawInBezierPath_angle_(top_band, 90.0)

        # Hairline border to define panel edges cleanly
        inset = NSMakeRect(0.5, 0.5, b.size.width - 1.0, b.size.height - 1.0)
        border = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            inset, CORNER_RADIUS - 0.5, CORNER_RADIUS - 0.5
        )
        border.setLineWidth_(1.0)
        NSColor.colorWithCalibratedWhite_alpha_(0.92, 0.14).set()
        border.stroke()


class RightClickView(NSView):
    """Transparent content view that handles right-click for context menu."""

    def drawRect_(self, rect):
        pass  # NSVisualEffectView handles background

    def rightMouseDown_(self, event):
        w = self.window()
        if w is not None:
            d = w.delegate()
            if d is not None and hasattr(d, "showContextMenu"):
                d.showContextMenu()


def main():
    from PyObjCTools import AppHelper

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    delegate = EspinAppDelegate.alloc().init()
    app.setDelegate_(delegate)

    AppHelper.installMachInterrupt()
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
