#!/usr/bin/env python3
"""Quick test - creates test audio using say command and transcribes it."""

import sys
import os
import tempfile
import time

try:
    import mlx_whisper
except ImportError:
    print("Error: mlx-whisper not installed")
    print("Run: uv add mlx-whisper")
    sys.exit(1)

TEST_PHRASES = [
    "git status",
    "create a new file called test dot py",
    "list all files in the current directory",
]

def main():
    print("Quick ASR Test")
    print("=" * 40)
    
    for phrase in TEST_PHRASES:
        print(f"\nTest: \"{phrase}\"")
        
        # Create audio using macOS say command
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            tmp_wav = f.name
        
        # Use say to generate audio (convert to 16kHz mono)
        wav_44k = tmp_wav.replace('.wav', '_44k.wav')
        
        os.system(f'say "{phrase}" -o {wav_44k} 2>/dev/null')
        
        # Convert to 16kHz mono using ffmpeg if available
        convert_cmd = f'ffmpeg -y -i {wav_44k} -ar 16000 -ac 1 {tmp_wav} 2>/dev/null'
        result = os.system(convert_cmd)
        
        if result != 0:
            # Fallback: just use the original
            os.rename(wav_44k, tmp_wav)
        
        # Transcribe
        start = time.perf_counter()
        result = mlx_whisper.transcribe(
            tmp_wav,
            path_or_hf_repo="mlx-community/whisper-medium",
            language="en",
            temperature=0.0,
        )
        elapsed = time.perf_counter() - start
        
        print(f"  Got:   \"{result['text'].strip()}\"")
        print(f"  Time:  {elapsed:.2f}s")
        
        # Cleanup
        os.unlink(tmp_wav)
        if os.path.exists(wav_44k):
            os.unlink(wav_44k)
    
    print("\n" + "=" * 40)
    print("Done!")

if __name__ == "__main__":
    main()
