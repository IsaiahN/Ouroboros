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
from typing import Dict


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

    # Eisenhower thresholds - if wrong, nothing gets done or everything does
    urgency_threshold: float = 0.6       # Theory: >0.5 is "more urgent than not"
    importance_threshold: float = 0.5    # Theory: same logic

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

    # Queue management
    scheduled_queue_max: int = 10        # Max Q2 tasks to queue
    queue_aging_rate: float = 0.05       # Urgency increase per cycle

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
            'stabilizer_confirmations', 'stabilizer_cooldown'
        }
        tier2 = {
            'kk_ku_confirmations', 'ku_kk_confirmations',
            'kk_uk_confirmations', 'uk_uu_confirmations',
            'valence_threat_threshold', 'valence_opportunity_threshold',
            'scheduled_queue_max', 'queue_aging_rate',
            'kk_cooldown', 'ku_cooldown', 'uk_cooldown', 'uu_cooldown'
        }

        if param_name in tier1:
            return 1
        elif param_name in tier2:
            return 2
        else:
            return 3


# Default parameters instance
DEFAULT_COGNITIVE_PARAMS = CognitiveParameters()
