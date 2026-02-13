#!/usr/bin/env python3
"""Test CGEvent key injection - inject basic text."""

import sys
import time
from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap

# Key code mapping for US keyboard
KEY_CODES = {
    'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5, 'h': 4,
    'i': 34, 'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45, 'o': 31, 'p': 35,
    'q': 12, 'r': 15, 's': 1, 't': 17, 'u': 32, 'v': 9, 'w': 13, 'x': 7,
    'y': 16, 'z': 6,
    '0': 29, '1': 18, '2': 19, '3': 20, '4': 21, '5': 23, '6': 22, '7': 26,
    '8': 28, '9': 25,
    ' ': 49,  # Space
    '\n': 36,  # Return
    '\t': 48,  # Tab
}

def type_key(key_code, flags=0):
    """Press and release a key."""
    down = CGEventCreateKeyboardEvent(None, key_code, True)
    up = CGEventCreateKeyboardEvent(None, key_code, False)
    
    if flags:
        CGEventSetFlags(down, flags)
        CGEventSetFlags(up, flags)
    
    CGEventPost(kCGHIDEventTap, down)
    time.sleep(0.01)
    CGEventPost(kCGHIDEventTap, up)
    time.sleep(0.02)

def type_char(c):
    """Type a single character."""
    if c.lower() in KEY_CODES:
        type_key(KEY_CODES[c.lower()])
    else:
        # For other chars, try shifted keys
        if c.isupper():
            type_key(KEY_CODES.get(c.lower(), 0), 0x100 | 0x200)  # Shift
        else:
            print(f"Unknown char: {c}")

def type_string(s):
    """Type a string."""
    for c in s:
        if c == ' ':
            type_key(KEY_CODES[' '])
        elif c == '\n':
            type_key(KEY_CODES['\n'])
        elif c == '\t':
            type_key(KEY_CODES['\t'])
        elif c.isalpha():
            type_char(c)
        elif c.isdigit():
            type_key(KEY_CODES[c])
        else:
            print(f"Skipping: {c}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_inject.py <text>")
        print("Focus a text field first!")
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    
    print(f"Typing: {text}")
    print("Press Ctrl+C to cancel, or wait 3 seconds...")
    
    time.sleep(3)
    
    type_string(text)
    
    print("Done!")

if __name__ == "__main__":
    main()
