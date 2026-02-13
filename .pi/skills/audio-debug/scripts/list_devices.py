#!/usr/bin/env python3
"""List available audio input devices."""

import sounddevice as sd

def main():
    print("Available audio devices:\n")
    print(sd.query_devices())
    print("\nDefault input device:")
    print(sd.query_devices(kind='input'))

if __name__ == "__main__":
    main()
