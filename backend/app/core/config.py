"""
Central app configuration, loaded from environment variables / .env.

Everything that varies between dev/staging/prod or between developers'
machines lives here, not scattered through the codebase.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql://gait_user:gait_pass@localhost:5432/gait_intelligence"
    video_storage_path: str = "./storage/videos"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
