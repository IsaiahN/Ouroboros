import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
TriggerController - Prevents feedback resonance in metric-driven adjustments.

Part of the Societal Metrics System.
See DOCS/Societal_Metrics_Implementation_Analysis.md for design rationale.

Implements Constraint 1 from the analysis:
- Cooldowns between trigger fires
- Multi-metric corroboration
- Small nudges, not emergency brakes
- Damping for consecutive fires
"""

import logging
import uuid
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class TriggerController:
    """
    Manages metric triggers with anti-resonance protections.
    
    Autopoiesis Role: Prevents feedback loops and cascade oscillations
    Problem Solved: Trigger coupling risk - single-metric triggers causing runaway adjustments
    
    All parameter adjustments MUST go through this controller to ensure:
    1. Cooldown periods between same trigger firing
    2. Multi-metric corroboration before action
    3. Damping for consecutive fires
    4. Maximum adjustment caps
    
    Usage:
        controller = TriggerController(db)
        result = controller.fire_with_safeguards(
            trigger_name="emergence_low",
            generation=100,
            primary_metric_value=0.3,
            secondary_metric_values={"velocity": 0.6, "diversity": 0.7},
            base_adjustment=0.15,
            apply_func=lambda adj: increase_transmission(adj)
        )
    """
    
    # Configuration constants
    COOLDOWN_GENERATIONS = 3       # Minimum generations between same trigger
    DAMPING_FACTOR = 0.5           # Each consecutive fire reduces magnitude by this factor
    MAX_ADJUSTMENT = 0.10          # 10% max change per generation
    CORROBORATION_THRESHOLD = 2    # Minimum metrics that must agree
    LOOKBACK_WINDOW = 10           # Generations to look back for consecutive fires
    
    def __init__(self, db):
        """
        Initialize with database interface (dependency injection).
        
        Args:
            db: DatabaseInterface instance for persistence
        """
        self.db = db
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create trigger_history table if not exists (idempotent)."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS trigger_history (
                    trigger_id TEXT PRIMARY KEY,
                    trigger_name TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    fired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metric_value REAL,
                    adjustment_magnitude REAL,
                    corroborating_metrics TEXT,
                    was_damped INTEGER DEFAULT 0,
                    consecutive_fire_count INTEGER DEFAULT 1
                )
            """)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_trigger_name_gen 
                ON trigger_history(trigger_name, generation)
            """)
        except Exception as e:
            logger.warning(f"Schema creation warning (may already exist): {e}")
    
    def can_fire(self, trigger_name: str, generation: int) -> bool:
        """
        Check if trigger is allowed to fire (cooldown respected).
        
        Args:
            trigger_name: Name of the trigger to check
            generation: Current evolution generation
            
        Returns:
            True if trigger can fire, False if in cooldown period
        """
        try:
            result = self.db.execute_query("""
                SELECT MAX(generation) as last_gen
                FROM trigger_history
                WHERE trigger_name = ?
            """, (trigger_name,))
            
            if not result or result[0].get('last_gen') is None:
                return True
            
            last_gen = result[0]['last_gen']
            can_fire = (generation - last_gen) >= self.COOLDOWN_GENERATIONS
            
            if not can_fire:
                logger.debug(f"Trigger '{trigger_name}' blocked by cooldown "
                           f"(last fired gen {last_gen}, current {generation})")
            
            return can_fire
            
        except Exception as e:
            logger.error(f"Error checking trigger cooldown: {e}")
            return True  # Allow on error to prevent deadlock
    
    def get_consecutive_fires(self, trigger_name: str, generation: int) -> int:
        """
        Count how many times this trigger has fired in recent generations.
        
        Args:
            trigger_name: Name of the trigger
            generation: Current generation
            
        Returns:
            Number of times trigger fired in lookback window
        """
        try:
            result = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM trigger_history
                WHERE trigger_name = ?
                  AND generation > ?
            """, (trigger_name, generation - self.LOOKBACK_WINDOW))
            
            return result[0]['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Error counting consecutive fires: {e}")
            return 0
    
    def calculate_damped_magnitude(self, trigger_name: str, 
                                    base_magnitude: float,
                                    generation: int) -> float:
        """
        Apply damping for consecutive fires.
        
        Each consecutive fire reduces the adjustment magnitude by DAMPING_FACTOR.
        Result is always capped at MAX_ADJUSTMENT.
        
        Args:
            trigger_name: Name of the trigger
            base_magnitude: Requested adjustment magnitude
            generation: Current generation
            
        Returns:
            Damped adjustment magnitude (0.0 to MAX_ADJUSTMENT)
        """
        consecutive = self.get_consecutive_fires(trigger_name, generation)
        damped = base_magnitude * (self.DAMPING_FACTOR ** consecutive)
        final = min(damped, self.MAX_ADJUSTMENT)
        
        if final < base_magnitude:
            logger.debug(f"Trigger '{trigger_name}' damped from {base_magnitude:.3f} "
                        f"to {final:.3f} (consecutive fires: {consecutive})")
        
        return final
    
    def require_corroboration(self, primary_value: float,
                               secondary_values: List[float],
                               threshold: float = 0.5) -> bool:
        """
        Check if multiple metrics agree before allowing adjustment.
        
        Args:
            primary_value: Main metric value that triggered this
            secondary_values: List of secondary metric values
            threshold: Minimum value for a metric to count as "agreeing"
            
        Returns:
            True if enough metrics exceed threshold
        """
        if not secondary_values:
            # No secondary metrics provided - allow single-metric triggers
            # but log warning for monitoring
            logger.warning("Trigger fired without corroborating metrics")
            return True
        
        agreeing = sum(1 for v in secondary_values if v > threshold)
        meets_threshold = agreeing >= self.CORROBORATION_THRESHOLD
        
        if not meets_threshold:
            logger.debug(f"Corroboration failed: only {agreeing}/{len(secondary_values)} "
                        f"metrics above {threshold} (need {self.CORROBORATION_THRESHOLD})")
        
        return meets_threshold
    
    def record_fire(self, trigger_name: str, generation: int,
                    metric_value: float, adjustment: float,
                    corroborating_metrics: List[str]) -> str:
        """
        Record that a trigger fired.
        
        Args:
            trigger_name: Name of the trigger
            generation: Current generation
            metric_value: Primary metric value
            adjustment: Actual adjustment applied
            corroborating_metrics: List of metric names that corroborated
            
        Returns:
            Unique trigger_id for this fire event
        """
        trigger_id = f"trig_{uuid.uuid4().hex[:12]}"
        consecutive = self.get_consecutive_fires(trigger_name, generation) + 1
        was_damped = 1 if consecutive > 1 else 0
        
        try:
            self.db.execute_query("""
                INSERT INTO trigger_history 
                (trigger_id, trigger_name, generation, metric_value, 
                 adjustment_magnitude, corroborating_metrics, 
                 was_damped, consecutive_fire_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trigger_id, trigger_name, generation, metric_value,
                adjustment, json.dumps(corroborating_metrics),
                was_damped, consecutive
            ))
            
            logger.info(f"[TRIGGER] {trigger_name} fired at gen {generation}: "
                       f"value={metric_value:.3f}, adjustment={adjustment:.3f}, "
                       f"damped={bool(was_damped)}, consecutive={consecutive}")
            
        except Exception as e:
            logger.error(f"Error recording trigger fire: {e}")
        
        return trigger_id
    
    def fire_with_safeguards(self, trigger_name: str,
                              generation: int,
                              primary_metric_value: float,
                              secondary_metric_values: Dict[str, float],
                              base_adjustment: float,
                              apply_func: Callable[[float], Any]) -> Optional[Dict[str, Any]]:
        """
        Attempt to fire a trigger with all safeguards applied.
        
        This is the main entry point for all metric-driven adjustments.
        It applies: cooldown check, corroboration check, damping, and max cap.
        
        Args:
            trigger_name: Name of the trigger (e.g., "emergence_low")
            generation: Current evolution generation
            primary_metric_value: Main metric that triggered this
            secondary_metric_values: Dict of {metric_name: value} for corroboration
            base_adjustment: Desired adjustment magnitude (before damping/caps)
            apply_func: Function to call if trigger fires (receives adjusted magnitude)
            
        Returns:
            Dict with trigger details if fired, None if blocked by safeguards
            
        Example:
            result = controller.fire_with_safeguards(
                trigger_name="emergence_low",
                generation=100,
                primary_metric_value=0.3,
                secondary_metric_values={"velocity": 0.6, "diversity": 0.7},
                base_adjustment=0.15,
                apply_func=lambda adj: set_transmission_rate(current_rate + adj)
            )
        """
        # Check cooldown
        if not self.can_fire(trigger_name, generation):
            logger.debug(f"Trigger '{trigger_name}' blocked by cooldown")
            return None
        
        # Check corroboration
        # Accept dict or list/tuple for corroboration metrics
        try:
            corroboration_values = list(secondary_metric_values.values())
        except AttributeError:
            corroboration_values = list(secondary_metric_values or [])

        if not self.require_corroboration(
            primary_metric_value,
            corroboration_values
        ):
            logger.debug(f"Trigger '{trigger_name}' blocked by corroboration requirement")
            return None
        
        # Calculate damped adjustment
        actual_adjustment = self.calculate_damped_magnitude(
            trigger_name, base_adjustment, generation
        )
        
        # Apply the adjustment
        try:
            result = apply_func(actual_adjustment)
        except Exception as e:
            logger.error(f"Error applying trigger '{trigger_name}': {e}")
            return None
        
        # Record the fire
        trigger_id = self.record_fire(
            trigger_name, generation, primary_metric_value,
            actual_adjustment,
            list(secondary_metric_values.keys()) if hasattr(secondary_metric_values, 'keys') else []
        )
        
        return {
            'trigger_id': trigger_id,
            'trigger_name': trigger_name,
            'generation': generation,
            'primary_value': primary_metric_value,
            'adjustment_applied': actual_adjustment,
            'was_damped': actual_adjustment < base_adjustment,
            'corroborating_metrics': list(secondary_metric_values.keys()) if hasattr(secondary_metric_values, 'keys') else [],
            'result': result
        }
    
    def get_trigger_history(self, trigger_name: Optional[str] = None, 
                            limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent trigger history for analysis.
        
        Args:
            trigger_name: Filter by trigger name (None for all)
            limit: Maximum records to return
            
        Returns:
            List of trigger history records
        """
        try:
            if trigger_name:
                result = self.db.execute_query("""
                    SELECT * FROM trigger_history
                    WHERE trigger_name = ?
                    ORDER BY generation DESC
                    LIMIT ?
                """, (trigger_name, limit))
            else:
                result = self.db.execute_query("""
                    SELECT * FROM trigger_history
                    ORDER BY generation DESC
                    LIMIT ?
                """, (limit,))
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting trigger history: {e}")
            return []
    
    def get_fire_rate(self, trigger_name: str, window: int = 50) -> float:
        """
        Calculate how often a trigger fires per generation.
        
        Args:
            trigger_name: Name of the trigger
            window: Number of generations to look back
            
        Returns:
            Fire rate (fires per generation)
        """
        try:
            result = self.db.execute_query("""
                SELECT 
                    COUNT(*) as fires,
                    MAX(generation) - MIN(generation) + 1 as span
                FROM trigger_history
                WHERE trigger_name = ?
                  AND generation >= (SELECT MAX(generation) FROM trigger_history) - ?
            """, (trigger_name, window))
            
            if result and result[0]['span'] and result[0]['span'] > 0:
                return result[0]['fires'] / result[0]['span']
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating fire rate: {e}")
            return 0.0
