from abc import ABC, abstractmethod

class InferenceBackend(ABC):
    @abstractmethod
    async def predict(
        self,
        prompt:str,
        model:str,
        temperature: float,
        max_tokens: int,
        ) -> str:
        pass
    