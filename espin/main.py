"""Main orchestrator for espin - simple version, transcribe at end only. No streaming."""

import os
import subprocess
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
MAX_RECORDING_SECONDS = 30

# Audio cues
SOUND_START = "/System/Library/Sounds/Ping.aiff"
SOUND_STOP = "/System/Library/Sounds/Pop.aiff"


def play_sound(path: str):
    if os.path.exists(path):
        subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Espin:
    """Simple Espin - transcribe at end only. No streaming."""
    
    def __init__(self):
        from espin.state import EspinState
        from espin.hotkey import HotkeyListener
        from espin.audio import AudioRecorder, compute_level_meter
        from espin.asr import ASREngine
        from espin.injector import Injector
        
        self.state = EspinState()
        self.audio = AudioRecorder(on_level=self._on_audio_level)
        self.asr = ASREngine()
        self.injector = Injector()
        
        self.hotkey = HotkeyListener(on_toggle=self._on_hotkey_toggle)
        
        self._running = False
        self._current_level = 0.0
        self._recording_start_time: Optional[float] = None
    
    def _on_audio_level(self, rms: float):
        self._current_level = rms
    
    def _on_hotkey_toggle(self):
        if self.state.is_idle:
            self.start_recording()
        else:
            self.stop_recording()
    
    def _print_status(self, status: str, newline: bool = False):
        if newline:
            print()
        sys.stdout.write(f"\r{status}")
        sys.stdout.flush()
    
    def _format_time(self, seconds: float) -> str:
        return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"
    
    def _get_level_meter(self) -> str:
        from espin.audio import compute_level_meter
        return compute_level_meter(self._current_level)
    
    def start_recording(self):
        if not self.state.start_recording():
            return
        
        if not self.audio.start():
            self.state.cancel()
            self._print_status("⚠ ERROR: Audio device", newline=True)
            return
        
        self._recording_start_time = time.time()
        play_sound(SOUND_START)
        self._print_status(f"● REC {self._format_time(0)} lvl:{self._get_level_meter()}")
    
    def stop_recording(self):
        if self.state.is_idle:
            return
        
        self.audio.stop()
        play_sound(SOUND_STOP)
        
        self._print_status("… TRANSCRIBING …")
        print()
        
        # Get all audio
        audio = self.audio.get_recent_audio(self.audio.audio_length)
        print(f"[DEBUG] Audio: {len(audio)/16000:.2f}s", file=sys.stderr)
        
        if len(audio) < 1600:
            self.state.stop()
            self._print_status("✓ DONE (too short)", newline=True)
            return
        
        # Transcribe ONCE
        try:
            hypothesis = self.asr.transcribe(audio)
            print(f"[DEBUG] Got: '{hypothesis}'", file=sys.stderr)
        except Exception as e:
            print(f"[DEBUG] Error: {e}", file=sys.stderr)
            hypothesis = ""
        
        self.state.stop()
        
        # Type the result
        if hypothesis:
            self.injector.type_text(hypothesis)
        
        duration = time.time() - self._recording_start_time if self._recording_start_time else 0
        self._print_status(f"✓ DONE ({duration:.1f}s)", newline=True)
    
    def run(self):
        self._running = True
        
        print("espin running.")
        print("Press Ctrl+Option+Space to start/stop recording.")
        print("Press Ctrl+C to quit.")
        print()
        self._print_status("espin ready — press Ctrl+Option+Space")
        print()
        
        self.hotkey.start()
        
        try:
            while self._running:
                if self.state.is_recording:
                    elapsed = time.time() - self._recording_start_time if self._recording_start_time else 0
                    self._print_status(f"● REC {self._format_time(elapsed)} lvl:{self._get_level_meter()}")
                    
                    if elapsed > MAX_RECORDING_SECONDS:
                        print("\n[TIMEOUT]", file=sys.stderr)
                        self.stop_recording()
                
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.hotkey.stop()
            if self.audio.is_recording:
                self.audio.stop()


def main():
    from dotenv import load_dotenv
    load_dotenv()
    
    espin = Espin()
    espin.run()


if __name__ == "__main__":
    main()
