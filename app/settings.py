from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://aigw_user:aigw_password@localhost:5432/aigw_db")
    api_key_pepper: str = os.getenv("API_KEY_PEPPER", "change_me_to_a_random_secret_value")

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra = "ignore",
    )
    
settings = Settings()