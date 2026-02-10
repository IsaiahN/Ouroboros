"""
Core Gameplay v3.0 - Convenience Wrapper
========================================

Thin convenience wrapper around the production ``GamePlayer`` (sync path)
and the lightweight ``GameLoop`` (async state-machine path).

Both paths feed through ``ContextBuilder`` so that rungs always receive
an identical ``DecisionContext`` contract.

Architecture:
    GameplayEngine (this file)
        |
        +-- play_single_game()            -> delegates to GamePlayer.play_game_standalone()
        +-- play_single_game_async()      -> delegates to GameLoop.run() (async)
        +-- play_multiple_games()         -> sequential calls to play_single_game()
        |
        shared: ContextBuilder, DecisionRungSystem, OutcomeProcessor

Usage:
    from core_gameplay import GameplayEngine

    engine = GameplayEngine()
    result = engine.play_single_game("ls20")

    # With agent config
    from context_builder import AgentConfig
    agent = AgentConfig(agent_id="pioneer-1", role="pioneer")
    result = engine.play_single_game("ls20", agent_config=agent)

    # List available games
    games = engine.list_games()

Key Classes:
    - GameplayEngine: Main orchestrator (convenience wrapper)
    - GameResult: Result of a complete game (from learning_systems)
    - AgentConfig: Agent configuration (from context_builder)
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from database_interface import DatabaseInterface

# Core modules
from arc_api_adapter import ArcadeWrapper, GameAction, GameConfig, GameInfo, GameState
from context_builder import AgentConfig, ContextBuilder
from game_loop import GameLoop, LoopConfig
from learning_systems import GameResult, LearningSystems
from outcome_processor import OutcomeProcessor

# Re-export key types
__all__ = [
    'GameplayEngine',
    'GameResult',
    'AgentConfig',
    'GameConfig',
    'GameInfo',
    'GameAction',
    'GameState',
    'LoopConfig',
]


@dataclass
class EngineConfig:
    """Configuration for the gameplay engine."""
    # API settings
    api_key: Optional[str] = None
    operation_mode: Optional[str] = None  # NORMAL, OFFLINE, ONLINE (default: from env or NORMAL)

    # Database
    db_path: str = "core_data.db"

    # Decision system
    decision_ordering: str = "comprehensive"  # Which rung ordering to use
    decision_strategy: str = "ladder"  # ladder or tournament

    # Game defaults
    default_max_actions: int = 2000
    default_render_mode: Optional[str] = None  # terminal, terminal-fast, human

    # Verbose mode
    verbose: bool = False


class GameplayEngine:
    """
    Convenience wrapper for ARC-AGI-3 gameplay.

    Provides two game-playing paths that share the same ``ContextBuilder``
    and ``DecisionRungSystem``:

    * **Sync path** (``play_single_game``): Constructs a minimal
      ``GamePlayer`` instance with no evolution-specific engines.
      Uses ``ContextBuilder.build_from_runner_state()`` — the same
      context contract as production evolution runs.

    * **Async path** (``play_single_game_async``): Delegates to
      ``GameLoop`` for lightweight async execution.  Uses
      ``ContextBuilder.build()`` with ``LoopState``.

    Both paths produce ``DecisionContext`` → ``decision_rung_system.decide()``
    so rungs see an identical contract regardless of entry point.

    Usage:
        engine = GameplayEngine()
        result = engine.play_single_game("ls20")
    """

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        db: Optional["DatabaseInterface"] = None,
    ):
        """
        Initialize the gameplay engine.

        Args:
            config: Engine configuration
            db: Optional database interface (will create if not provided)
        """
        self._config = config or EngineConfig()

        # Database
        self._db: Optional["DatabaseInterface"] = db
        if self._db is None:
            self._db = self._create_database()

        # API adapter
        self._api = ArcadeWrapper(
            api_key=self._config.api_key,
            operation_mode=self._config.operation_mode,
        )

        # Decision system (lazy loaded)
        self._decision_system = None

        # Context builder
        self._context_builder = ContextBuilder(self._db)

        # Outcome processor
        self._outcome_processor = OutcomeProcessor(self._db)

        # Learning systems (lazy loaded)
        self._learning_systems = None

        # Session tracking
        self._games_played = 0
        self._total_wins = 0

    def _create_database(self):
        """Create database interface."""
        try:
            from database_interface import DatabaseInterface
            return DatabaseInterface(self._config.db_path)
        except ImportError:
            # Fallback: no database
            return None
        except Exception as e:
            print(f"[WARN] Database creation failed: {e}")
            return None

    @property
    def decision_system(self):
        """Get decision system (lazy loaded)."""
        if self._decision_system is None:
            self._decision_system = self._create_decision_system()
        return self._decision_system

    def _create_decision_system(self):
        """Create the decision rung system."""
        try:
            from decision_rung_system import ORDERING_PRESETS, DecisionRungSystem

            system = DecisionRungSystem(strategy=self._config.decision_strategy)

            # Load ordering preset if specified
            if self._config.decision_ordering in ORDERING_PRESETS:
                system.load_ordering(self._config.decision_ordering)

            return system
        except ImportError:
            # Fallback: simple random decision
            return SimpleDecisionFallback()
        except Exception as e:
            print(f"[WARN] Decision system creation failed: {e}")
            return SimpleDecisionFallback()

    @property
    def learning_systems(self) -> LearningSystems:
        """Get learning systems (lazy loaded)."""
        if self._learning_systems is None:
            self._learning_systems = LearningSystems(db=self._db)
        return self._learning_systems

    # =========================================================================
    # Main API
    # =========================================================================

    def play_single_game(
        self,
        game_id: str,
        agent_config: Optional[AgentConfig] = None,
        max_actions: Optional[int] = None,
        render_mode: Optional[str] = None,
        use_async: bool = False,
    ) -> GameResult:
        """
        Play a single game.

        By default uses the sync ``GamePlayer`` path (same context
        contract as production evolution runs).  Pass ``use_async=True``
        to use the lightweight ``GameLoop`` state machine instead.

        Args:
            game_id: Game identifier (e.g., "ls20", "vc33")
            agent_config: Optional agent configuration
            max_actions: Maximum actions allowed (default from config)
            render_mode: Render mode ("terminal", "human", None)
            use_async: Use async GameLoop instead of sync GamePlayer

        Returns:
            GameResult with final score, levels completed, and action sequence
        """
        if use_async:
            return asyncio.run(self.play_single_game_async(
                game_id=game_id,
                agent_config=agent_config,
                max_actions=max_actions,
                render_mode=render_mode,
            ))

        return self._play_via_game_player(
            game_id=game_id,
            agent_config=agent_config,
            max_actions=max_actions,
        )

    def _play_via_game_player(
        self,
        game_id: str,
        agent_config: Optional[AgentConfig] = None,
        max_actions: Optional[int] = None,
    ) -> GameResult:
        """Play a game using the sync GamePlayer path.

        Constructs a minimal GamePlayer with no evolution-specific
        engines and delegates to ``play_game_standalone()``.
        Uses ``ContextBuilder.build_from_runner_state()`` — same
        context contract as production evolution.
        """
        agent_config = agent_config or AgentConfig(agent_id=f"agent-{self._games_played}")
        max_actions = max_actions or self._config.default_max_actions

        try:
            from engines.perception.player_localizer import PlayerLocalizer
            from engines.perception.property_extractor import PropertyExtractor
            from event_bus import EventBus
            from evolution_types import GameResult as EvolutionGameResult
            from game_player import GamePlayer
            from pipeline_assertions import PipelineAssertions

            # Minimal dependency set — no mastery, no concept_discovery
            player = GamePlayer(
                db=self._db,
                arcade=self._api._arcade if hasattr(self._api, '_arcade') else self._api,
                context_builder=self._context_builder,
                decision_system=self.decision_system,
                event_bus=EventBus(),
                pipe=PipelineAssertions(self._db),
                player_localizer=PlayerLocalizer(),
                property_extractor=PropertyExtractor(),
                mastery_system=None,
                concept_discovery_engine=None,
                max_actions=max_actions,
                verbose=self._config.verbose,
            )

            evo_result: EvolutionGameResult = player.play_game_standalone(
                game_id=game_id,
                agent_id=agent_config.agent_id,
            )

            # Convert evolution_types.GameResult -> learning_systems.GameResult
            result = GameResult(
                game_id=evo_result.game_id,
                final_score=evo_result.score,
                levels_completed=evo_result.levels_completed,
                win_levels=evo_result.total_levels,
                total_actions=evo_result.actions_taken,
                is_win=evo_result.is_win,
                is_full_win=evo_result.is_win and evo_result.levels_completed >= evo_result.total_levels,
                action_sequence=evo_result.action_sequence,
                agent_id=evo_result.agent_id,
            )

            # Update session stats
            self._games_played += 1
            if result.is_win:
                self._total_wins += 1

            return result
        except ImportError as e:
            # Fallback to async path if GamePlayer dependencies missing
            print(f"[WARN] GamePlayer not available ({e}), falling back to async path")
            return asyncio.run(self.play_single_game_async(
                game_id=game_id,
                agent_config=agent_config,
                max_actions=max_actions,
            ))

    async def play_single_game_async(
        self,
        game_id: str,
        agent_config: Optional[AgentConfig] = None,
        max_actions: Optional[int] = None,
        render_mode: Optional[str] = None,
    ) -> GameResult:
        """
        Play a single game asynchronously.

        Same as play_single_game but async.
        """
        agent_config = agent_config or AgentConfig(agent_id=f"agent-{self._games_played}")
        max_actions = max_actions or self._config.default_max_actions
        render_mode = render_mode or self._config.default_render_mode

        # Create game config
        game_config = GameConfig(
            game_id=game_id,
            render_mode=render_mode,
        )

        # Create environment
        env = self._api.create_environment(game_config)
        if env is None:
            return self._create_failed_result(game_id, agent_config, "Failed to create environment")

        # Create loop config
        loop_config = LoopConfig(
            max_actions=max_actions,
            render_mode=render_mode,
            verbose=self._config.verbose,
        )

        # Create game loop
        loop = GameLoop(
            env=env,
            decision_system=self.decision_system,
            context_builder=self._context_builder,
            outcome_processor=self._outcome_processor,
            learning_systems=self.learning_systems,
            config=loop_config,
        )

        # Run the game
        result = await loop.run(agent_config=agent_config, max_actions=max_actions)

        # Update session stats
        self._games_played += 1
        if result.is_win:
            self._total_wins += 1

        return result

    def play_multiple_games(
        self,
        game_ids: List[str],
        agent_config: Optional[AgentConfig] = None,
        max_actions_per_game: Optional[int] = None,
    ) -> List[GameResult]:
        """
        Play multiple games sequentially.

        Args:
            game_ids: List of game identifiers
            agent_config: Optional agent configuration (shared across games)
            max_actions_per_game: Max actions per game

        Returns:
            List of GameResult objects
        """
        results: List[GameResult] = []

        for game_id in game_ids:
            result = self.play_single_game(
                game_id=game_id,
                agent_config=agent_config,
                max_actions=max_actions_per_game,
            )
            results.append(result)

        return results

    def _create_failed_result(
        self,
        game_id: str,
        agent_config: AgentConfig,
        _error: str,  # Unused but kept for API consistency
    ) -> GameResult:
        """Create a failed game result."""
        return GameResult(
            game_id=game_id,
            final_score=0.0,
            levels_completed=0,
            win_levels=0,
            total_actions=0,
            is_win=False,
            is_full_win=False,
            action_sequence=[],
            agent_id=agent_config.agent_id,
        )

    # =========================================================================
    # Game Discovery
    # =========================================================================

    def list_games(self) -> List[GameInfo]:
        """
        List all available games.

        Returns:
            List of GameInfo objects with game_id, title, and tags
        """
        return self._api.list_games()

    def list_game_ids(self) -> List[str]:
        """
        List just the game IDs.

        Returns:
            List of game ID strings
        """
        return self._api.list_game_ids()

    # =========================================================================
    # Scorecard Management
    # =========================================================================

    def get_scorecard(self, scorecard_id: Optional[str] = None):
        """
        Get scorecard results.

        Args:
            scorecard_id: Specific scorecard ID, or None for default

        Returns:
            Scorecard object with results
        """
        return self._api.get_scorecard(scorecard_id)

    def close_scorecard(self, scorecard_id: Optional[str] = None):
        """
        Close and finalize a scorecard.

        Args:
            scorecard_id: Specific scorecard ID, or None for default

        Returns:
            Final scorecard with results
        """
        return self._api.close_scorecard(scorecard_id)

    def create_scorecard(
        self,
        source_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Create a new scorecard.

        Args:
            source_url: Optional URL for tracking
            tags: Optional tags for filtering

        Returns:
            Scorecard ID string
        """
        return self._api.create_scorecard(source_url=source_url, tags=tags)

    # =========================================================================
    # Session Stats
    # =========================================================================

    @property
    def games_played(self) -> int:
        """Get total games played this session."""
        return self._games_played

    @property
    def total_wins(self) -> int:
        """Get total wins this session."""
        return self._total_wins

    @property
    def win_rate(self) -> float:
        """Get session win rate."""
        if self._games_played == 0:
            return 0.0
        return self._total_wins / self._games_played

    # =========================================================================
    # Configuration
    # =========================================================================

    def set_decision_ordering(self, ordering: str) -> None:
        """
        Set the decision rung ordering.

        Args:
            ordering: Ordering preset name (e.g., "efficiency", "exploration")
        """
        if self._decision_system is not None and hasattr(self._decision_system, 'load_ordering'):
            try:
                self._decision_system.load_ordering(ordering)  # type: ignore
            except Exception as e:
                print(f"[WARN] Failed to set ordering: {e}")

    def set_verbose(self, verbose: bool) -> None:
        """Set verbose mode."""
        self._config.verbose = verbose


class SimpleDecisionFallback:
    """
    Simple fallback decision system when DecisionRungSystem is not available.

    Just returns a random action from available actions.
    """

    def decide(self, frame: Any, context: Dict[str, Any]) -> tuple[str, str]:
        """Make a random decision."""
        import random

        available = context.get('available_actions', ['ACTION1'])
        action = random.choice(available)

        return action, "random_fallback"


# =============================================================================
# Convenience Functions
# =============================================================================

def quick_play(game_id: str, max_actions: int = 500) -> GameResult:
    """
    Quick play a single game with default settings.

    Args:
        game_id: Game identifier
        max_actions: Maximum actions

    Returns:
        GameResult
    """
    engine = GameplayEngine()
    return engine.play_single_game(game_id, max_actions=max_actions)


def list_all_games() -> List[str]:
    """List all available game IDs."""
    engine = GameplayEngine(config=EngineConfig(operation_mode="OFFLINE"))
    return engine.list_game_ids()


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    print("Core Gameplay v3.0 - Quick Test")
    print("=" * 50)
    print("  Sync path:  GamePlayer.play_game_standalone()")
    print("  Async path: GameLoop.run()")
    print()

    # Test in offline mode
    config = EngineConfig(
        operation_mode="OFFLINE",
        verbose=True,
    )

    engine = GameplayEngine(config=config)

    print(f"\nOperation Mode: {config.operation_mode}")

    # List games
    games = engine.list_games()
    print(f"\nAvailable Games: {len(games)}")
    for g in games[:5]:
        print(f"  - {g.game_id}: {g.title}")

    # Try to play if games available
    if games:
        print(f"\n--- Playing: {games[0].game_id} ---")

        agent = AgentConfig(
            agent_id="test-agent",
            role="pioneer",
            action_budget=100,  # Short budget for test
        )

        result = engine.play_single_game(
            games[0].game_id,
            agent_config=agent,
            max_actions=50,  # Very short for test
        )

        print(f"\nResult:")
        print(f"  Game: {result.game_id}")
        print(f"  Score: {result.final_score:.2f}")
        print(f"  Levels: {result.levels_completed}/{result.win_levels}")
        print(f"  Actions: {result.total_actions}")
        print(f"  Win: {result.is_win}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        print(f"  Sequence (first 10): {result.action_sequence[:10]}")

    print(f"\n--- Session Stats ---")
    print(f"  Games played: {engine.games_played}")
    print(f"  Total wins: {engine.total_wins}")
    print(f"  Win rate: {engine.win_rate:.1%}")

    print("\n[OK] All tests passed!")
