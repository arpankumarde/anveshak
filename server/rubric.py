"""Severity rubric for log analysis and crash detection."""
from typing import Dict, Any, List
import re
from datetime import datetime

class SeverityRubric:
    """Calculates severity scores for logs based on various factors."""
    
    # Keywords that indicate high severity
    CRITICAL_KEYWORDS = [
        "crash", "fatal", "critical", "panic", "abort", "segmentation fault",
        "out of memory", "stack overflow", "null pointer", "access violation",
        "kernel panic", "system halt", "data corruption", "database down"
    ]
    
    ERROR_KEYWORDS = [
        "error", "exception", "failed", "failure", "timeout", "connection refused",
        "unauthorized", "forbidden", "not found", "internal server error",
        "bad request", "service unavailable", "gateway timeout"
    ]
    
    WARNING_KEYWORDS = [
        "warning", "warn", "deprecated", "slow", "retry", "fallback",
        "degraded", "throttled", "rate limit"
    ]
    
    # PII patterns
    PII_PATTERNS = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{16}\b',  # Credit card
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}-\d{3}-\d{4}\b',  # Phone
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP (can be PII in some contexts)
    ]
    
    def calculate_severity(self, log_entry: Dict[str, Any]) -> int:
        """
        Calculate severity score (0-10) for a log entry.
        
        Returns:
            int: Severity score from 0 (lowest) to 10 (highest)
        """
        severity = 0
        log_text = str(log_entry.get('data', '')).lower()
        event = str(log_entry.get('event', '')).lower()
        
        # Check for critical keywords (adds 4-6 points)
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in log_text or keyword in event:
                severity += 5
                break
        
        # Check for error keywords (adds 2-3 points)
        if severity < 5:  # Don't double count if already critical
            for keyword in self.ERROR_KEYWORDS:
                if keyword in log_text or keyword in event:
                    severity += 3
                    break
        
        # Check for warning keywords (adds 1 point)
        if severity < 3:
            for keyword in self.WARNING_KEYWORDS:
                if keyword in log_text or keyword in event:
                    severity += 1
                    break
        
        # Check for stack traces (adds 2 points)
        if 'traceback' in log_text or 'stack trace' in log_text or 'at ' in log_text:
            severity += 2
        
        # Check for HTTP error codes (adds 1-3 points)
        http_codes = re.findall(r'\b(4\d{2}|5\d{2})\b', log_text)
        if http_codes:
            for code in http_codes:
                code_int = int(code)
                if code_int >= 500:
                    severity += 3
                elif code_int >= 400:
                    severity += 2
        
        # Check for repeated errors (adds 1 point)
        if log_entry.get('repeat_count', 0) > 5:
            severity += 1
        
        # Cap at 10
        severity = min(severity, 10)
        
        return severity
    
    def detect_pii(self, log_entry: Dict[str, Any]) -> List[str]:
        """
        Detect PII in log entry.
        
        Returns:
            List[str]: List of detected PII types
        """
        detected_pii = []
        log_text = str(log_entry.get('data', ''))
        
        for pattern in self.PII_PATTERNS:
            if re.search(pattern, log_text):
                if 'ssn' in pattern or 'd{3}-d{2}-d{4}' in pattern:
                    detected_pii.append('SSN')
                elif 'credit' in pattern or 'd{16}' in pattern:
                    detected_pii.append('Credit Card')
                elif '@' in pattern:
                    detected_pii.append('Email')
                elif 'phone' in pattern or 'd{3}-d{3}-d{4}' in pattern:
                    detected_pii.append('Phone')
                elif 'ip' in pattern:
                    detected_pii.append('IP Address')
        
        return detected_pii
    
    def is_crash(self, log_entry: Dict[str, Any], severity: int) -> bool:
        """
        Determine if log entry indicates a crash.
        
        Args:
            log_entry: The log entry to analyze
            severity: Calculated severity score
            
        Returns:
            bool: True if this is a crash, False otherwise
        """
        # If severity > 8, it's definitely a crash
        if severity > 8:
            return True
        
        # Check for crash-specific keywords
        log_text = str(log_entry.get('data', '')).lower()
        event = str(log_entry.get('event', '')).lower()
        
        crash_indicators = [
            'crash', 'fatal', 'panic', 'abort', 'segmentation fault',
            'stack overflow', 'null pointer exception', 'access violation',
            'kernel panic', 'system halt', 'application terminated'
        ]
        
        for indicator in crash_indicators:
            if indicator in log_text or indicator in event:
                return True
        
        return False
    
    def get_cluster_type(self, log_entry: Dict[str, Any], severity: int) -> str:
        """
        Determine the cluster type for a log entry.
        
        Returns:
            str: One of 'pii', 'debug', 'error', 'warning', 'info', 'crash'
        """
        # Check for PII first
        pii_types = self.detect_pii(log_entry)
        if pii_types:
            return 'pii'
        
        # Check for crash
        if self.is_crash(log_entry, severity):
            return 'crash'
        
        # Check severity-based classification
        if severity >= 5:
            return 'error'
        elif severity >= 3:
            return 'warning'
        elif 'debug' in str(log_entry.get('data', '')).lower():
            return 'debug'
        else:
            return 'info'
    
    def requires_attention(self, log_entry: Dict[str, Any], severity: int) -> bool:
        """
        Determine if log entry requires attention (non-error but important).
        
        Returns:
            bool: True if requires attention
        """
        # PII always requires attention
        if self.detect_pii(log_entry):
            return True
        
        # Debug issues that might indicate problems
        log_text = str(log_entry.get('data', '')).lower()
        attention_keywords = [
            'slow query', 'performance', 'memory leak', 'resource exhaustion',
            'deprecated', 'security', 'authentication', 'authorization',
            'rate limit', 'throttle', 'circuit breaker'
        ]
        
        for keyword in attention_keywords:
            if keyword in log_text:
                return True
        
        # Medium severity logs (3-4) that aren't errors but need review
        if 3 <= severity < 5:
            return True
        
        return False

# Global rubric instance
rubric = SeverityRubric()

