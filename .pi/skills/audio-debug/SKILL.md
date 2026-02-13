---
name: audio-debug
description: List audio input devices, test microphone capture, monitor audio levels in real-time. Use when setting up audio or debugging mic issues.
---

# Audio Debug Skill

Debug audio input devices and test microphone capture for espin.

## Setup

Ensure dependencies are installed:
```bash
uv add sounddevice numpy
```

## List Audio Devices

```bash
python .pi/skills/audio-debug/scripts/list_devices.py
```

Lists all available audio input/output devices with their sample rates and channels.

## Test Microphone Capture

```bash
python .pi/skills/audio-debug/scripts/test_capture.py
```

Records 5 seconds of audio and saves to `/tmp/espin_test.wav`. Prints RMS level and duration.

## Monitor Audio Levels

```bash
python .pi/skills/audio-debug/scripts/monitor_levels.py
```

Real-time audio level monitoring (Ctrl+C to stop). Shows 5-block level meter:
- ▁ (quiet)
- ▂▄▆█ (loud)

Useful to verify mic is working before running full ASR.

## Troubleshooting

**No devices found:**
- Check microphone permissions in System Settings → Privacy & Security → Microphone
- Ensure app has permission

**High latency:**
- Verify 16kHz sample rate (espin uses 16kHz mono)
- Check buffer size in sounddevice

**Permission denied:**
- Run: `sudo chown -R $(whoami) /dev/audio*` (if using OSS)
- Or grant microphone access to Terminal/IDE
