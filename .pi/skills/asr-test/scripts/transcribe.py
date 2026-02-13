#!/usr/bin/env python3
"""Transcribe an audio file using MLX Whisper."""

import sys
import time
import wave

try:
    import mlx_whisper
except ImportError:
    print("Error: mlx-whisper not installed")
    print("Run: uv add mlx-whisper")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    print(f"Transcribing: {audio_file}")
    print("-" * 40)
    
    start = time.perf_counter()
    result = mlx_whisper.transcribe(
        audio_file,
        path_or_hf_repo="mlx-community/whisper-medium",
        language="en",
        temperature=0.0,
    )
    elapsed = time.perf_counter() - start
    
    print(f"Transcript: {result['text']}")
    print(f"\nTime: {elapsed:.2f}s")
    
    if "words" in result:
        print("\nWords with timestamps:")
        for word in result["words"][:10]:  # First 10 words
            print(f"  {word.get('word', '')}: {word.get('start', 0):.2f}s - {word.get('end', 0):.2f}s")

if __name__ == "__main__":
    main()
