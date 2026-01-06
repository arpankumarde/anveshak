"""Crash detection agent for identifying and analyzing crashes."""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import logging
from datetime import datetime
from config import LANGCHAIN_MODEL, LANGCHAIN_TEMPERATURE, CRASH_SEVERITY_THRESHOLD, OPENAI_API_KEY, OPENAI_BASE_URL, LLM_TIMEOUT
from rubric import rubric
from embedding_service import embedding_service

logger = logging.getLogger(__name__)

class CrashDetectionAgent:
    """Agent for detecting and analyzing crashes."""
    
    def __init__(self):
        llm_kwargs = {
            "model": LANGCHAIN_MODEL,
            "temperature": LANGCHAIN_TEMPERATURE,
            "api_key": OPENAI_API_KEY,
            "timeout": LLM_TIMEOUT,
            "max_retries": 2
        }
        if OPENAI_BASE_URL:
            llm_kwargs["base_url"] = OPENAI_BASE_URL
        
        self.llm = ChatOpenAI(**llm_kwargs)
        self.crash_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert crash analyst specializing in application crash detection and analysis.
Your task is to analyze log entries to determine if they represent a crash and provide:
1. Crash type: Application crash, system crash, service crash, etc.
2. Crash severity: 0-10 scale (8+ is critical crash)
3. Crash indicators: Specific signals that indicate a crash
4. Affected components: What parts of the system are affected
5. Recovery status: Whether the system recovered automatically
6. Immediate actions: What needs to be done immediately
7. Root cause: Why the crash occurred
8. Prevention: How to prevent similar crashes

Return your analysis as JSON with these fields:
- is_crash: Boolean
- crash_type: String
- severity: Integer (0-10)
- crash_indicators: List of strings
- affected_components: List of strings
- recovery_status: String
- immediate_actions: List of strings
- root_cause: String
- prevention: String"""),
            ("human", "Analyze this log entry for crash detection: {log_entry}")
        ])
    
    def detect_crash(self, log_entry: Dict[str, Any], context_logs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Detect if a log entry represents a crash.
        
        Args:
            log_entry: Log entry to analyze
            context_logs: Related logs before/after (optional)
            
        Returns:
            Dict with crash detection results
        """
        try:
            # First check rubric
            severity = rubric.calculate_severity(log_entry)
            is_crash_rubric = rubric.is_crash(log_entry, severity)
            
            # Prepare log context
            log_text = json.dumps({
                "event": log_entry.get("event", ""),
                "data": str(log_entry.get("data", "")),
                "timestamp": log_entry.get("timestamp", ""),
                "severity": severity
            }, indent=2)
            
            if context_logs:
                # Use embeddings to find most relevant context (semantically similar, not just time-based)
                try:
                    # Find similar logs using embeddings
                    similar_logs = embedding_service.find_similar_logs(
                        log_entry,
                        limit=3,  # Only top 3 most similar
                        time_window_hours=2,
                        min_similarity=0.6
                    )
                    
                    if similar_logs:
                        # Use embedding-ranked logs
                        context_logs = [item["log"] for item in similar_logs]
                        logger.debug(f"Using {len(context_logs)} embedding-ranked context logs for crash detection")
                    
                    # Still separate by time for before/after context if possible
                    log_timestamp = log_entry.get("timestamp", 0)
                    before_logs = []
                    after_logs = []
                    
                    for log in context_logs:
                        log_ts = log.get("timestamp") or log.get("created_at", 0)
                        if log_ts < log_timestamp:
                            before_logs.append(log)
                        else:
                            after_logs.append(log)
                    
                    # Limit to most relevant
                    before_logs = before_logs[-2:] if before_logs else []
                    after_logs = after_logs[:2] if after_logs else []
                    
                except Exception as e:
                    logger.warning(f"Error using embeddings for crash context, using time-based: {e}")
                    # Fallback to time-based separation
                    log_timestamp = log_entry.get("timestamp", 0)
                    before_logs = [log for log in context_logs if (log.get("timestamp") or log.get("created_at", 0)) < log_timestamp][-2:]
                    after_logs = [log for log in context_logs if (log.get("timestamp") or log.get("created_at", 0)) > log_timestamp][:2]
                
                context_text = ""
                if before_logs:
                    context_text += "\n\nRelevant logs before crash:\n"
                    context_text += "\n".join([
                        f"  {str(log.get('data', '') or log.get('event', ''))[:150]}" 
                        for log in before_logs
                    ])
                if after_logs:
                    context_text += "\n\nRelevant logs after crash:\n"
                    context_text += "\n".join([
                        f"  {str(log.get('data', '') or log.get('event', ''))[:150]}" 
                        for log in after_logs
                    ])
                log_text += context_text
            
            # Get LLM analysis
            messages = self.crash_prompt.format_messages(log_entry=log_text)
            response = self.llm.invoke(messages)
            
            # Parse response
            try:
                response_text = response.content
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                analysis = json.loads(response_text)
            except (json.JSONDecodeError, ValueError):
                logger.warning(f"Failed to parse LLM response: {response.content}")
                # Use rubric-based detection
                analysis = {
                    "is_crash": is_crash_rubric,
                    "crash_type": "Unknown" if is_crash_rubric else "Not a crash",
                    "severity": severity,
                    "crash_indicators": ["Severity-based detection"],
                    "affected_components": [],
                    "recovery_status": "Unknown",
                    "immediate_actions": ["Review logs manually"],
                    "root_cause": "Unable to determine",
                    "prevention": "Review crash patterns"
                }
            
            # Override with rubric if severity > threshold
            if severity > CRASH_SEVERITY_THRESHOLD:
                analysis["is_crash"] = True
                analysis["severity"] = severity
                if not analysis.get("crash_type") or analysis.get("crash_type") == "Not a crash":
                    analysis["crash_type"] = "High Severity Crash"
            
            # Build result
            result = {
                "log_id": str(log_entry.get("_id", "")),
                "is_crash": analysis.get("is_crash", is_crash_rubric),
                "crash_type": analysis.get("crash_type", "Unknown"),
                "severity": analysis.get("severity", severity),
                "crash_indicators": analysis.get("crash_indicators", []),
                "affected_components": analysis.get("affected_components", []),
                "recovery_status": analysis.get("recovery_status", "Unknown"),
                "immediate_actions": analysis.get("immediate_actions", []),
                "root_cause": analysis.get("root_cause", ""),
                "prevention": analysis.get("prevention", ""),
                "timestamp": log_entry.get("timestamp", log_entry.get("created_at")),
                "log_data": str(log_entry.get("data", ""))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting crash: {e}")
            # Fallback to rubric
            severity = rubric.calculate_severity(log_entry)
            is_crash = rubric.is_crash(log_entry, severity)
            return {
                "log_id": str(log_entry.get("_id", "")),
                "is_crash": is_crash,
                "crash_type": "Unknown" if is_crash else "Not a crash",
                "severity": severity,
                "crash_indicators": ["Error in crash detection"],
                "affected_components": [],
                "recovery_status": "Unknown",
                "immediate_actions": ["Review manually"],
                "root_cause": f"Detection error: {str(e)}",
                "prevention": "Review crash detection system",
                "timestamp": log_entry.get("timestamp", log_entry.get("created_at")),
                "log_data": str(log_entry.get("data", ""))
            }
    
    def analyze_crash_pattern(self, crashes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze patterns across multiple crashes.
        
        Args:
            crashes: List of crash detection results
            
        Returns:
            Dict with pattern analysis
        """
        try:
            if not crashes:
                return {
                    "pattern_detected": False,
                    "pattern_type": None,
                    "frequency": 0,
                    "recommendation": "No crashes detected"
                }
            
            # Group by crash type
            crash_types = {}
            for crash in crashes:
                crash_type = crash.get("crash_type", "Unknown")
                if crash_type not in crash_types:
                    crash_types[crash_type] = []
                crash_types[crash_type].append(crash)
            
            # Find most common type
            most_common_type = max(crash_types.items(), key=lambda x: len(x[1]))[0]
            most_common_count = len(crash_types[most_common_type])
            
            # Check if pattern exists (same type occurring multiple times)
            pattern_detected = most_common_count > 1
            
            result = {
                "pattern_detected": pattern_detected,
                "pattern_type": most_common_type if pattern_detected else None,
                "frequency": most_common_count,
                "total_crashes": len(crashes),
                "crash_types": {k: len(v) for k, v in crash_types.items()},
                "recommendation": f"Investigate {most_common_type} crashes" if pattern_detected else "Monitor for patterns"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing crash pattern: {e}")
            return {
                "pattern_detected": False,
                "pattern_type": None,
                "frequency": 0,
                "recommendation": f"Error in pattern analysis: {str(e)}"
            }

