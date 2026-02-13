"""Espin GUI - floating window (no menu bar)."""

import os
import subprocess
import sys
import threading
import time
from typing import Optional

# Ensure project root is on path
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

# Window: top-center, pill style. Only visible while recording. Compact size, chart gets most space.
WINDOW_W = 240
WINDOW_H = 40
MARGIN = 12
PILL_CORNER_RADIUS = 20  # half of height for capsule shape
WAVEFORM_POINTS = 32  # smooth waveform (level history)
LEVEL_BAR_HISTORY_MAX = WAVEFORM_POINTS

# Make level meter more pronounced: typical speech RMS is small, so scale up for display
METER_DISPLAY_GAIN = 6.0
METER_SMOOTH_SAMPLES = 5


def _play_sound(path: str) -> None:
    if os.path.exists(path):
        subprocess.Popen(
            ["afplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


class EspinAppDelegate(NSObject):
    """Application delegate: owns the floating window and espin logic."""

    def init(self):
        self = objc_super(EspinAppDelegate, self).init()
        if self is None:
            return None
        self._current_level = 0.0
        self._rms_history = []  # for smoothing the meter (audio thread writes, main reads)
        self._rms_lock = threading.Lock()
        self._level_bar_history = []  # for voice bar chart (last N levels, 0-1)
        self._recording_start_time = None
        self._label = None
        self._bar_view = None
        self._window = None
        self._timer = None

        self.state = EspinState()
        self.audio = AudioRecorder(on_level=self._on_audio_level)
        self.asr = ASREngine()
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
        if self.state.is_idle:
            self._start_recording()
        else:
            threading.Thread(target=self._stop_recording, daemon=True).start()

    def _start_recording(self):
        if not self.state.start_recording():
            return
        if not self.audio.start():
            self.state.cancel()
            return
        self._recording_start_time = time.time()
        self._level_bar_history = []
        _play_sound(SOUND_START)
        # Hotkey runs on a background thread; AppKit UI must run on main thread
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
        audio = self.audio.get_recent_audio(self.audio.audio_length)
        if len(audio) < 1600:
            self.state.stop()
            self._hide_window()
            return
        try:
            hypothesis = self.asr.transcribe(audio)
        except Exception:
            hypothesis = ""
        self.state.stop()
        if hypothesis:
            self.injector.type_text(hypothesis)
        self._hide_window()

    def _format_time(self, seconds):
        return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

    def _meter_rms(self):
        """Smoothed RMS with display gain so normal speech moves the bars clearly."""
        with self._rms_lock:
            snap = list(self._rms_history)
        if not snap:
            # Fallback: use latest sample (audio thread may not have filled history yet)
            return min(self._current_level * METER_DISPLAY_GAIN, 1.0)
        smoothed = sum(snap) / len(snap)
        return min(smoothed * METER_DISPLAY_GAIN, 1.0)

    def _hide_window(self):
        if self._window is None:
            return
        # orderOut must run on main thread (stop_recording can be called from hotkey thread)
        self._window.performSelectorOnMainThread_withObject_waitUntilDone_("orderOut:", None, False)

    def _update_ui(self):
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
            self._label.setStringValue_(f"REC {self._format_time(elapsed)}")
        # Feed waveform: append current level, trim to history size
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
        # Floating window: top-center of main screen
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
        self._window.setBackgroundColor_(__import__("AppKit").NSColor.clearColor())
        self._window.setTitle_("Espin")
        self._window.setFloatingPanel_(True)
        self._window.setHasShadow_(True)
        self._window.setHidesOnDeactivate_(False)
        self._window.setDelegate_(self)

        NSColor = __import__("AppKit").NSColor
        NSFont = __import__("AppKit").NSFont
        # Content: pill-shaped container (rounded rect), time label + bar chart
        content_rect = NSMakeRect(0, 0, WINDOW_W, WINDOW_H)
        right_click_view = RightClickView.alloc().initWithFrame_(content_rect)
        right_click_view.setWantsLayer_(True)
        right_click_view.layer().setCornerRadius_(PILL_CORNER_RADIUS)
        right_click_view.layer().setMasksToBounds_(True)
        right_click_view._pillBgColor = NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.72)

        time_w = 52
        pad = 10
        label_h = 20
        label_y = (WINDOW_H - label_h) * 0.5
        self._label = NSTextField.alloc().initWithFrame_(NSMakeRect(pad, label_y, time_w, label_h))
        self._label.setEditable_(False)
        self._label.setSelectable_(False)
        self._label.setBezeled_(False)
        self._label.setDrawsBackground_(False)
        self._label.setFont_(NSFont.monospacedDigitSystemFontOfSize_weight_(12, 0.5))
        self._label.setTextColor_(NSColor.whiteColor())
        self._label.setAlignment_(1)  # NSCenterTextAlignment
        self._label.setStringValue_("REC 0:00")
        right_click_view.addSubview_(self._label)
        chart_left = pad + time_w + 8
        chart_top_bottom = 6
        bar_rect = NSMakeRect(chart_left, chart_top_bottom, WINDOW_W - chart_left - pad, WINDOW_H - 2 * chart_top_bottom)
        self._bar_view = LevelWaveformView.alloc().initWithFrame_(bar_rect)
        self._bar_view.setOpaque_(False)
        right_click_view.addSubview_(self._bar_view)
        self._window.setContentView_(right_click_view)

        # Start hidden; window appears when recording starts (hotkey) and hides when recording stops
        self._window.orderOut_(None)

        # Timer to update label every 0.2s (scheduledTimer already adds to current run loop)
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

    # Right-click: show context menu. NSPanel doesn't have a default context menu; we need to handle rightMouseDown.
    # Easiest: use a custom content view that forwards right-click to show menu.
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

        # Show at current mouse location
        from AppKit import NSEvent
        loc = NSEvent.mouseLocation()
        # menu.popUpMenuPositioningItem_atLocation_inView_ expects location in screen coords; mouseLocation is already screen
        from AppKit import NSGraphicsContext
        menu.popUpMenuPositioningItem_atLocation_inView_(None, loc, None)

    def menuToggle_(self, sender):
        self._on_hotkey_toggle()

    def menuAbout_(self, sender):
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Espin")
        alert.setInformativeText_(
            "Local streaming ASR for macOS.\n\n"
            "Press Ctrl+Option+Space to start/stop recording. The floating window appears only while recording.\n"
            "Right-click the window for menu; when not recording, quit with Ctrl+C."
        )
        alert.addButtonWithTitle_("OK")
        alert.runModal()

    def menuQuit_(self, sender):
        NSApplication.sharedApplication().terminate_(self)


class LevelWaveformView(NSView):
    """Smooth waveform from level history: filled gradient + stroked line (audio-app style)."""

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
        NSColor = __import__("AppKit").NSColor
        bounds = self.bounds()
        w = bounds.size.width
        h = bounds.size.height
        margin = 4.0
        # Clear to transparent so only the wave is visible (no brown/gray behind it)
        NSColor.clearColor().set()
        NSRectFill(rect)
        levels = self._levels
        n = len(levels)
        if n < 2:
            return
        draw_w = w - 2 * margin
        draw_h = h - 2 * margin
        points = []
        for i in range(n):
            x = margin + (i / (n - 1)) * draw_w
            lvl = min(1.0, max(0.0, levels[i]))
            y = margin + lvl * draw_h
            points.append((x, y))
        # Smooth curve: cubic Bezier (Catmull-Rom style) through points
        def smooth_segment(path, pts, i):
            """Append cubic Bezier from pts[i] to pts[i+1] with Catmull-Rom control points."""
            p0 = pts[i - 1] if i > 0 else pts[0]
            p1 = pts[i]
            p2 = pts[i + 1]
            p3 = pts[i + 2] if i + 2 < len(pts) else pts[i + 1]
            # Catmull-Rom to Bezier: cp1 = p1 + (p2-p0)/6, cp2 = p2 - (p3-p1)/6
            tension = 6.0
            c1x = p1[0] + (p2[0] - p0[0]) / tension
            c1y = p1[1] + (p2[1] - p0[1]) / tension
            c2x = p2[0] - (p3[0] - p1[0]) / tension
            c2y = p2[1] - (p3[1] - p1[1]) / tension
            path.curveToPoint_controlPoint1_controlPoint2_(
                NSMakePoint(p2[0], p2[1]),
                NSMakePoint(c1x, c1y),
                NSMakePoint(c2x, c2y),
            )
        # Build path: smooth wave left to right, then close along bottom
        path = NSBezierPath.bezierPath()
        path.moveToPoint_(NSMakePoint(points[0][0], points[0][1]))
        for i in range(len(points) - 1):
            smooth_segment(path, points, i)
        bottom_y = margin
        path.lineToPoint_(NSMakePoint(points[-1][0], bottom_y))
        path.lineToPoint_(NSMakePoint(points[0][0], bottom_y))
        path.closePath()
        # Gradient fill: dark blue/teal at bottom -> bright cyan/teal at top
        start_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.15, 0.35, 0.55, 0.85)
        end_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.35, 0.75, 0.95, 0.95)
        gradient = NSGradient.alloc().initWithStartingColor_endingColor_(start_color, end_color)
        gradient.drawInBezierPath_angle_(path, 90.0)
        # Stroke the smooth top edge
        line_path = NSBezierPath.bezierPath()
        line_path.moveToPoint_(NSMakePoint(points[0][0], points[0][1]))
        for i in range(len(points) - 1):
            smooth_segment(line_path, points, i)
        line_path.setLineWidth_(1.8)
        line_path.setLineCapStyle_(NSButtLineCapStyle)
        line_path.setLineJoinStyle_(NSRoundLineJoinStyle)
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.5, 0.88, 1.0, 0.95).set()
        line_path.stroke()


class RightClickView(NSView):
    """Pill-shaped content view; draws rounded rect background, shows context menu on right-click."""

    def drawRect_(self, rect):
        b = self.bounds()
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            b, PILL_CORNER_RADIUS, PILL_CORNER_RADIUS
        )
        color = getattr(self, "_pillBgColor", None)
        if color is None:
            from AppKit import NSColor
            color = NSColor.colorWithCalibratedWhite_alpha_(0.18, 0.95)
        color.set()
        path.fill()

    def rightMouseDown_(self, event):
        # Get delegate from window and show menu
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
