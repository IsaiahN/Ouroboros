import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Primitive Unlock Manager — Bootstrapping Mechanism for Cognitive Primitives
==========================================================================

Per Master Ruleset (Pillar 2 — Metalearning Theory):

    "Agents must EARN higher-level concepts by demonstrating understanding."

    Agent composes seed primitives in novel way
             |
    System detects structural similarity to locked primitive
             |
    "Achievement Unlocked" — agent gets human-polished version
             |
    Better tools -> Better learning -> More discoveries
             |
    RECURSIVE ACCELERATION

Primitives have three states:
- LOCKED: Exists in the registry, agent hasn't demonstrated understanding
- EMERGING: Evidence accumulates (3+ successes across 2+ games needed)
- UNLOCKED: Fully available for agent use

Unlock criteria:
1. Agent composed seed primitives to approximate the locked primitive's behavior
2. Evidence: successful actions matching the primitive's expected output pattern
3. Threshold: 3+ successful compositions across 2+ different games

Tables used:
- primitive_status: Tracks each primitive's current status
- primitive_unlock_attempts: Records evidence toward unlocking

Following Rule 2: All data in database.
Following Rule 11: No Unicode emojis.
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class PrimitiveStatus(Enum):
    """Status of a primitive in the bootstrapping pipeline."""
    SEED = 'seed'                 # Always available — innate (Tier 0)
    LOCKED = 'locked'             # Exists but agent hasn't earned it
    EMERGING = 'emerging'         # Evidence accumulating, not yet unlocked
    UNLOCKED = 'unlocked'         # Fully available for use
    NOVEL = 'novel'               # Discovered by agents, not pre-defined
    GRANDFATHERED = 'grandfathered'  # Legacy status from pre-unlock era


# Unlock thresholds (from theory: 3+ successes across 2+ games)
MIN_SUCCESSES_FOR_UNLOCK = 3
MIN_GAMES_FOR_UNLOCK = 2
MIN_CROSS_GAME_SUCCESS_RATE = 0.40  # 40% cross-game success required
MIN_CONFIDENCE_FOR_UNLOCK = 0.60    # 60% overall success rate required


class PrimitiveUnlockManager:
    """Manages the primitive bootstrapping pipeline.

    Tracks evidence toward unlocking locked primitives, records unlock
    attempts, and promotes primitives through LOCKED -> EMERGING -> UNLOCKED.

    Usage:
        manager = PrimitiveUnlockManager(db)
        manager.apply_unlock_pressure('boundary_detection', agent_id, evidence)
        if manager.check_unlock_readiness(agent_id, 'boundary_detection'):
            manager.unlock_primitive(agent_id, 'boundary_detection')
    """

    def __init__(
        self,
        db: Optional[DatabaseInterface] = None,
        db_path: str = 'core_data.db',
    ):
        self.db = db or DatabaseInterface(db_path)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS primitive_status (
                    primitive_name TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    unlock_condition TEXT,
                    implementation_hint TEXT,
                    difficulty REAL DEFAULT 0.5,
                    unlocked_at TIMESTAMP,
                    unlocked_by_agent TEXT,
                    discovered_pattern TEXT,
                    times_used INTEGER DEFAULT 0,
                    avg_success_rate REAL DEFAULT 0.0,
                    last_used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS primitive_unlock_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    primitive_name TEXT NOT NULL,
                    agent_id TEXT,
                    generation INTEGER DEFAULT 0,
                    discovered_pattern TEXT NOT NULL,
                    pattern_hash TEXT,
                    game_ids_tested TEXT,
                    games_tested_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    cross_game_success_rate REAL DEFAULT 0.0,
                    rlvr_validation_passed BOOLEAN DEFAULT FALSE,
                    oracle_verdict TEXT,
                    oracle_reasoning TEXT,
                    similarity_to_locked REAL DEFAULT 0.0,
                    unlocked BOOLEAN DEFAULT FALSE,
                    marked_as_novel BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (primitive_name) REFERENCES primitive_status(primitive_name)
                )
            """)

            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_unlock_attempts_primitive
                ON primitive_unlock_attempts(primitive_name, unlocked)
            """)

        except Exception as e:
            logger.debug(f"[UNLOCK] Table creation (may exist): {e}")

    # =========================================================================
    # Core API
    # =========================================================================

    def get_primitive_status(self, primitive_name: str) -> Optional[str]:
        """Get current status of a primitive.

        Returns:
            Status string ('seed', 'locked', 'emerging', 'unlocked', 'novel',
            'grandfathered') or None if primitive not found.
        """
        rows = self.db.execute_query(
            "SELECT status FROM primitive_status WHERE primitive_name = ?",
            (primitive_name,),
        )
        if rows:
            return rows[0]['status']
        return None

    def apply_unlock_pressure(
        self,
        primitive_name: str,
        agent_id: str,
        evidence: Dict[str, Any],
        generation: int = 0,
    ) -> Optional[str]:
        """Record evidence toward unlocking a primitive.

        This is the primary entry point for the bootstrapping mechanism.
        Each piece of evidence is recorded as an unlock attempt.  When
        enough evidence accumulates (per thresholds), the primitive
        transitions to EMERGING or UNLOCKED.

        Args:
            primitive_name: Name of the locked primitive.
            agent_id: Agent that produced the evidence.
            evidence: Dict with keys like 'game_id', 'success', 'pattern'.
            generation: Current generation number.

        Returns:
            attempt_id if recorded, None if primitive not found/not lockable.
        """
        status = self.get_primitive_status(primitive_name)
        if status is None or status in ('seed', 'unlocked', 'grandfathered'):
            return None  # Nothing to unlock

        game_ids = evidence.get('game_ids', [])
        if isinstance(game_ids, str):
            game_ids = [game_ids]

        success_rate = evidence.get('success_rate', 0.0)
        cross_game = evidence.get('cross_game_success_rate', 0.0)

        attempt_id = self.record_unlock_attempt(
            primitive_name=primitive_name,
            discovered_pattern=evidence,
            game_ids_tested=game_ids,
            success_rate=success_rate,
            cross_game_success_rate=cross_game,
            agent_id=agent_id,
            generation=generation,
        )

        # Check if this tips the scales
        if status == 'locked':
            self._maybe_transition_to_emerging(primitive_name)
        elif status == 'emerging':
            if self.check_unlock_readiness(agent_id, primitive_name):
                self.unlock_primitive(agent_id, primitive_name)

        return attempt_id

    def record_unlock_attempt(
        self,
        primitive_name: str,
        discovered_pattern: Any,
        game_ids_tested: List[str],
        success_rate: float = 0.0,
        cross_game_success_rate: float = 0.0,
        agent_id: Optional[str] = None,
        generation: int = 0,
    ) -> str:
        """Record a single unlock attempt in the database.

        Called by concept_discovery_engine._apply_unlock_pressure_for_concept().

        Returns:
            attempt_id of the recorded attempt.
        """
        attempt_id = f"ua_{uuid.uuid4().hex[:12]}"

        pattern_json = json.dumps(discovered_pattern) if not isinstance(discovered_pattern, str) else discovered_pattern
        pattern_hash = hashlib.md5(pattern_json.encode()).hexdigest()[:16]
        game_ids_json = json.dumps(game_ids_tested)

        try:
            self.db.execute_query("""
                INSERT INTO primitive_unlock_attempts (
                    attempt_id, primitive_name, agent_id, generation,
                    discovered_pattern, pattern_hash,
                    game_ids_tested, games_tested_count,
                    success_rate, cross_game_success_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attempt_id,
                primitive_name,
                agent_id or 'system',
                generation,
                pattern_json,
                pattern_hash,
                game_ids_json,
                len(game_ids_tested),
                success_rate,
                cross_game_success_rate,
            ))
        except Exception as e:
            logger.error(f"[UNLOCK] Failed to record attempt: {e}")

        return attempt_id

    def check_unlock_readiness(
        self,
        agent_id: Optional[str],
        primitive_name: str,
    ) -> bool:
        """Check if a primitive has accumulated enough evidence for unlock.

        Criteria (from theory):
        1. 3+ successful attempts (compositions that approximate the primitive)
        2. Across 2+ different games (cross-domain validation)
        3. Success rate >= 60%
        4. Cross-game success rate >= 40%

        Args:
            agent_id: Optional agent filter (None = system-wide check).
            primitive_name: Primitive to check.

        Returns:
            True if ready for unlock.
        """
        status = self.get_primitive_status(primitive_name)
        if status in ('unlocked', 'seed', 'grandfathered'):
            return False  # Already available

        try:
            # Aggregate evidence across all attempts for this primitive
            rows = self.db.execute_query("""
                SELECT
                    COUNT(*) as total_attempts,
                    AVG(success_rate) as avg_success,
                    AVG(cross_game_success_rate) as avg_cross_game,
                    SUM(games_tested_count) as total_games_tested
                FROM primitive_unlock_attempts
                WHERE primitive_name = ?
                  AND success_rate > 0
            """, (primitive_name,))

            if not rows:
                return False

            row = rows[0]
            total = row.get('total_attempts', 0) or 0
            avg_success = row.get('avg_success', 0.0) or 0.0
            avg_cross = row.get('avg_cross_game', 0.0) or 0.0
            total_games = row.get('total_games_tested', 0) or 0

            # Count distinct game types tested
            game_rows = self.db.execute_query("""
                SELECT game_ids_tested FROM primitive_unlock_attempts
                WHERE primitive_name = ? AND success_rate > 0
            """, (primitive_name,))

            distinct_games = set()
            for gr in (game_rows or []):
                try:
                    ids = json.loads(gr.get('game_ids_tested', '[]'))
                    for gid in ids:
                        # Extract game type prefix
                        gt = gid[:4] if len(gid) >= 4 else gid
                        distinct_games.add(gt)
                except (json.JSONDecodeError, TypeError):
                    pass

            meets_criteria = (
                total >= MIN_SUCCESSES_FOR_UNLOCK
                and len(distinct_games) >= MIN_GAMES_FOR_UNLOCK
                and avg_success >= MIN_CONFIDENCE_FOR_UNLOCK
                and avg_cross >= MIN_CROSS_GAME_SUCCESS_RATE
            )

            if meets_criteria:
                logger.info(
                    f"[UNLOCK] {primitive_name} READY: "
                    f"{total} attempts, {len(distinct_games)} game types, "
                    f"success={avg_success:.2f}, cross_game={avg_cross:.2f}"
                )

            return meets_criteria

        except Exception as e:
            logger.error(f"[UNLOCK] Readiness check failed for {primitive_name}: {e}")
            return False

    def unlock_primitive(
        self,
        agent_id: Optional[str],
        primitive_name: str,
    ) -> bool:
        """Promote a primitive from LOCKED/EMERGING to UNLOCKED.

        This is the "Achievement Unlocked" moment from the theory.
        The primitive becomes fully available for agent use.

        Args:
            agent_id: Agent that triggered the unlock (may be None for system).
            primitive_name: Primitive to unlock.

        Returns:
            True if successfully unlocked.
        """
        try:
            # Get the best discovered pattern for this primitive
            best = self.db.execute_query("""
                SELECT discovered_pattern, success_rate
                FROM primitive_unlock_attempts
                WHERE primitive_name = ? AND success_rate > 0
                ORDER BY success_rate DESC, created_at DESC
                LIMIT 1
            """, (primitive_name,))

            pattern_json = best[0]['discovered_pattern'] if best else '{}'

            self.db.execute_query("""
                UPDATE primitive_status SET
                    status = 'unlocked',
                    unlocked_at = CURRENT_TIMESTAMP,
                    unlocked_by_agent = ?,
                    discovered_pattern = ?
                WHERE primitive_name = ?
                  AND status IN ('locked', 'emerging')
            """, (
                agent_id or 'system',
                pattern_json,
                primitive_name,
            ))

            # Mark all attempts for this primitive as unlocked
            self.db.execute_query("""
                UPDATE primitive_unlock_attempts SET unlocked = 1
                WHERE primitive_name = ?
            """, (primitive_name,))

            logger.info(
                f"[UNLOCK] *** PRIMITIVE UNLOCKED: {primitive_name} ***"
                f" (by {agent_id or 'system'})"
            )

            return True

        except Exception as e:
            logger.error(f"[UNLOCK] Failed to unlock {primitive_name}: {e}")
            return False

    # =========================================================================
    # Transition helpers
    # =========================================================================

    def _maybe_transition_to_emerging(self, primitive_name: str) -> bool:
        """Transition a LOCKED primitive to EMERGING if evidence exists.

        A single successful attempt is enough to move to EMERGING.
        """
        try:
            rows = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM primitive_unlock_attempts
                WHERE primitive_name = ? AND success_rate > 0
            """, (primitive_name,))

            if rows and (rows[0].get('cnt', 0) or 0) >= 1:
                self.db.execute_query("""
                    UPDATE primitive_status SET status = 'emerging'
                    WHERE primitive_name = ? AND status = 'locked'
                """, (primitive_name,))
                logger.info(f"[UNLOCK] {primitive_name}: LOCKED -> EMERGING")
                return True

        except Exception as e:
            logger.debug(f"[UNLOCK] Transition check failed: {e}")

        return False

    # =========================================================================
    # Batch operations (called from evolution_runner every 10 gens)
    # =========================================================================

    def check_all_unlock_readiness(self, generation: int = 0) -> List[str]:
        """Check all EMERGING primitives for unlock readiness.

        Called periodically from evolution_runner to promote primitives
        that have accumulated sufficient evidence.

        Returns:
            List of primitive names that were unlocked this pass.
        """
        unlocked_this_pass: List[str] = []

        try:
            emerging = self.db.execute_query("""
                SELECT primitive_name FROM primitive_status
                WHERE status = 'emerging'
            """)

            if not emerging:
                return unlocked_this_pass

            for row in emerging:
                name = row['primitive_name']
                if self.check_unlock_readiness(None, name):
                    if self.unlock_primitive(None, name):
                        unlocked_this_pass.append(name)

        except Exception as e:
            logger.error(f"[UNLOCK] Batch readiness check failed: {e}")

        if unlocked_this_pass:
            logger.info(
                f"[UNLOCK] Generation {generation}: "
                f"unlocked {len(unlocked_this_pass)} primitives: {unlocked_this_pass}"
            )

        return unlocked_this_pass

    def get_unlock_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the primitive unlock pipeline.

        Returns:
            Dict with counts per status category and recent unlocks.
        """
        summary: Dict[str, Any] = {
            'seed': 0, 'locked': 0, 'emerging': 0,
            'unlocked': 0, 'novel': 0, 'grandfathered': 0,
            'total_attempts': 0, 'recent_unlocks': [],
        }

        try:
            status_counts = self.db.execute_query("""
                SELECT status, COUNT(*) as cnt
                FROM primitive_status
                GROUP BY status
            """)
            for row in (status_counts or []):
                s = row.get('status', '')
                if s in summary:
                    summary[s] = row.get('cnt', 0) or 0

            attempt_count = self.db.execute_query(
                "SELECT COUNT(*) as cnt FROM primitive_unlock_attempts"
            )
            if attempt_count:
                summary['total_attempts'] = attempt_count[0].get('cnt', 0) or 0

            recent = self.db.execute_query("""
                SELECT primitive_name, unlocked_at, unlocked_by_agent
                FROM primitive_status
                WHERE status = 'unlocked' AND unlocked_at IS NOT NULL
                ORDER BY unlocked_at DESC
                LIMIT 5
            """)
            summary['recent_unlocks'] = recent or []

        except Exception as e:
            logger.debug(f"[UNLOCK] Summary query failed: {e}")

        return summary
