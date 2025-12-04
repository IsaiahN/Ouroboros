# Core Gameplay Refactoring Plan

**Date**: December 4, 2025  
**Current State**: 5,942 lines, 73 methods in one file  
**Goal**: Clean, modular, readable code following Python best practices

---

## Phase 0: Pre-Refactoring Fixes (MUST DO FIRST)

Before any refactoring, implement these BLOCKING missing features:

### 0.1 Full Game Sequence Storage (Priority: CRITICAL)
**Status**: Table `winning_sequences_full_game` exists but NO code writes to it  
**Location**: `core_gameplay.py` line ~3235 (`_capture_winning_sequence`)  
**Fix**: Add detection for full game wins and INSERT to protected table  
**Effort**: ~50 lines  

### 0.2 Optimizer End Subsequence (Priority: CRITICAL)
**Status**: NOT IMPLEMENTED  
**Problem**: Optimizers reset levels mid-play, saving sequences that DON'T include final win actions  
**Fix**: When optimizer saves sequence, auto-append proven ending from existing wins  
**Effort**: ~30 lines  

### 0.3 Agent Revival Integration (Priority: HIGH)
**Status**: `revive_agents.py` (386 lines) is ORPHANED - never called  
**Fix**: Add to `autonomous_evolution_runner.py` evolution loop  
**Effort**: ~20 lines  

---

## Codebase Audit Summary

### Files That ARE Being Used (Actively Imported)

| File | Used By | Status |
|------|---------|--------|
| `multi_stage_matching_pipeline.py` | `core_gameplay.py` | Active - 5-stage sequence fallback |
| `agent_self_model.py` | `core_gameplay.py` | Active - "I am this object" tracking |
| `sequence_abstraction.py` | `core_gameplay.py` | Active - concept-based matching |
| `subgoal_planner.py` | `core_gameplay.py`, `autonomous_evolution_runner.py` | Active - hierarchical planning |
| `subgoal_planning_activator.py` | `core_gameplay.py` | Active - subgoal integration |
| `enhanced_database_interface.py` | `autonomous_evolution_runner.py` | Active - schema auto-maintenance |
| `frustration_detector.py` | `autonomous_evolution_runner.py` | Active - quorum sensing |
| `breakthrough_detector.py` | `core_gameplay.py` | Active - momentum detection |
| `breakthrough_budget_allocator.py` | `core_gameplay.py`, `autonomous_evolution_runner.py` | Active - dynamic budgets |
| `near_miss_analyzer.py` | `autonomous_evolution_runner.py` | Active - learn from 15-18/20 scores |
| `counterfactual_analyzer.py` | `autonomous_evolution_runner.py` | Active - "what if?" analysis |
| `safe_cleanup.py` | `autonomous_evolution_runner.py` | Active - runs every 10 generations |

### Orphaned Files - DECISIONS

| File | Lines | Decision | Rationale |
|------|-------|----------|-----------|
| `revive_agents.py` | 386 | **INTEGRATE** | Valuable, complete implementation - just needs connection to evolution loop |
| `emotional_gameplay_mixin.py` | 100 | **DELETE** | SomaticProfileSystem exists but mixin pattern adds complexity without benefit |
| `symbolic_reasoning_engine.py` | 1,451 | **FUTURE** | Mark as experimental/future feature in code; don't integrate now |
| `visual_reasoning_engine.py` | 700 | **FUTURE** | Mark as experimental/future feature in code; don't integrate now |
| `specialist_coordinator.py` | 236 | **DELETE** | Unclear purpose, overlaps with agent_operating_mode_system |

### Manual Tools (Moved to `manual_tools/` folder)
Files not needing integration - standalone developer utilities:
- `list_sequences.py`, `list_tables.py`, `check_db.py`, `inspect_db.py`, `dump_logs.py`
- `review_*.py` (4 files), `get_replay_url.py`, `run_validation_cycle.py`
- `emergency_*.py`, `rebuild_*.py`, `monitor_*.py`

### Missing Features (Per Master Ruleset)

| Feature | Status | Priority | Effort |
|---------|--------|----------|--------|
| `winning_sequences_full_game` usage | Table exists, NOT USED | CRITICAL | 50 lines |
| End subsequence for optimizers | NOT IMPLEMENTED | CRITICAL | 30 lines |
| Agent revival integration | Orphaned but complete | HIGH | 20 lines |
| Exploiter 50/50 split | Partial (column exists) | MEDIUM | 15 lines |
| Automated sequence validation | Manual only | MEDIUM | 30 lines |
| Email notifications | NOT IMPLEMENTED | LOW | Optional |

---

## Executive Summary

`core_gameplay.py` has grown organically into a 6,000-line monolith with 73 methods handling:
- Game session management
- Sequence retrieval and storage
- Action selection and execution
- Pattern learning and meta-learning
- Viral evolution (packages and pariahs)
- Agent self-model tracking
- Frame analysis and comparison

This plan breaks it into **focused modules** with clear responsibilities.

---

## Proposed Architecture

```
core_gameplay/
├── __init__.py                    # Public API exports
├── engine.py                      # GameplayEngine (orchestrator, ~200 lines)
├── game_loop.py                   # Game loop logic (~400 lines)
├── sequence_manager.py            # Sequence CRUD operations (~500 lines)
├── sequence_replay.py             # Sequence replay logic (~400 lines)
├── action_selection.py            # Action selection strategies (~400 lines)
├── pattern_learning.py            # Pattern detection and storage (~500 lines)
├── frame_analysis.py              # Frame comparison and analysis (~300 lines)
├── agent_tracking.py              # Agent performance and self-model (~200 lines)
├── viral_evolution.py             # Viral packages and pariahs (~150 lines)
└── types.py                       # Dataclasses and type definitions (~100 lines)
```

**Total: ~3,250 lines** (45% reduction through deduplication and cleanup)

---

## Module Breakdown

### 1. `types.py` - Type Definitions (~100 lines)

**Purpose**: Central location for all dataclasses and type aliases.

```python
"""
Type definitions for the core gameplay system.

This module contains all dataclasses, enums, and type aliases used
throughout the gameplay engine. Centralizing types here:
1. Prevents circular imports
2. Makes the type system self-documenting
3. Enables easy IDE navigation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Tuple

class AgentMode(Enum):
    """Operating modes that define how an agent plays games."""
    PIONEER = auto()      # Explores frontier (unbeaten levels)
    OPTIMIZER = auto()    # Improves existing solutions
    GENERALIST = auto()   # Balanced play with sensation
    EXPLOITER = auto()    # Replays proven sequences only

class GameResult(Enum):
    """Possible outcomes of a game session."""
    WIN = "WIN"
    GAME_OVER = "GAME_OVER"
    NOT_FINISHED = "NOT_FINISHED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    NO_SEQUENCE_AVAILABLE = "NO_SEQUENCE_AVAILABLE"
    ERROR = "ERROR"

@dataclass
class GameLoopState:
    """Mutable state tracked during the game loop."""
    action_count: int = 0
    level_action_count: int = 0
    previous_score: float = 0.0
    level_completions: int = 0
    current_level: int = 1
    # ... rest of fields

@dataclass
class SequenceFallbackResult:
    """Result from the 3-try sequence fallback system."""
    success: bool = False
    game_state: Any = None
    successful_sequence: Optional[Dict] = None
    all_failed: bool = False
    # ... rest of fields

@dataclass
class SequenceInfo:
    """Information about a stored winning sequence."""
    sequence_id: str
    game_id: str
    level_number: int
    total_actions: int
    total_score: float
    action_sequence: List[int]
    initial_frame: Optional[List] = None
    success_rate: float = 0.0
    times_referenced: int = 0

@dataclass
class ActionResult:
    """Result of executing an action."""
    success: bool
    game_state: Any
    action_taken: Optional[str] = None
    error: Optional[str] = None

@dataclass
class GameResults:
    """Final results after completing a game."""
    game_id: str
    final_state: str
    final_score: float
    actions_taken: int
    win: bool
    level_completions: int
    levels_attempted: int
    duration_seconds: float
    method: str = "exploration"
    sequence_id: Optional[str] = None
    # ... additional fields
```

---

### 2. `sequence_manager.py` - Sequence CRUD (~500 lines)

**Purpose**: All database operations for sequences.

**Current Methods to Move**:
- `_capture_winning_sequence` (334 lines)
- `_get_best_cumulative_sequence` (66 lines)
- `_get_ranked_cumulative_sequences` (54 lines)
- `_get_best_sequence_for_game` (163 lines)
- `_flag_sequence_failure` (38 lines)
- `_record_sequence_validation` (136 lines)
- `_update_sequence_reputation` (96 lines)
- `_explore_sequence_recombination` (52 lines)

**Structure**:

```python
"""
Sequence Manager - CRUD operations for winning sequences.

This module handles all database operations related to sequences:
- Storing new sequences when levels are completed
- Retrieving sequences ranked by various criteria
- Updating sequence reputation based on replay success/failure
- Flagging and deactivating problematic sequences

Sequences are the core "memory" of the Ouroboros system - they store
proven solutions that can be replayed to reach known game states.
"""

class SequenceManager:
    """Manages winning sequence storage and retrieval."""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
    
    # =========================================================================
    # SEQUENCE RETRIEVAL
    # =========================================================================
    
    def get_best_sequence(self, game_id: str, level: int = 1) -> Optional[SequenceInfo]:
        """
        Get the single best sequence for a game/level combination.
        
        Selection criteria (in priority order):
        1. Highest success rate when reused (proven reliability)
        2. Most times referenced (battle-tested)
        3. Fewest actions (efficiency)
        
        Args:
            game_id: Full game ID (e.g., "ft09-b8377d4b7815")
            level: Target level number (default 1)
            
        Returns:
            SequenceInfo if found, None otherwise
        """
        # English explanation of the query:
        # - Find all ACTIVE sequences for this game type (prefix match)
        # - That reach at least the requested level (total_score >= level)
        # - Order by proven success, then usage, then efficiency
        # - Return the top one
        
    def get_ranked_sequences(
        self, 
        game_id: str, 
        limit: int = 3
    ) -> List[SequenceInfo]:
        """
        Get multiple sequences ranked by priority for the 3-try system.
        
        Returns up to `limit` sequences, enabling fallback if the first fails.
        
        Ranking criteria:
        1. Exact game_id match (same version)
        2. Game type match (same game, different version)
        3. Optimization sequences (marked for improvement)
        4. Any related sequence
        """
    
    def get_sequences_for_level(
        self, 
        game_id: str, 
        level: int
    ) -> List[SequenceInfo]:
        """Get all active sequences that complete a specific level."""
    
    # =========================================================================
    # SEQUENCE STORAGE
    # =========================================================================
    
    def capture_sequence(
        self,
        game_id: str,
        score: float,
        level_number: int,
        actions: List[int],
        initial_frame: Optional[List],
        action_coordinates: List[Tuple[int, int]],
        agent_id: Optional[str] = None,
        reason: str = "level_win"
    ) -> Optional[str]:
        """
        Store a new winning sequence in the database.
        
        This is called when an agent successfully completes a level.
        The sequence captures everything needed to replay that success:
        - The exact action sequence (ACTION1, ACTION2, etc.)
        - The coordinates for ACTION6 calls
        - The initial frame state for matching
        
        Duplicate Prevention:
        - Checks if an identical sequence already exists
        - Only stores if this is a new solution or improvement
        
        Diversity Bonus:
        - Allows storing if game type has < 10 active sequences
        - Ensures we don't over-specialize on one game
        
        Returns:
            sequence_id if stored, None if duplicate or invalid
        """
    
    def deactivate_sequence(self, sequence_id: str, reason: str) -> bool:
        """Mark a sequence as inactive with a reason."""
    
    def reactivate_sequence(self, sequence_id: str) -> bool:
        """Reactivate a previously deactivated sequence."""
    
    # =========================================================================
    # SEQUENCE REPUTATION
    # =========================================================================
    
    def record_validation_attempt(
        self,
        sequence_id: str,
        success: bool,
        reached_level: int,
        expected_level: int,
        failure_reason: Optional[str] = None
    ) -> None:
        """
        Record a sequence validation attempt (replay success/failure).
        
        This feeds into the Bayesian reputation system:
        - Successful replays increase trust
        - Failed replays decrease trust
        - Sequences with < 30% success rate get flagged
        """
    
    def flag_failure(self, sequence_id: str, reason: str) -> None:
        """
        Flag a sequence as failing and potentially deactivate it.
        
        After 3 consecutive failures, the sequence is deactivated.
        This prevents wasting actions on broken sequences.
        """
    
    def get_sequence_reputation(self, sequence_id: str) -> Dict[str, Any]:
        """Get reputation stats for a sequence."""
    
    # =========================================================================
    # SEQUENCE RECOMBINATION
    # =========================================================================
    
    def attempt_recombination(
        self,
        agent_id: str,
        game_id: str,
        current_level: int
    ) -> List[str]:
        """
        Attempt to create new sequences by combining existing ones.
        
        This is the "horizontal gene transfer" mechanism - agents can
        combine successful patterns from different sequences to create
        novel solutions.
        """
```

---

### 3. `sequence_replay.py` - Replay Logic (~400 lines)

**Purpose**: All logic for replaying sequences.

**Current Methods to Move**:
- `_replay_sequence_inline` (280 lines)
- `_try_replay_sequence` (130 lines)
- `_handle_3_try_fallback` (184 lines) - already extracted
- `_handle_sequence_replay_result` (92 lines) - already extracted
- `_find_partial_sequence_match` (93 lines)

**Structure**:

```python
"""
Sequence Replay - Logic for replaying stored sequences.

This module handles the actual replay of sequences:
- The 3-try fallback system (try multiple sequences before exploring)
- Inline replay execution (send stored actions to API)
- Partial sequence matching (resume from checkpoints)
- Frame validation (ensure current frame matches expected)

The replay system is critical for knowledge transfer - it allows
agents to instantly reach known game states instead of re-exploring.
"""

class SequenceReplayer:
    """Handles replaying stored sequences."""
    
    def __init__(
        self, 
        session_manager: GameSessionManager,
        sequence_manager: SequenceManager,
        db: DatabaseInterface
    ):
        self.session_manager = session_manager
        self.sequence_manager = sequence_manager
        self.db = db
    
    async def execute_3_try_fallback(
        self,
        game_state: GameState,
        ranked_sequences: List[SequenceInfo],
        game_id: str,
        agent_mode: Optional[AgentMode]
    ) -> SequenceFallbackResult:
        """
        Try up to 3 sequences in priority order.
        
        This is the primary sequence replay entry point. It implements:
        
        1. TRY SEQUENCE #1
           - If success: return immediately
           - If failure: flag sequence, reset game, try #2
           
        2. TRY SEQUENCE #2  
           - If success: return immediately
           - If failure: flag sequence, reset game, try #3
           
        3. TRY SEQUENCE #3
           - If success: return immediately
           - If failure: try multi-stage matching pipeline
           
        4. MULTI-STAGE PIPELINE
           - Try prefix/suffix/subsequence/conceptual matching
           - If found: return match for guided exploration
           
        5. ABSTRACTION HINTS
           - If no match: get conceptual hints for exploration
           
        Why full game reset between tries?
        - Different sequences may target different levels
        - Sequence A might reach level 3, Sequence B might only reach level 2
        - We need a fresh start (level 1) for each attempt
        """
    
    async def replay_sequence(
        self,
        game_state: GameState,
        sequence: SequenceInfo,
        start_index: int = 0
    ) -> Dict[str, Any]:
        """
        Replay a sequence starting from a given index.
        
        This sends each action from the sequence to the API in order.
        
        Frame Validation:
        - Before starting, verify current frame matches sequence's initial_frame
        - This prevents replaying sequences that don't apply to current state
        
        Error Handling:
        - If an action fails, mark position and return partial result
        - If frame corruption detected, abort immediately
        
        Returns:
            {
                'success': bool,
                'game_state': GameState,
                'actions_completed': int,
                'failure_reason': Optional[str]
            }
        """
    
    def find_partial_match(
        self,
        game_id: str,
        current_frame: List,
        current_level: int
    ) -> Optional[Dict]:
        """
        Find a sequence where we can resume from a checkpoint.
        
        If the current frame matches a mid-point in a stored sequence,
        we can skip the beginning and resume from that point.
        
        This enables efficient "checkpointing" - if we reach a known
        state, we don't need to replay the whole sequence.
        """
    
    def validate_frame_match(
        self,
        current_frame: List,
        expected_frame: List,
        tolerance: float = 0.95
    ) -> bool:
        """
        Check if current frame matches expected frame.
        
        Uses similarity scoring rather than exact match because:
        - Some games have minor visual variations
        - Animation frames may differ slightly
        - We want robustness over strict matching
        """
```

---

### 4. `action_selection.py` - Action Selection (~400 lines)

**Purpose**: All action selection logic.

**Current Methods to Move**:
- `_select_action` (346 lines)
- `_get_network_action_wisdom` (136 lines)
- `_analyze_sensation_context` (64 lines)
- `_convert_game_state_for_sensation_analysis` (20 lines)
- `_calculate_recent_success_rate_from_game_state` (20 lines)
- `_get_emotion_label` (12 lines)
- `_learn_from_action_outcome` (54 lines)

**Structure**:

```python
"""
Action Selection - Choosing the next action to take.

This module implements the action selection strategy:
1. Hierarchical subgoal planning (multi-step strategy)
2. Sensation-based navigation (emotional intelligence)
3. Viral package influence (prefer successful patterns)
4. Pariah avoidance (avoid known failures)
5. Network wisdom (learn from other agents)
6. Default exploration strategy

The selection process balances exploitation (use known good actions)
with exploration (try new things to discover better solutions).
"""

class ActionSelector:
    """Selects actions based on multiple strategy layers."""
    
    def __init__(
        self,
        action_handler: ActionHandler,
        sensation_engine: SensationEngine,
        db: DatabaseInterface
    ):
        self.action_handler = action_handler
        self.sensation_engine = sensation_engine
        self.db = db
        self.subgoal_planner = None  # Injected if available
    
    async def select_action(
        self,
        game_state: GameState,
        agent_id: Optional[str] = None,
        agent_mode: Optional[AgentMode] = None
    ) -> Tuple[str, str]:
        """
        Select the next action with reasoning.
        
        Selection Hierarchy:
        
        1. SUBGOAL PLANNING (if active plan exists)
           - Check if we have a multi-step plan in progress
           - If yes, return next action from plan
           
        2. SENSATION NAVIGATION (if enabled)
           - Analyze emotional context (frustration, curiosity, etc.)
           - Weight actions based on past emotional outcomes
           
        3. VIRAL PACKAGE INFLUENCE
           - Check if any viral packages apply to current state
           - Prefer actions from successful patterns
           
        4. PARIAH AVOIDANCE
           - Check if any pariahs apply to current state
           - Avoid actions that led to failures
           
        5. NETWORK WISDOM
           - Query what actions worked for other agents in similar states
           - Weight by prestige of contributing agents
           
        6. DEFAULT STRATEGY
           - Use action handler's built-in heuristics
           - Random exploration if nothing else applies
        
        Returns:
            Tuple of (action_string, reasoning_string)
        """
    
    def get_network_wisdom(
        self,
        game_state: GameState,
        available_actions: List[int]
    ) -> Dict[str, float]:
        """
        Get action recommendations from network knowledge.
        
        This queries the collective intelligence:
        - What actions worked for other agents at similar scores?
        - What's the success rate for each action type?
        - Which actions led to score improvements?
        
        Returns weights for each available action.
        """
    
    def learn_from_outcome(
        self,
        action: str,
        previous_score: float,
        new_state: GameState,
        agent_id: str
    ) -> None:
        """
        Learn from the outcome of an action.
        
        This feeds the sensation/emotional learning system:
        - If score improved: positive reinforcement
        - If score decreased: negative reinforcement
        - If stuck: frustration signal
        """
```

---

### 5. `game_loop.py` - Main Game Loop (~400 lines)

**Purpose**: The core game loop logic, extracted from `play_single_game`.

**Structure**:

```python
"""
Game Loop - The main loop for playing a single game.

This module contains the core game loop that:
1. Executes actions until budget exhausted or game won
2. Handles level completion detection
3. Manages API errors and retries
4. Detects stuck states at the frontier
5. Triggers sequence capture on level completion

The loop is intentionally simple - all complex logic is delegated
to specialized modules (action selection, sequence replay, etc.).
"""

class GameLoop:
    """Executes the main game loop."""
    
    def __init__(
        self,
        session_manager: GameSessionManager,
        action_selector: ActionSelector,
        sequence_manager: SequenceManager,
        db: DatabaseInterface
    ):
        self.session_manager = session_manager
        self.action_selector = action_selector
        self.sequence_manager = sequence_manager
        self.db = db
    
    async def run(
        self,
        game_state: GameState,
        game_id: str,
        agent_id: Optional[str],
        agent_mode: Optional[AgentMode],
        config: Dict[str, Any],
        action_callback: Optional[Callable] = None
    ) -> GameLoopState:
        """
        Run the game loop until completion.
        
        Loop Structure:
        
        WHILE actions_remaining AND session_active:
            
            1. CHECK SHUTDOWN
               - If shutdown requested, exit gracefully
               
            2. SYNC LEVEL STATE
               - Update current_level based on score
               - Reset level counters if level changed
               
            3. EXECUTE ACTION
               - Select action (via callback or action_selector)
               - Send to API
               - Handle API errors with exponential backoff
               
            4. CHECK LEVEL COMPLETION
               - If score increased by >= 1.0, level completed
               - Capture sequence
               - Update counters
               
            5. CHECK STUCK STATE (frontier only)
               - If 100 actions with no progress, abort
               
            6. CHECK LEVEL BUDGET
               - If max actions for level, move to next level
        
        Returns:
            GameLoopState with final counters
        """
    
    async def execute_single_action(
        self,
        game_state: GameState,
        loop_state: GameLoopState,
        action_callback: Optional[Callable],
        agent_id: Optional[str],
        game_id: str
    ) -> Tuple[GameState, bool, Optional[str]]:
        """
        Execute a single action and handle errors.
        
        Error Handling:
        - API errors: exponential backoff and retry
        - Session dead (400): abort immediately
        - Too many errors: abort game
        
        Returns:
            (new_game_state, action_succeeded, action_taken)
        """
    
    def handle_level_completion(
        self,
        game_state: GameState,
        loop_state: GameLoopState,
        game_id: str,
        agent_id: Optional[str]
    ) -> None:
        """
        Handle level completion side effects.
        
        - Capture winning sequence
        - Update agent self-model
        - Reset level counters
        - Log completion stats
        """
    
    def is_stuck_at_frontier(
        self,
        game_state: GameState,
        loop_state: GameLoopState,
        agent_mode: AgentMode,
        game_id: str
    ) -> bool:
        """
        Detect if pioneer is stuck at frontier with no progress.
        
        Only applies to:
        - Pioneer agents
        - At frontier levels (no known sequences)
        - After 100 actions with no frame change and no score increase
        """
```

---

### 6. `frame_analysis.py` - Frame Analysis (~300 lines)

**Purpose**: All frame comparison and analysis logic.

**Current Methods to Move**:
- `_calculate_frame_similarity` (45 lines)
- `_compare_frames` (76 lines)
- `_detect_frame_pattern` (94 lines)
- `_extract_frame_transitions` (31 lines)

**Structure**:

```python
"""
Frame Analysis - Comparing and analyzing game frames.

This module handles visual analysis of game frames:
- Similarity scoring between frames
- Pattern detection within frames
- Transition extraction between frames

Frames are 64x64 grids of color values (0-15). Understanding
frame changes is critical for:
- Validating sequence replays (frame matches expected?)
- Detecting stuck states (frame not changing?)
- Pattern learning (what visual patterns lead to success?)
"""

class FrameAnalyzer:
    """Analyzes game frames for patterns and similarities."""
    
    def calculate_similarity(
        self,
        frame_a: List[List[int]],
        frame_b: List[List[int]]
    ) -> float:
        """
        Calculate similarity score between two frames.
        
        Uses pixel-by-pixel comparison with normalization.
        
        Returns:
            Similarity score from 0.0 (completely different) to 1.0 (identical)
        """
    
    def frames_match(
        self,
        frame_a: List[List[int]],
        frame_b: List[List[int]],
        tolerance: float = 0.95
    ) -> bool:
        """Check if frames match within tolerance."""
    
    def detect_changes(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Detect what changed between two frames.
        
        Returns:
            {
                'pixels_changed': int,
                'regions_changed': List[Tuple[x, y, w, h]],
                'colors_added': List[int],
                'colors_removed': List[int]
            }
        """
    
    def extract_pattern(
        self,
        frame: List[List[int]]
    ) -> Dict[str, Any]:
        """
        Extract visual patterns from a frame.
        
        Looks for:
        - Symmetry (horizontal, vertical, rotational)
        - Color clustering
        - Geometric shapes
        - Grid structures
        """
```

---

### 7. `pattern_learning.py` - Pattern Detection (~500 lines)

**Purpose**: All meta-learning and pattern detection.

**Current Methods to Move**:
- `_detect_and_store_abstract_pattern` (78 lines)
- `_find_similar_patterns` (65 lines)
- `_meta_learn_pattern_from_frame` (64 lines)
- `_meta_detect_anomalies` (34 lines)
- `_meta_analyze_spatial_significance` (31 lines)
- All other `_meta_*` methods (~400 lines total)
- `_store_discovered_pattern` (61 lines)
- `_detect_pattern_tags` (25 lines)
- `_classify_game_type` (10 lines)

**Structure**:

```python
"""
Pattern Learning - Meta-learning and pattern detection.

This module handles higher-level pattern recognition:
- Detecting abstract patterns that generalize across games
- Finding similar patterns between different game types
- Learning transformation rules
- Building the pattern vocabulary

The goal is to develop transferable knowledge - patterns learned
in one game can potentially apply to others.
"""

class PatternLearner:
    """Learns and stores abstract patterns."""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
    
    def learn_from_frame(
        self,
        frame: List[List[int]],
        action_taken: str,
        result: str
    ) -> Optional[str]:
        """
        Learn a pattern from a frame-action-result triplet.
        
        This is the core meta-learning loop:
        1. Analyze the frame for salient features
        2. Associate features with the action taken
        3. Record whether the action led to success
        4. Build up statistical patterns over time
        """
    
    def detect_abstract_pattern(
        self,
        frames: List[List[List[int]]],
        actions: List[str],
        scores: List[float]
    ) -> Optional[Dict]:
        """
        Detect abstract patterns across a sequence of frames.
        
        Looks for:
        - Repeated visual motifs
        - Action-effect correlations
        - Score-change triggers
        """
    
    def find_similar_patterns(
        self,
        pattern: Dict
    ) -> List[Dict]:
        """Find stored patterns similar to the given pattern."""
    
    def store_pattern(
        self,
        pattern: Dict,
        game_id: str,
        confidence: float
    ) -> str:
        """Store a discovered pattern in the database."""
```

---

### 8. `agent_tracking.py` - Agent Tracking (~200 lines)

**Purpose**: Agent performance and self-model tracking.

**Current Methods to Move**:
- `_track_agent_performance` (99 lines)
- `_get_agent_self_awareness` (87 lines)
- `_apply_self_awareness_to_strategy` (35 lines)
- `_get_agent_operating_mode` (28 lines)

**Structure**:

```python
"""
Agent Tracking - Performance and self-model tracking.

This module tracks agent performance over time:
- Win/loss records
- Action efficiency
- Level progression
- Self-awareness development

The self-model helps agents understand their own capabilities
and adjust their strategies accordingly.
"""

class AgentTracker:
    """Tracks agent performance and self-awareness."""
    
    def __init__(self, db: DatabaseInterface, agent_self_model: AgentSelfModel):
        self.db = db
        self.self_model = agent_self_model
    
    def record_game_result(
        self,
        agent_id: str,
        game_id: str,
        final_score: float,
        actions_taken: int,
        level_completions: int,
        win: bool,
        duration: float
    ) -> None:
        """Record the results of a completed game."""
    
    def get_operating_mode(self, agent_id: str) -> AgentMode:
        """Get the current operating mode for an agent."""
    
    def get_self_awareness(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent's self-awareness profile.
        
        Returns understanding of:
        - Strengths (which games/actions work well)
        - Weaknesses (where agent struggles)
        - Controlled objects (self-model)
        """
```

---

### 9. `viral_evolution.py` - Viral Evolution (~150 lines)

**Purpose**: Viral packages and pariahs.

**Current Methods to Move**:
- `_handle_viral_evolution` (74 lines) - already extracted
- `_analyze_pariah_worthiness` (90 lines)

**Structure**:

```python
"""
Viral Evolution - Viral packages and pariah tracking.

This module implements the bidirectional evolution mechanism:
- Viral Packages: Successful patterns that spread between agents
- Pariahs: Failure patterns that agents learn to avoid

This is the "horizontal gene transfer" of the Ouroboros system -
knowledge spreads laterally between agents, not just through
parent-child inheritance.
"""

class ViralEvolutionHandler:
    """Handles viral packages and pariah creation/spreading."""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.viral_engine = ViralPackageEngine(db)
    
    async def process_game_result(
        self,
        results: Dict[str, Any],
        game_state: GameState,
        game_id: str,
        agent_id: str,
        generation: int
    ) -> None:
        """
        Process game result for viral evolution.
        
        If WIN: Create viral package from winning sequence
        If LOSS (score < 1): Create pariah from failure pattern
        
        Then spread to nearby agents (horizontal transfer).
        """
    
    def analyze_pariah_worthiness(
        self,
        sequence: SequenceInfo,
        game_id: str
    ) -> Dict[str, Any]:
        """
        Analyze if a sequence is worth challenging as a pariah.
        
        Returns whether the sequence should be attempted despite
        being marked as problematic.
        """
```

---

### 10. `engine.py` - GameplayEngine Orchestrator (~200 lines)

**Purpose**: The main orchestrator that ties everything together.

**Structure**:

```python
"""
Gameplay Engine - Main orchestrator for playing ARC games.

This is the primary entry point for the gameplay system. It:
1. Initializes all sub-components
2. Provides the public API (play_single_game, play_multiple_games, etc.)
3. Orchestrates the flow between components

The engine is intentionally thin - it delegates all complex logic
to specialized modules, making the code easy to understand and modify.
"""

class GameplayEngine:
    """Core engine for playing ARC games with integrated pattern learning."""

    def __init__(self, api_key: Optional[str] = None, db_path: str = "core_data.db"):
        """Initialize all components."""
        # Database
        self.db = DatabaseInterface(db_path)
        
        # Session management
        self.session_manager = GameSessionManager(api_key, db_path)
        
        # Component initialization
        self.sequence_manager = SequenceManager(self.db)
        self.sequence_replayer = SequenceReplayer(
            self.session_manager, self.sequence_manager, self.db
        )
        self.action_handler = ActionHandler(self.session_manager)
        self.action_selector = ActionSelector(
            self.action_handler, SensationEngine(self.db), self.db
        )
        self.game_loop = GameLoop(
            self.session_manager, self.action_selector, 
            self.sequence_manager, self.db
        )
        self.agent_tracker = AgentTracker(self.db, AgentSelfModel(db_path))
        self.pattern_learner = PatternLearner(self.db)
        self.viral_handler = ViralEvolutionHandler(self.db)
        self.frame_analyzer = FrameAnalyzer()
        
        # Configuration
        self.config = DEFAULT_CONFIG.copy()

    def configure(self, **config) -> None:
        """Update configuration."""
        self.config.update(config)

    async def play_single_game(
        self,
        game_id: str,
        action_callback: Optional[Callable] = None,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Play a single game to completion.
        
        Flow:
        1. Check agent budget (if agent_id provided)
        2. Start session and create game
        3. Try sequence replay (3-try fallback system)
        4. If replay fails or incomplete, run game loop
        5. Finalize and return results
        """
        # Pre-flight checks
        if agent_id and not self._check_agent_budget(agent_id, game_id):
            return self._budget_exhausted_result(game_id)
        
        # Initialize game
        game_state = await self._initialize_game(game_id, agent_id)
        agent_mode = self._get_agent_mode(agent_id)
        
        # Try sequence replay first
        sequences = self.sequence_manager.get_ranked_sequences(game_id)
        if sequences:
            fallback_result = await self.sequence_replayer.execute_3_try_fallback(
                game_state, sequences, game_id, agent_mode
            )
            
            # Check if we can return early
            early_result = await self._handle_replay_result(
                fallback_result, game_id, agent_id, agent_mode
            )
            if early_result:
                return early_result
            
            game_state = fallback_result.game_state
        
        # Run game loop
        loop_state = await self.game_loop.run(
            game_state, game_id, agent_id, agent_mode, 
            self.config, action_callback
        )
        
        # Finalize
        return await self._finalize_game(
            game_state, loop_state, game_id, agent_id
        )

    async def play_multiple_games(
        self,
        game_ids: List[str],
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Play multiple games in sequence."""
        results = []
        for game_id in game_ids:
            result = await self.play_single_game(game_id, agent_id=agent_id)
            results.append(result)
        return results

    # ... other public methods
```

---

## Implementation Order

### Phase 1: Types and Foundation (Day 1)
1. Create `core_gameplay/` package directory
2. Create `types.py` with all dataclasses
3. Create `__init__.py` with public exports

### Phase 2: Independent Modules (Day 2-3)
4. Create `frame_analysis.py` (no dependencies)
5. Create `sequence_manager.py` (depends on types, db)
6. Create `pattern_learning.py` (depends on types, db, frame_analysis)

### Phase 3: Integration Modules (Day 4-5)
7. Create `action_selection.py` (depends on types, db)
8. Create `sequence_replay.py` (depends on sequence_manager)
9. Create `agent_tracking.py` (depends on types, db)
10. Create `viral_evolution.py` (depends on types, db)

### Phase 4: Orchestration (Day 6)
11. Create `game_loop.py` (depends on all above)
12. Create `engine.py` (orchestrator)
13. Update imports throughout codebase

### Phase 5: Testing and Cleanup (Day 7)
14. Create unit tests for each module
15. Integration testing
16. Remove old `core_gameplay.py`
17. Update documentation

---

## Migration Strategy

### Backward Compatibility

During migration, maintain backward compatibility:

```python
# core_gameplay.py (temporary wrapper)
from core_gameplay.engine import GameplayEngine
from core_gameplay.types import *

# Deprecation warning for direct imports
import warnings
warnings.warn(
    "Importing from core_gameplay directly is deprecated. "
    "Use core_gameplay.engine instead.",
    DeprecationWarning
)
```

### Testing Approach

For each module:
1. Extract methods to new file
2. Create unit tests
3. Verify existing functionality still works
4. Remove old code only after tests pass

---

## Success Metrics

After refactoring:

| Metric | Before | After |
|--------|--------|-------|
| Lines in main file | 5,942 | ~200 |
| Methods in main class | 73 | ~10 |
| Max method length | 1,149 lines | ~100 lines |
| Cyclomatic complexity | Very High | Low |
| Test coverage | Unknown | >80% |
| Pylance errors | 1 (complexity) | 0 |

---

## Risk Mitigation

1. **Gradual Migration**: Don't refactor everything at once
2. **Test Coverage**: Write tests before moving code
3. **Backward Compatibility**: Old imports work during transition
4. **Version Control**: Commit after each module is complete
5. **Documentation**: Update docstrings as we go

---

## Appendix A: Method Classification

### High Priority (Core Functionality)
- `play_single_game` → Split into engine.py + game_loop.py
- `_capture_winning_sequence` → sequence_manager.py
- `_replay_sequence_inline` → sequence_replay.py
- `_select_action` → action_selection.py

### Medium Priority (Supporting)
- `_get_best_sequence_for_game` → sequence_manager.py
- `_handle_3_try_fallback` → Already extracted
- Frame comparison methods → frame_analysis.py

### Low Priority (Can Simplify)
- All `_meta_*` methods → Many can be consolidated or removed
- Pattern detection methods → Consolidate into pattern_learning.py

---

## Appendix B: Critical Missing Implementations

### 1. Full Game Sequence Storage (BLOCKING - Phase 0.1)

**Problem**: The `winning_sequences_full_game` table EXISTS (created in migrations) but NO code writes to it.

**Current Code** (`core_gameplay.py` line ~3235):
```python
# Current: Only inserts to winning_sequences
self.db.execute_query("""
    INSERT INTO winning_sequences (
        sequence_id, game_id, level_number, ...
    ) VALUES (?, ?, ?, ...)
""", (...))
```

**Required Fix**:
```python
def _capture_winning_sequence(self, ...):
    # ... existing code ...
    
    # NEW: Detect full game win
    if is_full_game_win:  # All levels completed in one playthrough
        self._store_full_game_sequence(
            game_id=game_id,
            agent_id=agent_id,
            session_id=session_id,
            total_actions=total_actions_all_levels,
            level_sequences=all_level_sequences,  # List of per-level data
            generation=generation
        )

def _store_full_game_sequence(self, game_id: str, agent_id: str, 
                               session_id: str, total_actions: int,
                               level_sequences: List[Dict], 
                               generation: int) -> str:
    """
    Store a complete game win in the PROTECTED full game table.
    
    Per Master Ruleset: "Full Game Sequences (Holy Grail)"
    - NEVER deleted, only inactivated if faulty
    - Priority: HIGHEST
    - Goal: Optimize total actions across all levels
    """
    sequence_id = str(uuid.uuid4())
    
    # Combine all level actions into single full game sequence
    all_actions = []
    for level_seq in level_sequences:
        all_actions.extend(level_seq['actions'])
    
    self.db.execute_query("""
        INSERT INTO winning_sequences_full_game (
            sequence_id, game_id, agent_id, session_id,
            total_actions, total_levels, action_sequence,
            level_breakdown, discovered_at, generation_discovered
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sequence_id, game_id, agent_id, session_id,
        total_actions, len(level_sequences), json.dumps(all_actions),
        json.dumps(level_sequences), datetime.now().isoformat(), generation
    ))
    
    logger.info(f"[HOLY GRAIL] Full game sequence stored: {game_id} "
               f"({len(level_sequences)} levels, {total_actions} total actions)")
    return sequence_id
```

**Detection Logic**:
```python
# In play_single_game, track if this is a fresh start (not continuing)
# If agent completes ALL levels from L1 → final without game reset = FULL GAME WIN
is_full_game_win = (
    started_from_level_1 and 
    completed_all_levels and 
    not used_level_reset_during_game
)
```

---

### 2. Optimizer End Subsequence (BLOCKING - Phase 0.2)

**Problem**: Optimizers reset levels to improve paths, but saved sequences DON'T include the final winning actions.

**Current Behavior**:
1. Optimizer plays level, finds better path
2. Resets level to try again
3. Saves "optimized" sequence → Missing ending!

**Required Fix**:
```python
def _append_end_subsequence(self, sequence_actions: List[Dict], 
                             game_id: str, level: int) -> List[Dict]:
    """
    Append proven ending to optimizer sequences.
    
    Per Master Ruleset: "Optimizer sequences MUST have end subsequence 
    auto-appended before DB save"
    
    Why: Optimizers reset mid-level, so their sequences miss final win actions.
    """
    # Get proven ending from existing winning sequence
    existing = self.db.execute_query("""
        SELECT action_sequence FROM winning_sequences
        WHERE game_id = ? AND level_number = ? AND is_active = 1
        ORDER BY success_rate_when_reused DESC, total_actions ASC
        LIMIT 1
    """, (game_id, level))
    
    if not existing:
        logger.warning(f"No proven ending for {game_id} L{level}")
        return sequence_actions  # Return as-is, may fail on replay
    
    proven_actions = json.loads(existing[0]['action_sequence'])
    
    # Find divergence point and append proven ending
    # (Optimized sequence may share prefix with proven sequence)
    # Append from first point of difference to end
    ending_actions = proven_actions[-10:]  # Last 10 actions as safety margin
    
    return sequence_actions + ending_actions
```

**Integration Point** (in `_capture_winning_sequence`):
```python
# Before saving optimizer sequence:
if agent_mode == 'optimizer':
    actions = self._append_end_subsequence(actions, game_id, level_number)
```

---

### 3. Agent Revival Integration (HIGH - Phase 0.3)

**Problem**: `revive_agents.py` has complete `AgentRevivalSystem` class but it's NEVER called.

**File**: `revive_agents.py` (386 lines) - fully implemented with:
- `detect_revival_triggers()` - finds performance regression, diversity collapse
- `revive_agent()` - Option B (hybrid) and Option C (successor) modes
- `agent_revivals` table for tracking

**Required Integration** (in `autonomous_evolution_runner.py`):
```python
# At top of file:
from revive_agents import AgentRevivalSystem

# In __init__:
self.revival_system = AgentRevivalSystem(self.db)

# In evolution loop (after each generation):
def _check_revival_triggers(self, generation: int):
    """Check if any agents should be revived based on triggers."""
    triggers = self.revival_system.detect_revival_triggers(generation)
    
    if triggers:
        logger.info(f"[REVIVAL] {len(triggers)} revival triggers detected")
        for trigger in triggers:
            revived_agent = self.revival_system.revive_agent(
                trigger,
                mode='hybrid'  # Per ruleset: "Use BOTH Option B + C"
            )
            if revived_agent:
                logger.info(f"[REVIVAL] Revived agent: {revived_agent['agent_id'][:8]} "
                           f"(trigger: {trigger['type']})")
```

---

### 4. Orphaned Code Cleanup

#### DELETE (Add to .gitignore or remove):
| File | Reason |
|------|--------|
| `emotional_gameplay_mixin.py` | Mixin pattern adds complexity; SomaticProfileSystem sufficient |
| `specialist_coordinator.py` | Unclear purpose, overlaps with agent_operating_mode_system |

#### MARK AS EXPERIMENTAL (Add header comment):
```python
# symbolic_reasoning_engine.py
"""
EXPERIMENTAL - NOT YET INTEGRATED
==================================
This module implements world model reasoning with objects, relations, and states.
It is NOT currently called by the main gameplay loop.

Future integration points:
- action_selection.py: Use world model to predict action outcomes
- pattern_learning.py: Extract symbolic rules from frame sequences

Status: Proof of concept, awaiting integration decision
"""
```

```python
# visual_reasoning_engine.py
"""
EXPERIMENTAL - NOT YET INTEGRATED  
==================================
This module implements visual pattern reasoning for game frames.
It is NOT currently called by the main gameplay loop.

Future integration points:
- frame_analysis.py: Use for deeper pattern recognition
- agent_self_model.py: Improve object identification

Status: Proof of concept, awaiting integration decision
"""
```

---

## Appendix C: Implementation Order

### Phase 0: Pre-Refactoring Fixes (MUST DO FIRST)

| Step | Task | Files | Effort | Blocks |
|------|------|-------|--------|--------|
| 0.1 | Full game sequence storage | `core_gameplay.py` | 50 lines | Phase 1+ |
| 0.2 | Optimizer end subsequence | `core_gameplay.py` | 30 lines | Phase 1+ |
| 0.3 | Agent revival integration | `autonomous_evolution_runner.py` | 20 lines | - |
| 0.4 | Delete orphaned files | `emotional_gameplay_mixin.py`, `specialist_coordinator.py` | 0 lines | - |
| 0.5 | Mark experimental files | `symbolic_reasoning_engine.py`, `visual_reasoning_engine.py` | 10 lines | - |

### Phase 1: Foundation (Day 1-2)
- Create `core_gameplay/` package structure
- Create `types.py` with all dataclasses
- Create `__init__.py` with backward-compatible exports

### Phase 2: Sequence System (Day 3-4)
- Extract `sequence_manager.py` (includes full game storage)
- Extract `sequence_replay.py` (includes 3-try fallback)
- Unit tests for sequence operations

### Phase 3: Action System (Day 5)
- Extract `action_selection.py`
- Extract `frame_analysis.py`

### Phase 4: Learning System (Day 6)
- Extract `pattern_learning.py`
- Extract `viral_evolution.py`

### Phase 5: Engine Consolidation (Day 7)
- Create slim `engine.py` orchestrator
- Create `game_loop.py`
- Final `core_gameplay.py` becomes thin wrapper

---

## Appendix D: File Organization Summary

### After Refactoring

```
BitterTruth-AI/
├── core_gameplay/                 # NEW: Refactored package
│   ├── __init__.py
│   ├── types.py                   # Dataclasses, enums (Level 0)
│   ├── config.py                  # Centralized configuration (Level 0)
│   ├── container.py               # Dependency injection container
│   ├── transactions.py            # Atomic operation boundaries
│   ├── state_machine.py           # Game state transitions
│   ├── metrics_hooks.py           # Decorator-based metrics collection
│   ├── engine.py                  # Orchestrator (Level 4)
│   ├── game_loop.py               # Main loop (Level 3)
│   ├── sequence_manager.py        # Sequence CRUD (Level 1)
│   ├── sequence_replay.py         # Replay logic (Level 2)
│   ├── action_selection.py        # Action selection (Level 2)
│   ├── pattern_learning.py        # Pattern detection (Level 1)
│   ├── frame_analysis.py          # Frame comparison (Level 1)
│   ├── agent_tracking.py          # Agent performance (Level 2)
│   └── viral_evolution.py         # Viral packages/pariahs (Level 2)
│
├── dashboards/                    # NEW: System health monitoring
│   ├── __init__.py
│   ├── health_dashboard.py        # Main Plotly dashboard
│   ├── metrics_collector.py       # Background metrics collection
│   ├── time_range_collector.py    # Time-range-aware metrics
│   ├── alert_manager.py           # Alert generation and management
│   ├── error_metrics.py           # Error tracking by role/game type
│   └── dashboard_config.py        # Dashboard settings
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── unit/                      # Unit tests (mocked dependencies)
│   ├── integration/               # Integration tests (real DB, mock API)
│   └── e2e/                       # End-to-end tests (real games)
│
├── manual_tools/                  # Standalone utilities (already moved)
│   ├── README.md
│   ├── check_db.py
│   ├── dump_logs.py
│   ├── inspect_db.py
│   ├── list_sequences.py
│   ├── list_tables.py
│   ├── get_replay_url.py
│   ├── review_*.py (4 files)
│   ├── run_validation_cycle.py
│   └── (other utilities)
│
├── experimental/                  # NEW: Future features
│   ├── README.md
│   ├── symbolic_reasoning_engine.py
│   └── visual_reasoning_engine.py
│
├── DELETED/                       # Files to remove
│   ├── emotional_gameplay_mixin.py
│   └── specialist_coordinator.py
│
└── (existing files remain)
```

---

## Appendix E: Viral Package Auto-Propagation System

### Problem Statement
When agents are deactivated (culled, retired, or crashed), their viral packages and pariahs die with them. This causes:
- Loss of valuable knowledge that took generations to discover
- Pariahs (failure patterns) forgotten, leading to repeated mistakes
- Viral packages with proven success disappearing from the network

### Solution: Auto-Propagation on Low Carrier Count

#### New Database Table: `viral_package_carriers`
```sql
CREATE TABLE viral_package_carriers (
    package_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    PRIMARY KEY (package_id, agent_id),
    FOREIGN KEY (package_id) REFERENCES viral_packages(package_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Index for fast carrier counts
CREATE INDEX idx_viral_carriers_package ON viral_package_carriers(package_id, is_active);
```

#### Configuration Parameters
```python
VIRAL_PROPAGATION_CONFIG = {
    'min_carrier_count': 3,           # Minimum agents carrying each package
    'critical_carrier_count': 1,       # Emergency propagation threshold
    'propagation_batch_size': 5,       # Max packages to propagate per cycle
    'pariah_min_carriers': 2,          # Pariahs need fewer carriers (lessons learned)
    'max_carriers_per_package': 20,    # Prevent over-saturation
    'propagation_check_interval': 10,  # Check every N games
}
```

#### Implementation: `viral_propagation_guardian.py`
```python
"""
Viral Propagation Guardian - Prevents knowledge death.

This module monitors viral package and pariah carrier counts,
automatically propagating to new agents when counts drop below
minimum thresholds.

Per Master Ruleset: "Viral Packages = Successful strategies spread like actual viruses"
This ensures valuable strategies NEVER die with individual agents.
"""

class ViralPropagationGuardian:
    """Monitors and maintains viral package carrier counts."""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.config = VIRAL_PROPAGATION_CONFIG
    
    def check_and_propagate(self) -> Dict[str, int]:
        """
        Check all active packages and propagate those below threshold.
        
        Returns:
            {
                'packages_checked': int,
                'packages_propagated': int,
                'new_carriers_assigned': int
            }
        """
        # 1. Find packages below threshold
        endangered_packages = self._find_endangered_packages()
        
        # 2. Find eligible recipient agents
        eligible_agents = self._find_eligible_carriers()
        
        # 3. Propagate packages to new carriers
        propagated = self._propagate_packages(endangered_packages, eligible_agents)
        
        return propagated
    
    def _find_endangered_packages(self) -> List[Dict]:
        """Find viral packages and pariahs with low carrier counts."""
        return self.db.execute_query("""
            SELECT 
                vp.package_id,
                vp.package_type,
                vp.game_id,
                vp.success_rate,
                vp.times_spread,
                COUNT(vpc.agent_id) as carrier_count
            FROM viral_packages vp
            LEFT JOIN viral_package_carriers vpc 
                ON vp.package_id = vpc.package_id AND vpc.is_active = 1
            LEFT JOIN agents a ON vpc.agent_id = a.agent_id AND a.is_active = 1
            WHERE vp.is_active = 1
            GROUP BY vp.package_id
            HAVING carrier_count < ?
            ORDER BY 
                CASE WHEN vp.package_type = 'pariah' THEN 0 ELSE 1 END,  -- Pariahs first
                carrier_count ASC,  -- Most endangered first
                vp.success_rate DESC  -- Highest success rate
            LIMIT ?
        """, (self.config['min_carrier_count'], self.config['propagation_batch_size']))
    
    def _find_eligible_carriers(self) -> List[str]:
        """Find active agents that can receive new packages."""
        return self.db.execute_query("""
            SELECT agent_id 
            FROM agents 
            WHERE is_active = 1
            AND (
                SELECT COUNT(*) FROM viral_package_carriers 
                WHERE agent_id = agents.agent_id AND is_active = 1
            ) < ?
            ORDER BY 
                prestige DESC,  -- Higher prestige = better carrier
                generation DESC  -- Newer agents preferred
            LIMIT 50
        """, (self.config['max_carriers_per_package'],))
    
    def _propagate_packages(
        self, 
        packages: List[Dict], 
        agents: List[str]
    ) -> Dict[str, int]:
        """Propagate endangered packages to eligible agents."""
        propagated_count = 0
        new_carriers = 0
        
        for package in packages:
            needed_carriers = self.config['min_carrier_count'] - package['carrier_count']
            
            # Find agents that don't already have this package
            available_agents = [
                a for a in agents 
                if not self._agent_has_package(a['agent_id'], package['package_id'])
            ]
            
            # Assign to available agents
            for agent in available_agents[:needed_carriers]:
                self._assign_package_to_agent(package['package_id'], agent['agent_id'])
                new_carriers += 1
            
            if new_carriers > 0:
                propagated_count += 1
                logger.info(
                    f"[GUARDIAN] Auto-propagated {package['package_type']} "
                    f"{package['package_id'][:8]} to {new_carriers} new carriers"
                )
        
        return {
            'packages_checked': len(packages),
            'packages_propagated': propagated_count,
            'new_carriers_assigned': new_carriers
        }
    
    def handle_agent_deactivation(self, agent_id: str) -> None:
        """
        Called when an agent is deactivated.
        Immediately checks if any packages need emergency propagation.
        """
        # Mark this agent's carrier records as inactive
        self.db.execute_query("""
            UPDATE viral_package_carriers 
            SET is_active = 0 
            WHERE agent_id = ?
        """, (agent_id,))
        
        # Check for critical packages (only 1 carrier left)
        critical_packages = self.db.execute_query("""
            SELECT package_id, package_type
            FROM viral_packages vp
            WHERE vp.is_active = 1
            AND (
                SELECT COUNT(*) FROM viral_package_carriers vpc
                JOIN agents a ON vpc.agent_id = a.agent_id
                WHERE vpc.package_id = vp.package_id 
                AND vpc.is_active = 1 AND a.is_active = 1
            ) <= ?
        """, (self.config['critical_carrier_count'],))
        
        if critical_packages:
            logger.warning(
                f"[GUARDIAN] CRITICAL: {len(critical_packages)} packages at risk "
                f"after agent {agent_id[:8]} deactivation. Emergency propagation triggered."
            )
            self.check_and_propagate()
```

#### Integration Points

1. **In `evolutionary_engine.py` (agent culling)**:
```python
def _cull_agents(self, generation: int):
    # ... existing culling logic ...
    
    for agent_id in agents_to_cull:
        # Notify guardian BEFORE deactivation
        self.viral_guardian.handle_agent_deactivation(agent_id)
        self._deactivate_agent(agent_id)
```

2. **In `autonomous_evolution_runner.py` (periodic check)**:
```python
def _post_generation_maintenance(self, generation: int):
    # ... existing maintenance ...
    
    # Check viral package health every 10 generations
    if generation % 10 == 0:
        stats = self.viral_guardian.check_and_propagate()
        if stats['packages_propagated'] > 0:
            logger.info(f"[GUARDIAN] Propagated {stats['packages_propagated']} endangered packages")
```

---

## Appendix F: Sequence Logic Documentation System

### Problem Statement
Sequence storage and retrieval logic is scattered across multiple files with complex conditions. 
Need a way to:
1. Document all code references for sequence logic
2. Create a real-time updated flow diagram
3. Make it easy to understand and modify thresholds

### Phase 1: Code Reference Gathering

#### Files Containing Sequence Logic
| File | Functions | Purpose |
|------|-----------|---------|
| `core_gameplay.py` | `_capture_winning_sequence`, `_get_best_sequence_for_game`, `_get_ranked_cumulative_sequences`, `_flag_sequence_failure`, `_record_sequence_validation` | Main sequence operations |
| `multi_stage_matching_pipeline.py` | `match_sequence`, `_exact_match`, `_prefix_match`, `_suffix_match`, `_subsequence_match`, `_conceptual_match` | 5-stage retrieval fallback |
| `sequence_abstraction.py` | `abstract_sequence`, `match_abstract`, `concept_similarity` | Concept-based matching |
| `sequence_pruning_system.py` | `prune_stale_sequences`, `calculate_sequence_health`, `should_deactivate` | Sequence lifecycle |
| `viral_package_engine.py` | `create_viral_from_sequence`, `spread_sequence_knowledge` | Sequence → Viral conversion |

### Phase 2: Sequence Logic Documentation Format

Create `DOCS/sequence_logic_reference.md`:

```markdown
# Sequence System Logic Reference

## STORAGE CONDITIONS

### When Sequences ARE Stored

| Condition | Threshold | Location | Line |
|-----------|-----------|----------|------|
| Level completion | score_increase >= 1.0 | `core_gameplay.py` | ~3200 |
| Not duplicate | action_hash != existing | `core_gameplay.py` | ~3245 |
| Diversity bonus | game_type_count < 10 | `core_gameplay.py` | ~3260 |
| Min actions | total_actions >= 1 | `core_gameplay.py` | ~3215 |
| Valid frame | initial_frame != None | `core_gameplay.py` | ~3220 |

### When Sequences are NOT Stored

| Condition | Threshold | Location | Line |
|-----------|-----------|----------|------|
| Duplicate exists | exact_match found | `core_gameplay.py` | ~3248 |
| Too many for game | count >= 50 per game | `core_gameplay.py` | ~3255 |
| Pioneer on beaten level | mode=='pioneer' AND level_beaten | `core_gameplay.py` | ~3230 |
| Zero score | final_score == 0 | `core_gameplay.py` | ~3210 |

## RETRIEVAL PRIORITY

### Ranking Criteria (in order)

1. **Exact game_id match** (weight: 10.0)
2. **Success rate when reused** (weight: 5.0)
3. **Times referenced** (weight: 2.0)
4. **Fewest actions** (weight: 1.0)
5. **Most recent** (weight: 0.5)

### 5-Stage Fallback Pipeline

```
STAGE 1: Exact Match
├── Frame similarity >= 0.95
├── Action count within 10%
└── Same game_id

STAGE 2: Prefix Match
├── First N actions identical
└── N >= 5 actions

STAGE 3: Suffix Match
├── Last N actions identical
└── N >= 3 actions

STAGE 4: Subsequence Match
├── Core pattern found within sequence
└── Pattern length >= 3

STAGE 5: Conceptual Match
├── Abstract concept similarity >= 0.7
└── Same game type
```

## THRESHOLDS REFERENCE

| Parameter | Value | Purpose | Configurable |
|-----------|-------|---------|--------------|
| `MIN_FRAME_SIMILARITY` | 0.95 | Exact frame matching | Yes |
| `MAX_SEQUENCES_PER_GAME` | 50 | Prevent bloat | Yes |
| `DIVERSITY_THRESHOLD` | 10 | Min sequences per game type | Yes |
| `SUCCESS_RATE_FLOOR` | 0.30 | Below this = flagged | Yes |
| `CONSECUTIVE_FAILURES_LIMIT` | 3 | Deactivation trigger | Yes |
| `STALE_SEQUENCE_DAYS` | 30 | Age-based pruning | Yes |
```

### Phase 3: Auto-Generated Flow Diagram

Create `sequence_flow_generator.py`:

```python
"""
Sequence Flow Generator - Creates real-time logic flow diagrams.

Parses sequence-related code and generates Mermaid diagrams
showing the decision tree for storage and retrieval.
"""

import ast
import re
from pathlib import Path

class SequenceFlowGenerator:
    """Generates flow diagrams from sequence logic code."""
    
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path)
        self.storage_conditions = []
        self.retrieval_conditions = []
    
    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze all files for sequence logic."""
        files_to_scan = [
            'core_gameplay.py',
            'multi_stage_matching_pipeline.py',
            'sequence_abstraction.py',
            'sequence_pruning_system.py'
        ]
        
        for filename in files_to_scan:
            filepath = self.root / filename
            if filepath.exists():
                self._analyze_file(filepath)
        
        return {
            'storage': self.storage_conditions,
            'retrieval': self.retrieval_conditions
        }
    
    def generate_mermaid_storage(self) -> str:
        """Generate Mermaid flowchart for sequence storage."""
        mermaid = """```mermaid
flowchart TD
    A[Level Completed] --> B{score_increase >= 1.0?}
    B -->|No| Z[Do Not Store]
    B -->|Yes| C{initial_frame valid?}
    C -->|No| Z
    C -->|Yes| D{Duplicate exists?}
    D -->|Yes| Z
    D -->|No| E{Game type count < 50?}
    E -->|No| F{Diversity bonus?}
    F -->|No| Z
    F -->|Yes| G[Store Sequence]
    E -->|Yes| G
    
    style G fill:#90EE90
    style Z fill:#FFB6C1
```"""
        return mermaid
    
    def generate_mermaid_retrieval(self) -> str:
        """Generate Mermaid flowchart for sequence retrieval."""
        mermaid = """```mermaid
flowchart TD
    A[Request Sequence] --> B[Stage 1: Exact Match]
    B -->|Found| SUCCESS[Return Sequence]
    B -->|Not Found| C[Stage 2: Prefix Match]
    C -->|Found| SUCCESS
    C -->|Not Found| D[Stage 3: Suffix Match]
    D -->|Found| SUCCESS
    D -->|Not Found| E[Stage 4: Subsequence Match]
    E -->|Found| SUCCESS
    E -->|Not Found| F[Stage 5: Conceptual Match]
    F -->|Found| SUCCESS
    F -->|Not Found| G[Return None - Explore]
    
    style SUCCESS fill:#90EE90
    style G fill:#FFD700
```"""
        return mermaid
    
    def export_documentation(self, output_path: str = "DOCS/sequence_logic_reference.md"):
        """Export complete documentation with diagrams."""
        analysis = self.analyze_codebase()
        
        doc = f"""# Sequence System Logic Reference

**Auto-generated**: {datetime.now().isoformat()}
**Source files scanned**: {len(analysis['storage']) + len(analysis['retrieval'])} conditions found

## Storage Flow

{self.generate_mermaid_storage()}

## Retrieval Flow

{self.generate_mermaid_retrieval()}

## Detailed Conditions

### Storage Conditions
{self._format_conditions(analysis['storage'])}

### Retrieval Conditions  
{self._format_conditions(analysis['retrieval'])}
"""
        
        Path(output_path).write_text(doc)
        return output_path
```

---

## Appendix G: System Health Dashboard

### Implementation To-Do List

- [x] **G.1 Sequence Failures**: All types (stale, low success, high-volume) ranked by impact
- [x] **G.2 Fault Priority**: API failures > System stuck > Knowledge loss
- [x] **G.3 Alert System**: Both visual + active alerts for user AND future autonomous coordinator
- [x] **G.4 Time Ranges**: Tabs/dropdowns for real-time, 24h, generational, all history
- [x] **G.5 Metric Count**: Medium-comprehensive (30-50 metrics)
- [x] **G.6 Communication Metrics**: Include viral packages/pariahs as communication

### Problem Statement
No visibility into system health metrics like:
- Knowledge diversity decay
- Failure cascade risk
- Innovation stagnation
- Agent population dynamics

### G.1 Sequence Failure Metrics (Ranked by Impact)

All sequence failure types tracked and ranked by their impact on system health:

```python
@dataclass
class SequenceFailureMetrics:
    """Comprehensive sequence failure tracking - ranked by system impact."""
    
    # TIER 1: HIGH IMPACT (blocks progress)
    stale_sequences_blocking_games: int      # Sequences that cause repeated failures
    high_volume_failures_1h: int             # Many failures in short time = systemic issue
    critical_game_types_failing: List[str]   # Which game types have 0 working sequences
    
    # TIER 2: MEDIUM IMPACT (degrades performance)  
    low_success_rate_sequences: int          # Sequences with <30% success rate
    sequences_never_validated: int           # Stored but never tested
    orphaned_sequences: int                  # No agent has used in 7+ days
    
    # TIER 3: LOW IMPACT (maintenance needed)
    duplicate_sequences: int                 # Redundant sequences wasting space
    outdated_frame_sequences: int            # Initial frames no longer match games
    suboptimal_sequences: int                # Working but far from optimal

class SequenceFailureAnalyzer:
    """Analyzes and ranks sequence failures by impact."""
    
    def get_failure_ranking(self) -> List[Dict[str, Any]]:
        """
        Get all sequence failures ranked by impact score.
        
        Impact Score = (failure_frequency * 0.4) + (games_affected * 0.3) + 
                      (recovery_difficulty * 0.3)
        """
        failures = []
        
        # Tier 1: Blocking failures
        blocking = self._get_blocking_failures()
        for f in blocking:
            f['impact_score'] = self._calculate_impact(f, tier=1)
            f['tier'] = 'CRITICAL'
        failures.extend(blocking)
        
        # Tier 2: Degrading failures
        degrading = self._get_degrading_failures()
        for f in degrading:
            f['impact_score'] = self._calculate_impact(f, tier=2)
            f['tier'] = 'WARNING'
        failures.extend(degrading)
        
        # Tier 3: Maintenance failures
        maintenance = self._get_maintenance_failures()
        for f in maintenance:
            f['impact_score'] = self._calculate_impact(f, tier=3)
            f['tier'] = 'INFO'
        failures.extend(maintenance)
        
        # Sort by impact score descending
        return sorted(failures, key=lambda x: x['impact_score'], reverse=True)
    
    def _get_blocking_failures(self) -> List[Dict]:
        """Get sequences causing complete blockage."""
        return self.db.execute_query("""
            SELECT 
                ws.sequence_id,
                ws.game_id,
                COUNT(sv.validation_id) as failure_count,
                MAX(sv.validated_at) as last_failure,
                'STALE_BLOCKING' as failure_type
            FROM winning_sequences ws
            JOIN sequence_validations sv ON ws.sequence_id = sv.sequence_id
            WHERE sv.success = 0 
              AND sv.validated_at > datetime('now', '-24 hours')
            GROUP BY ws.sequence_id
            HAVING failure_count >= 3
            ORDER BY failure_count DESC
        """)
    
    def _calculate_impact(self, failure: Dict, tier: int) -> float:
        """Calculate impact score (0-100) for a failure."""
        base_score = {1: 70, 2: 40, 3: 10}[tier]
        frequency_bonus = min(30, failure.get('failure_count', 0) * 3)
        return base_score + frequency_bonus
```

### G.2 Fault Priority System

Faults are prioritized in strict order: **API failures > System stuck > Knowledge loss**

```python
class FaultPriority(Enum):
    """Fault priority levels - higher number = more critical."""
    
    # PRIORITY 1: API/CONNECTIVITY (Highest - system cannot function)
    API_CONNECTION_FAILED = 100      # Cannot reach ARC API at all
    API_RATE_LIMITED = 95            # Being throttled by API
    API_AUTHENTICATION_ERROR = 90    # API key invalid/expired
    API_TIMEOUT = 85                 # Requests timing out
    API_MALFORMED_RESPONSE = 80      # API returning unexpected data
    
    # PRIORITY 2: SYSTEM STUCK (High - system running but not progressing)
    ALL_AGENTS_STUCK = 75            # Every agent stuck on same level
    EVOLUTION_STALLED = 70           # No progress for N generations
    GAME_LOOP_FROZEN = 65            # Game loop not advancing
    DATABASE_LOCKED = 60             # DB write contention
    SEQUENCE_REPLAY_LOOP = 55        # Stuck replaying failed sequences
    
    # PRIORITY 3: KNOWLEDGE LOSS (Medium - losing learned information)
    SEQUENCE_CORRUPTION = 50         # Stored sequences becoming invalid
    VIRAL_PACKAGE_DEATH = 45         # Viral packages losing all carriers
    PARIAH_AMNESIA = 40              # Pariahs being forgotten
    PRESTIGE_COLLAPSE = 35           # Prestige system malfunction
    AGENT_KNOWLEDGE_ORPHANED = 30    # Deactivated agents' knowledge lost


@dataclass
class SystemFault:
    """Represents a detected system fault."""
    fault_type: FaultPriority
    severity: float                  # 0.0-1.0 within priority level
    detected_at: datetime
    description: str
    affected_components: List[str]
    suggested_action: str
    auto_recoverable: bool


class FaultDetector:
    """Detects and prioritizes system faults."""
    
    def __init__(self, db: DatabaseInterface, api_client: ARCAPIClient):
        self.db = db
        self.api = api_client
        self.fault_history: List[SystemFault] = []
    
    def detect_all_faults(self) -> List[SystemFault]:
        """
        Detect all current faults, sorted by priority.
        
        Returns faults in strict priority order:
        1. API/Connectivity issues (check first - everything depends on API)
        2. System stuck issues (check second - is system progressing?)
        3. Knowledge loss issues (check third - are we losing learning?)
        """
        faults = []
        
        # Priority 1: API Health (HIGHEST)
        faults.extend(self._check_api_health())
        
        # Priority 2: System Progress
        faults.extend(self._check_system_stuck())
        
        # Priority 3: Knowledge Integrity
        faults.extend(self._check_knowledge_loss())
        
        # Sort by priority (highest first)
        return sorted(faults, key=lambda f: f.fault_type.value, reverse=True)
    
    def _check_api_health(self) -> List[SystemFault]:
        """Check API connectivity and health."""
        faults = []
        
        # Test API connection
        try:
            response = self.api.health_check()
            if response.status_code == 429:
                faults.append(SystemFault(
                    fault_type=FaultPriority.API_RATE_LIMITED,
                    severity=0.8,
                    detected_at=datetime.now(),
                    description="ARC API rate limiting active",
                    affected_components=['api_client', 'game_sessions'],
                    suggested_action="Reduce request frequency, wait for cooldown",
                    auto_recoverable=True
                ))
        except ConnectionError:
            faults.append(SystemFault(
                fault_type=FaultPriority.API_CONNECTION_FAILED,
                severity=1.0,
                detected_at=datetime.now(),
                description="Cannot connect to ARC API",
                affected_components=['ALL'],
                suggested_action="Check network, verify API endpoint",
                auto_recoverable=False
            ))
        
        return faults
    
    def _check_system_stuck(self) -> List[SystemFault]:
        """Check if system is stuck/not progressing."""
        faults = []
        
        # Check for stalled evolution
        result = self.db.execute_query("""
            SELECT COUNT(*) as stuck_count
            FROM agents 
            WHERE is_active = 1 
              AND last_game_at < datetime('now', '-1 hour')
        """)
        
        if result and result[0]['stuck_count'] > 10:
            faults.append(SystemFault(
                fault_type=FaultPriority.ALL_AGENTS_STUCK,
                severity=result[0]['stuck_count'] / 50,
                detected_at=datetime.now(),
                description=f"{result[0]['stuck_count']} agents haven't played in 1+ hour",
                affected_components=['evolution_loop', 'game_scheduler'],
                suggested_action="Check game assignment, reset stuck agents",
                auto_recoverable=True
            ))
        
        return faults
    
    def _check_knowledge_loss(self) -> List[SystemFault]:
        """Check for knowledge loss indicators."""
        faults = []
        
        # Check viral package carrier counts
        result = self.db.execute_query("""
            SELECT vp.package_id, COUNT(vpc.agent_id) as carrier_count
            FROM viral_packages vp
            LEFT JOIN viral_package_carriers vpc 
              ON vp.package_id = vpc.package_id AND vpc.is_active = 1
            WHERE vp.is_active = 1
            GROUP BY vp.package_id
            HAVING carrier_count < 2
        """)
        
        if result and len(result) > 0:
            faults.append(SystemFault(
                fault_type=FaultPriority.VIRAL_PACKAGE_DEATH,
                severity=len(result) / 20,
                detected_at=datetime.now(),
                description=f"{len(result)} viral packages at risk of death (<2 carriers)",
                affected_components=['viral_evolution', 'knowledge_transfer'],
                suggested_action="Trigger emergency propagation",
                auto_recoverable=True
            ))
        
        return faults
```

### G.3 Alert System (Visual + Active for Human AND Coordinator)

Dual-purpose alert system: visual dashboard for humans, programmatic API for autonomous coordinator.

```python
class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"    # Immediate attention required
    WARNING = "warning"      # Action needed soon
    INFO = "info"           # Informational only


@dataclass
class SystemAlert:
    """Alert that can be consumed by human or coordinator."""
    alert_id: str
    severity: AlertSeverity
    fault: SystemFault
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None  # 'human' or 'coordinator'
    resolved: bool = False
    resolution_action: Optional[str] = None


class AlertManager:
    """
    Manages alerts for both human users and autonomous coordinator.
    
    Two consumption modes:
    1. VISUAL: Dashboard shows alerts, user clicks to acknowledge
    2. PROGRAMMATIC: Coordinator polls for alerts, takes action, marks resolved
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.fault_detector = FaultDetector(db)
        self.active_alerts: Dict[str, SystemAlert] = {}
    
    # =========================================================================
    # ALERT GENERATION
    # =========================================================================
    
    def check_and_generate_alerts(self) -> List[SystemAlert]:
        """
        Check for faults and generate alerts.
        
        Called by:
        - Dashboard (every 30 seconds for visual display)
        - Coordinator (every generation for programmatic handling)
        """
        faults = self.fault_detector.detect_all_faults()
        new_alerts = []
        
        for fault in faults:
            # Don't duplicate existing active alerts
            if self._alert_exists_for_fault(fault):
                continue
            
            alert = SystemAlert(
                alert_id=str(uuid.uuid4()),
                severity=self._fault_to_severity(fault),
                fault=fault,
                created_at=datetime.now()
            )
            
            self.active_alerts[alert.alert_id] = alert
            self._store_alert(alert)
            new_alerts.append(alert)
        
        return new_alerts
    
    def _fault_to_severity(self, fault: SystemFault) -> AlertSeverity:
        """Map fault priority to alert severity."""
        if fault.fault_type.value >= 75:
            return AlertSeverity.CRITICAL
        elif fault.fault_type.value >= 40:
            return AlertSeverity.WARNING
        return AlertSeverity.INFO
    
    # =========================================================================
    # HUMAN INTERFACE (Visual Dashboard)
    # =========================================================================
    
    def get_visual_alerts(self) -> List[Dict[str, Any]]:
        """
        Get alerts formatted for dashboard display.
        
        Returns human-readable format with colors, icons, and actions.
        """
        alerts = []
        for alert in self.active_alerts.values():
            if alert.resolved:
                continue
            
            alerts.append({
                'id': alert.alert_id,
                'severity': alert.severity.value,
                'color': self._severity_color(alert.severity),
                'icon': self._severity_icon(alert.severity),
                'title': alert.fault.fault_type.name.replace('_', ' ').title(),
                'description': alert.fault.description,
                'suggested_action': alert.fault.suggested_action,
                'time_ago': self._time_ago(alert.created_at),
                'acknowledged': alert.acknowledged,
            })
        
        return sorted(alerts, key=lambda a: 
            {'critical': 0, 'warning': 1, 'info': 2}[a['severity']])
    
    def acknowledge_alert_human(self, alert_id: str) -> bool:
        """Human acknowledges alert via dashboard click."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.active_alerts[alert_id].acknowledged_by = 'human'
            return True
        return False
    
    def _severity_color(self, severity: AlertSeverity) -> str:
        """Get color for severity level."""
        return {'critical': '#FF4444', 'warning': '#FFAA00', 'info': '#4488FF'}[severity.value]
    
    def _severity_icon(self, severity: AlertSeverity) -> str:
        """Get ASCII icon for severity level."""
        return {'critical': '[!!!]', 'warning': '[!]', 'info': '[i]'}[severity.value]
    
    # =========================================================================
    # COORDINATOR INTERFACE (Programmatic)
    # =========================================================================
    
    def get_coordinator_alerts(self) -> List[SystemAlert]:
        """
        Get alerts for autonomous coordinator consumption.
        
        Returns raw SystemAlert objects for programmatic handling.
        Coordinator can inspect fault details and decide on action.
        """
        return [a for a in self.active_alerts.values() 
                if not a.resolved and a.fault.auto_recoverable]
    
    def get_critical_unhandled(self) -> List[SystemAlert]:
        """Get critical alerts that haven't been acknowledged."""
        return [a for a in self.active_alerts.values()
                if a.severity == AlertSeverity.CRITICAL 
                and not a.acknowledged 
                and not a.resolved]
    
    def resolve_alert_coordinator(
        self, 
        alert_id: str, 
        action_taken: str
    ) -> bool:
        """
        Coordinator resolves alert after taking action.
        
        Args:
            alert_id: The alert to resolve
            action_taken: Description of what coordinator did
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.acknowledged = True
            alert.acknowledged_by = 'coordinator'
            alert.resolution_action = action_taken
            self._update_alert_in_db(alert)
            return True
        return False
    
    def should_coordinator_act(self) -> bool:
        """
        Check if coordinator should take immediate action.
        
        Returns True if there are critical, auto-recoverable,
        unacknowledged alerts.
        """
        critical = self.get_critical_unhandled()
        return any(a.fault.auto_recoverable for a in critical)
    
    # =========================================================================
    # DATABASE PERSISTENCE
    # =========================================================================
    
    def _store_alert(self, alert: SystemAlert) -> None:
        """Store alert in database for history."""
        self.db.execute_query("""
            INSERT INTO system_alerts (
                alert_id, severity, fault_type, description,
                suggested_action, created_at, auto_recoverable
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.alert_id, alert.severity.value,
            alert.fault.fault_type.name, alert.fault.description,
            alert.fault.suggested_action, alert.created_at.isoformat(),
            alert.fault.auto_recoverable
        ))


# New table required:
"""
CREATE TABLE system_alerts (
    alert_id TEXT PRIMARY KEY,
    severity TEXT NOT NULL,
    fault_type TEXT NOT NULL,
    description TEXT,
    suggested_action TEXT,
    created_at TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    acknowledged_by TEXT,
    resolved INTEGER DEFAULT 0,
    resolution_action TEXT,
    auto_recoverable INTEGER DEFAULT 0
);

CREATE INDEX idx_alerts_severity ON system_alerts(severity, resolved);
CREATE INDEX idx_alerts_created ON system_alerts(created_at);
"""
```

### G.4 Time Range System (Tabs/Dropdowns)

Dashboard supports multiple time ranges via tabs and dropdowns for all metrics.

```python
class TimeRange(Enum):
    """Available time ranges for metrics viewing."""
    REAL_TIME = "real_time"          # Live, updates every 30 seconds
    LAST_HOUR = "1h"                 # Last 60 minutes
    LAST_24H = "24h"                 # Last 24 hours
    LAST_7D = "7d"                   # Last 7 days
    GENERATIONAL = "generational"    # Per-generation view
    ALL_HISTORY = "all"              # Complete history


@dataclass
class TimeRangeConfig:
    """Configuration for a time range."""
    range_type: TimeRange
    display_name: str
    sql_modifier: str                # For datetime queries
    refresh_interval_ms: int         # How often to refresh
    aggregation: str                 # 'none', 'hourly', 'daily', 'per_gen'


TIME_RANGE_CONFIGS = {
    TimeRange.REAL_TIME: TimeRangeConfig(
        range_type=TimeRange.REAL_TIME,
        display_name="Real-Time",
        sql_modifier="-5 minutes",
        refresh_interval_ms=30_000,  # 30 seconds
        aggregation='none'
    ),
    TimeRange.LAST_HOUR: TimeRangeConfig(
        range_type=TimeRange.LAST_HOUR,
        display_name="Last Hour",
        sql_modifier="-1 hour",
        refresh_interval_ms=60_000,  # 1 minute
        aggregation='none'
    ),
    TimeRange.LAST_24H: TimeRangeConfig(
        range_type=TimeRange.LAST_24H,
        display_name="Last 24 Hours",
        sql_modifier="-24 hours",
        refresh_interval_ms=300_000,  # 5 minutes
        aggregation='hourly'
    ),
    TimeRange.LAST_7D: TimeRangeConfig(
        range_type=TimeRange.LAST_7D,
        display_name="Last 7 Days",
        sql_modifier="-7 days",
        refresh_interval_ms=900_000,  # 15 minutes
        aggregation='daily'
    ),
    TimeRange.GENERATIONAL: TimeRangeConfig(
        range_type=TimeRange.GENERATIONAL,
        display_name="By Generation",
        sql_modifier="",  # Uses generation number, not time
        refresh_interval_ms=300_000,
        aggregation='per_gen'
    ),
    TimeRange.ALL_HISTORY: TimeRangeConfig(
        range_type=TimeRange.ALL_HISTORY,
        display_name="All History",
        sql_modifier="",  # No filter
        refresh_interval_ms=3600_000,  # 1 hour
        aggregation='daily'
    ),
}


class TimeRangeMetricsCollector:
    """Collects metrics for specific time ranges."""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
    
    def collect_for_range(
        self, 
        time_range: TimeRange
    ) -> Dict[str, Any]:
        """Collect all metrics for a specific time range."""
        config = TIME_RANGE_CONFIGS[time_range]
        
        if time_range == TimeRange.GENERATIONAL:
            return self._collect_generational()
        
        return {
            'time_range': config.display_name,
            'sequence_metrics': self._get_sequence_metrics(config),
            'agent_metrics': self._get_agent_metrics(config),
            'failure_metrics': self._get_failure_metrics(config),
            'communication_metrics': self._get_communication_metrics(config),
            'collected_at': datetime.now().isoformat(),
        }
    
    def _get_sequence_metrics(self, config: TimeRangeConfig) -> Dict:
        """Get sequence metrics for time range."""
        sql_filter = f"WHERE discovered_at > datetime('now', '{config.sql_modifier}')" \
                     if config.sql_modifier else ""
        
        result = self.db.execute_query(f"""
            SELECT 
                COUNT(*) as total_sequences,
                COUNT(DISTINCT game_id) as unique_games,
                AVG(total_actions) as avg_actions,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_count
            FROM winning_sequences
            {sql_filter}
        """)
        return result[0] if result else {}
    
    def _collect_generational(self) -> Dict[str, Any]:
        """Collect per-generation metrics."""
        result = self.db.execute_query("""
            SELECT 
                generation,
                COUNT(DISTINCT agent_id) as active_agents,
                SUM(games_played) as total_games,
                SUM(games_won) as total_wins,
                AVG(avg_score) as avg_score
            FROM generation_stats
            GROUP BY generation
            ORDER BY generation DESC
            LIMIT 50
        """)
        return {
            'time_range': 'By Generation',
            'generations': result or [],
            'collected_at': datetime.now().isoformat(),
        }
```

#### Dashboard Time Range UI

```python
# In health_dashboard.py - add to layout

def _setup_layout(self):
    """Create dashboard layout with time range controls."""
    self.app.layout = html.Div([
        html.H1("Ouroboros System Health Dashboard"),
        
        # TIME RANGE CONTROLS
        html.Div([
            # Tabs for main time ranges
            dcc.Tabs(id='time-range-tabs', value='real_time', children=[
                dcc.Tab(label='Real-Time', value='real_time'),
                dcc.Tab(label='Last 24h', value='24h'),
                dcc.Tab(label='Last 7 Days', value='7d'),
                dcc.Tab(label='By Generation', value='generational'),
            ]),
            
            # Dropdown for granular control
            html.Div([
                html.Label("Detailed Range:"),
                dcc.Dropdown(
                    id='time-range-dropdown',
                    options=[
                        {'label': 'Real-Time (30s refresh)', 'value': 'real_time'},
                        {'label': 'Last Hour', 'value': '1h'},
                        {'label': 'Last 24 Hours', 'value': '24h'},
                        {'label': 'Last 7 Days', 'value': '7d'},
                        {'label': 'By Generation', 'value': 'generational'},
                        {'label': 'All History', 'value': 'all'},
                    ],
                    value='real_time',
                    style={'width': '200px'}
                ),
            ], style={'display': 'inline-block', 'marginLeft': '20px'}),
        ], style={'marginBottom': '20px'}),
        
        # Dynamic refresh interval based on time range
        dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0),
        
        # ... rest of dashboard components
    ])

@self.app.callback(
    Output('interval-component', 'interval'),
    [Input('time-range-dropdown', 'value')]
)
def update_refresh_interval(time_range):
    """Adjust refresh rate based on selected time range."""
    config = TIME_RANGE_CONFIGS.get(TimeRange(time_range))
    return config.refresh_interval_ms if config else 30000
```

#### New Package: `dashboards/`

```
dashboards/
├── __init__.py
├── health_dashboard.py      # Main dashboard server
├── metrics_collector.py     # Background metrics collection
├── time_range_collector.py  # Time-range-aware metrics
├── alert_manager.py         # Alert generation and management
├── dashboard_config.py      # Configuration
└── templates/
    └── dashboard.html       # Custom template (optional)
```

### G.5 Comprehensive Metrics (30-50 Total)

Full metric catalog organized into 7 categories with 40+ metrics total.

```python
@dataclass
class ComprehensiveHealthMetrics:
    """
    Complete system health snapshot - 42 metrics across 7 categories.
    
    Categories:
    1. API/Connectivity (5 metrics)
    2. Sequence Health (8 metrics)
    3. Agent Population (7 metrics)
    4. Knowledge/Learning (6 metrics)
    5. Communication (6 metrics) - viral packages, pariahs
    6. Performance (5 metrics)
    7. System Resources (5 metrics)
    """
    timestamp: datetime
    time_range: str
    
    # =========================================================================
    # CATEGORY 1: API/CONNECTIVITY (5 metrics) - HIGHEST PRIORITY
    # =========================================================================
    api_connection_status: str           # 'healthy', 'degraded', 'down'
    api_response_time_ms: float          # Average response time
    api_error_rate_1h: float             # % of API calls failing
    api_rate_limit_remaining: int        # Requests remaining before limit
    api_last_successful_call: datetime   # When API last worked
    
    # =========================================================================
    # CATEGORY 2: SEQUENCE HEALTH (8 metrics)
    # =========================================================================
    total_active_sequences: int
    sequences_discovered_period: int     # In current time range
    sequence_success_rate: float         # % of replays that succeed
    stale_sequences_count: int           # Not used in 7+ days
    high_failure_sequences: int          # >3 consecutive failures
    sequence_diversity_gini: float       # 0=equal, 1=concentrated
    full_game_sequences: int             # Holy grail sequences
    avg_sequence_actions: float          # Efficiency metric
    
    # =========================================================================
    # CATEGORY 3: AGENT POPULATION (7 metrics)
    # =========================================================================
    total_active_agents: int
    pioneer_count: int
    optimizer_count: int
    generalist_count: int
    exploiter_count: int
    agents_stuck_count: int              # No progress in 1+ hour
    avg_agent_age_generations: float     # Average agent lifespan
    
    # =========================================================================
    # CATEGORY 4: KNOWLEDGE/LEARNING (6 metrics)
    # =========================================================================
    unique_game_types_beaten: int        # Games with at least 1 win
    games_fully_optimized: int           # Games at optimization saturation
    patterns_discovered_period: int      # New patterns in time range
    rules_learned_period: int            # New rules in time range
    avg_prestige_score: float
    prestige_gini: float                 # Prestige distribution inequality
    
    # =========================================================================
    # CATEGORY 5: COMMUNICATION (6 metrics) - Viral + Pariahs
    # =========================================================================
    active_viral_packages: int           # Currently spreading
    viral_propagations_period: int       # Spreads in time range
    endangered_packages: int             # <3 carriers
    active_pariahs: int                  # Failure patterns being avoided
    pariah_creations_period: int         # New pariahs in time range
    knowledge_transfer_rate: float       # Packages/pariahs per generation
    
    # =========================================================================
    # CATEGORY 6: PERFORMANCE (5 metrics)
    # =========================================================================
    games_played_period: int             # Games in time range
    games_won_period: int                # Wins in time range
    win_rate_period: float               # Win % in time range
    avg_score_period: float              # Average game score
    actions_per_win_avg: float           # Efficiency metric
    
    # =========================================================================
    # CATEGORY 7: SYSTEM RESOURCES (5 metrics)
    # =========================================================================
    database_size_mb: float
    database_growth_rate_mb_day: float   # MB per day
    pending_cleanup_records: int         # Records eligible for cleanup
    last_cleanup_at: datetime
    memory_usage_mb: float               # Current process memory


class ComprehensiveMetricsCollector:
    """Collects all 42 metrics."""
    
    def __init__(self, db: DatabaseInterface, api_client: Optional[ARCAPIClient] = None):
        self.db = db
        self.api = api_client
    
    def collect_all(self, time_range: TimeRange = TimeRange.REAL_TIME) -> ComprehensiveHealthMetrics:
        """Collect comprehensive metrics snapshot."""
        config = TIME_RANGE_CONFIGS[time_range]
        
        return ComprehensiveHealthMetrics(
            timestamp=datetime.now(),
            time_range=config.display_name,
            
            # Category 1: API
            **self._collect_api_metrics(),
            
            # Category 2: Sequences
            **self._collect_sequence_metrics(config),
            
            # Category 3: Agents
            **self._collect_agent_metrics(),
            
            # Category 4: Knowledge
            **self._collect_knowledge_metrics(config),
            
            # Category 5: Communication
            **self._collect_communication_metrics(config),
            
            # Category 6: Performance
            **self._collect_performance_metrics(config),
            
            # Category 7: Resources
            **self._collect_resource_metrics(),
        )
    
    def _collect_api_metrics(self) -> Dict[str, Any]:
        """Collect API health metrics."""
        # Check API status
        status = 'healthy'
        response_time = 0.0
        
        if self.api:
            try:
                start = datetime.now()
                response = self.api.health_check()
                response_time = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 429:
                    status = 'degraded'
                elif response.status_code >= 400:
                    status = 'down'
            except Exception:
                status = 'down'
                response_time = -1
        
        return {
            'api_connection_status': status,
            'api_response_time_ms': response_time,
            'api_error_rate_1h': self._get_api_error_rate(),
            'api_rate_limit_remaining': 1000,  # Would need API header parsing
            'api_last_successful_call': self._get_last_api_success(),
        }
    
    def _collect_communication_metrics(self, config: TimeRangeConfig) -> Dict[str, Any]:
        """Collect viral package and pariah communication metrics."""
        sql_filter = f"AND created_at > datetime('now', '{config.sql_modifier}')" \
                     if config.sql_modifier else ""
        
        viral_result = self.db.execute_query(f"""
            SELECT 
                COUNT(*) as active_packages,
                SUM(times_spread) as total_spreads
            FROM viral_packages 
            WHERE is_active = 1 {sql_filter}
        """)
        
        endangered = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM viral_packages vp
            LEFT JOIN viral_package_carriers vpc 
              ON vp.package_id = vpc.package_id AND vpc.is_active = 1
            WHERE vp.is_active = 1
            GROUP BY vp.package_id
            HAVING COUNT(vpc.agent_id) < 3
        """)
        
        pariah_result = self.db.execute_query(f"""
            SELECT COUNT(*) as active_pariahs
            FROM pariahs WHERE is_active = 1 {sql_filter}
        """)
        
        return {
            'active_viral_packages': viral_result[0]['active_packages'] if viral_result else 0,
            'viral_propagations_period': viral_result[0]['total_spreads'] if viral_result else 0,
            'endangered_packages': len(endangered) if endangered else 0,
            'active_pariahs': pariah_result[0]['active_pariahs'] if pariah_result else 0,
            'pariah_creations_period': self._count_new_pariahs(config),
            'knowledge_transfer_rate': self._calculate_transfer_rate(config),
        }
```

### G.6 Communication Metrics Detail (Viral Packages + Pariahs)

Viral packages and pariahs are forms of network communication - knowledge spreading laterally between agents.

```python
@dataclass
class CommunicationMetrics:
    """
    Detailed metrics for inter-agent communication.
    
    Per Master Ruleset: "Horizontal Gene Transfer = Knowledge sharing between 
    unrelated agents. Viral Packages = Successful strategies spread like 
    actual viruses. Pariahs = Failure patterns marked for network avoidance."
    """
    
    # VIRAL PACKAGES (Positive Knowledge Transfer)
    active_viral_packages: int           # Currently active packages
    packages_created_period: int         # New packages in time range
    packages_spread_count: int           # Total propagation events
    avg_package_carriers: float          # Average agents per package
    endangered_packages: int             # <3 carriers, risk of death
    package_success_rate: float          # % of packages leading to wins
    most_successful_package: str         # Package with highest wins
    package_type_distribution: Dict[str, int]  # By game type
    
    # PARIAHS (Negative Knowledge Transfer)
    active_pariahs: int                  # Currently active pariahs
    pariahs_created_period: int          # New pariahs in time range
    agents_avoiding_pariahs: int         # Agents with pariah awareness
    pariah_effectiveness: float          # % reduction in failed actions
    most_avoided_pariah: str             # Most referenced pariah
    pariah_type_distribution: Dict[str, int]  # By failure type
    
    # NETWORK HEALTH
    knowledge_flow_rate: float           # Packages + pariahs per hour
    network_connectivity: float          # % of agents sharing knowledge
    communication_diversity: float       # Variety of info types shared
    isolated_agents: int                 # Agents with no packages/pariahs


class CommunicationMetricsCollector:
    """Collects detailed communication metrics."""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
    
    def collect_communication_health(self, time_range: TimeRange) -> CommunicationMetrics:
        """Collect full communication metrics."""
        config = TIME_RANGE_CONFIGS[time_range]
        
        return CommunicationMetrics(
            # Viral packages
            **self._collect_viral_metrics(config),
            # Pariahs
            **self._collect_pariah_metrics(config),
            # Network health
            **self._collect_network_health(config),
        )
    
    def _collect_viral_metrics(self, config: TimeRangeConfig) -> Dict[str, Any]:
        """Collect viral package metrics."""
        sql_filter = f"AND created_at > datetime('now', '{config.sql_modifier}')" \
                     if config.sql_modifier else ""
        
        # Active packages
        active = self.db.execute_query("""
            SELECT COUNT(*) as count FROM viral_packages WHERE is_active = 1
        """)
        
        # Packages created in period
        created = self.db.execute_query(f"""
            SELECT COUNT(*) as count 
            FROM viral_packages 
            WHERE 1=1 {sql_filter}
        """)
        
        # Average carriers per package
        avg_carriers = self.db.execute_query("""
            SELECT AVG(carrier_count) as avg
            FROM (
                SELECT vp.package_id, COUNT(vpc.agent_id) as carrier_count
                FROM viral_packages vp
                LEFT JOIN viral_package_carriers vpc 
                  ON vp.package_id = vpc.package_id AND vpc.is_active = 1
                WHERE vp.is_active = 1
                GROUP BY vp.package_id
            )
        """)
        
        # Endangered packages (<3 carriers)
        endangered = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM (
                SELECT vp.package_id, COUNT(vpc.agent_id) as carrier_count
                FROM viral_packages vp
                LEFT JOIN viral_package_carriers vpc 
                  ON vp.package_id = vpc.package_id AND vpc.is_active = 1
                WHERE vp.is_active = 1
                GROUP BY vp.package_id
                HAVING carrier_count < 3
            )
        """)
        
        # Package type distribution
        distribution = self.db.execute_query("""
            SELECT 
                SUBSTR(game_id, 1, 4) as game_type,
                COUNT(*) as count
            FROM viral_packages
            WHERE is_active = 1
            GROUP BY game_type
        """)
        
        return {
            'active_viral_packages': active[0]['count'] if active else 0,
            'packages_created_period': created[0]['count'] if created else 0,
            'packages_spread_count': self._count_spreads(config),
            'avg_package_carriers': avg_carriers[0]['avg'] if avg_carriers else 0.0,
            'endangered_packages': endangered[0]['count'] if endangered else 0,
            'package_success_rate': self._calc_package_success_rate(),
            'most_successful_package': self._get_top_package(),
            'package_type_distribution': {r['game_type']: r['count'] for r in distribution} if distribution else {},
        }
    
    def _collect_pariah_metrics(self, config: TimeRangeConfig) -> Dict[str, Any]:
        """Collect pariah metrics."""
        sql_filter = f"AND created_at > datetime('now', '{config.sql_modifier}')" \
                     if config.sql_modifier else ""
        
        active = self.db.execute_query("""
            SELECT COUNT(*) as count FROM pariahs WHERE is_active = 1
        """)
        
        created = self.db.execute_query(f"""
            SELECT COUNT(*) as count FROM pariahs WHERE 1=1 {sql_filter}
        """)
        
        # Agents that have at least one pariah reference
        aware_agents = self.db.execute_query("""
            SELECT COUNT(DISTINCT agent_id) as count
            FROM agent_pariah_awareness
            WHERE is_active = 1
        """)
        
        return {
            'active_pariahs': active[0]['count'] if active else 0,
            'pariahs_created_period': created[0]['count'] if created else 0,
            'agents_avoiding_pariahs': aware_agents[0]['count'] if aware_agents else 0,
            'pariah_effectiveness': self._calc_pariah_effectiveness(),
            'most_avoided_pariah': self._get_top_pariah(),
            'pariah_type_distribution': self._get_pariah_distribution(),
        }
    
    def _collect_network_health(self, config: TimeRangeConfig) -> Dict[str, Any]:
        """Collect overall network communication health."""
        # Knowledge flow = packages + pariahs created per hour
        flow = self.db.execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM viral_packages 
                 WHERE created_at > datetime('now', '-1 hour')) +
                (SELECT COUNT(*) FROM pariahs 
                 WHERE created_at > datetime('now', '-1 hour')) as flow_rate
        """)
        
        # Network connectivity = % of agents with at least 1 package OR pariah
        connectivity = self.db.execute_query("""
            SELECT 
                (SELECT COUNT(DISTINCT agent_id) FROM viral_package_carriers WHERE is_active = 1) * 1.0 /
                NULLIF((SELECT COUNT(*) FROM agents WHERE is_active = 1), 0) as connectivity
        """)
        
        # Isolated agents = active agents with no packages and no pariah awareness
        isolated = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM agents a
            WHERE a.is_active = 1
              AND NOT EXISTS (SELECT 1 FROM viral_package_carriers vpc 
                              WHERE vpc.agent_id = a.agent_id AND vpc.is_active = 1)
              AND NOT EXISTS (SELECT 1 FROM agent_pariah_awareness apa 
                              WHERE apa.agent_id = a.agent_id AND apa.is_active = 1)
        """)
        
        return {
            'knowledge_flow_rate': flow[0]['flow_rate'] if flow else 0.0,
            'network_connectivity': connectivity[0]['connectivity'] if connectivity else 0.0,
            'communication_diversity': self._calc_comm_diversity(),
            'isolated_agents': isolated[0]['count'] if isolated else 0,
        }
```

#### Dashboard Communication Panel

```python
# In health_dashboard.py - Communication visualization

def _create_communication_panel(self, metrics: CommunicationMetrics) -> html.Div:
    """Create communication health visualization panel."""
    return html.Div([
        html.H3("Network Communication Health"),
        
        # Two-column layout: Viral Packages | Pariahs
        html.Div([
            # Left: Viral Packages
            html.Div([
                html.H4("Viral Packages (Positive Knowledge)"),
                html.Table([
                    html.Tr([html.Td("Active Packages"), 
                             html.Td(str(metrics.active_viral_packages))]),
                    html.Tr([html.Td("Avg Carriers"), 
                             html.Td(f"{metrics.avg_package_carriers:.1f}")]),
                    html.Tr([html.Td("Endangered"), 
                             html.Td(str(metrics.endangered_packages), 
                                    style={'color': 'red' if metrics.endangered_packages > 5 else 'inherit'})]),
                    html.Tr([html.Td("Success Rate"), 
                             html.Td(f"{metrics.package_success_rate:.1%}")]),
                ]),
                # Package distribution chart
                dcc.Graph(
                    figure=px.pie(
                        values=list(metrics.package_type_distribution.values()),
                        names=list(metrics.package_type_distribution.keys()),
                        title="By Game Type"
                    )
                )
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            # Right: Pariahs
            html.Div([
                html.H4("Pariahs (Failure Avoidance)"),
                html.Table([
                    html.Tr([html.Td("Active Pariahs"), 
                             html.Td(str(metrics.active_pariahs))]),
                    html.Tr([html.Td("Agents Avoiding"), 
                             html.Td(str(metrics.agents_avoiding_pariahs))]),
                    html.Tr([html.Td("Effectiveness"), 
                             html.Td(f"{metrics.pariah_effectiveness:.1%}")]),
                    html.Tr([html.Td("Most Avoided"), 
                             html.Td(metrics.most_avoided_pariah or "N/A")]),
                ]),
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ]),
        
        # Bottom: Network health gauge
        html.Div([
            html.H4("Network Connectivity"),
            dcc.Graph(
                figure=go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=metrics.network_connectivity * 100,
                    title={'text': "% Agents Connected"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': 'green' if metrics.network_connectivity > 0.7 else 'orange'},
                        'steps': [
                            {'range': [0, 50], 'color': 'red'},
                            {'range': [50, 80], 'color': 'yellow'},
                            {'range': [80, 100], 'color': 'lightgreen'}
                        ]
                    }
                ))
            ),
            html.P(f"Isolated Agents: {metrics.isolated_agents}", 
                   style={'color': 'red' if metrics.isolated_agents > 5 else 'inherit'})
        ])
    ])
```
    
    # Failure Cascade Risk
    consecutive_zero_score_games: int
    sequence_failure_rate_24h: float
    agents_stuck_same_level: int
    cascade_risk_score: float  # 0-1, computed from above
    
    # Innovation Stagnation
    new_sequences_24h: int
    new_sequences_7d: int
    sequence_discovery_rate: float  # sequences per generation
    generations_since_breakthrough: int
    stagnation_score: float  # 0-1, computed from above
    
    # Population Dynamics
    active_agents: int
    pioneer_ratio: float
    optimizer_ratio: float
    generalist_ratio: float
    exploiter_ratio: float
    avg_agent_prestige: float
    prestige_gini: float  # 0=equal, 1=all prestige in one agent


class MetricsCollector:
    """Collects system health metrics from database."""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
    
    def collect_snapshot(self) -> HealthMetrics:
        """Collect all metrics for current moment."""
        return HealthMetrics(
            timestamp=datetime.now(),
            
            # Knowledge Diversity
            unique_game_types_with_sequences=self._count_unique_game_types(),
            sequence_concentration_gini=self._calculate_sequence_gini(),
            viral_package_diversity=self._calculate_viral_diversity(),
            pariah_coverage=self._calculate_pariah_coverage(),
            
            # Failure Cascade
            consecutive_zero_score_games=self._count_consecutive_zeros(),
            sequence_failure_rate_24h=self._calculate_failure_rate(hours=24),
            agents_stuck_same_level=self._count_stuck_agents(),
            cascade_risk_score=self._compute_cascade_risk(),
            
            # Innovation
            new_sequences_24h=self._count_new_sequences(hours=24),
            new_sequences_7d=self._count_new_sequences(hours=168),
            sequence_discovery_rate=self._calculate_discovery_rate(),
            generations_since_breakthrough=self._generations_since_breakthrough(),
            stagnation_score=self._compute_stagnation_score(),
            
            # Population
            active_agents=self._count_active_agents(),
            pioneer_ratio=self._get_role_ratio('pioneer'),
            optimizer_ratio=self._get_role_ratio('optimizer'),
            generalist_ratio=self._get_role_ratio('generalist'),
            exploiter_ratio=self._get_role_ratio('exploiter'),
            avg_agent_prestige=self._avg_prestige(),
            prestige_gini=self._calculate_prestige_gini()
        )
    
    # =========================================================================
    # KNOWLEDGE DIVERSITY METRICS
    # =========================================================================
    
    def _count_unique_game_types(self) -> int:
        """Count unique game types with at least one sequence."""
        result = self.db.execute_query("""
            SELECT COUNT(DISTINCT SUBSTR(game_id, 1, 4)) as count
            FROM winning_sequences WHERE is_active = 1
        """)
        return result[0]['count'] if result else 0
    
    def _calculate_sequence_gini(self) -> float:
        """
        Calculate Gini coefficient for sequence distribution across games.
        
        Gini = 0: Perfectly equal (same # sequences per game)
        Gini = 1: Perfectly unequal (all sequences in one game)
        """
        counts = self.db.execute_query("""
            SELECT SUBSTR(game_id, 1, 4) as game_type, COUNT(*) as count
            FROM winning_sequences WHERE is_active = 1
            GROUP BY game_type
        """)
        
        if not counts:
            return 0.0
        
        values = sorted([c['count'] for c in counts])
        n = len(values)
        if n == 0:
            return 0.0
        
        # Gini calculation
        cumsum = sum((i + 1) * v for i, v in enumerate(values))
        return (2 * cumsum) / (n * sum(values)) - (n + 1) / n
    
    def _calculate_viral_diversity(self) -> float:
        """Ratio of unique viral packages to total possible."""
        result = self.db.execute_query("""
            SELECT 
                COUNT(DISTINCT package_id) as unique_packages,
                COUNT(DISTINCT SUBSTR(game_id, 1, 4)) as game_types
            FROM viral_packages WHERE is_active = 1
        """)
        if not result or result[0]['game_types'] == 0:
            return 0.0
        return min(1.0, result[0]['unique_packages'] / (result[0]['game_types'] * 10))
    
    # =========================================================================
    # FAILURE CASCADE METRICS
    # =========================================================================
    
    def _count_consecutive_zeros(self) -> int:
        """Count consecutive zero-score games (recent)."""
        result = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM (
                SELECT final_score, 
                       ROW_NUMBER() OVER (ORDER BY completed_at DESC) as rn
                FROM game_results
                WHERE completed_at > datetime('now', '-1 hour')
            )
            WHERE final_score = 0 AND rn <= 100
        """)
        return result[0]['count'] if result else 0
    
    def _compute_cascade_risk(self) -> float:
        """
        Compute failure cascade risk score (0-1).
        
        High risk indicators:
        - Many consecutive zeros
        - High sequence failure rate
        - Many stuck agents
        """
        zeros = self._count_consecutive_zeros()
        failure_rate = self._calculate_failure_rate(hours=24)
        stuck = self._count_stuck_agents()
        
        # Weighted combination
        risk = (
            min(1.0, zeros / 20) * 0.3 +      # 20+ consecutive zeros = max
            failure_rate * 0.4 +               # Direct failure rate
            min(1.0, stuck / 10) * 0.3         # 10+ stuck agents = max
        )
        return min(1.0, risk)
    
    # =========================================================================
    # INNOVATION STAGNATION METRICS
    # =========================================================================
    
    def _count_new_sequences(self, hours: int) -> int:
        """Count sequences discovered in last N hours."""
        result = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM winning_sequences
            WHERE discovered_at > datetime('now', ?)
        """, (f'-{hours} hours',))
        return result[0]['count'] if result else 0
    
    def _generations_since_breakthrough(self) -> int:
        """Count generations since last new game type was beaten."""
        result = self.db.execute_query("""
            SELECT MAX(generation) as last_gen
            FROM winning_sequences
            WHERE is_first_for_game = 1
        """)
        
        current_gen = self.db.execute_query("""
            SELECT MAX(generation) as gen FROM generation_stats
        """)
        
        if not result or not current_gen:
            return 0
        
        last = result[0]['last_gen'] or 0
        current = current_gen[0]['gen'] or 0
        return max(0, current - last)
    
    def _compute_stagnation_score(self) -> float:
        """
        Compute innovation stagnation score (0-1).
        
        High stagnation indicators:
        - Few new sequences recently
        - Many generations since breakthrough
        - Low discovery rate
        """
        new_24h = self._count_new_sequences(hours=24)
        new_7d = self._count_new_sequences(hours=168)
        gens_since = self._generations_since_breakthrough()
        
        # Stagnation factors
        recency_factor = max(0, 1 - (new_24h / 10))  # <10 new/day = stagnating
        trend_factor = max(0, 1 - (new_7d / 50))     # <50 new/week = stagnating
        breakthrough_factor = min(1, gens_since / 50) # 50+ gens = max stagnation
        
        return (recency_factor * 0.4 + trend_factor * 0.3 + breakthrough_factor * 0.3)
```

#### Dashboard Server

```python
# dashboards/health_dashboard.py
"""
System Health Dashboard - Real-time visualization.

Uses Plotly Dash to create an interactive dashboard showing:
- Knowledge diversity trends
- Failure cascade risk gauge
- Innovation stagnation timeline
- Agent population dynamics
"""

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from .metrics_collector import MetricsCollector, HealthMetrics

class HealthDashboard:
    """Plotly Dash dashboard for system health monitoring."""
    
    def __init__(self, db: DatabaseInterface, port: int = 8050):
        self.db = db
        self.collector = MetricsCollector(db)
        self.port = port
        self.app = dash.Dash(__name__)
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):
        """Create dashboard layout."""
        self.app.layout = html.Div([
            html.H1("Ouroboros System Health Dashboard", 
                   style={'textAlign': 'center'}),
            
            # Auto-refresh every 30 seconds
            dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0),
            
            # Top row: Risk gauges
            html.Div([
                html.Div([
                    html.H3("Failure Cascade Risk"),
                    dcc.Graph(id='cascade-gauge')
                ], style={'width': '33%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3("Innovation Stagnation"),
                    dcc.Graph(id='stagnation-gauge')
                ], style={'width': '33%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3("Knowledge Diversity"),
                    dcc.Graph(id='diversity-gauge')
                ], style={'width': '33%', 'display': 'inline-block'}),
            ]),
            
            # Middle row: Time series
            html.Div([
                html.Div([
                    html.H3("Sequence Discovery Rate"),
                    dcc.Graph(id='discovery-timeline')
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3("Agent Population Dynamics"),
                    dcc.Graph(id='population-chart')
                ], style={'width': '50%', 'display': 'inline-block'}),
            ]),
            
            # Bottom row: Detailed metrics
            html.Div([
                html.H3("Key Metrics"),
                html.Table(id='metrics-table')
            ])
        ])
    
    def _setup_callbacks(self):
        """Setup dashboard callbacks for real-time updates."""
        
        @self.app.callback(
            [Output('cascade-gauge', 'figure'),
             Output('stagnation-gauge', 'figure'),
             Output('diversity-gauge', 'figure'),
             Output('discovery-timeline', 'figure'),
             Output('population-chart', 'figure'),
             Output('metrics-table', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            metrics = self.collector.collect_snapshot()
            
            # Cascade Risk Gauge
            cascade_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=metrics.cascade_risk_score * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': self._risk_color(metrics.cascade_risk_score)},
                    'steps': [
                        {'range': [0, 30], 'color': 'lightgreen'},
                        {'range': [30, 70], 'color': 'yellow'},
                        {'range': [70, 100], 'color': 'red'}
                    ]
                }
            ))
            
            # Stagnation Gauge
            stagnation_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=metrics.stagnation_score * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': self._risk_color(metrics.stagnation_score)},
                    'steps': [
                        {'range': [0, 30], 'color': 'lightgreen'},
                        {'range': [30, 70], 'color': 'yellow'},
                        {'range': [70, 100], 'color': 'red'}
                    ]
                }
            ))
            
            # Diversity Gauge (inverted - higher is better)
            diversity_score = 1 - metrics.sequence_concentration_gini
            diversity_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=diversity_score * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': self._health_color(diversity_score)},
                    'steps': [
                        {'range': [0, 30], 'color': 'red'},
                        {'range': [30, 70], 'color': 'yellow'},
                        {'range': [70, 100], 'color': 'lightgreen'}
                    ]
                }
            ))
            
            # Discovery Timeline (mock historical data for now)
            discovery_fig = self._create_discovery_timeline()
            
            # Population Chart
            population_fig = go.Figure(data=[
                go.Bar(name='Pioneer', x=['Current'], y=[metrics.pioneer_ratio * 100]),
                go.Bar(name='Optimizer', x=['Current'], y=[metrics.optimizer_ratio * 100]),
                go.Bar(name='Generalist', x=['Current'], y=[metrics.generalist_ratio * 100]),
                go.Bar(name='Exploiter', x=['Current'], y=[metrics.exploiter_ratio * 100]),
            ])
            population_fig.update_layout(barmode='stack')
            
            # Metrics Table
            table = self._create_metrics_table(metrics)
            
            return cascade_fig, stagnation_fig, diversity_fig, discovery_fig, population_fig, table
    
    def _risk_color(self, score: float) -> str:
        """Get color for risk score."""
        if score < 0.3:
            return 'green'
        elif score < 0.7:
            return 'orange'
        return 'red'
    
    def _health_color(self, score: float) -> str:
        """Get color for health score (inverted from risk)."""
        if score > 0.7:
            return 'green'
        elif score > 0.3:
            return 'orange'
        return 'red'
    
    def _create_metrics_table(self, metrics: HealthMetrics) -> html.Table:
        """Create HTML table of key metrics."""
        rows = [
            ('Active Agents', metrics.active_agents),
            ('New Sequences (24h)', metrics.new_sequences_24h),
            ('New Sequences (7d)', metrics.new_sequences_7d),
            ('Unique Game Types', metrics.unique_game_types_with_sequences),
            ('Avg Agent Prestige', f"{metrics.avg_agent_prestige:.2f}"),
            ('Prestige Gini', f"{metrics.prestige_gini:.3f}"),
            ('Stuck Agents', metrics.agents_stuck_same_level),
            ('Gens Since Breakthrough', metrics.generations_since_breakthrough),
        ]
        
        return html.Table([
            html.Tr([html.Th('Metric'), html.Th('Value')])
        ] + [
            html.Tr([html.Td(name), html.Td(str(value))])
            for name, value in rows
        ])
    
    def run(self, debug: bool = False):
        """Start the dashboard server."""
        print(f"[DASHBOARD] Starting health dashboard on http://localhost:{self.port}")
        self.app.run_server(debug=debug, port=self.port)
```

#### Integration

```python
# In autonomous_evolution_runner.py or as standalone script

# Option 1: Background thread
import threading

def start_dashboard_background(db: DatabaseInterface):
    """Start dashboard in background thread."""
    from dashboards.health_dashboard import HealthDashboard
    dashboard = HealthDashboard(db)
    thread = threading.Thread(target=dashboard.run, daemon=True)
    thread.start()
    return thread

# Option 2: Standalone script (run_dashboard.py)
if __name__ == "__main__":
    from database_interface import DatabaseInterface
    from dashboards.health_dashboard import HealthDashboard
    
    db = DatabaseInterface("core_data.db")
    dashboard = HealthDashboard(db, port=8050)
    dashboard.run(debug=True)
```

#### Dependencies to Add

```
# requirements.txt additions
dash>=2.14.0
plotly>=5.18.0
pandas>=2.0.0  # For data manipulation in dashboard
```

---

## Appendix H: Refactoring Infrastructure (From Feedback Review)

### H.1 Dependency Injection Strategy

**Problem**: Modules take `db: DatabaseInterface` but complex dependencies need cleaner injection.

**Solution**: Use a simple container pattern (not over-engineered DI framework):

```python
# core_gameplay/container.py
"""
Dependency Container - Simple DI without framework overhead.

Provides lazy initialization of shared dependencies.
"""

from typing import Optional
from functools import cached_property

class GameplayContainer:
    """Holds all shared dependencies for the gameplay system."""
    
    def __init__(self, db_path: str = "core_data.db", api_key: Optional[str] = None):
        self._db_path = db_path
        self._api_key = api_key
    
    @cached_property
    def db(self) -> 'DatabaseInterface':
        from database_interface import DatabaseInterface
        return DatabaseInterface(self._db_path)
    
    @cached_property
    def api_client(self) -> 'ARCAPIClient':
        from arc_api_client import ARCAPIClient
        return ARCAPIClient(self._api_key)
    
    @cached_property
    def session_manager(self) -> 'GameSessionManager':
        from game_session_manager import GameSessionManager
        return GameSessionManager(self.api_client)
    
    @cached_property
    def sequence_manager(self) -> 'SequenceManager':
        from .sequence_manager import SequenceManager
        return SequenceManager(self.db)
    
    @cached_property
    def action_selector(self) -> 'ActionSelector':
        from .action_selection import ActionSelector
        return ActionSelector(self.db, self.sequence_manager)
    
    # For testing: allow injection of mocks
    def with_db(self, mock_db) -> 'GameplayContainer':
        """Create container with mocked database."""
        container = GameplayContainer.__new__(GameplayContainer)
        container._db_path = self._db_path
        container._api_key = self._api_key
        container.__dict__['db'] = mock_db  # Bypass cached_property
        return container


# Usage in engine.py:
class GameplayEngine:
    def __init__(self, container: Optional[GameplayContainer] = None):
        self.container = container or GameplayContainer()
        self.db = self.container.db
        self.sequence_manager = self.container.sequence_manager
```

### H.2 Error Recovery & Transaction Boundaries

**Problem**: What happens when operations fail mid-way?

**Solution**: Define atomic operations and recovery strategies:

```python
# core_gameplay/transactions.py
"""
Transaction boundaries for atomic operations.

Operations that MUST be atomic (all-or-nothing):
1. Sequence storage (all fields or none)
2. Agent creation with initial state
3. Viral package propagation to multiple agents

Operations that can be partial:
1. Game loop actions (each action independent)
2. Metrics collection (missing data is acceptable)
3. Pattern learning (best-effort)
"""

from contextlib import contextmanager
from typing import Generator

@contextmanager
def atomic_sequence_storage(db: DatabaseInterface) -> Generator[None, None, None]:
    """
    Ensure sequence storage is atomic.
    
    If any part fails, the entire sequence is not stored.
    """
    try:
        db.execute_query("BEGIN TRANSACTION")
        yield
        db.execute_query("COMMIT")
    except Exception as e:
        db.execute_query("ROLLBACK")
        raise SequenceStorageError(f"Atomic storage failed: {e}") from e


class SequenceStorageError(Exception):
    """Raised when sequence storage fails atomically."""
    pass


# Recovery strategies for mid-operation failures:
RECOVERY_STRATEGIES = {
    'replay_sequence_failed': 'flag_sequence_and_try_next',
    'api_timeout': 'retry_with_backoff_then_skip_game',
    'database_locked': 'wait_and_retry_3_times',
    'partial_level_completion': 'save_progress_continue_next_gen',
}
```

### H.3 Centralized Configuration

**Problem**: Thresholds scattered across code, hard to tune.

**Solution**: Single configuration module:

```python
# core_gameplay/config.py
"""
Centralized configuration for all gameplay parameters.

All tunable thresholds in one place for easy adjustment.
"""

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class SequenceConfig:
    """Sequence matching and storage thresholds."""
    min_frame_similarity: float = 0.95
    max_sequences_per_game: int = 50
    diversity_threshold: int = 10
    success_rate_floor: float = 0.30
    consecutive_failures_limit: int = 3
    stale_sequence_days: int = 30

@dataclass
class ActionConfig:
    """Action selection weights and limits."""
    default_actions_per_level: int = 400
    default_actions_per_game: int = 7000
    exploration_weight: float = 0.3
    exploitation_weight: float = 0.7
    viral_package_bonus: float = 0.2
    pariah_penalty: float = 0.5

@dataclass  
class APIConfig:
    """API client configuration."""
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    rate_limit_wait: int = 60

@dataclass
class GameplayConfig:
    """Master configuration combining all sub-configs."""
    sequence: SequenceConfig = field(default_factory=SequenceConfig)
    action: ActionConfig = field(default_factory=ActionConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'GameplayConfig':
        """Load configuration from dictionary (e.g., from JSON/YAML)."""
        return cls(
            sequence=SequenceConfig(**config_dict.get('sequence', {})),
            action=ActionConfig(**config_dict.get('action', {})),
            api=APIConfig(**config_dict.get('api', {})),
        )


# Global default config (can be overridden)
DEFAULT_CONFIG = GameplayConfig()
```

### H.4 Circular Import Prevention

**Problem**: `engine.py → game_loop.py → sequence_manager → ...` creates import web.

**Solution**: Strict import hierarchy with types module at bottom:

```
IMPORT HIERARCHY (top imports from bottom, never reverse):

Level 4 (Top):     engine.py
                      ↓
Level 3:           game_loop.py
                      ↓
Level 2:    sequence_replay.py, action_selection.py, agent_tracking.py
                      ↓
Level 1:    sequence_manager.py, frame_analysis.py, pattern_learning.py
                      ↓
Level 0 (Bottom):  types.py, config.py (NO imports from core_gameplay/)
```

**Rules**:
1. `types.py` and `config.py` import ONLY from stdlib and external packages
2. Level 1 modules import only from Level 0
3. Each level imports only from levels below it
4. Use TYPE_CHECKING for type hints that would cause circular imports:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import GameplayEngine  # Only for type hints, not runtime
```

### H.5 Game State Machine

**Problem**: `GameLoopState` dataclass doesn't clearly show valid state transitions.

**Solution**: Explicit state machine for game execution:

```python
# core_gameplay/state_machine.py
"""
Game State Machine - Clear state transitions during gameplay.
"""

from enum import Enum, auto
from typing import Optional, Set
from dataclasses import dataclass

class GameState(Enum):
    """Valid states during game execution."""
    INITIALIZING = auto()    # Setting up game session
    REPLAYING = auto()       # Replaying stored sequence
    EXPLORING = auto()       # Exploring new actions
    STUCK = auto()           # No progress detected
    LEVEL_COMPLETE = auto()  # Just completed a level
    GAME_WON = auto()        # All levels completed
    GAME_OVER = auto()       # Failed (budget exhausted, error, etc.)


# Valid transitions: {from_state: {valid_to_states}}
VALID_TRANSITIONS: dict[GameState, Set[GameState]] = {
    GameState.INITIALIZING: {GameState.REPLAYING, GameState.EXPLORING, GameState.GAME_OVER},
    GameState.REPLAYING: {GameState.EXPLORING, GameState.LEVEL_COMPLETE, GameState.GAME_OVER},
    GameState.EXPLORING: {GameState.STUCK, GameState.LEVEL_COMPLETE, GameState.GAME_OVER},
    GameState.STUCK: {GameState.EXPLORING, GameState.GAME_OVER},
    GameState.LEVEL_COMPLETE: {GameState.REPLAYING, GameState.EXPLORING, GameState.GAME_WON},
    GameState.GAME_WON: set(),  # Terminal state
    GameState.GAME_OVER: set(),  # Terminal state
}


@dataclass
class GameStateMachine:
    """Manages game state transitions with validation."""
    
    current_state: GameState = GameState.INITIALIZING
    state_history: list = None
    
    def __post_init__(self):
        self.state_history = [(self.current_state, None)]
    
    def transition_to(self, new_state: GameState, reason: Optional[str] = None) -> bool:
        """
        Attempt state transition.
        
        Returns True if transition valid, False otherwise.
        Raises InvalidTransitionError if transition not allowed.
        """
        valid_targets = VALID_TRANSITIONS.get(self.current_state, set())
        
        if new_state not in valid_targets:
            raise InvalidTransitionError(
                f"Cannot transition from {self.current_state.name} to {new_state.name}. "
                f"Valid targets: {[s.name for s in valid_targets]}"
            )
        
        self.state_history.append((new_state, reason))
        self.current_state = new_state
        return True
    
    def is_terminal(self) -> bool:
        """Check if current state is terminal (game ended)."""
        return self.current_state in {GameState.GAME_WON, GameState.GAME_OVER}
    
    def can_transition_to(self, state: GameState) -> bool:
        """Check if transition to state is valid."""
        return state in VALID_TRANSITIONS.get(self.current_state, set())


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass
```

### H.6 Metrics Collection Hooks

**Problem**: Appendix G defines metrics but not where they're collected in refactored modules.

**Solution**: Decorator-based metrics collection:

```python
# core_gameplay/metrics_hooks.py
"""
Metrics collection hooks for refactored modules.

Use decorators to collect metrics without cluttering business logic.
"""

import time
from functools import wraps
from typing import Callable, Any

# Global metrics collector (injected at startup)
_metrics_collector = None

def set_metrics_collector(collector):
    """Set the global metrics collector."""
    global _metrics_collector
    _metrics_collector = collector


def track_timing(metric_name: str):
    """Decorator to track method execution time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start
                if _metrics_collector:
                    _metrics_collector.record_timing(metric_name, elapsed)
        return wrapper
    return decorator


def track_count(metric_name: str, on_success: bool = True):
    """Decorator to count method calls."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                if _metrics_collector and on_success:
                    _metrics_collector.increment(metric_name)
                return result
            except Exception:
                if _metrics_collector and not on_success:
                    _metrics_collector.increment(f"{metric_name}_failed")
                raise
        return wrapper
    return decorator


# Usage in modules:
class SequenceManager:
    
    @track_timing("sequence_storage_time")
    @track_count("sequences_stored")
    def capture_sequence(self, ...):
        ...
    
    @track_timing("sequence_retrieval_time")
    def get_best_sequence(self, ...):
        ...


class SequenceReplayer:
    
    @track_timing("sequence_replay_time")
    @track_count("replay_attempts")
    def replay_sequence(self, ...):
        ...
```

### H.7 Error Tracking by Role and Game Type

**Addition to Appendix G metrics:**

```python
@dataclass
class ErrorMetrics:
    """Error tracking sorted by description, role, and game type."""
    
    # Errors by description (most frequent first)
    errors_by_type: Dict[str, int]  # {"API_TIMEOUT": 15, "SEQUENCE_NOT_FOUND": 8, ...}
    
    # Errors by agent role
    errors_by_role: Dict[str, Dict[str, int]]  # {"pioneer": {"API_TIMEOUT": 5}, ...}
    
    # Errors by game type
    errors_by_game_type: Dict[str, Dict[str, int]]  # {"ft09": {"STUCK": 3}, ...}
    
    # Combined view: role + game_type + error_type → count
    error_breakdown: List[Dict[str, Any]]


class ErrorMetricsCollector:
    """Collects error metrics for dashboard."""
    
    def collect_error_breakdown(self, time_range: TimeRange) -> ErrorMetrics:
        """Get errors broken down by all dimensions."""
        config = TIME_RANGE_CONFIGS[time_range]
        sql_filter = f"AND logged_at > datetime('now', '{config.sql_modifier}')" \
                     if config.sql_modifier else ""
        
        # Errors by type
        by_type = self.db.execute_query(f"""
            SELECT error_type, COUNT(*) as count
            FROM gameplay_errors
            WHERE 1=1 {sql_filter}
            GROUP BY error_type
            ORDER BY count DESC
        """)
        
        # Errors by role
        by_role = self.db.execute_query(f"""
            SELECT agent_role, error_type, COUNT(*) as count
            FROM gameplay_errors ge
            JOIN agents a ON ge.agent_id = a.agent_id
            WHERE 1=1 {sql_filter}
            GROUP BY agent_role, error_type
            ORDER BY count DESC
        """)
        
        # Errors by game type
        by_game = self.db.execute_query(f"""
            SELECT SUBSTR(game_id, 1, 4) as game_type, error_type, COUNT(*) as count
            FROM gameplay_errors
            WHERE 1=1 {sql_filter}
            GROUP BY game_type, error_type
            ORDER BY count DESC
        """)
        
        return ErrorMetrics(
            errors_by_type={r['error_type']: r['count'] for r in by_type},
            errors_by_role=self._pivot_by_role(by_role),
            errors_by_game_type=self._pivot_by_game(by_game),
            error_breakdown=list(by_role) + list(by_game),
        )


# New table for error tracking:
"""
CREATE TABLE gameplay_errors (
    error_id TEXT PRIMARY KEY,
    agent_id TEXT,
    game_id TEXT,
    error_type TEXT NOT NULL,
    error_message TEXT,
    stack_trace TEXT,
    logged_at TEXT NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE INDEX idx_errors_type ON gameplay_errors(error_type, logged_at);
CREATE INDEX idx_errors_agent ON gameplay_errors(agent_id, logged_at);
CREATE INDEX idx_errors_game ON gameplay_errors(game_id, logged_at);
"""
```

### H.8 Integration Testing Strategy

**Problem**: Unit tests per module ≠ system works.

**Solution**: Multi-level test strategy:

```python
# tests/test_strategy.py
"""
Test Strategy for Core Gameplay Refactoring

THREE LEVELS OF TESTING:

1. UNIT TESTS (per module)
   - Mock all dependencies
   - Test single method behavior
   - Fast, run on every commit
   - Location: tests/unit/

2. INTEGRATION TESTS (module interactions)
   - Real database (in-memory SQLite)
   - Mock API client only
   - Test module boundaries work together
   - Location: tests/integration/

3. END-TO-END TESTS (full system)
   - Real database
   - Real API (test environment or recorded responses)
   - Play actual games
   - Slow, run before release
   - Location: tests/e2e/
"""

# Example test fixtures:

import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_db():
    """Mock database for unit tests."""
    db = MagicMock(spec=DatabaseInterface)
    db.execute_query.return_value = []
    return db

@pytest.fixture
def memory_db():
    """In-memory SQLite for integration tests."""
    db = DatabaseInterface(":memory:")
    db.execute_query(open("complete_database_schema.sql").read())
    return db

@pytest.fixture
def test_container(memory_db):
    """Container with real DB, mock API."""
    container = GameplayContainer()
    container = container.with_db(memory_db)
    container.api_client = MagicMock(spec=ARCAPIClient)
    return container


# Example integration test:

class TestSequenceReplayIntegration:
    """Integration tests for sequence replay with real DB."""
    
    def test_replay_updates_reputation(self, test_container):
        """Replaying sequence should update its reputation."""
        # Arrange: Store a sequence
        seq_manager = test_container.sequence_manager
        seq_id = seq_manager.capture_sequence(
            game_id="test-game",
            score=1.0,
            level_number=1,
            actions=[1, 2, 3],
            initial_frame=[[0]*64]*64,
            action_coordinates=[],
        )
        
        # Act: Record successful replay
        seq_manager.record_validation_attempt(
            sequence_id=seq_id,
            success=True,
            reached_level=1,
            expected_level=1,
        )
        
        # Assert: Reputation increased
        reputation = seq_manager.get_sequence_reputation(seq_id)
        assert reputation['success_rate'] > 0


# Example E2E test:

class TestFullGameE2E:
    """End-to-end tests playing real games."""
    
    @pytest.mark.slow
    @pytest.mark.e2e
    def test_can_complete_known_game(self, real_api_key):
        """Agent should be able to complete a known solvable game."""
        engine = GameplayEngine(api_key=real_api_key)
        
        # Play a game known to be solvable
        result = await engine.play_single_game(
            game_url="https://three.arcprize.org/api/play/known-solvable-123"
        )
        
        assert result['win'] == True
        assert result['actions_taken'] < 1000  # Reasonable action count
```

---

## Appendix I: Additional Considerations

### I.1 Logging Strategy

**Problem**: Refactored modules need consistent logging that follows Master Ruleset Rule #2 (database-only logging).

**Solution**: Inject logger via container, trace sessions across modules:

```python
# core_gameplay/logging_setup.py
"""
Logging setup for refactored modules.

All logs go to database via DatabaseLogHandler per Master Ruleset.
"""

import logging
from database_logger import DatabaseLogHandler

def get_module_logger(module_name: str, db: 'DatabaseInterface') -> logging.Logger:
    """
    Get a logger for a specific module.
    
    All loggers use DatabaseLogHandler - NO file handlers.
    """
    logger = logging.getLogger(f"core_gameplay.{module_name}")
    
    if not logger.handlers:
        handler = DatabaseLogHandler(db)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '[%(name)s] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


class SessionTracer:
    """
    Traces a game session across multiple modules.
    
    Adds session_id to all log entries for correlation.
    """
    
    def __init__(self, session_id: str, db: 'DatabaseInterface'):
        self.session_id = session_id
        self.db = db
    
    def log(self, module: str, level: str, message: str, **extra):
        """Log with session context."""
        self.db.execute_query("""
            INSERT INTO system_logs (
                log_level, logger_name, message, session_id, extra_data, logged_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (level, f"core_gameplay.{module}", message, self.session_id, str(extra)))
```

**Log Levels by Module**:
| Module | Default Level | Rationale |
|--------|---------------|-----------|
| `engine.py` | INFO | High-level orchestration |
| `game_loop.py` | DEBUG | Detailed action tracking |
| `sequence_manager.py` | INFO | Storage/retrieval events |
| `sequence_replay.py` | DEBUG | Replay step-by-step |
| `action_selection.py` | DEBUG | Decision tracing |
| `frame_analysis.py` | WARNING | Only log anomalies |
| `pattern_learning.py` | INFO | Pattern discoveries |

### I.2 Async/Await Consistency

**Problem**: Mixed sync/async methods need clear boundaries.

**Solution**: Define module async status:

```python
# ASYNC MODULES (I/O-bound, API calls):
# - engine.py           → async play_single_game(), play_multiple_games()
# - game_loop.py        → async run(), execute_single_action()
# - sequence_replay.py  → async replay_sequence(), execute_3_try_fallback()
# - action_selection.py → async select_action() (may call API for subgoals)

# SYNC MODULES (CPU-bound, database):
# - sequence_manager.py → sync (database queries are fast)
# - frame_analysis.py   → sync (CPU-bound calculations)
# - pattern_learning.py → sync (database + CPU)
# - agent_tracking.py   → sync (database queries)
# - viral_evolution.py  → sync (database queries)
# - types.py, config.py → sync (no I/O)
```

**Calling Sync from Async**:
```python
# In async modules, call sync methods directly (they don't block event loop long):
async def play_single_game(self, ...):
    # OK: sync database call is fast
    sequence = self.sequence_manager.get_best_sequence(game_id)
    
    # OK: sync frame analysis is CPU-bound but fast
    similarity = self.frame_analyzer.calculate_similarity(frame_a, frame_b)
```

**Calling Async from Sync** (avoid if possible):
```python
# If absolutely needed, use asyncio.run() but prefer restructuring
import asyncio

def sync_wrapper():
    return asyncio.run(async_function())
```

### I.3 Rollback Plan

**Problem**: If refactoring breaks production, need quick recovery.

**Strategy**: Phased rollout with fallback:

```python
# Phase 1: Keep old core_gameplay.py as core_gameplay_legacy.py
# Phase 2: New imports with feature flag

# In autonomous_evolution_runner.py:
USE_REFACTORED_GAMEPLAY = False  # Feature flag

if USE_REFACTORED_GAMEPLAY:
    from core_gameplay.engine import GameplayEngine
else:
    from core_gameplay_legacy import GameplayEngine  # Original file

# Phase 3: After 1 week stable, remove legacy
# Phase 4: Delete core_gameplay_legacy.py
```

**Rollback Checklist**:
1. Set `USE_REFACTORED_GAMEPLAY = False`
2. Restart evolution runner
3. Verify games playing with legacy engine
4. Investigate refactored code issues
5. Fix and re-enable when ready

### I.4 Performance Baseline

**Problem**: No metrics to compare before/after refactoring.

**Solution**: Capture baseline before starting:

```python
# manual_tools/capture_performance_baseline.py
"""
Run before refactoring to establish performance baseline.

Metrics to capture:
1. Games per hour (throughput)
2. Average game duration
3. Memory usage during gameplay
4. Database query times
5. Sequence retrieval latency
"""

import time
import psutil
from database_interface import DatabaseInterface

def capture_baseline(db: DatabaseInterface) -> dict:
    """Capture current performance metrics."""
    
    # Games per hour (last 24h)
    result = db.execute_query("""
        SELECT COUNT(*) as count
        FROM game_results
        WHERE completed_at > datetime('now', '-24 hours')
    """)
    games_24h = result[0]['count'] if result else 0
    
    # Average game duration
    result = db.execute_query("""
        SELECT AVG(duration_seconds) as avg_duration
        FROM game_results
        WHERE completed_at > datetime('now', '-24 hours')
    """)
    avg_duration = result[0]['avg_duration'] if result else 0
    
    # Current memory usage
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    # Database size
    import os
    db_size_mb = os.path.getsize("core_data.db") / 1024 / 1024
    
    baseline = {
        'captured_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'games_per_hour': games_24h / 24,
        'avg_game_duration_seconds': avg_duration,
        'memory_usage_mb': memory_mb,
        'database_size_mb': db_size_mb,
    }
    
    print("=== PERFORMANCE BASELINE ===")
    for k, v in baseline.items():
        print(f"  {k}: {v}")
    
    return baseline
```

**Target After Refactoring**:
| Metric | Baseline | Target | Rationale |
|--------|----------|--------|-----------|
| Games/hour | (capture) | Same or better | No regression |
| Memory usage | (capture) | -10% or same | Cleaner code = less overhead |
| Avg game duration | (capture) | Same | No change to logic |
| Startup time | (capture) | Same or faster | Lazy loading |

### I.5 Edge Case Ownership Matrix

**Problem**: Which module handles edge cases?

| Edge Case | Owner Module | Handling Strategy |
|-----------|--------------|-------------------|
| Game session expires mid-replay | `sequence_replay.py` | Catch API error, flag sequence, return to game_loop |
| Agent deactivated while playing | `game_loop.py` | Check agent status before each action, graceful exit |
| Database locked during storage | `sequence_manager.py` | Retry 3x with backoff, then skip storage |
| API rate limited | `engine.py` | Wait per APIConfig.rate_limit_wait, then retry |
| Frame mismatch during replay | `sequence_replay.py` | Flag sequence, try next in fallback |
| Zero valid actions available | `action_selection.py` | Return random action, log warning |
| Sequence storage fails | `sequence_manager.py` | Raise SequenceStorageError, game_loop catches |
| Pattern learning OOM | `pattern_learning.py` | Catch MemoryError, skip pattern, log warning |

---

## Appendix J: Blue Sky Recommendations (Future Database Changes)

> **NOTE**: These require database schema changes and should be implemented AFTER the core refactoring is stable. Do NOT implement during initial refactoring.

### J.1 System Alerts Table (For G.3 Alert System)

```sql
-- FUTURE: Add when implementing full alert system
CREATE TABLE system_alerts (
    alert_id TEXT PRIMARY KEY,
    severity TEXT NOT NULL,
    fault_type TEXT NOT NULL,
    description TEXT,
    suggested_action TEXT,
    created_at TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    acknowledged_by TEXT,
    resolved INTEGER DEFAULT 0,
    resolution_action TEXT,
    auto_recoverable INTEGER DEFAULT 0
);

CREATE INDEX idx_alerts_severity ON system_alerts(severity, resolved);
CREATE INDEX idx_alerts_created ON system_alerts(created_at);
```

### J.2 Gameplay Errors Table (For H.7 Error Tracking)

```sql
-- FUTURE: Add when implementing error tracking dashboard
CREATE TABLE gameplay_errors (
    error_id TEXT PRIMARY KEY,
    agent_id TEXT,
    game_id TEXT,
    error_type TEXT NOT NULL,
    error_message TEXT,
    stack_trace TEXT,
    logged_at TEXT NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE INDEX idx_errors_type ON gameplay_errors(error_type, logged_at);
CREATE INDEX idx_errors_agent ON gameplay_errors(agent_id, logged_at);
CREATE INDEX idx_errors_game ON gameplay_errors(game_id, logged_at);
```

### J.3 Viral Package Carriers Table (For Appendix E)

```sql
-- FUTURE: Add when implementing viral propagation guardian
CREATE TABLE viral_package_carriers (
    package_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    PRIMARY KEY (package_id, agent_id),
    FOREIGN KEY (package_id) REFERENCES viral_packages(package_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE INDEX idx_viral_carriers_package ON viral_package_carriers(package_id, is_active);
```

### J.4 Metrics History Table (For Dashboard Historical Views)

```sql
-- FUTURE: Add when implementing time-range dashboard views
CREATE TABLE metrics_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    captured_at TEXT NOT NULL,
    generation INTEGER,
    metrics_json TEXT NOT NULL,  -- JSON blob of all metrics
    snapshot_type TEXT DEFAULT 'hourly'  -- 'hourly', 'daily', 'generational'
);

CREATE INDEX idx_metrics_time ON metrics_snapshots(captured_at, snapshot_type);
CREATE INDEX idx_metrics_gen ON metrics_snapshots(generation);
```

### J.5 Agent Pariah Awareness Table (For G.6 Communication)

```sql
-- FUTURE: Add when implementing detailed pariah tracking
CREATE TABLE agent_pariah_awareness (
    agent_id TEXT NOT NULL,
    pariah_id TEXT NOT NULL,
    learned_at TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    avoidance_count INTEGER DEFAULT 0,
    PRIMARY KEY (agent_id, pariah_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (pariah_id) REFERENCES pariahs(pariah_id)
);

CREATE INDEX idx_pariah_awareness_agent ON agent_pariah_awareness(agent_id, is_active);
```

---

**Last Updated**: December 4, 2025  
**Author**: GitHub Copilot  
**Status**: PLANNING PHASE + AUDIT COMPLETE + ORPHAN DECISIONS MADE + NEW FEATURES PLANNED
