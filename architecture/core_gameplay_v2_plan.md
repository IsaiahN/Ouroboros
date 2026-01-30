# Core Gameplay v2.0 Implementation Plan
**Date**: January 29, 2026  
**Purpose**: Clean, modular replacement for the 30,000-line core_gameplay_legacy.py  
**Key Change**: Uses new `arc_agi` SDK instead of custom HTTP client

---

## Overview

The legacy `core_gameplay.py` grew to **30,328 lines** because it mixed:
- API communication
- Game loop orchestration
- Action selection (42 decision features)
- Learning/memory systems
- Agent self-model
- Exploration tracking
- Terminal pattern detection
- ...and 50+ other concerns

**v2.0 GOAL**: Split into **7 focused modules** with clear interfaces.

---

## New Module Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          ENTRY POINT                                     │
│                      core_gameplay.py (~300 lines)                       │
│                                                                          │
│  - GameplayEngine class (thin orchestrator)                              │
│  - Configuration loading                                                 │
│  - Main entry points: play_single_game(), run_session()                  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐
│  arc_api_adapter  │  │   game_loop.py    │  │  decision_rung_system.py  │
│    (~200 lines)   │  │   (~500 lines)    │  │      (already exists)     │
│                   │  │                   │  │                           │
│ - ArcadeWrapper   │  │ - GameLoop class  │  │ - 42 Decision Rungs       │
│ - Uses arc_agi SDK│  │ - State machine   │  │ - Swappable orderings     │
│ - Scorecard mgmt  │  │ - Level handling  │  │ - Primitive integration   │
│ - Game discovery  │  │ - Budget tracking │  │                           │
└─────────┬─────────┘  └─────────┬─────────┘  └─────────────┬─────────────┘
          │                      │                          │
          └──────────────────────┼──────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐
│ learning_systems  │  │   context_builder │  │     outcome_processor     │
│    (~400 lines)   │  │    (~300 lines)   │  │       (~200 lines)        │
│                   │  │                   │  │                           │
│ - Coordinates:    │  │ - Builds context  │  │ - Process step results    │
│   - CODS engine   │  │   for rungs       │  │ - Record outcomes         │
│   - Replay learn  │  │ - Frame analysis  │  │ - Trigger learning        │
│   - Primitives    │  │ - Position track  │  │ - Death/win handling      │
│   - Self-model    │  │ - Safety weights  │  │                           │
└───────────────────┘  └───────────────────┘  └───────────────────────────┘
```

---

## Module Specifications

### 1. `arc_api_adapter.py` (~200 lines) - NEW

**Purpose**: Wrapper around the official `arc_agi` SDK

**Key Classes**:
```python
@dataclass
class GameConfig:
    """Configuration for a game session."""
    game_id: str
    seed: int = 0
    scorecard_id: Optional[str] = None
    save_recording: bool = False
    render_mode: Optional[str] = None  # "terminal", "human", None
    operation_mode: str = "NORMAL"  # NORMAL, OFFLINE, ONLINE

class ArcadeWrapper:
    """
    Thin wrapper around arc_agi.Arcade.
    
    Provides:
    - Consistent interface for our system
    - Automatic scorecard management
    - Game state translation to our types
    """
    
    def __init__(self, api_key: Optional[str] = None, operation_mode: str = "NORMAL"):
        from arc_agi import Arcade, OperationMode
        self.arcade = Arcade(
            arc_api_key=api_key,
            operation_mode=OperationMode[operation_mode]
        )
    
    def list_games(self) -> List[GameInfo]:
        """Get all available games."""
        return [GameInfo.from_env(e) for e in self.arcade.get_environments()]
    
    def create_environment(self, config: GameConfig) -> GameEnvironment:
        """Create a game environment."""
        env = self.arcade.make(
            config.game_id,
            seed=config.seed,
            scorecard_id=config.scorecard_id,
            save_recording=config.save_recording,
            render_mode=config.render_mode
        )
        return GameEnvironment(env)
    
    def get_scorecard(self) -> Optional[Scorecard]:
        """Get current scorecard results."""
        return self.arcade.get_scorecard()
    
    def close_scorecard(self) -> Optional[Scorecard]:
        """Close and finalize current scorecard."""
        return self.arcade.close_scorecard()
```

**Dependencies**: 
- `arc_agi` (official SDK)
- `arcengine` (game types)

---

### 2. `game_loop.py` (~500 lines) - NEW

**Purpose**: Game loop state machine and level orchestration

**Key Classes**:
```python
@dataclass
class LoopState:
    """Current state of the game loop."""
    game_id: str
    current_level: int
    action_count: int
    total_actions: int
    score: float
    state: GameState  # NOT_PLAYED, NOT_FINISHED, WIN, GAME_OVER
    frame: Optional[List[List[int]]]
    budget_used_percent: float
    phase: str  # "orientation", "hypothesis", "exploitation"

class GameLoop:
    """
    Manages the game loop state machine.
    
    States:
    - STARTING: Initialize environment
    - PLAYING: Main game loop
    - LEVEL_COMPLETE: Handle level transition
    - GAME_WON: Full game victory
    - GAME_OVER: Death/failure
    - FINISHED: Cleanup
    """
    
    def __init__(
        self,
        env: GameEnvironment,
        decision_system: DecisionRungSystem,
        context_builder: ContextBuilder,
        outcome_processor: OutcomeProcessor,
        learning_systems: LearningSystems,
    ):
        ...
    
    async def run(self, max_actions: int = 2000) -> GameResult:
        """Run the complete game loop."""
        state = await self._initialize()
        
        while not self._is_terminal(state):
            # 1. Build decision context
            context = self.context_builder.build(state)
            
            # 2. Get action from decision system
            action, reason = self.decision_system.decide(state.observation, context)
            
            # 3. Execute action
            observation = await self._execute(action, reason)
            
            # 4. Process outcome
            outcome = self.outcome_processor.process(state, action, observation)
            
            # 5. Update learning systems
            self.learning_systems.update(state, action, outcome)
            
            # 6. Update state
            state = self._update_state(state, observation, outcome)
        
        return self._build_result(state)
```

**Key Features**:
- Clean state machine (no 1500-line methods!)
- Pluggable components
- Budget tracking (orientation/hypothesis/exploitation phases)
- Level transition handling

---

### 3. `context_builder.py` (~300 lines) - NEW

**Purpose**: Build the context dict that decision rungs need

**Key Class**:
```python
class ContextBuilder:
    """
    Builds context for the decision rung system.
    
    Extracts and packages all the state that decision rungs need:
    - Game identification
    - Agent info (ID, role, w_A/w_B weights)
    - Position tracking
    - Safety weights from danger detection
    - Recent actions history
    - Exploration stats
    - CODS context
    """
    
    def __init__(
        self,
        db: DatabaseInterface,
        exploration_tracker: Optional[NetworkExplorationTracker] = None,
        terminal_detector: Optional[TerminalPatternDetector] = None,
    ):
        ...
    
    def build(self, loop_state: LoopState, agent_config: Dict) -> Dict[str, Any]:
        """Build complete context for decision making."""
        return {
            # Game context
            'game_id': loop_state.game_id,
            'game_type': loop_state.game_id[:4],
            'level': loop_state.current_level,
            'score': loop_state.score,
            
            # Budget context
            'action_count': loop_state.action_count,
            'budget_used_percent': loop_state.budget_used_percent,
            'phase': loop_state.phase,
            
            # Agent context
            'agent_id': agent_config.get('agent_id'),
            'w_A': agent_config.get('w_A', 0.5),
            'w_B': agent_config.get('w_B', 0.5),
            
            # Position & safety
            'agent_position': self._get_agent_position(loop_state.frame),
            'action_safety_weights': self._get_safety_weights(loop_state),
            
            # History
            'recent_actions': self._recent_actions[-10:],
            
            # Exploration
            'is_frontier': self._is_frontier(loop_state),
            'exploration_coverage': self._get_coverage(loop_state),
            
            # CODS
            'cods_context': self._build_cods_context(loop_state),
        }
```

---

### 4. `outcome_processor.py` (~200 lines) - NEW

**Purpose**: Process the result of each action

**Key Class**:
```python
@dataclass
class ActionOutcome:
    """Result of taking an action."""
    action: str
    frame_changed: bool
    score_changed: bool
    score_delta: float
    is_death: bool
    is_level_complete: bool
    is_game_win: bool
    position_delta: Optional[Tuple[int, int]]
    new_state: GameState

class OutcomeProcessor:
    """
    Process action outcomes and trigger appropriate responses.
    
    Responsibilities:
    - Detect frame changes
    - Detect score changes
    - Detect deaths (game_over)
    - Detect level completions
    - Detect full game wins
    - Record outcomes for learning
    """
    
    def __init__(self, db: DatabaseInterface):
        ...
    
    def process(
        self,
        before_state: LoopState,
        action: str,
        observation: FrameDataRaw
    ) -> ActionOutcome:
        """Process the outcome of an action."""
        frame_changed = self._detect_frame_change(before_state.frame, observation.frame)
        score_changed = observation.score != before_state.score
        
        return ActionOutcome(
            action=action,
            frame_changed=frame_changed,
            score_changed=score_changed,
            score_delta=observation.score - before_state.score,
            is_death=observation.state == GameState.GAME_OVER,
            is_level_complete=score_changed and observation.state != GameState.GAME_OVER,
            is_game_win=observation.state == GameState.WIN,
            position_delta=self._detect_movement(before_state.frame, observation.frame),
            new_state=observation.state,
        )
    
    def record(self, outcome: ActionOutcome, context: Dict) -> None:
        """Record outcome to database for learning."""
        ...
```

---

### 5. `learning_systems.py` (~400 lines) - NEW

**Purpose**: Coordinate all learning/memory systems

**Key Class**:
```python
class LearningSystems:
    """
    Coordinator for all learning and memory systems.
    
    Instead of 50+ imports in one file, this provides a clean interface
    to all learning capabilities:
    - CODS (Cognitive Operator Discovery System)
    - Replay Learning
    - Sequence Mining
    - Self-Model updates
    - Terminal Pattern recording
    - Network knowledge synthesis
    """
    
    def __init__(
        self,
        db: DatabaseInterface,
        cods_engine: Optional[CODSEngine] = None,
        replay_engine: Optional[ReplayLearningEngine] = None,
        self_model: Optional[AgentSelfModel] = None,
        terminal_detector: Optional[TerminalPatternDetector] = None,
    ):
        self.db = db
        self.cods = cods_engine
        self.replay = replay_engine
        self.self_model = self_model
        self.terminal = terminal_detector
    
    def update(
        self,
        state: LoopState,
        action: str,
        outcome: ActionOutcome
    ) -> None:
        """Update all learning systems with new experience."""
        
        # 1. Update self-model with control observations
        if self.self_model and outcome.position_delta:
            self.self_model.record_movement_observation(
                action=action,
                delta=outcome.position_delta,
                frame=state.frame
            )
        
        # 2. Record terminal pattern if death
        if self.terminal and outcome.is_death:
            self.terminal.record_death(
                game_type=state.game_id[:4],
                level=state.current_level,
                action=action,
                frame=state.frame
            )
        
        # 3. Update CODS with frame transition
        if self.cods:
            self.cods.observe_transition(
                frame_before=state.frame,
                frame_after=outcome.new_frame,
                action=action
            )
        
        # 4. Trigger replay learning on win
        if self.replay and outcome.is_game_win:
            self.replay.learn_from_win(state.game_id)
    
    def on_game_start(self, game_id: str, agent_id: str) -> None:
        """Initialize learning systems for new game."""
        ...
    
    def on_game_end(self, result: GameResult) -> None:
        """Finalize learning from completed game."""
        ...
```

---

### 6. `core_gameplay.py` (~300 lines) - MAIN ENTRY POINT

**Purpose**: Thin orchestrator that wires everything together

```python
"""
Core Gameplay v2.0 - Clean, Modular Game Engine
===============================================

This is the main entry point for playing ARC-AGI-3 games.

Architecture:
- arc_api_adapter.py: Wraps the arc_agi SDK
- game_loop.py: Game loop state machine
- decision_rung_system.py: Modular 42-rung decision system
- context_builder.py: Build context for decisions
- outcome_processor.py: Process action results
- learning_systems.py: Coordinate all learning

Usage:
    engine = GameplayEngine()
    result = await engine.play_single_game("ls20", agent_config)
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from database_interface import DatabaseInterface
from arc_api_adapter import ArcadeWrapper, GameConfig
from game_loop import GameLoop, LoopState
from decision_rung_system import DecisionRungSystem, ORDERING_PRESETS
from context_builder import ContextBuilder
from outcome_processor import OutcomeProcessor
from learning_systems import LearningSystems


@dataclass
class GameResult:
    """Result of a complete game."""
    game_id: str
    final_score: float
    levels_completed: int
    total_actions: int
    is_win: bool
    sequence: Optional[List[str]]  # Winning sequence if any


class GameplayEngine:
    """
    Main entry point for ARC-AGI-3 gameplay.
    
    This is a thin orchestrator that wires together:
    - API adapter (arc_agi SDK wrapper)
    - Game loop (state machine)
    - Decision system (42 modular rungs)
    - Learning systems (CODS, replay, self-model)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        db_path: str = "core_data.db",
        decision_ordering: str = "efficiency",
        operation_mode: str = "NORMAL",
    ):
        # Database
        self.db = DatabaseInterface(db_path)
        
        # API adapter
        self.api = ArcadeWrapper(api_key, operation_mode)
        
        # Decision system
        self.decision_system = DecisionRungSystem(strategy='ladder')
        self.decision_system.load_ordering(decision_ordering)
        
        # Context builder
        self.context_builder = ContextBuilder(self.db)
        
        # Outcome processor
        self.outcome_processor = OutcomeProcessor(self.db)
        
        # Learning systems (lazy loaded)
        self._learning_systems = None
    
    @property
    def learning_systems(self) -> LearningSystems:
        """Lazy-load learning systems."""
        if self._learning_systems is None:
            self._learning_systems = LearningSystems(
                db=self.db,
                # Other components loaded on demand
            )
        return self._learning_systems
    
    async def play_single_game(
        self,
        game_id: str,
        agent_config: Optional[Dict[str, Any]] = None,
        max_actions: int = 2000,
        render_mode: Optional[str] = None,
    ) -> GameResult:
        """
        Play a single game.
        
        Args:
            game_id: Game identifier (e.g., "ls20")
            agent_config: Agent configuration (id, role, weights)
            max_actions: Maximum actions allowed
            render_mode: "terminal", "human", or None
        
        Returns:
            GameResult with final score and sequence
        """
        agent_config = agent_config or {}
        
        # Create game config
        config = GameConfig(
            game_id=game_id,
            render_mode=render_mode,
        )
        
        # Create environment
        env = self.api.create_environment(config)
        
        # Initialize learning systems for this game
        self.learning_systems.on_game_start(game_id, agent_config.get('agent_id'))
        
        # Create game loop
        loop = GameLoop(
            env=env,
            decision_system=self.decision_system,
            context_builder=self.context_builder,
            outcome_processor=self.outcome_processor,
            learning_systems=self.learning_systems,
        )
        
        # Run the game
        result = await loop.run(max_actions=max_actions)
        
        # Finalize learning
        self.learning_systems.on_game_end(result)
        
        return result
    
    def list_games(self) -> List[str]:
        """List all available games."""
        return [g.game_id for g in self.api.list_games()]
    
    def get_scorecard(self):
        """Get current scorecard."""
        return self.api.get_scorecard()
```

---

## Migration Path

### Phase 1: Create New Files (No Breaking Changes)
1. Create `arc_api_adapter.py` - wraps arc_agi SDK
2. Create `game_loop.py` - game loop state machine
3. Create `context_builder.py` - context building
4. Create `outcome_processor.py` - outcome processing
5. Create `learning_systems.py` - learning coordinator
6. Create new `core_gameplay.py` - thin orchestrator

### Phase 2: Parallel Testing
1. Run both old and new systems on same games
2. Compare results (actions chosen, scores achieved)
3. Fix any divergences

### Phase 3: Gradual Migration
1. Update `autonomous_evolution_runner.py` to use new system
2. Update other consumers one by one
3. Keep `core_gameplay_legacy.py` for rollback

### Phase 4: Cleanup
1. Remove `core_gameplay_legacy.py` once stable
2. Update all imports
3. Archive migration docs

---

## Key Design Principles

### 1. Single Responsibility
Each file does ONE thing:
- `arc_api_adapter.py` - API communication
- `game_loop.py` - Loop orchestration
- `decision_rung_system.py` - Action selection
- `context_builder.py` - Context building
- `outcome_processor.py` - Outcome processing
- `learning_systems.py` - Learning coordination

### 2. Dependency Injection
Components receive dependencies, don't create them:
```python
# GOOD: Injected
loop = GameLoop(env, decision_system, ...)

# BAD: Created internally
class GameLoop:
    def __init__(self):
        self.decision = DecisionRungSystem()  # NO!
```

### 3. Clean Interfaces
Each component has a minimal, well-defined interface:
```python
# Decision system interface
action, reason = decision_system.decide(observation, context)

# Outcome processor interface
outcome = processor.process(before_state, action, observation)

# Learning systems interface
learning.update(state, action, outcome)
```

### 4. No 1500-Line Methods
The legacy `_select_action()` was 1500+ lines. In v2.0:
- Decision logic is 42 separate rungs (~50-100 lines each)
- Game loop is a simple state machine (~100 lines)
- Context building is extracted to its own file (~300 lines)

### 5. Gradual Learning System Loading
Learning systems are lazy-loaded to avoid import hell:
```python
@property
def learning_systems(self):
    if self._learning_systems is None:
        self._learning_systems = LearningSystems(...)
    return self._learning_systems
```

---

## File Summary

| File | Lines | Purpose |
|------|-------|---------|
| `core_gameplay.py` | ~300 | Main entry point, orchestrator |
| `arc_api_adapter.py` | ~200 | Wraps arc_agi SDK |
| `game_loop.py` | ~500 | Game loop state machine |
| `context_builder.py` | ~300 | Builds decision context |
| `outcome_processor.py` | ~200 | Processes action outcomes |
| `learning_systems.py` | ~400 | Coordinates learning |
| `decision_rung_system.py` | ~2500 | 42 decision rungs (already exists) |
| **TOTAL** | **~4400** | vs 30,328 in legacy |

**86% reduction in main module complexity** while maintaining all functionality.

---

## Implementation Order

1. **`arc_api_adapter.py`** - Foundation, wraps new SDK
2. **`outcome_processor.py`** - Simple, no dependencies
3. **`context_builder.py`** - Needs DB, builds on outcome
4. **`learning_systems.py`** - Coordinates existing engines
5. **`game_loop.py`** - Needs all of above
6. **`core_gameplay.py`** - Final orchestrator

---

## Questions to Resolve

1. **Async vs Sync**: Keep async for API calls? The arc_agi SDK appears sync.
2. **Database Interface**: Keep existing `DatabaseInterface` or simplify?
3. **Event Bus**: Keep the existing event bus system?
4. **Persona System**: Include in v2.0 or defer?
5. **Spine Emitter**: Keep telemetry or simplify?

---

**END OF IMPLEMENTATION PLAN**
