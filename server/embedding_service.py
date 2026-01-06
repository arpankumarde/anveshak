"""Embedding service for semantic similarity search and context retrieval."""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from langchain_openai import OpenAIEmbeddings
from config import OPENAI_API_KEY, OPENAI_BASE_URL
from db import db_manager

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings and finding similar logs."""
    
    def __init__(self):
        """Initialize embedding service."""
        try:
            embedding_kwargs = {
                "api_key": OPENAI_API_KEY,
            }
            if OPENAI_BASE_URL:
                embedding_kwargs["base_url"] = OPENAI_BASE_URL
            
            self.embeddings = OpenAIEmbeddings(**embedding_kwargs)
            self.embedding_cache: Dict[str, np.ndarray] = {}  # Cache for embeddings
            logger.info("Embedding service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            self.embeddings = None
    
    def _get_log_text(self, log_entry: Dict[str, Any]) -> str:
        """Extract text representation of log for embedding."""
        # Combine event and data
        event = str(log_entry.get("event", ""))
        data = str(log_entry.get("data", ""))
        
        # Include parsed fields if available
        parsed = log_entry.get("parsed_fields", {})
        message = parsed.get("message", "")
        log_level = parsed.get("log_level", "")
        service = parsed.get("service", "")
        
        # Build comprehensive text representation
        parts = []
        if log_level:
            parts.append(f"[{log_level}]")
        if service:
            parts.append(f"{service}:")
        if event:
            parts.append(event)
        if message:
            parts.append(message)
        elif data:
            parts.append(data)
        
        return " ".join(parts)
    
    def generate_embedding(self, log_entry: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        Generate embedding for a log entry.
        
        Args:
            log_entry: Log entry to embed
            
        Returns:
            Embedding vector as numpy array, or None on error
        """
        if not self.embeddings:
            return None
        
        try:
            # Create cache key from log content
            log_text = self._get_log_text(log_entry)
            cache_key = f"{log_entry.get('connection_id', '')}:{hash(log_text)}"
            
            # Check cache
            if cache_key in self.embedding_cache:
                return self.embedding_cache[cache_key]
            
            # Generate embedding
            embedding = self.embeddings.embed_query(log_text)
            embedding_array = np.array(embedding, dtype=np.float32)
            
            # Cache it
            self.embedding_cache[cache_key] = embedding_array
            
            return embedding_array
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def find_similar_logs(self, query_log: Dict[str, Any], 
                          limit: int = 5,
                          time_window_hours: int = 1,
                          min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find similar logs using embedding similarity.
        
        Args:
            query_log: Log entry to find similar logs for
            limit: Maximum number of similar logs to return
            time_window_hours: Time window to search within
            min_similarity: Minimum cosine similarity threshold
            
        Returns:
            List of similar log entries with similarity scores
        """
        if not self.embeddings:
            return []
        
        try:
            # Generate embedding for query log
            query_embedding = self.generate_embedding(query_log)
            if query_embedding is None:
                return []
            
            # Get recent logs from database
            time_window = datetime.utcnow() - timedelta(hours=time_window_hours)
            connection_id = query_log.get("connection_id")
            
            query = {
                "created_at": {"$gte": time_window}
            }
            
            # Try processed logs first, fallback to raw logs
            try:
                if connection_id:
                    query["connection_id"] = connection_id
                
                # Get recent processed logs (preferred)
                recent_logs = list(db_manager.db.processed_logs.find(query)
                                 .sort("created_at", -1)
                                 .limit(100))  # Limit search space for performance
                
                # If no processed logs, try raw logs
                if not recent_logs:
                    recent_logs = list(db_manager.db.raw_logs.find(query)
                                     .sort("created_at", -1)
                                     .limit(100))
            except Exception as e:
                logger.warning(f"Error querying logs for similarity: {e}")
                recent_logs = []
            
            if not recent_logs:
                return []
            
            # Calculate similarities
            similarities = []
            for log in recent_logs:
                # Skip the same log
                if str(log.get("_id")) == str(query_log.get("_id", "")):
                    continue
                
                # Generate embedding for this log
                log_embedding = self.generate_embedding(log)
                if log_embedding is None:
                    continue
                
                # Calculate cosine similarity
                similarity = np.dot(query_embedding, log_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(log_embedding)
                )
                
                if similarity >= min_similarity:
                    similarities.append({
                        "log": log,
                        "similarity": float(similarity)
                    })
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar logs: {e}")
            return []
    
    def get_relevant_context(self, log_entry: Dict[str, Any], 
                            max_context_logs: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant context logs using embedding similarity.
        This is smarter than time-based context - it finds semantically similar logs.
        
        Args:
            log_entry: Log entry to get context for
            max_context_logs: Maximum number of context logs to return
            
        Returns:
            List of relevant context logs
        """
        # Find similar logs
        similar_logs = self.find_similar_logs(
            log_entry,
            limit=max_context_logs,
            time_window_hours=2,  # Look back 2 hours
            min_similarity=0.65  # Lower threshold to get more context
        )
        
        # Return just the log entries, sorted by similarity
        return [item["log"] for item in similar_logs]
    
    def batch_generate_embeddings(self, log_entries: List[Dict[str, Any]]) -> List[Optional[np.ndarray]]:
        """
        Generate embeddings for a batch of logs (more efficient).
        
        Args:
            log_entries: List of log entries
            
        Returns:
            List of embeddings (None for failed ones)
        """
        if not self.embeddings:
            return [None] * len(log_entries)
        
        try:
            # Prepare texts
            texts = [self._get_log_text(log) for log in log_entries]
            
            # Generate embeddings in batch
            embeddings = self.embeddings.embed_documents(texts)
            
            # Convert to numpy arrays and cache
            results = []
            for i, embedding in enumerate(embeddings):
                embedding_array = np.array(embedding, dtype=np.float32)
                log_text = texts[i]
                cache_key = f"{log_entries[i].get('connection_id', '')}:{hash(log_text)}"
                self.embedding_cache[cache_key] = embedding_array
                results.append(embedding_array)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {e}")
            return [None] * len(log_entries)
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self.embedding_cache.clear()
        logger.debug("Embedding cache cleared")

# Global embedding service instance
embedding_service = EmbeddingService()

