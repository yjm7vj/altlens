"""Runtime configuration read from the environment.

Everything has a working default so the demo runs with no setup at all:
no API key, no database, no `.env` file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _split_env_list(name: str, default: tuple[str, ...]) -> list[str]:
    raw = os.getenv(name)

    if not raw:
        return list(default)

    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str | None = None
    cors_origins: list[str] = field(default_factory=lambda: list(DEFAULT_CORS_ORIGINS))
    model_provider: str = "rule_based"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    request_timeout_seconds: float = 30.0


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv("ALTLENS_DATABASE_URL") or os.getenv("DATABASE_URL"),
        cors_origins=_split_env_list("ALTLENS_CORS_ORIGINS", DEFAULT_CORS_ORIGINS),
        model_provider=os.getenv("ALTLENS_MODEL_PROVIDER", "rule_based"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("ALTLENS_OPENAI_MODEL", "gpt-4o-mini"),
        openai_base_url=os.getenv(
            "ALTLENS_OPENAI_BASE_URL", "https://api.openai.com/v1"
        ),
        ollama_base_url=os.getenv("ALTLENS_OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("ALTLENS_OLLAMA_MODEL", "llama3.1"),
        request_timeout_seconds=float(
            os.getenv("ALTLENS_REQUEST_TIMEOUT_SECONDS", "30")
        ),
    )


settings = load_settings()
