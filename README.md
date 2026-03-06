# Espin

Local Streaming ASR for Coding Agents on macOS.

A fully local, low-latency voice-to-text tool that uses MLX Whisper for English transcription and streams recognized words directly into the currently focused application.

## Features

- 🎤 **Local ASR** - Uses MLX Whisper (medium) for English-only transcription
- ⌨️ **Text Injection** - Types directly into the focused app via CGEvent
- 🔊 **Audio Cues** - Sound feedback for start/stop
- 📊 **Live Waveform** - Visual feedback during recording
- 🍎 **macOS Native** - No Electron, no GUI framework

## Requirements

- macOS 11+
- For Homebrew install: no Python/uv needed. For manual install: Python 3.11+ and [uv](https://github.com/astral-sh/uv).
- Any microphone (system default; set in System Settings → Sound → Input).

## Install

### Option 1: Homebrew (recommended)

```bash
brew tap ujj/espin
brew install espin
```

### Option 2: Manual (developers)

```bash
uv sync
uv pip install -e .
```

## Permissions

Grant your **terminal app** (Terminal, WezTerm, iTerm, Cursor, etc.) these permissions in System Settings → Privacy & Security:

1. **Accessibility** — required for typing transcribed text into the focused app
2. **Microphone** — required for recording

Most terminal power users already have Accessibility granted.

## Usage

Start Espin:
```bash
espin-gui
```

- **Ctrl+Option+Space** — Start or stop recording (floating window appears while recording)
- **Right-click** the recording window — Menu (Toggle, About, Quit)
- **Ctrl+C** — Quit

**Workflow:** Focus any text field → press Ctrl+Option+Space → speak → press Ctrl+Option+Space again → transcribed text is typed into the focused app.

## Configuration

Edit `espin/main.py` to adjust:
- `MAX_RECORDING_SECONDS` - Max recording duration (default: 30s)
- Audio device settings in `espin/audio.py`

## Architecture

```
espin/
├── main.py       # Orchestrator
├── state.py      # State machine (idle → recording)
├── hotkey.py     # Global hotkey listener
├── audio.py      # Audio recording with ring buffer
├── asr.py        # MLX Whisper transcription
├── stabilizer.py # Delta handling (not used in v1)
└── injector.py   # CGEvent key injection
```

## Status

- ✅ Transcription (MLX Whisper) and text injection
- ✅ Floating recording window (waveform, top-center)
- ✅ Homebrew Formula
- ⏳ Streaming mode (not implemented in v1)

## License

MIT
