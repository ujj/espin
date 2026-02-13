"""Delta stabilization algorithm for streaming ASR."""

from typing import Tuple


class Stabilizer:
    """
    Delta stabilizer for streaming ASR.
    
    Tracks what's been typed and only returns new content.
    """
    
    def __init__(self):
        self.typed_text: str = ""  # Everything we've typed so far
    
    def reset(self):
        """Reset the stabilizer."""
        self.typed_text = ""
    
    def update(self, hypothesis: str) -> Tuple[str, bool]:
        """
        Get only the NEW text from hypothesis.
        
        Returns:
            Tuple of (new_text, is_committed)
        """
        hypothesis = hypothesis.strip()
        
        if not hypothesis:
            return "", False
        
        # Find what's new - hypothesis might contain what we've already typed
        if hypothesis.startswith(self.typed_text):
            # Easy case - new text is appended
            new_text = hypothesis[len(self.typed_text):]
            self.typed_text = hypothesis
            return new_text.strip(), False
        
        # Hypothesis doesn't start with what we typed
        # This happens when Whisper gives very different transcriptions
        # In this case, find common prefix
        common_len = 0
        min_len = min(len(self.typed_text), len(hypothesis))
        for i in range(min_len):
            if self.typed_text[i] == hypothesis[i]:
                common_len = i + 1
            else:
                break
        
        if common_len > 0:
            # Found common prefix, new text is after it
            new_text = hypothesis[common_len:]
            self.typed_text = hypothesis
            return new_text.strip(), False
        
        # No common prefix - this is a big change
        # Only return text that looks new (check word boundaries)
        if self.typed_text and len(hypothesis) > len(self.typed_text):
            # Find last word in what we typed
            last_space = self.typed_text.rfind(' ')
            if last_space > 0:
                last_word = self.typed_text[last_space+1:]
                # Check if hypothesis contains this word
                if last_word.lower() in hypothesis.lower():
                    # Find where that word appears in hypothesis
                    idx = hypothesis.lower().find(last_word.lower())
                    if idx > 0:
                        new_text = hypothesis[idx + len(last_word):]
                        self.typed_text = hypothesis
                        return new_text.strip(), False
        
        # Just use the whole thing as new (but this might cause duplicates)
        # For safety, only return if it's substantially different
        if abs(len(hypothesis) - len(self.typed_text)) > 5:
            self.typed_text = hypothesis
            return hypothesis, False
        
        return "", False
    
    def commit_all(self) -> str:
        """Get any remaining text."""
        return ""
    
    def get_state(self) -> dict:
        return {"typed": repr(self.typed_text)}


if __name__ == "__main__":
    # Test
    s = Stabilizer()
    
    test = [
        "hello",
        "hello world",
        "how are you",
        "how are you doing",
    ]
    
    for h in test:
        delta = s.update(h)
        print(f"Hypothesis: '{h}'")
        print(f"  Delta: '{delta}'")
        print(f"  Typed: '{s.typed_text}'")
        print()
