import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Console Metrics Capture - Real-time metrics from console output
================================================================

Captures structured metrics during gameplay without needing API access
to reasoning logs. Uses in-memory aggregation during each generation.

ADDED: ReasoningLogCapture class for capturing reasoning payloads and
detecting bugs that require manual analysis (Q1-Q5, hypotheses, etc.)

Rule 1: Disable pycache
Rule 2: All data in database (final metrics stored)
Rule 11: No unicode emojis
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# REASONING LOG CAPTURE - For detecting bugs like "Q1 says no actions but
# frame_changes has 20+ items"
# =============================================================================

@dataclass
class ReasoningSnapshot:
    """Single reasoning payload snapshot for analysis."""
    game_id: str
    agent_id: str
    level: int
    action_index: int
    action_taken: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Q1-Q5 Emergent cognition
    q1_observable: str = ""
    q2_uncertainty: str = ""
    q3_curiosity: str = ""
    q4_fear: str = ""
    q5_desire: str = ""

    # Frame analysis
    frame_changes_count: int = 0
    delta_frame_changes_count: int = 0
    objects_in_scene: int = 0

    # Hypothesis state
    hypotheses_active: int = 0
    hypothesis_ids: List[str] = field(default_factory=list)
    working_theory: str = ""

    # Decision contributors
    decision_contributors: Dict[str, Any] = field(default_factory=dict)
    cods_active: bool = False

    # Self model
    controlled_objects: List[str] = field(default_factory=list)
    inferred_goals: List[str] = field(default_factory=list)


@dataclass
class ReasoningDiagnostic:
    """Diagnostic result detecting reasoning bugs."""
    bug_type: str
    severity: str  # 'critical', 'warning', 'info'
    description: str
    evidence: Dict[str, Any]
    snapshot: Optional[ReasoningSnapshot] = None


class ReasoningLogCapture:
    """
    Capture reasoning payloads during gameplay for automated bug detection.

    The Oracle can use this to detect bugs like:
    - Q1 says "no actions observed" but frame_changes has 20+ items
    - Hypothesis formed but never tested
    - Working theory stuck as "425 Too Early" for 400+ frames
    - Decision contributors show no influence from any system
    """

    def __init__(self, generation: int):
        self.generation = generation
        self.snapshots: Dict[str, List[ReasoningSnapshot]] = defaultdict(list)
        self.diagnostics: List[ReasoningDiagnostic] = []
        self._started_at = datetime.now()

    def reset(self, generation: int):
        """Reset for new generation."""
        self.generation = generation
        self.snapshots.clear()
        self.diagnostics.clear()
        self._started_at = datetime.now()

    def record_reasoning_payload(
        self,
        game_id: str,
        agent_id: str,
        level: int,
        action_index: int,
        action_taken: str,
        reasoning_payload: Dict[str, Any]
    ):
        """
        Record a reasoning payload for analysis.

        Call this from core_gameplay.py after building the reasoning JSON.

        Args:
            game_id: Current game ID
            agent_id: Agent executing the action
            level: Current level number
            action_index: Action counter (how many actions taken this game)
            action_taken: The action (e.g., "ACTION1")
            reasoning_payload: The full reasoning JSON dict
        """
        snapshot = ReasoningSnapshot(
            game_id=game_id,
            agent_id=agent_id,
            level=level,
            action_index=action_index,
            action_taken=action_taken
        )

        # Extract understanding section (Q1-Q5)
        understanding = reasoning_payload.get('understanding', {})
        snapshot.q1_observable = str(understanding.get('Q1_observable', ''))
        snapshot.q2_uncertainty = str(understanding.get('Q2_uncertainty', ''))
        snapshot.q3_curiosity = str(understanding.get('Q3_curiosity', ''))
        snapshot.q4_fear = str(understanding.get('Q4_fear', ''))
        snapshot.q5_desire = str(understanding.get('Q5_desire', ''))

        # Extract delta section (frame changes)
        delta = reasoning_payload.get('delta', {})
        frame_changes = delta.get('frame_changes', [])
        snapshot.frame_changes_count = len(frame_changes) if isinstance(frame_changes, list) else 0

        # Look for delta frame changes in various places
        delta_changes = delta.get('delta_frame_changes', [])
        if not delta_changes:
            # Check identity section for self_model delta
            identity = reasoning_payload.get('identity', {})
            self_model = identity.get('self_model', {})
            delta_changes = self_model.get('delta_frame_changes', [])
        snapshot.delta_frame_changes_count = len(delta_changes) if isinstance(delta_changes, list) else 0

        # Extract environment section
        environment = reasoning_payload.get('environment', {})
        world_model = environment.get('world_model', {})
        scene_obj = world_model.get('scene_objects', [])
        snapshot.objects_in_scene = len(scene_obj) if isinstance(scene_obj, list) else 0

        # Extract network wisdom (hypotheses)
        network = reasoning_payload.get('network_wisdom', {})
        hypotheses = network.get('hypotheses', [])
        snapshot.hypotheses_active = len(hypotheses) if isinstance(hypotheses, list) else 0
        if isinstance(hypotheses, list):
            snapshot.hypothesis_ids = [h.get('id', '')[:12] for h in hypotheses if isinstance(h, dict)]

        # Extract identity section for working theory
        identity = reasoning_payload.get('identity', {})
        snapshot.working_theory = str(identity.get('working_theory', ''))

        # Extract action section for decision contributors
        action_section = reasoning_payload.get('action', {})
        snapshot.decision_contributors = action_section.get('decision_contributors', {})

        # Check for CODS
        cods_suggestion = action_section.get('cods_suggestion')
        snapshot.cods_active = cods_suggestion is not None and cods_suggestion != ''

        # Extract self model for controlled objects
        self_model = identity.get('self_model', {})
        ctrl_objs = self_model.get('objects_agent_controls', [])
        if isinstance(ctrl_objs, list):
            snapshot.controlled_objects = [str(o) for o in ctrl_objs[:5]]

        goals = self_model.get('inferred_goals', [])
        if isinstance(goals, list):
            snapshot.inferred_goals = [str(g) for g in goals[:5]]

        # Store snapshot
        self.snapshots[game_id].append(snapshot)

        # Run live diagnostics
        self._run_live_diagnostics(snapshot)

    def _run_live_diagnostics(self, snapshot: ReasoningSnapshot):
        """Run diagnostic checks on each snapshot as it arrives."""

        # BUG 1: Q1 says "no actions" but frame has changes
        if snapshot.delta_frame_changes_count > 10:
            q1_lower = snapshot.q1_observable.lower()
            if 'no action' in q1_lower or 'no change' in q1_lower or '425' in q1_lower:
                self.diagnostics.append(ReasoningDiagnostic(
                    bug_type='Q1_DISCONNECT',
                    severity='critical',
                    description=(
                        f"Q1 reports no actions but {snapshot.delta_frame_changes_count} "
                        f"frame changes detected. Observation->Hypothesis loop broken."
                    ),
                    evidence={
                        'q1_text': snapshot.q1_observable[:200],
                        'delta_changes': snapshot.delta_frame_changes_count,
                        'action_index': snapshot.action_index
                    },
                    snapshot=snapshot
                ))

        # BUG 2: Working theory stuck as "425 Too Early" for too long
        if '425' in snapshot.working_theory and snapshot.action_index > 50:
            self.diagnostics.append(ReasoningDiagnostic(
                bug_type='WORKING_THEORY_STUCK',
                severity='warning',
                description=(
                    f"Working theory still '425 Too Early' after {snapshot.action_index} "
                    f"actions. Should have formed a theory by now."
                ),
                evidence={
                    'working_theory': snapshot.working_theory,
                    'action_index': snapshot.action_index,
                    'level': snapshot.level
                },
                snapshot=snapshot
            ))

        # BUG 3: Hypotheses exist but no decision contributor uses them
        if snapshot.hypotheses_active > 0:
            contrib = snapshot.decision_contributors
            # Check if any contributor mentions hypothesis
            contrib_str = json.dumps(contrib).lower()
            if 'hypothesis' not in contrib_str and 'dm-3' not in contrib_str:
                self.diagnostics.append(ReasoningDiagnostic(
                    bug_type='HYPOTHESIS_UNUSED',
                    severity='warning',
                    description=(
                        f"{snapshot.hypotheses_active} hypotheses available but not used "
                        f"in decision making. DM-3 not activating."
                    ),
                    evidence={
                        'hypothesis_count': snapshot.hypotheses_active,
                        'decision_contributors': contrib,
                        'hypothesis_ids': snapshot.hypothesis_ids
                    },
                    snapshot=snapshot
                ))

        # BUG 4: No controlled objects after many actions
        if snapshot.action_index > 100 and len(snapshot.controlled_objects) == 0:
            # Check if there's any self-model at all
            if not snapshot.inferred_goals:
                self.diagnostics.append(ReasoningDiagnostic(
                    bug_type='NO_SELF_MODEL',
                    severity='warning',
                    description=(
                        f"No controlled objects or goals identified after "
                        f"{snapshot.action_index} actions. Self-model not forming."
                    ),
                    evidence={
                        'action_index': snapshot.action_index,
                        'objects_in_scene': snapshot.objects_in_scene,
                        'level': snapshot.level
                    },
                    snapshot=snapshot
                ))

        # BUG 5: All Q fields empty/null status codes
        q_fields = [
            snapshot.q1_observable,
            snapshot.q2_uncertainty,
            snapshot.q3_curiosity,
            snapshot.q4_fear,
            snapshot.q5_desire
        ]
        null_count = sum(1 for q in q_fields if '425' in q or '404' in q or not q.strip())
        if null_count >= 4 and snapshot.action_index > 20:
            self.diagnostics.append(ReasoningDiagnostic(
                bug_type='EMERGENT_COGNITION_DEAD',
                severity='critical',
                description=(
                    f"{null_count}/5 Q-fields empty/null after {snapshot.action_index} "
                    f"actions. Emergent cognition system not activating."
                ),
                evidence={
                    'q1': snapshot.q1_observable[:100] if snapshot.q1_observable else 'EMPTY',
                    'q2': snapshot.q2_uncertainty[:100] if snapshot.q2_uncertainty else 'EMPTY',
                    'q3': snapshot.q3_curiosity[:100] if snapshot.q3_curiosity else 'EMPTY',
                    'action_index': snapshot.action_index
                },
                snapshot=snapshot
            ))

    def get_game_analysis(self, game_id: str) -> Dict[str, Any]:
        """Get reasoning analysis for a specific game."""
        snapshots = self.snapshots.get(game_id, [])
        if not snapshots:
            return {'game_id': game_id, 'status': 'no_data'}

        # Aggregate analysis
        total_actions = len(snapshots)

        # Q1 disconnect rate
        q1_disconnects = sum(
            1 for s in snapshots
            if s.delta_frame_changes_count > 10 and
               ('no action' in s.q1_observable.lower() or '425' in s.q1_observable)
        )

        # Hypothesis usage
        actions_with_hypotheses = sum(1 for s in snapshots if s.hypotheses_active > 0)

        # Theory formation
        theory_formed = any(
            '425' not in s.working_theory and s.working_theory.strip()
            for s in snapshots
        )
        first_theory_action = next(
            (i for i, s in enumerate(snapshots)
             if '425' not in s.working_theory and s.working_theory.strip()),
            -1
        )

        # Self-model formation
        self_model_formed = any(s.controlled_objects for s in snapshots)
        first_self_model_action = next(
            (i for i, s in enumerate(snapshots) if s.controlled_objects),
            -1
        )

        return {
            'game_id': game_id,
            'total_actions': total_actions,
            'q1_disconnect_rate': q1_disconnects / max(total_actions, 1),
            'q1_disconnect_count': q1_disconnects,
            'hypothesis_usage_rate': actions_with_hypotheses / max(total_actions, 1),
            'theory_formed': theory_formed,
            'first_theory_action': first_theory_action,
            'self_model_formed': self_model_formed,
            'first_self_model_action': first_self_model_action,
            'final_level': snapshots[-1].level if snapshots else 0
        }

    def get_diagnostics_summary(self) -> Dict[str, Any]:
        """Get summary of all diagnostics for Oracle consumption."""
        by_type = defaultdict(list)
        for d in self.diagnostics:
            by_type[d.bug_type].append(d)

        critical_count = sum(1 for d in self.diagnostics if d.severity == 'critical')
        warning_count = sum(1 for d in self.diagnostics if d.severity == 'warning')

        return {
            'generation': self.generation,
            'total_diagnostics': len(self.diagnostics),
            'critical_count': critical_count,
            'warning_count': warning_count,
            'by_type': {
                bug_type: {
                    'count': len(diags),
                    'severity': diags[0].severity if diags else 'unknown',
                    'sample_description': diags[0].description if diags else '',
                    'affected_games': list(set(
                        d.snapshot.game_id for d in diags if d.snapshot
                    ))[:5]
                }
                for bug_type, diags in by_type.items()
            },
            'games_analyzed': len(self.snapshots),
            'duration_seconds': (datetime.now() - self._started_at).total_seconds()
        }

    def print_diagnostics_report(self):
        """Print diagnostics report to console."""
        summary = self.get_diagnostics_summary()

        print(f"\n[REASONING-DIAG] Generation {summary['generation']} Reasoning Diagnostics")
        print("-" * 60)
        print(f"  Games Analyzed: {summary['games_analyzed']}")
        print(f"  Total Diagnostics: {summary['total_diagnostics']}")
        print(f"  Critical: {summary['critical_count']}, Warnings: {summary['warning_count']}")

        if summary['by_type']:
            print("\n  Bug Types Detected:")
            for bug_type, info in summary['by_type'].items():
                severity_marker = "[CRIT]" if info['severity'] == 'critical' else "[WARN]"
                print(f"    {severity_marker} {bug_type}: {info['count']} occurrences")
                print(f"        {info['sample_description'][:80]}...")
        else:
            print("\n  [OK] No reasoning bugs detected")

        print("-" * 60)


# =============================================================================
# GLOBAL REASONING CAPTURE SINGLETON
# =============================================================================

_global_reasoning_capture: Optional[ReasoningLogCapture] = None


def get_reasoning_capture(generation: int = 0) -> ReasoningLogCapture:
    """Get or create global reasoning capture instance."""
    global _global_reasoning_capture

    if _global_reasoning_capture is None:
        _global_reasoning_capture = ReasoningLogCapture(generation=generation)
    elif _global_reasoning_capture.generation != generation:
        _global_reasoning_capture.reset(generation)

    return _global_reasoning_capture


def record_reasoning(
    game_id: str,
    agent_id: str,
    level: int,
    action_index: int,
    action_taken: str,
    reasoning_payload: Dict[str, Any]
):
    """Convenience function to record reasoning payload."""
    if _global_reasoning_capture:
        _global_reasoning_capture.record_reasoning_payload(
            game_id, agent_id, level, action_index, action_taken, reasoning_payload
        )


def get_reasoning_diagnostics() -> Optional[Dict[str, Any]]:
    """Get reasoning diagnostics summary."""
    if _global_reasoning_capture:
        return _global_reasoning_capture.get_diagnostics_summary()
    return None


@dataclass
class GameMetrics:
    """Metrics for a single game."""
    game_id: str
    game_type: str
    agent_id: str
    final_score: float = 0.0
    levels_completed: int = 0
    total_actions: int = 0
    cods_activations: int = 0
    escape_attempts: int = 0
    sequence_replays: int = 0
    stuck_detections: int = 0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None


@dataclass
class GenerationMetrics:
    """Aggregated metrics for a generation."""
    generation: int
    games_played: int = 0
    total_score: float = 0.0
    total_levels: int = 0
    total_actions: int = 0
    total_cods_activations: int = 0
    total_escape_attempts: int = 0
    total_sequence_replays: int = 0
    total_stuck_detections: int = 0
    level_completions: int = 0  # Games with at least 1 level completed
    positive_scores: int = 0    # Games with score > 0
    max_score: float = 0.0
    max_levels: int = 0
    games_by_type: Dict[str, int] = field(default_factory=dict)
    scores_by_type: Dict[str, float] = field(default_factory=dict)

    def add_game(self, game: GameMetrics):
        """Add game metrics to generation totals."""
        self.games_played += 1
        self.total_score += game.final_score
        self.total_levels += game.levels_completed
        self.total_actions += game.total_actions
        self.total_cods_activations += game.cods_activations
        self.total_escape_attempts += game.escape_attempts
        self.total_sequence_replays += game.sequence_replays
        self.total_stuck_detections += game.stuck_detections

        if game.levels_completed > 0:
            self.level_completions += 1

        if game.final_score > 0:
            self.positive_scores += 1

        self.max_score = max(self.max_score, game.final_score)
        self.max_levels = max(self.max_levels, game.levels_completed)

        # Track by game type
        game_type = game.game_type
        if game_type not in self.games_by_type:
            self.games_by_type[game_type] = 0
            self.scores_by_type[game_type] = 0.0
        self.games_by_type[game_type] += 1
        self.scores_by_type[game_type] += game.final_score

    def get_summary(self) -> Dict[str, Any]:
        """Get summary metrics for health monitoring."""
        games = max(self.games_played, 1)  # Avoid division by zero

        return {
            'generation': self.generation,
            'games_played': self.games_played,
            'avg_score': self.total_score / games,
            'avg_levels': self.total_levels / games,
            'avg_actions': self.total_actions / games,
            'max_score': self.max_score,
            'max_levels': self.max_levels,
            'level_completions': self.level_completions,
            'positive_scores': self.positive_scores,
            'level_completion_rate': self.level_completions / games,
            'positive_score_rate': self.positive_scores / games,
            'cods_activations': self.total_cods_activations,
            'cods_rate': self.total_cods_activations / games,
            'escape_attempts': self.total_escape_attempts,
            'sequence_replays': self.total_sequence_replays,
            'stuck_detections': self.total_stuck_detections,
            'games_by_type': self.games_by_type,
            'avg_score_by_type': {
                gt: self.scores_by_type[gt] / count
                for gt, count in self.games_by_type.items()
            }
        }


class ConsoleMetricsCapture:
    """
    Capture and aggregate metrics during evolution.

    This class is designed to be called from within the evolution loop
    to record metrics as games are played, providing real-time data
    without needing to query the database.

    Usage:
        capture = ConsoleMetricsCapture(generation=5)

        # During game loop:
        capture.start_game(game_id, game_type, agent_id)
        capture.record_cods_activation(game_id)
        capture.record_escape_attempt(game_id)
        capture.end_game(game_id, score, levels, actions)

        # After generation:
        summary = capture.get_generation_summary()
    """

    def __init__(self, generation: int = 0):
        self.generation = generation
        self.current_games: Dict[str, GameMetrics] = {}
        self.completed_games: List[GameMetrics] = []
        self.generation_metrics = GenerationMetrics(generation=generation)
        self._started_at = datetime.now()

    def reset(self, generation: int):
        """Reset for a new generation."""
        self.generation = generation
        self.current_games = {}
        self.completed_games = []
        self.generation_metrics = GenerationMetrics(generation=generation)
        self._started_at = datetime.now()

    # =========================================================================
    # GAME LIFECYCLE
    # =========================================================================

    def start_game(self, game_id: str, game_type: str, agent_id: str):
        """Record game start."""
        self.current_games[game_id] = GameMetrics(
            game_id=game_id,
            game_type=game_type,
            agent_id=agent_id
        )

    def end_game(
        self,
        game_id: str,
        final_score: float,
        levels_completed: int,
        total_actions: int
    ):
        """Record game end and finalize metrics."""
        if game_id not in self.current_games:
            # Game wasn't started with start_game, create entry
            game = GameMetrics(
                game_id=game_id,
                game_type=game_id[:4] if len(game_id) >= 4 else 'unknown',
                agent_id='unknown',
                final_score=final_score,
                levels_completed=levels_completed,
                total_actions=total_actions
            )
        else:
            game = self.current_games.pop(game_id)
            game.final_score = final_score
            game.levels_completed = levels_completed
            game.total_actions = total_actions

        game.ended_at = datetime.now().isoformat()
        self.completed_games.append(game)
        self.generation_metrics.add_game(game)

    # =========================================================================
    # IN-GAME EVENTS
    # =========================================================================

    def record_cods_activation(self, game_id: str):
        """Record CODS suggesting an action."""
        if game_id in self.current_games:
            self.current_games[game_id].cods_activations += 1

    def record_escape_attempt(self, game_id: str):
        """Record stuck detection escape attempt."""
        if game_id in self.current_games:
            self.current_games[game_id].escape_attempts += 1

    def record_sequence_replay(self, game_id: str):
        """Record sequence being replayed."""
        if game_id in self.current_games:
            self.current_games[game_id].sequence_replays += 1

    def record_stuck_detection(self, game_id: str):
        """Record stuck state detection."""
        if game_id in self.current_games:
            self.current_games[game_id].stuck_detections += 1

    def record_action(self, game_id: str, action: str):
        """Record an action (optional - for detailed tracking)."""
        if game_id in self.current_games:
            self.current_games[game_id].total_actions += 1

    # =========================================================================
    # SUMMARIES
    # =========================================================================

    def get_generation_summary(self) -> Dict[str, Any]:
        """Get summary metrics for Oracle health monitoring."""
        summary = self.generation_metrics.get_summary()

        # Add timing info
        duration = (datetime.now() - self._started_at).total_seconds()
        summary['duration_seconds'] = duration
        summary['games_per_minute'] = (summary['games_played'] / duration * 60) if duration > 0 else 0

        return summary

    def get_game_metrics(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific game."""
        # Check current games
        if game_id in self.current_games:
            game = self.current_games[game_id]
            return {
                'game_id': game.game_id,
                'game_type': game.game_type,
                'agent_id': game.agent_id,
                'final_score': game.final_score,
                'levels_completed': game.levels_completed,
                'total_actions': game.total_actions,
                'cods_activations': game.cods_activations,
                'escape_attempts': game.escape_attempts,
                'sequence_replays': game.sequence_replays,
                'stuck_detections': game.stuck_detections,
                'status': 'in_progress'
            }

        # Check completed games
        for game in self.completed_games:
            if game.game_id == game_id:
                return {
                    'game_id': game.game_id,
                    'game_type': game.game_type,
                    'agent_id': game.agent_id,
                    'final_score': game.final_score,
                    'levels_completed': game.levels_completed,
                    'total_actions': game.total_actions,
                    'cods_activations': game.cods_activations,
                    'escape_attempts': game.escape_attempts,
                    'sequence_replays': game.sequence_replays,
                    'stuck_detections': game.stuck_detections,
                    'status': 'completed'
                }

        return None

    def get_by_game_type(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics broken down by game type."""
        by_type = defaultdict(lambda: {
            'games': 0,
            'total_score': 0.0,
            'total_levels': 0,
            'total_actions': 0,
            'cods_activations': 0,
            'level_completions': 0
        })

        for game in self.completed_games:
            gt = game.game_type
            by_type[gt]['games'] += 1
            by_type[gt]['total_score'] += game.final_score
            by_type[gt]['total_levels'] += game.levels_completed
            by_type[gt]['total_actions'] += game.total_actions
            by_type[gt]['cods_activations'] += game.cods_activations
            if game.levels_completed > 0:
                by_type[gt]['level_completions'] += 1

        # Calculate averages
        result = {}
        for gt, data in by_type.items():
            games = max(data['games'], 1)
            result[gt] = {
                'games': data['games'],
                'avg_score': data['total_score'] / games,
                'avg_levels': data['total_levels'] / games,
                'avg_actions': data['total_actions'] / games,
                'cods_rate': data['cods_activations'] / games,
                'level_completion_rate': data['level_completions'] / games
            }

        return result

    def print_summary(self):
        """Print generation summary to console."""
        summary = self.get_generation_summary()

        print(f"\n[METRICS] Generation {summary['generation']} Summary")
        print("-" * 50)
        print(f"  Games Played: {summary['games_played']}")
        print(f"  Avg Score: {summary['avg_score']:.2f} (max: {summary['max_score']:.1f})")
        print(f"  Avg Levels: {summary['avg_levels']:.2f} (max: {summary['max_levels']})")
        print(f"  Avg Actions: {summary['avg_actions']:.0f}")
        print(f"  Level Completions: {summary['level_completions']}/{summary['games_played']} "
              f"({summary['level_completion_rate']:.1%})")
        print(f"  Positive Scores: {summary['positive_scores']}/{summary['games_played']} "
              f"({summary['positive_score_rate']:.1%})")
        print(f"  CODS Activations: {summary['cods_activations']} "
              f"({summary['cods_rate']:.1f}/game)")
        print(f"  Escape Attempts: {summary['escape_attempts']}")
        print(f"  Stuck Detections: {summary['stuck_detections']}")
        print(f"  Duration: {summary['duration_seconds']:.0f}s "
              f"({summary['games_per_minute']:.1f} games/min)")

        if summary['games_by_type']:
            print(f"\n  By Game Type:")
            avg_by_type = summary.get('avg_score_by_type', {})
            for gt, count in sorted(summary['games_by_type'].items()):
                avg = avg_by_type.get(gt, 0)
                print(f"    {gt}: {count} games, avg score {avg:.2f}")

        print("-" * 50)


# =============================================================================
# SINGLETON FOR GLOBAL ACCESS
# =============================================================================

_global_capture: Optional[ConsoleMetricsCapture] = None


def get_metrics_capture(generation: int = 0) -> ConsoleMetricsCapture:
    """Get or create global metrics capture instance."""
    global _global_capture

    if _global_capture is None:
        _global_capture = ConsoleMetricsCapture(generation=generation)
    elif _global_capture.generation != generation:
        # New generation, reset
        _global_capture.reset(generation)

    return _global_capture


def reset_metrics_capture(generation: int):
    """Reset global metrics capture for new generation."""
    global _global_capture

    if _global_capture is None:
        _global_capture = ConsoleMetricsCapture(generation=generation)
    else:
        _global_capture.reset(generation)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def record_game_start(game_id: str, game_type: str, agent_id: str):
    """Record game start (uses global capture)."""
    if _global_capture:
        _global_capture.start_game(game_id, game_type, agent_id)


def record_game_end(game_id: str, score: float, levels: int, actions: int):
    """Record game end (uses global capture)."""
    if _global_capture:
        _global_capture.end_game(game_id, score, levels, actions)


def record_cods(game_id: str):
    """Record CODS activation (uses global capture)."""
    if _global_capture:
        _global_capture.record_cods_activation(game_id)


def record_escape(game_id: str):
    """Record escape attempt (uses global capture)."""
    if _global_capture:
        _global_capture.record_escape_attempt(game_id)


def record_stuck(game_id: str):
    """Record stuck detection (uses global capture)."""
    if _global_capture:
        _global_capture.record_stuck_detection(game_id)


def get_summary() -> Optional[Dict[str, Any]]:
    """Get generation summary (uses global capture)."""
    if _global_capture:
        return _global_capture.get_generation_summary()
    return None


if __name__ == "__main__":
    # Quick test
    capture = ConsoleMetricsCapture(generation=1)

    # Simulate some games
    for i in range(5):
        game_id = f"sp80-test{i}"
        capture.start_game(game_id, "sp80", f"agent_{i}")
        capture.record_cods_activation(game_id)
        capture.record_cods_activation(game_id)
        capture.record_stuck_detection(game_id)
        capture.record_escape_attempt(game_id)
        capture.end_game(game_id, i * 0.5, i, 100 + i * 50)

    capture.print_summary()

    print("\nBy game type:")
    for gt, data in capture.get_by_game_type().items():
        print(f"  {gt}: {data}")
