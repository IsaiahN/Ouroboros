import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
MetricRotator - Anti-Goodhart rotation system for metrics.

Part of the Societal Metrics System.
See DOCS/Societal_Metrics_Implementation_Analysis.md for design rationale.

Implements Constraint 4: Second-Order Goodhart Risk
Even with metric rotation, agents can learn:
- Which *classes* of metrics matter
- When rotations tend to happen
- Which behaviors are always "safe"

Countermeasures:
- Skip rotations randomly (unpredictability)
- One-time metrics (never reused)
- Noise injection (prevent exact gaming)
- Deliberate inconsistency (random evaluation)
"""

import logging
import random
import json
import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricRotator:
    """
    Rotates which metrics are used for selection/rewards.
    
    Autopoiesis Role: Prevents Goodhart's Law - agents optimizing for metrics instead of goals
    Problem Solved: Metric gaming and second-order Goodhart effects
    
    Metrics must be ephemeral, not institutionalized.
    
    Usage:
        rotator = MetricRotator(db)
        active_metrics = rotator.get_active_metrics(generation)
        value = rotator.apply_noise(raw_value)
    """
    
    # Configuration
    DEFAULT_ROTATION_PERIOD = 10      # Rotate every N generations
    SKIP_ROTATION_PROBABILITY = 0.20  # 20% chance to skip rotation
    ONE_TIME_METRIC_PROBABILITY = 0.05  # 5% chance to inject one-time metric
    NOISE_INJECTION_RANGE = 0.1       # +/- 10% noise on metrics
    
    # Metric pools organized by category
    DEFAULT_METRIC_POOLS = {
        'efficiency': [
            'marginal_value_per_action',
            'actions_per_level',
            'completion_time',
            'action_efficiency'
        ],
        'social': [
            'viral_spread',
            'teaching_events',
            'validation_rate',
            'prestige_contribution'
        ],
        'exploration': [
            'novel_solutions',
            'game_diversity',
            'frontier_attempts',
            'strategy_variety'
        ],
        'reliability': [
            'success_rate',
            'consistency_score',
            'recovery_speed',
            'sequence_validity'
        ],
        'emergence': [
            'emergence_gain',
            'information_velocity',
            'hub_fragility',
            'network_resilience'
        ]
    }
    
    def __init__(self, db, rotation_period: Optional[int] = None,
                 metric_pools: Optional[Dict[str, List[str]]] = None):
        """
        Initialize with database interface (dependency injection).
        
        Args:
            db: DatabaseInterface instance for persistence
            rotation_period: Generations between rotations (default: 10)
            metric_pools: Custom metric pools (default: DEFAULT_METRIC_POOLS)
        """
        self.db = db
        self.rotation_period = rotation_period or self.DEFAULT_ROTATION_PERIOD
        self.metric_pools = metric_pools or self.DEFAULT_METRIC_POOLS
        self.one_time_metrics_used: Set[str] = set()
        self._ensure_schema()
        self._load_one_time_history()
    
    def _ensure_schema(self):
        """Create metric_rotation_history table if not exists (idempotent)."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS metric_rotation_history (
                    rotation_id TEXT PRIMARY KEY,
                    generation INTEGER NOT NULL,
                    active_metrics TEXT NOT NULL,
                    was_skipped INTEGER DEFAULT 0,
                    one_time_metrics_added TEXT,
                    rotation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    noise_seed INTEGER
                )
            """)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_rotation_gen 
                ON metric_rotation_history(generation)
            """)
        except Exception as e:
            logger.warning(f"Schema creation warning (may already exist): {e}")
    
    def _load_one_time_history(self):
        """Load previously used one-time metrics from database."""
        try:
            result = self.db.execute_query("""
                SELECT one_time_metrics_added
                FROM metric_rotation_history
                WHERE one_time_metrics_added IS NOT NULL
            """)
            
            for row in (result or []):
                if row.get('one_time_metrics_added'):
                    try:
                        metrics = json.loads(row['one_time_metrics_added'])
                        self.one_time_metrics_used.update(metrics)
                    except json.JSONDecodeError:
                        pass
                        
        except Exception as e:
            logger.warning(f"Error loading one-time history: {e}")
    
    def get_rotation_phase(self, generation: int) -> int:
        """
        Get the current rotation phase number.
        
        Args:
            generation: Current generation
            
        Returns:
            Phase number (increments every rotation_period generations)
        """
        return generation // self.rotation_period
    
    def should_skip_rotation(self, generation: int) -> bool:
        """
        Determine if rotation should be skipped this cycle.
        
        20% chance to maintain previous metrics for unpredictability.
        
        Args:
            generation: Current generation
            
        Returns:
            True if rotation should be skipped
        """
        # Use generation as seed for reproducibility within same generation
        random.seed(generation * 7919)  # Prime number for better distribution
        should_skip = random.random() < self.SKIP_ROTATION_PROBABILITY
        random.seed()  # Reset to random state
        
        if should_skip:
            logger.info(f"[ROTATION] Skipping rotation at generation {generation} "
                       f"(unpredictability mechanism)")
        
        return should_skip
    
    def _get_previous_metrics(self, generation: int) -> List[str]:
        """
        Get the active metrics from the previous rotation.
        
        Args:
            generation: Current generation
            
        Returns:
            List of previously active metric names
        """
        try:
            result = self.db.execute_query("""
                SELECT active_metrics
                FROM metric_rotation_history
                WHERE generation < ?
                ORDER BY generation DESC
                LIMIT 1
            """, (generation,))
            
            if result and result[0].get('active_metrics'):
                return json.loads(result[0]['active_metrics'])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting previous metrics: {e}")
            return []
    
    def _generate_one_time_metric(self, generation: int) -> Optional[str]:
        """
        Generate a novel metric that will only be used once.
        
        These metrics create unpredictable selection pressure.
        
        Args:
            generation: Current generation
            
        Returns:
            One-time metric name, or None if already used
        """
        # Templates for one-time metrics
        templates = [
            f"action_diversity_level_{random.randint(1, 20)}",
            f"score_at_action_{random.randint(50, 200)}",
            f"recovery_from_score_{random.randint(1, 5)}",
            f"exploration_after_gen_{generation - random.randint(5, 20)}",
            f"consistency_window_{random.randint(3, 15)}",
            f"novelty_in_game_type_{random.randint(1, 10)}",
        ]
        
        # Try to find an unused one
        random.shuffle(templates)
        for metric in templates:
            if metric not in self.one_time_metrics_used:
                return metric
        
        # All templates used, generate truly unique one
        unique = f"unique_metric_{uuid.uuid4().hex[:8]}"
        return unique
    
    def get_active_metrics(self, generation: int) -> List[str]:
        """
        Get the currently active metrics for this generation.
        
        Applies all anti-Goodhart protections:
        - Rotation based on phase
        - Skip rotation randomly
        - Inject one-time metrics
        
        Args:
            generation: Current generation
            
        Returns:
            List of active metric names
        """
        # Check if this generation already has a recorded rotation
        existing = self._get_existing_rotation(generation)
        if existing:
            return existing
        
        # Check for skip rotation
        if self.should_skip_rotation(generation):
            previous = self._get_previous_metrics(generation)
            if previous:
                self._record_rotation(generation, previous, was_skipped=True)
                return previous
        
        # Perform regular rotation
        phase = self.get_rotation_phase(generation)
        metrics = self._select_metrics_for_phase(phase)
        
        # Possibly inject one-time metric
        one_time_added = []
        if random.random() < self.ONE_TIME_METRIC_PROBABILITY:
            one_time = self._generate_one_time_metric(generation)
            if one_time and one_time not in self.one_time_metrics_used:
                metrics.append(one_time)
                one_time_added.append(one_time)
                self.one_time_metrics_used.add(one_time)
                logger.info(f"[ROTATION] Injected one-time metric: {one_time}")
        
        # Record the rotation
        self._record_rotation(generation, metrics, one_time_metrics=one_time_added)
        
        return metrics
    
    def _get_existing_rotation(self, generation: int) -> Optional[List[str]]:
        """Check if rotation already recorded for this generation."""
        try:
            result = self.db.execute_query("""
                SELECT active_metrics
                FROM metric_rotation_history
                WHERE generation = ?
            """, (generation,))
            
            if result and result[0].get('active_metrics'):
                return json.loads(result[0]['active_metrics'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing rotation: {e}")
            return None
    
    def _select_metrics_for_phase(self, phase: int) -> List[str]:
        """
        Select metrics for a given rotation phase.
        
        Each phase uses a deterministic but varied selection from each pool.
        
        Args:
            phase: Rotation phase number
            
        Returns:
            List of selected metric names
        """
        selected = []
        
        for pool_name, pool_metrics in self.metric_pools.items():
            if not pool_metrics:
                continue
            
            # Use phase + pool_name hash as seed for reproducibility
            seed = phase + hash(pool_name) % 10000
            random.seed(seed)
            
            # Select 2 metrics from each pool (or all if fewer than 2)
            count = min(2, len(pool_metrics))
            selected.extend(random.sample(pool_metrics, count))
            
            random.seed()  # Reset
        
        return selected
    
    def _record_rotation(self, generation: int, metrics: List[str],
                         was_skipped: bool = False,
                         one_time_metrics: Optional[List[str]] = None):
        """Record a rotation event in database."""
        try:
            rotation_id = f"rot_{uuid.uuid4().hex[:12]}"
            
            self.db.execute_query("""
                INSERT INTO metric_rotation_history
                (rotation_id, generation, active_metrics, was_skipped, 
                 one_time_metrics_added, noise_seed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rotation_id, generation, json.dumps(metrics),
                1 if was_skipped else 0,
                json.dumps(one_time_metrics) if one_time_metrics else None,
                random.randint(0, 1000000)
            ))
            
            logger.info(f"[ROTATION] Generation {generation}: "
                       f"active={len(metrics)} metrics, "
                       f"skipped={was_skipped}")
            
        except Exception as e:
            logger.error(f"Error recording rotation: {e}")
    
    def apply_noise(self, value: float, metric_name: Optional[str] = None) -> float:
        """
        Apply noise to a metric value to prevent exact gaming.
        
        Args:
            value: Raw metric value
            metric_name: Optional metric name for logging
            
        Returns:
            Noisy metric value
        """
        noise = random.uniform(-self.NOISE_INJECTION_RANGE, 
                               self.NOISE_INJECTION_RANGE)
        noisy_value = value * (1 + noise)
        
        return noisy_value
    
    def get_metric_weight(self, metric_name: str, generation: int) -> float:
        """
        Get the current weight for a metric.
        
        Active metrics have weight 1.0, inactive have 0.0.
        Could be extended for graduated weights.
        
        Args:
            metric_name: Name of the metric
            generation: Current generation
            
        Returns:
            Weight (0.0 to 1.0)
        """
        active = self.get_active_metrics(generation)
        return 1.0 if metric_name in active else 0.0
    
    def is_metric_active(self, metric_name: str, generation: int) -> bool:
        """
        Check if a metric is currently active.
        
        Args:
            metric_name: Name of the metric
            generation: Current generation
            
        Returns:
            True if metric is active
        """
        return metric_name in self.get_active_metrics(generation)
    
    def get_rotation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent rotation history.
        
        Args:
            limit: Maximum records to return
            
        Returns:
            List of rotation records
        """
        try:
            result = self.db.execute_query("""
                SELECT generation, active_metrics, was_skipped, 
                       one_time_metrics_added, rotation_timestamp
                FROM metric_rotation_history
                ORDER BY generation DESC
                LIMIT ?
            """, (limit,))
            
            # Parse JSON fields
            for row in (result or []):
                if row.get('active_metrics'):
                    row['active_metrics'] = json.loads(row['active_metrics'])
                if row.get('one_time_metrics_added'):
                    row['one_time_metrics_added'] = json.loads(row['one_time_metrics_added'])
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error getting rotation history: {e}")
            return []
    
    def get_metric_usage_stats(self, metric_name: str,
                                window: int = 100) -> Dict[str, Any]:
        """
        Get usage statistics for a metric.
        
        Args:
            metric_name: Name of the metric
            window: Generations to look back
            
        Returns:
            Dict with usage statistics
        """
        try:
            result = self.db.execute_query("""
                SELECT COUNT(*) as times_active,
                       SUM(was_skipped) as times_in_skipped
                FROM metric_rotation_history
                WHERE active_metrics LIKE ?
                  AND generation > (SELECT MAX(generation) FROM metric_rotation_history) - ?
            """, (f'%"{metric_name}"%', window))
            
            total_rotations = self.db.execute_query("""
                SELECT COUNT(*) as total
                FROM metric_rotation_history
                WHERE generation > (SELECT MAX(generation) FROM metric_rotation_history) - ?
            """, (window,))
            
            times_active = result[0]['times_active'] if result else 0
            total = total_rotations[0]['total'] if total_rotations else 0
            
            return {
                'metric_name': metric_name,
                'times_active': times_active,
                'total_rotations': total,
                'activity_rate': times_active / max(total, 1),
                'window_generations': window
            }
            
        except Exception as e:
            logger.error(f"Error getting metric usage stats: {e}")
            return {'metric_name': metric_name, 'error': str(e)}


class AntiGoodhartRotator(MetricRotator):
    """
    Extended rotator with additional second-order Goodhart protections.
    
    Inherits from MetricRotator and adds:
    - Deliberate inconsistency
    - Pattern breaking
    - Correlation disruption
    
    Usage:
        rotator = AntiGoodhartRotator(db)
        metrics = rotator.get_active_metrics(generation)
    """
    
    def __init__(self, db, **kwargs):
        super().__init__(db, **kwargs)
        self.DELIBERATE_INCONSISTENCY_RATE = 0.10  # 10% chance to break patterns
    
    def get_active_metrics(self, generation: int) -> List[str]:
        """
        Get active metrics with additional anti-Goodhart protections.
        
        Adds deliberate inconsistency to break predictable patterns.
        """
        metrics = super().get_active_metrics(generation)
        
        # Deliberate inconsistency: randomly swap one metric
        if random.random() < self.DELIBERATE_INCONSISTENCY_RATE:
            metrics = self._apply_inconsistency(metrics, generation)
        
        return metrics
    
    def _apply_inconsistency(self, metrics: List[str], 
                             generation: int) -> List[str]:
        """
        Apply deliberate inconsistency to metric selection.
        
        Swaps one metric for a random one from any pool.
        """
        if not metrics:
            return metrics
        
        all_metrics = []
        for pool in self.metric_pools.values():
            all_metrics.extend(pool)
        
        # Remove one random metric and add a different random one
        metrics = list(metrics)
        to_remove = random.choice(metrics)
        candidates = [m for m in all_metrics if m not in metrics]
        
        if candidates:
            to_add = random.choice(candidates)
            metrics.remove(to_remove)
            metrics.append(to_add)
            
            logger.debug(f"[INCONSISTENCY] Swapped {to_remove} for {to_add} "
                        f"at generation {generation}")
        
        return metrics
