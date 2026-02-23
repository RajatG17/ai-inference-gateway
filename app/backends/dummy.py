from app.backends.base import InferenceBackend

class DummyBackend(InferenceBackend):
    async def predict(self, prompt: str, model: str, temperature: float, max_tokens: int):
        return f"Dummy response for prompt: {prompt}, model: {model}, temperature: {temperature}, max_tokens: {max_tokens}"