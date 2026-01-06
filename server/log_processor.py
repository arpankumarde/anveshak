"""Enhanced log processor orchestrator for multi-agent log analysis."""
import threading
import time
import logging
from typing import Dict, List, Any, Optional
from queue import Queue
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import LOG_BATCH_SIZE, PROCESSING_INTERVAL, LLM_BATCH_SIZE
from db import db_manager
from agents import (
    ClusteringAgent, ErrorAnalysisAgent, CrashDetectionAgent,
    ParserAgent, PatternRecognitionAgent, AnomalyDetectionAgent,
    ContextCorrelationAgent
)
from rubric import rubric
from embedding_service import embedding_service

logger = logging.getLogger(__name__)

class LogProcessor:
    """Enhanced orchestrator that coordinates all agents in parallel."""
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize the enhanced log processor.
        
        Args:
            max_workers: Maximum number of worker threads for parallel processing
        """
        # Initialize all agents
        self.parser_agent = ParserAgent()
        self.pattern_agent = PatternRecognitionAgent()
        self.anomaly_agent = AnomalyDetectionAgent()
        self.clustering_agent = ClusteringAgent()
        self.error_agent = ErrorAnalysisAgent()
        self.crash_agent = CrashDetectionAgent()
        self.context_agent = ContextCorrelationAgent()
        
        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        self.processing_queue = Queue()
        self.is_running = False
        self.processor_thread: Optional[threading.Thread] = None
        self.log_buffer: List[Dict[str, Any]] = []
        self.last_insight_time = datetime.utcnow()
    
    def start(self):
        """Start the log processor."""
        if self.is_running:
            logger.warning("Log processor is already running")
            return
        
        self.is_running = True
        self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processor_thread.start()
        logger.info("Log processor started")
    
    def stop(self):
        """Stop the log processor."""
        self.is_running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        self.executor.shutdown(wait=True)
        logger.info("Log processor stopped")
    
    def _execute_parallel(self, func, args_list, operation_name: str):
        """Execute a function in parallel and return results."""
        try:
            logger.debug(f"Executing {operation_name} in parallel...")
            future = self.executor.submit(func, *args_list)
            result = future.result(timeout=60)  # 60 second timeout
            logger.debug(f"{operation_name} completed, returned {len(result) if isinstance(result, list) else 'non-list'} items")
            return result
        except Exception as e:
            logger.error(f"Error in parallel {operation_name}: {e}", exc_info=True)
            # Return empty result on error
            return []
    
    def add_log(self, log_entry: Dict[str, Any], connection_id: str):
        """
        Add a log entry to the processing queue.
        
        Args:
            log_entry: Log entry from WebSocket
            connection_id: Connection identifier
        """
        # Add metadata
        enriched_log = {
            **log_entry,
            "connection_id": connection_id,
            "received_at": datetime.utcnow().isoformat()
        }
        
        # Store in MongoDB
        try:
            log_id = db_manager.insert_raw_log(enriched_log)
            enriched_log["_id"] = log_id
        except Exception as e:
            logger.error(f"Failed to store raw log: {e}")
            # Continue processing even if DB write fails
            enriched_log["_id"] = f"temp_{time.time()}"
        
        # Add to buffer for batch processing
        self.log_buffer.append(enriched_log)
        
        # Process if buffer is full
        if len(self.log_buffer) >= LOG_BATCH_SIZE:
            self._process_batch()
    
    def _process_loop(self):
        """Main processing loop."""
        while self.is_running:
            try:
                # Process batch if buffer has logs
                if self.log_buffer:
                    self._process_batch()
                
                # Generate periodic insights (every 10 minutes)
                time_since_last_insight = (datetime.utcnow() - self.last_insight_time).total_seconds()
                if time_since_last_insight >= 600:  # Every 10 minutes
                    self._generate_periodic_insights()
                    self.last_insight_time = datetime.utcnow()
                
                time.sleep(PROCESSING_INTERVAL)
            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                # Don't stop the processor, just log and continue
                time.sleep(PROCESSING_INTERVAL)
            except KeyboardInterrupt:
                logger.info("Processing loop interrupted")
                break
    
    def _process_batch(self):
        """Process a batch of logs through all agents in parallel."""
        if not self.log_buffer:
            return
        
        batch = self.log_buffer[:LOG_BATCH_SIZE]
        self.log_buffer = self.log_buffer[LOG_BATCH_SIZE:]
        
        logger.info(f"Processing batch of {len(batch)} logs through multi-agent pipeline")
        
        # Log batch statistics before processing
        logger.debug(f"Batch contains logs from connections: {set(log.get('connection_id', 'unknown') for log in batch)}")
        
        try:
            # Step 1: Parse all logs in parallel
            logger.info(f"Step 1: Parsing {len(batch)} logs...")
            try:
                parsed_logs = self._execute_parallel(
                    self.parser_agent.parse_batch, [batch], "parsing"
                )
                if not parsed_logs:
                    logger.warning("Parser returned empty results, using original logs")
                    parsed_logs = batch
                logger.info(f"Parsed {len(parsed_logs)} logs successfully")
            except Exception as e:
                logger.error(f"Error in parsing step: {e}", exc_info=True)
                parsed_logs = batch  # Fallback to original logs
            
            # Step 2: Execute pattern recognition, anomaly detection, and context correlation in parallel
            logger.info("Step 2: Pattern recognition, anomaly detection, and context correlation...")
            futures = {
                'patterns': self.executor.submit(self.pattern_agent.recognize_batch, parsed_logs),
                'anomalies': self.executor.submit(self.anomaly_agent.detect_batch, parsed_logs),
                'context': self.executor.submit(self.context_agent.correlate_batch, parsed_logs),
            }
            
            pattern_results = {}
            anomaly_results = {}
            context_results = {}
            
            for key, future in futures.items():
                try:
                    result_list = future.result(timeout=120)  # 2 minute timeout per agent
                    if key == 'patterns':
                        pattern_results = {i: result for i, result in enumerate(result_list)}
                        logger.debug(f"Pattern recognition: {len([r for r in pattern_results.values() if r.get('has_known_pattern')])} logs with known patterns")
                    elif key == 'anomalies':
                        anomaly_results = {i: result for i, result in enumerate(result_list)}
                        logger.debug(f"Anomaly detection: {len([r for r in anomaly_results.values() if r.get('is_anomaly')])} anomalies detected")
                    elif key == 'context':
                        context_results = {i: result for i, result in enumerate(result_list)}
                        logger.debug(f"Context correlation: {sum(len(r.get('related_logs', [])) for r in context_results.values())} related logs found")
                except Exception as e:
                    logger.error(f"Error in {key} processing: {e}", exc_info=True)
                    # Provide empty results on error
                    if key == 'patterns':
                        pattern_results = {i: {'patterns_matched': [], 'pattern_count': 0, 'has_known_pattern': False} for i in range(len(parsed_logs))}
                    elif key == 'anomalies':
                        anomaly_results = {i: {'is_anomaly': False, 'anomaly_score': 0.0} for i in range(len(parsed_logs))}
                    elif key == 'context':
                        context_results = {i: {'related_logs': [], 'correlation_score': 0.0} for i in range(len(parsed_logs))}
            
            # Step 3: Clustering (process in smaller batches to avoid timeouts)
            logger.info("Step 3: Clustering logs (this will call LLM for high-severity logs)...")
            clustering_results = []
            for i in range(0, len(parsed_logs), LLM_BATCH_SIZE):
                batch_chunk = parsed_logs[i:i + LLM_BATCH_SIZE]
                try:
                    chunk_results = self.clustering_agent.cluster_batch(batch_chunk)
                    clustering_results.extend(chunk_results)
                    logger.debug(f"Clustered chunk {i//LLM_BATCH_SIZE + 1}: {len(chunk_results)} results")
                except Exception as e:
                    logger.error(f"Error clustering batch chunk {i//LLM_BATCH_SIZE + 1}: {e}", exc_info=True)
                    # Fallback: use rubric for failed chunks
                    for log_entry in batch_chunk:
                        severity = rubric.calculate_severity(log_entry)
                        cluster_type = rubric.get_cluster_type(log_entry, severity)
                        clustering_results.append({
                            "log_id": str(log_entry.get("_id", "")),
                            "category": cluster_type.upper(),
                            "cluster_type": cluster_type,
                            "confidence": 0.5,
                            "reason": f"Fallback after error: {str(e)}",
                            "pii_types": rubric.detect_pii(log_entry),
                            "requires_review": rubric.requires_attention(log_entry, severity),
                            "severity": severity,
                            "timestamp": log_entry.get("timestamp", log_entry.get("created_at"))
                        })
            
            logger.info(f"Clustering complete: {len(clustering_results)} results, "
                       f"{len([r for r in clustering_results if r.get('cluster_type') != 'info'])} non-info clusters")
            
            # Step 4: Combine all agent results and process each log
            errors_to_analyze = []
            crashes_to_detect = []
            
            for i, (log_entry, parsed_log) in enumerate(zip(batch, parsed_logs)):
                cluster_result = clustering_results[i] if i < len(clustering_results) else {}
                pattern_result = pattern_results.get(i, {})
                anomaly_result = anomaly_results.get(i, {})
                context_result = context_results.get(i, {})
                
                # Combine all agent results
                combined_severity = max(
                    cluster_result.get("severity", 0),
                    pattern_result.get("pattern_score", 0),
                    anomaly_result.get("anomaly_score", 0) * 10 if anomaly_result.get("is_anomaly") else 0
                )
                
                # Store processed log with all agent results
                processed_log = {
                    "raw_log_id": str(log_entry.get("_id", "")),
                    "connection_id": log_entry.get("connection_id", ""),
                    "event": log_entry.get("event", ""),
                    "data": str(log_entry.get("data", "")),
                    "timestamp": log_entry.get("timestamp", log_entry.get("created_at")),
                    "severity": combined_severity,
                    "cluster_type": cluster_result.get("cluster_type", "info"),
                    "category": cluster_result.get("category", "INFO"),
                    "pii_types": cluster_result.get("pii_types", []),
                    "requires_review": cluster_result.get("requires_review", False),
                    # Parser results
                    "parsed_fields": parsed_log.get("parsed_fields", {}),
                    "parse_confidence": parsed_log.get("parse_confidence", 0.0),
                    "format_type": parsed_log.get("format_type", "unknown"),
                    # Pattern recognition results
                    "patterns_matched": pattern_result.get("patterns_matched", []),
                    "pattern_count": pattern_result.get("pattern_count", 0),
                    "has_known_pattern": pattern_result.get("has_known_pattern", False),
                    # Anomaly detection results
                    "is_anomaly": anomaly_result.get("is_anomaly", False),
                    "anomaly_score": anomaly_result.get("anomaly_score", 0.0),
                    "anomaly_confidence": anomaly_result.get("confidence", 0.0),
                    # Context correlation results
                    "related_logs_count": len(context_result.get("related_logs", [])),
                    "related_errors_count": len(context_result.get("related_errors", [])),
                    "related_crashes_count": len(context_result.get("related_crashes", [])),
                    "correlation_score": context_result.get("correlation_score", 0.0),
                }
                
                # Store cluster for all log types (not just PII/debug)
                # Group similar logs into clusters based on cluster_type and patterns
                cluster_type = cluster_result.get("cluster_type", "info")
                
                try:
                    # Try to find existing cluster of same type (within last 10 minutes)
                    existing_cluster = db_manager.db.clusters.find_one({
                        "cluster_type": cluster_type,
                        "created_at": {
                            "$gte": datetime.utcnow() - timedelta(minutes=10)  # Within last 10 minutes
                        }
                    }, sort=[("created_at", -1)])
                    
                    if existing_cluster and cluster_type in ["error", "warning", "info"]:
                        # Add to existing cluster
                        db_manager.db.clusters.update_one(
                            {"_id": existing_cluster["_id"]},
                            {
                                "$addToSet": {"log_ids": str(log_entry.get("_id", ""))},
                                "$inc": {"count": 1},
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                    else:
                        # Create new cluster
                        db_manager.insert_cluster({
                            "cluster_type": cluster_type,
                            "category": cluster_result.get("category", "INFO"),
                            "log_ids": [str(log_entry.get("_id", ""))],
                            "pii_types": cluster_result.get("pii_types", []),
                            "requires_review": cluster_result.get("requires_review", False),
                            "count": 1,
                            "pattern_matches": pattern_result.get("patterns_matched", []),
                            "is_anomaly": anomaly_result.get("is_anomaly", False),
                            "severity": combined_severity,
                            "first_seen": datetime.utcnow(),
                            "last_seen": datetime.utcnow()
                        })
                except Exception as e:
                    logger.error(f"Failed to store cluster: {e}")
                
                # Store processed log with all agent results
                try:
                    processed_log_id = db_manager.insert_processed_log(processed_log)
                    processed_log["_id"] = processed_log_id
                except Exception as e:
                    logger.error(f"Failed to store processed log for log_id {log_entry.get('_id', 'unknown')}: {e}", exc_info=True)
                
                # Collect errors for analysis (lowered thresholds to catch more errors)
                is_error = (
                    cluster_result.get("cluster_type") == "error" or
                    cluster_result.get("cluster_type") == "crash" or
                    combined_severity >= 3 or  # Lowered from 5 to 3
                    pattern_result.get("has_known_pattern", False) or
                    anomaly_result.get("is_anomaly", False) or
                    pattern_result.get("pattern_count", 0) > 0  # Any pattern match
                )
                if is_error:
                    errors_to_analyze.append((parsed_log, {
                        **cluster_result,
                        "pattern_result": pattern_result,
                        "anomaly_result": anomaly_result,
                        "context_result": context_result
                    }))
                
                # Check for crashes (lowered threshold to catch more crashes)
                if combined_severity >= 7 or cluster_result.get("cluster_type") == "crash":
                    crashes_to_detect.append((parsed_log, {
                        **cluster_result,
                        "pattern_result": pattern_result,
                        "anomaly_result": anomaly_result,
                        "context_result": context_result
                    }))
            
            # Step 3: Error analysis
            if errors_to_analyze:
                self._analyze_errors(errors_to_analyze)
            
            # Step 4: Crash detection
            if crashes_to_detect:
                self._detect_crashes(crashes_to_detect)
            
            # Mark logs as processed
            log_ids = [str(log.get("_id", "")) for log in batch if log.get("_id")]
            if log_ids:
                try:
                    db_manager.mark_logs_processed(log_ids)
                except Exception as e:
                    logger.error(f"Failed to mark logs as processed: {e}")
            
            # Generate insights after processing batch (if significant activity)
            if len(errors_to_analyze) > 0 or len(crashes_to_detect) > 0 or sum(1 for r in anomaly_results.values() if r.get('is_anomaly')) > 0:
                try:
                    self._generate_batch_insights(batch, errors_to_analyze, crashes_to_detect, anomaly_results)
                except Exception as e:
                    logger.error(f"Failed to generate batch insights: {e}")
            
            logger.info(
                f"Completed processing batch: {len(batch)} logs, "
                f"{len(errors_to_analyze)} errors, {len(crashes_to_detect)} crashes, "
                f"{sum(1 for r in anomaly_results.values() if r.get('is_anomaly'))} anomalies, "
                f"{len([c for c in clustering_results if c.get('cluster_type') in ['error', 'warning', 'pii', 'debug']])} significant clusters"
            )
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}", exc_info=True)
    
    def _analyze_errors(self, error_logs: List[tuple]):
        """Analyze errors using error analysis agent."""
        try:
            error_analyses = []
            
            for log_entry, cluster_result in error_logs:
                # Get context logs using embeddings (smarter than time-based)
                context_logs = None
                try:
                    # Use embedding service to find semantically similar logs
                    context_logs = embedding_service.get_relevant_context(log_entry, max_context_logs=5)
                    if not context_logs:
                        # Fallback to time-based if embeddings fail
                        connection_id = log_entry.get("connection_id")
                        if connection_id:
                            context_logs = db_manager.get_context_logs(connection_id, limit=5)
                except Exception as e:
                    logger.warning(f"Failed to get context logs: {e}")
                    # Fallback to time-based
                    try:
                        connection_id = log_entry.get("connection_id")
                        if connection_id:
                            context_logs = db_manager.get_context_logs(connection_id, limit=5)
                    except:
                        context_logs = None
                
                # Analyze error
                analysis = self.error_agent.analyze_error(log_entry, context_logs)
                error_analyses.append(analysis)
                
                # Store error
                try:
                    error_data = {
                        "log_id": analysis.get("log_id", ""),
                        "error_type": analysis.get("error_type", ""),
                        "error_message": analysis.get("error_message", ""),
                        "severity": analysis.get("severity", 0),
                        "root_cause": analysis.get("root_cause", ""),
                        "impact": analysis.get("impact", ""),
                        "likely_fix": analysis.get("likely_fix", ""),
                        "priority": analysis.get("priority", "MEDIUM"),
                        "stakeholder_insight": analysis.get("stakeholder_insight", ""),
                        "timestamp": analysis.get("timestamp")
                    }
                    db_manager.insert_error(error_data)
                except Exception as e:
                    logger.error(f"Failed to store error analysis: {e}")
            
            logger.info(f"Analyzed {len(error_analyses)} errors")
            
        except Exception as e:
            logger.error(f"Error in error analysis: {e}", exc_info=True)
    
    def _detect_crashes(self, crash_logs: List[tuple]):
        """Detect crashes using crash detection agent."""
        try:
            crash_detections = []
            
            for log_entry, cluster_result in crash_logs:
                # Get context logs using embeddings (smarter than time-based)
                context_logs = None
                try:
                    # Use embedding service to find semantically similar logs
                    context_logs = embedding_service.get_relevant_context(log_entry, max_context_logs=5)
                    if not context_logs:
                        # Fallback to time-based if embeddings fail
                        connection_id = log_entry.get("connection_id")
                        if connection_id:
                            context_logs = db_manager.get_context_logs(connection_id, limit=5)
                except Exception as e:
                    logger.warning(f"Failed to get context logs: {e}")
                    # Fallback to time-based
                    try:
                        connection_id = log_entry.get("connection_id")
                        if connection_id:
                            context_logs = db_manager.get_context_logs(connection_id, limit=5)
                    except:
                        context_logs = None
                
                # Detect crash
                detection = self.crash_agent.detect_crash(log_entry, context_logs)
                
                # Only store if it's actually a crash
                if detection.get("is_crash"):
                    crash_detections.append(detection)
                    
                    # Store crash
                    try:
                        crash_data = {
                            "log_id": detection.get("log_id", ""),
                            "crash_type": detection.get("crash_type", ""),
                            "severity": detection.get("severity", 0),
                            "crash_indicators": detection.get("crash_indicators", []),
                            "affected_components": detection.get("affected_components", []),
                            "recovery_status": detection.get("recovery_status", ""),
                            "immediate_actions": detection.get("immediate_actions", []),
                            "root_cause": detection.get("root_cause", ""),
                            "prevention": detection.get("prevention", ""),
                            "timestamp": detection.get("timestamp")
                        }
                        db_manager.insert_crash(crash_data)
                    except Exception as e:
                        logger.error(f"Failed to store crash detection: {e}")
            
            # Analyze crash patterns if multiple crashes
            if len(crash_detections) > 1:
                try:
                    pattern = self.crash_agent.analyze_crash_pattern(crash_detections)
                    if pattern.get("pattern_detected"):
                        logger.warning(f"Crash pattern detected: {pattern.get('pattern_type')} ({pattern.get('frequency')} occurrences)")
                except Exception as e:
                    logger.error(f"Failed to analyze crash pattern: {e}")
            
            logger.info(f"Detected {len(crash_detections)} crashes")
            
        except Exception as e:
            logger.error(f"Error in crash detection: {e}", exc_info=True)
    
    def _generate_batch_insights(self, batch: List[Dict[str, Any]], errors: List[tuple], 
                                 crashes: List[tuple], anomaly_results: Dict[int, Dict[str, Any]]):
        """Generate insights from a processed batch."""
        try:
            # Count statistics
            total_logs = len(batch)
            error_count = len(errors)
            crash_count = len(crashes)
            anomaly_count = sum(1 for r in anomaly_results.values() if r.get('is_anomaly'))
            
            # Get cluster statistics
            cluster_types = {}
            for log_entry in batch:
                cluster_type = log_entry.get("cluster_type", "info")
                cluster_types[cluster_type] = cluster_types.get(cluster_type, 0) + 1
            
            # Generate insight summary
            insight_parts = []
            if error_count > 0:
                insight_parts.append(f"Detected {error_count} error(s) in this batch")
            if crash_count > 0:
                insight_parts.append(f"{crash_count} crash(es) detected")
            if anomaly_count > 0:
                insight_parts.append(f"{anomaly_count} anomaly/anomalies identified")
            
            if cluster_types:
                cluster_summary = ", ".join([f"{count} {ctype}" for ctype, count in cluster_types.items()])
                insight_parts.append(f"Log distribution: {cluster_summary}")
            
            if insight_parts:
                insight_text = ". ".join(insight_parts) + "."
                
                # Determine impact level
                if crash_count > 0 or error_count > 5:
                    impact_level = "HIGH"
                elif error_count > 0 or anomaly_count > 3:
                    impact_level = "MEDIUM"
                else:
                    impact_level = "LOW"
                
                # Store insight
                try:
                    db_manager.insert_insight({
                        "insight_type": "batch",
                        "insight": insight_text,
                        "impact_level": impact_level,
                        "recommendation": self._generate_recommendation(error_count, crash_count, anomaly_count),
                        "trend_analysis": f"Batch processing: {total_logs} logs analyzed",
                        "error_count": error_count,
                        "crash_count": crash_count,
                        "anomaly_count": anomaly_count,
                        "high_severity_count": sum(1 for e in errors if e[1].get("severity", 0) >= 7)
                    })
                    logger.info(f"Generated batch insight: {insight_text}")
                except Exception as e:
                    logger.error(f"Failed to store batch insight: {e}")
            
        except Exception as e:
            logger.error(f"Error generating batch insights: {e}")
    
    def _generate_recommendation(self, error_count: int, crash_count: int, anomaly_count: int) -> str:
        """Generate recommendation based on batch statistics."""
        if crash_count > 0:
            return "Immediate investigation required for crashes. Review crash logs and affected components."
        elif error_count > 5:
            return "Multiple errors detected. Review error patterns and consider system-wide issues."
        elif anomaly_count > 3:
            return "Several anomalies detected. Monitor system behavior and review anomaly patterns."
        elif error_count > 0:
            return "Errors detected. Review error logs for root cause analysis."
        else:
            return "System operating normally. Continue monitoring."
    
    def _generate_periodic_insights(self):
        """Generate periodic insights for stakeholders."""
        try:
            # Get recent errors (last 10 minutes for more frequent insights)
            time_window = datetime.utcnow() - timedelta(minutes=10)
            recent_errors = list(db_manager.db.errors.find({
                "created_at": {
                    "$gte": time_window
                }
            }).limit(50))
            
            # Get recent processed logs for statistics (last 10 minutes)
            recent_logs = list(db_manager.db.processed_logs.find({
                "created_at": {
                    "$gte": time_window
                }
            }).limit(100))
            
            # Get cluster statistics (last 10 minutes)
            recent_clusters = list(db_manager.db.clusters.find({
                "created_at": {
                    "$gte": time_window
                }
            }))
            
            # Generate comprehensive insights
            if recent_errors or recent_logs:
                # Convert to analysis format
                error_analyses = [
                    {
                        "error_type": err.get("error_type", ""),
                        "severity": err.get("severity", 0),
                        "root_cause": err.get("root_cause", ""),
                        "impact": err.get("impact", ""),
                        "timestamp": str(err.get("timestamp", ""))
                    }
                    for err in recent_errors
                ]
                
                # Generate insights from errors if available
                if error_analyses:
                    # Use embeddings to find representative errors (reduce token usage)
                    try:
                        if len(error_analyses) > 10:
                            # Group by error_type and severity to find diverse patterns
                            error_groups = {}
                            for err in error_analyses:
                                error_type = err.get("error_type", "unknown")
                                severity_bucket = "high" if err.get("severity", 0) >= 7 else "medium" if err.get("severity", 0) >= 4 else "low"
                                key = f"{error_type}:{severity_bucket}"
                                if key not in error_groups:
                                    error_groups[key] = []
                                error_groups[key].append(err)
                            
                            # Take top error from each group
                            representative_errors = []
                            for key, errors in error_groups.items():
                                errors.sort(key=lambda x: x.get("severity", 0), reverse=True)
                                representative_errors.append(errors[0])
                            
                            # Limit to top 10 by severity
                            if len(representative_errors) > 10:
                                representative_errors.sort(key=lambda x: x.get("severity", 0), reverse=True)
                                representative_errors = representative_errors[:10]
                            
                            error_analyses = representative_errors
                            logger.debug(f"Using {len(error_analyses)} representative errors for insights (reduced from larger set)")
                    except Exception as e:
                        logger.warning(f"Error selecting representative errors: {e}")
                        error_analyses = error_analyses[:10]  # Fallback limit
                    
                    insights = self.error_agent.generate_insights(error_analyses, time_window_hours=24)
                else:
                    # Generate insights from processed logs
                    cluster_summary = {}
                    for cluster in recent_clusters:
                        ctype = cluster.get("cluster_type", "info")
                        cluster_summary[ctype] = cluster_summary.get(ctype, 0) + cluster.get("count", 1)
                    
                    insights = {
                        "insight": f"Processed {len(recent_logs)} logs in last 10 minutes. Cluster distribution: {dict(cluster_summary)}",
                        "impact_level": "LOW" if len(recent_errors) == 0 else "MEDIUM",
                        "recommendation": "Continue monitoring system health",
                        "trend_analysis": f"Active monitoring: {len(recent_clusters)} clusters created in last 10 minutes"
                    }
                
                # Store insights
                try:
                    db_manager.insert_insight({
                        "insight_type": "periodic",
                        "insight": insights.get("insight", ""),
                        "impact_level": insights.get("impact_level", ""),
                        "recommendation": insights.get("recommendation", ""),
                        "trend_analysis": insights.get("trend_analysis", ""),
                        "error_count": insights.get("error_count", len(recent_errors)),
                        "high_severity_count": insights.get("high_severity_count", sum(1 for e in recent_errors if e.get("severity", 0) >= 7)),
                        "log_count": len(recent_logs),
                        "cluster_count": len(recent_clusters)
                    })
                    logger.info("Generated periodic insights")
                except Exception as e:
                    logger.error(f"Failed to store insights: {e}")
            else:
                # Generate basic insight even if no errors
                try:
                    db_manager.insert_insight({
                        "insight_type": "periodic",
                        "insight": "System monitoring active. No significant issues detected in the last 24 hours.",
                        "impact_level": "LOW",
                        "recommendation": "Continue regular monitoring",
                        "trend_analysis": "Normal operation",
                        "error_count": 0,
                        "high_severity_count": 0
                    })
                    logger.info("Generated periodic insights (no errors)")
                except Exception as e:
                    logger.error(f"Failed to store insights: {e}")
            
        except Exception as e:
            logger.error(f"Error generating periodic insights: {e}")

# Global log processor instance
log_processor = LogProcessor()

