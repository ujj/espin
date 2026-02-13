#!/usr/bin/env python3
"""Test streaming ASR - simulates the 0.8s chunk interval."""

import sys
import time
import numpy as np

try:
    import mlx_whisper
    import sounddevice as sd
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: uv add mlx-whisper sounddevice")
    sys.exit(1)

SAMPLE_RATE = 16000
CHUNK_SECONDS = 2
TOTAL_SECONDS = 6
OVERLAP_SECONDS = 1

def record_audio(duration):
    """Record audio for given duration."""
    print(f"Recording {duration}s of audio...")
    audio_data = []
    
    def callback(indata, frames, time_info, status):
        audio_data.append(indata.copy())
    
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32',
        callback=callback
    ):
        sd.sleep(duration * 1000)
    
    audio = np.concatenate(audio_data).flatten()
    return audio

def transcribe_chunk(audio):
    """Transcribe audio chunk."""
    import tempfile
    import wave
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmp_path = f.name
    
    with wave.open(tmp_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        audio_int16 = (audio * 32767).astype(np.int16)
        wf.writeframes(audio_int16.tobytes())
    
    result = mlx_whisper.transcribe(
        tmp_path,
        path_or_hf_repo="mlx-community/whisper-medium",
        language="en",
        temperature=0.0,
    )
    
    import os
    os.unlink(tmp_path)
    
    return result['text']

def main():
    print("Streaming ASR Test")
    print("=" * 40)
    print("Speak continuously for ~6 seconds")
    print()
    
    # Record full audio
    full_audio = record_audio(TOTAL_SECONDS)
    
    print("\nSimulating streaming chunks...")
    print("-" * 40)
    
    # Simulate streaming: transcribe overlapping chunks
    prev_text = ""
    for i in range(3):
        start_idx = i * (CHUNK_SECONDS - OVERLAP_SECONDS) * SAMPLE_RATE
        end_idx = min((i + 1) * CHUNK_SECONDS * SAMPLE_RATE, len(full_audio))
        chunk = full_audio[start_idx:end_idx]
        
        text = transcribe_chunk(chunk)
        
        # Find delta
        if text.startswith(prev_text):
            delta = text[len(prev_text):]
        else:
            delta = f"NEW: {text}"
        
        print(f"Chunk {i+1}: {text}")
        print(f"  Delta: {delta}")
        
        prev_text = text
        time.sleep(0.5)

if __name__ == "__main__":
    main()
