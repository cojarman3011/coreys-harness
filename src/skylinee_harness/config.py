from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SKYLINEE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Corey's Harness"
    ollama_base_url: str = "http://127.0.0.1:11434"
    api_key: str = ""
    model_general: str = "qwen2.5:1.5b"
    model_code: str = "deepseek-coder:1.3b"
    model_security: str = "qwen2.5:1.5b"
    request_timeout_seconds: float = Field(default=180, gt=0)
    audit_log_path: Path = Path("data/audit.jsonl")
    log_prompt_content: bool = False

    @property
    def model_map(self) -> dict[str, str]:
        return {
            "general": self.model_general,
            "code": self.model_code,
            "security": self.model_security,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
