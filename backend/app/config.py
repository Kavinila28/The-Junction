"""Application configuration for THE JUNCTION backend.

Settings are loaded from environment variables and a local .env file
(if present). No API keys are required anywhere in this project.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root: backend/
BASE_DIR = Path(__file__).resolve().parent.parent
# Repository root: THE-JUNCTION/
REPO_ROOT = BASE_DIR.parent
DATA_DIR = REPO_ROOT / "data"

UPLOAD_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"
MODEL_DIR = DATA_DIR / "models"
DB_DIR = DATA_DIR / "db"
SAMPLES_DIR = DATA_DIR / "samples"


class Settings(BaseSettings):
    """Runtime configuration, overridable via environment variables."""

    app_name: str = "THE JUNCTION API"
    app_version: str = "0.1.0"
    environment: str = "development"

    host: str = "127.0.0.1"
    port: int = 8000

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    upload_dir: Path = UPLOAD_DIR
    results_dir: Path = RESULTS_DIR
    model_dir: Path = MODEL_DIR
    db_dir: Path = DB_DIR
    db_path: Path = DB_DIR / "junction.db"

    # Detection / analysis tuning
    model_name: str = "yolov8n.pt"
    model_path: Path = MODEL_DIR / "yolov8n.pt"
    conf_threshold: float = 0.25
    iou_threshold: float = 0.45
    imgsz: int = 640
    max_upload_mb: int = 200

    # Junction-relevant COCO classes: person, bicycle, car, motorcycle, bus, truck
    junction_classes: list[int] = [0, 1, 2, 3, 5, 7]

    sample_video: Path = SAMPLES_DIR / "traffic_sample.mp4"

    model_config = SettingsConfigDict(
        env_file=str(UPLOAD_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_dirs(self) -> None:
        """Create all data directories this service needs."""
        for path in (self.upload_dir, self.results_dir, self.model_dir, self.db_dir, SAMPLES_DIR):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()