#!/usr/bin/env python3
"""Check Accessibility permission status."""

import sys

try:
    from ApplicationServices import AXIsProcessTrusted
    from Foundation import NSWorkspace
except ImportError as e:
    print(f"Error: Missing dependency: {e}")
    print("Run: uv add pyobjc-framework-Quartz")
    sys.exit(1)

def main():
    print("Accessibility Permission Check")
    print("=" * 40)
    
    trusted = AXIsProcessTrusted()
    
    if trusted:
        print("✓ GRANTED - Espin can inject keystrokes")
    else:
        print("✗ NOT GRANTED - Espin cannot inject keystrokes")
        print()
        print("To grant:")
        print('  open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"')
        print()
        print("Add your terminal/IDE app, then restart it.")

if __name__ == "__main__":
    main()
