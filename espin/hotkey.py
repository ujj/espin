"""Global hotkey listener for espin."""

import sys
import time
from typing import Callable, Optional

from pynput import keyboard


class HotkeyListener:
    """
    Global hotkey listener using pynput.

    Hotkey:
    - Ctrl+Option+Space: Toggle recording (start/stop)
    """

    def __init__(
        self,
        on_toggle: Callable[[], None]
    ):
        self.on_toggle = on_toggle
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        self._modifier_state = set()
        self._last_toggle_time = 0
        self._toggle_cooldown = 0.7  # Prevent double-trigger from key repeat
        self._combo_armed = True

    @staticmethod
    def _is_ctrl(key) -> bool:
        from pynput.keyboard import Key
        return key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r)

    @staticmethod
    def _is_alt(key) -> bool:
        from pynput.keyboard import Key
        return key in (Key.alt, Key.alt_l, Key.alt_r)
    
    def _on_press(self, key):
        """Handle key press."""
        from pynput.keyboard import Key

        # Track ctrl and alt (left/right variants included)
        if self._is_ctrl(key):
            self._modifier_state.add("ctrl")
        elif self._is_alt(key):
            self._modifier_state.add("alt")

        # Toggle: Ctrl+Option+Space
        if self._modifier_state == {"ctrl", "alt"} and key == Key.space:
            now = time.time()
            if (not self._combo_armed) or (now - self._last_toggle_time < self._toggle_cooldown):
                return True

            self._last_toggle_time = now
            self._combo_armed = False
            try:
                self.on_toggle()
            except Exception as e:
                print(f"[HOTKEY] Toggle callback failed: {e}", file=sys.stderr)
            return True

        return True
    
    def _on_release(self, key):
        """Handle key release."""
        if self._is_ctrl(key):
            self._modifier_state.discard("ctrl")
        elif self._is_alt(key):
            self._modifier_state.discard("alt")

        # Re-arm only when combo is no longer held
        if self._modifier_state != {"ctrl", "alt"}:
            self._combo_armed = True
        return True
    
    def start(self):
        """Start listening for hotkeys."""
        if self._running and self.is_healthy():
            return

        self._running = True
        self._modifier_state = set()
        self._combo_armed = True
        self._last_toggle_time = 0
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False
        )
        self._listener.start()
    
    def is_healthy(self) -> bool:
        """Whether listener thread is alive."""
        return bool(self._listener and self._listener.is_alive())

    def stop(self):
        """Stop listening for hotkeys."""
        if not self._running:
            return
        
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
