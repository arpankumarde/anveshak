"""Error analysis agent for cause analysis and insights generation."""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import logging
from datetime import datetime
from config import LANGCHAIN_MODEL, LANGCHAIN_TEMPERATURE, OPENAI_API_KEY, OPENAI_BASE_URL, LLM_TIMEOUT
from rubric import rubric
from embedding_service import embedding_service

logger = logging.getLogger(__name__)

class ErrorAnalysisAgent:
    """Agent for analyzing errors and generating insights."""
    
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
        self.error_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert error analyst specializing in root cause analysis.
Your task is to analyze error logs and provide:
1. Root cause: The underlying reason for the error
2. Impact: Who/what is affected
3. Likely fix: Suggested remediation steps
4. Priority: HIGH, MEDIUM, LOW based on severity and impact
5. Related errors: Patterns that suggest this is part of a larger issue
6. Stakeholder insights: Business/operational insights for non-technical stakeholders

Return your analysis as JSON with these fields:
- root_cause: String
- impact: String
- likely_fix: String
- priority: String (HIGH/MEDIUM/LOW)
- related_errors: List of error patterns
- stakeholder_insight: String (non-technical explanation)
- technical_details: String (for technical team)"""),
            ("human", "Analyze this error log: {error_log}")
        ])
        
        self.insight_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a business analyst creating insights from error logs for stakeholders.
Generate actionable insights that explain:
- What happened in business terms
- Why it matters
- What's being done about it
- Any trends or patterns

Keep it concise, non-technical, and actionable.
Return as JSON with: insight, impact_level, recommendation, trend_analysis"""),
            ("human", "Create stakeholder insight from these errors: {errors}")
        ])
    
    def analyze_error(self, log_entry: Dict[str, Any], context_logs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Analyze a single error log entry.
        
        Args:
            log_entry: Error log entry to analyze
            context_logs: Related logs for context (optional)
            
        Returns:
            Dict with error analysis
        """
        try:
            severity = rubric.calculate_severity(log_entry)
            
            # Prepare error context - use embeddings to find most relevant context
            error_text = json.dumps({
                "event": log_entry.get("event", ""),
                "data": str(log_entry.get("data", "")),
                "timestamp": log_entry.get("timestamp", ""),
                "severity": severity
            }, indent=2)
            
            if context_logs:
                # Use embeddings to rank and select most relevant context (max 3 to reduce token usage)
                try:
                    # Find similar logs using embeddings
                    similar_logs = embedding_service.find_similar_logs(
                        log_entry,
                        limit=3,  # Only top 3 most similar
                        time_window_hours=2,
                        min_similarity=0.6
                    )
                    
                    # Use embedding-ranked logs if available, otherwise use provided context
                    if similar_logs:
                        context_logs = [item["log"] for item in similar_logs]
                        logger.debug(f"Using {len(context_logs)} embedding-ranked context logs")
                    else:
                        # Fallback to provided context, but limit to 3
                        context_logs = context_logs[:3]
                        logger.debug(f"Using {len(context_logs)} time-based context logs (fallback)")
                except Exception as e:
                    logger.warning(f"Error using embeddings for context, using provided context: {e}")
                    context_logs = context_logs[:3]  # Limit to 3
                
                # Prepare concise context (only essential info)
                context_parts = []
                for log in context_logs:
                    # Extract key info from processed log
                    log_data = log.get("data", "") or log.get("event", "")
                    cluster_type = log.get("cluster_type", "")
                    log_severity = log.get("severity", 0)
                    
                    # Only include relevant parts
                    context_parts.append(f"[{cluster_type.upper()}] {str(log_data)[:200]}")
                
                if context_parts:
                    context_text = "\n".join(context_parts)
                    error_text += f"\n\nRelevant context (top {len(context_parts)} similar logs):\n{context_text}"
            
            # Get LLM analysis
            messages = self.error_prompt.format_messages(error_log=error_text)
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
                analysis = {
                    "root_cause": "Unable to determine root cause",
                    "impact": "Unknown",
                    "likely_fix": "Review error logs manually",
                    "priority": "MEDIUM" if severity >= 5 else "LOW",
                    "related_errors": [],
                    "stakeholder_insight": "An error occurred that requires investigation",
                    "technical_details": str(log_entry.get("data", ""))
                }
            
            result = {
                "log_id": str(log_entry.get("_id", "")),
                "error_type": log_entry.get("event", "unknown"),
                "error_message": str(log_entry.get("data", "")),
                "severity": severity,
                "timestamp": log_entry.get("timestamp", log_entry.get("created_at")),
                "root_cause": analysis.get("root_cause", ""),
                "impact": analysis.get("impact", ""),
                "likely_fix": analysis.get("likely_fix", ""),
                "priority": analysis.get("priority", "MEDIUM"),
                "related_errors": analysis.get("related_errors", []),
                "stakeholder_insight": analysis.get("stakeholder_insight", ""),
                "technical_details": analysis.get("technical_details", "")
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing error log: {e}")
            return {
                "log_id": str(log_entry.get("_id", "")),
                "error_type": log_entry.get("event", "unknown"),
                "error_message": str(log_entry.get("data", "")),
                "severity": rubric.calculate_severity(log_entry),
                "timestamp": log_entry.get("timestamp", log_entry.get("created_at")),
                "root_cause": f"Analysis error: {str(e)}",
                "impact": "Unknown",
                "likely_fix": "Review manually",
                "priority": "MEDIUM",
                "related_errors": [],
                "stakeholder_insight": "An error occurred that requires investigation",
                "technical_details": str(log_entry.get("data", ""))
            }
    
    def generate_insights(self, error_analyses: List[Dict[str, Any]], time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Generate stakeholder insights from multiple error analyses.
        
        Args:
            error_analyses: List of error analysis results
            time_window_hours: Time window for trend analysis
            
        Returns:
            Dict with insights
        """
        try:
            if not error_analyses:
                return {
                    "insight": "No errors to analyze",
                    "impact_level": "NONE",
                    "recommendation": "Continue monitoring",
                    "trend_analysis": "No trends detected"
                }
            
            # Use embeddings to find most representative errors (instead of all)
            # This reduces token usage and focuses on diverse error patterns
            try:
                if len(error_analyses) > 10:
                    # For large sets, use embeddings to find diverse/representative errors
                    # Group by error_type first, then use embeddings for diversity
                    error_groups = {}
                    for err in error_analyses:
                        error_type = err.get("error_type", "unknown")
                        if error_type not in error_groups:
                            error_groups[error_type] = []
                        error_groups[error_type].append(err)
                    
                    # Take top error from each group, then fill remaining with diverse samples
                    representative_errors = []
                    for error_type, errors in error_groups.items():
                        # Sort by severity and take top
                        errors.sort(key=lambda x: x.get("severity", 0), reverse=True)
                        representative_errors.append(errors[0])
                    
                    # If still too many, limit to top 10 by severity
                    if len(representative_errors) > 10:
                        representative_errors.sort(key=lambda x: x.get("severity", 0), reverse=True)
                        representative_errors = representative_errors[:10]
                    
                    error_analyses = representative_errors
                    logger.debug(f"Reduced error analyses to {len(error_analyses)} representative errors using embeddings")
            except Exception as e:
                logger.warning(f"Error using embeddings for error selection, using all: {e}")
                error_analyses = error_analyses[:15]  # Fallback limit
            
            # Prepare concise summary for LLM
            errors_summary = json.dumps([
                {
                    "error_type": err.get("error_type", ""),
                    "severity": err.get("severity", 0),
                    "root_cause": err.get("root_cause", "")[:200],  # Truncate long root causes
                    "impact": err.get("impact", "")[:150],  # Truncate long impacts
                    "timestamp": str(err.get("timestamp", ""))
                }
                for err in error_analyses
            ], indent=2)
            
            # Get LLM insight
            messages = self.insight_prompt.format_messages(errors=errors_summary)
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
                
                insight = json.loads(response_text)
            except (json.JSONDecodeError, ValueError):
                # Generate basic insight
                high_severity_count = sum(1 for e in error_analyses if e.get("severity", 0) >= 7)
                insight = {
                    "insight": f"Detected {len(error_analyses)} errors, {high_severity_count} high severity",
                    "impact_level": "HIGH" if high_severity_count > 0 else "MEDIUM",
                    "recommendation": "Review high severity errors immediately",
                    "trend_analysis": "Manual review recommended"
                }
            
            # Add metadata
            insight["error_count"] = len(error_analyses)
            insight["high_severity_count"] = sum(1 for e in error_analyses if e.get("severity", 0) >= 7)
            insight["time_window_hours"] = time_window_hours
            insight["generated_at"] = datetime.utcnow().isoformat()
            
            return insight
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                "insight": f"Error generating insights: {str(e)}",
                "impact_level": "UNKNOWN",
                "recommendation": "Manual review required",
                "trend_analysis": "Unable to analyze trends"
            }

