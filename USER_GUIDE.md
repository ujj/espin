# Espin User Guide

## Installation

### Homebrew Installation (Recommended)

```bash
# Add the tap
brew tap ujj/espin

# Install
brew install espin
```

### Manual Installation

```bash
# Install dependencies
uv sync

# Install the package
uv pip install -e .
```

## First-Time Setup

### 1. Grant Permissions

Espin requires two permissions to function:

#### Accessibility Permission

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the **+** button
3. Find and select your terminal app (e.g., Terminal, iTerm2, WezTerm)
4. Click **Open**
5. You may need to enter your password

#### Microphone Permission

1. Open **System Settings** → **Privacy & Security** → **Microphone**
2. Toggle the switch for your terminal app
3. You may need to enter your password

### 2. Launch Espin

```bash
# Using Homebrew
open /opt/homebrew/Caskroom/espin/Espin.app

# Or use the command line
espin
```

You should see a menu bar icon appear.

### 3. Verify Installation

1. Click the Espin icon in the menu bar
2. Select **Start Recording** (or press `Ctrl+Option+Space`)
3. Speak a short phrase (e.g., "git status")
4. Click **Stop Recording** (or press `Ctrl+Option+Space` again)
5. The text should appear in your terminal

## Usage

### Basic Recording

1. **Focus** on the application where you want to type (terminal, editor, etc.)
2. **Press** `Ctrl+Option+Space` to start recording
3. **Speak** your command
4. **Press** `Ctrl+Option+Space` to stop recording
5. **Result** - The text appears in the focused application

### Menu Bar Controls

The Espin menu bar icon provides quick access to controls:

- **Start/Stop Recording** - Toggle recording on/off
- **Settings...** - Open settings window
- **About** - Show version information
- **Quit** - Exit Espin

### Status Indicators

- **Idle** - Menu bar icon shows "E" (green)
- **Recording** - Menu bar icon shows pulsing red dot
- **Transcribing** - Menu bar icon shows spinning animation
- **Error** - Menu bar icon shows warning icon

## Settings

### Hotkey Configuration

1. Click the Espin icon → **Settings...**
2. Navigate to **Hotkey** tab
3. Click the hotkey field
4. Press your desired hotkey combination
5. Click **Save**

### Audio Device Selection

1. Click the Espin icon → **Settings...**
2. Navigate to **Audio** tab
3. Select your preferred audio input device
4. Click **Save**

### Recording Duration

1. Click the Espin icon → **Settings...**
2. Navigate to **Recording** tab
3. Adjust the maximum recording duration (default: 30 seconds)
4. Click **Save**

### Sound Feedback

1. Click the Espin icon → **Settings...**
2. Navigate to **Audio** tab
3. Toggle sound feedback on/off
4. Click **Save**

### MLX Model Selection

1. Click the Espin icon → **Settings...**
2. Navigate to **ASR** tab
3. Select your preferred model:
   - **tiny** - Fastest, lower accuracy
   - **medium** - Balanced (default)
   - **large** - Slowest, highest accuracy
4. Click **Save**

## Troubleshooting

### Text Not Appearing

**Problem**: After recording, no text appears in the focused app.

**Solutions**:

1. Check that Accessibility permission is granted
2. Make sure your terminal app is selected in Accessibility settings
3. Try restarting Espin
4. Check the terminal logs for errors

### No Audio Input

**Problem**: Recording doesn't capture audio.

**Solutions**:

1. Check that Microphone permission is granted
2. Select the correct audio device in Settings
3. Test your microphone with another app
4. Check that your terminal app has microphone access

### Hotkey Not Working

**Problem**: Pressing the hotkey doesn't start/stop recording.

**Solutions**:

1. Check that the hotkey is not conflicting with another app
2. Try a different hotkey combination
3. Restart Espin
4. Check that the hotkey is enabled in Settings

### App Won't Start

**Problem**: Espin crashes on launch.

**Solutions**:

1. Check the terminal logs for error messages
2. Verify all dependencies are installed (`uv sync`)
3. Check that Python 3.11+ is installed
4. Try reinstalling: `brew reinstall espin`

### Permission Denied Errors

**Problem**: Espin shows permission errors.

**Solutions**:

1. Open System Settings → Privacy & Security
2. Grant Accessibility permission
3. Grant Microphone permission
4. Restart Espin

## Performance Tips

### For Faster Transcription

1. Use the **tiny** MLX model in Settings
2. Speak clearly and at a moderate pace
3. Use a good quality microphone
4. Reduce background noise

### For Better Accuracy

1. Use the **medium** or **large** MLX model
2. Speak clearly and at a moderate pace
3. Use a high-quality microphone
4. Reduce background noise

### For Lower Latency

1. Use the **tiny** MLX model
2. Use a fast computer
3. Close other resource-intensive apps
4. Use a wired microphone instead of Bluetooth

## Keyboard Shortcuts

| Action               | Shortcut                                  |
| -------------------- | ----------------------------------------- |
| Start/Stop Recording | `Ctrl+Option+Space`                       |
| Quit Espin           | `Ctrl+C` (in terminal) or menu bar → Quit |

## Getting Help

- **GitHub Issues**: https://github.com/ujjwal/espin/issues
- **Documentation**: See README.md for more details
- **Homebrew**: https://formulae.brew.sh/formula/espin

## Uninstallation

### Homebrew

```bash
brew uninstall espin
brew untap ujjwal/espin
```

### Manual

```bash
# Remove the package
uv pip uninstall espin

# Remove dependencies (optional)
uv sync --no-dev
```

## License

MIT
