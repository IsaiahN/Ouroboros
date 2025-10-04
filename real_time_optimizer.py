#!/usr/bin/env python3
"""
REAL-TIME ADAPTIVE OPTIMIZATION SYSTEM
======================================
Phase 1 Implementation: +100% improvement target

Revolutionary performance monitoring and adaptive optimization system
that continuously monitors game performance and makes real-time adjustments
to strategies, parameters, and decision-making processes.
"""

import time
import json
import logging
import asyncio
import sqlite3
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import threading

logger = logging.getLogger(__name__)

class OptimizationLevel(Enum):
    """Performance optimization urgency levels."""
    NORMAL = "normal"
    ATTENTION = "attention"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class PerformanceMetrics:
    """Real-time performance tracking metrics."""
    timestamp: float
    game_id: str
    session_id: str
    action_number: int
    action_type: str
    algorithm_id: str

    # Performance indicators
    score_change: float
    score_efficiency: float  # score_change / actions_taken
    action_success_rate: float
    decision_time_ms: float

    # Strategic metrics
    coordinate_effectiveness: float
    algorithm_confidence: float
    ensemble_agreement: float

    # System metrics
    memory_usage_mb: float
    cpu_usage_percent: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class OptimizationRecommendation:
    """Adaptive optimization recommendation."""
    urgency: OptimizationLevel
    category: str  # "coordinate", "algorithm", "strategy", "system"
    description: str
    suggested_action: str
    expected_improvement: float
    confidence: float

class RealTimeOptimizer:
    """Revolutionary real-time performance optimization system."""

    def __init__(self, db_path: str = "core_data.db", monitoring_window: int = 100):
        """Initialize the real-time optimizer.

        Args:
            db_path: Database path for persistence
            monitoring_window: Number of recent actions to analyze
        """
        self.db_path = db_path
        self.monitoring_window = monitoring_window

        # Performance tracking
        self.metrics_buffer = deque(maxlen=monitoring_window)
        self.session_metrics: Dict[str, List[PerformanceMetrics]] = defaultdict(list)

        # Optimization state
        self.current_optimization_level = OptimizationLevel.NORMAL
        self.active_recommendations: List[OptimizationRecommendation] = []
        self.optimization_history: List[Dict[str, Any]] = []

        # Performance baselines and targets
        self.performance_baselines = {
            "min_score_efficiency": 0.01,  # Minimum score per action
            "min_success_rate": 0.15,      # Minimum action success rate
            "max_decision_time": 2000.0,   # Maximum decision time in ms
            "target_score_efficiency": 0.05,  # Target score per action
            "target_success_rate": 0.35,   # Target success rate
        }

        # Adaptive parameters
        self.adaptive_parameters = {
            "coordinate_exploration_rate": 0.2,
            "algorithm_switching_threshold": 0.1,
            "ensemble_confidence_threshold": 0.7,
            "emergency_fallback_enabled": True,
        }

        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None

        logger.info("RealTimeOptimizer initialized with real-time monitoring capabilities")

    def start_monitoring(self):
        """Start real-time performance monitoring."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("Real-time performance monitoring started")

    def stop_monitoring(self):
        """Stop real-time performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logger.info("Real-time performance monitoring stopped")

    def _monitoring_loop(self):
        """Continuous monitoring loop running in background thread."""
        while self.monitoring_active:
            try:
                # Analyze recent performance every 5 seconds
                if len(self.metrics_buffer) >= 5:
                    self._analyze_performance_trends()
                    self._generate_optimization_recommendations()
                    self._apply_adaptive_adjustments()

                time.sleep(5.0)  # Monitor every 5 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10.0)  # Back off on error

    def record_performance_metric(self, metric: PerformanceMetrics):
        """Record a new performance metric for real-time analysis."""
        # Add timestamp if not set
        if metric.timestamp == 0:
            metric.timestamp = time.time()

        # Calculate derived metrics
        metric.score_efficiency = metric.score_change / max(1, metric.action_number)

        # Add to buffers
        self.metrics_buffer.append(metric)
        self.session_metrics[metric.session_id].append(metric)

        # Store in database
        self._store_metric_to_db(metric)

        # Immediate critical analysis
        if metric.score_change < -0.5 or metric.decision_time_ms > 5000:
            self._trigger_emergency_optimization(metric)

    def _analyze_performance_trends(self):
        """Analyze recent performance trends and detect issues."""
        if len(self.metrics_buffer) < 10:
            return

        recent_metrics = list(self.metrics_buffer)[-20:]  # Last 20 actions

        # Calculate trend indicators
        score_changes = [m.score_change for m in recent_metrics]
        success_rates = [m.action_success_rate for m in recent_metrics if m.action_success_rate >= 0]
        decision_times = [m.decision_time_ms for m in recent_metrics]
        score_efficiencies = [m.score_efficiency for m in recent_metrics]

        # Performance analysis
        avg_score_change = statistics.mean(score_changes) if score_changes else 0.0
        avg_success_rate = statistics.mean(success_rates) if success_rates else 0.0
        avg_decision_time = statistics.mean(decision_times) if decision_times else 0.0
        avg_score_efficiency = statistics.mean(score_efficiencies) if score_efficiencies else 0.0

        # Trend detection
        recent_score_trend = self._calculate_trend(score_changes[-10:]) if len(score_changes) >= 10 else 0.0
        performance_deterioration = recent_score_trend < -0.01 and avg_score_change < 0.0

        # Update optimization level
        previous_level = self.current_optimization_level

        if (avg_score_efficiency < self.performance_baselines["min_score_efficiency"] or
            avg_success_rate < self.performance_baselines["min_success_rate"] or
            performance_deterioration):

            if avg_score_change < -0.2:
                self.current_optimization_level = OptimizationLevel.EMERGENCY
            elif avg_score_efficiency < 0.005:
                self.current_optimization_level = OptimizationLevel.CRITICAL
            else:
                self.current_optimization_level = OptimizationLevel.ATTENTION
        else:
            self.current_optimization_level = OptimizationLevel.NORMAL

        # Log level changes
        if self.current_optimization_level != previous_level:
            logger.warning(f"Optimization level changed: {previous_level.value} -> {self.current_optimization_level.value}")
            logger.info(f"Performance indicators - Efficiency: {avg_score_efficiency:.4f}, Success: {avg_success_rate:.3f}, Trend: {recent_score_trend:.4f}")

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend slope for a series of values."""
        if len(values) < 3:
            return 0.0

        n = len(values)
        x_values = list(range(n))

        # Simple linear regression slope
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n

        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0.0

    def _generate_optimization_recommendations(self):
        """Generate adaptive optimization recommendations based on current performance."""
        self.active_recommendations.clear()

        if len(self.metrics_buffer) < 10:
            return

        recent_metrics = list(self.metrics_buffer)[-15:]

        # Coordinate optimization analysis
        coordinate_effectiveness = [m.coordinate_effectiveness for m in recent_metrics if m.coordinate_effectiveness >= 0]
        if coordinate_effectiveness and statistics.mean(coordinate_effectiveness) < 0.3:
            self.active_recommendations.append(OptimizationRecommendation(
                urgency=OptimizationLevel.ATTENTION,
                category="coordinate",
                description="Low coordinate effectiveness detected",
                suggested_action="Increase exploration rate and diversify coordinate selection",
                expected_improvement=0.15,
                confidence=0.75
            ))

        # Algorithm performance analysis
        algorithm_performance = defaultdict(list)
        for metric in recent_metrics:
            algorithm_performance[metric.algorithm_id].append(metric.score_change)

        for algo_id, scores in algorithm_performance.items():
            if len(scores) >= 3 and statistics.mean(scores) < -0.05:
                self.active_recommendations.append(OptimizationRecommendation(
                    urgency=OptimizationLevel.CRITICAL,
                    category="algorithm",
                    description=f"Algorithm {algo_id} showing poor performance",
                    suggested_action=f"Reduce usage of {algo_id} and boost alternative algorithms",
                    expected_improvement=0.20,
                    confidence=0.80
                ))

        # Decision time optimization
        decision_times = [m.decision_time_ms for m in recent_metrics]
        if decision_times and statistics.mean(decision_times) > self.performance_baselines["max_decision_time"]:
            self.active_recommendations.append(OptimizationRecommendation(
                urgency=OptimizationLevel.ATTENTION,
                category="system",
                description="High decision times detected",
                suggested_action="Enable decision time limits and faster fallback strategies",
                expected_improvement=0.10,
                confidence=0.65
            ))

        # Ensemble agreement analysis
        ensemble_agreements = [m.ensemble_agreement for m in recent_metrics if m.ensemble_agreement >= 0]
        if ensemble_agreements and statistics.mean(ensemble_agreements) < 0.5:
            self.active_recommendations.append(OptimizationRecommendation(
                urgency=OptimizationLevel.ATTENTION,
                category="strategy",
                description="Low ensemble agreement - algorithms disagree frequently",
                suggested_action="Adjust ensemble weights and confidence thresholds",
                expected_improvement=0.12,
                confidence=0.70
            ))

    def _apply_adaptive_adjustments(self):
        """Apply adaptive parameter adjustments based on recommendations."""
        for recommendation in self.active_recommendations:
            if recommendation.confidence >= 0.7:

                if recommendation.category == "coordinate" and "exploration" in recommendation.suggested_action:
                    # Increase coordinate exploration
                    current_rate = self.adaptive_parameters["coordinate_exploration_rate"]
                    new_rate = min(0.8, current_rate * 1.2)
                    self.adaptive_parameters["coordinate_exploration_rate"] = new_rate
                    logger.info(f"Adaptive adjustment: Coordinate exploration rate {current_rate:.3f} -> {new_rate:.3f}")

                elif recommendation.category == "algorithm":
                    # Adjust algorithm switching threshold
                    current_threshold = self.adaptive_parameters["algorithm_switching_threshold"]
                    new_threshold = max(0.05, current_threshold * 0.8)
                    self.adaptive_parameters["algorithm_switching_threshold"] = new_threshold
                    logger.info(f"Adaptive adjustment: Algorithm switching threshold {current_threshold:.3f} -> {new_threshold:.3f}")

                elif recommendation.category == "strategy" and "ensemble" in recommendation.suggested_action:
                    # Adjust ensemble confidence threshold
                    current_threshold = self.adaptive_parameters["ensemble_confidence_threshold"]
                    new_threshold = max(0.5, current_threshold * 0.9)
                    self.adaptive_parameters["ensemble_confidence_threshold"] = new_threshold
                    logger.info(f"Adaptive adjustment: Ensemble confidence threshold {current_threshold:.3f} -> {new_threshold:.3f}")

        # Emergency fallback activation
        if self.current_optimization_level == OptimizationLevel.EMERGENCY:
            self.adaptive_parameters["emergency_fallback_enabled"] = True
            logger.warning("Emergency optimization mode activated - enabling all fallback strategies")

    def _trigger_emergency_optimization(self, metric: PerformanceMetrics):
        """Trigger immediate emergency optimization for critical performance issues."""
        logger.critical(f"Emergency optimization triggered - Action: {metric.action_type}, "
                        f"Score change: {metric.score_change}, Decision time: {metric.decision_time_ms}ms")

        # Immediate parameter adjustments
        if metric.score_change < -0.3:
            self.adaptive_parameters["coordinate_exploration_rate"] = 0.6  # High exploration
            self.adaptive_parameters["algorithm_switching_threshold"] = 0.05  # Quick switching

        if metric.decision_time_ms > 3000:
            self.adaptive_parameters["emergency_fallback_enabled"] = True
            logger.warning("Decision time emergency - enabling fast fallback strategies")

    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status and recommendations."""
        recent_metrics = list(self.metrics_buffer)[-10:] if self.metrics_buffer else []

        # Calculate recent performance
        recent_score_changes = [m.score_change for m in recent_metrics]
        recent_efficiencies = [m.score_efficiency for m in recent_metrics]

        return {
            "optimization_level": self.current_optimization_level.value,
            "monitoring_active": self.monitoring_active,
            "recent_actions_analyzed": len(recent_metrics),
            "recent_avg_score_change": statistics.mean(recent_score_changes) if recent_score_changes else 0.0,
            "recent_avg_efficiency": statistics.mean(recent_efficiencies) if recent_efficiencies else 0.0,
            "active_recommendations": [
                {
                    "urgency": rec.urgency.value,
                    "category": rec.category,
                    "description": rec.description,
                    "expected_improvement": rec.expected_improvement,
                    "confidence": rec.confidence
                }
                for rec in self.active_recommendations
            ],
            "adaptive_parameters": self.adaptive_parameters.copy(),
            "performance_baselines": self.performance_baselines.copy()
        }

    def get_adaptive_parameter(self, parameter_name: str, default_value: Any = None) -> Any:
        """Get current adaptive parameter value for use by other systems."""
        return self.adaptive_parameters.get(parameter_name, default_value)

    def _store_metric_to_db(self, metric: PerformanceMetrics):
        """Store performance metric to database for historical analysis."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    timestamp REAL,
                    game_id TEXT,
                    session_id TEXT,
                    action_number INTEGER,
                    action_type TEXT,
                    algorithm_id TEXT,
                    score_change REAL,
                    score_efficiency REAL,
                    action_success_rate REAL,
                    decision_time_ms REAL,
                    coordinate_effectiveness REAL,
                    algorithm_confidence REAL,
                    ensemble_agreement REAL,
                    memory_usage_mb REAL,
                    cpu_usage_percent REAL
                )
            """)

            # Insert metric
            cursor.execute("""
                INSERT INTO performance_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.timestamp, metric.game_id, metric.session_id, metric.action_number,
                metric.action_type, metric.algorithm_id, metric.score_change, metric.score_efficiency,
                metric.action_success_rate, metric.decision_time_ms, metric.coordinate_effectiveness,
                metric.algorithm_confidence, metric.ensemble_agreement, metric.memory_usage_mb,
                metric.cpu_usage_percent
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing performance metric: {e}")

# Global instance
real_time_optimizer = RealTimeOptimizer()

def start_performance_monitoring():
    """Start global performance monitoring."""
    real_time_optimizer.start_monitoring()

def stop_performance_monitoring():
    """Stop global performance monitoring."""
    real_time_optimizer.stop_monitoring()

def record_action_performance(game_id: str, session_id: str, action_number: int,
                            action_type: str, algorithm_id: str, score_change: float,
                            decision_time_ms: float = 0.0, coordinate_effectiveness: float = -1.0,
                            algorithm_confidence: float = -1.0, ensemble_agreement: float = -1.0) -> None:
    """Record performance metrics for an action."""

    # Calculate action success
    action_success = 1.0 if score_change > 0 else 0.0

    metric = PerformanceMetrics(
        timestamp=time.time(),
        game_id=game_id,
        session_id=session_id,
        action_number=action_number,
        action_type=action_type,
        algorithm_id=algorithm_id,
        score_change=score_change,
        score_efficiency=0.0,  # Calculated in record_performance_metric
        action_success_rate=action_success,
        decision_time_ms=decision_time_ms,
        coordinate_effectiveness=coordinate_effectiveness,
        algorithm_confidence=algorithm_confidence,
        ensemble_agreement=ensemble_agreement,
        memory_usage_mb=0.0,  # TODO: Add system monitoring
        cpu_usage_percent=0.0
    )

    real_time_optimizer.record_performance_metric(metric)

def get_optimization_recommendations() -> Dict[str, Any]:
    """Get current optimization status and recommendations."""
    return real_time_optimizer.get_optimization_status()

def get_adaptive_parameter(parameter_name: str, default_value: Any = None) -> Any:
    """Get adaptive parameter for use by other systems."""
    return real_time_optimizer.get_adaptive_parameter(parameter_name, default_value)

if __name__ == "__main__":
    # Test the real-time optimizer
    optimizer = RealTimeOptimizer()
    optimizer.start_monitoring()

    print("=== REAL-TIME OPTIMIZER TEST ===")

    # Simulate some performance metrics
    import random
    for i in range(20):
        score_change = random.uniform(-0.2, 0.3)
        decision_time = random.uniform(500, 2500)

        metric = PerformanceMetrics(
            timestamp=time.time(),
            game_id="test_game",
            session_id="test_session",
            action_number=i+1,
            action_type=f"ACTION{random.randint(1,7)}",
            algorithm_id=f"test_algorithm_{i%3}",
            score_change=score_change,
            score_efficiency=0.0,
            action_success_rate=1.0 if score_change > 0 else 0.0,
            decision_time_ms=decision_time,
            coordinate_effectiveness=random.uniform(0.2, 0.8),
            algorithm_confidence=random.uniform(0.3, 0.9),
            ensemble_agreement=random.uniform(0.4, 0.8),
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0
        )

        optimizer.record_performance_metric(metric)
        time.sleep(0.1)

    # Get status
    time.sleep(2.0)  # Let monitoring analyze
    status = optimizer.get_optimization_status()
    print(f"\nOptimization Status: {status}")

    optimizer.stop_monitoring()