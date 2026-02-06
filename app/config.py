import os

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
