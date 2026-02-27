import os
import asyncio
import random

INFERENCE_TIMEOUT_SECONDS = 10
MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 0.5

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # DATABASE_URL from env; dotenv optional for local .env


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return url

