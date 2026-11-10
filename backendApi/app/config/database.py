import os
from pymongo import AsyncMongoClient
from beanie import init_beanie
import logging

from app.models.interface.dataset_interface import FileDataset

logger = logging.getLogger(__name__)


def mongodb_credentials(settings) -> dict:
    """
    MongoDB credentials read from MONGODB_PASSWORD_FILE, passed to the client separately from
    MONGODB_URL so that the password is neither in the configuration nor in the logs.

    Returns:
        dict: {"username", "password"} or {} when MONGODB_PASSWORD_FILE is not set

    Raises:
        RuntimeError: If the file is missing, unreadable or empty, or MONGODB_USERNAME is not set
    """
    if not settings.mongodb_password_file:
        return {}
    if not settings.mongodb_username:
        raise RuntimeError("MONGODB_USERNAME must be set when MONGODB_PASSWORD_FILE is set")
    try:
        with open(settings.mongodb_password_file, encoding="utf-8") as f:
            password = f.read().strip()
    except OSError as e:
        raise RuntimeError(f"Cannot read the MongoDB password from {settings.mongodb_password_file} ({e.strerror})") from e
    if not password:
        raise RuntimeError(f"The MongoDB password file {settings.mongodb_password_file} is empty")
    return {"username": settings.mongodb_username, "password": password}


class DatabaseConfig:
    def __init__(self):
        self.client = None
        self.database = None
    
    async def connect(self, settings, models):
        """Connect to MongoDB and initialize Beanie using settings"""
        try:
            # MongoDB connection using settings (plus besoin d'os.getenv)
            mongodb_url = settings.mongodb_url
            database_name = settings.database_name
            
            logger.info(f"Connecting to MongoDB: {database_name}")
            logger.debug(f"MongoDB URL: {mongodb_url}")

            self.client = AsyncMongoClient(mongodb_url, **mongodb_credentials(settings))
            self.database = self.client[database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("MongoDB ping successful")
            
            # Initialize Beanie with models
            await init_beanie(database=self.database, document_models=models)
            
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}", exc_info=True)
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

# Global instance
db_config = DatabaseConfig()