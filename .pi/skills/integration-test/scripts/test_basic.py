#!/usr/bin/env python3
"""Test 1: Basic transcription - speak "git status"."""

import time

def main():
    print("Test 1: Basic Transcription")
    print("-" * 40)
    print()
    print("Instructions:")
    print("1. Focus WezTerm or another text field")
    print("2. Press Opt+Cmd+Space to start recording")
    print("3. Say: 'git status'")
    print("4. Press Opt+Cmd+Space to stop")
    print()
    print("Expected: 'git status' appears in ~1-2 seconds")
    print()
    print("Press Enter when ready to start timing test...")
    input()
    
    print("\nRecording for 3 seconds...")
    print("Say 'git status' now!")
    time.sleep(3)
    
    print("\nStop recording now (Opt+Cmd+Space)")
    print()
    print("Verify: 'git status' appeared in target app")
    print("Timing: Should be < 1.5s for first partial")

if __name__ == "__main__":
    main()
