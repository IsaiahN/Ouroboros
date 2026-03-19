"""
Rung Affinity Model - H41: Imitation Learning for Rung Selection.

Learns which rungs produce correct actions for each game type by
shadow-evaluating rungs during solver replay and crediting rungs
during cognitive wins.

The affinity table is the learned policy: for game_type X, rung Y
correctly matched the solver Z% of the time. High-affinity rungs
get priority boosts; low-affinity rungs get suppressed.

This replaces hardcoded game-type orderings with a generalizable,
data-driven mechanism that scales to 100s of game types.

Usage:
    model = RungAffinityModel()
    model.load(db)

    # During replay shadow evaluation
    model.record(game_type='ft09', rung_name='causal_click_mapping', hit=True)

    # Query for cognitive routing
    boost = model.get_boost_rungs('ft09')  # ['causal_click_mapping', ...]

    # Persist after game
    model.persist(db)
"""
import sys

sys.dont_write_bytecode = True

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class RungAffinityModel:
    """
    Tracks per-(game_type, rung_name) success rates from solver imitation.

    In-memory accumulator with batch DB persistence. No per-action writes.
    """

    def __init__(
        self,
        boost_threshold: float = 0.3,
        suppress_threshold: float = 0.05,
    ):
        self.boost_threshold = boost_threshold
        self.suppress_threshold = suppress_threshold

        # Core data: {game_type: {rung_name: {'hits': int, 'misses': int}}}
        self._data: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: {'hits': 0, 'misses': 0})
        )

        # Dirty flag for persistence
        self._dirty: Set[str] = set()

        # Cached affinity scores: {game_type: {rung_name: float}}
        self._affinity_cache: Dict[str, Dict[str, float]] = {}

    def load(self, db: Any) -> None:
        """Load existing affinity data from database."""
        if db is None:
            return
        try:
            rows = db.execute_query(
                "SELECT game_type, rung_name, hits, misses FROM rung_affinity"
            )
            if rows:
                for row in rows:
                    gt = row['game_type']
                    rn = row['rung_name']
                    self._data[gt][rn] = {
                        'hits': row['hits'],
                        'misses': row['misses'],
                    }
                self._affinity_cache.clear()
                logger.info(
                    f"[RUNG-AFFINITY] Loaded {len(rows)} entries "
                    f"for {len(self._data)} game types"
                )
        except Exception as e:
            logger.warning(f"[RUNG-AFFINITY] Load failed: {e}")

    def record(self, game_type: str, rung_name: str, hit: bool) -> None:
        """Record a shadow evaluation result (hit = matched solver action)."""
        entry = self._data[game_type][rung_name]
        if hit:
            entry['hits'] += 1
        else:
            entry['misses'] += 1
        self._dirty.add(game_type)
        # Invalidate cache for this game_type
        self._affinity_cache.pop(game_type, None)

    def get_affinity(self, game_type: str) -> Dict[str, float]:
        """Get affinity scores for all rungs in a game type.

        Returns:
            {rung_name: affinity_score} where score is hits/(hits+misses).
        """
        if game_type in self._affinity_cache:
            return self._affinity_cache[game_type]

        result: Dict[str, float] = {}
        if game_type in self._data:
            for rung_name, counts in self._data[game_type].items():
                total = counts['hits'] + counts['misses']
                if total > 0:
                    result[rung_name] = counts['hits'] / total

        self._affinity_cache[game_type] = result
        return result

    def get_boost_rungs(self, game_type: str, min_evals: int = 10) -> List[str]:
        """Get rungs with high affinity that should be priority-boosted.

        Args:
            game_type: Game type to query.
            min_evals: Minimum total evaluations to be considered (avoids noise).

        Returns:
            List of rung names with affinity above boost_threshold.
        """
        result = []
        if game_type not in self._data:
            return result
        for rung_name, counts in self._data[game_type].items():
            total = counts['hits'] + counts['misses']
            if total >= min_evals:
                affinity = counts['hits'] / total
                if affinity >= self.boost_threshold:
                    result.append(rung_name)
        return result

    def get_suppress_rungs(self, game_type: str, min_evals: int = 20) -> List[str]:
        """Get rungs with very low affinity that can be skipped.

        Requires more evaluations than boost to avoid premature suppression.
        """
        result = []
        if game_type not in self._data:
            return result
        for rung_name, counts in self._data[game_type].items():
            total = counts['hits'] + counts['misses']
            if total >= min_evals:
                affinity = counts['hits'] / total
                if affinity <= self.suppress_threshold:
                    result.append(rung_name)
        return result

    def persist(self, db: Any) -> None:
        """Batch-persist dirty entries to database."""
        if db is None or not self._dirty:
            return
        try:
            now = datetime.now().isoformat()
            for game_type in self._dirty:
                if game_type not in self._data:
                    continue
                for rung_name, counts in self._data[game_type].items():
                    total = counts['hits'] + counts['misses']
                    affinity = counts['hits'] / total if total > 0 else 0.0
                    db.execute_query(
                        """INSERT INTO rung_affinity
                           (game_type, rung_name, hits, misses, total, affinity, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(game_type, rung_name) DO UPDATE SET
                             hits = excluded.hits,
                             misses = excluded.misses,
                             total = excluded.total,
                             affinity = excluded.affinity,
                             updated_at = excluded.updated_at
                        """,
                        (game_type, rung_name, counts['hits'], counts['misses'],
                         total, affinity, now),
                    )
            self._dirty.clear()
            logger.debug("[RUNG-AFFINITY] Persisted to DB")
        except Exception as e:
            logger.warning(f"[RUNG-AFFINITY] Persist failed: {e}")

    def summary(self) -> str:
        """Human-readable summary of learned affinities."""
        lines = []
        for game_type in sorted(self._data.keys()):
            affinities = self.get_affinity(game_type)
            if not affinities:
                continue
            # Sort by affinity descending
            ranked = sorted(affinities.items(), key=lambda x: -x[1])
            top5 = ranked[:5]
            total_evals = sum(
                self._data[game_type][r]['hits'] + self._data[game_type][r]['misses']
                for r in affinities
            )
            lines.append(
                f"  {game_type}: {total_evals} evals, "
                f"top={', '.join(f'{n}({v:.0%})' for n, v in top5)}"
            )
        if lines:
            return "[RUNG-AFFINITY]\n" + "\n".join(lines)
        return "[RUNG-AFFINITY] No data yet"
