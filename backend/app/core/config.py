from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/waterway_db"
    REDIS_URL: str = "redis://localhost:6379"

    # OSM
    OSM_AREA: str = "Vietnam"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ML Model
    MODEL_PATH: str = "data/eta_model.joblib"

    # Data directory
    DATA_DIR: str = "data"

    # Graph cache file
    GRAPH_CACHE_FILE: str = "data/waterway_graph.pkl"

    # OSM cache file
    OSM_CACHE_FILE: str = "data/osm_waterways.json"

    # App settings
    APP_NAME: str = "Smart Waterway Routing API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Overpass API
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    OVERPASS_TIMEOUT: int = 120

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
