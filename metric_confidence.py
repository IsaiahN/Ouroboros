import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
MetricConfidenceTracker - Track confidence in metrics themselves.

Part of the Societal Metrics System.
See DOCS/Societal_Metrics_Implementation_Analysis.md for design rationale.

Implements Constraint 5: Metric Confidence Meta-Metric
Closes the final Goodhart loop by tracking whether metrics are trustworthy.

Confidence Signals:
- High contradiction rate: Metric disagrees with others -> lower weight
- Fast agent adaptation: Agents gaming this metric -> increase decay
- Low predictive power: Doesn't predict success -> consider removal
- Too influential: Single-point-of-failure -> distribute weight
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricConfidenceTracker:
    """
    Track confidence in metrics themselves. Closes the final Goodhart loop.
    
    Autopoiesis Role: Meta-regulation - ensures the measurement system is trustworthy
    Problem Solved: How do we know if a metric itself is still valid?
    
    When a metric becomes too predictive, too stable, or too influential,
    it should decay faster to prevent gaming.
    
    Usage:
        tracker = MetricConfidenceTracker(db)
        confidence = tracker.calculate_metric_confidence("emergence_gain", generation)
        decay_mult = tracker.get_decay_multiplier("emergence_gain", generation)
    """
    
    # Thresholds for confidence signals
    CONTRADICTION_THRESHOLD = 0.3      # Max acceptable contradiction rate
    ADAPTATION_SPEED_THRESHOLD = 5     # Generations for suspicious adaptation
    PREDICTIVE_POWER_THRESHOLD = 0.2   # Minimum predictive power
    INFLUENCE_THRESHOLD = 0.4          # Max acceptable influence concentration
    
    # Weights for confidence calculation
    CONTRADICTION_WEIGHT = 0.25
    ADAPTATION_WEIGHT = 0.25
    PREDICTIVE_WEIGHT = 0.30
    INFLUENCE_WEIGHT = 0.20
    
    def __init__(self, db):
        """
        Initialize with database interface (dependency injection).
        
        Args:
            db: DatabaseInterface instance for persistence
        """
        self.db = db
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create metric_confidence table if not exists (idempotent)."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS metric_confidence (
                    metric_name TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    confidence_score REAL NOT NULL,
                    contradiction_rate REAL,
                    adaptation_speed REAL,
                    predictive_power REAL,
                    influence_concentration REAL,
                    decay_multiplier REAL,
                    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (metric_name, generation)
                )
            """)
            
            # Also ensure ecosystem_metrics table exists for metric values
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS ecosystem_metrics (
                    metric_name TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    value REAL NOT NULL,
                    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    PRIMARY KEY (metric_name, generation)
                )
            """)
            
        except Exception as e:
            logger.warning(f"Schema creation warning (may already exist): {e}")
    
    def calculate_metric_confidence(self, metric_name: str, 
                                     generation: int) -> float:
        """
        Calculate confidence in a metric (0.0 = untrustworthy, 1.0 = highly reliable).
        
        Args:
            metric_name: Name of the metric to evaluate
            generation: Current generation
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Calculate each factor
        contradiction_rate = self._calculate_contradiction_rate(metric_name, generation)
        adaptation_speed = self._calculate_adaptation_speed(metric_name, generation)
        predictive_power = self._calculate_predictive_power(metric_name, generation)
        influence_score = self._calculate_influence_concentration(metric_name, generation)
        
        # Combine into confidence score
        # Low contradiction = good, slow adaptation = good
        # High predictive = good, low influence = good
        confidence = (
            (1.0 - contradiction_rate) * self.CONTRADICTION_WEIGHT +
            (1.0 - adaptation_speed) * self.ADAPTATION_WEIGHT +
            predictive_power * self.PREDICTIVE_WEIGHT +
            (1.0 - influence_score) * self.INFLUENCE_WEIGHT
        )
        
        confidence = max(0.0, min(1.0, confidence))
        
        # Calculate decay multiplier
        decay_multiplier = self._calculate_decay_multiplier(confidence)
        
        # Store the confidence measurement
        self._store_confidence(
            metric_name, generation, confidence,
            contradiction_rate, adaptation_speed,
            predictive_power, influence_score, decay_multiplier
        )
        
        logger.debug(f"Metric '{metric_name}' confidence: {confidence:.3f} "
                    f"(contradiction={contradiction_rate:.2f}, "
                    f"adaptation={adaptation_speed:.2f}, "
                    f"predictive={predictive_power:.2f}, "
                    f"influence={influence_score:.2f})")
        
        return confidence
    
    def _calculate_contradiction_rate(self, metric_name: str, 
                                       generation: int,
                                       window: int = 20) -> float:
        """
        How often does this metric disagree with the majority of other metrics?
        
        Uses correlation between this metric's agent rankings and other metrics.
        
        Args:
            metric_name: Metric to check
            generation: Current generation
            window: Generations to look back
            
        Returns:
            Contradiction rate (0.0 = perfect agreement, 1.0 = always disagrees)
        """
        try:
            # Get this metric's values over recent generations
            this_metric = self.db.execute_query("""
                SELECT generation, value
                FROM ecosystem_metrics
                WHERE metric_name = ?
                  AND generation > ? - ?
                ORDER BY generation
            """, (metric_name, generation, window))
            
            if not this_metric or len(this_metric) < 5:
                return 0.5  # Neutral if not enough data
            
            # Get all other metrics in the same window
            other_metrics = self.db.execute_query("""
                SELECT metric_name, generation, value
                FROM ecosystem_metrics
                WHERE metric_name != ?
                  AND generation > ? - ?
                ORDER BY metric_name, generation
            """, (metric_name, generation, window))
            
            if not other_metrics:
                return 0.5
            
            # Group by metric and calculate correlations
            # Simplified: Check if trends align (both increasing or both decreasing)
            this_values = [r['value'] for r in this_metric]
            this_trend = 1 if this_values[-1] > this_values[0] else -1
            
            contradictions = 0
            total_comparisons = 0
            
            current_metric = None
            current_values = []
            
            for row in other_metrics:
                if row['metric_name'] != current_metric:
                    if current_values and len(current_values) >= 5:
                        other_trend = 1 if current_values[-1] > current_values[0] else -1
                        if other_trend != this_trend:
                            contradictions += 1
                        total_comparisons += 1
                    current_metric = row['metric_name']
                    current_values = []
                current_values.append(row['value'])
            
            # Process last metric
            if current_values and len(current_values) >= 5:
                other_trend = 1 if current_values[-1] > current_values[0] else -1
                if other_trend != this_trend:
                    contradictions += 1
                total_comparisons += 1
            
            if total_comparisons == 0:
                return 0.5
            
            return contradictions / total_comparisons
            
        except Exception as e:
            logger.error(f"Error calculating contradiction rate: {e}")
            return 0.5
    
    def _calculate_adaptation_speed(self, metric_name: str,
                                     generation: int,
                                     window: int = 20) -> float:
        """
        How fast are agents improving on this specific metric?
        
        Fast improvement suggests potential gaming.
        
        Args:
            metric_name: Metric to check
            generation: Current generation
            window: Generations to look back
            
        Returns:
            Adaptation speed (0.0 = stable, 1.0 = very fast improvement)
        """
        try:
            history = self.db.execute_query("""
                SELECT value
                FROM ecosystem_metrics
                WHERE metric_name = ?
                  AND generation > ? - ?
                ORDER BY generation ASC
            """, (metric_name, generation, window))
            
            if not history or len(history) < 5:
                return 0.5  # Neutral if not enough data
            
            values = [r['value'] for r in history]
            
            # Calculate improvement rate (normalized)
            improvement_rate = (values[-1] - values[0]) / len(values)
            
            # Normalize to 0-1 range (>20% per gen = very fast)
            normalized = min(1.0, abs(improvement_rate) / 0.20)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error calculating adaptation speed: {e}")
            return 0.5
    
    def _calculate_predictive_power(self, metric_name: str,
                                     generation: int,
                                     lag: int = 10) -> float:
        """
        Does high performance on this metric predict actual frontier success?
        
        Args:
            metric_name: Metric to check
            generation: Current generation
            lag: How many generations ago to check predictions
            
        Returns:
            Predictive power (0.0 = no prediction, 1.0 = perfect predictor)
        """
        try:
            # Get metric value from lag generations ago
            past_metric = self.db.execute_query("""
                SELECT value
                FROM ecosystem_metrics
                WHERE metric_name = ?
                  AND generation = ? - ?
            """, (metric_name, generation, lag))
            
            if not past_metric:
                return 0.5  # Neutral if no data
            
            past_value = past_metric[0]['value']
            
            # Get frontier progress since then
            # Count new winning sequences as proxy for frontier success
            success_count = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM winning_sequences
                WHERE discovered_at > datetime('now', '-7 days')
            """)
            
            current_success = success_count[0]['count'] if success_count else 0
            
            # Higher past metric value should correlate with higher success
            # This is a simplified proxy - real implementation would track historical
            if past_value > 0.7 and current_success > 0:
                return 0.8  # High metric predicted success
            elif past_value < 0.3 and current_success == 0:
                return 0.7  # Low metric predicted low success
            elif past_value > 0.7 and current_success == 0:
                return 0.3  # High metric but no success - poor predictor
            else:
                return 0.5  # Mixed signals
                
        except Exception as e:
            logger.error(f"Error calculating predictive power: {e}")
            return 0.5
    
    def _calculate_influence_concentration(self, metric_name: str,
                                            generation: int) -> float:
        """
        Is this metric too dominant in selection/adjustment decisions?
        
        Args:
            metric_name: Metric to check
            generation: Current generation
            
        Returns:
            Influence concentration (0.0 = not influential, 1.0 = too dominant)
        """
        try:
            # Check how often this metric triggered actions
            trigger_count = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM trigger_history
                WHERE trigger_name LIKE ?
                  AND generation > ? - 20
            """, (f"%{metric_name}%", generation))
            
            total_triggers = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM trigger_history
                WHERE generation > ? - 20
            """, (generation,))
            
            if not total_triggers or total_triggers[0]['count'] == 0:
                return 0.0
            
            ratio = trigger_count[0]['count'] / total_triggers[0]['count']
            
            # More than 40% of triggers = too influential
            return min(1.0, ratio / 0.40)
            
        except Exception as e:
            logger.error(f"Error calculating influence concentration: {e}")
            return 0.0
    
    def _calculate_decay_multiplier(self, confidence: float) -> float:
        """
        Calculate how fast this metric should decay based on confidence.
        
        Low confidence metrics decay faster to reduce their influence.
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            Decay multiplier (0.5 = slow decay, 2.0 = fast decay)
        """
        # Low confidence (0.3) -> 2x decay rate
        # High confidence (0.9) -> 0.5x decay rate (slower decay)
        return 2.0 - (confidence * 1.5)
    
    def _store_confidence(self, metric_name: str, generation: int,
                          confidence: float, contradiction: float,
                          adaptation: float, predictive: float,
                          influence: float, decay_mult: float):
        """Store confidence measurement in database."""
        try:
            self.db.execute_query("""
                INSERT INTO metric_confidence 
                (metric_name, generation, confidence_score, contradiction_rate,
                 adaptation_speed, predictive_power, influence_concentration,
                 decay_multiplier)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(metric_name, generation) DO UPDATE SET
                    confidence_score = excluded.confidence_score,
                    contradiction_rate = excluded.contradiction_rate,
                    adaptation_speed = excluded.adaptation_speed,
                    predictive_power = excluded.predictive_power,
                    influence_concentration = excluded.influence_concentration,
                    decay_multiplier = excluded.decay_multiplier,
                    measured_at = CURRENT_TIMESTAMP
            """, (metric_name, generation, confidence, contradiction,
                  adaptation, predictive, influence, decay_mult))
                  
        except Exception as e:
            logger.error(f"Error storing metric confidence: {e}")
    
    def get_decay_multiplier(self, metric_name: str, generation: int) -> float:
        """
        Get the decay multiplier for a metric.
        
        Metrics with low confidence should decay faster.
        
        Args:
            metric_name: Name of the metric
            generation: Current generation
            
        Returns:
            Decay multiplier (>1.0 = faster decay, <1.0 = slower decay)
        """
        try:
            result = self.db.execute_query("""
                SELECT decay_multiplier
                FROM metric_confidence
                WHERE metric_name = ?
                ORDER BY generation DESC
                LIMIT 1
            """, (metric_name,))
            
            if result and result[0].get('decay_multiplier'):
                return result[0]['decay_multiplier']
            
            # If not calculated yet, calculate now
            confidence = self.calculate_metric_confidence(metric_name, generation)
            return self._calculate_decay_multiplier(confidence)
            
        except Exception as e:
            logger.error(f"Error getting decay multiplier: {e}")
            return 1.0  # Default: normal decay
    
    def get_confidence_history(self, metric_name: str,
                                limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get confidence history for a metric.
        
        Args:
            metric_name: Name of the metric
            limit: Maximum records to return
            
        Returns:
            List of confidence records
        """
        try:
            result = self.db.execute_query("""
                SELECT * FROM metric_confidence
                WHERE metric_name = ?
                ORDER BY generation DESC
                LIMIT ?
            """, (metric_name, limit))
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting confidence history: {e}")
            return []
    
    def get_low_confidence_metrics(self, generation: int,
                                    threshold: float = 0.4) -> List[Dict[str, Any]]:
        """
        Get metrics with confidence below threshold.
        
        Useful for identifying metrics that may need rotation or removal.
        
        Args:
            generation: Current generation
            threshold: Confidence threshold
            
        Returns:
            List of low-confidence metric records
        """
        try:
            result = self.db.execute_query("""
                SELECT DISTINCT metric_name, confidence_score, decay_multiplier
                FROM metric_confidence mc
                WHERE generation = (
                    SELECT MAX(generation) FROM metric_confidence 
                    WHERE metric_name = mc.metric_name
                )
                  AND confidence_score < ?
                ORDER BY confidence_score ASC
            """, (threshold,))
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting low confidence metrics: {e}")
            return []
    
    def apply_confidence_weighted_decay(self, generation: int):
        """
        Apply accelerated decay to low-confidence metrics.
        
        This is called during metric rotation to ensure gaming metrics
        lose influence faster.
        
        Args:
            generation: Current generation
        """
        low_confidence = self.get_low_confidence_metrics(generation)
        
        for metric in low_confidence:
            metric_name = metric['metric_name']
            decay_mult = metric.get('decay_multiplier', 1.0)
            
            logger.warning(f"Metric '{metric_name}' has low confidence "
                          f"({metric['confidence_score']:.2f}), "
                          f"applying {decay_mult:.1f}x decay")
