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
        self.active_games: Dict[str, ActiveGame] = {}
        self.game_type_mode_counts: Dict[str, Dict[str, int]] = {}
        self.last_assigned_game_type: Optional[str] = None
        self.current_generation: Optional[int] = None
        self.generation_game_type_assignments: Dict[str, str] = {}  # game_type -> last_mode_assigned
        
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
        # Reset counters when generation changes (enables mode rotation)
        if generation is not None and generation != self.current_generation:
            self.current_generation = generation
            self.game_type_mode_counts = {}
            print(f"  [SCHEDULER] Generation {generation} - Reset mode counters for rotation")
        
        # Remove completed active games (older than 30 minutes)
        self._cleanup_stale_games()
        
        # Get game type info for all available games
        game_infos = self._get_game_type_info(available_games)
        
        # Filter out games currently being played
        available_infos = [
            info for info in game_infos 
            if info.game_id not in self.active_games
        ]
        
        if not available_infos:
            print(f"⚠️  No games available - all {len(available_games)} games are in use")
            return None
        
        # Apply scheduling rules
        selected_game = self._select_game_by_rules(
            available_infos,
            agent_mode
        )
        
        if selected_game:
            # Mark game as active
            self.active_games[selected_game.game_id] = ActiveGame(
                game_id=selected_game.game_id,
                agent_id=agent_id,
                agent_mode=agent_mode,
                started_at=datetime.now(),
                session_id=session_id
            )
            
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
    
    def release_game(self, game_id: str):
        """Mark a game as no longer being played."""
        if game_id in self.active_games:
            active = self.active_games[game_id]
            duration = (datetime.now() - active.started_at).total_seconds()
            print(f"✓ Released {game_id} (played for {duration:.1f}s by {active.agent_id})")
            del self.active_games[game_id]
    
    def get_active_games(self) -> List[ActiveGame]:
        """Get list of currently active games."""
        return list(self.active_games.values())
    
    def _cleanup_stale_games(self):
        """Remove games that have been active too long (likely crashed/stuck)."""
        stale_threshold = datetime.now() - timedelta(minutes=30)
        stale_games = [
            game_id for game_id, active in self.active_games.items()
            if active.started_at < stale_threshold
        ]
        
        for game_id in stale_games:
            print(f"⚠️  Removing stale game: {game_id}")
            del self.active_games[game_id]
    
    def _get_game_type_info(self, game_ids: List[str]) -> List[GameTypeInfo]:
        """Get information about each game type for scheduling."""
        infos = []
        
        for game_id in game_ids:
            # Extract game type (e.g., 'sp80-abc123' -> 'sp80')
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            # Check for winning sequences
            sequences = self.db.execute_query("""
                SELECT ws.sequence_id, sr.reliability_score
                FROM winning_sequences ws
                LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                WHERE ws.game_id = ? AND ws.is_active = 1
                ORDER BY sr.reliability_score DESC
                LIMIT 1
            """, (game_id,))
            
            has_sequence = len(sequences) > 0
            reliability = sequences[0]['reliability_score'] if has_sequence and sequences[0]['reliability_score'] else 0.0
            
            # Check if fully won (score = 20)
            full_wins = self.db.execute_query("""
                SELECT COUNT(*) as win_count
                FROM game_results
                WHERE game_id = ? AND final_score >= 20
            """, (game_id,))
            is_fully_won = full_wins[0]['win_count'] > 0 if full_wins else False
            
            # Get play history
            history = self.db.execute_query("""
                SELECT COUNT(*) as plays, MAX(start_time) as last_played,
                       MAX(final_score) as best_score
                FROM game_results
                WHERE game_id = ?
            """, (game_id,))
            
            times_played = history[0]['plays'] if history else 0
            last_played_str = history[0]['last_played'] if history else None
            best_score = history[0]['best_score'] if history else 0.0
            
            last_played = None
            if last_played_str:
                try:
                    last_played = datetime.fromisoformat(last_played_str)
                except:
                    pass
            
            # NEW: Track which modes have attempted this game
            mode_attempts = self.db.execute_query("""
                SELECT 
                    aom.operating_mode,
                    COUNT(*) as attempts
                FROM agent_arc_performance aap
                JOIN agent_operating_modes aom ON aap.agent_id = aom.agent_id
                WHERE aap.game_id = ?
                GROUP BY aom.operating_mode
            """, (game_id,))
            
            mode_attempt_counts = {}
            for row in mode_attempts:
                mode_attempt_counts[row['operating_mode']] = row['attempts']
            
            # Calculate priority (lower = play sooner)
            priority = self._calculate_priority(
                has_sequence, reliability, times_played, last_played, is_fully_won
            )
            
            infos.append(GameTypeInfo(
                game_id=game_id,
                game_type=game_type,
                has_winning_sequence=has_sequence,
                winning_sequence_reliability=reliability,
                is_fully_won=is_fully_won,
                last_played_at=last_played,
                times_played=times_played,
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
        Select game using scheduling rules.
        
        Rules:
        1. Fully won games (20/20) → optimizer mode ONLY
        2. Don't assign games to modes that haven't attempted them yet (need data first)
        3. Round-robin game types (avoid repeating same type)
        4. Balance mode distribution per game type
        5. Consider game priority scores
        """
        if not available_games:
            return None
        
        # RULE 1: Filter fully won games - optimizer mode only
        if agent_mode == 'optimizer':
            # Optimizers can play any game, including fully won
            eligible_games = available_games
        else:
            # Pioneer/generalist cannot play fully won games
            eligible_games = [g for g in available_games if not g.is_fully_won]
            if not eligible_games:
                # If only fully won games available, allow it anyway
                eligible_games = available_games
        
        # RULE 2: Prefer games this mode has already attempted (have data to judge)
        # But also give untried modes a chance (30% of the time)
        import random
        give_untried_chance = random.random() < 0.3
        
        if not give_untried_chance:
            games_with_mode_data = [
                g for g in eligible_games 
                if agent_mode in g.mode_attempt_counts
            ]
            if games_with_mode_data:
                eligible_games = games_with_mode_data
        
        # Group by game type
        by_type: Dict[str, List[GameTypeInfo]] = {}
        for game in eligible_games:
            if game.game_type not in by_type:
                by_type[game.game_type] = []
            by_type[game.game_type].append(game)
        
        # RULE 3: Avoid repeating last assigned game type (round-robin)
        if self.last_assigned_game_type and self.last_assigned_game_type in by_type:
            other_types = {k: v for k, v in by_type.items() if k != self.last_assigned_game_type}
            if other_types:
                by_type = other_types
        
        # RULE 4 & 5: Score each game type by mode balance, rotation, and priority
        type_scores = []
        for game_type, games in by_type.items():
            # Check mode balance for this game type (current generation)
            mode_counts = self.game_type_mode_counts.get(game_type, {})
            current_mode_count = mode_counts.get(agent_mode, 0)
            
            # Prefer game types that need this mode (within generation)
            balance_score = -current_mode_count  # Fewer plays = higher score
            
            # ROTATION BONUS: Prefer game types that had different mode last generation
            rotation_bonus = 0
            last_mode = self.generation_game_type_assignments.get(game_type)
            if last_mode and last_mode != agent_mode:
                rotation_bonus = 15  # Strong encouragement for mode rotation across generations
            elif last_mode and last_mode == agent_mode:
                rotation_bonus = -10  # Penalty for repeating same mode
            
            # Prefer games without winning sequences or with low priority
            avg_priority = sum(g.priority for g in games) / len(games)
            priority_score = -avg_priority  # Lower priority = higher score
            
            # Prefer game types played less recently
            most_recent = max((g.last_played_at for g in games if g.last_played_at), default=None)
            recency_score = 0
            if most_recent:
                hours_ago = (datetime.now() - most_recent).total_seconds() / 3600
                recency_score = min(10, hours_ago)  # Older = higher score
            
            total_score = balance_score + rotation_bonus + priority_score + recency_score
            type_scores.append((game_type, total_score, games))
        
        # Select best game type
        type_scores.sort(key=lambda x: x[1], reverse=True)
        selected_type, score, games_in_type = type_scores[0]
        
        # Within selected type, choose game with best priority
        games_in_type.sort(key=lambda g: g.priority)
        return games_in_type[0]
    
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
        return {
            'active_games': len(self.active_games),
            'game_types_active': len(set(a.agent_mode for a in self.active_games.values())),
            'mode_distribution': self.game_type_mode_counts,
            'active_game_list': [
                {
                    'game_id': a.game_id,
                    'agent': a.agent_id,
                    'mode': a.agent_mode,
                    'duration_seconds': (datetime.now() - a.started_at).total_seconds()
                }
                for a in self.active_games.values()
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
