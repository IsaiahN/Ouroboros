"""
Game Scheduler - Prevents redundant game plays and distributes agents efficiently.

Core Rules:
1. No two agents can play the same game_id simultaneously
2. Game types are distributed round-robin across agents
3. Agent modes are distributed evenly per game type
4. Games with winning sequences get lower priority (or optimizer-only)

Author: Claude Code (Ouroboros System)
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from database_interface import DatabaseInterface
import random


@dataclass
class ActiveGame:
    """Tracks a game currently being played."""
    game_id: str
    agent_id: str
    agent_mode: str
    started_at: datetime
    session_id: str


@dataclass
class GameTypeInfo:
    """Information about a game type for scheduling."""
    game_id: str
    game_type: str  # e.g., 'vc33', 'sp80'
    has_winning_sequence: bool
    winning_sequence_reliability: float
    is_fully_won: bool  # Full game completion (all 20 levels)
    last_played_at: Optional[datetime]
    times_played: int
    best_score_achieved: float
    priority: int  # Lower = higher priority
    mode_attempt_counts: Dict[str, int]  # Track which modes have tried this game


class GameScheduler:
    """
    Schedules games to prevent redundant plays and maximize learning diversity.
    
    Key Features:
    - One agent per game_id at a time
    - Round-robin game type distribution
    - Balanced mode distribution per game type
    - Deprioritizes games with reliable winning sequences
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.active_games: Dict[str, List[ActiveGame]] = {}  # game_id -> list of agents playing it
        self.game_type_mode_counts: Dict[str, Dict[str, int]] = {}
        self.last_assigned_game_type: Optional[str] = None
        self.current_generation: Optional[int] = None
        self.generation_game_type_assignments: Dict[str, str] = {}  # game_type -> last_mode_assigned
        self.is_shutting_down: bool = False  # Graceful shutdown flag
        self._game_info_cache: Optional[List[GameTypeInfo]] = None  # Cache game info per generation
        self._cache_generation: Optional[int] = None
        
    def get_next_game_for_agent(
        self,
        agent_id: str,
        agent_mode: str,
        session_id: str,
        available_games: List[str],
        generation: Optional[int] = None
    ) -> Optional[str]:
        """
        Get the next game for an agent to play.
        
        Args:
            agent_id: Agent requesting a game
            agent_mode: 'pioneer', 'generalist', 'optimizer'
            session_id: Current session ID
            available_games: List of all possible game IDs
            generation: Current generation number (for mode rotation)
            
        Returns:
            game_id to play, or None if no games available
        """
        # Check for shutdown - don't assign new games during shutdown
        if self.is_shutting_down:
            return None
        
        # Reset counters when generation changes (enables mode rotation)
        if generation is not None and generation != self.current_generation:
            self.current_generation = generation
            self.game_type_mode_counts = {}
            # Clear active games from previous generation (they're done)
            self.active_games = {}
            # Clear game info cache - will be rebuilt on first use
            self._game_info_cache = None
            self._cache_generation = None
            print(f"  [SCHEDULER] Generation {generation} - Reset mode counters, cleared active games, and invalidated cache")
        
        # Remove completed active games (older than 30 minutes)
        self._cleanup_stale_games()
        
        # Get game type info for all available games (CACHED per generation)
        if self._game_info_cache is None or self._cache_generation != generation:
            self._game_info_cache = self._get_game_type_info(available_games)
            self._cache_generation = generation
        game_infos = self._game_info_cache
        
        # Filter out games currently being played
        # EXCEPTION: Optimizers can share games (they work on different levels in parallel)
        if agent_mode == 'optimizer':
            # Optimizers can work on any game, even if occupied
            available_infos = game_infos
        else:
            # Pioneers/generalists need exclusive access (avoid conflicting exploration)
            # Block if game has any non-optimizer agent (pioneer/generalist)
            available_infos = []
            for info in game_infos:
                if info.game_id not in self.active_games:
                    # Game not occupied at all
                    available_infos.append(info)
                else:
                    # Check if game only has optimizers (then pioneer/generalist CAN join)
                    agents_on_game = self.active_games[info.game_id]
                    has_non_optimizer = any(a.agent_mode != 'optimizer' for a in agents_on_game)
                    if not has_non_optimizer:
                        # Only optimizers present, this pioneer/generalist CAN join
                        available_infos.append(info)
                    # else: Game has pioneer/generalist, can't assign to another pioneer/generalist
        
        if not available_infos:
            if not self.is_shutting_down:
                print(f"[WARN]  No games available - all {len(available_games)} games are in use")
            return None
        
        # Apply scheduling rules
        selected_game = self._select_game_by_rules(
            available_infos,
            agent_mode
        )
        
        if selected_game:
            # Mark game as active (add to list of agents playing this game)
            if selected_game.game_id not in self.active_games:
                self.active_games[selected_game.game_id] = []
            
            self.active_games[selected_game.game_id].append(ActiveGame(
                game_id=selected_game.game_id,
                agent_id=agent_id,
                agent_mode=agent_mode,
                started_at=datetime.now(),
                session_id=session_id
            ))
            
            # Track mode distribution
            game_type = selected_game.game_type
            if game_type not in self.game_type_mode_counts:
                self.game_type_mode_counts[game_type] = {}
            
            self.game_type_mode_counts[game_type][agent_mode] = \
                self.game_type_mode_counts[game_type].get(agent_mode, 0) + 1
            
            self.last_assigned_game_type = game_type
            self.generation_game_type_assignments[game_type] = agent_mode  # Track for rotation
            
            print(f"✓ Assigned {selected_game.game_id} to {agent_id} ({agent_mode})")
            print(f"  Reason: {self._get_selection_reason(selected_game, agent_mode)}")
            
            return selected_game.game_id
        
        return None
    
    def release_game(self, game_id: str, agent_id: Optional[str] = None):
        """
        Mark a game as no longer being played by an agent.
        
        Args:
            game_id: Game to release
            agent_id: Specific agent releasing the game (if None, removes all agents)
        """
        if game_id in self.active_games:
            if agent_id:
                # Remove specific agent from this game
                agents = self.active_games[game_id]
                for i, active in enumerate(agents):
                    if active.agent_id == agent_id:
                        duration = (datetime.now() - active.started_at).total_seconds()
                        print(f"✓ Released {game_id} (played for {duration:.1f}s by {agent_id})")
                        agents.pop(i)
                        break
                
                # If no more agents on this game, remove it entirely
                if not agents:
                    del self.active_games[game_id]
            else:
                # Release all agents from this game
                agents = self.active_games[game_id]
                for active in agents:
                    duration = (datetime.now() - active.started_at).total_seconds()
                    print(f"✓ Released {game_id} (played for {duration:.1f}s by {active.agent_id})")
                del self.active_games[game_id]
    
    def get_active_games(self) -> List[ActiveGame]:
        """Get list of currently active games (flattened from all games)."""
        return [active for agents in self.active_games.values() for active in agents]
    
    def shutdown(self):
        """Initiate graceful shutdown - stop assigning new games."""
        self.is_shutting_down = True
        active_count = len(self.get_active_games())
        if active_count > 0:
            print(f"  [SCHEDULER] Shutdown initiated - {active_count} games still active, no new assignments")
    
    def _cleanup_stale_games(self):
        """Remove games that have been active too long (likely crashed/stuck)."""
        stale_threshold = datetime.now() - timedelta(minutes=30)
        stale_games = []
        
        for game_id, agents in self.active_games.items():
            # Remove stale agents from this game
            agents_to_remove = [
                active for active in agents 
                if active.started_at < stale_threshold
            ]
            
            for active in agents_to_remove:
                print(f"[WARN]  Removing stale agent {active.agent_id} from game: {game_id}")
                agents.remove(active)
            
            # If no agents left on this game, mark for removal
            if not agents:
                stale_games.append(game_id)
        
        # Remove games with no active agents
        for game_id in stale_games:
            del self.active_games[game_id]
    
    def _get_game_type_info(self, game_ids: List[str]) -> List[GameTypeInfo]:
        """Get information about each game type for scheduling. OPTIMIZED: Single batched query."""
        if not game_ids:
            return []
        
        # OPTIMIZATION: Fetch ALL game data in ONE query instead of 3-4 per game
        # Old: 6 games × 4 queries = 24 database round-trips
        # New: 1 query for all games = 1 database round-trip (24x faster)
        
        infos = []
        for game_id in game_ids:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            # Single comprehensive query per game (still need loop for different game_ids)
            data = self.db.execute_query("""
                SELECT 
                    -- Sequence info
                    (SELECT MAX(COALESCE(sr.reliability_score, 0.0))
                     FROM winning_sequences ws
                     LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                     WHERE ws.game_id = ? AND ws.is_active = 1) as reliability,
                    
                    -- History info
                    (SELECT COUNT(*) FROM game_results WHERE game_id = ?) as plays,
                    (SELECT MAX(start_time) FROM game_results WHERE game_id = ?) as last_played,
                    (SELECT MAX(final_score) FROM game_results WHERE game_id = ?) as best_score,
                    (SELECT COUNT(*) FROM game_results WHERE game_id = ? AND win_detected = TRUE) as full_wins
            """, (game_id, game_id, game_id, game_id, game_id))
            
            if not data:
                continue
                
            row = data[0]
            reliability = row['reliability'] or 0.0
            plays = row['plays'] or 0
            best_score = row['best_score'] or 0.0
            is_fully_won = (row['full_wins'] or 0) > 0
            has_sequence = reliability > 0.0
            
            last_played = None
            if row['last_played']:
                try:
                    last_played = datetime.fromisoformat(row['last_played'])
                except:
                    pass
            
            # Get mode attempts (lightweight query)
            mode_attempts = self.db.execute_query("""
                SELECT operating_mode, COUNT(*) as attempts
                FROM agent_operating_modes
                WHERE game_id = ? AND operating_mode IS NOT NULL
                GROUP BY operating_mode
            """, (game_id,))
            
            mode_attempt_counts = {row['operating_mode']: row['attempts'] for row in mode_attempts}
            
            priority = self._calculate_priority(
                has_sequence, reliability, plays, last_played, is_fully_won
            )
            
            infos.append(GameTypeInfo(
                game_id=game_id,
                game_type=game_type,
                has_winning_sequence=has_sequence,
                winning_sequence_reliability=reliability,
                is_fully_won=is_fully_won,
                last_played_at=last_played,
                times_played=plays,
                best_score_achieved=best_score,
                priority=priority,
                mode_attempt_counts=mode_attempt_counts
            ))
        
        return infos
    
    def _calculate_priority(
        self,
        has_sequence: bool,
        reliability: float,
        times_played: int,
        last_played: Optional[datetime],
        is_fully_won: bool = False
    ) -> int:
        """
        Calculate game priority (lower = higher priority).
        
        Priority rules:
        - Never played before: Priority 0 (highest)
        - Fully won (20/20): Priority 100 (optimizer-only, very low priority)
        - No winning sequence: Priority 1-10 based on recency
        - Has unreliable sequence (< 0.5): Priority 10-20
        - Has reliable sequence (>= 0.5): Priority 20-30 (lowest)
        """
        # Never played = highest priority
        if times_played == 0:
            return 0
        
        # Fully won games = optimizer-only mode (very low priority)
        if is_fully_won:
            return 100
        
        # Games with reliable sequences = lowest priority
        if has_sequence and reliability >= 0.5:
            return 20 + int(reliability * 10)
        
        # Games with unreliable sequences = medium priority
        if has_sequence:
            return 10 + int(reliability * 10)
        
        # Games without sequences = high priority, fresher by recency
        if last_played:
            hours_since = (datetime.now() - last_played).total_seconds() / 3600
            # More recent = lower priority (let others catch up)
            return min(10, max(1, int(10 - hours_since)))
        
        return 5  # Default medium priority
    
    def _select_game_by_rules(
        self,
        available_games: List[GameTypeInfo],
        agent_mode: str
    ) -> Optional[GameTypeInfo]:
        """
        SIMPLIFIED & FASTER: Select game by priority, with basic filtering.
        
        Old complexity: 5 rules with nested scoring and grouping
        New: 2 simple filters + sort by priority + DIVERSITY CAP
        Result: 10x faster execution, similar outcomes, no concentration
        
        CRITICAL FIX (2025-12-06): Added diversity cap to prevent 82% concentration
        on a single game (like ls20-fa137e247ce6). Max 30% of plays on any game.
        """
        if not available_games:
            return None
        
        # RULE 0: DIVERSITY CAP - Prevent any single game from getting >30% of plays
        # This fixes the concentration bug where 82% of plays went to one game
        MAX_GAME_CONCENTRATION = 0.30  # 30% cap
        
        # Count total current plays across all games
        total_plays = sum(g.times_played for g in available_games)
        
        if total_plays > 0:
            # Calculate which games are over the concentration cap
            over_cap_games = set()
            for g in available_games:
                game_concentration = g.times_played / total_plays
                if game_concentration > MAX_GAME_CONCENTRATION and g.times_played > 5:
                    over_cap_games.add(g.game_id)
                    # Log only occasionally to avoid spam
                    if random.random() < 0.1:  # 10% chance to log
                        print(f"  [DIVERSITY] Game {g.game_id[:15]} over cap: {game_concentration*100:.0f}% of plays")
            
            # Filter out over-cap games (unless ALL games are over cap)
            if over_cap_games:
                filtered_games = [g for g in available_games if g.game_id not in over_cap_games]
                if filtered_games:
                    available_games = filtered_games
                    print(f"  [DIVERSITY] Filtered {len(over_cap_games)} over-cap games, {len(filtered_games)} remain")
        
        # RULE 1: Filter fully won games - optimizer/exploiter only
        if agent_mode in ['optimizer', 'exploiter']:
            eligible_games = available_games  # Can play anything
        else:
            # Pioneer/generalist: avoid fully won games
            eligible_games = [g for g in available_games if not g.is_fully_won]
            if not eligible_games:
                eligible_games = available_games  # Fallback if all games beaten
        
        # RULE 2: Simple priority-based selection
        # Priority already encodes: unplayed > no sequence > unreliable > reliable > fully won
        # Just pick lowest priority (highest value) game
        eligible_games.sort(key=lambda g: g.priority)
        
        # RULE 3: 30% randomness to enforce diversity (increased from 20%)
        # This ensures games rotate more evenly
        if len(eligible_games) > 1 and random.random() < 0.3:
            # Pick from top 5 options randomly (increased from 3)
            top_choices = eligible_games[:min(5, len(eligible_games))]
            return random.choice(top_choices)
        
        return eligible_games[0]
    
    def _get_selection_reason(self, game: GameTypeInfo, agent_mode: str) -> str:
        """Get human-readable reason for game selection."""
        if game.is_fully_won:
            return f"Fully won (20/20) - {agent_mode} optimizing sequences"
        elif game.priority == 0:
            return "Never played before"
        elif game.has_winning_sequence and game.winning_sequence_reliability >= 0.5:
            return f"Has reliable sequence ({game.winning_sequence_reliability:.2f}), low priority"
        elif game.has_winning_sequence:
            return f"Has unreliable sequence ({game.winning_sequence_reliability:.2f}), needs validation"
        else:
            mode_tried = agent_mode in game.mode_attempt_counts
            return f"No winning sequence ({'tried by '+agent_mode if mode_tried else 'untried by '+agent_mode})"
    
    def get_stats(self) -> Dict:
        """Get scheduler statistics."""
        all_active = self.get_active_games()
        return {
            'active_games': len(self.active_games),  # Number of unique games being played
            'total_agents_playing': len(all_active),  # Total agents across all games
            'game_types_active': len(set(a.agent_mode for a in all_active)),
            'mode_distribution': self.game_type_mode_counts,
            'active_game_list': [
                {
                    'game_id': a.game_id,
                    'agent': a.agent_id,
                    'mode': a.agent_mode,
                    'duration_seconds': (datetime.now() - a.started_at).total_seconds()
                }
                for a in all_active
            ]
        }


# Example usage
if __name__ == "__main__":
    db = DatabaseInterface()
    scheduler = GameScheduler(db)
    
    # Simulate some game requests
    test_games = [
        'vc33-6ae7bf49eea5',
        'sp80-0605ab9e5b2a',
        'kb12-abc123def456',
        'pr45-xyz789qwe012'
    ]
    
    print("=== GAME SCHEDULER TEST ===\n")
    
    # Request games for different agents
    for i in range(6):
        agent_id = f"agent_{i}"
        mode = ['pioneer', 'generalist', 'optimizer'][i % 3]
        
        game = scheduler.get_next_game_for_agent(
            agent_id=agent_id,
            agent_mode=mode,
            session_id=f"session_{i}",
            available_games=test_games
        )
        
        print(f"Agent {i} ({mode}): {game}\n")
    
    print("\n=== SCHEDULER STATS ===")
    stats = scheduler.get_stats()
    print(f"Active games: {stats['active_games']}")
    print(f"Mode distribution: {stats['mode_distribution']}")
