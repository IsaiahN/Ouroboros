"""
Graph Evolution Engine with Valence-Weighted Crystallization.

Phase 11: Phenomenology <-> Graph Evolution Integration

Paths discovered under different FeltStates have different reliability:
- THREAT paths: Discovered under panic - may be suboptimal escapes
- BOREDOM paths: Discovered during exploration - may be gold (successful innovation)
- CONFUSION paths: Discovered while lost - may be lucky flukes

This module tracks the FeltState context of edge discovery and adjusts
crystallization thresholds accordingly:
- THREAT paths require 1.5x traversals to crystallize (panic decisions need validation)
- CONFUSION paths require 2.0x traversals (lucky flukes need lots of validation)
- BOREDOM paths with >70% success crystallize at 0.7x threshold (exploration gold)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# Import centralized parameters
from config.cognitive_parameters import DEFAULT_COGNITIVE_PARAMS as _PARAMS

# Import Valence from phenomenology layer
from engines.cognition.phenomenology_layer import FeltState, Valence

# ============================================================================
# CRYSTALLIZATION THRESHOLDS
# ============================================================================


BASE_CRYSTALLIZATION_THRESHOLD = _PARAMS.crystallization_base_threshold

# Multipliers for valence-adjusted thresholds (from CognitiveParameters)
VALENCE_THRESHOLD_MULTIPLIERS: Dict[Valence, float] = {
    Valence.THREAT: _PARAMS.crystallization_threat_multiplier,
    Valence.CONFUSION: _PARAMS.crystallization_confusion_multiplier,
    Valence.OPPORTUNITY: _PARAMS.crystallization_neutral_multiplier,
    Valence.STABILITY: _PARAMS.crystallization_curiosity_multiplier,  # Maps to "confident"
    Valence.BOREDOM: _PARAMS.crystallization_neutral_multiplier,  # Base, special case below
}

# Success rate threshold for BOREDOM fast-track crystallization
BOREDOM_SUCCESS_THRESHOLD = 0.7
BOREDOM_FAST_TRACK_MULTIPLIER = _PARAMS.crystallization_mastery_multiplier

# Minimum success rate for crystallization to occur at all
MIN_SUCCESS_RATE_FOR_CRYSTALLIZATION = 0.6


# ============================================================================
# VALENCE-WEIGHTED EDGE
# ============================================================================

@dataclass
class ValenceWeightedEdge:
    """
    Edge in the cognitive graph that tracks the FeltState context of discovery.

    Unlike traditional edges that only track traversal counts and success rates,
    ValenceWeightedEdge remembers HOW the path was discovered - under threat,
    during boredom, while confused, etc. This context affects how quickly
    the edge crystallizes into a preferred path.

    Crystallization = edge becomes a "trusted" path that gets priority

    Attributes:
        from_rung: Source rung identifier
        to_rung: Target rung identifier
        traversal_count: Total times this edge has been traversed
        success_count: Times traversal led to positive outcome
        discovery_valence: FeltState valence when edge was first discovered
        discovery_arousal: FeltState arousal when edge was first discovered
        discovery_timestamp: When the edge was first discovered
        last_traversal: When the edge was last used
        is_crystallized: Whether this edge has been crystallized
        crystallization_timestamp: When crystallization occurred (if applicable)
    """
    from_rung: str
    to_rung: str
    traversal_count: int = 0
    success_count: int = 0

    # FeltState context at discovery
    discovery_valence: Valence = Valence.CONFUSION
    discovery_arousal: float = 0.5

    # Timestamps
    discovery_timestamp: datetime = field(default_factory=datetime.now)
    last_traversal: datetime = field(default_factory=datetime.now)

    # Crystallization state
    is_crystallized: bool = False
    crystallization_timestamp: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate the success rate for this edge."""
        if self.traversal_count == 0:
            return 0.0
        return self.success_count / self.traversal_count

    @property
    def edge_key(self) -> Tuple[str, str]:
        """Return the unique key for this edge."""
        return (self.from_rung, self.to_rung)

    @property
    def valence_adjusted_crystallization_threshold(self) -> int:
        """
        Calculate the crystallization threshold adjusted for discovery context.

        Paths discovered under THREAT require more traversals to crystallize.
        Paths discovered under BOREDOM that succeed crystallize faster.
        Paths discovered under CONFUSION require the most validation.

        Returns:
            Adjusted threshold (number of successful traversals needed)
        """
        base = BASE_CRYSTALLIZATION_THRESHOLD

        # Get base multiplier for discovery valence
        multiplier = VALENCE_THRESHOLD_MULTIPLIERS.get(
            self.discovery_valence, 1.0
        )

        # Special case: BOREDOM with high success rate gets fast-tracked
        # Successful exploration is valuable - crystallize faster
        if (self.discovery_valence == Valence.BOREDOM and
            self.success_rate > BOREDOM_SUCCESS_THRESHOLD):
            multiplier = BOREDOM_FAST_TRACK_MULTIPLIER

        # Higher arousal at discovery = more scrutiny needed
        # (decisions made under high arousal may be reactive)
        arousal_adjustment = 1.0 + (self.discovery_arousal - 0.5) * 0.2

        final_threshold = base * multiplier * arousal_adjustment
        return max(1, int(final_threshold))

    def record_traversal(self, success: bool) -> None:
        """
        Record a traversal of this edge.

        Args:
            success: Whether the traversal led to a positive outcome
        """
        self.traversal_count += 1
        if success:
            self.success_count += 1
        self.last_traversal = datetime.now()

    def check_crystallization(self) -> bool:
        """
        Check if this edge should crystallize based on current stats.

        Returns:
            True if edge meets crystallization criteria
        """
        if self.is_crystallized:
            return True  # Already crystallized

        threshold = self.valence_adjusted_crystallization_threshold

        # Must have enough traversals AND sufficient success rate
        if self.traversal_count < threshold:
            return False

        if self.success_rate < MIN_SUCCESS_RATE_FOR_CRYSTALLIZATION:
            return False

        return True

    def crystallize(self) -> bool:
        """
        Attempt to crystallize this edge.

        Returns:
            True if crystallization succeeded, False if criteria not met
        """
        if self.is_crystallized:
            return True  # Already done

        if not self.check_crystallization():
            return False

        self.is_crystallized = True
        self.crystallization_timestamp = datetime.now()
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize edge to dictionary for database storage."""
        return {
            'from_rung': self.from_rung,
            'to_rung': self.to_rung,
            'traversal_count': self.traversal_count,
            'success_count': self.success_count,
            'discovery_valence': self.discovery_valence.value,
            'discovery_arousal': self.discovery_arousal,
            'discovery_timestamp': self.discovery_timestamp.isoformat(),
            'last_traversal': self.last_traversal.isoformat(),
            'is_crystallized': self.is_crystallized,
            'crystallization_timestamp': (
                self.crystallization_timestamp.isoformat()
                if self.crystallization_timestamp else None
            ),
            'success_rate': self.success_rate,
            'threshold': self.valence_adjusted_crystallization_threshold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValenceWeightedEdge':
        """Deserialize edge from dictionary."""
        edge = cls(
            from_rung=data['from_rung'],
            to_rung=data['to_rung'],
            traversal_count=data['traversal_count'],
            success_count=data['success_count'],
            discovery_valence=Valence(data['discovery_valence']),
            discovery_arousal=data['discovery_arousal'],
        )
        edge.discovery_timestamp = datetime.fromisoformat(data['discovery_timestamp'])
        edge.last_traversal = datetime.fromisoformat(data['last_traversal'])
        edge.is_crystallized = data['is_crystallized']
        if data['crystallization_timestamp']:
            edge.crystallization_timestamp = datetime.fromisoformat(
                data['crystallization_timestamp']
            )
        return edge


# ============================================================================
# GRAPH EVOLUTION ENGINE
# ============================================================================

class GraphEvolution:
    """
    Tracks edge traversals with FeltState context for intelligent crystallization.

    This engine maintains the cognitive graph that represents learned paths
    between rungs. Unlike traditional graph evolution that treats all paths
    equally, this version tracks the emotional/phenomenological context
    in which paths were discovered.

    Key features:
    - Records traversals with FeltState context
    - Applies valence-weighted crystallization thresholds
    - Tracks crystallized (preferred) vs non-crystallized paths
    - Supports edge trust queries for routing decisions

    Usage:
        graph = GraphEvolution()

        # Record a traversal
        graph.record_traversal('survey', 'pattern_detect', success=True, felt_state=felt)

        # Check if path should be preferred
        if graph.should_crystallize(('survey', 'pattern_detect')):
            graph.crystallize_edge(('survey', 'pattern_detect'))

        # Get edge trust for routing
        trust = graph.get_edge_trust('survey', 'pattern_detect')
    """

    def __init__(self):
        """Initialize empty graph evolution tracker."""
        self.edges: Dict[Tuple[str, str], ValenceWeightedEdge] = {}
        self._crystallized_paths: Set[Tuple[str, str]] = set()
        self._creation_time = datetime.now()

    def record_traversal(
        self,
        from_rung: str,
        to_rung: str,
        success: bool,
        felt_state: FeltState
    ) -> ValenceWeightedEdge:
        """
        Record a traversal between rungs with FeltState context.

        If this is a new edge, creates it with the current FeltState as
        discovery context. If edge exists, updates traversal stats.

        Args:
            from_rung: Source rung identifier
            to_rung: Target rung identifier
            success: Whether traversal led to positive outcome
            felt_state: Current phenomenological state

        Returns:
            The updated (or newly created) edge
        """
        edge_key = (from_rung, to_rung)

        if edge_key not in self.edges:
            # New edge - capture discovery context
            self.edges[edge_key] = ValenceWeightedEdge(
                from_rung=from_rung,
                to_rung=to_rung,
                traversal_count=1,
                success_count=1 if success else 0,
                discovery_valence=felt_state.valence,
                discovery_arousal=felt_state.arousal,
            )
        else:
            # Existing edge - update stats
            self.edges[edge_key].record_traversal(success)

        # Check for auto-crystallization
        edge = self.edges[edge_key]
        if edge.check_crystallization() and not edge.is_crystallized:
            edge.crystallize()
            self._crystallized_paths.add(edge_key)

        return edge

    def should_crystallize(self, edge_key: Tuple[str, str]) -> bool:
        """
        Check if edge should become crystallized (preferred path).

        Args:
            edge_key: Tuple of (from_rung, to_rung)

        Returns:
            True if edge meets valence-adjusted crystallization criteria
        """
        edge = self.edges.get(edge_key)
        if not edge:
            return False
        return edge.check_crystallization()

    def crystallize_edge(self, edge_key: Tuple[str, str]) -> bool:
        """
        Manually trigger crystallization of an edge.

        Args:
            edge_key: Tuple of (from_rung, to_rung)

        Returns:
            True if crystallization succeeded
        """
        edge = self.edges.get(edge_key)
        if not edge:
            return False

        if edge.crystallize():
            self._crystallized_paths.add(edge_key)
            return True
        return False

    def get_edge(self, from_rung: str, to_rung: str) -> Optional[ValenceWeightedEdge]:
        """
        Get edge between two rungs if it exists.

        Args:
            from_rung: Source rung identifier
            to_rung: Target rung identifier

        Returns:
            ValenceWeightedEdge or None
        """
        return self.edges.get((from_rung, to_rung))

    def get_edge_trust(self, from_rung: str, to_rung: str) -> float:
        """
        Get trust score for an edge (used in routing decisions).

        Trust is based on:
        - Success rate (primary factor)
        - Crystallization status (bonus)
        - Discovery context (valence-based adjustment)

        Args:
            from_rung: Source rung identifier
            to_rung: Target rung identifier

        Returns:
            Trust score between 0.0 and 1.0
        """
        edge = self.edges.get((from_rung, to_rung))
        if not edge:
            return 0.0

        # Base trust from success rate
        base_trust = edge.success_rate

        # Bonus for crystallized edges
        if edge.is_crystallized:
            base_trust = min(1.0, base_trust + 0.1)

        # Adjust for discovery valence
        # Paths discovered under STABILITY are more trustworthy
        # Paths discovered under CONFUSION are less trustworthy (even if successful)
        valence_trust_modifier = {
            Valence.STABILITY: 1.1,
            Valence.OPPORTUNITY: 1.0,
            Valence.BOREDOM: 1.0,
            Valence.THREAT: 0.9,
            Valence.CONFUSION: 0.85,
        }
        modifier = valence_trust_modifier.get(edge.discovery_valence, 1.0)

        return min(1.0, base_trust * modifier)

    def get_crystallized_edges(self) -> List[ValenceWeightedEdge]:
        """Get all crystallized (preferred) edges."""
        return [
            edge for edge in self.edges.values()
            if edge.is_crystallized
        ]

    def get_edges_from_rung(self, from_rung: str) -> List[ValenceWeightedEdge]:
        """Get all edges originating from a given rung."""
        return [
            edge for key, edge in self.edges.items()
            if key[0] == from_rung
        ]

    def get_edges_to_rung(self, to_rung: str) -> List[ValenceWeightedEdge]:
        """Get all edges leading to a given rung."""
        return [
            edge for key, edge in self.edges.items()
            if key[1] == to_rung
        ]

    def get_preferred_next_rung(self, from_rung: str) -> Optional[str]:
        """
        Get the preferred (highest trust) next rung from a given rung.

        Args:
            from_rung: Current rung identifier

        Returns:
            Best next rung identifier, or None if no edges exist
        """
        edges = self.get_edges_from_rung(from_rung)
        if not edges:
            return None

        # Sort by trust score descending
        edges_with_trust = [
            (edge, self.get_edge_trust(edge.from_rung, edge.to_rung))
            for edge in edges
        ]
        edges_with_trust.sort(key=lambda x: x[1], reverse=True)

        return edges_with_trust[0][0].to_rung if edges_with_trust else None

    def get_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for the graph."""
        if not self.edges:
            return {
                'total_edges': 0,
                'crystallized_edges': 0,
                'avg_success_rate': 0.0,
                'avg_traversals': 0.0,
                'valence_distribution': {},
            }

        valence_counts: Dict[str, int] = {}
        for edge in self.edges.values():
            val_name = edge.discovery_valence.value
            valence_counts[val_name] = valence_counts.get(val_name, 0) + 1

        return {
            'total_edges': len(self.edges),
            'crystallized_edges': len(self._crystallized_paths),
            'avg_success_rate': sum(e.success_rate for e in self.edges.values()) / len(self.edges),
            'avg_traversals': sum(e.traversal_count for e in self.edges.values()) / len(self.edges),
            'valence_distribution': valence_counts,
        }

    def decay_unused_edges(self, decay_factor: float = 0.95, min_age_hours: float = 24.0) -> int:
        """
        Apply decay to edges that haven't been used recently.

        This prevents the graph from being dominated by historical patterns
        that may no longer be relevant.

        Args:
            decay_factor: Multiplier for success_count (0.95 = 5% decay)
            min_age_hours: Only decay edges older than this

        Returns:
            Number of edges affected
        """
        now = datetime.now()
        affected = 0

        for edge in self.edges.values():
            hours_since_use = (now - edge.last_traversal).total_seconds() / 3600
            if hours_since_use >= min_age_hours:
                old_count = edge.success_count
                edge.success_count = max(0, int(edge.success_count * decay_factor))
                if edge.success_count != old_count:
                    affected += 1
                    # May need to un-crystallize if success rate dropped
                    if edge.is_crystallized and edge.success_rate < MIN_SUCCESS_RATE_FOR_CRYSTALLIZATION:
                        edge.is_crystallized = False
                        edge.crystallization_timestamp = None
                        self._crystallized_paths.discard(edge.edge_key)

        return affected

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire graph to dictionary."""
        return {
            'edges': {
                f"{k[0]}:{k[1]}": v.to_dict()
                for k, v in self.edges.items()
            },
            'creation_time': self._creation_time.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GraphEvolution':
        """Deserialize graph from dictionary."""
        graph = cls()
        graph._creation_time = datetime.fromisoformat(data['creation_time'])

        for key_str, edge_data in data['edges'].items():
            edge = ValenceWeightedEdge.from_dict(edge_data)
            graph.edges[edge.edge_key] = edge
            if edge.is_crystallized:
                graph._crystallized_paths.add(edge.edge_key)

        return graph


# ============================================================================
# GAME FEEL TRAJECTORY (Optional)
# ============================================================================

@dataclass
class GameFeelTrajectory:
    """
    Typical FeltState progression for a game type.

    Tracks the "normal" emotional arc of playing a particular game,
    allowing detection of anomalies - e.g., if a player is experiencing
    THREAT during what's normally a boring opening phase.

    Attributes:
        game_id: Game identifier
        typical_opening_valence: Usually CONFUSION or BOREDOM
        typical_midgame_valence: Usually OPPORTUNITY or THREAT
        typical_resolution_valence: Usually STABILITY or THREAT
        variance_by_phase: How much variation is normal per phase
        sample_count: Number of playthroughs used to build this trajectory
        last_updated: When this trajectory was last updated
    """
    game_id: str
    typical_opening_valence: Valence = Valence.CONFUSION
    typical_midgame_valence: Valence = Valence.OPPORTUNITY
    typical_resolution_valence: Valence = Valence.STABILITY
    variance_by_phase: Dict[str, float] = field(default_factory=lambda: {
        'opening': 0.3,
        'midgame': 0.4,
        'resolution': 0.3,
    })
    sample_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    # Collected history for trajectory learning
    _opening_valences: List[Valence] = field(default_factory=list)
    _midgame_valences: List[Valence] = field(default_factory=list)
    _resolution_valences: List[Valence] = field(default_factory=list)

    def record_playthrough(
        self,
        opening_valence: Valence,
        midgame_valence: Valence,
        resolution_valence: Valence
    ) -> None:
        """
        Record a playthrough's emotional trajectory.

        After enough samples, recalculates typical valences.
        """
        self._opening_valences.append(opening_valence)
        self._midgame_valences.append(midgame_valence)
        self._resolution_valences.append(resolution_valence)
        self.sample_count += 1
        self.last_updated = datetime.now()

        # Update typical valences after enough samples
        if self.sample_count >= 5:
            self._update_typical_valences()

    def _update_typical_valences(self) -> None:
        """Calculate most common valence for each phase."""
        def most_common(valences: List[Valence]) -> Valence:
            if not valences:
                return Valence.CONFUSION
            counts: Dict[Valence, int] = {}
            for v in valences:
                counts[v] = counts.get(v, 0) + 1
            return max(counts.keys(), key=lambda k: counts[k])

        self.typical_opening_valence = most_common(self._opening_valences[-20:])
        self.typical_midgame_valence = most_common(self._midgame_valences[-20:])
        self.typical_resolution_valence = most_common(self._resolution_valences[-20:])

        # Calculate variance (proportion of samples that differ from typical)
        def calc_variance(valences: List[Valence], typical: Valence) -> float:
            if not valences:
                return 0.5
            recent = valences[-20:]
            diff_count = sum(1 for v in recent if v != typical)
            return diff_count / len(recent)

        self.variance_by_phase = {
            'opening': calc_variance(self._opening_valences, self.typical_opening_valence),
            'midgame': calc_variance(self._midgame_valences, self.typical_midgame_valence),
            'resolution': calc_variance(self._resolution_valences, self.typical_resolution_valence),
        }

    def get_expected_valence(self, phase: str) -> Valence:
        """Get expected valence for a phase."""
        phase_map = {
            'opening': self.typical_opening_valence,
            'midgame': self.typical_midgame_valence,
            'resolution': self.typical_resolution_valence,
        }
        return phase_map.get(phase, Valence.CONFUSION)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize trajectory to dictionary."""
        return {
            'game_id': self.game_id,
            'typical_opening_valence': self.typical_opening_valence.value,
            'typical_midgame_valence': self.typical_midgame_valence.value,
            'typical_resolution_valence': self.typical_resolution_valence.value,
            'variance_by_phase': self.variance_by_phase,
            'sample_count': self.sample_count,
            'last_updated': self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameFeelTrajectory':
        """Deserialize trajectory from dictionary."""
        return cls(
            game_id=data['game_id'],
            typical_opening_valence=Valence(data['typical_opening_valence']),
            typical_midgame_valence=Valence(data['typical_midgame_valence']),
            typical_resolution_valence=Valence(data['typical_resolution_valence']),
            variance_by_phase=data['variance_by_phase'],
            sample_count=data['sample_count'],
            last_updated=datetime.fromisoformat(data['last_updated']),
        )


@dataclass
class FeelAnomaly:
    """Represents a detected anomaly in emotional trajectory."""
    game_id: str
    phase: str
    expected_valence: Valence
    actual_valence: Valence
    severity: float  # 0.0 to 1.0
    description: str
    timestamp: datetime = field(default_factory=datetime.now)


def detect_feel_anomaly(
    current_felt: FeltState,
    phase: str,
    trajectory: GameFeelTrajectory
) -> Optional[FeelAnomaly]:
    """
    Detect if current game is feeling unusual compared to typical trajectory.

    Args:
        current_felt: Current FeltState
        phase: Current game phase ('opening', 'midgame', 'resolution')
        trajectory: Typical trajectory for this game type

    Returns:
        FeelAnomaly if detected, None otherwise
    """
    if trajectory.sample_count < 5:
        # Not enough data for meaningful anomaly detection
        return None

    expected = trajectory.get_expected_valence(phase)
    actual = current_felt.valence

    if expected == actual:
        return None  # No anomaly

    # Calculate severity based on how different the valences are
    valence_severity = {
        # (expected, actual) -> severity
        # More severe when going from positive to negative
        (Valence.STABILITY, Valence.THREAT): 0.9,
        (Valence.STABILITY, Valence.CONFUSION): 0.6,
        (Valence.OPPORTUNITY, Valence.THREAT): 0.8,
        (Valence.OPPORTUNITY, Valence.CONFUSION): 0.5,
        (Valence.BOREDOM, Valence.THREAT): 0.7,
        (Valence.CONFUSION, Valence.THREAT): 0.4,
        # Less severe when going from negative to positive
        (Valence.THREAT, Valence.STABILITY): 0.3,
        (Valence.THREAT, Valence.OPPORTUNITY): 0.2,
        (Valence.CONFUSION, Valence.STABILITY): 0.2,
        (Valence.CONFUSION, Valence.OPPORTUNITY): 0.3,
    }

    severity = valence_severity.get((expected, actual), 0.5)

    # Reduce severity if high variance is normal for this phase
    phase_variance = trajectory.variance_by_phase.get(phase, 0.3)
    severity *= (1.0 - phase_variance * 0.5)

    # Only report significant anomalies
    if severity < 0.3:
        return None

    description = (
        f"In {phase} phase, expected {expected.value} but experiencing {actual.value}. "
        f"This differs from {trajectory.sample_count} previous playthroughs."
    )

    return FeelAnomaly(
        game_id=trajectory.game_id,
        phase=phase,
        expected_valence=expected,
        actual_valence=actual,
        severity=severity,
        description=description,
    )


# ============================================================================
# FEEL TRAJECTORY STORE
# ============================================================================

class FeelTrajectoryStore:
    """
    Storage and management for game feel trajectories.

    Tracks typical emotional patterns across different games,
    enabling anomaly detection and cross-game pattern analysis.
    """

    def __init__(self):
        """Initialize empty trajectory store."""
        self.trajectories: Dict[str, GameFeelTrajectory] = {}

    def get_or_create(self, game_id: str) -> GameFeelTrajectory:
        """Get existing trajectory or create new one for game."""
        if game_id not in self.trajectories:
            self.trajectories[game_id] = GameFeelTrajectory(game_id=game_id)
        return self.trajectories[game_id]

    def record_playthrough(
        self,
        game_id: str,
        opening_valence: Valence,
        midgame_valence: Valence,
        resolution_valence: Valence
    ) -> GameFeelTrajectory:
        """Record a playthrough for a game and update its trajectory."""
        trajectory = self.get_or_create(game_id)
        trajectory.record_playthrough(opening_valence, midgame_valence, resolution_valence)
        return trajectory

    def detect_anomaly(
        self,
        game_id: str,
        current_felt: FeltState,
        phase: str
    ) -> Optional[FeelAnomaly]:
        """Check for anomaly in current game feel."""
        trajectory = self.trajectories.get(game_id)
        if not trajectory:
            return None
        return detect_feel_anomaly(current_felt, phase, trajectory)

    def get_games_by_typical_opening(self, valence: Valence) -> List[str]:
        """Get games that typically start with a given valence."""
        return [
            game_id for game_id, traj in self.trajectories.items()
            if traj.typical_opening_valence == valence
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for trajectory store."""
        if not self.trajectories:
            return {'total_games': 0, 'total_playthroughs': 0}

        return {
            'total_games': len(self.trajectories),
            'total_playthroughs': sum(t.sample_count for t in self.trajectories.values()),
            'avg_playthroughs_per_game': (
                sum(t.sample_count for t in self.trajectories.values()) / len(self.trajectories)
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize store to dictionary."""
        return {
            'trajectories': {
                game_id: traj.to_dict()
                for game_id, traj in self.trajectories.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeelTrajectoryStore':
        """Deserialize store from dictionary."""
        store = cls()
        for game_id, traj_data in data.get('trajectories', {}).items():
            store.trajectories[game_id] = GameFeelTrajectory.from_dict(traj_data)
        return store
