#!/usr/bin/env python3
"""Test 3: Streaming behavior - 10 second sentence."""

import time

def main():
    print("Test 3: Streaming Behavior")
    print("-" * 40)
    print()
    print("Instructions:")
    print("1. Focus WezTerm or another text field")
    print("2. Press Opt+Cmd+Space to start recording")
    print("3. Speak a 10-second sentence, e.g.:")
    print("   'list all the python files in the current directory and show their sizes'")
    print("4. Press Opt+Cmd+Space to stop")
    print()
    print("Verify:")
    print("- Words appear gradually (every ~0.8s)")
    print("- No flicker or rewrites")
    print("- No duplicated words")
    print("- Smooth level meter during recording")
    print()
    print("Press Enter when ready...")
    input()
    
    print("\nRecording for 10 seconds...")
    print("Speak your sentence now!")
    time.sleep(10)
    
    print("\nStop recording now")
    print()
    print("Check for:")
    print("- Gradual word appearance (not all at once)")
    print("- No flickering/clearing")
    print("- No repeated fragments")

if __name__ == "__main__":
    main()
