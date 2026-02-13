#!/usr/bin/env python3
"""Test streaming text injection - character by character."""

import sys
import time
from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap

KEY_CODES = {
    'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5, 'h': 4,
    'i': 34, 'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45, 'o': 31, 'p': 35,
    'q': 12, 'r': 15, 's': 1, 't': 17, 'u': 32, 'v': 9, 'w': 13, 'x': 7,
    'y': 16, 'z': 6,
    '0': 29, '1': 18, '2': 19, '3': 20, '4': 21, '5': 23, '6': 22, '7': 26,
    '8': 28, '9': 25, ' ': 49,
}

def type_char(c):
    """Type a single character."""
    code = KEY_CODES.get(c.lower())
    if code is not None:
        down = CGEventCreateKeyboardEvent(None, code, True)
        up = CGEventCreateKeyboardEvent(None, code, False)
        CGEventPost(kCGHIDEventTap, down)
        time.sleep(0.005)
        CGEventPost(kCGHIDEventTap, up)

def main():
    text = "streaming text injection test"
    
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    
    print(f"Streaming: '{text}'")
    print("Focus a text field, press Enter to start...")
    input()
    
    for i, c in enumerate(text):
        type_char(c)
        # Small delay to simulate word-by-word appearance
        if c == ' ':
            time.sleep(0.05)
        else:
            time.sleep(0.03)
        
        # Progress indicator
        print(f"\rTyped: {text[:i+1]}", end='', flush=True)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
