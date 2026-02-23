from app.backends.base import InferenceBackend
import asyncio

class LocalBackend(InferenceBackend):
    async def predict(
            self, 
            prompt: str,
            model: str, 
            temperature: float,
            max_tokens: int
    ) -> str:
        
        await asyncio.sleep(0.2)

        return f"[local: {model}] processed: {prompt}"