---
name: integration-test
description: Full end-to-end integration tests for espin. Use to verify the complete voice-to-text pipeline works correctly.
---

# Integration Test Skill

Test the complete espin pipeline from recording to text injection.

## Prerequisites

Before running tests, ensure:
1. Accessibility permission granted
2. Microphone permission granted
3. Dependencies installed: uv add sounddevice numpy mlx-whisper pyobjc-framework-Quartz

## Run All Tests

```bash
python .pi/skills/integration-test/scripts/run_tests.py
```

Runs Test 1, 2, and 3 from the spec.

## Individual Tests

### Test 1: Basic Transcription
```bash
python .pi/skills/integration-test/scripts/test_basic.py
```
Speak "git status" → should appear in target app.

### Test 2: File Creation Command
```bash
python .pi/skills/integration-test/scripts/test_file_cmd.py
```
Speak "create a new file called test dot py" → verify spacing.

### Test 3: Streaming Behavior
```bash
python .pi/skills/integration-test/scripts/test_streaming.py
```
Speak 10-second sentence → verify gradual appearance, no flicker.

## Manual Testing Checklist

- [ ] Hotkey triggers recording (sound plays)
- [ ] Level meter updates smoothly
- [ ] Words appear within 1.5s
- [ ] No duplicate words
- [ ] No flicker/rewrites
- [ ] Stop hotkey finalizes
- [ ] Cancel hotkey discards
- [ ] Error states show properly

## Performance Targets

- First partial text < 1.5s
- Final transcription < 3s after stop
- No noticeable lag between words
