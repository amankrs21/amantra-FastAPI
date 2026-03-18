from __future__ import annotations

from pydantic import Field
from dotenv import load_dotenv
from functools import lru_cache
from typing import ClassVar
from pydantic_settings import BaseSettings

load_dotenv()  # Load environment variables from .env file


# Configuration settings
class AppConfig(BaseSettings):
    # Application settings
    APP_VERSION: ClassVar[str] = "1.1.0"
    APP_NAME: ClassVar[str] = "Amantra FastAPI Backend"
    APP_DESC: ClassVar[str] = (
        "FastAPI backend for Amantra app - vault, journal, watchlist, newsletter features with Google OAuth and AI integration."
    )

    # ROOT_PATH and CORS settings
    ROOT_PATH: str = Field(default="", alias="ROOT_PATH")
    CORS_ORIGINS: str = Field(default="", alias="CORS_ORIGINS")

    # MongoDB, JWT, and password settings
    MONGO_URL: str = Field(default=None, alias="MONGO_URL")
    JWT_SECRET: str = Field(default=None, alias="JWT_SECRET")
    PASSWORD_KEY: str = Field(default=None, alias="PASSWORD_KEY")

    # Tavily and Mistral API keys
    TAVILY_API_KEY: str = Field(default=None, alias="TAVILY_API_KEY")
    MISTRAL_API_KEY: str = Field(default=None, alias="MISTRAL_API_KEY")

    # Google OAuth
    GOOGLE_CLIENT_IDS: str = Field(default="", alias="GOOGLE_CLIENT_IDS")

    # Email settings (Brevo)
    BREVO_API_KEY: str = Field(default="", alias="BREVO_API_KEY")
    SMTP_EMAIL: str = Field(default="", alias="SMTP_EMAIL")

    @property
    def google_client_ids(self) -> list[str]:
        return [cid.strip() for cid in self.GOOGLE_CLIENT_IDS.split(",") if cid.strip()]


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()


config = get_config()
