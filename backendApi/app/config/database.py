import os
from pymongo import AsyncMongoClient
from beanie import init_beanie
import logging

from app.models.interface.dataset_interface import FileDataset

logger = logging.getLogger(__name__)

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
            
            self.client = AsyncMongoClient(mongodb_url)
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