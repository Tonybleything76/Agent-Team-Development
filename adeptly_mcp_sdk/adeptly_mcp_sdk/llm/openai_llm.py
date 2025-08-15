from .interfaces import LLMClient

class OpenAILLM(LLMClient):
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
    def generate(self, prompt: str) -> str:
        # placeholder to integrate real API
        return f"[{self.model}] {prompt[:80]}..."
