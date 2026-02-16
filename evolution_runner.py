#!/usr/bin/env python3
"""
Evolution Runner - Thin Orchestrator (Phase 4.1 decomposition)
==============================================================

Coordinates agents, games, evolution, and engine cadence.
Gameplay logic lives in game_player.py.
Result persistence lives in result_recorder.py.
Health assertions live in health_monitor.py.
Shared data types live in evolution_types.py.

Usage:
    python evolution_runner.py --mode=offline --test --game=ls20
    python evolution_runner.py --mode=online --max-generations=10
"""

import os
import sys
import time

# Rule 1: No pycache
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import argparse
import json
import random
import signal
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# SDK imports
from arc_agi import Arcade, OperationMode
from arcengine import GameAction, GameState

from context_builder import ContextBuilder

# Local imports
from database_interface import DatabaseInterface
from decision_rung_system import DecisionRungSystem
from event_bus import EventBus, EventType, make_event
from evolution_types import AgentState, GameResult

# Extracted modules (Phase 4.1)
from game_player import GamePlayer
from health_monitor import HealthMonitor

# Cognitive Loop - Perceive-Think-Map-Act architecture
try:
    from cognitive_game_player import CognitiveGamePlayer
    COGNITIVE_LOOP_AVAILABLE = True
except ImportError:
    COGNITIVE_LOOP_AVAILABLE = False
from pipeline_assertions import PipelineAssertions
from result_recorder import ResultRecorder

# Cognitive Router - Full architecture integration (Phases 1-11)
try:
    from engines.cognition.blackboard import Blackboard
    from engines.cognition.cognitive_router import (
        CognitiveRouter,
        DecisionResult,
        RouterConfig,
    )
    from engines.cognition.epistemic_tracker import RungResult
    from engines.cognition.routing_traces import RoutingTrace, RoutingTraceStore
    COGNITIVE_ROUTER_AVAILABLE = True
except ImportError as e:
    COGNITIVE_ROUTER_AVAILABLE = False
    print(f"[WARN] CognitiveRouter not available: {e}")

# Symbolic reasoning components (Phase 0-1)
from engines.perception.player_localizer import PlayerLocalizer
from engines.perception.property_extractor import PropertyExtractor
from evolutionary_engine import EvolutionaryEngine, calculate_youth_bonus

# Viral package engine for network knowledge sharing
try:
    from engines.social.viral_package_engine import ViralPackageEngine
    VIRAL_PACKAGE_AVAILABLE = True
except ImportError:
    VIRAL_PACKAGE_AVAILABLE = False

# Network Intelligence Engine - ecosystem health monitoring (Unified Theory core)
try:
    from network_intelligence_engine import NetworkIntelligenceEngine
    NETWORK_INTELLIGENCE_AVAILABLE = True
except ImportError:
    NETWORK_INTELLIGENCE_AVAILABLE = False

# Horizontal Transfer Engine - viral knowledge spread between agents
try:
    from horizontal_transfer_engine import HorizontalTransferEngine
    HORIZONTAL_TRANSFER_AVAILABLE = True
except ImportError:
    HORIZONTAL_TRANSFER_AVAILABLE = False

# Meta-Learning Curriculum - intelligent game selection for generalization
try:
    from meta_learning_curriculum import MetaLearningCurriculum
    META_LEARNING_AVAILABLE = True
except ImportError:
    META_LEARNING_AVAILABLE = False

# Agent Lifecycle Manager - safe agent birth/death/revival management
try:
    from agent_lifecycle_manager import AgentLifecycleManager
    LIFECYCLE_MANAGER_AVAILABLE = True
except ImportError:
    LIFECYCLE_MANAGER_AVAILABLE = False

# Collective Reasoning Engine - multi-agent ensemble intelligence
try:
    from collective_reasoning_engine import CollectiveReasoningEngine
    COLLECTIVE_REASONING_AVAILABLE = True
except ImportError:
    COLLECTIVE_REASONING_AVAILABLE = False

# Network Health Responder - translates health snapshots into corrective actions
try:
    from network_health_responder import NetworkHealthResponder
    HEALTH_RESPONDER_AVAILABLE = True
except ImportError:
    HEALTH_RESPONDER_AVAILABLE = False

# Resonance Detector - cross-game structural similarity (Phase 3.1)
try:
    from engines.social.resonance_detector import ResonanceDetector
    RESONANCE_DETECTOR_AVAILABLE = True
except ImportError:
    RESONANCE_DETECTOR_AVAILABLE = False

# Primitive Unlock Manager - bootstrapping mechanism (Phase 3.2)
try:
    from primitive_unlock_manager import PrimitiveUnlockManager
    PRIMITIVE_UNLOCK_AVAILABLE = True
except ImportError:
    PRIMITIVE_UNLOCK_AVAILABLE = False

# Concept Discovery Engine - high-level concept discovery (CODS Tier 4)
try:
    from concept_discovery_engine import ConceptDiscoveryEngine
    CONCEPT_DISCOVERY_AVAILABLE = True
except ImportError:
    CONCEPT_DISCOVERY_AVAILABLE = False

# Universal Pattern Engine - cross-game pattern transfer
try:
    from engines.self_model.universal_patterns import UniversalPatternEngine
    UNIVERSAL_PATTERN_AVAILABLE = True
except ImportError:
    UNIVERSAL_PATTERN_AVAILABLE = False

# Games-as-Teachers Engine - lesson extraction from wins
try:
    from engines.reasoning.scientific_method_engine import GamesAsTeachersEngine
    GAMES_AS_TEACHERS_AVAILABLE = True
except ImportError:
    GAMES_AS_TEACHERS_AVAILABLE = False

# Symbolic Reasoning Engine - abstract symbolic reasoning for complex games
try:
    from engines.reasoning.symbolic_reasoning_engine import SymbolicReasoningEngine
    SYMBOLIC_REASONING_AVAILABLE = True
except ImportError:
    SYMBOLIC_REASONING_AVAILABLE = False

# Agent Operating Mode System - assigns pioneer/optimizer/generalist/exploiter roles
try:
    from agent_operating_mode_system import AgentOperatingModeSystem
    OPERATING_MODE_AVAILABLE = True
except ImportError:
    OPERATING_MODE_AVAILABLE = False

# Mastery System - mastery-gated replay with stealth ablation (Phase 1.1)
try:
    from mastery_system import MasterySystem
    MASTERY_SYSTEM_AVAILABLE = True
except ImportError:
    MASTERY_SYSTEM_AVAILABLE = False

# System Health Gauges - seven runtime decay detectors (Phase 6.1)
try:
    from system_health_gauges import SystemHealthGauges
    HEALTH_GAUGES_AVAILABLE = True
except ImportError:
    HEALTH_GAUGES_AVAILABLE = False

# System Diagnostic - comprehensive self-diagnostic report (Phase 6.3)
try:
    from system_diagnostic import SystemDiagnostic
    SYSTEM_DIAGNOSTIC_AVAILABLE = True
except ImportError:
    SYSTEM_DIAGNOSTIC_AVAILABLE = False


class EvolutionRunner:
    """
    Thin orchestrator for the evolution loop.

    Owns engine instantiation and the run/generation/evolve cadence.
    Delegates gameplay to GamePlayer, result persistence to ResultRecorder,
    and health assertions to HealthMonitor.

    Core loop:
    1. Create agents
    2. Each agent plays games (-> GamePlayer)
    3. Record results (-> ResultRecorder)
    4. Evolve (select best, mutate, create offspring)
    5. Post-generation cadence (health, cleanup, engines)
    6. Repeat
    """

    def __init__(
        self,
        mode: str = "normal",
        db_path: str = "core_data.db",
        population_size: int = 100,
        games_per_generation: int = 5,
        max_generations: int = 10,
        max_actions_per_game: int = 500,
        target_game: Optional[str] = None,
        verbose: bool = False,
        rung_ordering: str = "comprehensive",
        use_cognitive_loop: bool = True,
        observe: bool = False,
    ):
        self.mode = mode
        self.verbose = verbose
        self.observe = observe
        self.rung_ordering = rung_ordering
        self._use_cognitive_loop = use_cognitive_loop and COGNITIVE_LOOP_AVAILABLE
        self.db = DatabaseInterface(db_path)
        self.pipe = PipelineAssertions(self.db)
        self.population_size = population_size
        self.games_per_generation = games_per_generation
        self.max_generations = max_generations
        self.max_actions = max_actions_per_game
        self.target_game = target_game

        # Evolution strategy (mutable -- health responder adjusts between gens)
        self._evolution_strategy: Dict[str, Any] = {
            'selection_pressure': 0.5,
            'crossover_rate': 0.6,
            'mutation_rate': 0.2,
            'diversity_mode': True,
            'focus': 'balanced',
        }

        # SDK setup
        op_mode = {
            'offline': OperationMode.OFFLINE,
            'online': OperationMode.ONLINE,
            'normal': OperationMode.NORMAL,
        }.get(mode.lower(), OperationMode.NORMAL)
        self.op_mode = op_mode

        self.arcade = Arcade(operation_mode=op_mode)

        # Cognitive Router - Full architecture implementation (Phases 1-11)
        self.cognitive_router: Optional[CognitiveRouter] = None
        self.routing_trace_store: Optional[RoutingTraceStore] = None
        self._use_cognitive_router = False

        if COGNITIVE_ROUTER_AVAILABLE:
            try:
                router_config = RouterConfig(
                    max_iterations=15,
                    max_rungs_per_call=5,
                    commit_threshold=0.50,
                    time_budget_seconds=30.0,
                    use_hysteresis=True,
                    use_meta_planner_cache=True,
                    use_catastrophic_fallback=True,
                    algorithm_switch_cooldown=3,
                    precompute_on_init=True,
                )
                self.cognitive_router = CognitiveRouter(config=router_config)
                self.routing_trace_store = RoutingTraceStore(db_interface=self.db)
                self._use_cognitive_router = True
                if self.verbose:
                    print("[INIT] CognitiveRouter initialized - Full architecture enabled")
                    print("       Phases: Blackboard + Epistemic + Phenomenology + Eisenhower + Meta-Planner")
            except Exception as e:
                print(f"[WARN] Could not initialize CognitiveRouter: {e}")
                self._use_cognitive_router = False

        # Decision system
        strategy = 'cognitive' if self._use_cognitive_router else 'ladder'
        self.decision_system = DecisionRungSystem(
            strategy=strategy,
            cognitive_router=self.cognitive_router,
            routing_trace_store=self.routing_trace_store
        )
        self.decision_system.load_ordering(self.rung_ordering)

        if self.verbose:
            strat_name = "COGNITIVE (full routing pipeline)" if self._use_cognitive_router else "LADDER (fallback mode)"
            print(f"[INIT] DecisionSystem strategy: {strat_name}")

        # Evolutionary engine
        self.evolutionary_engine = EvolutionaryEngine(self.db)

        # State
        self.agents: List[AgentState] = []
        self.current_generation = self._load_generation_from_db()
        self._start_generation = self.current_generation
        self.running = True

        # Symbolic reasoning components (Phase 0-1)
        self.player_localizer = PlayerLocalizer(confidence_threshold=0.6)
        self.property_extractor = PropertyExtractor(color_quantization=16)

        # Context builder - unified context contract (Phase 0.1)
        self.context_builder = ContextBuilder(db=self.db)

        # Event bus - network-wide pub/sub backbone (Phase 0.3)
        self.event_bus = EventBus()
        self.event_bus.set_hook_failure_event(EventType.HOOK_FAILURE_DETECTED)

        # ---- Optional engines (try/except, None if unavailable) ----
        self.viral_package_engine = None
        if VIRAL_PACKAGE_AVAILABLE:
            try:
                self.viral_package_engine = ViralPackageEngine(self.db)
                if self.verbose:
                    print("[INIT] Viral package engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize viral package engine: {e}")

        self.network_intelligence_engine = None
        if NETWORK_INTELLIGENCE_AVAILABLE:
            try:
                self.network_intelligence_engine = NetworkIntelligenceEngine(self.db)
                if self.verbose:
                    print("[INIT] Network intelligence engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize network intelligence engine: {e}")

        self.horizontal_transfer_engine = None
        if HORIZONTAL_TRANSFER_AVAILABLE:
            try:
                self.horizontal_transfer_engine = HorizontalTransferEngine(self.db)
                if self.verbose:
                    print("[INIT] Horizontal transfer engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize horizontal transfer engine: {e}")

        self.meta_learning_curriculum = None
        if META_LEARNING_AVAILABLE:
            try:
                self.meta_learning_curriculum = MetaLearningCurriculum(self.db)
                if self.verbose:
                    print("[INIT] Meta-learning curriculum initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize meta-learning curriculum: {e}")

        self.lifecycle_manager = None
        if LIFECYCLE_MANAGER_AVAILABLE:
            try:
                self.lifecycle_manager = AgentLifecycleManager(self.db)
                if self.verbose:
                    print("[INIT] Agent lifecycle manager initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize lifecycle manager: {e}")

        self.collective_reasoning_engine = None
        if COLLECTIVE_REASONING_AVAILABLE:
            try:
                self.collective_reasoning_engine = CollectiveReasoningEngine(self.db)
                if self.verbose:
                    print("[INIT] Collective reasoning engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize collective reasoning engine: {e}")

        self.health_responder = None
        if HEALTH_RESPONDER_AVAILABLE:
            try:
                self.health_responder = NetworkHealthResponder(self.db)
                if self.verbose:
                    print("[INIT] Network health responder initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize health responder: {e}")

        self.concept_discovery_engine = None
        if CONCEPT_DISCOVERY_AVAILABLE:
            try:
                self.concept_discovery_engine = ConceptDiscoveryEngine(self.db)
                if self.verbose:
                    print("[INIT] Concept discovery engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize concept discovery engine: {e}")

        self.resonance_detector = None
        if RESONANCE_DETECTOR_AVAILABLE:
            try:
                self.resonance_detector = ResonanceDetector(self.db)
                if self.verbose:
                    print("[INIT] Resonance detector initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize resonance detector: {e}")

        self.primitive_unlock_manager = None
        if PRIMITIVE_UNLOCK_AVAILABLE:
            try:
                self.primitive_unlock_manager = PrimitiveUnlockManager(db=self.db)
                if self.verbose:
                    print("[INIT] Primitive unlock manager initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize primitive unlock manager: {e}")

        self.universal_pattern_engine = None
        if UNIVERSAL_PATTERN_AVAILABLE:
            try:
                self.universal_pattern_engine = UniversalPatternEngine()
                if self.verbose:
                    print("[INIT] Universal pattern engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize universal pattern engine: {e}")

        self.games_as_teachers_engine = None
        if GAMES_AS_TEACHERS_AVAILABLE:
            try:
                self.games_as_teachers_engine = GamesAsTeachersEngine(self.db)
                if self.verbose:
                    print("[INIT] Games-as-teachers engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize games-as-teachers engine: {e}")

        self.operating_mode_system = None
        if OPERATING_MODE_AVAILABLE:
            try:
                self.operating_mode_system = AgentOperatingModeSystem(self.db)
                if self.verbose:
                    print("[INIT] Agent operating mode system initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize operating mode system: {e}")

        self.mastery_system = None
        if MASTERY_SYSTEM_AVAILABLE:
            try:
                self.mastery_system = MasterySystem(self.db, event_bus=self.event_bus)
                if self.verbose:
                    print("[INIT] Mastery system initialized - replay gating active")
            except Exception as e:
                print(f"[WARN] Could not initialize mastery system: {e}")

        # Phase 6.1: System Health Gauges (7 decay detectors)
        self.health_gauges = None
        if HEALTH_GAUGES_AVAILABLE:
            try:
                self.health_gauges = SystemHealthGauges(self.db)
                if self.verbose:
                    print("[INIT] System health gauges initialized (7 gauges)")
            except Exception as e:
                print(f"[WARN] Could not initialize health gauges: {e}")

        # Phase 6.3: System Diagnostic (comprehensive self-report)
        self.system_diagnostic = None
        if SYSTEM_DIAGNOSTIC_AVAILABLE:
            try:
                self.system_diagnostic = SystemDiagnostic(self.db, health_gauges=self.health_gauges)
                if self.verbose:
                    print("[INIT] System diagnostic initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize system diagnostic: {e}")

        # ---- Extracted sub-systems (Phase 4.1) ----
        self._game_player = GamePlayer(
            db=self.db,
            arcade=self.arcade,
            context_builder=self.context_builder,
            decision_system=self.decision_system,
            event_bus=self.event_bus,
            pipe=self.pipe,
            player_localizer=self.player_localizer,
            property_extractor=self.property_extractor,
            mastery_system=self.mastery_system,
            concept_discovery_engine=self.concept_discovery_engine,
            op_mode=self.op_mode,
            max_actions=self.max_actions,
            verbose=self.verbose,
            use_cognitive_router=self._use_cognitive_router,
        )

        # Cognitive Loop wrapper (Perceive-Think-Map-Act)
        self._cognitive_player: Optional[CognitiveGamePlayer] = None
        if self._use_cognitive_loop:
            try:
                self._cognitive_player = CognitiveGamePlayer(
                    game_player=self._game_player,
                    verbose=self.verbose,
                    observe=self.observe,
                )
                if self.verbose:
                    print("[INIT] CognitiveGamePlayer initialized - PTMA loop active")
            except Exception as e:
                print(f"[WARN] CognitiveGamePlayer init failed, falling back to standard: {e}")
                self._cognitive_player = None
                self._use_cognitive_loop = False

        self._result_recorder = ResultRecorder(
            db=self.db,
            pipe=self.pipe,
            viral_package_engine=self.viral_package_engine,
            games_as_teachers_engine=self.games_as_teachers_engine,
            verbose=self.verbose,
        )

        self._health_monitor = HealthMonitor(
            db=self.db,
            population_size=self.population_size,
            verbose=self.verbose,
        )

        # Wire event bus subscribers (Phase 0.3)
        self._wire_event_subscribers()

        # Signal handling (was stray in _record_goal_outcome, now correctly in __init__)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    # ------------------------------------------------------------------
    # Event Bus Wiring (Phase 0.3)
    # ------------------------------------------------------------------

    def _wire_event_subscribers(self) -> None:
        """Register engine callbacks on the event bus.

        Engines that react to gameplay events subscribe here.
        All handlers are wrapped so a single subscriber crash
        never kills the game loop (EventBus catches exceptions).
        """
        bus = self.event_bus

        # -- Network Intelligence: capture ecosystem snapshot every generation --
        if self.network_intelligence_engine:
            _nie = self.network_intelligence_engine
            def _on_generation_complete_nie(
                _et: EventType, payload: Dict[str, Any]
            ) -> None:
                gen = payload.get('generation', 0)
                _nie.capture_ecosystem_snapshot(
                    generation=gen,
                )
            bus.subscribe(EventType.GENERATION_COMPLETE, _on_generation_complete_nie)

        # -- Horizontal Transfer: spread knowledge at generation boundary --
        if self.horizontal_transfer_engine:
            _hte = self.horizontal_transfer_engine
            def _on_generation_complete_hte(
                _et: EventType, payload: Dict[str, Any]
            ) -> None:
                gen = payload.get('generation', 0)
                _hte.execute_generation_transfers(
                    generation=gen,
                )
            bus.subscribe(EventType.GENERATION_COMPLETE, _on_generation_complete_hte)

        # -- Concept Discovery: scan for emerging concepts on level-ups --
        if self.concept_discovery_engine:
            _cde = self.concept_discovery_engine
            def _on_level_up_cde(
                _et: EventType, payload: Dict[str, Any]
            ) -> None:
                _cde.check_concept_emergence()
            bus.subscribe(EventType.LEVEL_UP, _on_level_up_cde)

        # -- Meta-Learning Curriculum: update stage progress on game outcomes --
        if self.meta_learning_curriculum:
            _mlc = self.meta_learning_curriculum
            def _on_game_won_mlc(
                _et: EventType, payload: Dict[str, Any]
            ) -> None:
                agent_id = payload.get('agent_id', '')
                if agent_id:
                    _mlc.update_stage_progress(agent_id)
            bus.subscribe(EventType.GAME_WON, _on_game_won_mlc)

            def _on_game_over_mlc(
                _et: EventType, payload: Dict[str, Any]
            ) -> None:
                agent_id = payload.get('agent_id', '')
                if agent_id:
                    _mlc.update_stage_progress(agent_id)
            bus.subscribe(EventType.GAME_OVER, _on_game_over_mlc)

        # -- Mastery System: recalculate all mastery tiers each generation --
        if self.mastery_system:
            _ms = self.mastery_system
            def _on_generation_complete_ms(
                _et: EventType, payload: Dict[str, Any]
            ) -> None:
                gen = payload.get('generation', 0)
                _ms.update_all_mastery(generation=gen)
            bus.subscribe(EventType.GENERATION_COMPLETE, _on_generation_complete_ms)

        # -- Resonance Detector: opportunistic resonance check on new patterns --
        if self.resonance_detector:
            _rd = self.resonance_detector
            def _on_pattern_discovered_rd(
                _et: EventType, payload: Dict[str, Any]
            ) -> None:
                game_id = payload.get('game_id', '')
                if game_id:
                    beliefs = {
                        'working_theory_required': payload.get('pattern_type', ''),
                        'self_model_required': payload.get('details', {}).get('control_type', ''),
                    }
                    _rd.get_pattern_resonance(beliefs)
            bus.subscribe(EventType.PATTERN_DISCOVERED, _on_pattern_discovered_rd)

        # -- Phase 0.3: GAME_WON -> Network Intelligence (immediate snapshot) --
        if self.network_intelligence_engine:
            _nie2 = self.network_intelligence_engine
            def _on_game_won_nie(
                _et: EventType, payload: Dict[str, Any]
            ) -> None:
                gen = getattr(self, 'current_generation', 0)
                _nie2.capture_ecosystem_snapshot(
                    generation=gen,
                )
            bus.subscribe(EventType.GAME_WON, _on_game_won_nie)

        # -- Phase 0.3: AGENT_DEATH -> Lifecycle Manager (track death stats) --
        if self.lifecycle_manager:
            def _on_agent_death_alm(
                _et: EventType, payload: Dict[str, Any]
            ) -> None:
                agent_id = payload.get('agent_id', '')
                game_id = payload.get('game_id', '')
                if agent_id:
                    import logging as _logging
                    _logging.getLogger('lifecycle').info(
                        "[AGENT-DEATH] agent=%s game=%s action_count=%s",
                        agent_id, game_id, payload.get('action_count', '?'),
                    )
            bus.subscribe(EventType.AGENT_DEATH, _on_agent_death_alm)

        # -- Phase 1.4: GAME_WON -> Concept Discovery (track winning patterns) --
        if self.concept_discovery_engine:
            _cde2 = self.concept_discovery_engine
            def _on_game_won_cde(
                _et: EventType, payload: Dict[str, Any]
            ) -> None:
                _cde2.check_concept_emergence()
            bus.subscribe(EventType.GAME_WON, _on_game_won_cde)

        count = sum(len(v) for v in bus._subscribers.values())
        if self.verbose and count > 0:
            print(f"[INIT] Event bus: {count} subscribers wired across {len(bus._subscribers)} event types")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _handle_shutdown(self, signum, frame):
        print("\n[STOP] Shutdown requested...")
        self.running = False

    def _load_generation_from_db(self) -> int:
        """Load the next generation number from database."""
        try:
            result = self.db.execute_query("""
                SELECT MAX(gen) as max_gen FROM (
                    SELECT MAX(generation) as gen FROM game_results
                    UNION ALL
                    SELECT MAX(generation) as gen FROM agents WHERE is_active = TRUE
                )
            """)
            if result and result[0]['max_gen'] is not None:
                next_gen = result[0]['max_gen'] + 1
                print(f"[INIT] Resuming from generation {next_gen} (last completed: {next_gen - 1})")
                return next_gen
        except Exception as e:
            print(f"[WARN] Could not load generation from DB: {e}")
        return 0

    @staticmethod
    def _create_agent_id() -> str:
        """Generate unique agent ID."""
        return f"agent_{uuid.uuid4().hex[:12]}"

    def initialize_population(self) -> List[AgentState]:
        """Create initial agent population."""
        print(f"\n[INIT] Creating {self.population_size} agents...")

        agents = []
        for i in range(self.population_size):
            agent = AgentState(
                agent_id=self._create_agent_id(),
                generation=0,
            )
            agents.append(agent)

            genome = '{"exploration_rate": 0.3, "learning_rate": 0.1}'
            self.db.execute_query("""
                INSERT OR REPLACE INTO agents (
                    agent_id, generation, agent_type, genome, specialization,
                    created_at, is_active
                ) VALUES (?, ?, 'evolved', ?, 'generalist', datetime('now'), TRUE)
            """, (agent.agent_id, 0, genome))

        print(f"[OK] Created {len(agents)} agents")
        return agents

    def get_available_games(self) -> List[str]:
        """Get list of available game IDs."""
        try:
            envs = self.arcade.get_environments()
            game_ids = [e.game_id for e in envs]
            if self.target_game:
                game_ids = [g for g in game_ids if g.startswith(self.target_game)]
            return game_ids
        except Exception as e:
            print(f"[ERROR] Failed to get games: {e}")
            return []

    # ------------------------------------------------------------------
    # Delegation: play_game -> GamePlayer
    # ------------------------------------------------------------------

    def play_game(self, agent: AgentState, game_id: str) -> GameResult:
        """Play a single game with an agent.

        Routes through CognitiveGamePlayer (PTMA loop) when enabled,
        falls back to standard GamePlayer on failure.
        """
        if self._use_cognitive_loop and self._cognitive_player is not None:
            try:
                return self._cognitive_player.play_game(
                    agent=agent,
                    game_id=game_id,
                    current_generation=self.current_generation,
                    is_running_fn=lambda: self.running,
                )
            except Exception as e:
                if self.verbose:
                    print(f"    [PTMA-ERR] CognitiveLoop failed, falling back: {e}")

        return self._game_player.play_game(
            agent=agent,
            game_id=game_id,
            current_generation=self.current_generation,
            is_running_fn=lambda: self.running,
        )

    # ------------------------------------------------------------------
    # Collective reasoning helpers
    # ------------------------------------------------------------------

    def _get_agent_best_action_for_game(self, agent_id: str, game_id: str) -> Optional[Dict]:
        """Query an agent's most successful action for a given game."""
        try:
            rows = self.db.execute_query("""
                SELECT action_number, coordinates, score_change, level_number
                FROM action_traces at2
                JOIN training_sessions ts ON at2.session_id = ts.session_id
                JOIN game_results gr ON gr.session_id = ts.session_id
                WHERE at2.game_id = ? AND gr.agent_id = ?
                  AND at2.score_change > 0
                ORDER BY at2.score_change DESC
                LIMIT 1
            """, (game_id, agent_id))

            if rows:
                row = rows[0]
                coords = None
                if row.get('coordinates'):
                    try:
                        coords = json.loads(row['coordinates'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                return {
                    'action': row['action_number'],
                    'coordinates': coords,
                    'score_change': row['score_change'],
                    'level': row.get('level_number', 0),
                }

            rows = self.db.execute_query("""
                SELECT action_number, COUNT(*) as cnt
                FROM action_traces at2
                JOIN training_sessions ts ON at2.session_id = ts.session_id
                JOIN game_results gr ON gr.session_id = ts.session_id
                WHERE at2.game_id = ? AND gr.agent_id = ?
                  AND at2.frame_changed = 1
                GROUP BY action_number
                ORDER BY cnt DESC
                LIMIT 1
            """, (game_id, agent_id))

            if rows:
                return {
                    'action': rows[0]['action_number'],
                    'coordinates': None,
                    'score_change': 0.0,
                    'level': 0,
                }
            return None
        except Exception:
            return None

    def _run_collective_deliberation(self, game_id: str, results: List) -> Optional[Dict]:
        """Run full propose/vote/resolve cycle for a stuck game."""
        cre = self.collective_reasoning_engine
        if cre is None:
            return None
        gen = self.current_generation

        session_id = cre.start_collective_session(
            game_id=game_id, generation=gen, reasoning_mode='voting',
        )
        if not session_id:
            return None

        session_row = self.db.execute_query("""
            SELECT agent_ids FROM collective_reasoning_sessions
            WHERE session_id = ?
        """, (session_id,))
        if not session_row:
            return None

        try:
            agent_ids = json.loads(session_row[0]['agent_ids'])
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

        if len(agent_ids) < 2:
            return None

        # --- PROPOSE PHASE ---
        proposal_ids = []
        proposer_map = {}
        for aid in agent_ids:
            best = self._get_agent_best_action_for_game(aid, game_id)
            if best is None:
                best = {'action': 1, 'coordinates': None, 'score_change': 0.0}

            confidence = min(1.0, 0.3 + best.get('score_change', 0.0) * 2.0)
            reasoning = (
                f"score_delta={best.get('score_change', 0.0):.2f}, "
                f"level={best.get('level', 0)}"
            )

            pid = cre.propose_action(
                session_id=session_id, agent_id=aid,
                action=best['action'], coordinates=best.get('coordinates'),
                reasoning=reasoning, confidence=confidence,
            )
            if pid:
                proposal_ids.append(pid)
                proposer_map[pid] = aid

        if not proposal_ids:
            cre.complete_session(session_id, final_score=0.0)
            return None

        # --- VOTE PHASE ---
        for pid in proposal_ids:
            proposer = proposer_map[pid]
            for voter_id in agent_ids:
                if voter_id == proposer:
                    continue

                voter_best = self._get_agent_best_action_for_game(voter_id, game_id)
                voter_score = voter_best.get('score_change', 0.0) if voter_best else 0.0

                proposer_best = self._get_agent_best_action_for_game(proposer, game_id)
                proposer_score = proposer_best.get('score_change', 0.0) if proposer_best else 0.0

                if proposer_score >= voter_score:
                    vote_choice = 'for'
                    vote_reasoning = f"proposer_delta={proposer_score:.2f} >= mine={voter_score:.2f}"
                elif proposer_score > 0:
                    vote_choice = 'for'
                    vote_reasoning = f"positive delta {proposer_score:.2f}"
                else:
                    vote_choice = 'against'
                    vote_reasoning = f"proposer_delta={proposer_score:.2f} < mine={voter_score:.2f}"

                cre.vote_on_proposal(
                    proposal_id=pid, voting_agent_id=voter_id,
                    vote_choice=vote_choice, reasoning=vote_reasoning,
                    confidence=min(1.0, 0.4 + abs(proposer_score - voter_score)),
                )

        # --- RESOLVE PHASE ---
        consensus = cre.resolve_voting(session_id, turn_number=0)

        if consensus:
            cre.record_collective_insight(
                session_id=session_id, generation=gen,
                insight_type='consensus_action',
                description=(
                    f"Consensus ACTION{consensus.get('proposed_action', '?')} "
                    f"for {game_id} with "
                    f"{consensus.get('consensus_ratio', 0)*100:.0f}% agreement"
                ),
                contributing_agents=agent_ids,
                confidence=consensus.get('consensus_ratio', 0.5),
            )
            print(f"    [COLLECTIVE] Consensus: ACTION{consensus.get('proposed_action', '?')} "
                  f"({consensus.get('consensus_ratio', 0)*100:.0f}% agree)")

            # Phase 1.2: Store consensus as a viral package for network distribution
            try:
                consensus_action = consensus.get('proposed_action', 1)
                consensus_ratio = consensus.get('consensus_ratio', 0.5)
                pkg_id = f"consensus_{game_id}_{gen}_{session_id[:8]}"
                action_seq = json.dumps([consensus_action])
                self.db.execute_query("""
                    INSERT OR IGNORE INTO viral_information_packages (
                        package_id, package_name, package_type,
                        action_sequence, virulence, transmission_rate, mutation_rate,
                        discovery_generation, generation_discovered,
                        is_active, last_successful_use_generation,
                        meta_strategy_description
                    ) VALUES (?, ?, 'consensus_action', ?, ?, 0.3, 0.05, ?, ?, 1, ?, ?)
                """, (
                    pkg_id,
                    f"Consensus_{game_id[:12]}_gen{gen}",
                    action_seq,
                    min(1.0, consensus_ratio),  # virulence ~ agreement strength
                    gen, gen, gen,
                    f"Collective consensus ACTION{consensus_action} "
                    f"with {consensus_ratio*100:.0f}% agreement from {len(agent_ids)} agents",
                ))
            except Exception as e:
                import logging as _log
                _log.getLogger(__name__).debug(
                    "[COLLECTIVE] Could not store consensus as viral package: %s", e
                )

        game_results = [r for r in results if r.game_id == game_id]
        best_score = max((r.score for r in game_results), default=0.0)
        cre.complete_session(session_id, final_score=best_score)

        return consensus

    def _find_stuck_games(self, results: List[GameResult]) -> List[str]:
        """Find games where all agents failed to make progress."""
        game_scores: Dict[str, List[float]] = {}
        for result in results:
            game_scores.setdefault(result.game_id, []).append(result.score)

        stuck_games = []
        for game_id, scores in game_scores.items():
            if max(scores) < 0.2:
                stuck_games.append(game_id)
        return stuck_games

    # ------------------------------------------------------------------
    # Generation loop
    # ------------------------------------------------------------------

    def run_generation(self) -> Dict[str, Any]:
        """Run one generation of evolution."""
        print(f"\n{'='*60}")
        print(f"GENERATION {self.current_generation}")
        print(f"{'='*60}")

        games = self.get_available_games()
        if not games:
            print("[ERROR] No games available!")
            return {'games_played': 0, 'wins': 0}

        print(f"[GAMES] {len(games)} available: {games}")

        # ASSIGN OPERATING MODES: Pioneer/Optimizer/Generalist/Exploiter
        mode_assignments = {}
        if self.operating_mode_system:
            try:
                agent_ids = [a.agent_id for a in self.agents]
                mode_assignments = self.operating_mode_system.assign_population_modes(
                    generation=self.current_generation,
                    active_agents=agent_ids,
                    game_id=games[0] if len(games) == 1 else None
                )
                for agent_id, mode_val in mode_assignments.items():
                    self.db.execute_query(
                        "UPDATE agents SET specialization = ? WHERE agent_id = ?",
                        (mode_val, agent_id)
                    )
                if self.verbose:
                    mode_counts: Dict[str, int] = {}
                    for m in mode_assignments.values():
                        mode_counts[m] = mode_counts.get(m, 0) + 1
                    print(f"[MODES] Assigned: {mode_counts}")
            except Exception as e:
                print(f"[WARN] Mode assignment failed, defaulting to generalist: {e}")

        results: List[GameResult] = []
        total_wins = 0
        total_score = 0.0
        agents_played = 0
        agents_skipped = 0

        for agent in self.agents:
            if not self.running:
                break

            try:
                # Select games for this agent
                if self.meta_learning_curriculum:
                    try:
                        agent_games = self.meta_learning_curriculum.select_games_for_agent(
                            agent_id=agent.agent_id,
                            available_games=games,
                            num_games=self.games_per_generation
                        )
                        if not agent_games:
                            agent_games = random.sample(games, min(self.games_per_generation, len(games)))
                    except Exception as e:
                        if self.verbose:
                            print(f"    [CURRICULUM] Fallback to random: {e}")
                        agent_games = random.sample(games, min(self.games_per_generation, len(games)))
                else:
                    agent_games = random.sample(games, min(self.games_per_generation, len(games)))

                print(f"\n[AGENT] {agent.agent_id[:12]}... playing {len(agent_games)} games")

                for game_id in agent_games:
                    if not self.running:
                        break

                    result = self.play_game(agent, game_id)
                    results.append(result)

                    agent.games_played += 1
                    agent.total_score += result.score
                    if result.is_win:
                        agent.wins += 1
                        total_wins += 1
                    total_score += result.score

                    status = "[WIN]" if result.is_win else f"[{result.levels_completed}/{result.total_levels}]"
                    print(f"  {game_id}: {status} score={result.score:.1f} actions={result.actions_taken}")

                    # Store in database (delegates to ResultRecorder)
                    # Task A2: Pass world_model from context_builder for DB persistence
                    _wm = None
                    try:
                        _wm = getattr(self.context_builder, '_world_model', None)
                    except Exception:
                        pass
                    self._result_recorder.store_game_result(
                        result=result,
                        current_generation=self.current_generation,
                        session_id=self._game_player.last_session_id,
                        use_cognitive_router=self._use_cognitive_router,
                        world_model=_wm,
                    )

                # Update curriculum progress
                if self.meta_learning_curriculum:
                    try:
                        self.meta_learning_curriculum.update_stage_progress(agent.agent_id)
                    except Exception as e:
                        if self.verbose:
                            print(f"    [CURRICULUM] Progress update failed: {e}")

                agents_played += 1

            except Exception as e:
                agents_skipped += 1
                print(f"[ERROR] Agent {agent.agent_id[:12]}... failed: {type(e).__name__}: {e}")

        if agents_skipped > 0:
            print(f"\n[WARN] {agents_skipped}/{len(self.agents)} agents skipped due to errors")

        games_played = len(results)
        avg_score = total_score / max(1, games_played)
        win_rate = total_wins / max(1, games_played)

        print(f"\n[SUMMARY] Gen {self.current_generation}: {agents_played} agents, "
              f"{games_played} games, {total_wins} wins ({win_rate*100:.1f}%), avg score: {avg_score:.2f}")

        # COLLECTIVE REASONING on stuck games
        if self.collective_reasoning_engine and total_wins == 0 and self.current_generation > 5:
            try:
                stuck_games = self._find_stuck_games(results)
                for game_to_try in stuck_games[:3]:
                    consensus = self._run_collective_deliberation(game_to_try, results)
                    if consensus:
                        print(f"  [COLLECTIVE] Consensus reached for {game_to_try}")
                    elif self.verbose:
                        print(f"  [COLLECTIVE] No consensus for {game_to_try}")
            except Exception as e:
                if self.verbose:
                    print(f"  [COLLECTIVE-ERR] Collective reasoning failed: {e}")

        # Pipeline assertions
        self.pipe.assert_generation_flow(self.current_generation, games_played)
        self.pipe.print_summary()
        self.pipe.reset_counters()

        # Publish GENERATION_COMPLETE (Phase 0.3)
        gen_stats = {
            'games_played': games_played,
            'wins': total_wins,
            'win_rate': win_rate,
            'avg_score': avg_score,
            'agents_played': agents_played,
            'agents_skipped': agents_skipped,
        }
        self.event_bus.publish(make_event(
            EventType.GENERATION_COMPLETE,
            generation=self.current_generation,
            stats=gen_stats,
        ))

        return gen_stats

    # ------------------------------------------------------------------
    # Evolve
    # ------------------------------------------------------------------

    def evolve(self):
        """Evolve population using full EvolutionaryEngine.

        Features: youth bonus, prestige, genome mutation, crossover,
        survival protection, proper culling.

        Cadence dispatches at 5/10/50 gen intervals for network-level engines.
        """
        print(f"\n[EVOLVE] Evolving population via EvolutionaryEngine...")

        evolution_strategy = {
            **self._evolution_strategy,
            'generation': self.current_generation,
            'population_size': self.population_size,
        }

        try:
            new_population = self.evolutionary_engine.evolve_population(evolution_strategy)

            self.agents = []
            for agent_dict in new_population:
                agent_state = AgentState(
                    agent_id=agent_dict['agent_id'],
                    generation=agent_dict.get('generation', self.current_generation + 1),
                    total_score=agent_dict.get('total_score', 0.0),
                    games_played=agent_dict.get('games_played', 0),
                    wins=agent_dict.get('wins', 0),
                )
                self.agents.append(agent_state)

            print(f"  New population: {len(self.agents)} agents")
            print(f"  Features: youth_bonus, prestige, mutation, crossover, epigenetics")

            if self.agents:
                top_agents = sorted(self.agents, key=lambda a: a.avg_score * (1 + a.win_rate), reverse=True)[:3]
                print(f"  Top performers: {[f'{a.agent_id[:8]}(s={a.avg_score:.1f})' for a in top_agents]}")

            # ---- Every-generation cadence ----

            # HORIZONTAL TRANSFER
            if self.horizontal_transfer_engine:
                try:
                    transfers = self.horizontal_transfer_engine.execute_generation_transfers(
                        generation=self.current_generation,
                        max_transfers_per_agent=2
                    )
                    if transfers > 0:
                        print(f"  [TRANSFER] {transfers} horizontal knowledge transfers completed")
                        if self.verbose:
                            stats = self.horizontal_transfer_engine.get_transfer_statistics(self.current_generation)
                            if stats.get('layer_statistics'):
                                for layer_stat in stats['layer_statistics']:
                                    print(f"    Layer {layer_stat['transfer_layer']}: "
                                          f"{layer_stat['successful_transfers']}/{layer_stat['total_attempts']} "
                                          f"(compat: {layer_stat['avg_compatibility']:.2f})")
                except Exception as e:
                    if self.verbose:
                        print(f"  [TRANSFER-ERR] Horizontal transfer failed: {e}")

            # Phase 6.1: HEALTH GAUGES (every generation)
            if self.health_gauges:
                try:
                    gauge_result = self.health_gauges.evaluate(self.current_generation)
                    unhealthy = gauge_result.get('unhealthy_gauges', [])
                    if unhealthy:
                        print(f"  [GAUGES] {len(unhealthy)} unhealthy: {', '.join(unhealthy)}")
                        # Emergency: trigger health responder immediately
                        if gauge_result.get('emergency') and self.health_responder and self.network_intelligence_engine:
                            try:
                                snap = self.network_intelligence_engine.capture_ecosystem_snapshot(self.current_generation)
                                adj = self.health_responder.get_adjustments(snap, self.current_generation)
                                if adj.get('triggered_rules'):
                                    self.health_responder.apply_adjustments(adj, self._evolution_strategy)
                                    print(f"  [GAUGES] EMERGENCY correction applied: {len(adj['triggered_rules'])} rules")
                            except Exception:
                                pass
                    elif self.verbose:
                        health = gauge_result.get('memory_retention_score', 0)
                        print(f"  [GAUGES] All 7 gauges healthy (overall={self.health_gauges._overall_health(gauge_result):.2f})")
                except Exception as e:
                    if self.verbose:
                        print(f"  [GAUGES-ERR] Health gauge evaluation failed: {e}")

            # Phase 6.2: CONTRACT SPOT-CHECK (every generation)
            if hasattr(self, 'pipe') and self.pipe:
                try:
                    cstats = self.pipe.run_contract_spot_check(self.current_generation)
                    if cstats['failed'] > 0:
                        print(f"  [CONTRACT] {cstats['failed']}/{cstats['checked']} contract violations detected")
                    elif self.verbose and cstats['checked'] > 0:
                        print(f"  [CONTRACT] {cstats['passed']}/{cstats['checked']} contracts OK")
                except Exception as e:
                    if self.verbose:
                        print(f"  [CONTRACT-ERR] Contract spot-check failed: {e}")

            # ---- Every-5-gen cadence ----

            if self.current_generation % 5 == 0:
                # NETWORK INTELLIGENCE: Capture ecosystem snapshot
                if self.network_intelligence_engine:
                    try:
                        # Phase 6B (Affinity): Update alignment velocities BEFORE
                        # snapshot so the snapshot reads fresh values.
                        try:
                            n_vel = self.network_intelligence_engine.update_all_alignment_velocities(
                                self.current_generation
                            )
                        except Exception as vel_err:
                            n_vel = 0
                            if self.verbose:
                                print(f"  [AFFINITY-ERR] Alignment velocity update failed: {vel_err}")

                        snapshot = self.network_intelligence_engine.capture_ecosystem_snapshot(self.current_generation)
                        health_status = snapshot.get('health_status', 'unknown')
                        health_score = snapshot.get('health_score', 0.0)
                        print(f"  [NETWORK] Ecosystem health: {health_status} (score: {health_score:.3f})")

                        avg_vel = snapshot.get('alignment_velocity_avg', 0.0)
                        if avg_vel > 0 or self.verbose:
                            print(f"  [AFFINITY] Alignment velocity: avg={avg_vel:.4f} ({n_vel} agents)")

                        if self.verbose:
                            print(f"    Knowledge: {snapshot.get('total_sequences', 0)} sequences, "
                                  f"{snapshot.get('total_patterns', 0)} patterns, "
                                  f"{snapshot.get('unique_games_solved', 0)} games solved")
                            print(f"    Diversity index: {snapshot.get('knowledge_diversity_index', 0):.3f}")

                        # Phase 1.3: Health Responder
                        if self.health_responder:
                            try:
                                adj = self.health_responder.get_adjustments(snapshot, self.current_generation)
                                triggered = adj.get('triggered_rules', [])
                                if triggered:
                                    self.health_responder.apply_adjustments(adj, self._evolution_strategy)
                                    print(f"  [HEALTH] {len(triggered)} corrective rule(s) fired:")
                                    for rule_desc in triggered:
                                        print(f"    - {rule_desc}")
                                elif self.verbose:
                                    print(f"  [HEALTH] No corrective rules triggered")

                                # Phase 5.3: Fine-grained adaptive parameter tuning
                                mut_delta = self.health_responder.get_mutation_adjustment(
                                    snapshot, self.current_generation,
                                )
                                if abs(mut_delta) > 0.001:
                                    old_mr = self._evolution_strategy.get('mutation_rate', 0.2)
                                    self._evolution_strategy['mutation_rate'] = max(
                                        0.01, min(0.99, old_mr + mut_delta)
                                    )
                                    if self.verbose:
                                        print(f"  [HEALTH] Mutation rate: {old_mr:.3f} -> {self._evolution_strategy['mutation_rate']:.3f}")

                                role_deltas = self.health_responder.get_role_allocation(
                                    snapshot, self.current_generation,
                                )
                                if self.operating_mode_system and any(
                                    abs(v) > 0.001 for v in role_deltas.values()
                                ):
                                    self.operating_mode_system.apply_health_adjustments(role_deltas)
                                    if self.verbose:
                                        print(f"  [HEALTH] Role allocation adjusted: {role_deltas}")

                                explore_mult = self.health_responder.get_exploration_budget_multiplier(
                                    snapshot, self.current_generation,
                                )
                                if abs(explore_mult - 1.0) > 0.01:
                                    self._evolution_strategy['exploration_budget_mult'] = explore_mult
                                    if self.verbose:
                                        print(f"  [HEALTH] Exploration budget multiplier: {explore_mult:.2f}")

                            except Exception as he:
                                if self.verbose:
                                    print(f"  [HEALTH-ERR] Responder failed: {he}")

                    except Exception as e:
                        if self.verbose:
                            print(f"  [NETWORK-ERR] Ecosystem snapshot failed: {e}")

                # RESONANCE DETECTION: Scan compressed templates
                if self.resonance_detector:
                    try:
                        belief_patterns = self.resonance_detector.detect_resonance(
                            generation=self.current_generation
                        )
                        template_patterns = self.resonance_detector.scan_compressed_templates(
                            generation=self.current_generation
                        )
                        visual_patterns = self.resonance_detector.detect_visual_resonance(
                            generation=self.current_generation
                        )

                        total = len(belief_patterns) + len(template_patterns) + len(visual_patterns)
                        if total > 0:
                            print(f"  [RESONANCE] {len(belief_patterns)} belief + "
                                  f"{len(template_patterns)} template + "
                                  f"{len(visual_patterns)} visual resonance patterns")

                            combined = self.resonance_detector.get_combined_resonance()
                            multi_signal = sum(
                                1 for v in combined.values() if v['active_signals'] >= 2
                            )
                            if multi_signal > 0:
                                print(f"  [RESONANCE] {multi_signal} game-type pair(s) "
                                      f"with multi-signal agreement")
                        elif self.verbose:
                            print(f"  [RESONANCE] No new resonance patterns detected")
                    except Exception as e:
                        if self.verbose:
                            print(f"  [RESONANCE-ERR] Resonance detection failed: {e}")

            # ---- Every-10-gen cadence ----

            if self.current_generation % 10 == 0:
                # CONCEPT DISCOVERY
                if self.concept_discovery_engine:
                    try:
                        new_concepts = self.concept_discovery_engine.check_concept_emergence()
                        if new_concepts:
                            print(f"  [CONCEPTS] Discovered {len(new_concepts)} concept candidates")
                            if self.verbose:
                                for concept in new_concepts[:3]:
                                    print(f"    - {concept.get('pattern', 'unnamed')[:20]}: {concept.get('confidence', 0):.2f}")
                    except Exception as e:
                        if self.verbose:
                            print(f"  [CONCEPT-ERR] Concept discovery failed: {e}")

                # PRIMITIVE UNLOCK
                if self.primitive_unlock_manager:
                    try:
                        unlocked = self.primitive_unlock_manager.check_all_unlock_readiness(
                            generation=self.current_generation
                        )
                        if unlocked:
                            print(f"  [UNLOCK] {len(unlocked)} primitive(s) unlocked: "
                                  f"{', '.join(unlocked)}")
                        elif self.verbose:
                            summary = self.primitive_unlock_manager.get_unlock_summary()
                            emerging = summary.get('emerging', 0)
                            if emerging > 0:
                                print(f"  [UNLOCK] {emerging} primitive(s) emerging, none ready yet")
                    except Exception as e:
                        if self.verbose:
                            print(f"  [UNLOCK-ERR] Primitive unlock check failed: {e}")

                # Phase 6.3: SYSTEM DIAGNOSTIC (every 10 generations)
                if self.system_diagnostic:
                    try:
                        diag = self.system_diagnostic.run(self.current_generation)
                        status = diag.get('health_status', 'unknown')
                        score = diag.get('overall_health', 0.0)
                        print(f"  [DIAGNOSTIC] System health: {status} ({score:.3f})")
                        disc = diag.get('disconnected_systems', [])
                        if disc:
                            names = ', '.join(d['table'] for d in disc[:3])
                            print(f"  [DIAGNOSTIC] Disconnected: {names}")
                        bottlenecks = diag.get('bottleneck_systems', [])
                        if bottlenecks:
                            names = ', '.join(b['table'] for b in bottlenecks[:3])
                            print(f"  [DIAGNOSTIC] Bottlenecks: {names}")
                        util = diag.get('knowledge_utilisation', 0.0)
                        if self.verbose:
                            print(f"  [DIAGNOSTIC] Knowledge util: {util:.1%}, "
                                  f"compression: {diag.get('compression_effectiveness', 0):.3f}, "
                                  f"resonance conn: {diag.get('resonance_connectivity', 0):.3f}")
                    except Exception as e:
                        if self.verbose:
                            print(f"  [DIAGNOSTIC-ERR] System diagnostic failed: {e}")

            # ---- Every-50-gen cadence ----

            if self.current_generation % 50 == 0:
                # AGENT LIFECYCLE: Clean up ancient inactive agents
                if self.lifecycle_manager:
                    try:
                        cleanup_stats = self.lifecycle_manager.cleanup_ancient_inactive_agents(
                            current_generation=self.current_generation,
                            dry_run=False
                        )
                        total_deleted = cleanup_stats.get('total_deleted', 0)
                        if total_deleted > 0:
                            print(f"  [LIFECYCLE] Cleaned {total_deleted} ancient inactive agents")
                    except Exception as e:
                        if self.verbose:
                            print(f"  [LIFECYCLE-ERR] Agent cleanup failed: {e}")

        except Exception as e:
            print(f"  [WARN] EvolutionaryEngine failed, using fallback: {e}")
            self._simple_evolve_fallback()

        # Pipeline assertion: population size after evolution
        self.pipe.assert_population_size(
            self.population_size, self.current_generation
        )

    def _simple_evolve_fallback(self):
        """Fallback simple evolution if EvolutionaryEngine fails."""
        def fitness(a: AgentState) -> float:
            return a.avg_score * (1 + a.win_rate)

        self.agents.sort(key=fitness, reverse=True)
        keep_count = max(1, len(self.agents) // 2)
        survivors = self.agents[:keep_count]
        culled = self.agents[keep_count:]

        if culled:
            culled_ids = [a.agent_id for a in culled]
            placeholders = ','.join(['?' for _ in culled_ids])
            self.db.execute_query(f"""
                UPDATE agents SET is_active = FALSE
                WHERE agent_id IN ({placeholders})
            """, culled_ids)
            print(f"  [FALLBACK] Culled {len(culled)} underperformers")

        offspring = []
        while len(survivors) + len(offspring) < self.population_size:
            parent = random.choice(survivors)
            child = AgentState(
                agent_id=self._create_agent_id(),
                generation=self.current_generation + 1,
            )
            offspring.append(child)
            genome = '{"exploration_rate": 0.3, "learning_rate": 0.1}'
            self.db.execute_query("""
                INSERT INTO agents (
                    agent_id, generation, agent_type, genome, specialization,
                    parent_ids, created_at, is_active
                ) VALUES (?, ?, 'evolved', ?, 'generalist', ?, datetime('now'), TRUE)
            """, (child.agent_id, child.generation, genome, f'["{parent.agent_id}"]'))

        self.agents = survivors + offspring
        print(f"  [FALLBACK] New population: {len(self.agents)}")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        """Main evolution loop."""
        print("\n" + "="*60)
        print("EVOLUTION RUNNER")
        print("="*60)
        print(f"Mode: {self.mode.upper()}")
        print(f"Population: {self.population_size}")
        print(f"Games/Gen: {self.games_per_generation}")
        print(f"Max Generations: {self.max_generations}")
        if self.target_game:
            print(f"Target Game: {self.target_game}")
        print("="*60)

        self.agents = self.initialize_population()

        target_generation = self._start_generation + self.max_generations
        while self.running and self.current_generation < target_generation:
            stats = self.run_generation()

            if not self.running:
                break

            self.evolve()

            # Post-generation health checks (delegates to HealthMonitor)
            self._health_monitor.run_generation_health_checks(
                self.current_generation, stats
            )

            # Rule 12: Safe cleanup every 10 generations
            self._health_monitor.run_safe_cleanup(self.current_generation)

            self.current_generation += 1

        print("\n" + "="*60)
        print("EVOLUTION COMPLETE")
        print("="*60)
        print(f"Generations: {self.current_generation}")
        print(f"Final population: {len(self.agents)}")

        if self.agents:
            best = max(self.agents, key=lambda a: a.avg_score)
            print(f"Best agent: {best.agent_id} (avg score: {best.avg_score:.2f}, wins: {best.wins})")


def main():
    parser = argparse.ArgumentParser(description='Evolution Runner')
    parser.add_argument('--mode', choices=['online', 'offline', 'normal'], default='normal',
                       help='Operation mode')
    parser.add_argument('--population', type=int, default=100,
                       help='Population size (default: 100, recommended: 50-500)')
    parser.add_argument('--games-per-gen', type=int, default=5,
                       help='Games per generation per agent')
    parser.add_argument('--max-generations', type=int, default=10,
                       help='Maximum generations')
    parser.add_argument('--max-actions', type=int, default=None,
                       help='Max actions per game (default: 2500, or 7500 in offline mode)')
    parser.add_argument('--game', type=str, default=None,
                       help='Target specific game (e.g., ls20)')
    parser.add_argument('--test', action='store_true',
                       help='Quick test mode (1 agent, 1 game, 1 gen)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show each action and score during gameplay')
    parser.add_argument('--rungs', type=str, default='comprehensive',
                       choices=['comprehensive', 'efficiency', 'minimal', 'llm_optimal',
                                'human_brain', 'frontier_exploration', 'phased_orientation',
                                'phased_hypothesis', 'phased_exploitation'],
                       help='Rung ordering preset (default: comprehensive)')
    parser.add_argument('--log-file', type=str, default=None,
                       help='Write all output to this file (unbuffered)')
    parser.add_argument('--observe', action='store_true',
                       help='Enable Tier 2 observation: save frame snapshots at '
                            'level-ups, game-overs, and every 20th action')

    args = parser.parse_args()

    # Determine max_actions based on mode if not explicitly set
    if args.max_actions is None:
        if args.mode == 'offline':
            args.max_actions = 7500
        else:
            args.max_actions = 2500

    # Test mode overrides
    if args.test:
        args.population = 1
        args.games_per_gen = 1
        args.max_generations = 1
        args.max_actions = 300

    # Log file redirect - always write to log/ directory (Rule 2 exception for CLI debug)
    log_file_handle = None
    if args.log_file:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.basename(args.log_file)
        log_path = os.path.join(log_dir, log_filename)
        log_file_handle = open(log_path, 'w', encoding='utf-8', buffering=1)
        sys.stdout = log_file_handle
        sys.stderr = log_file_handle
        import logging
        file_handler = logging.StreamHandler(log_file_handle)
        file_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(file_handler)

    runner = EvolutionRunner(
        mode=args.mode,
        population_size=args.population,
        games_per_generation=args.games_per_gen,
        max_generations=args.max_generations,
        max_actions_per_game=args.max_actions,
        target_game=args.game,
        verbose=args.verbose,
        rung_ordering=args.rungs,
        observe=getattr(args, 'observe', False),
    )

    runner.run()

    # Clean up log file
    if log_file_handle:
        log_file_handle.flush()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        log_file_handle.close()


if __name__ == "__main__":
    main()
