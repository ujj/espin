#!/usr/bin/env python3
"""Test 2: File creation command with correct spacing."""

import time

def main():
    print("Test 2: File Creation Command")
    print("-" * 40)
    print()
    print("Instructions:")
    print("1. Focus WezTerm or another text field")
    print("2. Press Opt+Cmd+Space to start recording")
    print("3. Say: 'create a new file called test dot py'")
    print("4. Press Opt+Cmd+Space to stop")
    print()
    print("Expected: 'create a new file called test.py'")
    print("          (space after 'called', dot converted to period)")
    print()
    print("Press Enter when ready...")
    input()
    
    print("\nRecording for 5 seconds...")
    print("Speak now!")
    time.sleep(5)
    
    print("\nStop recording now")
    print()
    print("Verify:")
    print("- 'create a new file called test.py'")
    print("- No duplicates")
    print("- Correct spacing")

if __name__ == "__main__":
    main()
