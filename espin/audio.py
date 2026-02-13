"""Audio recorder with ring buffer for espin."""

import numpy as np
import sounddevice as sd
import sys
import threading
import time
from typing import Callable, Optional


# Configuration
SAMPLE_RATE = 16000  # Required by Whisper
CHANNELS = 1  # Mono
BUFFER_SECONDS = 60  # Ring buffer size (must be >= longest recording; was 12, caused only last 12s to be transcribed)
INPUT_SAMPLE_RATE = 48000  # Default macOS mic sample rate


class AudioRecorder:
    """
    Audio recorder with ring buffer for streaming ASR.
    
    Records audio at 16kHz mono, maintains a rolling buffer
    of the last BUFFER_SECONDS.
    """
    
    def __init__(
        self,
        on_level: Optional[Callable[[float], None]] = None,
        sample_rate: int = SAMPLE_RATE,
        channels: int = CHANNELS,
        buffer_seconds: int = BUFFER_SECONDS
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_seconds = buffer_seconds
        
        # Ring buffer
        self.buffer_size = sample_rate * buffer_seconds
        self._buffer = np.zeros(self.buffer_size, dtype=np.float32)
        self._buffer_lock = threading.Lock()
        self._write_pos = 0
        self._samples_recorded = 0
        
        # State
        self._recording = False
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()
        
        # Level callback
        self.on_level = on_level
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        with self._lock:
            return self._recording
    
    @property
    def buffer(self) -> np.ndarray:
        """Get current buffer contents (thread-safe)."""
        with self._buffer_lock:
            return self._buffer.copy()
    
    @property
    def audio_length(self) -> float:
        """Get length of recorded audio in seconds."""
        with self._lock:
            return min(self._samples_recorded, self.buffer_size) / self.sample_rate
    
    def _callback(self, indata, frames, time_info, status):
        """Audio input callback."""
        if status:
            print(f"Audio status: {status}")
        
        if not self._recording:
            return
        
        # Get audio data (mono)
        audio = indata[:, 0]  # Take first channel if stereo
        
        # Calculate RMS level
        if self.on_level and len(audio) > 0:
            rms = np.sqrt(np.mean(audio**2))
            self.on_level(rms)
        
        # Write to ring buffer
        with self._buffer_lock:
            for sample in audio:
                self._buffer[self._write_pos] = sample
                self._write_pos = (self._write_pos + 1) % self.buffer_size
            
            self._samples_recorded += len(audio)
    
    def start(self) -> bool:
        """Start recording. Returns True if successful."""
        import time
        
        with self._lock:
            if self._recording:
                return False
            
            # Close any existing stream first
            if self._stream:
                try:
                    self._stream.close()
                except:
                    pass
                self._stream = None
            
            # Reset buffer
            self._buffer.fill(0)
            self._write_pos = 0
            self._samples_recorded = 0
            
            # Small delay to let previous stream release
            time.sleep(0.1)
            
            # Open stream - uses system default input (set in System Settings > Sound > Input)
            try:
                device_info = sd.query_devices(kind='input')
                print(f"[AUDIO] Using device: {device_info['name']}", file=sys.stderr)
                
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype='float32',
                    callback=self._callback,
                    blocksize=1024
                )
                self._stream.start()
                self._recording = True
                return True
            except Exception as e:
                print(f"[AUDIO] Error starting: {e}", file=sys.stderr)
                self._stream = None
                return False
    
    def stop(self) -> bool:
        """Stop recording. Returns True if successful."""
        with self._lock:
            if not self._recording:
                return False
            
            self._recording = False
            
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            
            return True
    
    def get_recent_audio(self, seconds: float) -> np.ndarray:
        """
        Get the most recent N seconds of audio.
        
        Args:
            seconds: Number of seconds to get
            
        Returns:
            Audio data as numpy array
        """
        with self._buffer_lock:
            num_samples = int(seconds * self.sample_rate)
            num_samples = min(num_samples, self.buffer_size)
            
            # Calculate read position (go back N samples)
            read_pos = (self._write_pos - num_samples) % self.buffer_size
            
            # Handle wrap-around
            if read_pos + num_samples <= self.buffer_size:
                audio = self._buffer[read_pos:read_pos + num_samples].copy()
            else:
                # Wraps around
                part1 = self._buffer[read_pos:]
                part2 = self._buffer[:(read_pos + num_samples) % self.buffer_size]
                audio = np.concatenate([part1, part2])
            
            return audio
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def compute_level_meter(rms: float) -> str:
    """
    Compute level meter string from RMS value.
    
    Args:
        rms: RMS amplitude (0.0 to 1.0)
        
    Returns:
        Level meter string like "▁▂▄▆█"
    """
    level_blocks = "▁▂▄▆█"
    
    # Map RMS to 5 levels
    level = min(int(rms * 20), 5)
    
    if level == 0:
        return "▁▁▁▁▁"
    
    meter = "".join([level_blocks[min(i, 4)] for i in range(level)])
    meter += "▁" * (5 - level)
    
    return meter


if __name__ == "__main__":
    # Test audio recorder
    print("Testing AudioRecorder...")
    
    levels = []
    
    def on_level(rms):
        levels.append(rms)
        if len(levels) % 10 == 0:
            meter = compute_level_meter(rms)
            print(f"  Level: {meter}")
    
    recorder = AudioRecorder(on_level=on_level)
    
    print("Starting recording for 3 seconds...")
    recorder.start()
    time.sleep(3)
    recorder.stop()
    
    print(f"Recorded {recorder.audio_length:.2f} seconds")
    print(f"Buffer size: {len(recorder.buffer)} samples")
