from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ShotForge"
    storage_root: Path = Path("data")
    runs_dir: Path = Path("data/runs")
    versions_dir: Path = Path("data/versions")
    knowledge_base_path: Path = Path("data/knowledge_base.json")
    memory_store_path: Path = Path("data/memory.jsonl")
    default_duration_seconds: int = 24

    model_config = SettingsConfigDict(env_prefix="SHOTFORGE_", env_file=".env")

    def ensure_dirs(self) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
