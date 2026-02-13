"""CGEvent key injection for espin - fixed version."""

import time
import sys
from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap, CGEventSourceCreate, kCGEventSourceStateHIDSystemState


# US Keyboard key codes - complete mapping
KEY_CODES = {
    # Letters
    'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5, 'h': 4,
    'i': 34, 'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45, 'o': 31, 'p': 35,
    'q': 12, 'r': 15, 's': 1, 't': 17, 'u': 32, 'v': 9, 'w': 13, 'x': 7,
    'y': 16, 'z': 6,
    # Numbers
    '0': 29, '1': 18, '2': 19, '3': 20, '4': 21, '5': 23, '6': 22, '7': 26,
    '8': 28, '9': 25,
    # Punctuation
    ' ': 49,  # Space
    '\n': 36,  # Return
    '\t': 48,  # Tab
    '\b': 51,  # Backspace
    '-': 27, '=': 24, '[': 33, ']': 30, '\\': 42, ';': 41, "'": 39,
    ',': 43, '.': 47, '/': 44, '`': 50,
}

# Shift key modifier flag
SHIFT_FLAG = 0x100


class Injector:
    """Text injector using CGEvent key injection."""
    
    def __init__(self, delay: float = 0.003):
        self.delay = delay
        self._source = CGEventSourceCreate(kCGEventSourceStateHIDSystemState)
    
    def _press_key(self, key_code: int, with_shift: bool = False):
        """Press and release a key."""
        flags = SHIFT_FLAG if with_shift else 0
        
        down = CGEventCreateKeyboardEvent(None, key_code, True)
        up = CGEventCreateKeyboardEvent(None, key_code, False)
        
        if flags:
            from Quartz import CGEventSetFlags
            CGEventSetFlags(down, flags)
            CGEventSetFlags(up, flags)
        
        CGEventPost(kCGHIDEventTap, down)
        time.sleep(self.delay)
        CGEventPost(kCGHIDEventTap, up)
        time.sleep(self.delay)
    
    def type_char(self, c: str):
        """Type a single character."""
        # Handle special characters
        if c == ' ':
            self._press_key(KEY_CODES[' '])
            return
        if c == '\n':
            self._press_key(KEY_CODES['\n'])
            return
        if c == '\t':
            self._press_key(KEY_CODES['\t'])
            return
        if c == '\b':
            self._press_key(KEY_CODES['\b'])
            return
        
        # Get the character to look up
        lookup = c.lower() if c.isalpha() else c
        
        # Look up key code
        key_code = KEY_CODES.get(lookup)
        
        if key_code is None:
            print(f"[INJECTOR] Unknown char: '{c}'", file=sys.stderr)
            return
        
        # Type with shift if uppercase
        self._press_key(key_code, c.isupper())
    
    def type_string(self, text: str):
        """Type a string."""
        for char in text:
            self.type_char(char)
    
    def type_text(self, text: str):
        """Type text."""
        if not text:
            return
        print(f"[INJECTOR] Typing: '{text}'", file=sys.stderr)
        self.type_string(text)
        print(f"[INJECTOR] Done", file=sys.stderr)


if __name__ == "__main__":
    print("Testing Injector...")
    print("Focus a text field and press Enter...")
    input()
    
    injector = Injector(delay=0.003)
    injector.type_text("Hello World! Testing 123.")
    print("Done!")
