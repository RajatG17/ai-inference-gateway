import os
from app.backends.dummy import DummyBackend
from app.backends.base import InferenceBackend

def get_backend() -> InferenceBackend:
    backend_type = os.getenv("INFERENCE_BACKEND", "dummy")

    if backend_type == "dummy":
        return DummyBackend()
    
    raise ValueError(f"Unsupported backend type: {backend_type}")
