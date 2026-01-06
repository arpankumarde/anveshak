"""Pattern recognition agent for identifying known error signatures and failure modes."""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from db import db_manager

logger = logging.getLogger(__name__)

class PatternRecognitionAgent:
    """Agent for recognizing known error patterns and failure modes."""
    
    def __init__(self):
        """Initialize pattern recognition agent with known patterns."""
        self.patterns = self._load_patterns()
        self.learned_patterns: List[Dict[str, Any]] = []
        self._load_learned_patterns()
    
    def _load_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load built-in error patterns."""
        return {
            'database': [
                {
                    'name': 'Connection Timeout',
                    'pattern': r'connection.*timeout|timeout.*connection|unable to connect',
                    'severity': 7,
                    'category': 'database',
                    'description': 'Database connection timeout'
                },
                {
                    'name': 'Connection Pool Exhausted',
                    'pattern': r'connection pool.*exhausted|no available connections|too many connections',
                    'severity': 8,
                    'category': 'database',
                    'description': 'Database connection pool exhausted'
                },
                {
                    'name': 'Deadlock',
                    'pattern': r'deadlock|deadlock detected|transaction.*deadlock',
                    'severity': 8,
                    'category': 'database',
                    'description': 'Database deadlock detected'
                },
                {
                    'name': 'Query Timeout',
                    'pattern': r'query.*timeout|slow query|query.*exceeded',
                    'severity': 6,
                    'category': 'database',
                    'description': 'Database query timeout'
                },
            ],
            'memory': [
                {
                    'name': 'Out of Memory',
                    'pattern': r'out of memory|OOM|memory.*exhausted|heap.*space',
                    'severity': 9,
                    'category': 'memory',
                    'description': 'Out of memory error'
                },
                {
                    'name': 'Memory Leak',
                    'pattern': r'memory leak|increasing.*memory|memory.*growing',
                    'severity': 7,
                    'category': 'memory',
                    'description': 'Potential memory leak detected'
                },
            ],
            'network': [
                {
                    'name': 'Connection Refused',
                    'pattern': r'connection refused|refused to connect|ECONNREFUSED',
                    'severity': 7,
                    'category': 'network',
                    'description': 'Network connection refused'
                },
                {
                    'name': 'Network Timeout',
                    'pattern': r'network.*timeout|socket.*timeout|ETIMEDOUT',
                    'severity': 6,
                    'category': 'network',
                    'description': 'Network timeout'
                },
                {
                    'name': 'DNS Resolution Failed',
                    'pattern': r'DNS.*failed|name resolution.*failed|getaddrinfo.*failed',
                    'severity': 7,
                    'category': 'network',
                    'description': 'DNS resolution failed'
                },
            ],
            'authentication': [
                {
                    'name': 'Authentication Failed',
                    'pattern': r'authentication.*failed|auth.*failed|invalid.*credentials|unauthorized',
                    'severity': 6,
                    'category': 'authentication',
                    'description': 'Authentication failure'
                },
                {
                    'name': 'Token Expired',
                    'pattern': r'token.*expired|expired.*token|JWT.*expired',
                    'severity': 5,
                    'category': 'authentication',
                    'description': 'Authentication token expired'
                },
                {
                    'name': 'Rate Limit',
                    'pattern': r'rate limit|too many requests|429|throttled',
                    'severity': 5,
                    'category': 'authentication',
                    'description': 'Rate limit exceeded'
                },
            ],
            'application': [
                {
                    'name': 'Null Pointer Exception',
                    'pattern': r'null.*pointer|NullPointerException|NoneType.*error',
                    'severity': 8,
                    'category': 'application',
                    'description': 'Null pointer exception'
                },
                {
                    'name': 'Stack Overflow',
                    'pattern': r'stack.*overflow|StackOverflowError|recursion.*too deep',
                    'severity': 9,
                    'category': 'application',
                    'description': 'Stack overflow error'
                },
                {
                    'name': 'Index Out of Bounds',
                    'pattern': r'index.*out.*bounds|IndexOutOfBoundsException|array.*index',
                    'severity': 7,
                    'category': 'application',
                    'description': 'Index out of bounds error'
                },
                {
                    'name': 'File Not Found',
                    'pattern': r'file.*not.*found|FileNotFoundException|no such file',
                    'severity': 5,
                    'category': 'application',
                    'description': 'File not found error'
                },
            ],
            'http': [
                {
                    'name': 'HTTP 500',
                    'pattern': r'HTTP.*500|500.*error|internal.*server.*error',
                    'severity': 8,
                    'category': 'http',
                    'description': 'HTTP 500 Internal Server Error'
                },
                {
                    'name': 'HTTP 503',
                    'pattern': r'HTTP.*503|503.*error|service.*unavailable',
                    'severity': 8,
                    'category': 'http',
                    'description': 'HTTP 503 Service Unavailable'
                },
                {
                    'name': 'HTTP 502',
                    'pattern': r'HTTP.*502|502.*error|bad.*gateway',
                    'severity': 7,
                    'category': 'http',
                    'description': 'HTTP 502 Bad Gateway'
                },
                {
                    'name': 'HTTP 404',
                    'pattern': r'HTTP.*404|404.*error|not.*found',
                    'severity': 4,
                    'category': 'http',
                    'description': 'HTTP 404 Not Found'
                },
            ],
            'security': [
                {
                    'name': 'SQL Injection Attempt',
                    'pattern': r'sql.*injection|union.*select|drop.*table|exec.*\(|xp_cmdshell',
                    'severity': 9,
                    'category': 'security',
                    'description': 'Potential SQL injection attempt'
                },
                {
                    'name': 'XSS Attempt',
                    'pattern': r'<script|javascript:|onerror=|onload=',
                    'severity': 8,
                    'category': 'security',
                    'description': 'Potential XSS attempt'
                },
                {
                    'name': 'Path Traversal',
                    'pattern': r'\.\./|\.\.\\|\.\.%2f|\.\.%5c',
                    'severity': 8,
                    'category': 'security',
                    'description': 'Potential path traversal attempt'
                },
            ],
        }
    
    def _load_learned_patterns(self):
        """Load learned patterns from database."""
        try:
            # Load patterns from historical incidents
            # This would query MongoDB for patterns learned from past incidents
            # For now, we'll keep it empty and add patterns as we learn
            pass
        except Exception as e:
            logger.warning(f"Failed to load learned patterns: {e}")
    
    def recognize_patterns(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recognize patterns in a log entry.
        
        Args:
            log_entry: Log entry (can be raw or parsed)
            
        Returns:
            Dict with recognized patterns and matches
        """
        try:
            # Get log message
            log_data = log_entry.get('data', '')
            parsed_fields = log_entry.get('parsed_fields', {})
            
            # Combine all text sources
            text_sources = [
                str(log_data),
                parsed_fields.get('message', ''),
                parsed_fields.get('raw_message', ''),
            ]
            combined_text = ' '.join([s for s in text_sources if s]).lower()
            
            matches = []
            matched_categories = set()
            
            # Check against all pattern categories
            for category, patterns in self.patterns.items():
                for pattern_def in patterns:
                    pattern = pattern_def['pattern']
                    compiled = re.compile(pattern, re.IGNORECASE)
                    
                    if compiled.search(combined_text):
                        match = {
                            'pattern_name': pattern_def['name'],
                            'category': category,
                            'severity': pattern_def['severity'],
                            'description': pattern_def['description'],
                            'matched_text': self._extract_matched_text(compiled, combined_text),
                            'confidence': 0.9  # High confidence for known patterns
                        }
                        matches.append(match)
                        matched_categories.add(category)
            
            # Check learned patterns
            for learned_pattern in self.learned_patterns:
                pattern = learned_pattern.get('pattern')
                if pattern:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    if compiled.search(combined_text):
                        match = {
                            'pattern_name': learned_pattern.get('name', 'Learned Pattern'),
                            'category': learned_pattern.get('category', 'unknown'),
                            'severity': learned_pattern.get('severity', 5),
                            'description': learned_pattern.get('description', ''),
                            'matched_text': self._extract_matched_text(compiled, combined_text),
                            'confidence': learned_pattern.get('confidence', 0.7),
                            'source': 'learned'
                        }
                        matches.append(match)
                        matched_categories.add(learned_pattern.get('category', 'unknown'))
            
            # Calculate overall pattern score
            max_severity = max([m['severity'] for m in matches], default=0)
            pattern_score = max_severity if matches else 0
            
            return {
                'patterns_matched': matches,
                'pattern_count': len(matches),
                'categories': list(matched_categories),
                'pattern_score': pattern_score,
                'has_known_pattern': len(matches) > 0,
                'highest_severity': max_severity
            }
            
        except Exception as e:
            logger.error(f"Error recognizing patterns: {e}")
            return {
                'patterns_matched': [],
                'pattern_count': 0,
                'categories': [],
                'pattern_score': 0,
                'has_known_pattern': False,
                'error': str(e)
            }
    
    def _extract_matched_text(self, pattern: re.Pattern, text: str, context: int = 50) -> str:
        """Extract matched text with context."""
        match = pattern.search(text)
        if match:
            start = max(0, match.start() - context)
            end = min(len(text), match.end() + context)
            return text[start:end].strip()
        return ''
    
    def learn_pattern(self, pattern_def: Dict[str, Any]):
        """
        Learn a new pattern from historical incidents.
        
        Args:
            pattern_def: Pattern definition with name, pattern, category, severity, etc.
        """
        try:
            # Validate pattern
            re.compile(pattern_def['pattern'], re.IGNORECASE)
            
            # Add to learned patterns
            pattern_def['learned_at'] = datetime.utcnow().isoformat()
            pattern_def['confidence'] = pattern_def.get('confidence', 0.7)
            self.learned_patterns.append(pattern_def)
            
            # Store in database for persistence
            try:
                db_manager.db.patterns.insert_one({
                    **pattern_def,
                    'created_at': datetime.utcnow()
                })
            except Exception as e:
                logger.warning(f"Failed to store learned pattern: {e}")
            
            logger.info(f"Learned new pattern: {pattern_def.get('name')}")
            
        except re.error as e:
            logger.error(f"Invalid pattern regex: {e}")
        except Exception as e:
            logger.error(f"Error learning pattern: {e}")
    
    def recognize_batch(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recognize patterns in a batch of log entries."""
        return [self.recognize_patterns(entry) for entry in log_entries]

