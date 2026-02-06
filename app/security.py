import hashlib
import hmac
from app.settings import settings

def _pepper():
    return getattr(settings, "api_key_pepper", "dev-pepper-change-me").encode("utf-8")

def hash_api_key(api_key: str):
    return hmac.new(_pepper(), api_key.encode("utf-8"), hashlib.sha256).hexdigest()