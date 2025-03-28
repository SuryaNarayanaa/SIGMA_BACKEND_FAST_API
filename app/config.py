import logging
import os
from logging.handlers import RotatingFileHandler

from pydantic_settings import BaseSettings

# Ensure the logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# File handler with rotation
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"), maxBytes=1_000_000, backupCount=5  # 1 MB per file, keep 5 backups
)

# Global logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        file_handler,                # Logs to the `logs/app.log` file
        logging.StreamHandler()      # Logs to the terminal
    ]
)

# Create a logger instance
logger = logging.getLogger("app_logger")


# Settings class that inherits from BaseSettings for environment variable configuration
class Settings(BaseSettings):
    """
    Settings class for application configuration.

    Inherits from:
        BaseSettings (pydantic_settings.BaseSettings): Pydantic BaseSettings class for environment variable management.
    """
    # MongoDB connection URI
    MONGODB_URI: str
    
    # MongoDB database name
    DB_NAME: str
    
    # Secret key for JWT token signing
    SECRET_KEY: str

    # Algorithm used for JWT token encoding/decoding
    ALGORITHM: str = "HS256"

    # Token expiration time in minutes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Refresh Token Secret Key
    REFRESH_SECRET_KEY: str

    # Expiry time for the refresh token
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 40

    class Config:
        # Specify the environment file to load variables from
        env_file = ".env"
        extra = "allow"

# Create an instance of Settings
settings = Settings()
