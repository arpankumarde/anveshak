"""MongoDB connection and database operations."""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
from config import MONGO_URI, MONGO_DB_NAME

logger = logging.getLogger(__name__)

class MongoDBManager:
    """Manages MongoDB connections and operations."""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self._connected = False
        try:
            self._connect()
        except Exception as e:
            logger.warning(f"MongoDB connection failed at initialization: {e}. Will retry on first use.")
            self._connected = False
    
    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[MONGO_DB_NAME]
            
            # Create collections and indexes
            self._setup_collections()
            self._connected = True
            logger.info(f"Connected to MongoDB: {MONGO_DB_NAME}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._connected = False
            raise
    
    def _ensure_connected(self):
        """Ensure MongoDB connection is established."""
        if not self._connected:
            try:
                self._connect()
            except Exception as e:
                logger.error(f"Failed to reconnect to MongoDB: {e}")
                raise
    
    def _setup_collections(self):
        """Create collections and indexes."""
        # Raw logs collection
        raw_logs = self.db.raw_logs
        raw_logs.create_index([("timestamp", -1)])
        raw_logs.create_index([("connection_id", 1)])
        raw_logs.create_index([("processed", 1)])
        
        # Processed logs collection
        processed_logs = self.db.processed_logs
        processed_logs.create_index([("timestamp", -1)])
        processed_logs.create_index([("severity", -1)])
        processed_logs.create_index([("cluster_type", 1)])
        processed_logs.create_index([("is_crash", 1)])
        processed_logs.create_index([("connection_id", 1)])
        
        # Clusters collection
        clusters = self.db.clusters
        clusters.create_index([("cluster_type", 1)])
        clusters.create_index([("created_at", -1)])
        
        # Errors collection
        errors = self.db.errors
        errors.create_index([("timestamp", -1)])
        errors.create_index([("severity", -1)])
        errors.create_index([("resolved", 1)])
        
        # Crashes collection
        crashes = self.db.crashes
        crashes.create_index([("timestamp", -1)])
        crashes.create_index([("severity", -1)])
        crashes.create_index([("resolved", 1)])
        
        # Insights collection
        insights = self.db.insights
        insights.create_index([("created_at", -1)])
        insights.create_index([("insight_type", 1)])
        
        # Patterns collection (for learned patterns)
        patterns = self.db.patterns
        patterns.create_index([("category", 1)])
        patterns.create_index([("created_at", -1)])
        patterns.create_index([("pattern", 1)])
    
    def insert_raw_log(self, log_data: Dict[str, Any]) -> str:
        """Insert a raw log entry."""
        self._ensure_connected()
        log_entry = {
            **log_data,
            "processed": False,
            "created_at": datetime.utcnow()
        }
        result = self.db.raw_logs.insert_one(log_entry)
        return str(result.inserted_id)
    
    def insert_processed_log(self, processed_data: Dict[str, Any]) -> str:
        """Insert a processed log entry."""
        self._ensure_connected()
        processed_entry = {
            **processed_data,
            "created_at": datetime.utcnow()
        }
        result = self.db.processed_logs.insert_one(processed_entry)
        return str(result.inserted_id)
    
    def mark_logs_processed(self, log_ids: List[str]):
        """Mark logs as processed."""
        self._ensure_connected()
        # Convert string IDs to ObjectId
        object_ids = []
        for log_id in log_ids:
            try:
                if isinstance(log_id, str):
                    object_ids.append(ObjectId(log_id))
                else:
                    object_ids.append(log_id)
            except Exception:
                # Skip invalid IDs
                continue
        
        if object_ids:
            self.db.raw_logs.update_many(
                {"_id": {"$in": object_ids}},
                {"$set": {"processed": True, "processed_at": datetime.utcnow()}}
            )
    
    def get_context_logs(self, connection_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent logs from a specific connection for context."""
        self._ensure_connected()
        return list(self.db.raw_logs.find({
            "connection_id": connection_id
        }).sort("timestamp", -1).limit(limit))
    
    def get_unprocessed_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get unprocessed logs."""
        self._ensure_connected()
        return list(self.db.raw_logs.find({"processed": False}).limit(limit))
    
    def insert_cluster(self, cluster_data: Dict[str, Any]) -> str:
        """Insert a cluster entry."""
        self._ensure_connected()
        cluster_entry = {
            **cluster_data,
            "created_at": datetime.utcnow()
        }
        result = self.db.clusters.insert_one(cluster_entry)
        return str(result.inserted_id)
    
    def insert_error(self, error_data: Dict[str, Any]) -> str:
        """Insert an error entry."""
        self._ensure_connected()
        error_entry = {
            **error_data,
            "resolved": False,
            "created_at": datetime.utcnow()
        }
        result = self.db.errors.insert_one(error_entry)
        return str(result.inserted_id)
    
    def insert_crash(self, crash_data: Dict[str, Any]) -> str:
        """Insert a crash entry."""
        self._ensure_connected()
        crash_entry = {
            **crash_data,
            "resolved": False,
            "created_at": datetime.utcnow()
        }
        result = self.db.crashes.insert_one(crash_entry)
        return str(result.inserted_id)
    
    def insert_insight(self, insight_data: Dict[str, Any]) -> str:
        """Insert an insight entry."""
        self._ensure_connected()
        insight_entry = {
            **insight_data,
            "created_at": datetime.utcnow()
        }
        result = self.db.insights.insert_one(insight_entry)
        return str(result.inserted_id)
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global MongoDB manager instance
db_manager = MongoDBManager()

