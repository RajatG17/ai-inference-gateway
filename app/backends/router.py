from app.backends.local import LocalBackend
from app.backends.openai_backend import OpenAIBackend
from app.backends.gemini_backend import GeminiBackend
from app.backends.circuit_breaker import CircuitBreaker
from app.metrics import (PROVIDER_FAILURES, PROVIDER_REJECTIONS)
from fastapi import HTTPException

class BackendRouter:
    def __init__(self):
        self.backends = {
            "local": LocalBackend(),
            "openai": None,  # OpenAIBackend will be initialized lazily
            "gemini": None,  # GeminiBackend will be initialized lazily
        }
        self.breakers = {
            "openai": CircuitBreaker(failure_threshold=3, cooldown_seconds=60),
            "gemini": CircuitBreaker(failure_threshold=3, cooldown_seconds=60),
            "local": CircuitBreaker(failure_threshold=5, cooldown_seconds=30),
        }
    
    def get_backend_for_model(self, model: str):
        """
        Strategy:
        - if model starts with "gpt-" use openAI
        - otherwise use local
        """

        if model.startswith("gpt-"):
            provider = "openai"
            fallback = self.backends["local"]
            if self.backends["openai"] is None:
                self.backends["openai"] = OpenAIBackend()
            backend = self.backends["openai"]
        elif model.startswith("gemini-"):
            provider = "gemini"
            fallback = self.backends["local"]
            if self.backends["gemini"] is None:                
                self.backends["gemini"] = GeminiBackend()
            backend = self.backends["gemini"]
        else:
            provider = "local"
            fallback = None
            backend = self.backends["local"]

        breaker = self.breakers[provider]

        if not breaker.allow_request():
            PROVIDER_REJECTIONS.labels(provider=provider).inc()
            raise HTTPException(
                status_code=503, 
                detail=f"{provider} backend temporarily unavailable"
            )
        
        return backend, breaker, provider, fallback
    