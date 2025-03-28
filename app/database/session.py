from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings, logger

class Database:
    client: AsyncIOMotorClient = None
    db = None

async def connect_to_mongo():
    """Create database connection."""
    logger.info("Connecting to MongoDB Atlas...")
    Database.client = AsyncIOMotorClient(settings.MONGODB_URI)
    Database.db = Database.client[settings.DB_NAME]
    logger.info("Connected to MongoDB Atlas.")

async def close_mongo_connection():
    """Close database connection."""
    if Database.client:
        logger.info("Closing MongoDB connection...")
        Database.client.close()
        logger.info("MongoDB connection closed.")

def get_db():
    """Get database instance."""
    return Database.db

def get_collection(collection_name: str):
    """Get a specific collection from the database."""
    return Database.db[collection_name]
