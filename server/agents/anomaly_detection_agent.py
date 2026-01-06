"""Anomaly detection agent using ML models for detecting deviations from normal behavior."""
import logging
import re
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import deque
from db import db_manager

logger = logging.getLogger(__name__)

class AnomalyDetectionAgent:
    """Agent for detecting anomalies using ML models."""
    
    def __init__(self, window_size: int = 1000, contamination: float = 0.1):
        """
        Initialize anomaly detection agent.
        
        Args:
            window_size: Size of sliding window for baseline
            contamination: Expected proportion of anomalies (0.0 to 0.5)
        """
        self.window_size = window_size
        self.contamination = contamination
        self.baselines: Dict[str, deque] = {}  # Per service/component baselines
        self.scalers: Dict[str, StandardScaler] = {}
        self.models: Dict[str, IsolationForest] = {}
        self.feature_history: Dict[str, deque] = {}
    
    def extract_features(self, log_entry: Dict[str, Any]) -> Optional[np.ndarray]:
        """
        Extract numerical features from log entry for anomaly detection.
        
        Args:
            log_entry: Log entry (parsed or raw)
            
        Returns:
            Feature vector as numpy array
        """
        try:
            parsed = log_entry.get('parsed_fields', {})
            raw_data = str(log_entry.get('data', ''))
            
            # Extract features
            features = []
            
            # 1. Message length
            features.append(len(raw_data))
            
            # 2. Log level (encoded)
            log_level = parsed.get('log_level', '').upper()
            level_map = {'TRACE': 0, 'DEBUG': 1, 'INFO': 2, 'WARN': 3, 
                        'WARNING': 3, 'ERROR': 4, 'FATAL': 5, 'CRITICAL': 5}
            features.append(level_map.get(log_level, 2))
            
            # 3. Error code (if present)
            error_code = parsed.get('error_code', '0')
            try:
                features.append(int(error_code))
            except (ValueError, TypeError):
                features.append(0)
            
            # 4. Number of special characters (indicates structured data)
            special_chars = sum(1 for c in raw_data if c in '{}[]():;=')
            features.append(special_chars)
            
            # 5. Number of numbers (indicates metrics/data)
            numbers = sum(1 for c in raw_data if c.isdigit())
            features.append(numbers)
            
            # 6. Contains stack trace indicators
            stack_trace_indicators = ['traceback', 'stack trace', 'at ', 'exception', 'error']
            has_stack = any(indicator in raw_data.lower() for indicator in stack_trace_indicators)
            features.append(1 if has_stack else 0)
            
            # 7. HTTP status code (if present)
            http_status = 0
            http_match = re.search(r'HTTP\s+(\d{3})|(\d{3})\s+error', raw_data, re.IGNORECASE)
            if http_match:
                http_status = int(http_match.group(1) or http_match.group(2))
            features.append(http_status)
            
            # 8. Timestamp features (hour, minute, day of week)
            timestamp = parsed.get('timestamp')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    features.append(dt.hour)
                    features.append(dt.minute)
                    features.append(dt.weekday())
                except (ValueError, AttributeError):
                    features.extend([0, 0, 0])
            else:
                features.extend([0, 0, 0])
            
            # 9. Service identifier hash (normalized)
            service = parsed.get('service', 'unknown')
            service_hash = hash(service) % 1000
            features.append(service_hash)
            
            # 10. Word count
            word_count = len(raw_data.split())
            features.append(word_count)
            
            return np.array(features, dtype=np.float64)
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    def update_baseline(self, service_id: str, features: np.ndarray):
        """Update baseline for a service."""
        if service_id not in self.baselines:
            self.baselines[service_id] = deque(maxlen=self.window_size)
            self.scalers[service_id] = StandardScaler()
            self.feature_history[service_id] = deque(maxlen=self.window_size)
        
        self.feature_history[service_id].append(features)
        
        # Update baseline when we have enough samples
        if len(self.feature_history[service_id]) >= 100:
            # Fit scaler
            feature_array = np.array(list(self.feature_history[service_id]))
            self.scalers[service_id].fit(feature_array)
            
            # Train isolation forest
            scaled_features = self.scalers[service_id].transform(feature_array)
            self.models[service_id] = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100
            )
            self.models[service_id].fit(scaled_features)
    
    def detect_anomaly(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect if log entry is an anomaly.
        
        Args:
            log_entry: Log entry to analyze
            
        Returns:
            Anomaly detection results
        """
        try:
            # Extract features
            features = self.extract_features(log_entry)
            if features is None:
                return {
                    'is_anomaly': False,
                    'anomaly_score': 0.0,
                    'confidence': 0.0,
                    'reason': 'Feature extraction failed'
                }
            
            # Get service identifier
            parsed = log_entry.get('parsed_fields', {})
            service_id = parsed.get('service', 'default')
            connection_id = log_entry.get('connection_id', 'default')
            service_id = f"{connection_id}:{service_id}"
            
            # Update baseline
            self.update_baseline(service_id, features)
            
            # Check if we have enough data for detection
            if service_id not in self.models or len(self.feature_history[service_id]) < 50:
                return {
                    'is_anomaly': False,
                    'anomaly_score': 0.0,
                    'confidence': 0.0,
                    'reason': 'Insufficient baseline data',
                    'baseline_size': len(self.feature_history.get(service_id, []))
                }
            
            # Scale features
            scaled_features = self.scalers[service_id].transform(features.reshape(1, -1))
            
            # Predict anomaly
            prediction = self.models[service_id].predict(scaled_features)
            anomaly_score = self.models[service_id].score_samples(scaled_features)[0]
            
            # Normalize score (lower is more anomalous)
            # Isolation Forest returns negative scores for anomalies
            is_anomaly = prediction[0] == -1
            normalized_score = -anomaly_score  # Invert so higher = more anomalous
            
            # Calculate confidence
            confidence = min(abs(normalized_score) * 2, 1.0)  # Scale to 0-1
            
            return {
                'is_anomaly': is_anomaly,
                'anomaly_score': float(normalized_score),
                'confidence': float(confidence),
                'service_id': service_id,
                'baseline_size': len(self.feature_history[service_id]),
                'features': features.tolist(),
                'reason': 'Statistical anomaly detected' if is_anomaly else 'Normal behavior'
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomaly: {e}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def detect_batch(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in a batch of log entries."""
        results = []
        for entry in log_entries:
            result = self.detect_anomaly(entry)
            results.append(result)
        return results
    
    def get_baseline_stats(self, service_id: str) -> Dict[str, Any]:
        """Get baseline statistics for a service."""
        if service_id not in self.feature_history:
            return {'error': 'No baseline data'}
        
        features = np.array(list(self.feature_history[service_id]))
        return {
            'service_id': service_id,
            'sample_count': len(features),
            'feature_mean': features.mean(axis=0).tolist(),
            'feature_std': features.std(axis=0).tolist(),
            'is_trained': service_id in self.models
        }

