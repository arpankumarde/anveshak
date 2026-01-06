"""Context correlation agent for linking related log entries across distributed services."""
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from db import db_manager

logger = logging.getLogger(__name__)

class ContextCorrelationAgent:
    """Agent for correlating logs with infrastructure events and related incidents."""
    
    def __init__(self, correlation_window_seconds: int = 300):
        """
        Initialize context correlation agent.
        
        Args:
            correlation_window_seconds: Time window for correlating events (default 5 minutes)
        """
        self.correlation_window = timedelta(seconds=correlation_window_seconds)
        self.service_graph: Dict[str, Set[str]] = defaultdict(set)  # Service dependency graph
    
    def correlate_context(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Correlate log entry with related events and context.
        
        Args:
            log_entry: Log entry to correlate
            
        Returns:
            Correlation results with related events
        """
        try:
            parsed = log_entry.get('parsed_fields', {})
            connection_id = log_entry.get('connection_id', '')
            timestamp = log_entry.get('timestamp')
            
            # Parse timestamp
            log_time = None
            if timestamp:
                try:
                    if isinstance(timestamp, (int, float)):
                        log_time = datetime.fromtimestamp(timestamp)
                    else:
                        log_time = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    pass
            
            if not log_time:
                log_time = datetime.utcnow()
            
            # Get correlation window
            window_start = log_time - self.correlation_window
            window_end = log_time + self.correlation_window
            
            correlations = {
                'related_logs': [],
                'related_errors': [],
                'related_crashes': [],
                'infrastructure_events': [],
                'deployment_events': [],
                'service_dependencies': [],
                'correlation_score': 0.0,
                'correlation_count': 0
            }
            
            # 1. Find related logs from same connection/service
            service = parsed.get('service', '')
            if connection_id:
                related_logs = self._find_related_logs(
                    connection_id, service, window_start, window_end, log_time
                )
                correlations['related_logs'] = related_logs
                correlations['correlation_count'] += len(related_logs)
            
            # 2. Find related errors
            if parsed.get('log_level', '').upper() in ['ERROR', 'FATAL', 'CRITICAL']:
                related_errors = self._find_related_errors(
                    connection_id, service, window_start, window_end
                )
                correlations['related_errors'] = related_errors
                correlations['correlation_count'] += len(related_errors)
            
            # 3. Find related crashes
            related_crashes = self._find_related_crashes(
                connection_id, service, window_start, window_end
            )
            correlations['related_crashes'] = related_crashes
            correlations['correlation_count'] += len(related_crashes)
            
            # 4. Find infrastructure events (deployments, config changes)
            # This would integrate with external systems - placeholder for now
            infrastructure_events = self._find_infrastructure_events(
                service, window_start, window_end
            )
            correlations['infrastructure_events'] = infrastructure_events
            correlations['correlation_count'] += len(infrastructure_events)
            
            # 5. Find service dependencies
            dependencies = self._find_service_dependencies(service, connection_id)
            correlations['service_dependencies'] = dependencies
            
            # Calculate correlation score
            correlations['correlation_score'] = self._calculate_correlation_score(correlations)
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error correlating context: {e}")
            return {
                'related_logs': [],
                'related_errors': [],
                'related_crashes': [],
                'correlation_score': 0.0,
                'correlation_count': 0,
                'error': str(e)
            }
    
    def _find_related_logs(self, connection_id: str, service: str, 
                          window_start: datetime, window_end: datetime,
                          log_time: datetime) -> List[Dict[str, Any]]:
        """Find related logs in time window."""
        try:
            query = {
                'connection_id': connection_id,
                'created_at': {
                    '$gte': window_start,
                    '$lte': window_end
                }
            }
            
            if service:
                query['parsed_fields.service'] = service
            
            related = list(db_manager.db.raw_logs.find(query)
                          .sort('created_at', -1)
                          .limit(20))
            
            # Convert to correlation format
            return [{
                'log_id': str(log.get('_id', '')),
                'timestamp': log.get('created_at'),
                'service': log.get('parsed_fields', {}).get('service', ''),
                'log_level': log.get('parsed_fields', {}).get('log_level', ''),
                'time_delta_seconds': abs((log.get('created_at') - log_time).total_seconds())
            } for log in related]
            
        except Exception as e:
            logger.warning(f"Error finding related logs: {e}")
            return []
    
    def _find_related_errors(self, connection_id: str, service: str,
                            window_start: datetime, window_end: datetime) -> List[Dict[str, Any]]:
        """Find related errors in time window."""
        try:
            query = {
                'created_at': {
                    '$gte': window_start,
                    '$lte': window_end
                }
            }
            
            if connection_id:
                # Find errors from same connection or related services
                related_errors = list(db_manager.db.errors.find(query)
                                     .sort('created_at', -1)
                                     .limit(10))
                
                return [{
                    'error_id': str(err.get('_id', '')),
                    'error_type': err.get('error_type', ''),
                    'severity': err.get('severity', 0),
                    'timestamp': err.get('created_at'),
                    'root_cause': err.get('root_cause', '')
                } for err in related_errors]
            
        except Exception as e:
            logger.warning(f"Error finding related errors: {e}")
            return []
    
    def _find_related_crashes(self, connection_id: str, service: str,
                             window_start: datetime, window_end: datetime) -> List[Dict[str, Any]]:
        """Find related crashes in time window."""
        try:
            query = {
                'created_at': {
                    '$gte': window_start,
                    '$lte': window_end
                }
            }
            
            related_crashes = list(db_manager.db.crashes.find(query)
                                  .sort('created_at', -1)
                                  .limit(10))
            
            return [{
                'crash_id': str(crash.get('_id', '')),
                'crash_type': crash.get('crash_type', ''),
                'severity': crash.get('severity', 0),
                'timestamp': crash.get('created_at'),
                'affected_components': crash.get('affected_components', [])
            } for crash in related_crashes]
            
        except Exception as e:
            logger.warning(f"Error finding related crashes: {e}")
            return []
    
    def _find_infrastructure_events(self, service: str,
                                    window_start: datetime, window_end: datetime) -> List[Dict[str, Any]]:
        """Find infrastructure events (deployments, config changes)."""
        # Placeholder - would integrate with deployment systems, config management, etc.
        # For now, check if we have any deployment markers in logs
        try:
            query = {
                'parsed_fields.message': {
                    '$regex': 'deploy|deployment|config.*change|restart|scale',
                    '$options': 'i'
                },
                'created_at': {
                    '$gte': window_start,
                    '$lte': window_end
                }
            }
            
            events = list(db_manager.db.raw_logs.find(query)
                         .sort('created_at', -1)
                         .limit(5))
            
            return [{
                'event_id': str(event.get('_id', '')),
                'event_type': 'deployment' if 'deploy' in str(event.get('data', '')).lower() else 'config_change',
                'timestamp': event.get('created_at'),
                'message': str(event.get('data', ''))[:100]
            } for event in events]
            
        except Exception as e:
            logger.warning(f"Error finding infrastructure events: {e}")
            return []
    
    def _find_service_dependencies(self, service: str, connection_id: str) -> List[str]:
        """Find service dependencies based on historical patterns."""
        # Build service dependency graph from historical logs
        # For now, return empty - would be built from log analysis
        if service in self.service_graph:
            return list(self.service_graph[service])
        return []
    
    def _calculate_correlation_score(self, correlations: Dict[str, Any]) -> float:
        """Calculate overall correlation score."""
        score = 0.0
        
        # Related logs contribute to score
        score += min(len(correlations['related_logs']) * 0.1, 0.5)
        
        # Related errors contribute more
        score += min(len(correlations['related_errors']) * 0.2, 0.6)
        
        # Related crashes contribute significantly
        score += min(len(correlations['related_crashes']) * 0.3, 0.8)
        
        # Infrastructure events contribute
        score += min(len(correlations['infrastructure_events']) * 0.15, 0.4)
        
        return min(score, 1.0)
    
    def correlate_batch(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Correlate a batch of log entries."""
        return [self.correlate_context(entry) for entry in log_entries]
    
    def update_service_graph(self, from_service: str, to_service: str):
        """Update service dependency graph."""
        if from_service and to_service:
            self.service_graph[from_service].add(to_service)

