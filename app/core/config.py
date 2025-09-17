from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
from decouple import config


class Settings(BaseSettings):
    PROJECT_NAME: str = "Synctra Backend"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = config("DATABASE_URL")
    REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379")
    
    JWT_SECRET_KEY: str = config("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = config("JWT_ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
    REFRESH_TOKEN_EXPIRE_DAYS: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7, cast=int)
    
    CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    ENVIRONMENT: str = config("ENVIRONMENT", default="development")
    GEOIP_DATABASE_PATH: str = config("GEOIP_DATABASE_PATH", default="./geoip/GeoLite2-City.mmdb")
    
    # OneSignal Configuration
    ONESIGNAL_APP_ID: str = config("ONESIGNAL_APP_ID")
    ONESIGNAL_REST_API_KEY: str = config("ONESIGNAL_REST_API_KEY")
    
    # Frontend URL
    FRONTEND_URL: str = config("FRONTEND_URL", default="https://synctra-admin.vercel.app")
    
    class Config:
        case_sensitive = True


settings = Settings()
