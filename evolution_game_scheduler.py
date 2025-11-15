"""
Integration wrapper for GameScheduler with autonomous_evolution_runner.py

This provides a simple interface for the evolution runner to get games
for agents without duplicating effort on the same game types.
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from typing import List, Dict, Optional
from game_scheduler import GameScheduler
from database_interface import DatabaseInterface


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
        
    def assign_games_to_agents(
        self,
        agents: List[Dict],
        total_games_to_play: int,
        available_game_ids: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """
        Assign games to agents, ensuring no duplicate game types running simultaneously.
        
        Args:
            agents: List of agent dicts with 'agent_id' and 'mode'
            total_games_to_play: Total number of games to play this generation
            available_game_ids: List of all possible games (if None, queries from DB)
            
        Returns:
            Dict mapping agent_id -> list of game_ids to play
        """
        if available_game_ids is None:
            available_game_ids = self._get_all_available_games()
        
        if not available_game_ids:
            print("⚠️  No games available in database!")
            return {}
        
        # Calculate games per agent
        if total_games_to_play <= len(agents):
            # Fewer games than agents - some agents won't play
            selected_agents = agents[:total_games_to_play]
            games_per_agent = 1
        else:
            # More games than agents - distribute evenly
            selected_agents = agents
            games_per_agent = max(1, total_games_to_play // len(agents))
        
        print(f"\n🎮 GAME SCHEDULER: Assigning {total_games_to_play} games to {len(selected_agents)} agents")
        print(f"   Games per agent: {games_per_agent}")
        print(f"   Available games: {len(available_game_ids)}")
        print(f"   Mode distribution: {self._count_modes(selected_agents)}\n")
        
        # Assign games to each agent
        assignments: Dict[str, List[str]] = {}
        
        for agent in selected_agents:
            agent_id = agent.get('agent_id')
            if not agent_id:
                continue  # Skip if no agent_id
                
            agent_mode = agent.get('mode', agent.get('operating_mode', 'generalist'))
            
            # Get games for this agent
            agent_games = []
            agent_generation = agent.get('generation', 0)
            for _ in range(games_per_agent):
                game_id = self.scheduler.get_next_game_for_agent(
                    agent_id=agent_id,
                    agent_mode=agent_mode,
                    session_id=f"gen_{agent_generation}",
                    available_games=available_game_ids,
                    generation=agent_generation  # Pass generation for rotation
                )
                
                if game_id:
                    agent_games.append(game_id)
                else:
                    print(f"   ⚠️  No more games available for {agent_id}")
                    break
            
            if agent_games:
                assignments[agent_id] = agent_games
        
        # Summary
        total_assigned = sum(len(games) for games in assignments.values())
        print(f"\n✓ Assigned {total_assigned} games to {len(assignments)} agents")
        print(f"  Active game types: {len(self.scheduler.get_active_games())}")
        
        return assignments
    
    def release_game(self, game_id: str):
        """Mark a game as completed (agent finished playing)."""
        self.scheduler.release_game(game_id)
    
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
    
    def _count_modes(self, agents: List[Dict]) -> Dict[str, int]:
        """Count agents by mode."""
        counts = {}
        for agent in agents:
            mode = agent.get('mode', agent.get('operating_mode', 'generalist'))
            counts[mode] = counts.get(mode, 0) + 1
        return counts


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
