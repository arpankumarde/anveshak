"""Parser agent for structuring unstructured logs into standardized formats."""
import re
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

class ParserAgent:
    """Agent for parsing and structuring log entries."""
    
    # Common log level patterns
    LOG_LEVELS = {
        'TRACE', 'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL',
        'PANIC', 'ALERT', 'EMERGENCY', 'NOTICE', 'VERBOSE'
    }
    
    # Common timestamp patterns
    TIMESTAMP_PATTERNS = [
        r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?',  # ISO 8601
        r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}',  # YYYY/MM/DD HH:MM:SS
        r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',  # MM/DD/YYYY HH:MM:SS
        r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]',  # [YYYY-MM-DD HH:MM:SS]
        r'(\w{3} \d{1,2}, \d{4} \d{2}:\d{2}:\d{2})',  # Mon DD, YYYY HH:MM:SS
    ]
    
    # Common service/component patterns
    SERVICE_PATTERNS = [
        r'\[([A-Za-z0-9_-]+)\]',  # [ServiceName]
        r'(\w+):',  # ServiceName:
        r'<(\w+)>',  # <ServiceName>
    ]
    
    # Common error code patterns
    ERROR_CODE_PATTERNS = [
        r'Error\s+(\d+)',
        r'ErrorCode:\s*(\d+)',
        r'Code:\s*(\d+)',
        r'HTTP\s+(\d{3})',
        r'Status:\s*(\d{3})',
        r'Exception\s+(\w+)',
    ]
    
    # Common thread/process patterns
    THREAD_PATTERNS = [
        r'\[([A-Za-z0-9_-]+-\d+)\]',  # [ThreadName-123]
        r'Thread\[([^\]]+)\]',
        r'PID:\s*(\d+)',
    ]
    
    def __init__(self):
        """Initialize the parser agent."""
        self.compiled_patterns = {
            'timestamp': [re.compile(p, re.IGNORECASE) for p in self.TIMESTAMP_PATTERNS],
            'service': [re.compile(p) for p in self.SERVICE_PATTERNS],
            'error_code': [re.compile(p, re.IGNORECASE) for p in self.ERROR_CODE_PATTERNS],
            'thread': [re.compile(p) for p in self.THREAD_PATTERNS],
        }
    
    def parse_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a log entry into structured format.
        
        Args:
            log_entry: Raw log entry with 'event', 'data', 'timestamp'
            
        Returns:
            Structured log entry with parsed fields
        """
        try:
            # Get raw log data
            raw_data = str(log_entry.get('data', ''))
            event = str(log_entry.get('event', ''))
            raw_timestamp = log_entry.get('timestamp')
            
            # Initialize structured output
            structured = {
                'original': log_entry,
                'raw_message': raw_data,
                'event': event,
                'parsed_fields': {},
                'parse_confidence': 0.0,
                'format_type': 'unknown'
            }
            
            # Try to parse as JSON first
            json_parsed = self._try_parse_json(raw_data)
            if json_parsed:
                structured['format_type'] = 'json'
                structured['parsed_fields'] = json_parsed
                structured['parse_confidence'] = 0.9
                return structured
            
            # Try to parse as syslog format
            syslog_parsed = self._try_parse_syslog(raw_data)
            if syslog_parsed:
                structured['format_type'] = 'syslog'
                structured['parsed_fields'].update(syslog_parsed)
                structured['parse_confidence'] = 0.8
                return structured
            
            # Try to parse as common application log format
            app_log_parsed = self._try_parse_app_log(raw_data)
            if app_log_parsed:
                structured['format_type'] = 'application'
                structured['parsed_fields'].update(app_log_parsed)
                structured['parse_confidence'] = 0.7
                return structured
            
            # Fallback: extract what we can
            structured['format_type'] = 'unstructured'
            structured['parsed_fields'] = self._extract_common_fields(raw_data)
            structured['parse_confidence'] = 0.5
            
            return structured
            
        except Exception as e:
            logger.error(f"Error parsing log entry: {e}")
            return {
                'original': log_entry,
                'raw_message': str(log_entry.get('data', '')),
                'event': str(log_entry.get('event', '')),
                'parsed_fields': {},
                'parse_confidence': 0.0,
                'format_type': 'error',
                'parse_error': str(e)
            }
    
    def _try_parse_json(self, data: str) -> Optional[Dict[str, Any]]:
        """Try to parse as JSON."""
        try:
            # Try direct JSON parse
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                return parsed
            
            # Try extracting JSON from string
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', data)
            if json_match:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, dict):
                    return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        return None
    
    def _try_parse_syslog(self, data: str) -> Optional[Dict[str, Any]]:
        """Try to parse as syslog format."""
        # Syslog format: <PRI>TIMESTAMP HOSTNAME TAG: MESSAGE
        syslog_pattern = r'<(\d+)>(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+):\s*(.*)'
        match = re.match(syslog_pattern, data)
        if match:
            return {
                'priority': int(match.group(1)),
                'timestamp': match.group(2),
                'hostname': match.group(3),
                'tag': match.group(4),
                'message': match.group(5),
                'log_level': self._extract_log_level(match.group(5))
            }
        return None
    
    def _try_parse_app_log(self, data: str) -> Optional[Dict[str, Any]]:
        """Try to parse as common application log format."""
        parsed = {}
        
        # Try to extract timestamp
        timestamp = self._extract_timestamp(data)
        if timestamp:
            parsed['timestamp'] = timestamp
        
        # Try to extract log level
        log_level = self._extract_log_level(data)
        if log_level:
            parsed['log_level'] = log_level
        
        # Try to extract service/component
        service = self._extract_service(data)
        if service:
            parsed['service'] = service
        
        # Try to extract error code
        error_code = self._extract_error_code(data)
        if error_code:
            parsed['error_code'] = error_code
        
        # Try to extract thread/process
        thread = self._extract_thread(data)
        if thread:
            parsed['thread'] = thread
        
        # Extract message (remaining text)
        message = self._extract_message(data)
        if message:
            parsed['message'] = message
        
        return parsed if parsed else None
    
    def _extract_common_fields(self, data: str) -> Dict[str, Any]:
        """Extract common fields from unstructured log."""
        fields = {}
        
        # Extract log level
        log_level = self._extract_log_level(data)
        if log_level:
            fields['log_level'] = log_level
        
        # Extract timestamp
        timestamp = self._extract_timestamp(data)
        if timestamp:
            fields['timestamp'] = timestamp
        
        # Extract service
        service = self._extract_service(data)
        if service:
            fields['service'] = service
        
        # Extract error code
        error_code = self._extract_error_code(data)
        if error_code:
            fields['error_code'] = error_code
        
        # Extract message
        message = self._extract_message(data)
        if message:
            fields['message'] = message
        
        return fields
    
    def _extract_timestamp(self, data: str) -> Optional[str]:
        """Extract timestamp from log data."""
        for pattern in self.compiled_patterns['timestamp']:
            match = pattern.search(data)
            if match:
                try:
                    # Try to parse and normalize
                    ts_str = match.group(0)
                    dt = date_parser.parse(ts_str, fuzzy=True)
                    return dt.isoformat()
                except (ValueError, AttributeError):
                    return ts_str
        return None
    
    def _extract_log_level(self, data: str) -> Optional[str]:
        """Extract log level from data."""
        data_upper = data.upper()
        for level in self.LOG_LEVELS:
            # Look for standalone log level (not part of another word)
            pattern = r'\b' + re.escape(level) + r'\b'
            if re.search(pattern, data_upper):
                return level
        return None
    
    def _extract_service(self, data: str) -> Optional[str]:
        """Extract service/component name."""
        for pattern in self.compiled_patterns['service']:
            match = pattern.search(data)
            if match:
                return match.group(1)
        return None
    
    def _extract_error_code(self, data: str) -> Optional[str]:
        """Extract error code."""
        for pattern in self.compiled_patterns['error_code']:
            match = pattern.search(data)
            if match:
                return match.group(1)
        return None
    
    def _extract_thread(self, data: str) -> Optional[str]:
        """Extract thread/process identifier."""
        for pattern in self.compiled_patterns['thread']:
            match = pattern.search(data)
            if match:
                return match.group(1)
        return None
    
    def _extract_message(self, data: str) -> str:
        """Extract the main message content."""
        # Remove common prefixes
        message = data
        
        # Remove timestamp if present
        for pattern in self.compiled_patterns['timestamp']:
            message = pattern.sub('', message)
        
        # Remove log level
        for level in self.LOG_LEVELS:
            message = re.sub(r'\b' + re.escape(level) + r'\b', '', message, flags=re.IGNORECASE)
        
        # Remove service tags
        for pattern in self.compiled_patterns['service']:
            message = pattern.sub('', message)
        
        # Clean up whitespace
        message = re.sub(r'\s+', ' ', message).strip()
        
        return message if message else data
    
    def parse_batch(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse a batch of log entries."""
        return [self.parse_log(entry) for entry in log_entries]

