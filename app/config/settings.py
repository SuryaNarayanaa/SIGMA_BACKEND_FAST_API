import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API config
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SIGMA API"
    PROJECT_DESCRIPTION: str = "Backend API for SIGMA project"
    PROJECT_VERSION: str = "0.1.0"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "sigma_db")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "supersecretkey")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
