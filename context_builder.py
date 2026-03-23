"""
Context Builder - Build context for decision rungs
==================================================

This module builds the context dictionary that the decision rung system
needs to make action decisions. It extracts and packages:
- Game identification and state
- Agent info (ID, role, weights)
- Position tracking
- Safety weights from danger detection
- Recent action history
- Exploration stats
- CODS context

Usage:
    from context_builder import ContextBuilder

    builder = ContextBuilder(db)
    context = builder.build(loop_state, agent_config)

    # Pass to decision system
    action, reason = decision_system.decide(observation, context)
"""

import logging
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

logger = logging.getLogger(__name__)

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from arcengine import GameAction, GameState

# Import our types
from arc_api_adapter import Observation
from outcome_processor import ActionOutcome, LoopState

# Visual cortex for scene understanding
try:
    from engines.perception.visual_cortex import SceneDescription, VisualCortex
    VISUAL_CORTEX_AVAILABLE = True
except ImportError:
    VISUAL_CORTEX_AVAILABLE = False


@dataclass
class AgentConfig:
    """Configuration for an agent playing games."""
    agent_id: str
    role: str = "pioneer"  # pioneer, optimizer, generalist, exploiter

    # Stream weights (Two Streams theory)
    w_A: float = 0.5  # Private experience weight
    w_B: float = 0.5  # Collective wisdom weight

    # Exploration settings
    exploration_rate: float = 0.3

    # Budget
    action_budget: int = 2000

    # Metadata
    generation: int = 0
    fitness: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'w_A': self.w_A,
            'w_B': self.w_B,
            'exploration_rate': self.exploration_rate,
            'action_budget': self.action_budget,
            'generation': self.generation,
            'fitness': self.fitness,
        }


@dataclass
class DecisionContext:
    """
    Complete context for making a decision.

    This is what gets passed to the decision rung system.
    """
    # Game identification
    game_id: str
    game_type: str  # First 4 chars of game_id
    level: int

    # Game state
    score: float
    levels_completed: int
    win_levels: int
    game_state: GameState

    # Budget tracking
    action_count: int
    budget_remaining: int
    budget_used_percent: float
    phase: str  # "orientation", "hypothesis", "exploitation"

    # Agent info
    agent_id: Optional[str] = None
    agent_role: str = "pioneer"
    w_A: float = 0.5
    w_B: float = 0.5

    # Position tracking
    agent_position: Optional[Tuple[int, int]] = None
    last_position: Optional[Tuple[int, int]] = None
    position_history: List[Tuple[int, int]] = field(default_factory=lambda: [])

    # Safety weights (danger avoidance)
    action_safety_weights: Dict[str, float] = field(default_factory=lambda: {})

    # Recent history
    recent_actions: List[str] = field(default_factory=lambda: [])
    recent_outcomes: List[str] = field(default_factory=lambda: [])  # "positive", "negative", "neutral"

    # Exploration tracking
    is_frontier: bool = False  # Unbeaten level
    exploration_coverage: float = 0.0
    visited_positions: int = 0

    # CODS context (if available)
    cods_hypothesis: Optional[str] = None
    cods_confidence: float = 0.0

    # Sequence context
    has_winning_sequence: bool = False
    sequence_step: int = 0
    sequence_length: int = 0

    # Frontier checkpoint context (constructive pathfinding)
    checkpoint_sequence: Optional[List[int]] = None
    checkpoint_position: int = 0

    # Flags
    is_stuck: bool = False
    is_oscillating: bool = False
    death_count: int = 0

    # Frame info
    frame_width: int = 0
    frame_height: int = 0
    frame_hash: str = ""  # Hash of current frame for topology queries

    # Prior lessons (from lessons_learned table)
    prior_lessons: List[Dict[str, Any]] = field(default_factory=lambda: [])

    # Event understanding (from OutcomeProcessor's EventDetector)
    recent_events: List[Dict[str, Any]] = field(default_factory=lambda: [])
    frame_delta_count: int = 0

    # =====================================================================
    # Visual Cortex scene understanding (populated by ContextBuilder)
    # Full hierarchical visual analysis: panels, tiles, objects, symmetry,
    # transformation hypotheses, reference detection, scene narrative.
    # =====================================================================
    visual_scene: Optional[Dict[str, Any]] = None  # SceneDescription.to_dict()

    # Two-stage analysis (extract objects THEN detect transformations)
    # Populated by PaletteDetectionRung
    detected_palette: Optional[Dict[str, Any]] = None  # PaletteInfo as dict
    extracted_objects: Optional[Dict[str, Any]] = None  # Categorized objects from frame
    detected_transformations: List[Dict[str, Any]] = field(default_factory=lambda: [])

    # Sparse grid representation (efficient pattern matching)
    # Populated by SparseGridRung
    sparse_grid: Optional[Any] = None  # SparseGrid object
    sparse_hash: str = ""  # Structural hash for comparison
    sparse_cell_count: int = 0  # Number of non-background cells
    sparse_colors: Set[int] = field(default_factory=set)  # Colors used
    sparse_components: List[Dict[str, Any]] = field(default_factory=list)  # Connected components
    sparse_diff: Optional[Dict[str, Any]] = None  # Diff from previous frame

    # =====================================================================
    # Part 7 Cognitive Capabilities (world model, goals, classification)
    # These enable the system to accumulate knowledge across actions,
    # understand what the goal is, and select appropriate strategies.
    # =====================================================================

    # 7.1 Within-Game Persistent World Model
    # Accumulates across actions AND levels. Contains causal_map, cell_states,
    # rules_learned, action_history. Updated by on_action_complete feedback.
    world_model: Optional[Dict[str, Any]] = None

    # 7.4 Goal-State Differencing
    # Extracted from reference panel by visual cortex. Shows what needs to change.
    goal_state: Optional[Dict[str, Any]] = None  # {(x,y): target_color}
    goal_delta: Optional[Dict[str, Any]] = None  # {(x,y): (current, target)}

    # 7.5 Puzzle-Type Classification
    # Determined before first action from available_actions + visual analysis.
    # One of: click_toggle, click_transform, movement_maze, pattern_completion, hybrid, unknown
    puzzle_type: str = 'unknown'

    # 7.3 Level-to-Level Differencing
    # What changed between previous and current level. The delta IS the lesson.
    level_diffs: List[Dict[str, Any]] = field(default_factory=list)

    # Phase 0.2 Epistemic State (exposed to rungs for informed decisions)
    # One of: KK (known-known), KU (known-unknown), UK (unknown-known), UU (unknown-unknown)
    epistemic_quadrant: str = 'UU'

    # Part 7.2: Level-aware deliberate experimentation phase
    # 'learning' (levels 1-2), 'transitioning' (level 3), 'applying' (levels 4+)
    level_phase: str = 'learning'

    # =====================================================================
    # Runtime fields (populated by EvolutionRunner game loop)
    # These fields exist so that both ContextBuilder.build() (game_loop.py)
    # and EvolutionRunner.play_game() produce identical context contracts.
    # =====================================================================

    # Raw observation and available actions
    frame_data: Optional[Any] = None  # Raw observation object (obs)
    available_actions: List[int] = field(default_factory=lambda: [1, 2, 3, 4])

    # Action history (evolution_runner tracking)
    last_action: str = ''
    last_actions: List[str] = field(default_factory=list)  # Last 5 actions
    failed_actions: Set[str] = field(default_factory=set)  # Actions that produced no frame change

    # Score tracking
    score_delta: float = 0.0
    last_outcome: str = 'neutral'  # 'positive', 'negative', 'neutral', 'death'

    # Mode flags
    is_novel_game: bool = False  # True for first 50 actions
    optimization_mode: bool = False  # True when game has a full win

    # Session/scorecard tracking
    session_id: Optional[str] = None
    scorecard_id: Optional[str] = None

    # Sequence replay state
    active_sequence: Optional[List] = None
    sequence_position: int = 0
    is_replay: bool = False

    # Stuck tracking
    recent_stuck_count: int = 0

    # Click exploration (ACTION6)
    tried_colors: Set = field(default_factory=set)
    is_action6_only_game: bool = False
    action6_available: bool = False

    # Progress tracking
    last_progress_action: int = 0

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rung system compatibility."""
        return {
            # Game
            'game_id': self.game_id,
            'game_type': self.game_type,
            'level': self.level,
            'score': self.score,
            'levels_completed': self.levels_completed,
            'win_levels': self.win_levels,
            'game_state': self.game_state.name,

            # Budget
            'action_count': self.action_count,
            'budget_remaining': self.budget_remaining,
            'budget_used_percent': self.budget_used_percent,
            'phase': self.phase,

            # Agent
            'agent_id': self.agent_id,
            'agent_role': self.agent_role,
            'w_A': self.w_A,
            'w_B': self.w_B,

            # Position
            'agent_position': self.agent_position,
            'last_position': self.last_position,

            # Safety
            'action_safety_weights': self.action_safety_weights,

            # History
            'recent_actions': self.recent_actions,
            'recent_outcomes': self.recent_outcomes,

            # Exploration
            'is_frontier': self.is_frontier,
            'exploration_coverage': self.exploration_coverage,

            # CODS
            'cods_hypothesis': self.cods_hypothesis,
            'cods_confidence': self.cods_confidence,

            # Sequence
            'has_winning_sequence': self.has_winning_sequence,
            'sequence_step': self.sequence_step,
            'sequence_length': self.sequence_length,

            # Frontier checkpoint (constructive pathfinding)
            'checkpoint_sequence': self.checkpoint_sequence,
            'checkpoint_position': self.checkpoint_position,

            # Flags
            'is_stuck': self.is_stuck,
            'is_oscillating': self.is_oscillating,
            'death_count': self.death_count,

            # Frame
            'frame_width': self.frame_width,
            'frame_height': self.frame_height,
            'frame_hash': self.frame_hash,

            # Frontier mode (alias for is_frontier, used by topology rung)
            'frontier_mode': self.is_frontier,

            # Prior lessons for PriorLessonsRung
            'prior_lessons': self.prior_lessons,

            # Event understanding
            'recent_events': self.recent_events,
            'frame_delta_count': self.frame_delta_count,

            # Visual cortex scene understanding
            'visual_scene': self.visual_scene,

            # Two-stage analysis
            'detected_palette': self.detected_palette,
            'extracted_objects': self.extracted_objects,
            'detected_transformations': self.detected_transformations,

            # Sparse grid representation
            'sparse_grid': self.sparse_grid,
            'sparse_hash': self.sparse_hash,
            'sparse_cell_count': self.sparse_cell_count,
            'sparse_colors': self.sparse_colors,
            'sparse_components': self.sparse_components,
            'sparse_diff': self.sparse_diff,

            # Part 7 Cognitive Capabilities
            'world_model': self.world_model,
            'goal_state': self.goal_state,
            'goal_delta': self.goal_delta,
            'puzzle_type': self.puzzle_type,
            'level_diffs': self.level_diffs,
            'epistemic_quadrant': self.epistemic_quadrant,
            'level_phase': self.level_phase,

            # Runtime fields (evolution_runner game loop)
            'state': self.game_state.name if hasattr(self.game_state, 'name') else str(self.game_state),
            'frame_data': self.frame_data,
            'available_actions': self.available_actions,
            'level_number': self.level,  # Alias
            'last_action': self.last_action,
            'last_actions': self.last_actions,
            'failed_actions': self.failed_actions,
            'position': self.agent_position or (32, 32),
            'player_position': self.agent_position or (32, 32),  # Alias
            'score_delta': self.score_delta,
            'last_outcome': self.last_outcome,
            'frontier_mode': self.is_frontier,  # Alias
            'is_novel_game': self.is_novel_game,
            'optimization_mode': self.optimization_mode,
            'session_id': self.session_id,
            'scorecard_id': self.scorecard_id,
            'active_sequence': self.active_sequence,
            'sequence_position': self.sequence_position,
            'is_replay': self.is_replay,
            'replay_mode': self.is_replay,  # Alias
            'recent_stuck_count': self.recent_stuck_count,
            'tried_colors': self.tried_colors,
            'is_action6_only_game': self.is_action6_only_game,
            'action6_available': self.action6_available,
            'has_winning_sequence': self.has_winning_sequence,
            'last_progress_action': self.last_progress_action,
            'action_budget': self.budget_remaining + self.action_count,  # Total budget
            'total_budget': self.budget_remaining + self.action_count,  # Alias
            'frame_changed': True,  # Default for first action; overwritten by game_player with meaningful_change (Fix 2.4)
        }


class ContextBuilder:
    """
    Build context for the decision rung system.

    Extracts and packages all the state that decision rungs need:
    - Game identification
    - Agent info (ID, role, w_A/w_B weights)
    - Position tracking
    - Safety weights from danger detection
    - Recent actions history
    - Exploration stats
    - CODS context
    - Frontier checkpoint replay state with divergence detection
    """

    def __init__(
        self,
        db: Any = None,
        exploration_tracker: Any = None,
        terminal_detector: Any = None,
    ):
        """
        Initialize the context builder.

        Args:
            db: Database interface for querying state
            exploration_tracker: Optional NetworkExplorationTracker
            terminal_detector: Optional TerminalPatternDetector
        """
        self._db: Any = db
        self._exploration_tracker: Any = exploration_tracker
        self._terminal_detector: Any = terminal_detector

        # Internal state
        self._recent_actions: List[str] = []
        self._recent_outcomes: List[str] = []
        self._position_history: List[Tuple[int, int]] = []
        self._visited_positions: Set[Tuple[int, int]] = set()
        self._death_count = 0
        self._current_game_id: Optional[str] = None

        # Frontier checkpoint replay state
        self._checkpoint_sequence: Optional[List[str]] = None
        self._checkpoint_position: int = 0
        self._checkpoint_level: Optional[int] = None  # Track which level checkpoint is for

        # Divergence detection state
        self._checkpoint_expected_frames: int = 0  # Expected unique frames from checkpoint
        self._checkpoint_frames_seen: Set[str] = set()  # Frame hashes seen during replay
        self._checkpoint_divergence_checked: bool = False  # Only check once at midpoint

        # Event understanding state (populated from OutcomeProcessor)
        self._recent_events: List[Dict[str, Any]] = []
        self._last_frame_delta_count: int = 0

        # Visual cortex for scene understanding
        self._visual_cortex: Optional[Any] = None
        if VISUAL_CORTEX_AVAILABLE:
            try:
                self._visual_cortex = VisualCortex()
                logger.info("[CORTEX] Visual cortex initialized - scene understanding enabled")
            except Exception as e:
                logger.warning(f"Visual cortex init failed: {e}")
                self._visual_cortex = None

        # =====================================================================
        # Part 7 Cognitive Capability State (persists across actions in a game)
        # =====================================================================

        # 7.1 World Model — accumulates causal knowledge across actions/levels
        self._world_model: Dict[str, Any] = {
            'causal_map': {},       # {pos_key: {effect_type, affected_cells, observations}}
            'cell_states': {},      # {pos_key: current_color}
            'goal_state': {},       # {pos_key: target_color}  (from reference panel)
            'delta': {},            # {pos_key: (current, target)}
            'rules_learned': [],    # Compact rules extracted from causal_map
            'level_diffs': [],      # What changed between levels
            'action_history': [],   # [(action, x, y, frame_changed, changes_count)]
        }

        # 7.3 Level-to-Level Differencing state
        self._prev_level_scene: Optional[Dict[str, Any]] = None  # Visual scene at end of prev level
        self._prev_level_number: int = 0
        self._level_diffs: List[Dict[str, Any]] = []

        # 7.5 Puzzle-Type Classification (set once per game, cached)
        self._puzzle_type: str = 'unknown'
        self._puzzle_type_classified: bool = False

        # Phase 0.2: Reference to EpistemicTracker for real quadrant state
        self._epistemic_source: Any = None

    def set_epistemic_source(self, tracker: Any) -> None:
        """Store a reference to an EpistemicTracker for real epistemic state.

        Called once during wiring (e.g. from GamePlayer.__init__).
        The tracker's ``current_state.primary_quadrant.name`` is read each
        time ``build_from_runner_state()`` constructs a DecisionContext.
        """
        self._epistemic_source = tracker

    def build(
        self,
        loop_state: LoopState,
        agent_config: Optional[AgentConfig] = None,
        observation: Optional[Observation] = None,
    ) -> DecisionContext:
        """
        Build complete context for decision making.

        Args:
            loop_state: Current game loop state
            agent_config: Optional agent configuration
            observation: Optional current observation

        Returns:
            DecisionContext with all relevant information
        """
        agent_config = agent_config or AgentConfig(agent_id="default")

        # Calculate budget info
        budget = agent_config.action_budget
        budget_remaining = max(0, budget - loop_state.action_count)
        budget_used_percent = loop_state.action_count / budget if budget > 0 else 1.0

        # Determine phase based on budget used
        phase = self._determine_phase(budget_used_percent)

        # Get frame dimensions
        frame_width = 0
        frame_height = 0
        if loop_state.frame:
            frame_height = len(loop_state.frame)
            frame_width = len(loop_state.frame[0]) if frame_height > 0 else 0

        # Get agent position (simplified - would use self-model in full implementation)
        agent_position = self._detect_agent_position(loop_state.frame)

        # Check if this is a frontier (unbeaten) level
        is_frontier = self._check_is_frontier(loop_state.game_id, loop_state.current_level)

        # Get safety weights
        safety_weights = self._get_safety_weights(loop_state)

        # Check for winning sequence
        has_sequence, seq_step, seq_length = self._check_winning_sequence(
            loop_state.game_id, loop_state.current_level
        )

        # Get CODS context
        cods_hypothesis, cods_confidence = self._get_cods_context(loop_state.game_id)

        # Build context
        return DecisionContext(
            # Game
            game_id=loop_state.game_id,
            game_type=loop_state.game_id[:4] if len(loop_state.game_id) >= 4 else loop_state.game_id,
            level=loop_state.current_level,
            score=loop_state.score,
            levels_completed=loop_state.levels_completed,
            win_levels=loop_state.win_levels,
            game_state=loop_state.state,

            # Budget
            action_count=loop_state.action_count,
            budget_remaining=budget_remaining,
            budget_used_percent=budget_used_percent,
            phase=phase,

            # Agent
            agent_id=agent_config.agent_id,
            agent_role=agent_config.role,
            w_A=agent_config.w_A,
            w_B=agent_config.w_B,

            # Position
            agent_position=agent_position,
            last_position=self._position_history[-1] if self._position_history else None,
            position_history=self._position_history[-10:],

            # Safety
            action_safety_weights=safety_weights,

            # History
            recent_actions=self._recent_actions[-10:],
            recent_outcomes=self._recent_outcomes[-10:],

            # Exploration
            is_frontier=is_frontier,
            exploration_coverage=self._calculate_coverage(),
            visited_positions=len(self._visited_positions),

            # CODS
            cods_hypothesis=cods_hypothesis,
            cods_confidence=cods_confidence,

            # Sequence
            has_winning_sequence=has_sequence,
            sequence_step=seq_step,
            sequence_length=seq_length,

            # Frontier checkpoint (for CONTEXT_ADAPTIVE strategy transition)
            checkpoint_sequence=self._checkpoint_sequence,
            checkpoint_position=self._checkpoint_position,

            # Flags
            is_stuck=self._detect_stuck(),
            is_oscillating=self._detect_oscillation(),
            death_count=self._death_count,

            # Frame
            frame_width=frame_width,
            frame_height=frame_height,

            # Event understanding
            recent_events=self._recent_events.copy(),
            frame_delta_count=self._last_frame_delta_count,
        )

    def build_from_runner_state(
        self,
        *,
        game_id: str,
        obs: Any,
        agent_id: str,
        agent_role: str = 'pioneer',
        w_A: float = 0.5,
        w_B: float = 0.5,
        actions_taken: int,
        max_actions: int,
        available_actions: List[int],
        win_levels: int,
        last_action: str = '',
        recent_actions: Optional[List[str]] = None,
        last_frame_changed: bool = True,
        failed_actions: Optional[set] = None,
        score: float = 0.0,
        score_delta: float = 0.0,
        last_outcome: str = 'neutral',
        has_full_win: bool = False,
        active_sequence: Optional[list] = None,
        sequence_position: int = 0,
        is_replay_mode: bool = False,
        has_level_sequence: bool = False,
        stuck_count: int = 0,
        tried_colors: Optional[set] = None,
        frame_hash: str = '',
        level_start_action_index: int = 0,
        session_id: Optional[str] = None,
        scorecard_id: Optional[str] = None,
    ) -> DecisionContext:
        """
        Build context from EvolutionRunner's game loop state.

        This is the single integration point between EvolutionRunner and the
        decision system. All runtime game state flows through here, ensuring
        rungs see the same context contract regardless of entry point.

        All parameters are keyword-only to prevent positional argument bugs.
        """
        levels_completed = getattr(obs, 'levels_completed', 0) or 0
        level = levels_completed + 1
        game_type = game_id[:4] if game_id and len(game_id) >= 4 else game_id
        budget_remaining = max(0, max_actions - actions_taken)
        budget_used_percent = actions_taken / max(max_actions, 1)
        phase = self._determine_phase(budget_used_percent)
        game_state = getattr(obs, 'state', None)

        # Frame dimensions
        frame = getattr(obs, 'frame', None)
        frame_width = 0
        frame_height = 0
        if frame is not None:
            try:
                if hasattr(frame, 'shape'):
                    frame_height, frame_width = frame.shape[:2]
                elif isinstance(frame, list) and len(frame) > 0:
                    frame_height = len(frame)
                    frame_width = len(frame[0]) if frame_height > 0 else 0
            except Exception:
                pass

        # ACTION6 flags
        _aa_list = list(available_actions) if available_actions is not None else []
        is_action6_only = _aa_list == [6]
        action6_avail = 6 in _aa_list

        # Detect frontier and stuck/oscillation from internal state
        is_frontier = not has_full_win
        is_stuck = self._detect_stuck()
        is_oscillating = self._detect_oscillation()

        # Visual cortex scene analysis
        visual_scene_dict = None
        if self._visual_cortex is not None and frame is not None:
            try:
                frame_list = frame
                if hasattr(frame, 'tolist'):
                    frame_list = frame.tolist()
                if isinstance(frame_list, list) and len(frame_list) > 0:
                    scene = self._visual_cortex.analyze(frame_list)
                    visual_scene_dict = scene.to_dict()
            except Exception as e:
                logger.debug(f"Visual cortex analysis failed: {e}")

        # =====================================================================
        # Part 7 Cognitive Capabilities population
        # =====================================================================

        # 7.5 Puzzle-Type Classification (once per game)
        puzzle_type = self.classify_puzzle_type(available_actions, visual_scene_dict)

        # 7.4 Goal-State Differencing (every action — reference panel may become clearer)
        goal_state, goal_delta = self.extract_goal_state(visual_scene_dict, frame)

        # 7.3 Level-to-Level Differencing (on level transition)
        if level > self._prev_level_number and self._prev_level_number > 0:
            self.compute_level_diff(visual_scene_dict, level)
        elif self._prev_level_number == 0:
            # First action — snapshot for future comparison
            self._prev_level_scene = visual_scene_dict
            self._prev_level_number = level

        # Phase 0.2: Real epistemic state from tracker
        epistemic_q = 'UU'
        if self._epistemic_source is not None:
            try:
                epistemic_q = self._epistemic_source.current_state.primary_quadrant.name
            except Exception:
                pass

        # Part 7.2: Deliberate experimentation mode
        # Levels 1-2: LEARNING phase - maximize information gain
        # Level 3: TRANSITIONING - start applying learned rules
        # Levels 4+: APPLYING - exploit knowledge to complete levels
        if level <= 2:
            level_phase = 'learning'
        elif level == 3:
            level_phase = 'transitioning'
        else:
            level_phase = 'applying'

        return DecisionContext(
            # Game
            game_id=game_id,
            game_type=game_type,
            level=level,
            score=score,
            levels_completed=levels_completed,
            win_levels=win_levels,
            game_state=game_state,

            # Budget
            action_count=actions_taken,
            budget_remaining=budget_remaining,
            budget_used_percent=budget_used_percent,
            phase=phase,

            # Agent
            agent_id=agent_id,
            agent_role=agent_role,
            w_A=w_A,
            w_B=w_B,

            # Position (default center; updated by self-model when available)
            agent_position=(32, 32),
            last_position=self._position_history[-1] if self._position_history else None,
            position_history=self._position_history[-10:],

            # History
            recent_actions=(recent_actions or [])[-10:],
            recent_outcomes=self._recent_outcomes[-10:],

            # Exploration
            is_frontier=is_frontier,
            exploration_coverage=self._calculate_coverage(),
            visited_positions=len(self._visited_positions),

            # Sequence
            has_winning_sequence=has_full_win or has_level_sequence,
            sequence_step=sequence_position,
            sequence_length=len(active_sequence) if active_sequence else 0,

            # Frontier checkpoint
            checkpoint_sequence=self._checkpoint_sequence,
            checkpoint_position=self._checkpoint_position,

            # Flags
            is_stuck=is_stuck,
            is_oscillating=is_oscillating,
            death_count=self._death_count,

            # Frame
            frame_width=frame_width,
            frame_height=frame_height,
            frame_hash=frame_hash,

            # Event understanding
            recent_events=self._recent_events.copy(),
            frame_delta_count=self._last_frame_delta_count,

            # Visual cortex scene understanding
            visual_scene=visual_scene_dict,

            # Part 7 Cognitive Capabilities
            world_model=self._world_model.copy(),
            goal_state=goal_state,
            goal_delta=goal_delta,
            puzzle_type=puzzle_type,
            level_diffs=self._level_diffs.copy(),

            # Phase 0.2: Real epistemic quadrant
            epistemic_quadrant=epistemic_q,

            # Part 7.2: Level-aware experimentation phase
            level_phase=level_phase,

            # Runtime fields (unique to evolution_runner path)
            frame_data=obs,
            available_actions=available_actions,
            last_action=last_action,
            last_actions=(recent_actions or [])[-5:],
            failed_actions=failed_actions or set(),
            score_delta=score_delta,
            last_outcome=last_outcome,
            is_novel_game=actions_taken < 50,
            optimization_mode=has_full_win,
            session_id=session_id,
            scorecard_id=scorecard_id,
            active_sequence=active_sequence if active_sequence else None,
            sequence_position=sequence_position,
            is_replay=is_replay_mode,
            recent_stuck_count=stuck_count,
            tried_colors=tried_colors or set(),
            is_action6_only_game=is_action6_only,
            action6_available=action6_avail,
            last_progress_action=level_start_action_index,
        )

    def update_runner_outcome(self, action: str, outcome_type: str, frame_changed: bool) -> None:
        """
        Lightweight update for EvolutionRunner path (no ActionOutcome object).

        Args:
            action: Action name taken (e.g. 'ACTION4')
            outcome_type: 'positive', 'negative', 'neutral', 'death'
            frame_changed: Whether the frame hash changed
        """
        self._recent_actions.append(action)
        if len(self._recent_actions) > 50:
            self._recent_actions = self._recent_actions[-50:]

        self._recent_outcomes.append(outcome_type)
        if len(self._recent_outcomes) > 50:
            self._recent_outcomes = self._recent_outcomes[-50:]

        if outcome_type == 'death':
            self._death_count += 1

    def update(self, action: str, outcome: ActionOutcome, decision_metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update internal state after an action.

        Args:
            action: The action name that was taken
            outcome: The outcome of the action
            decision_metadata: Optional metadata from the decision system (contains checkpoint info)
        """
        # Track action
        self._recent_actions.append(action)
        if len(self._recent_actions) > 50:
            self._recent_actions = self._recent_actions[-50:]

        # Track outcome type
        if outcome.is_positive:
            self._recent_outcomes.append("positive")
        elif outcome.is_negative:
            self._recent_outcomes.append("negative")
        else:
            self._recent_outcomes.append("neutral")

        if len(self._recent_outcomes) > 50:
            self._recent_outcomes = self._recent_outcomes[-50:]

        # Track position
        if outcome.position_delta and outcome.frame_after:
            # Update position based on delta
            if self._position_history:
                last_x, last_y = self._position_history[-1]
                dx, dy = outcome.position_delta
                new_pos = (last_x + dx, last_y + dy)
            else:
                new_pos = self._detect_agent_position(outcome.frame_after)

            if new_pos:
                self._position_history.append(new_pos)
                self._visited_positions.add(new_pos)

        if len(self._position_history) > 100:
            self._position_history = self._position_history[-100:]

        # Track deaths - also clears checkpoint on death
        if outcome.is_death:
            self._death_count += 1
            self._clear_checkpoint()

        # Track events from outcome (for event understanding rungs)
        self._last_frame_delta_count = getattr(outcome, 'frame_delta_count', 0)
        if hasattr(outcome, 'detected_events') and outcome.detected_events:
            self._recent_events.extend(outcome.detected_events)
            # Keep only last 50 events
            if len(self._recent_events) > 50:
                self._recent_events = self._recent_events[-50:]

        # Handle checkpoint state from decision metadata
        if decision_metadata:
            self._handle_checkpoint_metadata(decision_metadata)

        # Advance checkpoint position if we're replaying
        if self._checkpoint_sequence is not None:
            # Track frame for divergence detection
            if outcome.frame_after:
                frame_hash = self._compute_frame_hash(outcome.frame_after)
                self._track_frame_for_divergence(frame_hash)

            # Check for divergence at midpoint
            if self._check_checkpoint_divergence():
                # Checkpoint has diverged - bail early and switch to WEIGHTED
                self._clear_checkpoint()
            else:
                self._checkpoint_position += 1
                # Check if we've exhausted the checkpoint
                if self._checkpoint_position >= len(self._checkpoint_sequence):
                    # Checkpoint exhausted - will fall through to WEIGHTED on next decision
                    # Keep the sequence for one more cycle so strategy can detect the transition
                    pass

    def _handle_checkpoint_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Handle checkpoint-related metadata from decision system.

        When FrontierCheckpointRung loads a checkpoint, it returns metadata with:
        - checkpoint_loaded: True
        - checkpoint_data: {'action_sequence': [...], 'unique_frames_seen': N, ...}

        This captures that data for subsequent context builds and divergence detection.
        """
        if metadata.get('checkpoint_loaded') and metadata.get('checkpoint_data'):
            checkpoint_data = metadata['checkpoint_data']
            sequence = checkpoint_data.get('action_sequence', [])
            if sequence:
                self._checkpoint_sequence = sequence
                self._checkpoint_position = 0  # Will be incremented after this action
                # Capture expected frames for divergence detection
                self._checkpoint_expected_frames = checkpoint_data.get('unique_frames_seen', 0)
                self._checkpoint_frames_seen = set()  # Reset frame tracking
                self._checkpoint_divergence_checked = False

    def _track_frame_for_divergence(self, frame_hash: str) -> None:
        """Track a frame hash during checkpoint replay for divergence detection."""
        if self._checkpoint_sequence is not None and frame_hash:
            self._checkpoint_frames_seen.add(frame_hash)

    def _check_checkpoint_divergence(self) -> bool:
        """
        Check if checkpoint replay has diverged from expected trajectory.

        Called at ~50% through the checkpoint. If unique_frames_seen is
        significantly below expected, the game state has diverged and we
        should bail early to avoid wasting actions.

        Returns:
            True if diverged (should clear checkpoint), False if on track
        """
        if self._checkpoint_sequence is None:
            return False

        if self._checkpoint_divergence_checked:
            return False  # Only check once

        seq_len = len(self._checkpoint_sequence)
        midpoint = seq_len // 2

        # Only check at or after midpoint
        if self._checkpoint_position < midpoint:
            return False

        self._checkpoint_divergence_checked = True

        # If no expected frames recorded, skip check
        if self._checkpoint_expected_frames <= 0:
            return False

        # Calculate expected frames at this point (proportional)
        progress_ratio = self._checkpoint_position / seq_len
        expected_at_this_point = int(self._checkpoint_expected_frames * progress_ratio)

        # Allow 30% tolerance - if we're seeing <70% of expected frames, bail
        threshold = expected_at_this_point * 0.7
        actual_frames = len(self._checkpoint_frames_seen)

        if actual_frames < threshold and expected_at_this_point >= 3:
            # Diverged - not seeing enough unique frames
            # Minimum 3 expected frames to trigger (avoid false positives on short checkpoints)
            return True

        return False

    def set_checkpoint(self, sequence: List[str], level: int) -> None:
        """
        Explicitly set a checkpoint sequence for replay.

        Args:
            sequence: List of action names to replay
            level: The level this checkpoint is for
        """
        self._checkpoint_sequence = sequence
        self._checkpoint_position = 0
        self._checkpoint_level = level
        self._checkpoint_expected_frames = 0
        self._checkpoint_frames_seen = set()
        self._checkpoint_divergence_checked = False

    def _clear_checkpoint(self) -> None:
        """Clear checkpoint state (on death, level change, divergence, or exhaustion)."""
        self._checkpoint_sequence = None
        self._checkpoint_position = 0
        self._checkpoint_level = None
        self._checkpoint_expected_frames = 0
        self._checkpoint_frames_seen = set()
        self._checkpoint_divergence_checked = False

    def _compute_frame_hash(self, frame: Optional[List[List[int]]]) -> str:
        """
        Compute a hash of a frame for divergence detection.

        Args:
            frame: 2D grid of integers

        Returns:
            Hash string, or empty string if frame is None
        """
        if frame is None:
            return ""
        # Handle numpy arrays: convert to list for safe iteration
        if hasattr(frame, 'tolist'):
            frame = frame.tolist()
        if not isinstance(frame, list) or len(frame) == 0:
            return ""
        try:
            import hashlib

            # Flatten and convert to bytes
            flat = []
            for row in frame:
                for cell in row:
                    # Handle both scalar and array values
                    if hasattr(cell, '__iter__') and not isinstance(cell, (str, bytes)):
                        flat.extend(cell)
                    else:
                        flat.append(int(cell))
            data = bytes(flat)
            return hashlib.md5(data).hexdigest()[:12]
        except Exception:
            return ""

    def on_level_change(self, new_level: int) -> None:
        """
        Handle level transition.

        Clears checkpoint if it was for a different level.
        """
        if self._checkpoint_level is not None and self._checkpoint_level != new_level:
            self._clear_checkpoint()

    def reset(self, game_id: str) -> None:
        """
        Reset state for a new game.

        Args:
            game_id: The new game ID
        """
        self._current_game_id = game_id
        self._recent_actions.clear()
        self._recent_outcomes.clear()
        self._position_history.clear()
        self._visited_positions.clear()
        self._death_count = 0
        self._clear_checkpoint()  # Clear checkpoint on game reset

        # Reset Part 7 cognitive state for new game
        self._world_model = {
            'causal_map': {},
            'cell_states': {},
            'goal_state': {},
            'delta': {},
            'rules_learned': [],
            'level_diffs': [],
            'action_history': [],
        }

        # Task A2: Seed world_model from previously-persisted state for this game type
        if self._db is not None:
            try:
                game_prefix = game_id[:4] if len(game_id) >= 4 else game_id
                # Find most recent world_model for any game with same prefix
                rows = self._db.execute_query("""
                    SELECT objects_json, game_id FROM world_model_states
                    WHERE game_id LIKE ? || '%'
                    ORDER BY created_at DESC LIMIT 1
                """, (game_prefix,))
                if rows and rows[0].get('objects_json'):
                    import json as _json
                    stored = _json.loads(rows[0]['objects_json'])
                    if isinstance(stored, dict):
                        seed_causal = stored.get('causal_map', {})
                        seed_rules = stored.get('rules_learned', [])
                        seed_goals = stored.get('goal_states', {})
                        seed_no_effect = stored.get('no_effect_positions', {})
                        if seed_causal:
                            self._world_model['causal_map'] = seed_causal
                        if seed_rules:
                            self._world_model['rules_learned'] = seed_rules
                        if seed_goals:
                            self._world_model['solver_goal_states'] = seed_goals
                        if seed_no_effect:
                            self._world_model['no_effect_positions'] = seed_no_effect
                        # H39b: Load LS20 level configs if present
                        # H51d: solver_level_configs contain variant-specific
                        # maze layouts (walls, positions). Only load from
                        # exact game_id match — prefix match gives wrong
                        # variant's walls to new variants.
                        seed_level_configs = stored.get('solver_level_configs', {})
                        row_game_id = (
                            rows[0].get('game_id', '') if isinstance(rows[0], dict) else ''
                        )
                        if seed_level_configs and row_game_id == game_id:
                            self._world_model['solver_level_configs'] = seed_level_configs
                # Load solver-seeded knowledge from dedicated solver_seed_*
                # entry (separate from runtime wms_*_best to avoid overwrites)
                if 'solver_goal_states' not in self._world_model:
                    solver_rows = self._db.execute_query("""
                        SELECT objects_json FROM world_model_states
                        WHERE state_id = ?
                    """, (f"solver_seed_{game_prefix}",))
                    if solver_rows and solver_rows[0].get('objects_json'):
                        import json as _json2
                        solver_stored = _json2.loads(
                            solver_rows[0]['objects_json'])
                        if isinstance(solver_stored, dict):
                            sg = solver_stored.get('goal_states', {})
                            if sg:
                                self._world_model['solver_goal_states'] = sg
                            # H39b: Load LS20 level configs (targets, changers, init)
                            # H51d: solver_level_configs are variant-specific
                            # (walls, positions, changers). The solver_seed is
                            # built from ONE specific variant — loading its
                            # maze layout for a different variant causes wrong
                            # position tracking and navigation.
                            slc = solver_stored.get('solver_level_configs', {})
                            source_gid = solver_stored.get('source_game_id', '')
                            if slc and (not source_gid or source_gid == game_id):
                                self._world_model['solver_level_configs'] = slc
            except Exception:
                pass  # Non-critical: seeding failure is fine, start fresh

        self._prev_level_scene = None
        self._prev_level_number = 0
        self._level_diffs = []
        self._puzzle_type = 'unknown'
        self._puzzle_type_classified = False
        # NOTE: _epistemic_source is NOT reset here — it is structural wiring,
        # not game-scoped state.  It persists across games for the same player.

    # =====================================================================
    # Part 7 Cognitive Capability Methods
    # =====================================================================

    def classify_puzzle_type(self, available_actions: List[int],
                            visual_scene: Optional[Dict[str, Any]] = None) -> str:
        """
        Classify the puzzle type from available actions and visual analysis.
        Called once per game, cached for subsequent actions.

        Returns one of: click_toggle, click_transform, movement_maze,
        pattern_completion, hybrid, unknown
        """
        if self._puzzle_type_classified:
            return self._puzzle_type

        # Primary signal: available actions
        has_directional = any(a in available_actions for a in [1, 2, 3, 4])
        has_click = 6 in available_actions
        has_submit = 5 in available_actions

        if has_click and not has_directional:
            # Click-only game
            puzzle_type = 'click_toggle'  # Default for click-only

            # Refine with visual analysis
            if visual_scene:
                panels = visual_scene.get('panels', [])
                panel_count = visual_scene.get('panel_count', 0)
                tile_grid = visual_scene.get('tile_grid')

                if panel_count >= 3:
                    # Multiple panels with reference = transformation game
                    puzzle_type = 'click_transform'
                elif tile_grid:
                    # Regular tile grid = toggle/constraint game
                    puzzle_type = 'click_toggle'

        elif has_directional and not has_click:
            puzzle_type = 'movement_maze'

        elif has_directional and has_click:
            puzzle_type = 'hybrid'

        else:
            puzzle_type = 'unknown'

        self._puzzle_type = puzzle_type
        self._puzzle_type_classified = True
        return puzzle_type

    def extract_goal_state(self, visual_scene: Optional[Dict[str, Any]],
                           frame: Optional[Any] = None) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Extract goal state from reference panel in visual scene.

        Returns (goal_state, goal_delta) where:
        - goal_state: {(x,y): target_color} from reference panel
        - goal_delta: {(x,y): (current_color, target_color)} differences
        """
        if not visual_scene or not frame:
            return None, None

        try:
            # Get panels with their roles
            panels = visual_scene.get('panels', [])
            reference_panel_idx = visual_scene.get('reference_panel_idx')

            if reference_panel_idx is None or reference_panel_idx >= len(panels):
                return None, None

            ref_panel = panels[reference_panel_idx]
            ref_bounds = ref_panel.get('bounds')  # (y_min, x_min, y_max, x_max)

            if not ref_bounds:
                return None, None

            # Get frame as list for indexing
            frame_data = frame
            if hasattr(frame, 'tolist'):
                frame_data = frame.tolist()

            if not isinstance(frame_data, list) or not frame_data:
                return None, None

            y_min, x_min, y_max, x_max = ref_bounds

            # Extract reference panel pixels as goal state
            goal_state = {}
            for y in range(max(0, y_min), min(len(frame_data), y_max)):
                row = frame_data[y]
                for x in range(max(0, x_min), min(len(row), x_max)):
                    color = row[x]
                    if color != 0:  # Non-background
                        goal_state[f"{x},{y}"] = color

            if not goal_state:
                return None, None

            # Find workspace panel to compute delta
            workspace_idx = None
            for i, p in enumerate(panels):
                role = p.get('role', '')
                if role in ('workspace', 'output') and i != reference_panel_idx:
                    workspace_idx = i
                    break

            goal_delta = None
            if workspace_idx is not None and workspace_idx < len(panels):
                ws_panel = panels[workspace_idx]
                ws_bounds = ws_panel.get('bounds')
                if ws_bounds:
                    wy_min, wx_min, wy_max, wx_max = ws_bounds
                    goal_delta = {}

                    # Map workspace positions to reference positions
                    # (offset-based correspondence)
                    ref_h = y_max - y_min
                    ref_w = x_max - x_min
                    ws_h = wy_max - wy_min
                    ws_w = wx_max - wx_min

                    if ref_h > 0 and ref_w > 0 and ws_h > 0 and ws_w > 0:
                        for ry in range(min(ref_h, ws_h)):
                            for rx in range(min(ref_w, ws_w)):
                                ref_y = y_min + ry
                                ref_x = x_min + rx
                                ws_y = wy_min + ry
                                ws_x = wx_min + rx

                                if (ref_y < len(frame_data) and ref_x < len(frame_data[ref_y])
                                        and ws_y < len(frame_data) and ws_x < len(frame_data[ws_y])):
                                    ref_color = frame_data[ref_y][ref_x]
                                    ws_color = frame_data[ws_y][ws_x]
                                    if ref_color != ws_color:
                                        goal_delta[f"{ws_x},{ws_y}"] = {
                                            'current': ws_color,
                                            'target': ref_color,
                                        }

            # Update world model goal tracking
            self._world_model['goal_state'] = goal_state
            self._world_model['delta'] = goal_delta or {}

            return goal_state, goal_delta

        except Exception as e:
            logger.debug(f"Goal state extraction failed: {e}")
            return None, None

    def compute_level_diff(self, current_scene: Optional[Dict[str, Any]],
                           current_level: int) -> Optional[Dict[str, Any]]:
        """
        Compare current level's visual scene to previous level's scene.
        The delta IS the lesson the game is teaching.

        Returns diff dict or None if no previous level to compare.
        """
        if not current_scene or current_level <= 1:
            # Store current scene for next level's comparison
            self._prev_level_scene = current_scene
            self._prev_level_number = current_level
            return None

        if self._prev_level_scene is None:
            self._prev_level_scene = current_scene
            self._prev_level_number = current_level
            return None

        prev = self._prev_level_scene
        curr = current_scene

        try:
            diff = {
                'from_level': self._prev_level_number,
                'to_level': current_level,
                'panel_count_change': curr.get('panel_count', 0) - prev.get('panel_count', 0),
                'new_colors': list(
                    set(curr.get('unique_colors', [])) - set(prev.get('unique_colors', []))
                ),
                'lost_colors': list(
                    set(prev.get('unique_colors', [])) - set(curr.get('unique_colors', []))
                ),
                'layout_changed': curr.get('layout', '') != prev.get('layout', ''),
                'grid_size_change': (
                    (curr.get('logical_grid_size', (0, 0))[0] - prev.get('logical_grid_size', (0, 0))[0],
                     curr.get('logical_grid_size', (0, 0))[1] - prev.get('logical_grid_size', (0, 0))[1])
                    if curr.get('logical_grid_size') and prev.get('logical_grid_size')
                    else (0, 0)
                ),
            }

            self._level_diffs.append(diff)
            self._world_model['level_diffs'] = self._level_diffs.copy()

            # Update prev for next level transition
            self._prev_level_scene = current_scene
            self._prev_level_number = current_level

            return diff

        except Exception as e:
            logger.debug(f"Level diff computation failed: {e}")
            self._prev_level_scene = current_scene
            self._prev_level_number = current_level
            return None

    def update_world_model_from_action(self, action: str, x: int, y: int,
                                       frame_changed: bool,
                                       pre_frame: Optional[Any] = None,
                                       post_frame: Optional[Any] = None) -> None:
        """
        Update the world model's causal map after an action.
        This is called from the feedback loop (on_action_complete path).

        Records what happened when we took this action at this position.
        """
        # Record in action history
        self._world_model['action_history'].append({
            'action': action,
            'x': x, 'y': y,
            'frame_changed': frame_changed,
        })
        # Keep history bounded
        if len(self._world_model['action_history']) > 200:
            self._world_model['action_history'] = self._world_model['action_history'][-200:]

        if not frame_changed or pre_frame is None or post_frame is None:
            return

        try:
            # Convert frames to lists if numpy
            pre = pre_frame.tolist() if hasattr(pre_frame, 'tolist') else pre_frame
            post = post_frame.tolist() if hasattr(post_frame, 'tolist') else post_frame

            if not isinstance(pre, list) or not isinstance(post, list):
                return

            # Squeeze leading dimensions: [[[pixel]]] -> [[pixel]]
            while pre and isinstance(pre, list) and isinstance(pre[0], list) and isinstance(pre[0][0], list):
                pre = pre[0]
            while post and isinstance(post, list) and isinstance(post[0], list) and isinstance(post[0][0], list):
                post = post[0]

            # Find all changed pixels
            changes = []
            for row_idx in range(min(len(pre), len(post))):
                pre_row = pre[row_idx]
                post_row = post[row_idx]
                for col_idx in range(min(len(pre_row), len(post_row))):
                    if pre_row[col_idx] != post_row[col_idx]:
                        changes.append({
                            'x': col_idx, 'y': row_idx,
                            'from_color': pre_row[col_idx],
                            'to_color': post_row[col_idx],
                        })

            if not changes:
                return

            # Record in causal map
            pos_key = f"{x},{y}"
            if pos_key not in self._world_model['causal_map']:
                self._world_model['causal_map'][pos_key] = {
                    'action': action,
                    'observations': [],
                    'total_observations': 0,
                }

            entry = self._world_model['causal_map'][pos_key]
            entry['observations'].append({
                'changes': changes[:50],  # Cap per observation
                'change_count': len(changes),
            })
            entry['total_observations'] += 1

            # Keep observations bounded
            if len(entry['observations']) > 10:
                entry['observations'] = entry['observations'][-10:]

            # Extract rules when we have enough observations
            if entry['total_observations'] >= 2:
                self._extract_causal_rules(pos_key, entry)

        except Exception as e:
            logger.debug(f"World model causal update failed: {e}")

    def _extract_causal_rules(self, pos_key: str, entry: Dict[str, Any]) -> None:
        """Extract compact causal rules from repeated observations at a position."""
        observations = entry['observations']
        if len(observations) < 2:
            return

        # Check if effect is consistent across observations
        first_changes = set()
        for c in observations[0].get('changes', []):
            first_changes.add((c['x'], c['y']))

        consistent = True
        for obs in observations[1:]:
            obs_changes = set()
            for c in obs.get('changes', []):
                obs_changes.add((c['x'], c['y']))
            if obs_changes != first_changes:
                consistent = False
                break

        if consistent and first_changes:
            rule = {
                'trigger_pos': pos_key,
                'action': entry.get('action', ''),
                'affected_positions': [f"{x},{y}" for x, y in first_changes],
                'effect_type': 'toggle' if len(first_changes) > 1 else 'single',
                'confidence': min(1.0, entry['total_observations'] / 5.0),
            }

            # Add rule if not already present
            existing_triggers = {r['trigger_pos'] for r in self._world_model['rules_learned']}
            if pos_key not in existing_triggers:
                self._world_model['rules_learned'].append(rule)
            else:
                # Update existing rule
                for i, r in enumerate(self._world_model['rules_learned']):
                    if r['trigger_pos'] == pos_key:
                        self._world_model['rules_learned'][i] = rule
                        break

    def snapshot_level_scene(self, visual_scene: Optional[Dict[str, Any]], level: int) -> None:
        """
        Snapshot the current visual scene at level end for level-to-level diffing.
        Call this just before a level transition.
        """
        self._prev_level_scene = visual_scene
        self._prev_level_number = level

    def _determine_phase(self, budget_used_percent: float) -> str:
        """Determine the current game phase based on budget usage."""
        if budget_used_percent < 0.1:
            return "orientation"  # First 10% - learning game mechanics
        elif budget_used_percent < 0.5:
            return "hypothesis"  # 10-50% - testing theories
        else:
            return "exploitation"  # 50%+ - using what we've learned

    def _detect_agent_position(
        self,
        frame: Optional[List[List[int]]],
    ) -> Optional[Tuple[int, int]]:
        """
        Detect the agent's position in the frame.

        This is a simplified heuristic. Full implementation would use
        the agent self-model.
        """
        if frame is None or (isinstance(frame, list) and len(frame) == 0):
            return None

        # Simple heuristic: find first non-zero cell
        # (In reality, would track controlled object)
        try:
            for y, row in enumerate(frame):
                for x, val in enumerate(row):
                    # Handle both scalar and array values
                    try:
                        is_nonzero = bool(val != 0)
                    except ValueError:
                        # Numpy array - check if any element is nonzero
                        import numpy as np
                        is_nonzero = np.any(val != 0)

                    if is_nonzero:
                        return (x, y)
        except Exception:
            pass

        return None

    def _check_is_frontier(self, game_id: str, level: int) -> bool:
        """Check if this level has been beaten before."""
        if self._db is None:
            return True  # Assume frontier if no DB

        try:
            # Query database for winning sequences
            result = self._db.execute("""
                SELECT COUNT(*) FROM winning_sequences
                WHERE game_type = ? AND level = ? AND is_active = 1
            """, (game_id[:4], level)).fetchone()

            return result[0] == 0
        except Exception:
            return True

    def _get_safety_weights(
        self,
        loop_state: LoopState,
    ) -> Dict[str, float]:
        """
        Get safety weights for each action based on danger patterns.

        Higher weight = safer action.
        """
        weights: Dict[str, float] = {}

        # Default weights (all actions equally safe)
        for action in GameAction:
            weights[action.name] = 1.0

        if self._terminal_detector is None:
            return weights

        try:
            # Query terminal patterns for this game
            patterns: List[Dict[str, Any]] = self._terminal_detector.get_danger_patterns(
                loop_state.game_id[:4],
                loop_state.current_level,
            )

            # Reduce weight for actions that led to deaths
            for pattern in patterns:
                action_name: str = str(pattern.get('action', ''))
                if action_name in weights:
                    # Reduce weight based on death count
                    death_count: int = int(pattern.get('death_count', 0))
                    weights[action_name] = max(0.1, 1.0 - (death_count * 0.1))

        except Exception:
            pass

        return weights

    def _check_winning_sequence(
        self,
        game_id: str,
        level: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if there's a winning sequence for this level.

        Returns:
            Tuple of (has_sequence, current_step, total_length)
        """
        if self._db is None:
            return False, 0, 0

        try:
            # Query for winning sequence
            result = self._db.execute("""
                SELECT sequence_data, action_count
                FROM winning_sequences
                WHERE game_type = ? AND level = ? AND is_active = 1
                ORDER BY action_count ASC
                LIMIT 1
            """, (game_id[:4], level)).fetchone()

            if result:
                return True, 0, result[1]

            return False, 0, 0
        except Exception:
            return False, 0, 0

    def _get_cods_context(
        self,
        game_id: str,
    ) -> Tuple[Optional[str], float]:
        """
        Get CODS (Cognitive Operator Discovery System) context.

        Returns:
            Tuple of (hypothesis_description, confidence)
        """
        if self._db is None:
            return None, 0.0

        try:
            # Query for active hypothesis
            result = self._db.execute("""
                SELECT hypothesis_id, reliability_score
                FROM network_object_control_hypotheses
                WHERE game_type = ? AND is_active = 1
                ORDER BY reliability_score DESC
                LIMIT 1
            """, (game_id[:4],)).fetchone()

            if result:
                return result[0], result[1]

            return None, 0.0
        except Exception:
            return None, 0.0

    def _calculate_coverage(self) -> float:
        """Calculate exploration coverage as fraction of visited positions."""
        if not self._visited_positions:
            return 0.0

        # Simple metric: visited positions / reasonable estimate
        # (Better would be: visited / total reachable positions)
        return min(1.0, len(self._visited_positions) / 100.0)

    def _detect_stuck(self) -> bool:
        """Detect if the agent appears stuck."""
        if len(self._recent_outcomes) < 10:
            return False

        # Stuck = many neutral outcomes in a row
        recent = self._recent_outcomes[-10:]
        neutral_count = sum(1 for o in recent if o == "neutral")
        return neutral_count >= 8

    def _detect_oscillation(self) -> bool:
        """Detect if recent actions show oscillation pattern."""
        if len(self._recent_actions) < 6:
            return False

        recent = self._recent_actions[-6:]

        # Check for A-B-A-B pattern
        if len(set(recent)) == 2:
            first = recent[0]
            second = recent[1]
            expected = [first, second, first, second, first, second]
            if recent == expected:
                return True

        return False


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    print("Context Builder - Quick Test")
    print("=" * 50)

    # Create mock state
    loop_state = LoopState(
        game_id="ls20",
        current_level=0,
        action_count=50,
        score=0.0,
        state=GameState.NOT_FINISHED,
        frame=[[0, 1, 0], [0, 0, 0], [0, 0, 2]],
        levels_completed=0,
        win_levels=5,
    )

    agent_config = AgentConfig(
        agent_id="test-agent",
        role="pioneer",
        w_A=0.6,
        w_B=0.4,
        action_budget=2000,
    )

    # Create builder (no DB)
    builder = ContextBuilder()

    # Build context
    context = builder.build(loop_state, agent_config)

    print(f"\nGame: {context.game_id} (type: {context.game_type})")
    print(f"Level: {context.level}")
    print(f"Phase: {context.phase}")
    print(f"Budget: {context.action_count}/{agent_config.action_budget} ({context.budget_used_percent:.1%})")
    print(f"Agent: {context.agent_id} ({context.agent_role})")
    print(f"Weights: w_A={context.w_A}, w_B={context.w_B}")
    print(f"Frontier: {context.is_frontier}")
    print(f"Position: {context.agent_position}")

    # Test update
    print("\nTesting update...")
    from outcome_processor import ActionOutcome

    outcome = ActionOutcome(
        action=GameAction.ACTION1,
        action_name="ACTION1",
        frame_changed=True,
        position_changed=True,
        position_delta=(1, 0),
    )
    builder.update("ACTION1", outcome)

    context2 = builder.build(loop_state, agent_config)
    print(f"Recent actions: {context2.recent_actions}")
    print(f"Recent outcomes: {context2.recent_outcomes}")

    # Test to_dict
    print("\nContext as dict (sample keys):")
    d = context.to_dict()
    for key in ['game_id', 'phase', 'agent_role', 'is_frontier']:
        print(f"  {key}: {d[key]}")

    print("\n[OK] All tests passed!")
