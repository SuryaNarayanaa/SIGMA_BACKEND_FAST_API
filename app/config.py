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

    Configuration:
        - MONGO_URI: Complete MongoDB connection URI (includes database name).
        - SECRET_KEY: Secret key for general signing.
        - JWT_SECRET_KEY: Secret key for JWT token signing.
        - EMAILID: Email ID for notifications or communications.
        - EMAILPS: Email password associated with the email ID.
    """
    # MongoDB connection URI (includes database name)
    MONGO_URI: str

    # Secret key for general signing
    SECRET_KEY: str

    # Secret key for JWT token signing
    JWT_SECRET_KEY: str

    # Email ID for notifications or communications
    EMAILID: str

    # Email password associated with the email ID
    EMAILPS: str

    class Config:
        # Specify the environment file to load variables from
        env_file = ".env"
        extra = "allow"

# Create an instance of Settings
settings = Settings()
