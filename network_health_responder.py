import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Network Health Responder
========================

Reads ecosystem health snapshots and returns corrective parameter adjustments.
This closes the feedback loop: snapshot -> diagnosis -> parameter change.

The network_intelligence_engine captures health metrics every 5 generations.
This module translates those metrics into concrete parameter adjustments
that evolution_runner applies to the next generation.

Following Rule 2: All adjustments logged to network_regulation_history table.
Following Rule 3: Enhances existing NIE, doesn't replace it.
Following Rule 10: No duplicate functionality.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from database_interface import DatabaseInterface

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Threshold constants -- each maps a health metric to a corrective action.
# Derived from the Master Ruleset and implementation plan Phase 1.3.
# ---------------------------------------------------------------------------

HEALTH_RULES: List[Dict[str, Any]] = [
    {
        'metric': 'knowledge_diversity_index',
        'condition': 'lt',
        'threshold': 0.3,
        'adjustments': {
            'mutation_rate': 0.10,         # +10% absolute
            'pioneer_allocation': 0.05,    # +5% share
        },
        'description': 'Low diversity -- increase mutation and pioneer allocation',
    },
    {
        'metric': 'knowledge_creation_rate',
        'condition': 'lt',
        'threshold': 0.01,
        'adjustments': {
            'exploration_budget_mult': 0.15,  # +15%
            'optimizer_allocation': -0.05,    # -5% share
        },
        'description': 'Stagnant knowledge -- boost exploration, reduce optimizers',
    },
    {
        'metric': 'validation_rate',
        'condition': 'lt',
        'threshold': 0.1,
        'adjustments': {
            'generalist_allocation': 0.05,        # +5% share
            'collective_reasoning_frequency': 1,   # additional collective sessions
        },
        'description': 'Low validation -- increase generalists, trigger collective reasoning',
    },
    {
        'metric': 'orphan_ratio',  # Computed: orphan_sequences / total_sequences
        'condition': 'gt',
        'threshold': 0.5,
        'adjustments': {
            'generalist_allocation': 0.05,
            'validation_campaign': True,
        },
        'description': 'Too many orphan sequences -- trigger validation campaign',
    },
    {
        'metric': 'transfer_learning_rate',
        'condition': 'lt',
        'threshold': 0.01,
        'adjustments': {
            'horizontal_transfer_frequency': 1,   # extra transfer rounds
        },
        'description': 'Low transfer rate -- boost horizontal transfer',
    },
    {
        'metric': 'system_entropy',
        'condition': 'gt',
        'threshold': 0.9,
        'adjustments': {
            'cleanup_frequency_mult': 0.5,         # run cleanup sooner
            'forgetting_decay_rate': 0.05,         # tighten forgetting
        },
        'description': 'High entropy -- increase cleanup, tighten forgetting',
    },
    {
        'metric': 'emergence_gain',
        'condition': 'lt',
        'threshold': 1.0,
        'adjustments': {
            'mutation_rate': 0.05,
            'pioneer_allocation': 0.03,
            'exploration_budget_mult': 0.10,
        },
        'description': 'Network worse than sum of parts -- increase agent diversity',
    },
]


class NetworkHealthResponder:
    """Translates ecosystem health snapshots into parameter adjustments.

    Usage (inside evolution_runner):
        snapshot = nie.capture_ecosystem_snapshot(gen)
        adjustments = responder.get_adjustments(snapshot, gen)
        # apply adjustments to next-gen parameters
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_adjustments(
        self, snapshot: Dict[str, Any], generation: int
    ) -> Dict[str, Any]:
        """Evaluate snapshot against health rules, return parameter deltas.

        Returns a dict like:
            {
                'mutation_rate': +0.10,
                'pioneer_allocation': +0.05,
                'triggered_rules': ['Low diversity -- ...'],
                'health_score': 0.35,
            }
        """
        adjustments: Dict[str, Any] = {}
        triggered: List[str] = []

        # Derive orphan_ratio (not stored directly in snapshot)
        total_seq = snapshot.get('total_sequences', 0)
        orphan_seq = snapshot.get('orphan_sequences_count', 0)
        orphan_ratio = orphan_seq / max(1, total_seq)
        snapshot_ext = {**snapshot, 'orphan_ratio': orphan_ratio}

        # Also pull emergence_gain if available (may not be in snapshot)
        if 'emergence_gain' not in snapshot_ext:
            snapshot_ext['emergence_gain'] = self._query_emergence_gain(generation)

        for rule in HEALTH_RULES:
            metric_val = snapshot_ext.get(rule['metric'])
            if metric_val is None:
                continue

            fired = False
            if rule['condition'] == 'lt' and metric_val < rule['threshold']:
                fired = True
            elif rule['condition'] == 'gt' and metric_val > rule['threshold']:
                fired = True

            if fired:
                triggered.append(rule['description'])
                for param, delta in rule['adjustments'].items():
                    if isinstance(delta, bool):
                        adjustments[param] = delta
                    elif isinstance(delta, (int, float)):
                        adjustments[param] = adjustments.get(param, 0) + delta

        adjustments['triggered_rules'] = triggered
        adjustments['health_score'] = snapshot.get('health_score', 0.0)

        # Log every adjustment to network_regulation_history
        if triggered:
            self._log_adjustments(
                generation=generation,
                adjustments=adjustments,
                snapshot=snapshot,
            )

        return adjustments

    def apply_adjustments(
        self,
        adjustments: Dict[str, Any],
        evolution_strategy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply adjustment deltas to an evolution_strategy dict (in-place safe).

        Returns the modified strategy dict (also mutates it).
        """
        for key in ('mutation_rate', 'exploration_budget_mult',
                     'forgetting_decay_rate', 'cleanup_frequency_mult'):
            delta = adjustments.get(key, 0)
            if delta:
                old = evolution_strategy.get(key, 0.2 if key == 'mutation_rate' else 0.0)
                new_val = max(0.01, min(0.99, old + delta))
                evolution_strategy[key] = new_val

        # Role allocation adjustments (stored separately, read by op mode system)
        for key in ('pioneer_allocation', 'optimizer_allocation',
                     'generalist_allocation'):
            delta = adjustments.get(key, 0)
            if delta:
                old = evolution_strategy.get(key, 0.0)
                evolution_strategy[key] = max(0.0, min(1.0, old + delta))

        return evolution_strategy

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _query_emergence_gain(self, generation: int) -> float:
        """Query latest emergence gain from database."""
        try:
            rows = self.db.execute_query("""
                SELECT metric_value FROM emergence_metrics
                WHERE metric_name = 'emergence_gain'
                  AND generation <= ?
                ORDER BY generation DESC LIMIT 1
            """, (generation,))
            if rows:
                return rows[0].get('metric_value', 1.0)
        except Exception:
            pass
        return 1.0  # Default: no signal

    def _log_adjustments(
        self,
        generation: int,
        adjustments: Dict[str, Any],
        snapshot: Dict[str, Any],
    ) -> None:
        """Write each parameter adjustment to network_regulation_history."""
        health_score = snapshot.get('health_score', 0.0)
        rules_desc = ', '.join(adjustments.get('triggered_rules', []))

        for param, delta in adjustments.items():
            if param in ('triggered_rules', 'health_score'):
                continue
            if isinstance(delta, bool):
                delta_num = 1.0 if delta else 0.0
            else:
                delta_num = float(delta)

            try:
                reg_id = f"reg_{uuid.uuid4().hex[:12]}"
                self.db.execute_query("""
                    INSERT INTO network_regulation_history (
                        regulation_id, generation, parameter_name,
                        old_value, new_value, adjustment_magnitude,
                        net_signal_strength, network_health_before,
                        failing_metrics_addressed
                    ) VALUES (?, ?, ?, 0.0, ?, ?, ?, ?, ?)
                """, (
                    reg_id,
                    generation,
                    param,
                    delta_num,
                    abs(delta_num),
                    abs(delta_num),
                    health_score,
                    rules_desc,
                ))
            except Exception as e:
                self.logger.warning(f"Failed to log regulation: {e}")

    # ------------------------------------------------------------------
    # Phase 5.3: Dedicated parameter-adaptation helpers
    # ------------------------------------------------------------------
    # These three methods provide fine-grained adjustments with a hard
    # cap of 20% change per generation to prevent oscillation.
    # ------------------------------------------------------------------

    _MAX_DELTA_PCT = 0.20  # Self-regulation bound (Rule from impl plan)

    def get_mutation_adjustment(
        self, snapshot: Dict[str, Any], generation: int
    ) -> float:
        """Return a +-delta for the base mutation rate.

        * Low diversity  -> increase mutation (explore more)
        * Low emergence   -> increase mutation (break out of local optima)
        * High diversity + high emergence -> decrease (let solutions stabilise)

        Clamped to ``[-MAX_DELTA, +MAX_DELTA]``.
        """
        diversity = snapshot.get('knowledge_diversity_index', 0.5)
        emergence = snapshot.get('emergence_gain', 1.0)

        delta = 0.0
        if diversity < 0.3:
            delta += 0.10
        elif diversity > 0.7:
            delta -= 0.05

        if emergence < 1.0:
            delta += 0.05
        elif emergence > 2.0:
            delta -= 0.05

        delta = max(-self._MAX_DELTA_PCT, min(delta, self._MAX_DELTA_PCT))
        self._log_param_adjustment(generation, 'mutation_rate', delta, snapshot)
        return delta

    def get_role_allocation(
        self, snapshot: Dict[str, Any], generation: int
    ) -> Dict[str, float]:
        """Return adjusted Pioneer/Optimizer/Generalist/Exploiter percentages.

        Rules:
        * Low diversity           -> +pioneer, -optimizer
        * Low validation rate     -> +generalist
        * High knowledge creation -> +optimizer (harvest solutions)
        * Percentages always sum to 1.0
        * No individual shift > ``_MAX_DELTA_PCT`` from the incoming values
        """
        diversity = snapshot.get('knowledge_diversity_index', 0.5)
        validation = snapshot.get('validation_rate', 0.5)
        creation = snapshot.get('knowledge_creation_rate', 0.05)

        # Start from neutral deltas
        d_pioneer = 0.0
        d_optimizer = 0.0
        d_generalist = 0.0
        d_exploiter = 0.0

        if diversity < 0.3:
            d_pioneer += 0.05
            d_optimizer -= 0.05
        elif diversity > 0.7 and creation > 0.05:
            d_pioneer -= 0.05
            d_optimizer += 0.05

        if validation < 0.1:
            d_generalist += 0.05
            d_exploiter -= 0.03
            d_pioneer -= 0.02

        # Clamp each delta
        cap = self._MAX_DELTA_PCT
        d_pioneer = max(-cap, min(d_pioneer, cap))
        d_optimizer = max(-cap, min(d_optimizer, cap))
        d_generalist = max(-cap, min(d_generalist, cap))
        d_exploiter = max(-cap, min(d_exploiter, cap))

        result = {
            'pioneer_delta': d_pioneer,
            'optimizer_delta': d_optimizer,
            'generalist_delta': d_generalist,
            'exploiter_delta': d_exploiter,
        }
        self._log_param_adjustment(generation, 'role_allocation', sum(abs(v) for v in result.values()), snapshot)
        return result

    def get_exploration_budget_multiplier(
        self, snapshot: Dict[str, Any], generation: int
    ) -> float:
        """Return a multiplier (0.5 – 2.0) for exploration action budgets.

        * Stagnant knowledge creation -> higher budget (more actions)
        * High entropy               -> lower budget  (act more conservatively)
        * Normal                      -> 1.0 (unchanged)
        """
        creation = snapshot.get('knowledge_creation_rate', 0.05)
        entropy = snapshot.get('system_entropy', 0.5)

        multiplier = 1.0
        if creation < 0.01:
            multiplier += 0.15
        elif creation > 0.1:
            multiplier -= 0.10

        if entropy > 0.9:
            multiplier -= 0.15
        elif entropy < 0.3:
            multiplier += 0.10

        multiplier = max(0.5, min(multiplier, 2.0))
        self._log_param_adjustment(generation, 'exploration_budget_mult', multiplier - 1.0, snapshot)
        return multiplier

    def _log_param_adjustment(
        self, generation: int, param: str, delta: float, snapshot: Dict[str, Any]
    ) -> None:
        """Compact helper to record an auto-adaptation in regulation history."""
        if abs(delta) < 0.001:
            return  # Insignificant -- skip
        try:
            reg_id = f"reg_auto_{uuid.uuid4().hex[:12]}"
            self.db.execute_query("""
                INSERT INTO network_regulation_history (
                    regulation_id, generation, parameter_name,
                    old_value, new_value, adjustment_magnitude,
                    net_signal_strength, network_health_before,
                    failing_metrics_addressed
                ) VALUES (?, ?, ?, 0.0, ?, ?, ?, ?, ?)
            """, (
                reg_id,
                generation,
                f"auto_{param}",
                delta,
                abs(delta),
                abs(delta),
                snapshot.get('health_score', 0.0),
                'auto_adaptation',
            ))
        except Exception:
            pass  # Best-effort logging
