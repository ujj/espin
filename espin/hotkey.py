"""Global hotkey listener for espin."""

from typing import Callable, Optional
from pynput import keyboard
import time


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
        self._toggle_cooldown = 0.5  # Prevent double-trigger
    
    def _on_press(self, key):
        """Handle key press."""
        from pynput.keyboard import Key
        
        # Track ctrl and alt
        if key == Key.ctrl:
            self._modifier_state.add('ctrl')
        elif key == Key.alt:
            self._modifier_state.add('alt')
        
        # Toggle: Ctrl+Option+Space
        if self._modifier_state == {'ctrl', 'alt'} and key == Key.space:
            # Check cooldown
            now = time.time()
            if now - self._last_toggle_time < self._toggle_cooldown:
                self._modifier_state.clear()
                return True
            
            self._last_toggle_time = now
            self.on_toggle()
            self._modifier_state.clear()
            return True  # Continue listening
        
        return True
    
    def _on_release(self, key):
        """Handle key release."""
        from pynput.keyboard import Key
        
        if key == Key.ctrl:
            self._modifier_state.discard('ctrl')
        elif key == Key.alt:
            self._modifier_state.discard('alt')
        return True
    
    def start(self):
        """Start listening for hotkeys."""
        if self._running:
            return
        
        self._running = True
        self._modifier_state = set()
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False
        )
        self._listener.start()
    
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
