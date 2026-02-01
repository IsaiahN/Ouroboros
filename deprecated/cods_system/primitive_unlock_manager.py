import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Primitive Unlock Manager - Track earned vs locked primitives
=============================================================

Manages the "earn-to-learn" system:
- Tracks which primitives are unlocked (earned through discovery)
- Stores unlock attempts and their outcomes
- Validates unlock requests against RLVR criteria
- Logs the discovery journey for analysis

Three Primitive Categories:
1. SEED - Always available (~50) - Given at birth
2. LOCKED - Must be earned (70+) - Human knowledge to unlock
3. NOVEL - System-created - Discoveries with no human analog

Rule 1: Disable pycache
Rule 2: All data in database
Rule 10: Leverage existing systems
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from database_interface import DatabaseInterface

# Import seed primitives for syncing
try:
    from seed_primitives import get_seed_primitives, SeedPrimitiveRegistry
    SEED_PRIMITIVES_AVAILABLE = True
except ImportError:
    get_seed_primitives = None
    SeedPrimitiveRegistry = None
    SEED_PRIMITIVES_AVAILABLE = False

logger = logging.getLogger(__name__)


class PrimitiveStatus(Enum):
    """Status of a primitive in the unlock system."""
    SEED = "seed"           # Always available, given at birth
    LOCKED = "locked"       # Known but must be earned
    UNLOCKED = "unlocked"   # Earned through discovery
    NOVEL = "novel"         # System-discovered, no human analog
    GRANDFATHERED = "grandfathered"  # Oracle-approved from existing code


@dataclass
class LockedPrimitive:
    """Definition of a locked primitive waiting to be earned."""
    name: str
    category: str
    description: str
    unlock_condition: str  # Natural language description
    implementation_hint: Optional[str] = None  # Where the optimized version exists
    difficulty: float = 0.5  # 0.0 (easy) to 1.0 (hard)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'unlock_condition': self.unlock_condition,
            'implementation_hint': self.implementation_hint,
            'difficulty': self.difficulty
        }


@dataclass
class UnlockAttempt:
    """Record of an attempt to unlock a primitive."""
    attempt_id: str
    primitive_name: str
    discovered_pattern: str  # JSON representation of what system composed
    game_ids_tested: List[str]
    success_rate: float
    cross_game_success_rate: float  # Critical: 40% weight
    rlvr_validation_passed: bool
    oracle_verdict: Optional[str] = None
    unlocked: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class PrimitiveUnlockManager:
    """
    Manages the earn-to-learn primitive system.
    
    Workflow:
    1. System composes seed primitives
    2. Discovers a pattern that correlates with success
    3. RLVR validates: pattern actually helps
    4. Oracle checks: does this match a known primitive?
    5. If YES -> unlock optimized human version
    6. If NO -> record as NOVEL discovery
    """
    
    def __init__(self, db: Optional[DatabaseInterface] = None, db_path: str = "core_data.db"):
        self.db = db or DatabaseInterface(db_path)
        self._seed_registry: Optional[Any] = None
        self._initialize_schema()
        self._register_seed_primitives()  # Register seeds FIRST so they're available
        self._register_locked_primitives()
        self._grandfathered_primitives: Dict[str, str] = {}  # name -> implementation

    def attempt_unlock(self, primitive_name: str, pattern: Optional[Dict[str, Any]] = None,
                       agent_id: Optional[str] = None, generation: int = 0, success_rate: float = 0.0,
                       cross_game_success_rate: float = 0.0, rlvr_validation_passed: Optional[bool] = None,
                       unlock_reason: Optional[str] = None, **kwargs: Any) -> bool:
        """Attempt to unlock a primitive using provided evidence.

        This now records a real attempt and, if RLVR passes, marks the primitive
        unlocked. Legacy callers can still pass minimal data; however, zeroed
        success metrics will no longer spam failed rows."""
        try:
            pattern_json = json.dumps(pattern or {}, default=str)
            # Compute RLVR if not explicitly provided
            combined_score = (success_rate * 0.6) + (cross_game_success_rate * 0.4)
            rlvr_pass = rlvr_validation_passed
            if rlvr_pass is None:
                rlvr_pass = combined_score >= 0.7 and cross_game_success_rate >= 0.5

            attempt_id = self.record_unlock_attempt(
                primitive_name=primitive_name,
                discovered_pattern=json.loads(pattern_json),
                game_ids_tested=[],
                success_rate=success_rate,
                cross_game_success_rate=cross_game_success_rate,
                agent_id=agent_id,
                generation=generation
            )

            # If RLVR passed (or caller forced it), approve unlock directly
            if rlvr_pass:
                unlocked = self.approve_unlock(
                    attempt_id=attempt_id,
                    oracle_reasoning=unlock_reason or "RLVR passed; auto-approval",
                    similarity=0.9
                )
                return unlocked

            return False
        except Exception:
            logger.debug("attempt_unlock compatibility flow failed (ignored)")
            return False
    
    def _initialize_schema(self):
        """Create database tables for primitive tracking."""
        
        # Primitive status tracking
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS primitive_status (
                primitive_name TEXT PRIMARY KEY,
                status TEXT NOT NULL,  -- 'seed', 'locked', 'unlocked', 'novel', 'grandfathered'
                category TEXT NOT NULL,
                description TEXT,
                unlock_condition TEXT,
                implementation_hint TEXT,
                difficulty REAL DEFAULT 0.5,
                
                -- Unlock metadata
                unlocked_at TIMESTAMP,
                unlocked_by_agent TEXT,
                discovered_pattern TEXT,  -- JSON: the pattern that earned unlock
                
                -- Usage tracking
                times_used INTEGER DEFAULT 0,
                avg_success_rate REAL DEFAULT 0.0,
                last_used_at TIMESTAMP,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Unlock attempt history
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS primitive_unlock_attempts (
                attempt_id TEXT PRIMARY KEY,
                primitive_name TEXT NOT NULL,
                agent_id TEXT,
                generation INTEGER DEFAULT 0,
                
                -- What the system composed
                discovered_pattern TEXT NOT NULL,  -- JSON: composition tree
                pattern_hash TEXT,  -- For deduplication
                
                -- Validation results
                game_ids_tested TEXT,  -- JSON: list of game IDs
                games_tested_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                cross_game_success_rate REAL DEFAULT 0.0,
                rlvr_validation_passed BOOLEAN DEFAULT FALSE,
                
                -- Oracle decision
                oracle_verdict TEXT,  -- 'approved', 'rejected', 'pending'
                oracle_reasoning TEXT,
                similarity_to_locked REAL DEFAULT 0.0,
                
                -- Outcome
                unlocked BOOLEAN DEFAULT FALSE,
                marked_as_novel BOOLEAN DEFAULT FALSE,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (primitive_name) REFERENCES primitive_status(primitive_name)
            )
        """)
        
        # Novel primitive discoveries
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS novel_primitives (
                primitive_id TEXT PRIMARY KEY,
                discovered_name TEXT NOT NULL,  -- System-generated name
                composition_tree TEXT NOT NULL,  -- JSON: how it's composed from seeds
                
                -- Discovery context
                discovered_by_agent TEXT,
                discovered_in_game TEXT,
                discovered_at_generation INTEGER,
                
                -- Validation
                success_rate REAL DEFAULT 0.0,
                games_validated_on INTEGER DEFAULT 0,
                cross_game_generalization REAL DEFAULT 0.0,
                
                -- Competition with human primitives
                competes_with_human TEXT,  -- If similar to locked primitive
                outperforms_human BOOLEAN DEFAULT FALSE,
                
                -- Lifecycle
                is_active BOOLEAN DEFAULT TRUE,
                times_used INTEGER DEFAULT 0,
                last_used_at TIMESTAMP,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Primitive competition tracking (discovered vs human)
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS primitive_competition (
                competition_id TEXT PRIMARY KEY,
                primitive_name TEXT NOT NULL,
                
                -- Discovered version stats
                discovered_wins INTEGER DEFAULT 0,
                discovered_uses INTEGER DEFAULT 0,
                discovered_avg_score REAL DEFAULT 0.0,
                
                -- Human version stats  
                human_wins INTEGER DEFAULT 0,
                human_uses INTEGER DEFAULT 0,
                human_avg_score REAL DEFAULT 0.0,
                
                -- Current winner
                current_winner TEXT DEFAULT 'tie',  -- 'discovered', 'human', 'tie'
                
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_primitive_status 
            ON primitive_status(status)
        """)
        
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_unlock_attempts_primitive 
            ON primitive_unlock_attempts(primitive_name, rlvr_validation_passed)
        """)
    
    def _register_seed_primitives(self):
        """
        Register all seed primitives from SeedPrimitiveRegistry into the database.
        
        This ensures that is_available() returns True for seed primitives.
        Seed primitives are always available - they are the foundation.
        """
        if not SEED_PRIMITIVES_AVAILABLE or get_seed_primitives is None:
            logger.warning("[UNLOCK] Seed primitives not available - cannot register")
            return
        
        try:
            self._seed_registry = get_seed_primitives()
            registered_count = 0
            
            for name, primitive in self._seed_registry.primitives.items():
                # Check if already registered
                existing = self.db.execute_query(
                    "SELECT primitive_name FROM primitive_status WHERE primitive_name = ?",
                    (name,)
                )
                
                if not existing:
                    # Register as seed (always available)
                    self.db.execute_query("""
                        INSERT INTO primitive_status 
                        (primitive_name, status, category, description, difficulty)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        name,
                        PrimitiveStatus.SEED.value,
                        primitive.category.value if hasattr(primitive.category, 'value') else str(primitive.category),
                        primitive.description,
                        0.0  # Seeds have no difficulty - they're given
                    ))
                    registered_count += 1
            
            if registered_count > 0:
                logger.info(f"[UNLOCK] Registered {registered_count} seed primitives in database")
                
        except Exception as e:
            logger.warning(f"[UNLOCK] Failed to register seed primitives: {e}")
    
    def _register_locked_primitives(self):
        """Register all locked primitives from CODS design doc."""
        
        locked_primitives = [
            # Spatial/Perceptual (from existing VisualReasoningEngine)
            LockedPrimitive(
                "detect_symmetry", "spatial",
                "Detect horizontal, vertical, rotational symmetry",
                "System discovers symmetry-detection pattern",
                "visual_reasoning_engine.py:detect_symmetry()", 0.4
            ),
            LockedPrimitive(
                "flood_fill", "spatial",
                "Find connected regions of same color",
                "System discovers connected-component pattern",
                "object_detector.py:_flood_fill()", 0.3
            ),
            LockedPrimitive(
                "detect_shapes", "spatial",
                "Detect distinct shapes/objects",
                "System discovers shape detection pattern",
                "visual_reasoning_engine.py:detect_shapes()", 0.5
            ),
            LockedPrimitive(
                "find_repeating_patterns", "spatial",
                "Detect repeating motifs in grid",
                "System discovers periodicity/tiling pattern",
                "visual_reasoning_engine.py:find_repeating_patterns()", 0.5
            ),
            LockedPrimitive(
                "detect_edges", "spatial",
                "Find color boundaries/edges",
                "System discovers edge-detection pattern",
                None, 0.4
            ),
            LockedPrimitive(
                "is_enclosed", "spatial",
                "Check if region is fully bounded",
                "System discovers enclosure/containment pattern",
                None, 0.6
            ),
            LockedPrimitive(
                "motion_vector", "spatial",
                "Track movement direction between frames",
                "System discovers motion tracking pattern",
                None, 0.5
            ),
            LockedPrimitive(
                "count_neighbors", "spatial",
                "Count adjacent cells of specific type",
                "System discovers neighbor counting pattern",
                None, 0.3
            ),
            
            # Temporal/Predictive
            LockedPrimitive(
                "predict_next_state", "temporal",
                "Predict next frame given history",
                "System builds Markov model over transitions",
                None, 0.7
            ),
            LockedPrimitive(
                "detect_cycles", "temporal",
                "Identify repeating state sequences",
                "System discovers periodicity in sequences",
                None, 0.5
            ),
            LockedPrimitive(
                "rate_of_change", "temporal",
                "Measure velocity of change",
                "System correlates frame-to-frame deltas",
                None, 0.4
            ),
            LockedPrimitive(
                "stability_score", "temporal",
                "How unchanging a region is over time",
                "System tracks variance over N frames",
                None, 0.4
            ),
            
            # Relational/Logical
            LockedPrimitive(
                "causal_link", "relational",
                "Test if A precedes B consistently",
                "System discovers temporal correlation patterns",
                None, 0.6
            ),
            LockedPrimitive(
                "dependency_check", "relational",
                "Test if presence/state of A affects B",
                "System discovers conditional probability pattern",
                None, 0.6
            ),
            
            # Structural/Topological
            LockedPrimitive(
                "path_exists", "structural",
                "Check connectivity between points",
                "System discovers flood-fill connectivity",
                None, 0.4
            ),
            LockedPrimitive(
                "distance_transform", "structural",
                "Distance from each cell to nearest feature",
                "System computes distance map",
                None, 0.5
            ),
            
            # Statistical
            LockedPrimitive(
                "entropy_calc", "statistical",
                "Information entropy of region",
                "System discovers Shannon entropy on colors",
                None, 0.5
            ),
            LockedPrimitive(
                "correlation", "statistical",
                "Correlation between two features",
                "System discovers Pearson pattern",
                None, 0.6
            ),
            LockedPrimitive(
                "outlier_detection", "statistical",
                "Identify unusual cells/objects",
                "System discovers Z-score analysis",
                None, 0.6
            ),
            
            # Goal-Oriented
            LockedPrimitive(
                "goal_distance", "goal",
                "Estimate steps to goal",
                "System discovers heuristic path planning",
                None, 0.6
            ),
            LockedPrimitive(
                "subgoal_extract", "goal",
                "Extract intermediate objectives",
                "System discovers backward chaining",
                None, 0.7
            ),
            LockedPrimitive(
                "progress_estimate", "goal",
                "Estimate completion percentage",
                "System discovers current vs goal comparison",
                None, 0.5
            ),
            LockedPrimitive(
                "dead_end_detect", "goal",
                "Identify blocked/unreachable states",
                "System discovers connectivity analysis",
                None, 0.6
            ),
            
            # Meta-Cognitive
            LockedPrimitive(
                "uncertainty_estimate", "metacognitive",
                "Measure confidence in detection",
                "System tracks variance across methods",
                None, 0.7
            ),
            LockedPrimitive(
                "novelty_score", "metacognitive",
                "How novel/unexpected a pattern is",
                "System compares against known patterns",
                None, 0.6
            ),
            LockedPrimitive(
                "learning_progress", "metacognitive",
                "Rate of improvement on task",
                "System computes performance slope",
                None, 0.5
            ),
            
            # Agent-Centric
            LockedPrimitive(
                "control_test", "agent",
                "Test if agent can affect region",
                "System simulates actions, checks changes",
                "agent_self_model.py:learn_control_mapping()", 0.5
            ),
            LockedPrimitive(
                "effect_scope", "agent",
                "Determine what actions affect",
                "System discovers action-consequence correlation",
                None, 0.5
            ),
            LockedPrimitive(
                "self_location", "agent",
                "Locate agent in frame",
                "System matches against known agent signature",
                "agent_self_model.py:identify_controlled_objects()", 0.4
            ),
            
            # Physical Simulation (Containment/Flow)
            LockedPrimitive(
                "flow_simulation", "physics",
                "Predict where content will flow",
                "System discovers path-of-least-resistance",
                None, 0.7
            ),
            LockedPrimitive(
                "containment_check", "physics",
                "Check if region is fully sealed",
                "System discovers unsealed edges cause failures",
                None, 0.5
            ),
            LockedPrimitive(
                "boundary_seal_check", "physics",
                "Verify all edges are blocked",
                "System discovers sealing-before-filling pattern",
                None, 0.5
            ),
            
            # Meta-Representational
            LockedPrimitive(
                "identify_reference_object", "meta",
                "Detect objects that define rules for others",
                "System discovers keys/legends",
                None, 0.8
            ),
            LockedPrimitive(
                "extract_schema", "meta",
                "Get abstract structure independent of values",
                "System discovers pattern vs content separation",
                None, 0.8
            ),
            LockedPrimitive(
                "apply_template", "meta",
                "Instantiate schema with bindings",
                "System discovers template application",
                None, 0.7
            ),
            
            # Constraint Satisfaction
            LockedPrimitive(
                "identify_constraints", "constraint",
                "Extract active constraints from state",
                "System discovers implicit rules",
                None, 0.7
            ),
            LockedPrimitive(
                "check_constraint_satisfaction", "constraint",
                "Verify if constraint is met",
                "System discovers constraint checking",
                None, 0.5
            ),
            LockedPrimitive(
                "find_minimal_changes", "constraint",
                "Minimum edits to satisfy constraint",
                "System discovers optimization",
                None, 0.7
            ),
            
            # Inverse/Optimization
            LockedPrimitive(
                "calculate_goal_distance", "inverse",
                "Distance from target in arbitrary space",
                "System discovers distance heuristics",
                None, 0.5
            ),
            LockedPrimitive(
                "find_inverse_action", "inverse",
                "What undoes a given action",
                "System discovers action reversal",
                None, 0.5
            ),
            LockedPrimitive(
                "optimize_action_sequence", "inverse",
                "Minimize steps to achieve goal",
                "System discovers sequence optimization",
                None, 0.7
            ),
        ]
        
        # Insert locked primitives if not already present
        for prim in locked_primitives:
            existing = self.db.execute_query(
                "SELECT primitive_name FROM primitive_status WHERE primitive_name = ?",
                (prim.name,)
            )
            if not existing:
                self.db.execute_query("""
                    INSERT INTO primitive_status 
                    (primitive_name, status, category, description, unlock_condition, 
                     implementation_hint, difficulty)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    prim.name, PrimitiveStatus.LOCKED.value, prim.category,
                    prim.description, prim.unlock_condition,
                    prim.implementation_hint, prim.difficulty
                ))
    
    # ======================================================================
    # PUBLIC API
    # ======================================================================
    
    def get_status(self, primitive_name: str) -> Optional[PrimitiveStatus]:
        """Get the unlock status of a primitive."""
        result = self.db.execute_query(
            "SELECT status FROM primitive_status WHERE primitive_name = ?",
            (primitive_name,)
        )
        if result:
            return PrimitiveStatus(result[0]['status'])
        
        # Fallback: Check if it's a seed primitive not yet in database
        if self._seed_registry and primitive_name in self._seed_registry.primitives:
            return PrimitiveStatus.SEED
        
        return None
    
    def is_available(self, primitive_name: str) -> bool:
        """
        Check if a primitive is available for use.
        
        Returns True for:
        - SEED primitives (always available)
        - UNLOCKED primitives (earned through discovery)
        - NOVEL primitives (system-discovered)
        - GRANDFATHERED primitives (oracle-approved existing code)
        """
        status = self.get_status(primitive_name)
        if status is None:
            # Final fallback: Check seed registry directly
            if self._seed_registry and primitive_name in self._seed_registry.primitives:
                return True
            return False
        return status in [
            PrimitiveStatus.SEED, 
            PrimitiveStatus.UNLOCKED, 
            PrimitiveStatus.NOVEL,
            PrimitiveStatus.GRANDFATHERED
        ]
    
    def list_locked(self) -> List[Dict[str, Any]]:
        """List all locked primitives."""
        results = self.db.execute_query("""
            SELECT primitive_name, category, description, difficulty
            FROM primitive_status 
            WHERE status = 'locked'
            ORDER BY difficulty ASC
        """)
        return [dict(r) for r in results] if results else []
    
    def list_unlocked(self) -> List[Dict[str, Any]]:
        """List all unlocked primitives."""
        results = self.db.execute_query("""
            SELECT primitive_name, category, description, unlocked_at, unlocked_by_agent
            FROM primitive_status 
            WHERE status IN ('unlocked', 'grandfathered')
            ORDER BY unlocked_at DESC
        """)
        return [dict(r) for r in results] if results else []
    
    def list_novel(self) -> List[Dict[str, Any]]:
        """List all novel discoveries."""
        results = self.db.execute_query("""
            SELECT primitive_id, discovered_name, composition_tree, 
                   success_rate, cross_game_generalization, times_used
            FROM novel_primitives 
            WHERE is_active = TRUE
            ORDER BY success_rate DESC
        """)
        return [dict(r) for r in results] if results else []
    
    def record_unlock_attempt(
        self,
        primitive_name: str,
        discovered_pattern: Dict[str, Any],
        game_ids_tested: List[str],
        success_rate: float,
        cross_game_success_rate: float,
        agent_id: Optional[str] = None,
        generation: int = 0
    ) -> str:
        """
        Record an attempt to unlock a primitive.
        
        Args:
            primitive_name: Target primitive to unlock
            discovered_pattern: JSON composition tree
            game_ids_tested: Games used for validation
            success_rate: Overall success rate
            cross_game_success_rate: Cross-game generalization (40% weight)
            agent_id: Agent that discovered this
            generation: Current generation
            
        Returns:
            attempt_id
        """
        attempt_id = f"unlock_{uuid.uuid4().hex[:12]}"
        pattern_json = json.dumps(discovered_pattern, default=str)
        pattern_hash = hash(pattern_json) % (2**32)
        games_json = json.dumps(game_ids_tested)
        
        # Check RLVR criteria
        # Weighted: 60% success_rate + 40% cross_game
        combined_score = (success_rate * 0.6) + (cross_game_success_rate * 0.4)
        rlvr_passed = combined_score >= 0.7 and cross_game_success_rate >= 0.5
        
        self.db.execute_query("""
            INSERT INTO primitive_unlock_attempts
            (attempt_id, primitive_name, agent_id, generation, discovered_pattern,
             pattern_hash, game_ids_tested, games_tested_count, success_rate,
             cross_game_success_rate, rlvr_validation_passed, oracle_verdict)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attempt_id, primitive_name, agent_id, generation, pattern_json,
            str(pattern_hash), games_json, len(game_ids_tested), success_rate,
            cross_game_success_rate, rlvr_passed, 'pending' if rlvr_passed else 'rejected'
        ))
        
        logger.info(f"[CODS] Unlock attempt {attempt_id[:8]} for '{primitive_name}': "
                   f"RLVR {'PASSED' if rlvr_passed else 'FAILED'} "
                   f"(combined={combined_score:.2f}, cross_game={cross_game_success_rate:.2f})")
        
        return attempt_id
    
    def approve_unlock(
        self,
        attempt_id: str,
        oracle_reasoning: str = "Pattern matches locked primitive",
        similarity: float = 0.9
    ) -> bool:
        """
        Oracle approves an unlock attempt.
        
        Args:
            attempt_id: The unlock attempt to approve
            oracle_reasoning: Explanation of approval
            similarity: How similar to the locked primitive
            
        Returns:
            True if unlock successful
        """
        # Get attempt details
        attempt = self.db.execute_query(
            "SELECT * FROM primitive_unlock_attempts WHERE attempt_id = ?",
            (attempt_id,)
        )
        if not attempt:
            return False
        
        attempt = dict(attempt[0])
        primitive_name = attempt['primitive_name']
        
        # Update attempt
        self.db.execute_query("""
            UPDATE primitive_unlock_attempts 
            SET oracle_verdict = 'approved', 
                oracle_reasoning = ?,
                similarity_to_locked = ?,
                unlocked = TRUE
            WHERE attempt_id = ?
        """, (oracle_reasoning, similarity, attempt_id))
        
        # Update primitive status
        self.db.execute_query("""
            UPDATE primitive_status 
            SET status = 'unlocked',
                unlocked_at = CURRENT_TIMESTAMP,
                unlocked_by_agent = ?,
                discovered_pattern = ?
            WHERE primitive_name = ?
        """, (attempt.get('agent_id'), attempt['discovered_pattern'], primitive_name))
        
        logger.info(f"[CODS] UNLOCKED '{primitive_name}' via attempt {attempt_id[:8]}")
        return True
    
    def record_novel_primitive(
        self,
        composition_tree: Dict[str, Any],
        discovered_by_agent: str,
        discovered_in_game: str,
        generation: int,
        success_rate: float,
        games_validated: int,
        cross_game_rate: float
    ) -> str:
        """
        Record a novel primitive (no human analog).
        
        Args:
            composition_tree: How it's composed from seeds
            discovered_by_agent: Agent that discovered it
            discovered_in_game: Game where discovered
            generation: Discovery generation
            success_rate: Validation success rate
            games_validated: Number of games validated on
            cross_game_rate: Cross-game generalization
            
        Returns:
            primitive_id
        """
        primitive_id = f"novel_{uuid.uuid4().hex[:12]}"
        
        # Generate name from composition
        discovered_name = self._generate_novel_name(composition_tree)
        
        self.db.execute_query("""
            INSERT INTO novel_primitives
            (primitive_id, discovered_name, composition_tree, discovered_by_agent,
             discovered_in_game, discovered_at_generation, success_rate,
             games_validated_on, cross_game_generalization)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            primitive_id, discovered_name, json.dumps(composition_tree, default=str),
            discovered_by_agent, discovered_in_game, generation,
            success_rate, games_validated, cross_game_rate
        ))
        
        logger.info(f"[CODS] NOVEL PRIMITIVE discovered: '{discovered_name}' "
                   f"(cross_game={cross_game_rate:.2f})")
        
        return primitive_id
    
    def grandfather_primitive(
        self,
        primitive_name: str,
        implementation_ref: str,
        reason: str = "Oracle observed system needed this"
    ):
        """
        Grandfather a primitive (unlock without discovery).
        
        Used for primitives already in codebase that user approved.
        """
        existing = self.db.execute_query(
            "SELECT status FROM primitive_status WHERE primitive_name = ?",
            (primitive_name,)
        )
        
        if existing:
            self.db.execute_query("""
                UPDATE primitive_status 
                SET status = 'grandfathered',
                    unlocked_at = CURRENT_TIMESTAMP,
                    implementation_hint = ?
                WHERE primitive_name = ?
            """, (implementation_ref, primitive_name))
        else:
            self.db.execute_query("""
                INSERT INTO primitive_status
                (primitive_name, status, category, description, implementation_hint)
                VALUES (?, 'grandfathered', 'grandfathered', ?, ?)
            """, (primitive_name, reason, implementation_ref))
        
        self._grandfathered_primitives[primitive_name] = implementation_ref
        logger.info(f"[CODS] Grandfathered '{primitive_name}' -> {implementation_ref}")
    
    def track_primitive_usage(
        self,
        primitive_name: str,
        success: bool,
        score_contribution: float = 0.0
    ):
        """Track usage of a primitive for competition analysis."""
        self.db.execute_query("""
            UPDATE primitive_status 
            SET times_used = times_used + 1,
                avg_success_rate = (avg_success_rate * times_used + ?) / (times_used + 1),
                last_used_at = CURRENT_TIMESTAMP
            WHERE primitive_name = ?
        """, (1.0 if success else 0.0, primitive_name))
    
    def get_unlock_stats(self) -> Dict[str, Any]:
        """Get statistics about primitive unlocking."""
        stats = {}
        
        # Count by status
        counts = self.db.execute_query("""
            SELECT status, COUNT(*) as cnt
            FROM primitive_status
            GROUP BY status
        """)
        stats['by_status'] = {r['status']: r['cnt'] for r in counts} if counts else {}
        
        # Recent unlocks
        recent = self.db.execute_query("""
            SELECT primitive_name, unlocked_at, unlocked_by_agent
            FROM primitive_status
            WHERE status = 'unlocked'
            ORDER BY unlocked_at DESC
            LIMIT 5
        """)
        stats['recent_unlocks'] = [dict(r) for r in recent] if recent else []
        
        # Unlock attempt success rate
        attempts = self.db.execute_query("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN unlocked = 1 THEN 1 ELSE 0 END) as successful
            FROM primitive_unlock_attempts
        """)
        if attempts:
            total = attempts[0]['total'] or 0
            successful = attempts[0]['successful'] or 0
            stats['unlock_success_rate'] = successful / total if total > 0 else 0.0
            stats['total_attempts'] = total
        
        # Novel discoveries
        novel = self.db.execute_query("""
            SELECT COUNT(*) as cnt, AVG(cross_game_generalization) as avg_cross
            FROM novel_primitives
            WHERE is_active = TRUE
        """)
        if novel:
            stats['novel_count'] = novel[0]['cnt'] or 0
            stats['novel_avg_generalization'] = novel[0]['avg_cross'] or 0.0
        
        return stats
    
    def _generate_novel_name(self, composition_tree: Dict[str, Any]) -> str:
        """Generate a name for a novel primitive from its composition."""
        # Extract component primitives
        components = []
        
        def extract_names(node):
            if isinstance(node, dict):
                if 'primitive' in node:
                    components.append(node['primitive'])
                for v in node.values():
                    extract_names(v)
            elif isinstance(node, list):
                for item in node:
                    extract_names(item)
        
        extract_names(composition_tree)
        
        # Create name from first 3 components
        if components:
            parts = components[:3]
            name = "_".join(p[:4] for p in parts)
            return f"composed_{name}_{uuid.uuid4().hex[:4]}"
        
        return f"novel_{uuid.uuid4().hex[:8]}"


# ============================================================================
# GRANDFATHERED PRIMITIVES (Already Earned via Oracle Approval)
# ============================================================================

def grandfather_existing_primitives(manager: PrimitiveUnlockManager):
    """
    Grandfather primitives that already exist in codebase.
    These are considered "already unlocked" per CODS design doc.
    """
    
    grandfathered = [
        ("detect_symmetry", "visual_reasoning_engine.py:detect_symmetry()"),
        ("flood_fill", "object_detector.py:_flood_fill()"),
        ("detect_shapes", "visual_reasoning_engine.py:detect_shapes()"),
        ("find_repeating_patterns", "visual_reasoning_engine.py:find_repeating_patterns()"),
        ("analyze_color_distribution", "visual_reasoning_engine.py:analyze_color_distribution()"),
        ("analyze_spatial_relations", "visual_reasoning_engine.py:analyze_spatial_relations()"),
        ("detect_objects_in_frame", "object_detector.py:detect_objects_in_frame()"),
        ("parse_scene", "symbolic_reasoning_engine.py:parse_scene()"),
        ("_pattern_similarity", "sequence_abstraction.py:_pattern_similarity()"),
    ]
    
    for name, implementation in grandfathered:
        manager.grandfather_primitive(name, implementation)
    
    logger.info(f"[CODS] Grandfathered {len(grandfathered)} existing primitives")
