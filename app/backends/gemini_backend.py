import os
from google import genai
from app.backends.base import InferenceBackend

class GeminiBackend(InferenceBackend):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        self.client = genai.Client()

    async def predict(
            self,
            prompt: str,
            model: str,
            temperature: float,
            max_tokens: int
    ) -> str:
        try:
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=prompt,
            )
        except Exception as e:
            # log error
            print(f"Gemini API error: {e}")
            raise

        return str(response.text)
