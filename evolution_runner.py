#!/usr/bin/env python3
"""
Evolution Runner - Clean SDK-based implementation
=================================================

Simple, direct implementation using the arc_agi SDK.
Replaces the bloated autonomous_evolution_runner.py.

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
import asyncio
import hashlib
import json
import random
import signal
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import requests

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# SDK imports
from arc_agi import Arcade, OperationMode
from arcengine import GameAction, GameState

# Local imports
from database_interface import DatabaseInterface
from decision_rung_system import DecisionRungSystem

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
from engines.perception.property_extractor import PropertyExtractor, properties_to_json
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


@dataclass
class AgentState:
    """Minimal agent state for evolution."""
    agent_id: str
    generation: int = 0
    total_score: float = 0.0
    games_played: int = 0
    wins: int = 0

    @property
    def avg_score(self) -> float:
        return self.total_score / max(1, self.games_played)

    @property
    def win_rate(self) -> float:
        return self.wins / max(1, self.games_played)


@dataclass
class GameResult:
    """Result of a single game."""
    game_id: str
    agent_id: str
    score: float
    levels_completed: int
    total_levels: int
    is_win: bool
    actions_taken: int
    action_sequence: List[str] = field(default_factory=list)


class EvolutionRunner:
    """
    Clean evolution runner using arc_agi SDK directly.

    Core loop:
    1. Create agents
    2. Each agent plays games
    3. Record results
    4. Evolve (select best, mutate, create offspring)
    5. Repeat
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
    ):
        self.mode = mode
        self.verbose = verbose
        self.rung_ordering = rung_ordering
        self.db = DatabaseInterface(db_path)
        self.population_size = population_size
        self.games_per_generation = games_per_generation
        self.max_generations = max_generations
        self.max_actions = max_actions_per_game
        self.target_game = target_game

        # SDK setup
        op_mode = {
            'offline': OperationMode.OFFLINE,
            'online': OperationMode.ONLINE,
            'normal': OperationMode.NORMAL,
        }.get(mode.lower(), OperationMode.NORMAL)
        self.op_mode = op_mode  # Store for tag generation

        self.arcade = Arcade(operation_mode=op_mode)

        # Scorecard will be created per-agent with proper tags
        self.current_scorecard_id: Optional[str] = None

        # Cognitive Router - Full architecture implementation (Phases 1-11)
        # This implements the Blackboard + Meta-Planner + Cognitive Graph architecture
        # with Phenomenology, Epistemic, and Eisenhower layers
        self.cognitive_router: Optional[CognitiveRouter] = None
        self.routing_trace_store: Optional[RoutingTraceStore] = None
        self._use_cognitive_router = False  # Will be set True if router initializes

        if COGNITIVE_ROUTER_AVAILABLE:
            try:
                # Configure router per architecture spec
                # max_iterations=12: With ~50 rungs, 12 iterations x 5 per call
                # = 60 rung evals max. With agreement boost, commits in 2-4
                # iterations when rungs agree (0.6+0.15=0.75>0.50).
                # commit_threshold=0.50: Single confident rung (0.6) can now
                # commit. Previous 0.65 was unreachable for individual rungs,
                # causing 100% fallback to random for 5000+ generations.
                router_config = RouterConfig(
                    max_iterations=12,
                    max_rungs_per_call=5,
                    commit_threshold=0.50,
                    time_budget_seconds=5.0,
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

        # Decision system - uses COGNITIVE strategy when router available, LADDER fallback
        strategy = 'cognitive' if self._use_cognitive_router else 'ladder'
        self.decision_system = DecisionRungSystem(
            strategy=strategy,
            cognitive_router=self.cognitive_router,
            routing_trace_store=self.routing_trace_store  # For recording decision traces
        )
        self.decision_system.load_ordering(self.rung_ordering)

        if self.verbose and self._use_cognitive_router:
            print(f"[INIT] DecisionSystem strategy: COGNITIVE (full routing pipeline)")
        elif self.verbose:
            print(f"[INIT] DecisionSystem strategy: LADDER (fallback mode)")

        # Evolutionary engine for sophisticated evolution (youth bonus, prestige, mutation, etc.)
        self.evolutionary_engine = EvolutionaryEngine(self.db)

        # State
        self.agents: List[AgentState] = []
        self.current_generation = self._load_generation_from_db()
        self._start_generation = self.current_generation  # Track where this session began
        self.running = True

        # Session tracking for action traces
        self._current_session_id: Optional[str] = None

        # Symbolic reasoning components (Phase 0-1)
        self.player_localizer = PlayerLocalizer(confidence_threshold=0.6)
        self.property_extractor = PropertyExtractor(color_quantization=16)
        self._prev_frame: Optional[np.ndarray] = None  # For localization
        self._prev_properties: Optional[dict] = None   # For change detection

        # Viral package engine for network knowledge sharing
        self.viral_package_engine = None
        if VIRAL_PACKAGE_AVAILABLE:
            try:
                self.viral_package_engine = ViralPackageEngine(self.db)
                if self.verbose:
                    print("[INIT] Viral package engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize viral package engine: {e}")

        # Network Intelligence Engine - ecosystem health monitoring
        # Per Unified Theory: "The database IS the AGI. Agents are temporary cells."
        self.network_intelligence_engine = None
        if NETWORK_INTELLIGENCE_AVAILABLE:
            try:
                self.network_intelligence_engine = NetworkIntelligenceEngine(self.db)
                if self.verbose:
                    print("[INIT] Network intelligence engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize network intelligence engine: {e}")

        # Horizontal Transfer Engine - viral knowledge spread
        # Per Unified Theory: "Intelligence spreads through horizontal information transfer"
        self.horizontal_transfer_engine = None
        if HORIZONTAL_TRANSFER_AVAILABLE:
            try:
                self.horizontal_transfer_engine = HorizontalTransferEngine(self.db)
                if self.verbose:
                    print("[INIT] Horizontal transfer engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize horizontal transfer engine: {e}")

        # Meta-Learning Curriculum - intelligent game selection
        # Per Unified Theory: 4-stage curriculum for generalization
        self.meta_learning_curriculum = None
        if META_LEARNING_AVAILABLE:
            try:
                self.meta_learning_curriculum = MetaLearningCurriculum(self.db)
                if self.verbose:
                    print("[INIT] Meta-learning curriculum initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize meta-learning curriculum: {e}")

        # Agent Lifecycle Manager - safe agent birth/death/revival
        # Per Unified Theory: "Good players never deleted, just retired"
        self.lifecycle_manager = None
        if LIFECYCLE_MANAGER_AVAILABLE:
            try:
                self.lifecycle_manager = AgentLifecycleManager(self.db)
                if self.verbose:
                    print("[INIT] Agent lifecycle manager initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize lifecycle manager: {e}")

        # Collective Reasoning Engine - multi-agent ensemble intelligence
        # Per Unified Theory: "Top performers collaborate on challenging games"
        self.collective_reasoning_engine = None
        if COLLECTIVE_REASONING_AVAILABLE:
            try:
                self.collective_reasoning_engine = CollectiveReasoningEngine(self.db)
                if self.verbose:
                    print("[INIT] Collective reasoning engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize collective reasoning engine: {e}")

        # Concept Discovery Engine - high-level concept discovery (CODS Tier 4)
        # Per Unified Theory: "Concepts emerge from cross-game pattern recognition"
        self.concept_discovery_engine = None
        if CONCEPT_DISCOVERY_AVAILABLE:
            try:
                self.concept_discovery_engine = ConceptDiscoveryEngine(self.db)
                if self.verbose:
                    print("[INIT] Concept discovery engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize concept discovery engine: {e}")

        # Universal Pattern Engine - cross-game pattern transfer
        # Per Unified Theory: "Patterns that transfer across games become universal"
        self.universal_pattern_engine = None
        if UNIVERSAL_PATTERN_AVAILABLE:
            try:
                self.universal_pattern_engine = UniversalPatternEngine()
                if self.verbose:
                    print("[INIT] Universal pattern engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize universal pattern engine: {e}")

        # Games-as-Teachers Engine - lesson extraction from wins
        # Per Unified Theory: "Games are teachers - each level is a lesson"
        self.games_as_teachers_engine = None
        if GAMES_AS_TEACHERS_AVAILABLE:
            try:
                self.games_as_teachers_engine = GamesAsTeachersEngine(self.db)
                if self.verbose:
                    print("[INIT] Games-as-teachers engine initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize games-as-teachers engine: {e}")

        # Agent Operating Mode System - assigns roles per Unified Theory
        # Per Unified Theory: "Roles emerge from agent's wA/wB ratios"
        self.operating_mode_system = None
        if OPERATING_MODE_AVAILABLE:
            try:
                self.operating_mode_system = AgentOperatingModeSystem(self.db)
                if self.verbose:
                    print("[INIT] Agent operating mode system initialized")
            except Exception as e:
                print(f"[WARN] Could not initialize operating mode system: {e}")

    def _load_generation_from_db(self) -> int:
        """Load the next generation number from database.

        Queries the max generation from game_results and agents tables
        so we continue counting from where the last run left off.
        """
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

    def _compute_frame_hash(self, obs: Any) -> str:
        """Compute hash of frame state for topology matching."""
        if obs is None:
            return "null_frame"
        try:
            # Get frame data - try multiple attributes
            frame_data = None
            for attr in ['frame', 'state', 'grid', 'observation']:
                if hasattr(obs, attr):
                    frame_data = getattr(obs, attr)
                    break

            if frame_data is None:
                frame_data = str(obs)

            # Convert to string if needed
            if hasattr(frame_data, 'tolist'):
                frame_str = str(frame_data.tolist())
            else:
                frame_str = str(frame_data)

            return hashlib.md5(frame_str.encode()).hexdigest()[:16]
        except Exception:
            return "hash_error"

    def _record_action_trace(
        self,
        game_id: str,
        action_num: int,
        obs_before: Any,
        obs_after: Any,
        score_before: float,
        score_after: float,
        level_before: int,
        level_after: int,
        is_game_over: bool,
        coordinates: Optional[Dict] = None,
    ) -> None:
        """Record action trace with frame hash and score change.

        This is CRITICAL for learning - without this, the network has no memory.
        Coordinates are stored for ACTION6 spatial learning.
        """
        try:
            # Compute frame hashes
            frame_hash_before = self._compute_frame_hash(obs_before)
            frame_hash_after = self._compute_frame_hash(obs_after)
            frame_changed = frame_hash_before != frame_hash_after

            # Get frame data as string
            frame_before_str = None
            frame_after_str = None
            try:
                if obs_before and hasattr(obs_before, 'frame'):
                    frame_before_str = str(obs_before.frame.tolist() if hasattr(obs_before.frame, 'tolist') else obs_before.frame)
                if obs_after and hasattr(obs_after, 'frame'):
                    frame_after_str = str(obs_after.frame.tolist() if hasattr(obs_after.frame, 'tolist') else obs_after.frame)
            except Exception:
                pass

            # Serialize coordinates for ACTION6
            coords_json = None
            if coordinates:
                import json as json_lib
                coords_json = json_lib.dumps(coordinates)

            # Record to database
            self.db.execute_query("""
                INSERT INTO action_traces (
                    session_id, game_id, action_number, coordinates, timestamp,
                    frame_before, frame_after, frame_changed,
                    score_before, score_after, score_change,
                    level_number, resulted_in_game_over,
                    frame_hash, created_at
                ) VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                self._current_session_id,
                game_id,
                action_num,
                coords_json,
                frame_before_str,
                frame_after_str,
                1 if frame_changed else 0,
                score_before,
                score_after,
                score_after - score_before,
                level_after,
                1 if is_game_over else 0,
                frame_hash_before,
            ))
        except Exception as e:
            # Don't let trace recording break gameplay
            if self.verbose:
                print(f"    [TRACE-ERR] {e}")

    def _get_frame_array(self, obs: Any) -> Optional[np.ndarray]:
        """Extract frame as numpy array from observation."""
        if obs is None:
            return None
        try:
            # Try multiple attributes
            for attr in ['frame', 'grid', 'observation']:
                if hasattr(obs, attr):
                    data = getattr(obs, attr)
                    if isinstance(data, np.ndarray):
                        return data
                    if isinstance(data, list):
                        # Frame data from ARC games is often a list
                        return np.array(data, dtype=np.uint8)
                    if hasattr(data, 'tolist'):
                        return np.array(data)
            return None
        except Exception:
            return None

    def _record_player_state(
        self,
        game_id: str,
        action_num: int,
        action_taken: str,
        obs_before: Any,
        obs_after: Any,
        action_result: str,
        level_number: int,
    ) -> Optional[dict]:
        """
        Record player state for symbolic reasoning (Phase 0-1).

        1. Attempt to localize player sprite
        2. Extract properties if confident
        3. Detect property changes
        4. Record to player_state_history table

        Returns current properties dict or None.
        """
        try:
            # Get frames as numpy arrays
            frame_before = self._get_frame_array(obs_before)
            frame_after = self._get_frame_array(obs_after)

            if frame_before is None or frame_after is None:
                return None

            # Step 1: Attempt player localization
            localization = self.player_localizer.localize(
                frame_before, frame_after, action_taken
            )

            player_region = None
            player_bbox = localization.get('region')
            confidence = localization.get('confidence', 0.0)

            # Step 2: Extract properties if confident about player location
            current_properties = None
            if confidence >= 0.5 and player_bbox is not None:
                player_region = self.player_localizer.get_player_region(frame_after)
                if player_region is not None:
                    current_properties = self.property_extractor.extract_properties(player_region)

            # Step 3: Detect property changes
            property_changes = {}
            if self._prev_properties and current_properties:
                property_changes = self.property_extractor.properties_changed(
                    self._prev_properties, current_properties
                )

                # PHASE 2: Record property transformations to database
                if property_changes:
                    self._record_property_transformations(
                        game_id=game_id,
                        level_number=level_number,
                        player_bbox=player_bbox,
                        property_changes=property_changes
                    )
                    if self.verbose:
                        for prop, change in property_changes.items():
                            print(f"    [PROP] {prop}: {change['from']} -> {change['to']}")

            # PHASE 3: Track goal outcomes (success/failure at goals)
            if action_result in ('success', 'win'):
                self._record_goal_outcome(
                    game_id=game_id,
                    level_number=level_number,
                    player_bbox=player_bbox,
                    properties=current_properties,
                    succeeded=True
                )

            # Step 4: Record to database
            props_json = properties_to_json(current_properties)

            self.db.execute_query("""
                INSERT INTO player_state_history (
                    session_id, game_id, level_number, action_number,
                    player_region_x, player_region_y, player_region_w, player_region_h,
                    localization_confidence, properties_json,
                    dominant_color, shape_phash, orientation,
                    action_taken, action_resulted_in, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                self._current_session_id,
                game_id,
                level_number,
                action_num,
                player_bbox[0] if player_bbox else None,
                player_bbox[1] if player_bbox else None,
                player_bbox[2] if player_bbox else None,
                player_bbox[3] if player_bbox else None,
                confidence,
                props_json,
                current_properties.get('dominant_color') if current_properties else None,
                current_properties.get('shape_signature') if current_properties else None,
                current_properties.get('orientation') if current_properties else None,
                action_taken,
                action_result,
            ))

            # Update state for next iteration
            self._prev_frame = frame_after
            self._prev_properties = current_properties

            return current_properties

        except Exception as e:
            if self.verbose:
                print(f"    [STATE-ERR] {e}")
            return None

    def _record_property_transformations(
        self,
        game_id: str,
        level_number: int,
        player_bbox: Optional[tuple],
        property_changes: dict
    ) -> None:
        """
        Record property transformations to database (Phase 2).

        When the player's properties change (color, shape, orientation),
        record what changed and where it happened. This builds a knowledge
        base of "transformer" locations in the game.
        """
        try:
            for prop_name, change in property_changes.items():
                # Check if this exact transformation was seen before
                existing = self.db.execute_query("""
                    SELECT id, times_observed FROM property_transformations
                    WHERE game_id = ? AND level_number = ?
                      AND object_position_x = ? AND object_position_y = ?
                      AND property_changed = ?
                      AND value_before = ? AND value_after = ?
                """, (
                    game_id, level_number,
                    player_bbox[0] if player_bbox else None,
                    player_bbox[1] if player_bbox else None,
                    prop_name,
                    str(change.get('from')),
                    str(change.get('to')),
                ))

                row = existing.fetchone() if existing else None

                if row:
                    # Update existing record
                    new_times = row[1] + 1
                    new_confidence = min(0.99, 0.5 + (new_times * 0.1))
                    self.db.execute_query("""
                        UPDATE property_transformations SET
                            times_observed = ?,
                            confidence = ?,
                            last_observed = datetime('now')
                        WHERE id = ?
                    """, (new_times, new_confidence, row[0]))
                else:
                    # Insert new record
                    self.db.execute_query("""
                        INSERT INTO property_transformations (
                            game_id, level_number,
                            object_position_x, object_position_y,
                            property_changed, value_before, value_after,
                            times_observed, confidence, created_at, last_observed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0.5, datetime('now'), datetime('now'))
                    """, (
                        game_id,
                        level_number,
                        player_bbox[0] if player_bbox else None,
                        player_bbox[1] if player_bbox else None,
                        prop_name,
                        str(change.get('from')),
                        str(change.get('to')),
                    ))
        except Exception as e:
            if self.verbose:
                print(f"    [TRANSFORM-ERR] {e}")

    def _record_goal_outcome(
        self,
        game_id: str,
        level_number: int,
        player_bbox: Optional[tuple],
        properties: Optional[dict],
        succeeded: bool
    ) -> None:
        """
        Record goal outcome to build requirement knowledge (Phase 3).

        When a player succeeds or fails at a goal position, record their
        properties at that moment. Over time, this reveals what properties
        are required to complete each goal.
        """
        if properties is None:
            return

        try:
            # Determine goal_index from level (simplified - could track multiple goals)
            goal_index = 0  # For now, assume single goal per level

            # Get current stats for this goal
            existing = self.db.execute_query("""
                SELECT id, times_succeeded, times_failed
                FROM goal_requirements
                WHERE game_id = ? AND level_number = ? AND goal_index = ?
            """, (game_id, level_number, goal_index))

            row = existing.fetchone() if existing else None

            if row:
                # Update existing record
                if succeeded:
                    new_succeeded = row[1] + 1
                    new_failed = row[2]
                else:
                    new_succeeded = row[1]
                    new_failed = row[2] + 1

                total = new_succeeded + new_failed
                new_confidence = new_succeeded / total if total > 0 else 0.0

                self.db.execute_query("""
                    UPDATE goal_requirements SET
                        times_succeeded = ?,
                        times_failed = ?,
                        confidence = ?,
                        required_dominant_color = ?,
                        required_shape_phash = ?,
                        required_orientation = ?,
                        last_observed = datetime('now')
                    WHERE id = ?
                """, (
                    new_succeeded,
                    new_failed,
                    new_confidence,
                    str(properties.get('dominant_color')) if succeeded else None,
                    properties.get('shape_signature') if succeeded else None,
                    properties.get('orientation') if succeeded else None,
                    row[0],
                ))
            else:
                # Insert new record
                times_succeeded = 1 if succeeded else 0
                times_failed = 0 if succeeded else 1
                confidence = 1.0 if succeeded else 0.0

                self.db.execute_query("""
                    INSERT INTO goal_requirements (
                        game_id, level_number, goal_index,
                        goal_position_x, goal_position_y,
                        required_dominant_color, required_shape_phash, required_orientation,
                        times_succeeded, times_failed, confidence,
                        created_at, last_observed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    game_id,
                    level_number,
                    goal_index,
                    player_bbox[0] if player_bbox else None,
                    player_bbox[1] if player_bbox else None,
                    str(properties.get('dominant_color')) if succeeded else None,
                    properties.get('shape_signature') if succeeded else None,
                    properties.get('orientation') if succeeded else None,
                    times_succeeded,
                    times_failed,
                    confidence,
                ))
        except Exception as e:
            if self.verbose:
                print(f"    [GOAL-ERR] {e}")

        # Signal handling
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        print("\n[STOP] Shutdown requested...")
        self.running = False

    def _create_agent_id(self) -> str:
        """Generate unique agent ID."""
        import uuid
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

            # Default genome
            genome = '{"exploration_rate": 0.3, "learning_rate": 0.1}'

            # Store in database
            self.db.execute_query("""
                INSERT OR REPLACE INTO agents (
                    agent_id, generation, agent_type, genome, specialization,
                    created_at, is_active
                ) VALUES (?, ?, 'evolved', ?, 'generalist', datetime('now'), TRUE)
            """, (agent.agent_id, 0, genome))

        print(f"[OK] Created {len(agents)} agents")
        return agents

    def _create_scorecard_tags(self, agent: AgentState, game_id: str) -> List[str]:
        """
        Generate scorecard tags in the format:
        branch_Ouroboros-v3, online/offline, game_{type}, agent, agent_{id}, mode_{role}, gen_{n}
        """
        # Determine mode string
        if self.op_mode == OperationMode.ONLINE:
            mode_tag = "online"
        elif self.op_mode == OperationMode.OFFLINE:
            mode_tag = "offline"
        else:
            mode_tag = "normal"

        # Get game type (first 4 chars, e.g., "ls20")
        game_type = game_id[:4] if len(game_id) >= 4 else game_id

        # Get agent role from database (default to generalist)
        role = "generalist"
        try:
            result = self.db.execute_query(
                "SELECT specialization FROM agents WHERE agent_id = ?",
                (agent.agent_id,)
            )
            if result:
                role = result[0].get('specialization', 'generalist') or 'generalist'
        except Exception:
            pass

        return [
            "branch_Ouroboros-v3",
            mode_tag,
            f"game_{game_type}",
            "agent",
            f"agent_{agent.agent_id.replace('agent_', '')}",  # Remove prefix if present
            f"mode_{role}",
            f"gen_{agent.generation}",
        ]

    def _get_or_create_scorecard(self, agent: AgentState, game_id: str) -> Optional[str]:
        """Get or create a scorecard with proper tags for this agent/game."""
        try:
            tags = self._create_scorecard_tags(agent, game_id)
            scorecard_id = self.arcade.create_scorecard(
                source_url="https://github.com/BitterTruth-AI/Ouroboros",
                tags=tags
            )
            if self.verbose:
                print(f"    [SCORECARD] Created: {scorecard_id}")
                print(f"    [TAGS] {', '.join(tags)}")
            return scorecard_id
        except Exception as e:
            if self.verbose:
                print(f"    [WARN] Failed to create scorecard: {e}")
            return None

    def get_available_games(self) -> List[str]:
        """Get list of available game IDs."""
        try:
            envs = self.arcade.get_environments()
            game_ids = [e.game_id for e in envs]

            # Filter to target game if specified
            if self.target_game:
                game_ids = [g for g in game_ids if g.startswith(self.target_game)]

            return game_ids
        except Exception as e:
            print(f"[ERROR] Failed to get games: {e}")
            return []

    def play_game(self, agent: AgentState, game_id: str) -> GameResult:
        """
        Play a single game with an agent.

        Uses the decision system to select actions.
        Creates a scorecard with proper tags for tracking.
        """
        # Create scorecard with proper tags for this agent/game
        scorecard_id = self._get_or_create_scorecard(agent, game_id)

        env = None
        try:
            env = self.arcade.make(game_id, scorecard_id=scorecard_id)
        except Exception as e:
            print(f"  [ERROR] Failed to create env for {game_id}: {e}")
            return GameResult(
                game_id=game_id,
                agent_id=agent.agent_id,
                score=0.0,
                levels_completed=0,
                total_levels=1,
                is_win=False,
                actions_taken=0,
            )

        if env is None:
            print(f"  [ERROR] env is None for {game_id}")
            return GameResult(
                game_id=game_id,
                agent_id=agent.agent_id,
                score=0.0,
                levels_completed=0,
                total_levels=1,
                is_win=False,
                actions_taken=0,
            )

        actions_taken = 0
        action_sequence = []
        last_obs = None
        prev_levels = 0
        prev_score = 0.0  # Track score for learning

        # Track state for decision context (used by rungs like MapIntelCollisionRung)
        last_action_str = ''
        last_frame_changed = True  # Assume first frame is "changed"
        failed_actions: set = set()  # Track actions that resulted in no change
        recent_actions: list = []  # Track last N actions for context
        last_score_delta = 0.0  # Track score change from last action
        last_outcome_type = 'neutral'  # 'positive', 'negative', 'neutral', 'death'
        has_full_win = False  # Track if this game type has been fully won before
        active_sequence: list = []  # Current winning sequence to follow (if any)
        sequence_position = 0  # Current position in active_sequence
        is_replay_mode = False  # True when following a known sequence
        stuck_count = 0  # Count of consecutive stuck frames
        tried_colors: set = set()  # Colors we've tried clicking (for ACTION6 exploration)
        level_start_action_index = 0  # Track where current level's actions begin (for per-level winning sequences)

        # Check if game already has a winning sequence (for frontier_mode)
        try:
            result = self.db.execute_query("""
                SELECT winning_sequence FROM winning_sequences_full_game
                WHERE game_id = ? AND is_active = 1
                ORDER BY efficiency_score DESC LIMIT 1
            """, (game_id,))
            if result:
                has_full_win = True
                # Load the best sequence for replay
                seq_data = result[0][0]
                if seq_data:
                    import json
                    if isinstance(seq_data, str):
                        active_sequence = json.loads(seq_data)
                    else:
                        active_sequence = list(seq_data)
                    is_replay_mode = True
        except Exception:
            has_full_win = False

        # Reset symbolic reasoning state for new game
        self.player_localizer.reset()
        self._prev_frame = None
        self._prev_properties = None

        # Create session for action traces (FK requirement)
        self._current_session_id = f"session_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
        try:
            self.db.execute_query("""
                INSERT INTO training_sessions (
                    session_id, game_id, start_time, mode, status, total_actions
                ) VALUES (?, ?, datetime('now'), 'evolution', 'in_progress', 0)
            """, (self._current_session_id, game_id))
        except Exception as e:
            if self.verbose:
                print(f"    [WARN] Failed to create training session: {e}")

        # Get initial observation and available actions
        initial_obs = env.observation_space
        available_actions = getattr(initial_obs, 'available_actions', [1, 2, 3, 4])
        win_levels = getattr(initial_obs, 'win_levels', 7)

        if self.verbose:
            print(f"    Game: {game_id} | Available actions: {available_actions} | Win at: {win_levels} levels")

        # Game loop
        while actions_taken < self.max_actions:
            if not self.running:
                break

            # Get current observation from last step (or initial)
            obs = last_obs if last_obs else initial_obs

            # Get CURRENT available_actions from observation (can change mid-game)
            current_available = getattr(obs, 'available_actions', None) or available_actions

            # Build context for decision system with available_actions
            context = {
                'game_id': game_id,
                'game_type': game_id[:4] if game_id and len(game_id) >= 4 else '',  # Extract game type prefix
                'agent_id': agent.agent_id,
                'actions_taken': actions_taken,
                'action_count': actions_taken,  # Alias for budget tracking
                'state': str(obs.state) if obs else 'UNKNOWN',
                'frame_data': obs,
                'available_actions': current_available,  # Current, not initial
                'levels_completed': getattr(obs, 'levels_completed', 0),
                'level': (getattr(obs, 'levels_completed', 0) or 0) + 1,  # Current level (1-indexed)
                'level_number': (getattr(obs, 'levels_completed', 0) or 0) + 1,  # Alias
                'win_levels': win_levels,
                # State tracking for MapIntelCollisionRung and ThreeLayerFilterRung
                'last_action': last_action_str,
                'last_actions': recent_actions[-5:] if recent_actions else [],  # Last 5 actions
                'frame_changed': last_frame_changed,
                'failed_actions': failed_actions,
                # Position tracking (default to center if unknown)
                'position': (32, 32),
                'player_position': (32, 32),  # Alias
                # Score tracking
                'score': getattr(obs, 'score', 0.0),
                'score_delta': last_score_delta,
                'last_outcome': last_outcome_type,  # 'positive', 'negative', 'neutral', 'death'
                # Frontier/mode flags
                'frontier_mode': not has_full_win,  # Frontier if no full game win yet
                'is_frontier': not has_full_win,
                'is_novel_game': actions_taken < 50,  # Novel for first 50 actions
                'optimization_mode': has_full_win,  # Optimization mode if we have a win
                # Session tracking
                'session_id': self._current_session_id,
                'scorecard_id': scorecard_id,
                # Sequence tracking (for ThreeTrySequenceRung, MultiStageMatchingRung)
                'active_sequence': active_sequence,
                'sequence_position': sequence_position,
                'is_replay': is_replay_mode,
                'replay_mode': is_replay_mode,  # Alias
                # Stuck tracking
                'recent_stuck_count': stuck_count,
                # Click exploration tracking
                'tried_colors': tried_colors,
                # ACTION6 innate understanding - helps rungs know this is a click-only game
                # ACTION6 is fundamentally different: it requires (x,y) coordinates
                'is_action6_only_game': current_available == [6],
                'action6_available': 6 in current_available,
            }

            # Get action from decision system
            action_data = None  # For ACTION6 coordinates
            try:
                # Note: decide(game_state, context) - pass obs as game_state, context as context
                result = self.decision_system.decide(obs, context)

                # Decision system returns (action_str, reason) tuple
                if isinstance(result, tuple):
                    action_str, reason = result
                    # Extract action number from string like 'ACTION1'
                    if isinstance(action_str, str) and action_str.startswith('ACTION'):
                        action_num = int(action_str.replace('ACTION', ''))
                    else:
                        action_num = random.choice(current_available)

                    # Extract ACTION6 coordinates from decision system metadata
                    if action_num == 6 and hasattr(self.decision_system, 'last_decision_metadata'):
                        metadata = self.decision_system.last_decision_metadata or {}
                        # Try different coordinate formats from rungs
                        if 'pixel_position' in metadata:
                            px, py = metadata['pixel_position']
                            action_data = {'x': int(px), 'y': int(py)}
                        elif 'target' in metadata:
                            target = metadata['target']
                            action_data = {'x': int(target.get('x', 32)), 'y': int(target.get('y', 32))}
                        elif 'grid_target' in metadata:
                            # GridExplorationRung provides coordinates in grid_target
                            grid_target = metadata['grid_target']
                            action_data = {'x': int(grid_target.get('x', 32)), 'y': int(grid_target.get('y', 32))}
                        elif 'x' in metadata and 'y' in metadata:
                            action_data = {'x': int(metadata['x']), 'y': int(metadata['y'])}
                        else:
                            # Fallback: center of screen
                            action_data = {'x': 32, 'y': 32}
                            if self.verbose:
                                print(f"    [WARN] ACTION6 without coordinates, using default (32, 32)")

                elif hasattr(result, 'action'):
                    action_num = result.action
                else:
                    action_num = random.choice(current_available)

                # Ensure action_num is an int
                if hasattr(action_num, 'value'):
                    action_num = action_num.value

                # Validate action is in available set - CRITICAL for online mode
                if action_num not in current_available:
                    if self.verbose:
                        # Debug: show which rung returned invalid action
                        rung_info = reason if 'reason' in dir() and reason else 'unknown'
                        print(f"    [WARN] Action {action_num} not in {current_available}, picking random | from: {rung_info[:50]}")
                    action_num = random.choice(current_available)

                action = getattr(GameAction, f'ACTION{action_num}', GameAction.ACTION1)
            except Exception as e:
                # Fallback to random from available actions only
                if self.verbose:
                    print(f"    [WARN] Decision failed: {e}, picking random")
                action_num = random.choice(available_actions)
                action = getattr(GameAction, f'ACTION{action_num}', GameAction.ACTION1)

            # Take action with retry logic for transient API errors
            obs = None
            max_step_retries = 3
            step_retry_delay = 2.0

            for step_attempt in range(max_step_retries):
                try:
                    obs_before = last_obs if last_obs else initial_obs
                    # Pass action_data for ACTION6 coordinates
                    obs = env.step(action, data=action_data)

                    # Check if step returned None (SDK may catch errors internally)
                    if obs is None:
                        if step_attempt < max_step_retries - 1:
                            wait_time = step_retry_delay * (2 ** step_attempt)
                            print(f"    [API] Step returned None for {action.name}, retry {step_attempt + 1}/{max_step_retries} in {wait_time:.1f}s")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"    [API] Step keeps failing after {max_step_retries} retries, ending game")
                            break

                    break  # Success - exit retry loop

                except Exception as e:
                    # Check if it's a server error by inspecting exception message
                    err_str = str(e)
                    err_lower = err_str.lower()
                    is_server_error = any(code in err_lower for code in ['500', '502', '503', '504', 'server error', 'internal server'])
                    is_rate_limit = '429' in err_lower or 'rate limit' in err_lower

                    if is_server_error or is_rate_limit:
                        # Transient error - retry with backoff
                        if step_attempt < max_step_retries - 1:
                            wait_time = step_retry_delay * (2 ** step_attempt)
                            print(f"    [API] Server error on {action.name}, retry {step_attempt + 1}/{max_step_retries} in {wait_time:.1f}s")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"    [API] Server error persists after {max_step_retries} retries, ending game")
                            obs = None
                            break
                    else:
                        # Non-transient error - don't retry
                        print(f"    [ERROR] Step failed: {type(e).__name__}: {e}")
                        obs = None
                        break

            # If step failed completely, end the game
            if obs is None:
                print(f"    [ABORT] Ending game {game_id} due to API failure")
                break

            actions_taken += 1
            action_sequence.append(action.name)

            # Update state tracking for decision context
            last_action_str = action.name
            recent_actions.append(action.name)
            if len(recent_actions) > 10:
                recent_actions.pop(0)  # Keep last 10

            # Detect if frame changed (for collision detection)
            frame_hash_before = self._compute_frame_hash(obs_before)
            frame_hash_after = self._compute_frame_hash(obs)
            last_frame_changed = frame_hash_before != frame_hash_after

            # CRITICAL FIX: Feed ACTION6 click feedback to visual_analyzer
            # Without this, the visual_analyzer never learns which coordinates
            # were tried or which produced frame changes. It generates the same
            # rigid grid every time, never filtering already-clicked positions.
            if action.name == 'ACTION6' and action_data:
                try:
                    va = None
                    if hasattr(self, 'decision_system') and hasattr(self.decision_system, '_engine_registry'):
                        registry = self.decision_system._engine_registry
                        if registry:
                            va = getattr(registry, 'visual_analyzer', None)
                    if va and hasattr(va, 'mark_coordinate_clicked'):
                        click_x = action_data.get('x', 32)
                        click_y = action_data.get('y', 32)
                        va.mark_coordinate_clicked(click_x, click_y, frame_changed=last_frame_changed)
                except Exception:
                    pass  # Non-critical - don't break game loop

            # Track failed actions (no change = potential collision/invalid)
            # EXCEPTION: For ACTION6-only games (click-based like vc33), frame hash
            # comparison is unreliable - clicks may change game state without visible
            # frame difference. Don't increment stuck_count for these games to prevent
            # the InfiniteLoopBreakerRung from firing deterministically at action #18/#34.
            is_action6_only = current_available == [6]
            if not last_frame_changed and action.name.startswith('ACTION'):
                failed_actions.add(action.name)
                if not is_action6_only:
                    stuck_count += 1  # Increment stuck counter (movement games only)
            else:
                stuck_count = 0  # Reset on successful action

            # Reset stuck counter after emergency fires so the cognitive
            # router gets a fresh window instead of being permanently locked
            # out by the self-reinforcing emergency -> no-change -> emergency loop.
            if 'reason' in dir() and reason and 'EMERGENCY' in reason:
                stuck_count = 0

            # Update sequence position if following a sequence
            if is_replay_mode and active_sequence and sequence_position < len(active_sequence):
                sequence_position += 1

            last_obs = obs

            # Track level progress
            current_levels = getattr(obs, 'levels_completed', 0) or 0
            level_up = current_levels > prev_levels

            # Calculate score for this step (levels completed as fraction)
            current_score = current_levels / win_levels if win_levels > 0 else 0.0

            # Update score tracking for context
            last_score_delta = current_score - prev_score
            is_game_over = obs and obs.state in (GameState.WIN, GameState.GAME_OVER)
            is_death = obs and obs.state == GameState.GAME_OVER and not level_up

            # Determine outcome type for context
            if is_death:
                last_outcome_type = 'death'
            elif last_score_delta > 0 or level_up:
                last_outcome_type = 'positive'
            elif last_score_delta < 0:
                last_outcome_type = 'negative'
            else:
                last_outcome_type = 'neutral'

            # CRITICAL: Record action trace for learning
            self._record_action_trace(
                game_id=game_id,
                action_num=action_num,
                obs_before=obs_before,
                obs_after=obs,
                score_before=prev_score,
                score_after=current_score,
                level_before=prev_levels,
                level_after=current_levels,
                is_game_over=is_game_over,
                coordinates=action_data,
            )

            # NEW: Record player state for symbolic reasoning (Phase 0-1)
            action_result = 'continue'
            if is_game_over:
                action_result = 'win' if obs.state == GameState.WIN else 'death'
            elif level_up:
                action_result = 'success'

            self._record_player_state(
                game_id=game_id,
                action_num=actions_taken,
                action_taken=action.name,
                obs_before=obs_before,
                obs_after=obs,
                action_result=action_result,
                level_number=current_levels,
            )

            # CRITICAL FIX: Save per-level winning subsequences on level_up
            # The architecture requires winning_sequences to store per-level
            # solutions (winning_sequences table has level_number column).
            # Previously, only full-game wins were saved, so the matching
            # pipeline had nothing to replay and no knowledge transferred.
            if level_up:
                try:
                    level_subsequence = action_sequence[level_start_action_index:]
                    if level_subsequence:
                        import json as json_lib
                        level_seq_id = f"seq_{uuid.uuid4().hex[:12]}"
                        game_type = game_id[:4] if len(game_id) >= 4 else game_id
                        level_just_beaten = prev_levels + 1  # The level that was just completed

                        self.db.execute_query("""
                            INSERT INTO winning_sequences (
                                sequence_id, game_id, game_type, level_number,
                                action_sequence, total_actions, total_score,
                                efficiency_score, agent_id, session_id,
                                generation_discovered, is_active,
                                initial_frame, final_frame, discovered_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, '[]', '[]', datetime('now'))
                        """, (
                            level_seq_id,
                            game_id,
                            game_type,
                            level_just_beaten,
                            json_lib.dumps(level_subsequence),
                            len(level_subsequence),
                            current_score,
                            current_score / max(1, len(level_subsequence)),
                            agent.agent_id,
                            self._current_session_id or 'unknown',
                            self.current_generation,
                        ))
                        if self.verbose:
                            print(f"    [SEQ-SAVE] Level {level_just_beaten} sequence saved: {level_seq_id[:16]} ({len(level_subsequence)} actions)")
                except Exception as e:
                    if self.verbose:
                        print(f"    [SEQ-ERR] Failed to save level sequence: {e}")

                # Reset for next level
                level_start_action_index = len(action_sequence)

            prev_levels = current_levels
            prev_score = current_score

            # Verbose output
            if self.verbose:
                levels = current_levels
                state_str = str(obs.state).replace('GameState.', '') if obs else '?'
                level_indicator = ' [LEVEL UP!]' if level_up else ''
                # Show coordinates for ACTION6
                coord_str = ''
                if action.name == 'ACTION6' and action_data:
                    coord_str = f" @ ({action_data.get('x', '?')}, {action_data.get('y', '?')})"

                # Build routing trace info if using cognitive strategy
                trace_str = ''
                if self._use_cognitive_router and 'reason' in dir() and reason:
                    # Show first 60 chars of reasoning
                    short_reason = reason[:60] + '...' if len(reason) > 60 else reason
                    trace_str = f" | {short_reason}"

                print(f"    [{actions_taken:3d}] {action.name:8s}{coord_str} -> levels={levels}/{win_levels} state={state_str}{level_indicator}{trace_str}")

            # Check for game end
            if obs and obs.state == GameState.WIN:
                if self.verbose:
                    print(f"    [WIN!] Game won after {actions_taken} actions!")
                break
            if obs and obs.state == GameState.GAME_OVER:
                if self.verbose:
                    print(f"    [GAME OVER] after {actions_taken} actions")
                break

        # Extract results - use levels_completed as the score metric
        levels_completed = 0
        total_levels = win_levels
        is_win = False

        if last_obs:
            levels_completed = getattr(last_obs, 'levels_completed', 0) or 0
            is_win = last_obs.state == GameState.WIN

        # Score is based on level progress (0.0 to 1.0)
        score = levels_completed / total_levels if total_levels > 0 else 0.0

        return GameResult(
            game_id=game_id,
            agent_id=agent.agent_id,
            score=score,
            levels_completed=levels_completed,
            total_levels=total_levels,
            is_win=is_win,
            actions_taken=actions_taken,
            action_sequence=action_sequence,
        )

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
        # Per Unified Theory: Roles emerge from agent performance + wA/wB weights
        mode_assignments = {}
        if self.operating_mode_system:
            try:
                agent_ids = [a.agent_id for a in self.agents]
                mode_assignments = self.operating_mode_system.assign_population_modes(
                    generation=self.current_generation,
                    active_agents=agent_ids,
                    game_id=games[0] if len(games) == 1 else None  # Only pass game_id if single game
                )
                # Update specialization in agents table so _create_scorecard_tags reads correct mode
                for agent_id, mode in mode_assignments.items():
                    self.db.execute_query(
                        "UPDATE agents SET specialization = ? WHERE agent_id = ?",
                        (mode, agent_id)
                    )
                if self.verbose:
                    mode_counts = {}
                    for m in mode_assignments.values():
                        mode_counts[m] = mode_counts.get(m, 0) + 1
                    print(f"[MODES] Assigned: {mode_counts}")
            except Exception as e:
                print(f"[WARN] Mode assignment failed, defaulting to generalist: {e}")

        results = []
        total_wins = 0
        total_score = 0.0

        # Each agent plays games
        agents_played = 0
        agents_skipped = 0
        for agent in self.agents:
            if not self.running:
                break

            try:
                # Select games for this agent using MetaLearningCurriculum if available
                # Per Unified Theory: 4-stage curriculum for generalization
                if self.meta_learning_curriculum:
                    try:
                        agent_games = self.meta_learning_curriculum.select_games_for_agent(
                            agent_id=agent.agent_id,
                            available_games=games,
                            num_games=self.games_per_generation
                        )
                        if not agent_games:
                            # Fallback if curriculum returns empty
                            agent_games = random.sample(games, min(self.games_per_generation, len(games)))
                    except Exception as e:
                        if self.verbose:
                            print(f"    [CURRICULUM] Fallback to random: {e}")
                        agent_games = random.sample(games, min(self.games_per_generation, len(games)))
                else:
                    # No curriculum - random selection
                    agent_games = random.sample(games, min(self.games_per_generation, len(games)))

                print(f"\n[AGENT] {agent.agent_id[:12]}... playing {len(agent_games)} games")

                for game_id in agent_games:
                    if not self.running:
                        break

                    result = self.play_game(agent, game_id)
                    results.append(result)

                    # Update agent state
                    agent.games_played += 1
                    agent.total_score += result.score
                    if result.is_win:
                        agent.wins += 1
                        total_wins += 1

                    total_score += result.score

                    # Log result
                    status = "[WIN]" if result.is_win else f"[{result.levels_completed}/{result.total_levels}]"
                    print(f"  {game_id}: {status} score={result.score:.1f} actions={result.actions_taken}")

                    # Store in database
                    self._store_game_result(result)

                # Update curriculum progress for this agent after all games
                # Per Unified Theory: Track stage progression for generalization
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

        print(f"\n[SUMMARY] Gen {self.current_generation}: {agents_played} agents, {games_played} games, {total_wins} wins ({win_rate*100:.1f}%), avg score: {avg_score:.2f}")

        # COLLECTIVE REASONING: Try collective approach on stuck games
        # Per Unified Theory: "Top performers collaborate on challenging games"
        if self.collective_reasoning_engine and total_wins == 0 and self.current_generation > 5:
            try:
                # Find games with consistent failures
                stuck_games = self._find_stuck_games(results)
                if stuck_games and len(stuck_games) > 0:
                    game_to_try = stuck_games[0]
                    session_id = self.collective_reasoning_engine.start_collective_session(
                        game_id=game_to_try,
                        generation=self.current_generation,
                        reasoning_mode='voting'
                    )
                    if session_id:
                        print(f"  [COLLECTIVE] Started collective reasoning session for {game_to_try}")
            except Exception as e:
                if self.verbose:
                    print(f"  [COLLECTIVE-ERR] Collective reasoning failed: {e}")

        return {
            'games_played': games_played,
            'wins': total_wins,
            'win_rate': win_rate,
            'avg_score': avg_score,
        }

    def _find_stuck_games(self, results: List[GameResult]) -> List[str]:
        """Find games where all agents failed to make progress."""
        game_scores = {}
        for result in results:
            if result.game_id not in game_scores:
                game_scores[result.game_id] = []
            game_scores[result.game_id].append(result.score)

        stuck_games = []
        for game_id, scores in game_scores.items():
            # Game is "stuck" if max score < 0.2 (didn't complete 2 levels)
            if max(scores) < 0.2:
                stuck_games.append(game_id)

        return stuck_games

    def _store_game_result(self, result: GameResult):
        """Store game result in database."""
        import uuid
        session_id = str(uuid.uuid4())

        try:
            # Create training session first (FK requirement)
            self.db.execute_query("""
                INSERT INTO training_sessions (
                    session_id, game_id, start_time, mode, status, total_actions
                ) VALUES (?, ?, datetime('now'), 'evolution', 'completed', ?)
            """, (session_id, result.game_id, result.actions_taken))

            # Now store game result
            self.db.execute_query("""
                INSERT INTO game_results (
                    game_id, session_id, start_time, end_time, status,
                    final_score, total_actions, win_detected,
                    level_completions, generation
                ) VALUES (?, ?, datetime('now'), datetime('now'), 'completed',
                          ?, ?, ?, ?, ?)
            """, (
                result.game_id,
                session_id,
                result.score,
                result.actions_taken,
                result.is_win,
                result.levels_completed,
                self.current_generation,
            ))

            # Store winning sequence if won
            if result.is_win and result.action_sequence:
                # Generate sequence_id as required by schema
                import json as json_lib
                sequence_id = f"seq_{uuid.uuid4().hex[:12]}"
                game_type = result.game_id[:4] if len(result.game_id) >= 4 else result.game_id

                # First, insert the winning sequence with proper schema
                self.db.execute_query("""
                    INSERT INTO winning_sequences (
                        sequence_id, game_id, game_type, level_number,
                        action_sequence, total_actions, total_score, efficiency_score,
                        agent_id, session_id, generation_discovered, is_active,
                        initial_frame, final_frame, discovered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, '[]', '[]', datetime('now'))
                """, (
                    sequence_id,
                    result.game_id,
                    game_type,
                    result.levels_completed,
                    json_lib.dumps(result.action_sequence),  # JSON array
                    result.actions_taken,
                    result.score,
                    result.score / max(1, result.actions_taken),  # efficiency
                    result.agent_id,
                    self._current_session_id or 'unknown',
                    self.current_generation,
                ))
                print(f"    [SAVED] Winning sequence {sequence_id[:12]} for {result.game_id}")

                # CRITICAL: Create viral package to share with network
                # This enables network-level knowledge transfer per theory
                if self.viral_package_engine:
                    try:
                        package_id = self.viral_package_engine.create_viral_package_from_sequence(
                            sequence_id=sequence_id,
                            agent_id=result.agent_id,
                            generation=self.current_generation,
                            skip_if_exists=True  # Deduplication
                        )
                        if package_id:
                            print(f"    [VIRAL] Created package {package_id[:12]} for network sharing")
                    except Exception as vpe:
                        if self.verbose:
                            print(f"    [VIRAL-ERR] Could not create package: {vpe}")

                # GAMES-AS-TEACHERS: Extract lesson from win
                # Per Unified Theory: "I won = I demonstrated understanding"
                if self.games_as_teachers_engine:
                    try:
                        # Convert action sequence strings to ints for the engine
                        action_ints = []
                        for act in result.action_sequence:
                            if isinstance(act, str) and act.startswith('ACTION'):
                                action_ints.append(int(act.replace('ACTION', '')))
                            elif isinstance(act, int):
                                action_ints.append(act)

                        lesson = self.games_as_teachers_engine.extract_lesson(
                            game_type=game_type,
                            level_number=result.levels_completed,
                            winning_sequence=action_ints,
                            frame_history=None,  # Could capture frames for deeper analysis
                            working_theory=None  # Could pass current theory
                        )
                        if lesson:
                            concept = lesson.get('concept_demonstrated', 'unknown')
                            print(f"    [LESSON] Concept demonstrated: {concept}")
                    except Exception as le:
                        if self.verbose:
                            print(f"    [LESSON-ERR] Could not extract lesson: {le}")

        except Exception as e:
            print(f"  [WARN] Failed to store result: {e}")

    def evolve(self):
        """
        Evolve population using full EvolutionaryEngine.

        Features enabled (from Unified Theory):
        - Youth bonus: Newer agents get breeding opportunities
        - Prestige system: Network contribution affects breeding priority
        - Genome mutation: Proper genetic variation with role-based mutation rates
        - Crossover: Two-parent breeding with epigenetic inheritance
        - Survival protection: High-prestige agents resist culling
        - Proper culling: Bottom performers marked inactive (they "die")

        Per Unified Theory:
        - "Agents die, database persists"
        - "Anti-Vampire Rule: agents sunset when usefulness wanes"
        - "Youth Selection Bonus: newer generations get opportunities"
        - "Prestige affects trust, not access"
        """
        print(f"\n[EVOLVE] Evolving population via EvolutionaryEngine...")

        # Build evolution strategy with all parameters
        evolution_strategy = {
            'generation': self.current_generation,
            'population_size': self.population_size,
            'selection_pressure': 0.5,
            'crossover_rate': 0.6,
            'mutation_rate': 0.2,
            'diversity_mode': True,  # Enable diversity + meta-learning fitness
            'focus': 'balanced',
        }

        try:
            # Use full EvolutionaryEngine for sophisticated evolution
            new_population = self.evolutionary_engine.evolve_population(evolution_strategy)

            # Convert database dicts back to AgentState objects for runner
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

            # Log evolution results
            print(f"  New population: {len(self.agents)} agents")
            print(f"  Features: youth_bonus, prestige, mutation, crossover, epigenetics")

            # Show top performers with their fitness
            if self.agents:
                top_agents = sorted(self.agents, key=lambda a: a.avg_score * (1 + a.win_rate), reverse=True)[:3]
                print(f"  Top performers: {[f'{a.agent_id[:8]}(s={a.avg_score:.1f})' for a in top_agents]}")

            # HORIZONTAL TRANSFER: Spread knowledge between agents
            # Per Unified Theory: "Intelligence spreads through horizontal information transfer"
            if self.horizontal_transfer_engine:
                try:
                    transfers = self.horizontal_transfer_engine.execute_generation_transfers(
                        generation=self.current_generation,
                        max_transfers_per_agent=2
                    )
                    if transfers > 0:
                        print(f"  [TRANSFER] {transfers} horizontal knowledge transfers completed")

                        # Get transfer statistics
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

            # NETWORK INTELLIGENCE: Capture ecosystem snapshot
            # Per Unified Theory: "The database IS the AGI. Agents are temporary cells."
            if self.network_intelligence_engine and self.current_generation % 5 == 0:
                try:
                    snapshot = self.network_intelligence_engine.capture_ecosystem_snapshot(self.current_generation)
                    health_status = snapshot.get('health_status', 'unknown')
                    health_score = snapshot.get('health_score', 0.0)
                    print(f"  [NETWORK] Ecosystem health: {health_status} (score: {health_score:.3f})")

                    # Show key metrics
                    if self.verbose:
                        print(f"    Knowledge: {snapshot.get('total_sequences', 0)} sequences, "
                              f"{snapshot.get('total_patterns', 0)} patterns, "
                              f"{snapshot.get('unique_games_solved', 0)} games solved")
                        print(f"    Diversity index: {snapshot.get('knowledge_diversity_index', 0):.3f}")
                except Exception as e:
                    if self.verbose:
                        print(f"  [NETWORK-ERR] Ecosystem snapshot failed: {e}")

            # AGENT LIFECYCLE: Clean up ancient inactive agents periodically
            # Per Unified Theory: "Good players never deleted, just retired"
            if self.lifecycle_manager and self.current_generation % 50 == 0:
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

            # CONCEPT DISCOVERY: Analyze cross-game patterns periodically
            # Per Unified Theory: "Concepts emerge from cross-game pattern recognition"
            if self.concept_discovery_engine and self.current_generation % 10 == 0:
                try:
                    # Check for newly emerging concepts from pattern tracking
                    new_concepts = self.concept_discovery_engine.check_concept_emergence()
                    if new_concepts:
                        print(f"  [CONCEPTS] Discovered {len(new_concepts)} concept candidates")
                        if self.verbose:
                            for concept in new_concepts[:3]:  # Show top 3
                                print(f"    - {concept.get('pattern', 'unnamed')[:20]}: {concept.get('confidence', 0):.2f}")
                except Exception as e:
                    if self.verbose:
                        print(f"  [CONCEPT-ERR] Concept discovery failed: {e}")

        except Exception as e:
            print(f"  [WARN] EvolutionaryEngine failed, using fallback: {e}")
            # Fallback to simple evolution if engine fails
            self._simple_evolve_fallback()

    def _simple_evolve_fallback(self):
        """Fallback simple evolution if EvolutionaryEngine fails."""
        def fitness(a: AgentState) -> float:
            return a.avg_score * (1 + a.win_rate)

        self.agents.sort(key=fitness, reverse=True)
        keep_count = max(1, len(self.agents) // 2)
        survivors = self.agents[:keep_count]
        culled = self.agents[keep_count:]

        # Deactivate culled agents
        if culled:
            culled_ids = [a.agent_id for a in culled]
            placeholders = ','.join(['?' for _ in culled_ids])
            self.db.execute_query(f"""
                UPDATE agents SET is_active = FALSE
                WHERE agent_id IN ({placeholders})
            """, culled_ids)
            print(f"  [FALLBACK] Culled {len(culled)} underperformers")

        # Simple offspring creation
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

        # Initialize
        self.agents = self.initialize_population()

        # Main loop - max_generations is relative to session start
        target_generation = self._start_generation + self.max_generations
        while self.running and self.current_generation < target_generation:
            # Run generation
            stats = self.run_generation()

            if not self.running:
                break

            # Evolve
            self.evolve()

            self.current_generation += 1

        # Final summary
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

    args = parser.parse_args()

    # Determine max_actions based on mode if not explicitly set
    if args.max_actions is None:
        # Offline mode runs much faster - can afford more exploration
        if args.mode == 'offline':
            args.max_actions = 7500  # 2500 base * 3x offline multiplier
        else:
            args.max_actions = 2500  # Boosted baseline (was 500)

    # Test mode overrides
    if args.test:
        args.population = 1
        args.games_per_gen = 1
        args.max_generations = 1
        args.max_actions = 300  # Boosted for meaningful test (was 100)

    # Log file redirect - file only (no Tee, avoids KeyboardInterrupt on console writes)
    log_file_handle = None
    if args.log_file:
        log_file_handle = open(args.log_file, 'w', encoding='utf-8', buffering=1)  # Line-buffered
        sys.stdout = log_file_handle
        sys.stderr = log_file_handle
        # Also redirect logging to file
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
