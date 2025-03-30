from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings, logger

class Database:
    client: AsyncIOMotorClient = None
    db = None

async def list_all_collections():
    """List all collections in the database."""
    if Database.db is None:
        raise Exception("Database connection is not established.")
    collections = await Database.db.list_collection_names()
    logger.info("Collections in database: %s", collections)
    return collections

async def connect_to_mongo():
    """Create database connection."""
    logger.info("Connecting to MongoDB Atlas...")
    Database.client = AsyncIOMotorClient(settings.MONGO_URI)
    # Connect to the default database as specified in the MONGO_URI
    Database.db = Database.client.get_default_database()
    logger.info("Connected to MongoDB Atlas.")
    # await list_all_collections()


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
