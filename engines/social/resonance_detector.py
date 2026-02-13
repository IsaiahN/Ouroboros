#!/usr/bin/env python3
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Resonance Detector - Cross-Role Pattern Resonance Detection

Implements the Resonance Discovery Principle from harmonies theory:
"Truth amplifies itself through cross-domain resonance, not random search."

In our context, "cross-domain" means cross-ROLE:
- When Pioneers (blind exploration), Generalists (network-guided), and
  Exploiters (micro-optimization) ALL independently converge on the same
  abstract pattern, that's RESONANCE - evidence of objective truth.

Key Features:
1. Pattern hashing: Abstract fingerprints from inferred beliefs
2. Role diversity scoring: How many different roles found this pattern
3. Resonance amplification: High-resonance patterns get priority
4. Probability gates: Role-specific query frequencies

Theoretical Basis:
- Pioneers have no network bias (frontier isolation)
- Generalists follow network consensus
- Exploiters have 50% sociopathic (ignore network) split
- If all three converge despite radically different biases = objective truth
"""

import os
import sys

# Disable pycache (Rule 1)
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import hashlib
import json
import logging
import random
import uuid
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


def _notify_concept_from_resonance(pattern: Dict[str, Any], beliefs: Dict[str, Any]) -> None:
    """
    Notify ConceptDiscoveryEngine when high resonance is detected.

    This closes the Unification -> Generalization gap:
    When agents with different roles converge on the same pattern,
    that commonality IS a concept candidate for cross-game generalization.
    """
    try:
        from concept_discovery_engine import ConceptDiscoveryEngine
        db = DatabaseInterface()
        concept_engine = ConceptDiscoveryEngine(db)

        # High resonance means multiple roles agree - this is concept-worthy
        theory = beliefs.get('working_theory_required', '')
        control = beliefs.get('self_model_required', '')

        # Create a pattern description from resonance
        pattern_description = f"resonance:{theory}:{control}"

        # Track across all game types where resonance was found
        for game_type in pattern.get('game_types', []):
            concept_engine.track_successful_operator_pattern(
                operator_id=f"resonance_{pattern.get('pattern_hash', 'unknown')[:8]}",
                game_id=game_type,
                sub_patterns=[pattern_description, theory, control]
            )

        logger.debug(
            f"[RESONANCE->CONCEPT] High resonance pattern fed to concept engine: "
            f"score={pattern.get('resonance_score', 0):.2f}, roles={pattern.get('role_diversity', 0)}"
        )
    except Exception as e:
        # Non-critical - concept discovery is enhancement
        logger.debug(f"[RESONANCE->CONCEPT] Notification failed: {e}")


# =============================================================================
# RESONANCE QUERY FREQUENCIES BY ROLE
# =============================================================================
# From harmonies theory - role-specific probability gates

RESONANCE_QUERY_THRESHOLDS = {
    # FIX (2025-01-08): Increased pioneer rate from 1% to 15%
    # GAP 3 showed resonance never finding patterns because pioneers were blocked
    'pioneer': 0.15,      # 15% - Frontier exploration needs network patterns
    'optimizer': 0.20,    # 20% - When stuck or seeking inspiration
    'generalist': 0.30,   # 30% - Consistency checks
    'exploiter': 0.10,    # 10% - Occasional sanity checks
}

# Novelty boost for pioneers (when pattern is "interesting")
PIONEER_NOVELTY_BOOST_THRESHOLD = 0.20  # 20% when novelty > 0.7


class ResonanceDetector:
    """
    Detects patterns that resonate across different agent roles.

    Resonance = same abstract pattern discovered by >=2 different role types
    independently. This is evidence of objective truth because agents with
    radically different information access and biases converged on the same answer.
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Create resonance tracking tables if they don't exist."""
        try:
            # Add pattern_hash column to inferred_beliefs if missing
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS resonance_patterns (
                    pattern_hash TEXT PRIMARY KEY,

                    -- Resonance metrics
                    role_diversity INTEGER DEFAULT 1,
                    roles_found TEXT,  -- JSON list of roles that found this
                    independent_discoverers INTEGER DEFAULT 1,
                    resonance_score REAL DEFAULT 0.0,

                    -- Pattern content (abstract)
                    theory_type TEXT,
                    control_type TEXT,
                    strategy_type TEXT,
                    canonical_beliefs TEXT,  -- JSON of canonicalized beliefs

                    -- Example sequences using this pattern
                    example_sequences TEXT,  -- JSON list of sequence_ids
                    game_types TEXT,  -- JSON list of game types

                    -- Tracking
                    first_detected DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    times_validated INTEGER DEFAULT 0
                )
            """)

            # Index for fast resonance lookups
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_resonance_score
                ON resonance_patterns(resonance_score DESC)
            """)

            logger.debug("[RESONANCE] Tables initialized")

        except Exception as e:
            logger.debug(f"Resonance table creation (may already exist): {e}")

    # =========================================================================
    # PATTERN HASHING - Abstract fingerprints from beliefs
    # =========================================================================

    def compute_belief_hash(self, beliefs: Dict[str, Any]) -> str:
        """
        Compute abstract fingerprint from belief structure.

        Ignores game-specific details, keeps cognitive structure.
        Two sequences with the same belief hash represent the same
        "way of thinking" even if the raw actions differ.

        Args:
            beliefs: Inferred beliefs dict from _extract_inferred_beliefs_from_sequence

        Returns:
            16-character hex hash representing abstract pattern
        """
        # Extract and classify theory type
        theory_type = self._classify_theory(beliefs.get('working_theory_required', ''))

        # Extract and classify control type
        control_type = self._classify_control(beliefs.get('self_model_required', ''))

        # Extract strategy from Q4 inference
        inferences = beliefs.get('inferences', {})
        strategy_type = self._classify_strategy(inferences.get('Q4_strategy', ''))

        # Canonical structure (order-independent)
        canonical = {
            'theory': theory_type,
            'control': control_type,
            'strategy': strategy_type
        }

        # Hash the canonical structure
        canonical_json = json.dumps(canonical, sort_keys=True)
        return hashlib.md5(canonical_json.encode()).hexdigest()[:16]

    def _classify_theory(self, theory: str) -> str:
        """Classify theory into abstract type."""
        if not theory or 'NULL' in theory:
            return 'unknown'

        theory_lower = theory.lower()

        if 'click' in theory_lower or 'tap' in theory_lower:
            return 'click_puzzle'
        elif 'movement' in theory_lower or 'move' in theory_lower or 'control' in theory_lower:
            return 'movement_puzzle'
        elif 'environment' in theory_lower or 'manipulation' in theory_lower:
            return 'environment_puzzle'
        elif 'pattern' in theory_lower or 'sequence' in theory_lower:
            return 'pattern_puzzle'
        else:
            return 'general'

    def _classify_control(self, control: str) -> str:
        """Classify control type into abstract type."""
        if not control or 'NULL' in control:
            return 'unknown'

        control_lower = control.lower()

        if 'single' in control_lower or 'one' in control_lower:
            return 'single_object'
        elif 'multiple' in control_lower or 'group' in control_lower:
            return 'multi_object'
        elif 'cursor' in control_lower or 'pointer' in control_lower:
            return 'cursor_control'
        else:
            return 'general'

    def _classify_strategy(self, strategy: str) -> str:
        """Classify strategy into abstract type."""
        if not strategy or 'NULL' in strategy:
            return 'unknown'

        strategy_lower = strategy.lower()

        if 'single action' in strategy_lower:
            return 'specialized'
        elif 'limited' in strategy_lower or 'focused' in strategy_lower:
            return 'focused'
        elif 'diverse' in strategy_lower or 'adaptive' in strategy_lower:
            return 'adaptive'
        else:
            return 'general'

    # =========================================================================
    # RESONANCE DETECTION - Find patterns with cross-role agreement
    # =========================================================================

    def detect_resonance(self, _generation: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Detect resonant patterns: same abstract beliefs, different roles.

        This is the core resonance detection algorithm. It finds patterns
        where agents with different roles (and thus different biases)
        independently converged on the same solution.

        Args:
            generation: Optional generation filter for recent patterns

        Returns:
            List of resonant patterns with scores
        """
        try:
            # Query to find patterns with role diversity
            # Joins inferred_beliefs with winning_sequences and agents
            # FIX 2026-01-16: Use ws.agent_id instead of ws.discovered_by (column doesn't exist)
            query = """
                SELECT
                    ib.working_theory_required,
                    ib.self_model_required,
                    ib.inferences,
                    COUNT(DISTINCT a.preferred_role) as role_diversity,
                    COUNT(DISTINCT ws.agent_id) as independent_discoverers,
                    GROUP_CONCAT(DISTINCT a.preferred_role) as roles_found,
                    GROUP_CONCAT(DISTINCT SUBSTR(ws.game_id, 1, 4)) as game_types,
                    GROUP_CONCAT(DISTINCT ib.sequence_id) as sequence_ids
                FROM inferred_beliefs ib
                JOIN winning_sequences ws ON ib.sequence_id = ws.sequence_id
                JOIN agents a ON ws.agent_id = a.agent_id
                WHERE ib.working_theory_required NOT LIKE 'NULL%'
                  AND ib.working_theory_required != ''
                GROUP BY ib.working_theory_required, ib.self_model_required
                HAVING role_diversity >= 2
                ORDER BY role_diversity DESC, independent_discoverers DESC
                LIMIT 50
            """

            results = self.db.execute_query(query)

            resonant_patterns = []
            for row in results:
                # Compute resonance score
                role_diversity = row['role_diversity']
                discoverers = row['independent_discoverers']

                # Resonance formula: role_diversity * log(discoverers + 1)
                import math
                resonance_score = role_diversity * math.log(discoverers + 1)

                # Build beliefs dict for hashing
                beliefs = {
                    'working_theory_required': row['working_theory_required'],
                    'self_model_required': row['self_model_required'],
                    'inferences': json.loads(row['inferences']) if row['inferences'] else {}
                }

                pattern_hash = self.compute_belief_hash(beliefs)

                pattern = {
                    'pattern_hash': pattern_hash,
                    'resonance_score': resonance_score,
                    'role_diversity': role_diversity,
                    'independent_discoverers': discoverers,
                    'roles_found': row['roles_found'].split(',') if row['roles_found'] else [],
                    'game_types': row['game_types'].split(',') if row['game_types'] else [],
                    'sequence_ids': row['sequence_ids'].split(',')[:5] if row['sequence_ids'] else [],
                    'theory_type': self._classify_theory(row['working_theory_required']),
                    'control_type': self._classify_control(row['self_model_required'])
                }

                resonant_patterns.append(pattern)

                # Store/update in resonance_patterns table
                self._store_resonance_pattern(pattern, beliefs)

            logger.info(f"[RESONANCE] Detected {len(resonant_patterns)} resonant patterns")
            return resonant_patterns

        except Exception as e:
            logger.error(f"Resonance detection failed: {e}")
            return []

    def _store_resonance_pattern(self, pattern: Dict[str, Any], beliefs: Dict[str, Any]):
        """Store or update a resonance pattern in the database."""
        try:
            pattern_hash = pattern['pattern_hash']

            existing = self.db.execute_query("""
                SELECT pattern_hash, times_validated FROM resonance_patterns
                WHERE pattern_hash = ?
            """, (pattern_hash,))

            if existing:
                # Update existing
                self.db.execute_query("""
                    UPDATE resonance_patterns SET
                        role_diversity = ?,
                        roles_found = ?,
                        independent_discoverers = ?,
                        resonance_score = ?,
                        example_sequences = ?,
                        game_types = ?,
                        times_validated = times_validated + 1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE pattern_hash = ?
                """, (
                    pattern['role_diversity'],
                    json.dumps(pattern['roles_found']),
                    pattern['independent_discoverers'],
                    pattern['resonance_score'],
                    json.dumps(pattern['sequence_ids']),
                    json.dumps(pattern['game_types']),
                    pattern_hash
                ))
            else:
                # Insert new
                self.db.execute_query("""
                    INSERT INTO resonance_patterns
                    (pattern_hash, role_diversity, roles_found, independent_discoverers,
                     resonance_score, theory_type, control_type, strategy_type,
                     canonical_beliefs, example_sequences, game_types)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern_hash,
                    pattern['role_diversity'],
                    json.dumps(pattern['roles_found']),
                    pattern['independent_discoverers'],
                    pattern['resonance_score'],
                    pattern['theory_type'],
                    pattern['control_type'],
                    pattern.get('strategy_type', 'general'),
                    json.dumps(beliefs),
                    json.dumps(pattern['sequence_ids']),
                    json.dumps(pattern['game_types'])
                ))

                # =============================================================
                # COGNITIVE INTEGRATION: Resonance -> Concept Discovery
                # =============================================================
                # When high resonance is detected (multiple roles agree),
                # this is concept-worthy - feed to concept discovery engine
                # =============================================================
                if pattern['resonance_score'] >= 2.0 and pattern['role_diversity'] >= 2:
                    _notify_concept_from_resonance(pattern, beliefs)

        except Exception as e:
            logger.debug(f"Storing resonance pattern failed: {e}")

    # =========================================================================
    # PHASE 3.1: Template-based Resonance Scanning
    # =========================================================================

    def scan_compressed_templates(self, _generation: int = 0) -> List[Dict[str, Any]]:
        """Detect cross-game resonance from Phase 2 compressed templates.

        Loads sequence_concepts (generalized winning sequences) and viral
        package templates, then computes structural similarity between
        different game types.  If two game types share template structure
        (>70 % positional overlap), a resonance pattern is recorded.

        This provides a SECOND, complementary resonance signal:
        - ``detect_resonance()`` finds role-diverse belief convergence
        - ``scan_compressed_templates()`` finds structural sequence overlap

        Args:
            generation: Current generation number (for logging).

        Returns:
            List of newly-detected resonance patterns.
        """
        import math

        new_patterns: List[Dict[str, Any]] = []

        # ------------------------------------------------------------------
        # Step A: Load sequence concepts grouped by game_type
        # ------------------------------------------------------------------
        try:
            concepts = self.db.execute_query("""
                SELECT concept_id, goal_type, layout_signature,
                       strategy_type, constraints, abstraction_level
                FROM sequence_concepts
                ORDER BY abstraction_level DESC
            """)
        except Exception:
            concepts = []

        if not concepts:
            logger.debug("[RESONANCE] No sequence_concepts to scan")
            return new_patterns

        # Group by game_type prefix (goal_type stores "<game_type>_L<n>")
        by_game: Dict[str, List[Dict]] = {}
        for c in concepts:
            gt = (c.get('goal_type') or '').split('_L')[0]
            if gt:
                by_game.setdefault(gt, []).append(c)

        game_types = list(by_game.keys())
        if len(game_types) < 2:
            logger.debug(f"[RESONANCE] Only {len(game_types)} game type(s) with concepts, need 2+")
            return new_patterns

        # ------------------------------------------------------------------
        # Step B: Load viral package templates as supplementary signal
        # ------------------------------------------------------------------
        try:
            templates = self.db.execute_query("""
                SELECT package_id, action_sequence, frontier_game_type
                FROM viral_information_packages
                WHERE package_type = 'template' AND is_active = 1
            """)
        except Exception:
            templates = []

        template_by_game: Dict[str, List[List]] = {}
        for t in templates:
            gt = t.get('frontier_game_type', '')
            if gt:
                try:
                    seq = json.loads(t['action_sequence']) if isinstance(t['action_sequence'], str) else t['action_sequence']
                    template_by_game.setdefault(gt, []).append(seq or [])
                except (json.JSONDecodeError, TypeError):
                    pass

        # ------------------------------------------------------------------
        # Step C: Pairwise comparison between game types
        # ------------------------------------------------------------------
        for i, gt_a in enumerate(game_types):
            for gt_b in game_types[i + 1:]:
                sim_score = self._template_similarity(
                    by_game[gt_a], by_game[gt_b],
                    template_by_game.get(gt_a, []),
                    template_by_game.get(gt_b, []),
                )

                if sim_score < 0.70:
                    continue  # Below threshold

                # Build pattern hash from the pair
                pair_key = ':'.join(sorted([gt_a, gt_b]))
                pattern_hash = hashlib.md5(
                    f"template_resonance:{pair_key}".encode()
                ).hexdigest()[:16]

                # Count how many agents independently solved both game types
                try:
                    disc_row = self.db.execute_query("""
                        SELECT COUNT(DISTINCT agent_id) as cnt
                        FROM winning_sequences
                        WHERE is_active = 1
                          AND (game_type = ? OR game_type = ?)
                        GROUP BY agent_id
                        HAVING COUNT(DISTINCT game_type) = 2
                    """, (gt_a, gt_b))
                    independent = len(disc_row) if disc_row else 1
                except Exception:
                    independent = 1

                resonance_score = sim_score * math.log(independent + 1) * 1.2

                pattern = {
                    'pattern_hash': pattern_hash,
                    'resonance_score': resonance_score,
                    'role_diversity': 0,  # Unknown at template level
                    'independent_discoverers': independent,
                    'roles_found': [],
                    'game_types': [gt_a, gt_b],
                    'sequence_ids': [],
                    'theory_type': 'template_overlap',
                    'control_type': 'structural',
                    'strategy_type': 'general',
                }

                self._store_resonance_pattern(pattern, {
                    'working_theory_required': f'template_overlap:{pair_key}',
                    'self_model_required': 'structural',
                })

                new_patterns.append(pattern)

                logger.info(
                    f"[RESONANCE-TEMPLATE] {gt_a}<->{gt_b} "
                    f"sim={sim_score:.2f} score={resonance_score:.2f} "
                    f"discoverers={independent}"
                )

        return new_patterns

    @staticmethod
    def _template_similarity(
        concepts_a: List[Dict],
        concepts_b: List[Dict],
        templates_a: List[List],
        templates_b: List[List],
    ) -> float:
        """Compute structural similarity between two game types.

        Combines two signals:
        1. Layout-signature overlap (invariant positions in sequence_concepts)
        2. Viral package template positional match

        Returns 0.0-1.0 similarity score.
        """
        scores: List[float] = []

        # --- Signal 1: concept layout_signature overlap ---
        for ca in concepts_a:
            sig_a_raw = ca.get('layout_signature', '[]')
            try:
                sig_a = json.loads(sig_a_raw) if isinstance(sig_a_raw, str) else sig_a_raw
            except (json.JSONDecodeError, TypeError):
                continue
            if not sig_a:
                continue

            for cb in concepts_b:
                sig_b_raw = cb.get('layout_signature', '[]')
                try:
                    sig_b = json.loads(sig_b_raw) if isinstance(sig_b_raw, str) else sig_b_raw
                except (json.JSONDecodeError, TypeError):
                    continue
                if not sig_b:
                    continue

                # Positional overlap ratio
                min_len = min(len(sig_a), len(sig_b))
                if min_len == 0:
                    continue
                matches = sum(1 for k in range(min_len) if sig_a[k] == sig_b[k])
                scores.append(matches / min_len)

        # --- Signal 2: viral package template overlap ---
        for ta in templates_a:
            if not ta:
                continue
            for tb in templates_b:
                if not tb:
                    continue
                min_len = min(len(ta), len(tb))
                if min_len == 0:
                    continue
                # Strip wildcard prefixes for comparison
                def _clean(x):
                    return x.lstrip('*') if isinstance(x, str) else x
                matches = sum(1 for k in range(min_len) if _clean(ta[k]) == _clean(tb[k]))
                scores.append(matches / min_len)

        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    # =========================================================================
    # PHASE 3.3: Visual Embedding Resonance
    # =========================================================================

    def detect_visual_resonance(
        self,
        _generation: int = 0,
        similarity_threshold: float = 0.80,
        min_embeddings_per_game: int = 3,
    ) -> List[Dict[str, Any]]:
        """Detect cross-game resonance from visual embedding similarity.

        Reads pre-computed frame_embeddings (positive score_delta) from the DB,
        computes a centroid per game_type, then finds game-type pairs whose
        centroids exceed ``similarity_threshold`` in cosine space.

        This is the THIRD resonance signal:
        - ``detect_resonance()``: belief-based (role-diverse convergence)
        - ``scan_compressed_templates()``: structural (sequence concept overlap)
        - ``detect_visual_resonance()``: visual (embedding space proximity)

        No torch dependency -- only numpy for centroid arithmetic.

        Args:
            generation: Current generation (for logging).
            similarity_threshold: Cosine similarity threshold (default 0.80).
            min_embeddings_per_game: Minimum embeddings required per game type
                to form a meaningful centroid.

        Returns:
            List of newly-detected visual resonance patterns.
        """
        import math

        try:
            import numpy as np
        except ImportError:
            logger.debug("[RESONANCE-VISUAL] numpy not available")
            return []

        new_patterns: List[Dict[str, Any]] = []

        # Load positive-outcome embeddings grouped by game_type
        try:
            rows = self.db.execute_query("""
                SELECT game_type, embedding
                FROM frame_embeddings
                WHERE score_delta > 0
                ORDER BY score_delta DESC
                LIMIT 4000
            """)
        except Exception as e:
            logger.debug(f"[RESONANCE-VISUAL] Embedding query failed: {e}")
            return new_patterns

        if not rows:
            logger.debug("[RESONANCE-VISUAL] No positive-outcome embeddings found")
            return new_patterns

        # Group embeddings by game_type
        embeds_by_game: Dict[str, List] = {}
        for row in rows:
            gt = row['game_type']
            try:
                embed = np.frombuffer(row['embedding'], dtype=np.float32)
                if embed.shape[0] == 128:
                    embeds_by_game.setdefault(gt, []).append(embed)
            except Exception:
                continue

        # Compute L2-normalized centroid per game_type
        centroids: Dict[str, Any] = {}
        for gt, embeds in embeds_by_game.items():
            if len(embeds) < min_embeddings_per_game:
                continue
            stacked = np.stack(embeds)
            centroid = stacked.mean(axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 1e-8:
                centroids[gt] = centroid / norm

        game_types = list(centroids.keys())
        if len(game_types) < 2:
            logger.debug(
                f"[RESONANCE-VISUAL] Only {len(game_types)} game type(s) "
                f"with enough embeddings, need 2+"
            )
            return new_patterns

        # Pairwise cosine similarity between centroids
        for i, gt_a in enumerate(game_types):
            for gt_b in game_types[i + 1:]:
                sim = float(np.dot(centroids[gt_a], centroids[gt_b]))

                if sim < similarity_threshold:
                    continue

                # Build pattern hash
                pair_key = ':'.join(sorted([gt_a, gt_b]))
                pattern_hash = hashlib.md5(
                    f"visual_resonance:{pair_key}".encode()
                ).hexdigest()[:16]

                # Count independent discoverers (agents that beat both games)
                try:
                    disc_row = self.db.execute_query("""
                        SELECT COUNT(DISTINCT agent_id) as cnt
                        FROM winning_sequences
                        WHERE is_active = 1
                          AND (game_type = ? OR game_type = ?)
                        GROUP BY agent_id
                        HAVING COUNT(DISTINCT game_type) = 2
                    """, (gt_a, gt_b))
                    independent = len(disc_row) if disc_row else 1
                except Exception:
                    independent = 1

                resonance_score = sim * math.log(independent + 1) * 1.1

                pattern = {
                    'pattern_hash': pattern_hash,
                    'resonance_score': resonance_score,
                    'role_diversity': 0,
                    'independent_discoverers': independent,
                    'roles_found': [],
                    'game_types': [gt_a, gt_b],
                    'sequence_ids': [],
                    'theory_type': 'visual_similarity',
                    'control_type': 'embedding',
                    'strategy_type': 'general',
                }

                self._store_resonance_pattern(pattern, {
                    'working_theory_required': f'visual_similarity:{pair_key}',
                    'self_model_required': 'embedding',
                })

                new_patterns.append(pattern)

                logger.info(
                    f"[RESONANCE-VISUAL] {gt_a}<->{gt_b} "
                    f"cosine={sim:.3f} score={resonance_score:.2f}"
                )

        return new_patterns

    # =========================================================================
    # COMBINED RESONANCE SCORING (Phase 3.3)
    # =========================================================================

    def get_combined_resonance(self) -> Dict[str, Dict[str, Any]]:
        """Aggregate all three resonance signals into a combined score per pair.

        For each game-type pair in ``resonance_patterns``, computes:

        - **belief_score**: from role-diverse convergence (``detect_resonance``)
        - **template_score**: from structural overlap (``scan_compressed_templates``)
        - **visual_score**: from embedding similarity (``detect_visual_resonance``)
        - **combined_score**: ``max(signals) * agreement_bonus``

        Agreement bonus: 1.5x if 2 signals agree, 2.0x if all 3.

        Returns:
            Dict mapping ``"game_a:game_b"`` -> combined resonance info dict.
        """
        try:
            rows = self.db.execute_query("""
                SELECT pattern_hash, resonance_score, theory_type, game_types
                FROM resonance_patterns
                WHERE resonance_score > 0
                ORDER BY resonance_score DESC
            """)
        except Exception:
            return {}

        if not rows:
            return {}

        # Group by game-type pair
        pair_signals: Dict[str, Dict[str, float]] = {}
        for row in rows:
            try:
                game_types = json.loads(row['game_types']) if row['game_types'] else []
            except (json.JSONDecodeError, TypeError):
                game_types = []

            if len(game_types) < 2:
                continue

            pair_key = ':'.join(sorted(game_types[:2]))
            if pair_key not in pair_signals:
                pair_signals[pair_key] = {
                    'belief': 0.0, 'template': 0.0, 'visual': 0.0
                }

            theory = row.get('theory_type', '')
            score = row.get('resonance_score', 0.0) or 0.0

            if theory == 'template_overlap':
                pair_signals[pair_key]['template'] = max(
                    pair_signals[pair_key]['template'], score
                )
            elif theory == 'visual_similarity':
                pair_signals[pair_key]['visual'] = max(
                    pair_signals[pair_key]['visual'], score
                )
            else:
                pair_signals[pair_key]['belief'] = max(
                    pair_signals[pair_key]['belief'], score
                )

        # Compute combined scores with agreement bonus
        combined: Dict[str, Dict[str, Any]] = {}
        for pair_key, signals in pair_signals.items():
            active_signals = sum(1 for v in signals.values() if v > 0)
            max_signal = max(signals.values())

            # 1.5x if 2 signals agree, 2.0x if all 3
            if active_signals >= 3:
                agreement_bonus = 2.0
            elif active_signals >= 2:
                agreement_bonus = 1.5
            else:
                agreement_bonus = 1.0

            combined_score = max_signal * agreement_bonus

            combined[pair_key] = {
                'game_types': pair_key.split(':'),
                'belief_score': signals['belief'],
                'template_score': signals['template'],
                'visual_score': signals['visual'],
                'active_signals': active_signals,
                'agreement_bonus': agreement_bonus,
                'combined_score': combined_score,
            }

        return combined

    # =========================================================================
    # RESONANCE QUERIES - Role-specific pattern lookups
    # =========================================================================

    def get_resonant_patterns(
        self,
        min_score: float = 1.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get high-resonance patterns for network-wide prioritization.

        Args:
            min_score: Minimum resonance score threshold
            limit: Maximum patterns to return

        Returns:
            List of resonant patterns ordered by score
        """
        try:
            results = self.db.execute_query("""
                SELECT pattern_hash, resonance_score, role_diversity,
                       roles_found, theory_type, control_type, game_types
                FROM resonance_patterns
                WHERE resonance_score >= ?
                ORDER BY resonance_score DESC
                LIMIT ?
            """, (min_score, limit))

            patterns = []
            for row in results:
                patterns.append({
                    'pattern_hash': row['pattern_hash'],
                    'resonance_score': row['resonance_score'],
                    'role_diversity': row['role_diversity'],
                    'roles_found': json.loads(row['roles_found']) if row['roles_found'] else [],
                    'theory_type': row['theory_type'],
                    'control_type': row['control_type'],
                    'game_types': json.loads(row['game_types']) if row['game_types'] else []
                })

            return patterns

        except Exception as e:
            logger.debug(f"Getting resonant patterns failed: {e}")
            return []

    def get_pattern_resonance(self, beliefs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get resonance information for a specific belief pattern.

        Use this to check if the current pattern has been validated
        by multiple roles (i.e., is likely objective truth).

        Args:
            beliefs: Inferred beliefs dict

        Returns:
            Resonance info if pattern exists, None otherwise
        """
        try:
            pattern_hash = self.compute_belief_hash(beliefs)

            results = self.db.execute_query("""
                SELECT resonance_score, role_diversity, roles_found,
                       independent_discoverers, theory_type
                FROM resonance_patterns
                WHERE pattern_hash = ?
            """, (pattern_hash,))

            if results:
                row = results[0]
                return {
                    'pattern_hash': pattern_hash,
                    'resonance_score': row['resonance_score'],
                    'role_diversity': row['role_diversity'],
                    'roles_found': json.loads(row['roles_found']) if row['roles_found'] else [],
                    'independent_discoverers': row['independent_discoverers'],
                    'is_resonant': row['role_diversity'] >= 2
                }

            return None

        except Exception as e:
            logger.debug(f"Pattern resonance lookup failed: {e}")
            return None

    # =========================================================================
    # PROBABILITY GATES - Role-specific query frequencies
    # =========================================================================

    def should_query_resonance(
        self,
        agent_role: str,
        pattern_novelty: float = 0.0,
        is_stuck: bool = False
    ) -> bool:
        """
        Determine if agent should query for cross-role resonance this action.

        Implements role-specific frequency gates from harmonies theory:
        - Pioneer: 1% base, boosted to 20% on high-novelty patterns
        - Optimizer: 10% base, boosted when stuck
        - Generalist: 30% (consistency checks)
        - Exploiter: 5% (occasional sanity checks)

        Args:
            agent_role: Role of the agent (pioneer, optimizer, generalist, exploiter)
            pattern_novelty: 0.0-1.0 novelty score of current pattern
            is_stuck: Whether agent is currently stuck

        Returns:
            True if agent should query resonance this action
        """
        base_threshold = RESONANCE_QUERY_THRESHOLDS.get(agent_role.lower(), 0.10)

        # Pioneer boost on high-novelty patterns
        if agent_role.lower() == 'pioneer' and pattern_novelty > 0.7:
            base_threshold = PIONEER_NOVELTY_BOOST_THRESHOLD
            logger.debug(f"[RESONANCE] Pioneer novelty boost: {base_threshold}")

        # Optimizer boost when stuck
        if agent_role.lower() == 'optimizer' and is_stuck:
            base_threshold = min(0.30, base_threshold * 2.0)
            logger.debug(f"[RESONANCE] Optimizer stuck boost: {base_threshold}")

        should_query = random.random() < base_threshold

        if should_query:
            logger.debug(f"[RESONANCE] {agent_role} triggered resonance query (threshold: {base_threshold})")

        return should_query

    # =========================================================================
    # RESONANCE SCORING - Calculate pattern resonance
    # =========================================================================

    def calculate_resonance_score(
        self,
        role_diversity: int,
        independent_discoverers: int,
        game_type_diversity: int = 1
    ) -> float:
        """
        Calculate resonance score for a pattern.

        Formula: role_diversity * log(discoverers + 1) * (1 + game_diversity * 0.1)

        Higher scores indicate:
        - More role types agree (strongest signal)
        - More independent agents found it
        - Pattern works across more game types

        Args:
            role_diversity: Number of different roles that found pattern
            independent_discoverers: Number of independent agents
            game_type_diversity: Number of different game types

        Returns:
            Resonance score (0.0 = no resonance, higher = stronger)
        """
        import math

        if role_diversity < 2:
            return 0.0  # No resonance with single role

        base_score = role_diversity * math.log(independent_discoverers + 1)
        game_bonus = 1.0 + (game_type_diversity - 1) * 0.1

        return base_score * game_bonus

    # =========================================================================
    # NETWORK INTEGRATION - For regulatory engine
    # =========================================================================

    def get_resonance_summary(self) -> Dict[str, Any]:
        """
        Get summary of resonance state for regulatory engine.

        Returns:
            Summary dict with resonance health metrics
        """
        try:
            # Count total resonant patterns
            total = self.db.execute_query("""
                SELECT COUNT(*) as count, AVG(resonance_score) as avg_score,
                       MAX(resonance_score) as max_score
                FROM resonance_patterns
                WHERE role_diversity >= 2
            """)

            # Get role coverage
            role_coverage = self.db.execute_query("""
                SELECT roles_found, COUNT(*) as pattern_count
                FROM resonance_patterns
                WHERE role_diversity >= 2
                GROUP BY roles_found
                ORDER BY pattern_count DESC
                LIMIT 5
            """)

            if total and total[0]:
                return {
                    'total_resonant_patterns': total[0]['count'] or 0,
                    'average_resonance_score': total[0]['avg_score'] or 0.0,
                    'max_resonance_score': total[0]['max_score'] or 0.0,
                    'top_role_combinations': [
                        {'roles': r['roles_found'], 'count': r['pattern_count']}
                        for r in role_coverage
                    ] if role_coverage else []
                }

            return {
                'total_resonant_patterns': 0,
                'average_resonance_score': 0.0,
                'max_resonance_score': 0.0,
                'top_role_combinations': []
            }

        except Exception as e:
            logger.debug(f"Resonance summary failed: {e}")
            return {'error': str(e)}

    def update_pattern_effectiveness(self, pattern: Dict[str, Any], was_positive: bool) -> None:
        """
        Update pattern effectiveness based on outcome feedback.

        This is called by experience_outcome() when a resonance-matched action
        produces a result. Updates the pattern's resonance score based on whether
        it led to positive or negative outcomes.

        Args:
            pattern: Pattern dict with 'pattern_hash' or similar identifier
            was_positive: Whether the action using this pattern was successful
        """
        try:
            pattern_hash = pattern.get('pattern_hash')
            if not pattern_hash:
                return

            # Get current validation count
            result = self.db.execute_query("""
                SELECT times_validated, times_succeeded, resonance_score
                FROM resonance_patterns
                WHERE pattern_hash = ?
            """, (pattern_hash,))

            if not result:
                return

            row = result[0]
            times_validated = (row.get('times_validated') or 0) + 1
            times_succeeded = (row.get('times_succeeded') or 0) + (1 if was_positive else 0)

            # Update resonance score based on success rate
            # Higher success rate = higher resonance confidence
            success_rate = times_succeeded / max(times_validated, 1)
            current_score = row.get('resonance_score') or 1.0

            # Adjust score: successful uses increase it, failures decrease it
            if was_positive:
                new_score = current_score * 1.05  # 5% boost
            else:
                new_score = current_score * 0.95  # 5% penalty

            self.db.execute_query("""
                UPDATE resonance_patterns SET
                    times_validated = ?,
                    times_succeeded = ?,
                    resonance_score = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE pattern_hash = ?
            """, (times_validated, times_succeeded, new_score, pattern_hash))

            logger.debug(
                f"[RESONANCE] Pattern {pattern_hash[:8]} effectiveness updated: "
                f"success_rate={success_rate:.2f}, score={current_score:.2f}->{new_score:.2f}"
            )

        except Exception as e:
            logger.debug(f"Pattern effectiveness update failed: {e}")


# =============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# =============================================================================

def should_query_resonance(agent_role: str, pattern_novelty: float = 0.0, is_stuck: bool = False) -> bool:
    """
    Module-level convenience function for role-based resonance query gate.

    Can be imported directly without instantiating ResonanceDetector.
    """
    # FIX (2025-01-08): Always query resonance when stuck (GAP 3)
    # Stuck agents desperately need network wisdom - don't block them
    if is_stuck:
        return True

    base_threshold = RESONANCE_QUERY_THRESHOLDS.get(agent_role.lower(), 0.10)

    if agent_role.lower() == 'pioneer' and pattern_novelty > 0.7:
        base_threshold = PIONEER_NOVELTY_BOOST_THRESHOLD

    if agent_role.lower() == 'optimizer':
        # Optimizers should query more often to find proven patterns
        base_threshold = min(0.40, base_threshold * 2.0)

    return random.random() < base_threshold
