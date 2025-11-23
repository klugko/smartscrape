import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


class Settings:
    def __init__(self) -> None:
        # App
        self.APP_ENV = os.getenv("APP_ENV", "dev")
        self.APP_PORT = int(os.getenv("APP_PORT", "8000"))

        # Postgres
        self.POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
        self.POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "smartscrape_v2")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "abcd")

        # Redis
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # Scraper
        self.SCRAPER_USER_AGENT = os.getenv(
            "SCRAPER_USER_AGENT",
            "SmartScrapeBot/0.1 (+https://example.com)",
        )
        self.SCRAPER_MAX_DEPTH = int(os.getenv("SCRAPER_MAX_DEPTH", "2"))
        self.SCRAPER_REQUEST_DELAY_SECONDS = float(
            os.getenv("SCRAPER_REQUEST_DELAY_SECONDS", "1.0")
        )
        self.SCRAPER_REQUEST_TIMEOUT_SECONDS = float(
            os.getenv("SCRAPER_REQUEST_TIMEOUT_SECONDS", "15.0")
        )
        self.SCRAPER_MAX_PAGES_PER_DOMAIN = int(
            os.getenv("SCRAPER_MAX_PAGES_PER_DOMAIN", "60")
        )

        # OpenAI / LLM
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.OPENAI_ENABLE = os.getenv("OPENAI_ENABLE", "1") == "1"
        self.OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "600"))
        self.LLM_MAX_CHARS = int(os.getenv("LLM_MAX_CHARS", "20000"))

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
