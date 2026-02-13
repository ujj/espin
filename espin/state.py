"""State machine for espin recording states."""

from enum import Enum
from typing import Optional
import threading


class State(Enum):
    """Espin recording states."""
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"


class EspinState:
    """
    Thread-safe state machine for espin.
    
    States: idle → recording → transcribing → idle
    """
    
    def __init__(self):
        self._state = State.IDLE
        self._lock = threading.Lock()
        self._start_time: Optional[float] = None
    
    @property
    def state(self) -> State:
        """Get current state."""
        with self._lock:
            return self._state
    
    @property
    def is_idle(self) -> bool:
        """Check if idle."""
        return self.state == State.IDLE
    
    @property
    def is_recording(self) -> bool:
        """Check if recording."""
        return self.state == State.RECORDING
    
    @property
    def is_transcribing(self) -> bool:
        """Check if transcribing."""
        return self.state == State.TRANSCRIBING
    
    @property
    def start_time(self) -> Optional[float]:
        """Get recording start time."""
        with self._lock:
            return self._start_time
    
    def start_recording(self) -> bool:
        """
        Transition from idle to recording.
        Returns True if successful, False if not in idle state.
        """
        import time
        with self._lock:
            if self._state == State.IDLE:
                self._state = State.RECORDING
                self._start_time = time.time()
                return True
            return False
    
    def start_transcribing(self) -> bool:
        """
        Transition from recording to transcribing.
        Returns True if successful, False if not in recording state.
        """
        with self._lock:
            if self._state == State.RECORDING:
                self._state = State.TRANSCRIBING
                return True
            return False
    
    def stop(self) -> bool:
        """
        Transition from recording or transcribing to idle.
        Returns True if successful, False if not in recording/transcribing.
        """
        with self._lock:
            if self._state in (State.RECORDING, State.TRANSCRIBING):
                self._state = State.IDLE
                self._start_time = None
                return True
            return False
    
    def cancel(self) -> bool:
        """
        Cancel recording and return to idle.
        Works from recording state only.
        Returns True if successful, False if not in recording.
        """
        with self._lock:
            if self._state == State.RECORDING:
                self._state = State.IDLE
                self._start_time = None
                return True
            return False
    
    def __repr__(self) -> str:
        return f"EspinState({self._state.value})"
