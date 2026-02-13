"""MLX Whisper ASR engine for espin."""

import tempfile
import wave
import os
import sys
from typing import Optional
import numpy as np


# Configuration
MODEL_NAME = "whisper-medium"
LANGUAGE = "en"
TEMPERATURE = 0.0


class ASREngine:
    """
    MLX Whisper ASR engine for streaming transcription services.
    
    Uses whisper-medium model for English transcription services. see: https://github.com/mlx-ai/whisper-medium
    see: https://github.com/mlx-ai/mlx-whisper
    """
    
    def __init__(
        self,
        model_name: str = MODEL_NAME,
        language: str = LANGUAGE,
        temperature: float = TEMPERATURE
    ):
        self.model_name = model_name
        self.language = language
        self.temperature = temperature
        self._model = None

    def ensure_model(self) -> None:
        """
        Ensure the HF model snapshot exists locally.

        On first run, downloads the model and shows progress via huggingface_hub.
        """
        repo_id = f"mlx-community/{self.model_name}"
        try:
            from huggingface_hub import snapshot_download, try_to_load_from_cache
        except Exception:
            # mlx_whisper will still try to download on first transcribe; we just can't show progress here.
            print(
                "[ASR] huggingface_hub not available; model will be fetched on first transcription.",
                file=sys.stderr,
            )
            return

        # Fast path: already cached (huggingface_hub caches by repo, independent of mlx_whisper)
        try:
            cache_hit = try_to_load_from_cache(repo_id, "README.md")
        except Exception:
            cache_hit = None
        if cache_hit:
            return

        print(f"[ASR] Downloading Whisper model ({repo_id})…", file=sys.stderr)
        # snapshot_download emits progress bars (tqdm) by default.
        snapshot_download(repo_id)
        print("[ASR] Model download complete.", file=sys.stderr)
    
    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                import mlx_whisper
                # Pre-download/load the model
                self._model = mlx_whisper
                print(f"[ASR] Loaded model: {self.model_name}", file=sys.stderr)
            except ImportError:
                raise RuntimeError("mlx-whisper not installed. Run: uv add mlx-whisper")
    
    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> str:
        """
        Transcribe audio data.
        
        Args:
            audio: Audio data as float32 numpy array (mono)
            sample_rate: Sample rate of audio
            
        Returns:
            Transcribed text
        """
        self._load_model()
        
        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            tmp_path = f.name
        
        try:
            # Write WAV file
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                # Convert float32 to int16
                audio_int16 = (audio * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
            
            # Transcribe
            import mlx_whisper
            result = mlx_whisper.transcribe(
                tmp_path,
                path_or_hf_repo=f"mlx-community/{self.model_name}",
                language=self.language,
                temperature=self.temperature,
            )
            
            return result.get('text', '').strip()
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def transcribe_file(self, audio_path: str) -> str:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        self._load_model()
        
        import mlx_whisper
        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=f"mlx-community/{self.model_name}",
            language=self.language,
            temperature=self.temperature,
        )
        
        return result.get('text', '').strip()


if __name__ == "__main__":
    # Quick test using silence for now
    import time
    
    print("Testing ASR Engine...")
    
    # Create test audio (silence for now)
    sample_rate = 16000
    duration = 2  # seconds
    audio = np.zeros(sample_rate * duration, dtype=np.float32)
    
    engine = ASREngine()
    
    print("Transcribing test audio (silence)...")
    start = time.perf_counter()
    result = engine.transcribe(audio, sample_rate)
    elapsed = time.perf_counter() - start
    
    print(f"Result: '{result}'")
    print(f"Time: {elapsed:.2f}s")
