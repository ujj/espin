#!/usr/bin/env python3
"""Monitor audio levels in real-time."""

import sounddevice as sd
import numpy as np
import sys

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1024

def main():
    print("Monitoring audio levels (Ctrl+C to stop)...")
    print("Level: ", end="", flush=True)
    
    level_blocks = "▁▂▄▆█"
    
    def callback(indata, frames, time_info, status):
        if status:
            print(f"\nStatus: {status}")
        
        # Calculate RMS
        rms = np.sqrt(np.mean(indata**2))
        
        # Map to 5 levels
        level = min(int(rms * 20), 5)
        meter = "".join([level_blocks[min(i, 4)] for i in range(level)])
        meter += "▁" * (5 - level)
        
        # Overwrite line
        sys.stdout.write(f"\rLevel: {meter} ")
        sys.stdout.flush()
    
    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            blocksize=BLOCK_SIZE,
            callback=callback
        ):
            while True:
                sd.sleep(100)
    except KeyboardInterrupt:
        print("\n\nStopped.")

if __name__ == "__main__":
    main()
