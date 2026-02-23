from app.backends.local import LocalBackend
from app.backends.openai_backend import OpenAIBackend
from app.backends.gemini_backend import GeminiBackend

class BackendRouter:
    def __init__(self):
        self.backends = {
            "local": LocalBackend(),
            "openai": None,  # OpenAIBackend will be initialized lazily
            "gemini": None,  # GeminiBackend will be initialized lazily
        }
    
    def get_backend_for_model(self, model: str):
        """
        Strategy:
        - if model starts with "gpt-" use openAI
        - otherwise use local
        """

        if model.startswith("gpt-"):
            if self.backends["openai"] is None:
                self.backends["openai"] = OpenAIBackend()
            return self.backends["openai"]
        if model.startswith("gemini-"):
            if self.backends["gemini"] is None:
                from app.backends.gemini_backend import GeminiBackend
                self.backends["gemini"] = GeminiBackend()
            return self.backends["gemini"]
        
        return self.backends["local"]