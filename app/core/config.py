from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets

class Settings(BaseSettings):
    PROJECT_NAME: str = "Synctra"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    DATABASE_URL: str = "sqlite:///./synctra.db"
    REDIS_URL: str = "redis://localhost:6379"
    
    ALLOWED_HOSTS: List[str] = ["*"]
    DEBUG: bool = True
    
    BCRYPT_ROUNDS: int = 12
    
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_PER_SECOND: int = 10
    
    # Stockage local pour les fichiers
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    DOMAIN: str = "synctra.link"
    
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
