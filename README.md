# Espin

Local Streaming ASR for Coding Agents on macOS.

A fully local, low-latency voice-to-text tool that uses MLX Whisper for English transcription and streams recognized words directly into the currently focused application.

## Features

- 🎤 **Local ASR** - Uses MLX Whisper (medium) for English-only transcription
- ⌨️ **Text Injection** - Types directly into the focused app via CGEvent
- 🔊 **Audio Cues** - Sound feedback for start/stop
- 📊 **Level Meter** - Visual feedback during recording
- 🍎 **macOS Native** - No Electron, no GUI framework

## Requirements

- macOS 11+
- For Homebrew install: no Python/uv needed. For manual install: Python 3.11+ and [uv](https://github.com/astral-sh/uv).
- Any microphone (system default; set in System Settings → Sound → Input).

## Setup

### Option 1: Homebrew (recommended)

**App in Applications (double-click to launch):**
```bash
brew tap ujjwal/espin
brew install --cask espin
```
Then open **Espin** from Applications (or Spotlight). No `uv` or Terminal needed.

**Formula only** (app under Homebrew prefix, or use `espin` / `espin-gui` in Terminal):
```bash
brew tap ujjwal/espin
brew install espin
open espin.app   # or: open $(brew --prefix espin)/bin/espin.app
```

### Option 2: Manual installation (developers)

```bash
uv sync
uv pip install -e .
```

Run GUI: `uv run espin-gui` or double-click `espin.app` (keep it inside the project folder after running `uv sync` once).

### Permissions

Grant these to **Espin** (or your terminal app if you run the CLI) in System Settings → Privacy & Security:

1. **Accessibility** — required for typing transcribed text into the focused app  
2. **Microphone** — required for recording

## Usage

- **Ctrl+Option+Space** — Start or stop recording (floating window appears while recording)
- **Right-click** the recording window — Menu (Toggle, About, Quit)
- **Ctrl+C** — Quit when run from Terminal

**Workflow:** Focus any text field → Ctrl+Option+Space to start → speak → Ctrl+Option+Space to stop → transcribed text is typed into the focused app.

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
├── asr.py       # MLX Whisper transcription
├── stabilizer.py # Delta handling (not used in v1)
└── injector.py   # CGEvent key injection
```

## Status

- ✅ Transcription (MLX Whisper) and text injection
- ✅ Floating recording window (waveform, top-center)
- ✅ Homebrew Formula + Cask (double-click app in Applications)
- ⏳ Streaming mode (not implemented in v1)

## License

MIT
