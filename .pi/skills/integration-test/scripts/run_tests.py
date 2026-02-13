#!/usr/bin/env python3
"""Integration tests for espin - runs Test 1, 2, 3 from spec."""

import subprocess
import sys

TESTS = [
    ("Basic Transcription", "test_basic.py"),
    ("File Command", "test_file_cmd.py"),
    ("Streaming Behavior", "test_streaming.py"),
]

def main():
    print("Espin Integration Tests")
    print("=" * 50)
    print()
    print("These tests require manual verification:")
    print("- Speak into microphone")
    print("- Verify text appears in target app")
    print()
    print("Press Enter to start each test, or Ctrl+C to quit")
    print()
    
    for name, script in TESTS:
        print(f"\n{'='*50}")
        print(f"Test: {name}")
        print("=" * 50)
        input("Press Enter to run...")
        
        result = subprocess.run(
            [sys.executable, f".pi/skills/integration-test/scripts/{script}"],
            cwd="."
        )
        
        if result.returncode != 0:
            print(f"\n✗ Test failed with code {result.returncode}")
            response = input("Continue to next test? [y/N] ")
            if response.lower() != 'y':
                break
        else:
            print("\n✓ Test script completed")
            print("Verify the output manually!")
    
    print("\n" + "=" * 50)
    print("All tests complete!")
    print("Please verify results in your target application.")

if __name__ == "__main__":
    main()
