from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection."""
    logger.info("Connecting to MongoDB")
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongodb.db = mongodb.client[settings.MONGO_DB_NAME]
    logger.info("Connected to MongoDB")

async def close_mongo_connection():
    """Close database connection."""
    logger.info("Closing MongoDB connection")
    if mongodb.client:
        mongodb.client.close()
    logger.info("MongoDB connection closed")

def get_database():
    """Return database instance."""
    return mongodb.db
