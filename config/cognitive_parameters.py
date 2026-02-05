"""
Cognitive Parameters - Centralized Configuration for Cognitive Routing.

Phase 8 Implementation - Appendix C (Production Concerns)

This module centralizes all tunable parameters for the cognitive routing system,
classified by sensitivity tier:

- TIER 1 (CRITICAL): Wrong values break the system. Strong theoretical priors.
- TIER 2 (PERFORMANCE): Affects quality but won't break system. Benefits from tuning.
- TIER 3 (FINE-TUNING): Minor impact. Safe for online adaptation.

Never auto-tune TIER 1 parameters without human review.
TIER 3 parameters are candidates for sensitivity analysis and online adaptation.
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Tuple


@dataclass
class CognitiveParameters:
    """
    All tunable parameters for cognitive routing in one place.

    Parameters are classified by sensitivity tier:
    - Tier 1: Critical (wrong values break the system)
    - Tier 2: Performance (affects quality, won't break system)
    - Tier 3: Fine-tuning (minor impact, safe to auto-tune)
    """

    # =========================================================================
    # TIER 1: CRITICAL (wrong values break the system)
    # These have strong theoretical priors. Don't tune blindly.
    # =========================================================================

    # NOTE: Eisenhower thresholds defined in PHASE 8 section below (urgency_threshold, importance_threshold)

    # Stabilizer - if wrong, FeltState thrashes or never changes
    stabilizer_confirmations: int = 2    # Theory: 1 is too reactive, 3+ too slow
    stabilizer_cooldown: int = 3         # Theory: must exceed confirmation window

    # =========================================================================
    # TIER 2: PERFORMANCE (affects quality, won't break system)
    # These benefit from empirical tuning via sensitivity analysis.
    # =========================================================================

    # Epistemic transition hysteresis
    kk_ku_confirmations: int = 3         # KK -> KU requires 3 signals
    ku_kk_confirmations: int = 2         # KU -> KK requires 2 signals (easier to confirm)
    kk_uk_confirmations: int = 4         # KK -> UK requires 4 signals (retrieval is rare)
    uk_uu_confirmations: int = 3         # UK -> UU requires 3 signals

    # Valence classification thresholds
    valence_threat_threshold: float = -0.3    # Below this = THREAT
    valence_opportunity_threshold: float = 0.3  # Above this = OPPORTUNITY

    # NOTE: Queue management defined in PHASE 8 section below (scheduled_queue_max, queue_aging_rate)

    # Cooldown periods (cycles before can transition again)
    kk_cooldown: int = 5
    ku_cooldown: int = 3
    uk_cooldown: int = 7
    uu_cooldown: int = 4

    # =========================================================================
    # TIER 3: FINE-TUNING (minor impact, can safely auto-tune)
    # These are candidates for online adaptation via sensitivity analysis.
    # =========================================================================

    # FeltState dimension weights (sum to 1.0)
    felt_weight_valence: float = 0.25
    felt_weight_arousal: float = 0.20
    felt_weight_certainty: float = 0.20
    felt_weight_agency: float = 0.20
    felt_weight_salience: float = 0.15

    # Graph evolution
    edge_trust_decay: float = 0.95        # Per-cycle decay of edge trust
    crystallization_base_threshold: int = 5  # Traversals needed to crystallize

    # Urgency computation weights
    urgency_budget_weight: float = 0.4
    urgency_volatility_weight: float = 0.3
    urgency_blocking_weight: float = 0.2
    urgency_cascade_weight: float = 0.1

    # Importance computation weights
    importance_win_prob_weight: float = 0.4
    importance_theory_weight: float = 0.3
    importance_unlock_weight: float = 0.2
    importance_trust_weight: float = 0.1

    # =========================================================================
    # PHASE 8: EISENHOWER LAYER PARAMETERS
    # =========================================================================

    # Urgency score component weights (must sum to 1.0)
    urgency_time_pressure_weight: float = 0.30    # Actions remaining / budget
    urgency_resource_scarcity_weight: float = 0.30  # How close to limits
    urgency_volatility_weight_eis: float = 0.20   # How fast things change
    urgency_external_forcing_weight: float = 0.20  # Deadline pressure

    # Importance score component weights (must sum to 1.0)
    importance_epistemic_value_weight: float = 0.40  # How much we'd learn
    importance_goal_alignment_weight: float = 0.40   # How much it helps winning
    importance_strategic_value_weight: float = 0.20  # Long-term benefit

    # Cross-matrix mapping (Rumsfeld -> Eisenhower bias)
    rumsfeld_kk_urgency_boost: float = 0.2    # KK: trust what we know
    rumsfeld_kk_importance_boost: float = 0.1
    rumsfeld_ku_urgency_boost: float = 0.0    # KU: questions important, urgency varies
    rumsfeld_ku_importance_boost: float = 0.2
    rumsfeld_uk_urgency_boost: float = -0.1   # UK: retrieval not urgent
    rumsfeld_uk_importance_boost: float = 0.1
    rumsfeld_uu_urgency_boost: float = -0.2   # UU: exploration not urgent
    rumsfeld_uu_importance_boost: float = 0.0

    # EisenhowerLayer class constants
    scheduled_queue_max: int = 10             # Max Q2 tasks in queue
    queue_aging_rate: float = 0.05            # Urgency increase per cycle
    default_rung_unlock_score: float = 0.3    # Default unlock score for unmapped rungs

    # Urgency/importance thresholds
    urgency_threshold: float = 0.5            # Score above = urgent
    importance_threshold: float = 0.5         # Score above = important

    # =========================================================================
    # PHASE 9: PHENOMENOLOGY LAYER PARAMETERS
    # =========================================================================

    # Valence classification thresholds (raw score boundaries)
    phenomenology_threat_threshold: float = -0.3      # Below = THREAT
    phenomenology_confusion_threshold: float = -0.1   # -0.3 to -0.1 = CONFUSION
    phenomenology_curiosity_threshold: float = 0.2    # 0.2 to 0.4 = CURIOSITY
    phenomenology_mastery_threshold: float = 0.4      # Above = MASTERY

    # FeltState stabilizer settings
    phenomenology_inertia: float = 0.3           # Blend with previous (0=no inertia, 1=frozen)
    phenomenology_max_valence_changes: int = 2   # Max valence changes per window
    phenomenology_smoothing_window: int = 5      # Cycles to average over

    # Cold start handling
    phenomenology_cold_start_cycles: int = 3     # Cycles before full confidence
    phenomenology_cold_start_salience: float = 0.7  # High salience during cold start

    # Transition stabilizer (FeltStateStabilizer)
    phenomenology_transition_cooldown: int = 3   # Cycles before can transition again

    # PhenomenologyLayer class constants
    phenomenology_compression_budget_ms: float = 5.0  # Max ms for compression
    phenomenology_max_history: int = 100         # Max FeltState history
    phenomenology_max_trace_log: int = 500       # Max trace entries

    # Threshold parameters for FeltState biases
    phenomenology_certainty_high: float = 0.7    # High certainty threshold
    phenomenology_certainty_low: float = 0.3     # Low certainty threshold
    phenomenology_agency_high: float = 0.7       # High agency threshold
    phenomenology_salience_high: float = 0.7     # High salience threshold
    phenomenology_momentum_negative: float = -0.3  # Negative momentum threshold

    # Valence scoring thresholds (different from classification)
    phenomenology_valence_threat_threshold: float = -0.3  # Score below = THREAT
    phenomenology_valence_opportunity_threshold: float = 0.3  # Score above = OPPORTUNITY

    # Progress weight in valence computation
    valence_progress_weight: float = 0.3         # Weight for level progress

    # Algorithm modulation multipliers
    modulation_panic_beam_width: float = 0.5     # Narrow beam in panic
    modulation_panic_exploitation_bonus: float = 0.3
    modulation_bored_beam_width: float = 1.5     # Wide beam when bored
    modulation_bored_exploration_bonus: float = 0.3
    modulation_mastery_exploitation_bonus: float = 0.5

    # CRITICAL: External validation weights for valence computation
    # Prevents "feeling good while losing" - must include objective signals
    valence_internal_weight: float = 0.5         # Confidence, agency, certainty
    valence_external_weight: float = 0.5         # Score delta, action success, deaths
    # External signal components
    valence_score_delta_weight: float = 0.4      # Did score improve?
    valence_action_success_weight: float = 0.3   # Did last action work?
    valence_death_penalty_weight: float = 0.3    # Deaths are bad signals

    # =========================================================================
    # PHASE 10: VALENCE-TAGGED KNOWLEDGE PARAMETERS
    # =========================================================================

    # Auto-tagging thresholds
    valence_tag_threat_urgency: float = 1.0      # Threat tags get max urgency
    valence_tag_threat_importance: float = 1.0
    valence_tag_confusion_urgency: float = 0.7
    valence_tag_confusion_importance: float = 0.9
    valence_tag_curiosity_urgency: float = 0.3
    valence_tag_curiosity_importance: float = 0.7
    valence_tag_mastery_urgency: float = 0.2
    valence_tag_mastery_importance: float = 1.0

    # Aggregate computation
    valence_aggregate_decay: float = 0.9         # Per-cycle decay of old tags

    # =========================================================================
    # PHASE 11: GRAPH EVOLUTION + PHENOMENOLOGY INTEGRATION
    # =========================================================================

    # Valence-weighted crystallization multipliers
    crystallization_mastery_multiplier: float = 0.7   # Faster crystallization
    crystallization_curiosity_multiplier: float = 0.8
    crystallization_neutral_multiplier: float = 1.0
    crystallization_threat_multiplier: float = 1.5    # Needs more validation
    crystallization_confusion_multiplier: float = 2.0  # Much more validation

    # Edge trust penalties for discovery context
    edge_trust_confusion_penalty: float = 0.2    # Penalize confused discoveries
    edge_trust_threat_penalty: float = 0.1       # Slight penalty for panic discoveries

    # Feel trajectory tracking
    feel_trajectory_window: int = 20             # Cycles to track
    feel_anomaly_threshold: float = 2.0          # Std devs for anomaly detection

    def validate(self) -> bool:
        """
        Validate parameter constraints.

        Returns:
            True if valid, raises ValueError if invalid
        """
        # Tier 1 constraints
        if not 0 < self.urgency_threshold < 1:
            raise ValueError(f"urgency_threshold must be in (0, 1), got {self.urgency_threshold}")
        if not 0 < self.importance_threshold < 1:
            raise ValueError(f"importance_threshold must be in (0, 1), got {self.importance_threshold}")
        if self.stabilizer_confirmations < 1:
            raise ValueError(f"stabilizer_confirmations must be >= 1, got {self.stabilizer_confirmations}")
        if self.stabilizer_cooldown < self.stabilizer_confirmations:
            raise ValueError(
                f"stabilizer_cooldown ({self.stabilizer_cooldown}) must be >= "
                f"stabilizer_confirmations ({self.stabilizer_confirmations})"
            )

        # Tier 3 weight constraints (should sum to 1.0)
        felt_weights = (
            self.felt_weight_valence +
            self.felt_weight_arousal +
            self.felt_weight_certainty +
            self.felt_weight_agency +
            self.felt_weight_salience
        )
        if abs(felt_weights - 1.0) > 0.01:
            raise ValueError(f"FeltState weights must sum to 1.0, got {felt_weights:.2f}")

        urgency_weights = (
            self.urgency_budget_weight +
            self.urgency_volatility_weight +
            self.urgency_blocking_weight +
            self.urgency_cascade_weight
        )
        if abs(urgency_weights - 1.0) > 0.01:
            raise ValueError(f"Urgency weights must sum to 1.0, got {urgency_weights:.2f}")

        importance_weights = (
            self.importance_win_prob_weight +
            self.importance_theory_weight +
            self.importance_unlock_weight +
            self.importance_trust_weight
        )
        if abs(importance_weights - 1.0) > 0.01:
            raise ValueError(f"Importance weights must sum to 1.0, got {importance_weights:.2f}")

        # Phase 8: Eisenhower weights validation
        eis_urgency_weights = (
            self.urgency_time_pressure_weight +
            self.urgency_resource_scarcity_weight +
            self.urgency_volatility_weight_eis +
            self.urgency_external_forcing_weight
        )
        if abs(eis_urgency_weights - 1.0) > 0.01:
            raise ValueError(f"Eisenhower urgency weights must sum to 1.0, got {eis_urgency_weights:.2f}")

        eis_importance_weights = (
            self.importance_epistemic_value_weight +
            self.importance_goal_alignment_weight +
            self.importance_strategic_value_weight
        )
        if abs(eis_importance_weights - 1.0) > 0.01:
            raise ValueError(f"Eisenhower importance weights must sum to 1.0, got {eis_importance_weights:.2f}")

        # Phase 9: External validation weights
        valence_weights = self.valence_internal_weight + self.valence_external_weight
        if abs(valence_weights - 1.0) > 0.01:
            raise ValueError(f"Valence internal/external weights must sum to 1.0, got {valence_weights:.2f}")

        external_signal_weights = (
            self.valence_score_delta_weight +
            self.valence_action_success_weight +
            self.valence_death_penalty_weight
        )
        if abs(external_signal_weights - 1.0) > 0.01:
            raise ValueError(f"External signal weights must sum to 1.0, got {external_signal_weights:.2f}")

        # Phase 11: Crystallization multipliers must be positive
        if self.crystallization_mastery_multiplier <= 0:
            raise ValueError("crystallization_mastery_multiplier must be > 0")
        if self.crystallization_confusion_multiplier <= 0:
            raise ValueError("crystallization_confusion_multiplier must be > 0")

        return True

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for logging/storage."""
        return {
            # Tier 1
            'urgency_threshold': self.urgency_threshold,
            'importance_threshold': self.importance_threshold,
            'stabilizer_confirmations': self.stabilizer_confirmations,
            'stabilizer_cooldown': self.stabilizer_cooldown,
            # Tier 2
            'kk_ku_confirmations': self.kk_ku_confirmations,
            'ku_kk_confirmations': self.ku_kk_confirmations,
            'kk_uk_confirmations': self.kk_uk_confirmations,
            'uk_uu_confirmations': self.uk_uu_confirmations,
            'valence_threat_threshold': self.valence_threat_threshold,
            'valence_opportunity_threshold': self.valence_opportunity_threshold,
            'scheduled_queue_max': self.scheduled_queue_max,
            'queue_aging_rate': self.queue_aging_rate,
            'kk_cooldown': self.kk_cooldown,
            'ku_cooldown': self.ku_cooldown,
            'uk_cooldown': self.uk_cooldown,
            'uu_cooldown': self.uu_cooldown,
            # Tier 3
            'felt_weight_valence': self.felt_weight_valence,
            'felt_weight_arousal': self.felt_weight_arousal,
            'felt_weight_certainty': self.felt_weight_certainty,
            'felt_weight_agency': self.felt_weight_agency,
            'felt_weight_salience': self.felt_weight_salience,
            'edge_trust_decay': self.edge_trust_decay,
            'crystallization_base_threshold': self.crystallization_base_threshold,
            'urgency_budget_weight': self.urgency_budget_weight,
            'urgency_volatility_weight': self.urgency_volatility_weight,
            'urgency_blocking_weight': self.urgency_blocking_weight,
            'urgency_cascade_weight': self.urgency_cascade_weight,
            'importance_win_prob_weight': self.importance_win_prob_weight,
            'importance_theory_weight': self.importance_theory_weight,
            'importance_unlock_weight': self.importance_unlock_weight,
            'importance_trust_weight': self.importance_trust_weight,
            # Phase 8: Eisenhower
            'urgency_time_pressure_weight': self.urgency_time_pressure_weight,
            'urgency_resource_scarcity_weight': self.urgency_resource_scarcity_weight,
            'urgency_volatility_weight_eis': self.urgency_volatility_weight_eis,
            'urgency_external_forcing_weight': self.urgency_external_forcing_weight,
            'importance_epistemic_value_weight': self.importance_epistemic_value_weight,
            'importance_goal_alignment_weight': self.importance_goal_alignment_weight,
            'importance_strategic_value_weight': self.importance_strategic_value_weight,
            'rumsfeld_kk_urgency_boost': self.rumsfeld_kk_urgency_boost,
            'rumsfeld_kk_importance_boost': self.rumsfeld_kk_importance_boost,
            'rumsfeld_ku_urgency_boost': self.rumsfeld_ku_urgency_boost,
            'rumsfeld_ku_importance_boost': self.rumsfeld_ku_importance_boost,
            'rumsfeld_uk_urgency_boost': self.rumsfeld_uk_urgency_boost,
            'rumsfeld_uk_importance_boost': self.rumsfeld_uk_importance_boost,
            'rumsfeld_uu_urgency_boost': self.rumsfeld_uu_urgency_boost,
            'rumsfeld_uu_importance_boost': self.rumsfeld_uu_importance_boost,
            # Phase 9: Phenomenology
            'phenomenology_threat_threshold': self.phenomenology_threat_threshold,
            'phenomenology_confusion_threshold': self.phenomenology_confusion_threshold,
            'phenomenology_curiosity_threshold': self.phenomenology_curiosity_threshold,
            'phenomenology_mastery_threshold': self.phenomenology_mastery_threshold,
            'phenomenology_inertia': self.phenomenology_inertia,
            'phenomenology_max_valence_changes': self.phenomenology_max_valence_changes,
            'phenomenology_smoothing_window': self.phenomenology_smoothing_window,
            'phenomenology_cold_start_cycles': self.phenomenology_cold_start_cycles,
            'phenomenology_cold_start_salience': self.phenomenology_cold_start_salience,
            'modulation_panic_beam_width': self.modulation_panic_beam_width,
            'modulation_panic_exploitation_bonus': self.modulation_panic_exploitation_bonus,
            'modulation_bored_beam_width': self.modulation_bored_beam_width,
            'modulation_bored_exploration_bonus': self.modulation_bored_exploration_bonus,
            'modulation_mastery_exploitation_bonus': self.modulation_mastery_exploitation_bonus,
            'valence_internal_weight': self.valence_internal_weight,
            'valence_external_weight': self.valence_external_weight,
            'valence_score_delta_weight': self.valence_score_delta_weight,
            'valence_action_success_weight': self.valence_action_success_weight,
            'valence_death_penalty_weight': self.valence_death_penalty_weight,
            # Phase 10: Valence-Tagged Knowledge
            'valence_tag_threat_urgency': self.valence_tag_threat_urgency,
            'valence_tag_threat_importance': self.valence_tag_threat_importance,
            'valence_tag_confusion_urgency': self.valence_tag_confusion_urgency,
            'valence_tag_confusion_importance': self.valence_tag_confusion_importance,
            'valence_tag_curiosity_urgency': self.valence_tag_curiosity_urgency,
            'valence_tag_curiosity_importance': self.valence_tag_curiosity_importance,
            'valence_tag_mastery_urgency': self.valence_tag_mastery_urgency,
            'valence_tag_mastery_importance': self.valence_tag_mastery_importance,
            'valence_aggregate_decay': self.valence_aggregate_decay,
            # Phase 11: Graph Evolution + Phenomenology
            'crystallization_mastery_multiplier': self.crystallization_mastery_multiplier,
            'crystallization_curiosity_multiplier': self.crystallization_curiosity_multiplier,
            'crystallization_neutral_multiplier': self.crystallization_neutral_multiplier,
            'crystallization_threat_multiplier': self.crystallization_threat_multiplier,
            'crystallization_confusion_multiplier': self.crystallization_confusion_multiplier,
            'edge_trust_confusion_penalty': self.edge_trust_confusion_penalty,
            'edge_trust_threat_penalty': self.edge_trust_threat_penalty,
            'feel_trajectory_window': self.feel_trajectory_window,
            'feel_anomaly_threshold': self.feel_anomaly_threshold,
        }

    @classmethod
    def get_tier(cls, param_name: str) -> int:
        """
        Get the tier for a parameter name.

        Args:
            param_name: Name of the parameter

        Returns:
            1, 2, or 3 for the tier level
        """
        tier1 = {
            'urgency_threshold', 'importance_threshold',
            'stabilizer_confirmations', 'stabilizer_cooldown',
            # Phase 9: If wrong, valence completely disconnected from reality
            'valence_internal_weight', 'valence_external_weight',
        }
        tier2 = {
            'kk_ku_confirmations', 'ku_kk_confirmations',
            'kk_uk_confirmations', 'uk_uu_confirmations',
            'valence_threat_threshold', 'valence_opportunity_threshold',
            'scheduled_queue_max', 'queue_aging_rate',
            'kk_cooldown', 'ku_cooldown', 'uk_cooldown', 'uu_cooldown',
            # Phase 8: Eisenhower cross-matrix mapping
            'rumsfeld_kk_urgency_boost', 'rumsfeld_kk_importance_boost',
            'rumsfeld_ku_urgency_boost', 'rumsfeld_ku_importance_boost',
            'rumsfeld_uk_urgency_boost', 'rumsfeld_uk_importance_boost',
            'rumsfeld_uu_urgency_boost', 'rumsfeld_uu_importance_boost',
            # Phase 9: Valence thresholds affect classification
            'phenomenology_threat_threshold', 'phenomenology_confusion_threshold',
            'phenomenology_curiosity_threshold', 'phenomenology_mastery_threshold',
            'phenomenology_inertia', 'phenomenology_max_valence_changes',
            # Phase 11: Crystallization multipliers
            'crystallization_mastery_multiplier', 'crystallization_confusion_multiplier',
            'crystallization_threat_multiplier',
        }

        if param_name in tier1:
            return 1
        elif param_name in tier2:
            return 2
        else:
            return 3

    @classmethod
    def from_dict(cls, overrides: Dict[str, Any]) -> 'CognitiveParameters':
        """
        Create CognitiveParameters from a dict of overrides.

        Args:
            overrides: Dict of parameter_name -> value

        Returns:
            New CognitiveParameters with overrides applied
        """
        return cls(**overrides)

    def diff(self, other: 'CognitiveParameters') -> Dict[str, Tuple[Any, Any]]:
        """
        Return parameters that differ between two configurations.

        Useful for debugging when comparing parameter sets.

        Args:
            other: Another CognitiveParameters instance to compare

        Returns:
            Dict mapping param_name -> (self_value, other_value)
        """
        diffs = {}
        for key in self.to_dict():
            v1 = getattr(self, key)
            v2 = getattr(other, key)
            if v1 != v2:
                diffs[key] = (v1, v2)
        return diffs

    @classmethod
    def from_dict_by_tier(cls, overrides: Dict[str, Any], max_tier: int = 3) -> 'CognitiveParameters':
        """
        Load only parameters up to specified tier (safety for auto-tuning).

        This prevents auto-tuning systems from accidentally modifying
        critical Tier 1 parameters.

        Args:
            overrides: Dict of parameter overrides
            max_tier: Maximum tier to allow (1, 2, or 3)

        Returns:
            New CognitiveParameters with safe overrides applied
        """
        safe_overrides = {
            k: v for k, v in overrides.items()
            if cls.get_tier(k) <= max_tier
        }
        return cls.from_dict(safe_overrides)


# =============================================================================
# PARAMETER HISTORY TRACKING
# =============================================================================

@dataclass
class ParameterChangeRecord:
    """Record of a single parameter change."""
    timestamp: datetime
    reason: str
    param_name: str
    old_value: Any
    new_value: Any


class CognitiveParameterHistory:
    """
    Track parameter changes over time for debugging.

    Usage:
        history = CognitiveParameterHistory()
        history.record("tuning experiment", old_params, new_params)
        changes = history.find_changes("urgency_threshold")
    """

    def __init__(self):
        self.records: List[ParameterChangeRecord] = []
        self._snapshots: List[Tuple[datetime, str, CognitiveParameters]] = []

    def record(self, reason: str, old_params: CognitiveParameters, new_params: CognitiveParameters):
        """
        Record parameter changes between two configurations.

        Args:
            reason: Why the change was made
            old_params: Previous configuration
            new_params: New configuration
        """
        timestamp = datetime.now()
        diffs = old_params.diff(new_params)

        for param_name, (old_val, new_val) in diffs.items():
            self.records.append(ParameterChangeRecord(
                timestamp=timestamp,
                reason=reason,
                param_name=param_name,
                old_value=old_val,
                new_value=new_val,
            ))

        # Also store full snapshot
        self._snapshots.append((timestamp, reason, new_params))

    def snapshot(self, reason: str, params: CognitiveParameters):
        """Record a snapshot without comparison."""
        self._snapshots.append((datetime.now(), reason, params))

    def find_changes(self, param_name: str) -> List[ParameterChangeRecord]:
        """
        Find all changes to a specific parameter.

        Args:
            param_name: Name of the parameter to search for

        Returns:
            List of change records for that parameter
        """
        return [r for r in self.records if r.param_name == param_name]

    def get_recent(self, n: int = 10) -> List[ParameterChangeRecord]:
        """Get the N most recent parameter changes."""
        return self.records[-n:] if self.records else []

    def get_snapshots(self) -> List[Tuple[datetime, str, CognitiveParameters]]:
        """Get all snapshots."""
        return self._snapshots.copy()

    def to_json(self) -> str:
        """
        Serialize history for persistence.

        Useful for persisting parameter history across restarts to investigate
        "what changed last Tuesday when things started failing."

        Returns:
            JSON string of all parameter change records
        """
        import json
        return json.dumps([
            {
                'timestamp': r.timestamp.isoformat(),
                'reason': r.reason,
                'param_name': r.param_name,
                'old_value': r.old_value,
                'new_value': r.new_value,
            }
            for r in self.records
        ])

    @classmethod
    def from_json(cls, json_str: str) -> 'CognitiveParameterHistory':
        """
        Deserialize history from JSON.

        Args:
            json_str: JSON string from to_json()

        Returns:
            New CognitiveParameterHistory with loaded records
        """
        import json
        history = cls()
        for item in json.loads(json_str):
            history.records.append(ParameterChangeRecord(
                timestamp=datetime.fromisoformat(item['timestamp']),
                reason=item['reason'],
                param_name=item['param_name'],
                old_value=item['old_value'],
                new_value=item['new_value'],
            ))
        return history


# Default parameters instance
DEFAULT_COGNITIVE_PARAMS = CognitiveParameters()

# Global history tracker (optional - import and use if needed)
PARAMETER_HISTORY = CognitiveParameterHistory()
