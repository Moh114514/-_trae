from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
from pydantic import field_validator


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE_PATH = (BACKEND_DIR / "beims.db").as_posix()


class Settings(BaseSettings):
    APP_NAME: str = "BEIMS建筑能源智能管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    
    DATABASE_URL: str = f"sqlite:///{DEFAULT_SQLITE_PATH}"
    ENERGY_TABLE_NAME: str = "energy_data"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    FORCE_POSTGRESQL: bool = False
    STATS_DEBUG: bool = True
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None

    ASSISTANT_PROXY_ENABLED: bool = True
    ASSISTANT_BASE_URL: str = "http://localhost:8082"
    ASSISTANT_PROXY_TIMEOUT: float = 45.0
    ASSISTANT_FALLBACK_LOCAL: bool = True
    
    RAGFLOW_API_URL: str = "http://localhost:9380"
    RAGFLOW_API_KEY: Optional[str] = None
    
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 8001
    
    UPLOAD_DIR: str = "uploads"
    EXPORT_DIR: str = "exports"
    KNOWLEDGE_BASE_DIR: str = "knowledge_base"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_sqlite_path(cls, value):
        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        if value.startswith("sqlite:///./"):
            relative_path = value[len("sqlite:///./"):]
            absolute_path = (BACKEND_DIR / relative_path).resolve().as_posix()
            return f"sqlite:///{absolute_path}"
        return value
    
    class Config:
        env_file = str(BACKEND_DIR / ".env")
        case_sensitive = True


settings = Settings()
