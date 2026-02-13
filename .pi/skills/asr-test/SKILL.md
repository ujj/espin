---
name: asr-test
description: Test MLX Whisper transcription independently. Use to verify ASR engine works before integrating with full application.
---

# ASR Test Skill

Test MLX Whisper transcription engine for espin.

## Setup

Install MLX Whisper:
```bash
uv add mlx-whisper
```

## Transcribe Audio File

```bash
python .pi/skills/asr-test/scripts/transcribe.py /tmp/espin_test.wav
```

Transcribes a WAV file and prints transcript, processing time, and words with timestamps.

## Test Streaming Mode

```bash
python .pi/skills/asr-test/scripts/test_streaming.py
```

Simulates streaming ASR - records 5 seconds, transcribes in chunks, shows delta.

## Quick Test

```bash
python .pi/skills/asr-test/scripts/quick_test.py
```

Creates test audio and transcribes it without needing a real mic.
