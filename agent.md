# Agent Configuration: espin

## Project Context

Building **espin** — a fully local, low-latency voice-to-text tool for macOS coding agents. 

- Uses MLX Whisper (medium) for English ASR
- Streams recognized words into the currently focused app via CGEvent key injection
- Global hotkey driven (Opt+Cmd+Space), no GUI, terminal status feedback
- Target apps: WezTerm, Claude Code, Cursor, any editor

## Persona

Think like a **mid-to-senior engineer** with a **bias for action**:

- Prefer working code over perfect abstractions
- Ship incrementally, validate assumptions quickly
- When in doubt, run the code and see what happens
- Keep it simple until complexity is justified

## Technical Preferences

### Package Management
- **Use `uv` exclusively** for Python packages
- Commands: `uv add <pkg>`, `uv run <script>`, `uv pip install`
- Never use raw `pip` or `pipenv`

### Environment Variables
- **Use `python-dotenv`** for env vars
- Load with `from dotenv import load_dotenv; load_dotenv()`
- Keep `.env` in gitignore, provide `.env.example`

### Version Control
- **Use git** for all version control
- Make frequent, small commits with clear messages
- Use branches for features if they touch multiple files

### Python Standards
- Python 3.11+
- Type hints where they help clarity, skip where they obstruct
- Docstrings for public functions, inline comments for tricky logic
- Follow existing project structure in `espin/` directory

## Debugging & Monitoring Philosophy

**Always write debug scripts to validate your work:**

- Create `scripts/test_<component>.py` for isolated testing
- Add `scripts/debug.py` for quick sanity checks
- Include timing/profiling when performance matters (target: <1.5s first partial)
- Use logging over print statements in production code
- Add `--debug` flag support where useful

**Preferred debugging tools:**
- `python -m pdb` for stepping through
- `logging` module with levels (DEBUG, INFO, WARNING)
- Simple timing: `time.perf_counter()`
- Audio debug: write test WAV files to `/tmp` when needed

## macOS Specifics

This is **macOS only**:
- Use `pyobjc-framework-Quartz` for CGEvent injection
- Use `afplay` for audio cues (non-blocking subprocess)
- Request Accessibility permissions explicitly
- Test in WezTerm as primary target

## Component Patterns

### Audio (`audio.py`)
- Use `sounddevice` with callback-based recording
- Ring buffer for 12s of 16kHz mono float32 audio
- RMS calculation for level meter (5-block: ▁▂▄▆█)

### ASR (`asr.py`)
- `mlx-whisper` with temperature=0, language="en"
- Transcribe rolling buffer every 0.8s
- Word timestamps if available

### Stabilizer (`stabilizer.py`)
- Maintain `prev_hypothesis`, `committed_text`, `stability_counter`
- Commit only words unchanged in 2 consecutive iterations
- Never delete committed text, only append

### Injector (`injector.py`)
- Use `CGEventCreateKeyboardEvent`, not clipboard
- Simulate real key events for streaming effect
- Handle special keys (space, return) via key codes

### Hotkeys (`hotkey.py`)
- Use `pynput` for global hotkey listening
- Handle: Opt+Cmd+Space (toggle), Opt+Cmd+Esc (cancel)
- Non-blocking, runs in separate thread

### State (`state.py`)
- Simple state machine: idle → recording → transcribing → idle
- Thread-safe where needed

### Main (`main.py`)
- Orchestrate components
- Terminal status line with `\r` + flush updates
- Audio cue spawning (afplay in background)

## Status Line Format

Use exact strings for states:
- Idle: `espin ready — press ⌥⌘Space to record, ⌥⌘Esc to cancel`
- Recording: `● REC 00:07 lvl:▂▄▆█▆` (updates every 200ms)
- Transcribing: `… TRANSCRIBING …`
- Done: `✓ DONE (712 tokens, 26.0s)`
- Cancelled: `⨯ CANCELLED`
- Error: `⚠ ERROR: <short message>`

## When Implementing

1. **Read the spec** — acceptance criteria are the source of truth
2. **Start with a test script** — validate component in isolation
3. **Wire it together** — minimal integration, test end-to-end
4. **Polish** — logging, error handling, edge cases
5. **Verify acceptance criteria** — run Test 1, 2, 3 manually

## Testing Checklist

Before saying "done", verify:
- [ ] `uv run espin` starts without errors
- [ ] Hotkey triggers recording (Ping sound plays)
- [ ] Level meter updates smoothly during recording
- [ ] Words appear in focused app within 1.5s
- [ ] No duplicate words, no flicker
- [ ] Stop hotkey finalizes transcription
- [ ] Cancel hotkey discards and plays Basso sound
- [ ] Error states show ⚠ and play Sosumi

## Communication Style

- Be concise, technical, direct
- Show file paths when editing
- When summarizing, output plain text (no cat/bash for display)
- If stuck, propose 2-3 specific options with tradeoffs
- Celebrate wins: `✓ Component working`

## Skills

Use these project-specific skills during development:

### Debug Skills (`.pi/skills/`)

- **audio-debug** — List devices, test mic capture, monitor levels
  - `/skill:audio-debug` to load
  - Scripts: `list_devices.py`, `test_capture.py`, `monitor_levels.py`

- **asr-test** — Test MLX Whisper transcription
  - `/skill:asr-test` to load
  - Scripts: `transcribe.py`, `test_streaming.py`, `quick_test.py`

- **text-inject-test** — Test CGEvent key injection
  - `/skill:text-inject-test` to load
  - Scripts: `test_inject.py`, `test_keys.py`, `test_stream.py`

- **accessibility-check** — Verify macOS permissions
  - `/skill:accessibility-check` to load
  - Script: `check.py`

- **integration-test** — Full end-to-end tests
  - `/skill:integration-test` to load
  - Scripts: `run_tests.py`, `test_basic.py`, `test_file_cmd.py`, `test_streaming.py`

### Usage Pattern

1. When setting up audio: `python .pi/skills/audio-debug/scripts/list_devices.py`
2. When testing transcription: `python .pi/skills/asr-test/scripts/transcribe.py /tmp/test.wav`
3. When debugging injection: `python .pi/skills/text-inject-test/scripts/check_permission.py`
4. When doing full testing: `python .pi/skills/integration-test/scripts/run_tests.py`
