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

    # Guards against OOM / runaway processing time on constrained hosting
    # (e.g. Render's free tier: 0.1 vCPU, 512MB RAM). MediaPipe extraction
    # holds every frame's landmarks in memory and is CPU-bound per frame,
    # so a long video on a slow/small instance can exhaust either. Raise
    # this once running on hardware that can actually handle longer clips.
    max_pose_extraction_frames: int = 300  # ~10s at 30fps

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
