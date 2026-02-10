import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Integration wrapper for GameScheduler with autonomous_evolution_runner.py

This provides a simple interface for the evolution runner to get games
for agents without duplicating effort on the same game types.

Phase 3.4: Resonance-informed scheduling - game-type pairs with high
resonance are prioritized for optimizers/generalists and deprioritized
for pioneers (forces genuinely novel territory).
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import logging
import random
from typing import Dict, List, Optional

from database_interface import DatabaseInterface
from game_scheduler import GameScheduler

logger = logging.getLogger(__name__)


class EvolutionGameScheduler:
    """
    Wrapper around GameScheduler for evolution system integration.

    Usage in autonomous_evolution_runner.py:
        scheduler = EvolutionGameScheduler(db)
        games_for_agents = scheduler.assign_games_to_agents(
            agents=active_agents,
            total_games_to_play=50
        )
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.scheduler = GameScheduler(db)
        # Resonance priority cache: refreshed each generation
        self._resonance_cache: Optional[Dict[str, float]] = None
        self._resonance_cache_gen: Optional[int] = None

    def shutdown(self):
        """Initiate graceful shutdown."""
        self.scheduler.shutdown()

    def assign_games_to_agents(
        self,
        agents: List[Dict],
        total_games_to_play: int,
        available_game_ids: Optional[List[str]] = None,
        ensure_game_type_coverage: bool = False,
        mixed_domain: bool = False,
    ) -> Dict[str, List[str]]:
        """
        Assign games to agents, ensuring no duplicate game types running simultaneously.

        Args:
            agents: List of agent dicts with 'agent_id' and 'mode'
            total_games_to_play: Total number of games to play this generation
            available_game_ids: List of all possible games (if None, queries from DB)
            ensure_game_type_coverage: If True, ensures one game from each unique game type
                                       before random assignment (good when total_games_to_play
                                       equals the number of game types)
            mixed_domain: If True, mark this batch as mixed-domain (telemetry-only)

        Returns:
            Dict mapping agent_id -> list of game_ids to play
        """
        if available_game_ids is None:
            available_game_ids = self._get_all_available_games()

        if not available_game_ids:
            print("[WARN]  No games available in database!")
            return {}

        # Telemetry-only mixed-domain flag (does not change scheduling logic)
        self.scheduler.mixed_domain_flag = mixed_domain
        if mixed_domain:
            print("[SCHEDULER] Mixed-domain batch enabled (telemetry only; role ratios/budgets unchanged)")

        # ENSURE GAME TYPE COVERAGE: When enabled, make sure each unique game type is played
        if ensure_game_type_coverage:
            # Group games by type (prefix before '-')
            games_by_type: Dict[str, List[str]] = {}
            for game_id in available_game_ids:
                game_type = game_id.split('-')[0] if '-' in game_id else game_id
                if game_type not in games_by_type:
                    games_by_type[game_type] = []
                games_by_type[game_type].append(game_id)

            unique_types = len(games_by_type)

            # If we have fewer/equal games to play than unique types, guarantee one per type
            if total_games_to_play <= unique_types:
                # Pick one random game from each type
                import random
                coverage_games = []
                for game_type, type_games in games_by_type.items():
                    coverage_games.append(random.choice(type_games))

                # Shuffle and take only what we need
                random.shuffle(coverage_games)
                available_game_ids = coverage_games[:total_games_to_play]
                print(f"[COVERAGE] Ensured {len(available_game_ids)} unique game types: {[g.split('-')[0] for g in available_game_ids]}")
            else:
                # More games than types: include one of each type, then fill rest randomly
                import random
                coverage_games = []
                remaining_games = []

                for game_type, type_games in games_by_type.items():
                    # One guaranteed from each type
                    selected = random.choice(type_games)
                    coverage_games.append(selected)
                    # Rest go to remaining pool
                    remaining_games.extend([g for g in type_games if g != selected])

                # Fill remaining slots randomly
                extra_needed = total_games_to_play - len(coverage_games)
                if extra_needed > 0 and remaining_games:
                    random.shuffle(remaining_games)
                    coverage_games.extend(remaining_games[:extra_needed])

                available_game_ids = coverage_games
                print(f"[COVERAGE] Ensured {unique_types} game types covered + {extra_needed} extra games")

        # Calculate games per agent
        if total_games_to_play <= len(agents):
            # Fewer games than agents - some agents won't play
            selected_agents = agents[:total_games_to_play]
            games_per_agent = 1
        else:
            # More games than agents - distribute evenly
            selected_agents = agents
            games_per_agent = max(1, total_games_to_play // len(agents))

        print(f"\n[GAME] GAME SCHEDULER: Assigning {total_games_to_play} games to {len(selected_agents)} agents")
        print(f"   Games per agent: {games_per_agent}")
        print(f"   Available games: {len(available_game_ids)}")
        print(f"   Mode distribution: {self._count_modes(selected_agents)}\n")
        if mixed_domain:
            print("   Batch tag: mixed-domain (telemetry)")

        # Assign games to each agent
        assignments: Dict[str, List[str]] = {}

        # Phase 3.4: Load resonance priorities once per batch
        generation = agents[0].get('generation', 0) if agents else 0
        resonance_priorities = self._get_resonance_game_priorities(generation)
        if resonance_priorities:
            n_resonant = sum(1 for v in resonance_priorities.values() if v > 0)
            print(f"  [RESONANCE-SCHED] {n_resonant} game type(s) with resonance signal")

        for agent in selected_agents:
            # Check for shutdown before each agent assignment
            if self.scheduler.is_shutting_down:
                print("   [STOP] Graceful shutdown requested - stopping game assignments")
                break

            agent_id = agent.get('agent_id')
            if not agent_id:
                continue  # Skip if no agent_id

            agent_mode = agent.get('mode', agent.get('operating_mode', 'generalist'))

            # Phase 3.4: Reorder available games by resonance for this role
            role_games = self._reorder_games_by_resonance(
                available_game_ids, agent_mode, resonance_priorities
            )

            # Get games for this agent
            agent_games = []
            agent_generation = agent.get('generation', 0)
            for _ in range(games_per_agent):
                game_id = self.scheduler.get_next_game_for_agent(
                    agent_id=agent_id,
                    agent_mode=agent_mode,
                    session_id=f"gen_{agent_generation}{'_mixed' if mixed_domain else ''}",
                    available_games=role_games,
                    generation=agent_generation  # Pass generation for rotation
                )

                if game_id:
                    agent_games.append(game_id)
                else:
                    # If no games available and agent is not already optimizer, make them one
                    if agent_mode != 'optimizer' and not self.scheduler.is_shutting_down:
                        print(f"   [SYNC] Converting {agent_id} to optimizer mode (all games occupied)")
                        game_id = self.scheduler.get_next_game_for_agent(
                            agent_id=agent_id,
                            agent_mode='optimizer',  # Try as optimizer (can share games)
                            session_id=f"gen_{agent_generation}",
                            available_games=available_game_ids,
                            generation=agent_generation
                        )
                        if game_id:
                            agent_games.append(game_id)
                        elif not self.scheduler.is_shutting_down:
                            print(f"   [WARN]  No games available even as optimizer for {agent_id}")
                            break
                    else:
                        if not self.scheduler.is_shutting_down:
                            print(f"   [WARN]  No more games available for {agent_id}")
                        break

            if agent_games:
                assignments[agent_id] = agent_games

        # Summary
        total_assigned = sum(len(games) for games in assignments.values())
        print(f"\n[OK] Assigned {total_assigned} games to {len(assignments)} agents")
        print(f"  Active game types: {len(self.scheduler.get_active_games())}")

        return assignments

    def release_game(self, game_id: str, agent_id: Optional[str] = None):
        """Mark a game as completed (agent finished playing)."""
        self.scheduler.release_game(game_id, agent_id=agent_id)

    def release_all_agent_games(self, agent_id: str):
        """Release all games assigned to an agent."""
        active = self.scheduler.get_active_games()
        for game in active:
            if game.agent_id == agent_id:
                self.scheduler.release_game(game.game_id)

    def get_stats(self) -> Dict:
        """Get scheduler statistics."""
        return self.scheduler.get_stats()

    def _get_all_available_games(self) -> List[str]:
        """
        Dynamically discover all available game IDs from database.

        Sources (in priority order):
        1. game_results (games that have been played)
        2. winning_sequences (games with known sequences)
        3. agent_arc_performance (games attempted by agents)

        This scales automatically as new games are discovered.
        """
        # Get all unique game IDs from multiple sources
        games = self.db.execute_query("""
            SELECT DISTINCT game_id
            FROM (
                SELECT game_id FROM game_results WHERE game_id IS NOT NULL
                UNION
                SELECT game_id FROM winning_sequences WHERE game_id IS NOT NULL
                UNION
                SELECT game_id FROM agent_arc_performance WHERE game_id IS NOT NULL
            )
            ORDER BY game_id
        """)

        game_ids = [g['game_id'] for g in games if g['game_id']]

        if game_ids:
            # Detect unique game types dynamically
            game_types = set(gid.split('-')[0] for gid in game_ids if '-' in gid)
            print(f"  [DISCOVER] Found {len(game_ids)} games across {len(game_types)} game types: {sorted(game_types)}")

        return game_ids

    # =========================================================================
    # PHASE 3.4: Resonance-Informed Game Scheduling
    # =========================================================================

    def _get_resonance_game_priorities(
        self, generation: int
    ) -> Dict[str, float]:
        """Load resonance scores per game type from resonance_patterns.

        Returns a dict mapping ``game_type`` -> max resonance score across
        all resonance patterns that mention that game type.  Cached per
        generation to avoid repeated DB queries within the same batch.

        Args:
            generation: Current generation (for cache key).

        Returns:
            Dict mapping game_type -> max resonance_score (0.0 = no signal).
        """
        if (self._resonance_cache is not None
                and self._resonance_cache_gen == generation):
            return self._resonance_cache

        priorities: Dict[str, float] = {}

        try:
            rows = self.db.execute_query("""
                SELECT game_types, resonance_score
                FROM resonance_patterns
                WHERE resonance_score > 0
                ORDER BY resonance_score DESC
                LIMIT 200
            """)
        except Exception as e:
            logger.debug(f"Resonance priority query failed: {e}")
            self._resonance_cache = priorities
            self._resonance_cache_gen = generation
            return priorities

        if not rows:
            self._resonance_cache = priorities
            self._resonance_cache_gen = generation
            return priorities

        for row in rows:
            try:
                game_types = json.loads(row['game_types']) if row['game_types'] else []
            except (json.JSONDecodeError, TypeError):
                game_types = []

            score = row.get('resonance_score', 0.0) or 0.0
            for gt in game_types:
                priorities[gt] = max(priorities.get(gt, 0.0), score)

        self._resonance_cache = priorities
        self._resonance_cache_gen = generation
        return priorities

    def _reorder_games_by_resonance(
        self,
        available_game_ids: List[str],
        agent_mode: str,
        resonance_priorities: Dict[str, float],
    ) -> List[str]:
        """Reorder available games based on resonance signal and agent role.

        - **Optimizers / Generalists**: Front-load games with high resonance
          (leverage cross-game knowledge transfer).
        - **Pioneers**: Push resonant games to the back (force genuinely novel
          territory where no cross-game shortcut exists).
        - **Exploiters**: No reordering (micro-optimisation, not discovery).

        The underlying ``GameScheduler._select_game_by_rules`` still applies
        its own priority + 30% randomness, so this is a *soft* bias, not a
        hard override.

        Args:
            available_game_ids: List of game IDs in their current order.
            agent_mode: Agent role string.
            resonance_priorities: From ``_get_resonance_game_priorities()``.

        Returns:
            Reordered copy of ``available_game_ids``.
        """
        if not resonance_priorities or agent_mode == 'exploiter':
            return available_game_ids  # No change

        def _game_type(game_id: str) -> str:
            return game_id.split('-')[0] if '-' in game_id else game_id

        def _resonance_key(game_id: str) -> float:
            return resonance_priorities.get(_game_type(game_id), 0.0)

        if agent_mode in ('optimizer', 'generalist'):
            # Front-load: highest resonance first (descending)
            return sorted(available_game_ids, key=_resonance_key, reverse=True)
        elif agent_mode == 'pioneer':
            # Push back: lowest resonance first (ascending — novel territory)
            return sorted(available_game_ids, key=_resonance_key)
        else:
            return available_game_ids

    def _count_modes(self, agents: List[Dict]) -> Dict[str, int]:
        """Count agents by mode."""
        counts = {}
        for agent in agents:
            mode = agent.get('mode', agent.get('operating_mode', 'generalist'))
            counts[mode] = counts.get(mode, 0) + 1
        return counts

    # ------------------------------------------------------------------
    # Phase 3.4: Scheduling outcome tracking
    # ------------------------------------------------------------------

    def record_scheduling_outcome(
        self,
        agent_id: str,
        game_id: str,
        was_resonant: bool,
        score: float,
        generation: int,
    ) -> None:
        """Record whether a resonance-scheduled game produced a better outcome.

        Stores results in ``scheduling_outcomes`` so we can later compare
        win-rate / average score for resonant vs non-resonant assignments.
        """
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS scheduling_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    was_resonant INTEGER NOT NULL,
                    score REAL NOT NULL,
                    generation INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.db.execute_query("""
                INSERT INTO scheduling_outcomes
                    (agent_id, game_id, was_resonant, score, generation)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_id, game_id, 1 if was_resonant else 0, score, generation))
        except Exception as e:
            logger.debug(f"[SCHED-OUTCOME] Could not record: {e}")

    def get_scheduling_effectiveness(self, last_n_generations: int = 10) -> Dict:
        """Compare outcomes for resonance-scheduled vs non-resonant games.

        Returns dict with avg scores and win rates for each category.
        """
        try:
            rows = self.db.execute_query("""
                SELECT
                    was_resonant,
                    AVG(score) as avg_score,
                    COUNT(*) as count,
                    SUM(CASE WHEN score > 0 THEN 1 ELSE 0 END) as wins
                FROM scheduling_outcomes
                WHERE generation >= (
                    SELECT MAX(generation) - ? FROM scheduling_outcomes
                )
                GROUP BY was_resonant
            """, (last_n_generations,))

            stats = {'resonant': {}, 'non_resonant': {}}
            for row in (rows or []):
                key = 'resonant' if row['was_resonant'] else 'non_resonant'
                count = row['count'] or 1
                stats[key] = {
                    'avg_score': row['avg_score'] or 0.0,
                    'count': count,
                    'win_rate': (row['wins'] or 0) / count,
                }
            return stats
        except Exception:
            return {}


# Example usage
if __name__ == "__main__":
    db = DatabaseInterface()
    evo_scheduler = EvolutionGameScheduler(db)

    # Simulate agent population
    test_agents = [
        {'agent_id': f'agent_{i}', 'mode': ['pioneer', 'generalist', 'optimizer'][i % 3], 'generation': 5}
        for i in range(10)
    ]

    print("=== EVOLUTION GAME SCHEDULER TEST ===\n")

    # Assign games
    assignments = evo_scheduler.assign_games_to_agents(
        agents=test_agents,
        total_games_to_play=15
    )

    print("\n=== ASSIGNMENTS ===")
    for agent_id, games in assignments.items():
        print(f"{agent_id}: {games}")

    print("\n=== STATS ===")
    stats = evo_scheduler.get_stats()
    print(f"Active games: {stats['active_games']}")
    print(f"Mode distribution per game type:")
    for game_type, modes in stats['mode_distribution'].items():
        print(f"  {game_type}: {modes}")
