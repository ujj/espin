#!/usr/bin/env python3
"""Test microphone capture with device selection."""

import sounddevice as sd
import numpy as np
import wave
import sys

SAMPLE_RATE = 16000
DURATION = 5
CHANNELS = 1

def main():
    # Check for device argument
    device = None
    if len(sys.argv) > 1:
        try:
            device = int(sys.argv[1])
            print(f"Using device: {device}")
        except ValueError:
            print(f"Invalid device: {sys.argv[1]}")
            sys.exit(1)
    else:
        print("Using default input device")
    
    print(f"\nRecording {DURATION} seconds...")
    print("Speak now! (Ctrl+C to stop early)")
    print("-" * 40)
    
    try:
        audio_data = []
        
        def callback(indata, frames, time_info, status):
            if status:
                print(f"Status: {status}")
            audio_data.append(indata.copy())
            
            # Show we're getting data
            if len(audio_data) % 10 == 0:
                rms = np.sqrt(np.mean(indata**2))
                print(f"  Received {len(audio_data)} chunks, RMS: {rms:.4f}", end='\r')
        
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            device=device,
            callback=callback
        ) as stream:
            print(f"Stream started - device: {stream.device}")
            print(f"Sample rate: {stream.samplerate}, Channels: {stream.channels}")
            print()
            
            sd.sleep(DURATION * 1000)
        
        # Combine and flatten
        audio = np.concatenate(audio_data).flatten()
        
        # Calculate RMS
        rms = np.sqrt(np.mean(audio**2))
        
        # Save to WAV
        output_path = "/tmp/espin_test.wav"
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            audio_int16 = (audio * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())
        
        print(f"\n\n✓ Saved to {output_path}")
        print(f"  Duration: {len(audio) / SAMPLE_RATE:.2f}s")
        print(f"  RMS level: {rms:.4f}")
        
        if rms < 0.001:
            print("  WARNING: Very low audio level - check microphone!")
        
        # Map to level
        level = min(int(rms * 20), 5)
        meter = "▁▂▄▆█"
        bar = "".join([meter[min(i, 4)] for i in range(level)]) + "▁" * (5 - level)
        print(f"  Level: {bar}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
