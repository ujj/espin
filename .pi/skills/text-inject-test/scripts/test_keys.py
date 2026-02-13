#!/usr/bin/env python3
"""Test various key codes."""

import sys
import time
from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap

KEY_CODES = {
    'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5, 'h': 4,
    'i': 34, 'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45, 'o': 31, 'p': 35,
    'q': 12, 'r': 15, 's': 1, 't': 17, 'u': 32, 'v': 9, 'w': 13, 'x': 7,
    'y': 16, 'z': 6,
    '0': 29, '1': 18, '2': 19, '3': 20, '4': 21, '5': 23, '6': 22, '7': 26,
    '8': 28, '9': 25,
    'space': 49, 'return': 36, 'tab': 48, 'delete': 51, 'escape': 53,
    'left': 123, 'right': 124, 'down': 125, 'up': 126,
}

def press_key(key_code):
    """Press and release a key."""
    down = CGEventCreateKeyboardEvent(None, key_code, True)
    up = CGEventCreateKeyboardEvent(None, key_code, False)
    CGEventPost(kCGHIDEventTap, down)
    time.sleep(0.01)
    CGEventPost(kCGHIDEventTap, up)
    time.sleep(0.05)

def main():
    print("Key Test")
    print("=" * 40)
    print("Focus a text field, then press Enter to start...")
    input()
    
    tests = [
        ('letters', ['a', 'b', 'c', 'x', 'y', 'z']),
        ('numbers', ['0', '1', '2', '3', '4', '5']),
        ('space/return', ['space', 'return']),
    ]
    
    for name, keys in tests:
        print(f"\nTesting {name}...")
        for key in keys:
            code = KEY_CODES.get(key)
            if code:
                press_key(code)
                time.sleep(0.1)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
