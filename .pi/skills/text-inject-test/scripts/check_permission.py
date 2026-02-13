#!/usr/bin/env python3
"""Check if Accessibility permission is granted."""

import sys

try:
    from Quartz import AXIsProcessTrusted
except ImportError:
    print("Error: pyobjc-framework-Quartz not installed")
    print("Run: uv add pyobjc-framework-Quartz")
    sys.exit(1)

def main():
    trusted = AXIsProcessTrusted()
    
    if trusted:
        print("✓ Accessibility permission: GRANTED")
    else:
        print("✗ Accessibility permission: NOT GRANTED")
        print()
        print("To grant permission:")
        print("  1. Open System Settings → Privacy & Security → Accessibility")
        print("  2. Add your terminal/IDE app")
        print("  3. Restart the app")
        print()
        print("Or run:")
        print('  open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"')

if __name__ == "__main__":
    main()
