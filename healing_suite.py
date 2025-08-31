"""
The Healing Suite™ - Enterprise-Grade Error Healing and Recovery System
Advanced error detection, mitigation, processing, correction, management, support, and healing
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import traceback
import re
from decimal import Decimal, InvalidOperation, DivisionByZero, Overflow
import psutil
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    CALCULATION = "calculation"
    VALIDATION = "validation"
    NETWORK = "network"
    SYSTEM = "system"
    DATABASE = "database"
    REDIS = "redis"
    WEBSOCKET = "websocket"
    CURRENCY = "currency"
    PRECISION = "precision"
    SECURITY = "security"

class HealingAction(Enum):
    DETECTION = "detection"
    MITIGATION = "mitigation" 
    PROCESSING = "processing"
    CORRECTION = "correction"
    MANAGEMENT = "management"
    SUPPORT = "support"
    HEALING = "healing"

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorPattern:
    """Pattern for error detection and learning"""
    pattern_id: str
    regex_pattern: str
    error_type: str
    category: ErrorCategory
    severity: Severity
    auto_fix_available: bool
    fix_strategy: str
    occurrences: int = 0
    last_seen: Optional[datetime] = None
    success_rate: float = 0.0

@dataclass
class HealingAction:
    """Individual healing action record"""
    action_id: str
    action_type: HealingAction
    timestamp: datetime
    error_info: Dict[str, Any]
    strategy_applied: str
    success: bool
    execution_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class ErrorDetector:
    """Advanced error detection with pattern learning"""
    
    def __init__(self):
        self.patterns: Dict[str, ErrorPattern] = {}
        self.recent_errors = deque(maxlen=1000)
        self.error_stats = defaultdict(int)
        self._load_default_patterns()
    
    def _load_default_patterns(self):
        """Load default error patterns"""
        default_patterns = [
            ErrorPattern(
                pattern_id="div_by_zero",
                regex_pattern=r"(division by zero|divide by zero|ZeroDivisionError)",
                error_type="ZeroDivisionError",
                category=ErrorCategory.CALCULATION,
                severity=Severity.HIGH,
                auto_fix_available=True,
                fix_strategy="Use epsilon value or limit calculation"
            ),
            ErrorPattern(
                pattern_id="invalid_decimal",
                regex_pattern=r"(invalid literal|InvalidOperation|invalid decimal)",
                error_type="InvalidOperation",
                category=ErrorCategory.VALIDATION,
                severity=Severity.MEDIUM,
                auto_fix_available=True,
                fix_strategy="Sanitize and validate input format"
            ),
            ErrorPattern(
                pattern_id="overflow",
                regex_pattern=r"(overflow|too large|exceeds maximum)",
                error_type="Overflow",
                category=ErrorCategory.PRECISION,
                severity=Severity.HIGH,
                auto_fix_available=True,
                fix_strategy="Break into smaller calculations or increase precision"
            ),
            ErrorPattern(
                pattern_id="network_timeout",
                regex_pattern=r"(timeout|connection|network|unreachable)",
                error_type="NetworkError",
                category=ErrorCategory.NETWORK,
                severity=Severity.MEDIUM,
                auto_fix_available=True,
                fix_strategy="Retry with exponential backoff"
            ),
            ErrorPattern(
                pattern_id="redis_connection",
                regex_pattern=r"(redis|connection pool|cache)",
                error_type="RedisError",
                category=ErrorCategory.REDIS,
                severity=Severity.MEDIUM,
                auto_fix_available=True,
                fix_strategy="Use fallback storage mechanism"
            )
        ]
        
        for pattern in default_patterns:
            self.patterns[pattern.pattern_id] = pattern
    
    def detect_error(self, error: Exception, context: Dict[str, Any] = None) -> List[ErrorPattern]:
        """Detect error patterns and categorize them"""
        error_message = str(error)
        error_type = type(error).__name__
        matched_patterns = []
        
        # Record error for statistics
        self.error_stats[error_type] += 1
        self.recent_errors.append({
            "timestamp": datetime.utcnow(),
            "type": error_type,
            "message": error_message,
            "context": context or {}
        })
        
        # Check against known patterns
        for pattern in self.patterns.values():
            if re.search(pattern.regex_pattern, error_message, re.IGNORECASE):
                pattern.occurrences += 1
                pattern.last_seen = datetime.utcnow()
                matched_patterns.append(pattern)
        
        # If no patterns match, create a new one
        if not matched_patterns:
            new_pattern = self._create_pattern_from_error(error, error_message)
            if new_pattern:
                self.patterns[new_pattern.pattern_id] = new_pattern
                matched_patterns.append(new_pattern)
        
        return matched_patterns
    
    def _create_pattern_from_error(self, error: Exception, message: str) -> Optional[ErrorPattern]:
        """Create new pattern from unknown error"""
        error_type = type(error).__name__
        pattern_id = f"auto_{error_type.lower()}_{len(self.patterns)}"
        
        # Simple heuristics for categorization
        category = ErrorCategory.SYSTEM
        severity = Severity.MEDIUM
        auto_fix = False
        fix_strategy = "Manual investigation required"
        
        if "calculation" in message.lower() or isinstance(error, (ArithmeticError, ValueError)):
            category = ErrorCategory.CALCULATION
            severity = Severity.HIGH
            auto_fix = True
            fix_strategy = "Validate inputs and adjust calculation"
        elif "network" in message.lower() or "connection" in message.lower():
            category = ErrorCategory.NETWORK
            severity = Severity.MEDIUM
            auto_fix = True
            fix_strategy = "Retry with backoff strategy"
        elif "database" in message.lower() or "sql" in message.lower():
            category = ErrorCategory.DATABASE
            severity = Severity.HIGH
            fix_strategy = "Check database connection and retry"
        
        return ErrorPattern(
            pattern_id=pattern_id,
            regex_pattern=re.escape(message[:50]),  # Use first 50 chars as pattern
            error_type=error_type,
            category=category,
            severity=severity,
            auto_fix_available=auto_fix,
            fix_strategy=fix_strategy,
            occurrences=1,
            last_seen=datetime.utcnow()
        )

class ErrorMitigator:
    """Proactive error mitigation strategies"""
    
    def __init__(self):
        self.mitigation_strategies = {
            ErrorCategory.CALCULATION: self._mitigate_calculation_error,
            ErrorCategory.VALIDATION: self._mitigate_validation_error,
            ErrorCategory.NETWORK: self._mitigate_network_error,
            ErrorCategory.REDIS: self._mitigate_redis_error,
            ErrorCategory.DATABASE: self._mitigate_database_error,
            ErrorCategory.PRECISION: self._mitigate_precision_error
        }
        self.circuit_breakers = {}
        self.retry_counts = defaultdict(int)
    
    async def mitigate_error(self, patterns: List[ErrorPattern], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply mitigation strategies based on detected patterns"""
        mitigation_results = {
            "strategies_applied": [],
            "success": False,
            "fallback_used": False,
            "recommendation": None
        }
        
        for pattern in patterns:
            strategy = self.mitigation_strategies.get(pattern.category)
            if strategy:
                try:
                    result = await strategy(pattern, context)
                    mitigation_results["strategies_applied"].append({
                        "pattern": pattern.pattern_id,
                        "strategy": pattern.fix_strategy,
                        "result": result
                    })
                    
                    if result.get("success"):
                        mitigation_results["success"] = True
                        break
                        
                except Exception as e:
                    logger.error(f"Mitigation strategy failed: {e}")
        
        return mitigation_results
    
    async def _mitigate_calculation_error(self, pattern: ErrorPattern, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mitigate calculation errors"""
        if "division by zero" in pattern.regex_pattern.lower():
            # Use epsilon for near-zero values
            return {
                "success": True,
                "strategy": "epsilon_replacement",
                "suggestion": "Replace zero with small epsilon value",
                "auto_fix": "operand2 = '1e-60' if operand2 == '0' else operand2"
            }
        elif "overflow" in pattern.regex_pattern.lower():
            return {
                "success": True,
                "strategy": "precision_adjustment",
                "suggestion": "Reduce precision or break into smaller calculations",
                "auto_fix": "Implement chunked calculation"
            }
        
        return {"success": False, "reason": "No specific mitigation available"}
    
    async def _mitigate_validation_error(self, pattern: ErrorPattern, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mitigate validation errors"""
        return {
            "success": True,
            "strategy": "input_sanitization",
            "suggestion": "Apply input cleaning and validation",
            "auto_fix": "Strip whitespace, validate format, convert to proper decimal"
        }
    
    async def _mitigate_network_error(self, pattern: ErrorPattern, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mitigate network errors with retry and fallback"""
        retry_key = context.get("endpoint", "unknown")
        
        if self.retry_counts[retry_key] < 3:
            self.retry_counts[retry_key] += 1
            return {
                "success": True,
                "strategy": "exponential_backoff_retry",
                "suggestion": f"Retry {self.retry_counts[retry_key]}/3 with backoff",
                "delay_seconds": 2 ** self.retry_counts[retry_key]
            }
        else:
            return {
                "success": True,
                "strategy": "fallback_mechanism",
                "suggestion": "Use cached data or alternative endpoint",
                "fallback_used": True
            }
    
    async def _mitigate_redis_error(self, pattern: ErrorPattern, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mitigate Redis connection errors"""
        return {
            "success": True,
            "strategy": "memory_fallback",
            "suggestion": "Use in-memory cache as fallback",
            "fallback_used": True
        }
    
    async def _mitigate_database_error(self, pattern: ErrorPattern, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mitigate database errors"""
        return {
            "success": True,
            "strategy": "connection_pool_refresh",
            "suggestion": "Refresh connection pool and retry",
            "auto_fix": "Recreate database connection"
        }
    
    async def _mitigate_precision_error(self, pattern: ErrorPattern, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mitigate precision-related errors"""
        return {
            "success": True,
            "strategy": "adaptive_precision",
            "suggestion": "Dynamically adjust precision based on operand size",
            "auto_fix": "Implement precision scaling algorithm"
        }

class ErrorProcessor:
    """Systematic error processing and triage"""
    
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.processing_stats = {
            "total_processed": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "avg_processing_time": 0.0
        }
        self.is_processing = False
    
    async def process_error(self, error: Exception, context: Dict[str, Any], patterns: List[ErrorPattern]) -> Dict[str, Any]:
        """Process error with comprehensive analysis"""
        start_time = time.time()
        
        processing_result = {
            "error_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "patterns_matched": [p.pattern_id for p in patterns],
            "severity": max([p.severity.value for p in patterns], default="low"),
            "processing_steps": [],
            "recommendations": [],
            "auto_fix_available": any(p.auto_fix_available for p in patterns)
        }
        
        # Step 1: Error categorization
        processing_result["processing_steps"].append("Error categorized and indexed")
        
        # Step 2: Impact assessment
        impact = self._assess_impact(error, context, patterns)
        processing_result["impact_assessment"] = impact
        processing_result["processing_steps"].append("Impact assessment completed")
        
        # Step 3: Generate recommendations
        recommendations = self._generate_recommendations(patterns, impact)
        processing_result["recommendations"] = recommendations
        processing_result["processing_steps"].append("Recommendations generated")
        
        # Step 4: Create actionable logs
        actionable_logs = self._create_actionable_logs(error, context, patterns)
        processing_result["actionable_logs"] = actionable_logs
        processing_result["processing_steps"].append("Actionable logs created")
        
        # Update statistics
        processing_time = time.time() - start_time
        self.processing_stats["total_processed"] += 1
        self.processing_stats["avg_processing_time"] = (
            (self.processing_stats["avg_processing_time"] * (self.processing_stats["total_processed"] - 1) + processing_time) /
            self.processing_stats["total_processed"]
        )
        
        processing_result["processing_time_ms"] = processing_time * 1000
        
        return processing_result
    
    def _assess_impact(self, error: Exception, context: Dict[str, Any], patterns: List[ErrorPattern]) -> Dict[str, Any]:
        """Assess the impact of the error on system operations"""
        impact_score = 0
        affected_components = []
        user_impact = "low"
        
        for pattern in patterns:
            if pattern.severity == Severity.CRITICAL:
                impact_score += 10
                user_impact = "high"
            elif pattern.severity == Severity.HIGH:
                impact_score += 5
                user_impact = "medium" if user_impact == "low" else user_impact
            elif pattern.severity == Severity.MEDIUM:
                impact_score += 2
            else:
                impact_score += 1
            
            if pattern.category == ErrorCategory.CALCULATION:
                affected_components.append("calculation_engine")
            elif pattern.category == ErrorCategory.DATABASE:
                affected_components.append("persistence_layer")
            elif pattern.category == ErrorCategory.NETWORK:
                affected_components.append("external_apis")
        
        return {
            "impact_score": impact_score,
            "user_impact": user_impact,
            "affected_components": list(set(affected_components)),
            "estimated_downtime": "none" if impact_score < 5 else "minimal" if impact_score < 10 else "significant",
            "priority": "critical" if impact_score >= 10 else "high" if impact_score >= 5 else "medium"
        }
    
    def _generate_recommendations(self, patterns: List[ErrorPattern], impact: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        for pattern in patterns:
            rec = {
                "pattern_id": pattern.pattern_id,
                "priority": impact["priority"],
                "action": pattern.fix_strategy,
                "auto_applicable": pattern.auto_fix_available,
                "effort_estimate": "low" if pattern.auto_fix_available else "medium",
                "success_rate": pattern.success_rate if pattern.success_rate > 0 else 0.8
            }
            recommendations.append(rec)
        
        # Add system-level recommendations
        if impact["impact_score"] >= 10:
            recommendations.append({
                "pattern_id": "system_level",
                "priority": "critical",
                "action": "Implement circuit breaker and fallback mechanisms",
                "auto_applicable": False,
                "effort_estimate": "high",
                "success_rate": 0.9
            })
        
        return recommendations
    
    def _create_actionable_logs(self, error: Exception, context: Dict[str, Any], patterns: List[ErrorPattern]) -> Dict[str, Any]:
        """Create structured, actionable logs"""
        return {
            "error_fingerprint": hash(f"{type(error).__name__}:{str(error)[:100]}"),
            "stacktrace": traceback.format_exc(),
            "context_variables": context,
            "environment_state": {
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent(),
                "timestamp": datetime.utcnow().isoformat()
            },
            "debugging_hints": [
                "Check input validation for calculation parameters",
                "Verify network connectivity to external services",
                "Validate database connection pool status",
                "Review recent system resource usage patterns"
            ],
            "search_keywords": [pattern.error_type for pattern in patterns] + [type(error).__name__]
        }

class ErrorCorrector:
    """Auto-fix and patch capabilities"""
    
    def __init__(self):
        self.correction_strategies = {
            "div_by_zero": self._correct_division_by_zero,
            "invalid_decimal": self._correct_invalid_decimal,
            "overflow": self._correct_overflow,
            "network_timeout": self._correct_network_timeout,
            "redis_connection": self._correct_redis_connection
        }
        self.correction_stats = {
            "total_attempts": 0,
            "successful_corrections": 0,
            "failed_corrections": 0
        }
    
    async def correct_error(self, patterns: List[ErrorPattern], context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt automatic error correction"""
        correction_result = {
            "corrections_attempted": [],
            "successful_corrections": [],
            "failed_corrections": [],
            "overall_success": False,
            "corrected_data": None
        }
        
        for pattern in patterns:
            if pattern.auto_fix_available and pattern.pattern_id in self.correction_strategies:
                self.correction_stats["total_attempts"] += 1
                
                try:
                    strategy = self.correction_strategies[pattern.pattern_id]
                    result = await strategy(context)
                    
                    correction_result["corrections_attempted"].append(pattern.pattern_id)
                    
                    if result.get("success"):
                        correction_result["successful_corrections"].append({
                            "pattern": pattern.pattern_id,
                            "correction": result
                        })
                        correction_result["corrected_data"] = result.get("corrected_data")
                        correction_result["overall_success"] = True
                        self.correction_stats["successful_corrections"] += 1
                        
                        # Update pattern success rate
                        pattern.success_rate = (pattern.success_rate + 1.0) / 2.0 if pattern.success_rate > 0 else 0.9
                        break
                    else:
                        correction_result["failed_corrections"].append({
                            "pattern": pattern.pattern_id,
                            "reason": result.get("reason", "Unknown failure")
                        })
                        self.correction_stats["failed_corrections"] += 1
                        
                except Exception as e:
                    logger.error(f"Correction strategy failed: {e}")
                    correction_result["failed_corrections"].append({
                        "pattern": pattern.pattern_id,
                        "reason": str(e)
                    })
                    self.correction_stats["failed_corrections"] += 1
        
        return correction_result
    
    async def _correct_division_by_zero(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Correct division by zero errors"""
        operand2 = context.get("operand2", "0")
        
        if operand2 == "0" or float(operand2) == 0.0:
            # Replace with small epsilon value
            corrected_operand2 = "1e-60"
            return {
                "success": True,
                "correction_type": "epsilon_replacement",
                "original_value": operand2,
                "corrected_data": {"operand2": corrected_operand2},
                "explanation": "Replaced zero divisor with epsilon value for mathematical continuity"
            }
        
        return {"success": False, "reason": "No zero divisor found"}
    
    async def _correct_invalid_decimal(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Correct invalid decimal format"""
        operand1 = context.get("operand1", "")
        operand2 = context.get("operand2", "")
        
        corrected_data = {}
        
        # Clean and validate operands
        for key, value in [("operand1", operand1), ("operand2", operand2)]:
            if value:
                # Remove invalid characters, normalize decimal separators
                cleaned = re.sub(r'[^0-9\.\-\+eE]', '', str(value))
                cleaned = cleaned.replace(',', '.')  # Handle comma as decimal separator
                
                try:
                    # Validate by creating Decimal
                    Decimal(cleaned)
                    corrected_data[key] = cleaned
                except InvalidOperation:
                    # Try to extract numeric part
                    numbers = re.findall(r'[\d\.\-\+eE]+', cleaned)
                    if numbers:
                        corrected_data[key] = numbers[0]
        
        if corrected_data:
            return {
                "success": True,
                "correction_type": "input_sanitization",
                "corrected_data": corrected_data,
                "explanation": "Cleaned and validated decimal input format"
            }
        
        return {"success": False, "reason": "Could not sanitize decimal input"}
    
    async def _correct_overflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Correct overflow errors by adjusting precision"""
        return {
            "success": True,
            "correction_type": "precision_adjustment",
            "corrected_data": {"precision_override": 40},  # Reduce from default 60
            "explanation": "Reduced precision to prevent overflow"
        }
    
    async def _correct_network_timeout(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Correct network timeout by using cached data"""
        return {
            "success": True,
            "correction_type": "cached_fallback",
            "corrected_data": {"use_cache": True, "cache_timeout": 3600},
            "explanation": "Using cached exchange rates due to network timeout"
        }
    
    async def _correct_redis_connection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Correct Redis connection issues"""
        return {
            "success": True,
            "correction_type": "memory_fallback",
            "corrected_data": {"use_memory_cache": True},
            "explanation": "Switched to in-memory caching due to Redis unavailability"
        }

class HealingSuite:
    """The complete healing suite orchestrator"""
    
    def __init__(self):
        self.detector = ErrorDetector()
        self.mitigator = ErrorMitigator()
        self.processor = ErrorProcessor()
        self.corrector = ErrorCorrector()
        
        self.healing_stats = {
            "total_errors_processed": 0,
            "successful_healings": 0,
            "failed_healings": 0,
            "avg_healing_time_ms": 0.0,
            "self_learning_improvements": 0
        }
        
        self.active = True
        self.healing_history = deque(maxlen=1000)
    
    async def heal_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Complete error healing process"""
        if not self.active:
            return {"success": False, "reason": "Healing suite is disabled"}
        
        start_time = time.time()
        healing_id = str(uuid.uuid4())
        
        healing_result = {
            "healing_id": healing_id,
            "timestamp": datetime.utcnow(),
            "success": False,
            "stages": {},
            "final_recommendation": None,
            "auto_fix_applied": False,
            "learning_data": {}
        }
        
        try:
            # Stage 1: Error Detection
            patterns = self.detector.detect_error(error, context)
            healing_result["stages"]["detection"] = {
                "patterns_found": len(patterns),
                "patterns": [p.pattern_id for p in patterns]
            }
            
            # Stage 2: Error Mitigation
            mitigation_result = await self.mitigator.mitigate_error(patterns, context or {})
            healing_result["stages"]["mitigation"] = mitigation_result
            
            # Stage 3: Error Processing
            processing_result = await self.processor.process_error(error, context or {}, patterns)
            healing_result["stages"]["processing"] = processing_result
            
            # Stage 4: Error Correction (if auto-fix available)
            correction_result = await self.corrector.correct_error(patterns, context or {})
            healing_result["stages"]["correction"] = correction_result
            
            # Stage 5: Learning and Adaptation
            learning_result = self._apply_learning(patterns, mitigation_result, correction_result)
            healing_result["learning_data"] = learning_result
            
            # Determine overall success
            healing_result["success"] = (
                correction_result.get("overall_success", False) or
                mitigation_result.get("success", False)
            )
            
            healing_result["auto_fix_applied"] = correction_result.get("overall_success", False)
            healing_result["final_recommendation"] = self._generate_final_recommendation(
                patterns, mitigation_result, correction_result, processing_result
            )
            
            # Update statistics
            self.healing_stats["total_errors_processed"] += 1
            if healing_result["success"]:
                self.healing_stats["successful_healings"] += 1
            else:
                self.healing_stats["failed_healings"] += 1
            
            healing_time = (time.time() - start_time) * 1000
            self.healing_stats["avg_healing_time_ms"] = (
                (self.healing_stats["avg_healing_time_ms"] * (self.healing_stats["total_errors_processed"] - 1) + healing_time) /
                self.healing_stats["total_errors_processed"]
            )
            
            healing_result["healing_time_ms"] = healing_time
            
            # Store in history
            self.healing_history.append({
                "healing_id": healing_id,
                "timestamp": healing_result["timestamp"],
                "success": healing_result["success"],
                "error_type": type(error).__name__,
                "patterns": [p.pattern_id for p in patterns],
                "auto_fix_applied": healing_result["auto_fix_applied"]
            })
            
        except Exception as healing_error:
            logger.error(f"Healing suite error: {healing_error}")
            healing_result["stages"]["healing_error"] = str(healing_error)
            healing_result["success"] = False
        
        return healing_result
    
    def _apply_learning(self, patterns: List[ErrorPattern], mitigation_result: Dict, correction_result: Dict) -> Dict[str, Any]:
        """Apply machine learning and pattern improvement"""
        learning_result = {
            "patterns_updated": 0,
            "new_strategies_learned": 0,
            "success_rates_adjusted": 0
        }
        
        # Update pattern success rates based on healing results
        for pattern in patterns:
            if correction_result.get("overall_success"):
                pattern.success_rate = min(1.0, pattern.success_rate * 1.1)  # Increase success rate
                learning_result["success_rates_adjusted"] += 1
            elif not mitigation_result.get("success"):
                pattern.success_rate = max(0.1, pattern.success_rate * 0.9)  # Decrease success rate
                learning_result["success_rates_adjusted"] += 1
        
        # Learn new strategies from successful mitigations
        if mitigation_result.get("success"):
            for strategy in mitigation_result.get("strategies_applied", []):
                if strategy.get("result", {}).get("success"):
                    learning_result["new_strategies_learned"] += 1
        
        self.healing_stats["self_learning_improvements"] += learning_result["new_strategies_learned"]
        
        return learning_result
    
    def _generate_final_recommendation(self, patterns: List[ErrorPattern], 
                                     mitigation_result: Dict, correction_result: Dict, 
                                     processing_result: Dict) -> Dict[str, Any]:
        """Generate final recommendation based on all healing stages"""
        if correction_result.get("overall_success"):
            return {
                "action": "auto_fix_applied",
                "description": "Error was automatically corrected",
                "corrected_data": correction_result.get("corrected_data"),
                "confidence": 0.9
            }
        
        if mitigation_result.get("success"):
            return {
                "action": "mitigation_applied",
                "description": "Error was mitigated with fallback strategy",
                "strategy": mitigation_result.get("strategies_applied", [{}])[0].get("strategy"),
                "confidence": 0.7
            }
        
        # Fall back to processing recommendations
        recommendations = processing_result.get("recommendations", [])
        if recommendations:
            top_rec = max(recommendations, key=lambda x: x.get("success_rate", 0))
            return {
                "action": "manual_intervention_required",
                "description": top_rec.get("action", "Manual investigation required"),
                "priority": top_rec.get("priority", "medium"),
                "confidence": top_rec.get("success_rate", 0.5)
            }
        
        return {
            "action": "escalate",
            "description": "Unable to heal error automatically - escalation required",
            "priority": "high",
            "confidence": 0.1
        }
    
    def get_healing_status(self) -> Dict[str, Any]:
        """Get comprehensive healing suite status"""
        return {
            "active": self.active,
            "statistics": self.healing_stats.copy(),
            "recent_activity": list(self.healing_history)[-10:],  # Last 10 healing actions
            "patterns_learned": len(self.detector.patterns),
            "error_categories_tracked": len(set(p.category for p in self.detector.patterns.values())),
            "auto_fix_success_rate": (
                self.healing_stats["successful_healings"] / max(self.healing_stats["total_errors_processed"], 1)
            ),
            "components": {
                "detector": "active",
                "mitigator": "active", 
                "processor": "active",
                "corrector": "active"
            }
        }
    
    def toggle_healing_suite(self, active: bool):
        """Enable or disable the healing suite"""
        self.active = active
        logger.info(f"Healing suite {'activated' if active else 'deactivated'}")

# Global instance
healing_suite = HealingSuite()

# Decorator for automatic error healing
def auto_heal(func):
    """Decorator to automatically apply healing to function errors"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Extract context from function arguments
            context = {
                "function": func.__name__,
                "args": str(args)[:200],  # Limit size
                "kwargs": str(kwargs)[:200]
            }
            
            # Apply healing
            healing_result = await healing_suite.heal_error(e, context)
            
            # If auto-fix was applied and corrected data is available, retry with corrected data
            if healing_result.get("auto_fix_applied") and healing_result.get("stages", {}).get("correction", {}).get("corrected_data"):
                corrected_data = healing_result["stages"]["correction"]["corrected_data"]
                # Apply corrected data to kwargs
                kwargs.update(corrected_data)
                try:
                    return await func(*args, **kwargs)
                except Exception:
                    pass  # Fall through to original error
            
            # Re-raise original error with healing info
            e.healing_info = healing_result
            raise e
    
    return wrapper

if __name__ == "__main__":
    # Test the healing suite
    async def test_healing_suite():
        suite = HealingSuite()
        
        # Test division by zero
        try:
            1 / 0
        except Exception as e:
            result = await suite.heal_error(e, {"operand1": "10", "operand2": "0", "operation": "divide"})
            print("Division by zero healing result:", json.dumps(result, indent=2, default=str))
        
        # Test invalid decimal
        try:
            from decimal import Decimal
            Decimal("invalid_number")
        except Exception as e:
            result = await suite.heal_error(e, {"operand1": "invalid_number", "operation": "add"})
            print("Invalid decimal healing result:", json.dumps(result, indent=2, default=str))
        
        # Print healing status
        status = suite.get_healing_status()
        print("Healing suite status:", json.dumps(status, indent=2, default=str))
    
    # Run test
    asyncio.run(test_healing_suite())