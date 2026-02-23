import os
from openai import AsyncOpenAI
from app.backends.base import InferenceBackend

class OpenAIBackend(InferenceBackend):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        self.client = AsyncOpenAI(api_key=api_key)

    async def predict(
            self,
            prompt: str,
            model: str,
            temperature: float,
            max_tokens: int
    ) -> str:
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )

        return str(response.choices[0].message.content)
    