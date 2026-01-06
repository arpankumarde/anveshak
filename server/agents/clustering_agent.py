"""Clustering agent for categorizing logs (PII, Debug, Attention-required)."""
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import logging
from config import LANGCHAIN_MODEL, LANGCHAIN_TEMPERATURE, OPENAI_API_KEY, OPENAI_BASE_URL, LLM_TIMEOUT
from rubric import rubric

logger = logging.getLogger(__name__)

class ClusteringAgent:
    """Agent for clustering logs into categories."""
    
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
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert log analyst specializing in categorizing logs.
Your task is to analyze log entries and classify them into one of these categories:
1. PII - Contains personally identifiable information (emails, SSNs, credit cards, etc.)
2. DEBUG - Debug information that might indicate issues
3. ATTENTION - Non-error logs that require attention (performance, security, deprecation warnings)
4. ERROR - Error logs (handled by error analysis agent)
5. INFO - Standard informational logs

For each log entry, provide:
- category: One of PII, DEBUG, ATTENTION, ERROR, INFO
- confidence: 0.0 to 1.0
- reason: Brief explanation
- pii_types: List of PII types found (if category is PII)
- requires_review: Boolean indicating if human review is needed

Return your analysis as JSON."""),
            ("human", "Analyze this log entry: {log_entry}")
        ])
    
    def cluster_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cluster a single log entry.
        
        Args:
            log_entry: Log entry to analyze
            
        Returns:
            Dict with clustering results
        """
        try:
            # First check rubric for quick classification
            severity = rubric.calculate_severity(log_entry)
            cluster_type = rubric.get_cluster_type(log_entry, severity)
            pii_types = rubric.detect_pii(log_entry)
            requires_attention = rubric.requires_attention(log_entry, severity)
            
            # Only use LLM for logs that need deeper analysis (high severity, PII, or attention-required)
            # For most logs, rubric-based classification is sufficient
            # Lower threshold to test - can be adjusted
            use_llm = severity >= 3 or len(pii_types) > 0 or requires_attention
            
            if use_llm:
                try:
                    # Prepare log text for LLM
                    log_text = json.dumps({
                        "event": log_entry.get("event", ""),
                        "data": str(log_entry.get("data", "")),
                        "timestamp": log_entry.get("timestamp", "")
                    }, indent=2)
                    
                    # Get LLM analysis with timeout
                    messages = self.prompt_template.format_messages(log_entry=log_text)
                    response = self.llm.invoke(messages)
                except Exception as llm_error:
                    logger.warning(f"LLM analysis failed, using rubric: {llm_error}")
                    use_llm = False
            
            if not use_llm:
                # Use rubric-based classification only
                return {
                    "log_id": str(log_entry.get("_id", "")),
                    "category": cluster_type.upper(),
                    "cluster_type": cluster_type,
                    "confidence": 0.7,
                    "reason": "Rubric-based classification",
                    "pii_types": pii_types,
                    "requires_review": requires_attention,
                    "severity": severity,
                    "timestamp": log_entry.get("timestamp", log_entry.get("created_at"))
                }
            
            # Parse LLM response
            try:
                # Try to extract JSON from response
                response_text = response.content
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                llm_result = json.loads(response_text)
            except (json.JSONDecodeError, ValueError):
                # Fallback to rubric-based classification
                logger.warning(f"Failed to parse LLM response, using rubric: {response.content}")
                llm_result = {
                    "category": cluster_type.upper(),
                    "confidence": 0.7,
                    "reason": "Rubric-based classification",
                    "pii_types": pii_types,
                    "requires_review": requires_attention
                }
            
            # Merge rubric and LLM results
            result = {
                "log_id": str(log_entry.get("_id", "")),
                "category": llm_result.get("category", cluster_type.upper()),
                "cluster_type": cluster_type,
                "confidence": llm_result.get("confidence", 0.7),
                "reason": llm_result.get("reason", ""),
                "pii_types": llm_result.get("pii_types", pii_types),
                "requires_review": llm_result.get("requires_review", requires_attention),
                "severity": severity,
                "timestamp": log_entry.get("timestamp", log_entry.get("created_at"))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error clustering log entry: {e}")
            # Fallback to rubric-based classification
            severity = rubric.calculate_severity(log_entry)
            cluster_type = rubric.get_cluster_type(log_entry, severity)
            return {
                "log_id": str(log_entry.get("_id", "")),
                "category": cluster_type.upper(),
                "cluster_type": cluster_type,
                "confidence": 0.5,
                "reason": f"Error in clustering: {str(e)}",
                "pii_types": rubric.detect_pii(log_entry),
                "requires_review": rubric.requires_attention(log_entry, severity),
                "severity": severity,
                "timestamp": log_entry.get("timestamp", log_entry.get("created_at"))
            }
    
    def cluster_batch(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster a batch of log entries.
        
        Args:
            log_entries: List of log entries to analyze
            
        Returns:
            List of clustering results
        """
        results = []
        for log_entry in log_entries:
            result = self.cluster_log(log_entry)
            results.append(result)
        return results

