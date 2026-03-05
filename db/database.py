"""
Database operations and connection management
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ConfigurationError
import logging
from typing import Optional
from config import (
    MONGO_URI, DATABASE_NAME,
    COLLECTION_MASTER, COLLECTION_ACCOUNTS,
    COLLECTION_LOGS, COLLECTION_CATEGORIES
)
from db.schemas import INDEXES

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
# Keep db logger at INFO so connection success/failure is still visible
logger.setLevel(logging.INFO)


class DatabaseManager:
    """Manages MongoDB connection and database operations"""

    def __init__(self, connection_string: Optional[str] = None):
        """Initialize database connection"""
        self.connection_string = connection_string or MONGO_URI
        self.client: Optional[MongoClient] = None
        self.db = None
        self.is_connected = False

    def connect(self):
        """Establish connection to MongoDB Atlas"""
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50
            )
            self.client.admin.command('ping')
            self.db = self.client[DATABASE_NAME]
            self.is_connected = True
            logger.info(f"Successfully connected to MongoDB Atlas - Database: {DATABASE_NAME}")
            return True
        except OperationFailure as e:
            logger.error(f"MongoDB authentication failed — check username/password in MONGO_URI: {e}")
            self.is_connected = False
            return False
        except ConfigurationError as e:
            logger.error(f"MongoDB URI is malformed — check MONGO_URI format: {e}")
            self.is_connected = False
            return False
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed — check network/URI: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("Disconnected from MongoDB")

    def initialize_collections(self):
        """Create collections and indexes"""
        if not self.is_connected:
            logger.error("Not connected to database")
            return False

        try:
            existing_collections = self.db.list_collection_names()

            collections = [
                COLLECTION_MASTER,
                COLLECTION_ACCOUNTS,
                COLLECTION_LOGS,
                COLLECTION_CATEGORIES
            ]

            for collection_name in collections:
                if collection_name not in existing_collections:
                    self.db.create_collection(collection_name)
                    logger.info(f"Created collection: {collection_name}")

            self._create_indexes()
            logger.info("Collections initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing collections: {e}")
            return False

    def _create_indexes(self):
        """Create indexes for all collections"""
        for collection_name, indexes in INDEXES.items():
            collection = self.db[collection_name]
            for index_spec in indexes:
                try:
                    keys = index_spec['keys']
                    unique = index_spec.get('unique', False)
                    sparse = index_spec.get('sparse', False)
                    collection.create_index(
                        keys,
                        unique=unique,
                        sparse=sparse,
                        background=True
                    )
                    logger.info(f"Created index on {collection_name}: {keys}")
                except Exception as e:
                    logger.warning(f"Index may already exist on {collection_name}: {e}")

    @property
    def master_password(self):
        """Get master password collection"""
        return self.db[COLLECTION_MASTER]

    @property
    def accounts(self):
        """Get accounts collection"""
        return self.db[COLLECTION_ACCOUNTS]

    @property
    def activity_logs(self):
        """Get activity logs collection"""
        return self.db[COLLECTION_LOGS]

    @property
    def categories(self):
        """Get categories collection"""
        return self.db[COLLECTION_CATEGORIES]

    def get_database_stats(self):
        """Get database statistics"""
        if not self.is_connected:
            return None

        stats = {
            'database': DATABASE_NAME,
            'collections': {},
            'total_size': 0
        }

        for collection_name in self.db.list_collection_names():
            col_stats = self.db.command('collstats', collection_name)
            stats['collections'][collection_name] = {
                'count': col_stats.get('count', 0),
                'size': col_stats.get('size', 0),
                'indexes': col_stats.get('nindexes', 0)
            }
            stats['total_size'] += col_stats.get('size', 0)

        return stats

    def health_check(self):
        """Check database health"""
        try:
            if not self.is_connected:
                return {'status': 'disconnected', 'healthy': False}

            self.client.admin.command('ping')
            stats = self.get_database_stats()

            return {
                'status': 'connected',
                'healthy': True,
                'database': DATABASE_NAME,
                'collections': list(stats['collections'].keys()) if stats else []
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'error', 'healthy': False, 'error': str(e)}


# Singleton instance
db_manager = DatabaseManager()


if __name__ == "__main__":
    print("Testing database connection...")

    if db_manager.connect():
        print("✓ Connected successfully")

        if db_manager.initialize_collections():
            print("✓ Collections initialized")

        stats = db_manager.get_database_stats()
        print(f"\nDatabase Statistics:")
        print(f"Database: {stats['database']}")
        print(f"Collections:")
        for col_name, col_stats in stats['collections'].items():
            print(f"  - {col_name}: {col_stats['count']} documents, {col_stats['indexes']} indexes")

        health = db_manager.health_check()
        print(f"\nHealth Check: {health}")

        db_manager.disconnect()
    else:
        print("✗ Connection failed")

