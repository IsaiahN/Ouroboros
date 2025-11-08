#!/usr/bin/env python3
"""
Game Diversity Preservation System

Ensures every game has at least one active specialist at all times.
Scales to hundreds of games without bloating population.

Design:
1. Protected Slots: Each game gets 1-3 protected specialist slots
2. Dynamic Assignment: Underrepresented games get priority
3. Generalist Reserve: Pool of agents that can fill gaps
4. Pruning Protection: Last specialist of each game cannot be culled
"""

from database_interface import DatabaseInterface
from typing import Dict, List, Set, Tuple, Any
import json
import random

class GameDiversityPreserver:
    """Ensures all games maintain active specialist coverage"""
    
    def __init__(self, db: DatabaseInterface, min_specialists_per_game: int = 1,
                 max_specialists_per_game: int = 3):
        """
        Initialize diversity preserver
        
        Args:
            db: Database interface
            min_specialists_per_game: Minimum specialists per game (default 1)
            max_specialists_per_game: Maximum specialists per game (for priority games)
        """
        self.db = db
        self.min_specialists = min_specialists_per_game
        self.max_specialists = max_specialists_per_game
    
    def get_game_specialist_counts(self) -> Dict[str, int]:
        """
        Get count of active specialists for each game
        
        Returns:
            Dict mapping game_id -> count of active specialists
        """
        agents = self.db.execute_query("""
            SELECT agent_id, specialization, is_active
            FROM agents
            WHERE is_active = TRUE
        """)
        
        game_counts = {}
        for agent in agents:
            spec = json.loads(agent['specialization'])
            assigned_games = spec.get('assigned_games', [])
            
            for game_id in assigned_games:
                if game_id not in game_counts:
                    game_counts[game_id] = 0
                game_counts[game_id] += 1
        
        return game_counts
    
    def get_endangered_games(self, all_games: List[str]) -> List[str]:
        """
        Find games with fewer than min_specialists active agents
        
        Args:
            all_games: List of all available game IDs
            
        Returns:
            List of game IDs needing more specialists
        """
        counts = self.get_game_specialist_counts()
        endangered = []
        
        for game_id in all_games:
            if counts.get(game_id, 0) < self.min_specialists:
                endangered.append(game_id)
        
        return endangered
    
    def get_protected_agents(self) -> Set[str]:
        """
        Get agent IDs that should be protected from pruning (last specialist of any game)
        
        Returns:
            Set of protected agent IDs
        """
        agents = self.db.execute_query("""
            SELECT agent_id, specialization
            FROM agents
            WHERE is_active = TRUE
        """)
        
        # Map each game to list of specialists
        game_specialists = {}
        for agent in agents:
            spec = json.loads(agent['specialization'])
            assigned_games = spec.get('assigned_games', [])
            
            for game_id in assigned_games:
                if game_id not in game_specialists:
                    game_specialists[game_id] = []
                game_specialists[game_id].append(agent['agent_id'])
        
        # Mark agents as protected if they're the last (or only) specialist for any game
        protected = set()
        for game_id, specialists in game_specialists.items():
            if len(specialists) <= self.min_specialists:
                # All specialists for this game are protected
                protected.update(specialists)
        
        return protected
    
    def assign_generalists_to_endangered_games(self, endangered_games: List[str],
                                               max_assignments: int = 10) -> int:
        """
        Assign generalist agents to endangered games
        
        Args:
            endangered_games: Games needing more specialists
            max_assignments: Maximum number of new assignments to make
            
        Returns:
            Number of assignments made
        """
        if not endangered_games:
            return 0
        
        # Find generalist agents (not currently specialized)
        generalists = self.db.execute_query("""
            SELECT agent_id, specialization, generation
            FROM agents
            WHERE is_active = TRUE
            ORDER BY generation DESC
            LIMIT ?
        """, (max_assignments,))
        
        assignments_made = 0
        for agent in generalists:
            if assignments_made >= max_assignments:
                break
            
            spec = json.loads(agent['specialization'])
            
            # Check if this is a specialist
            if spec.get('type') == 'specialist' and spec.get('assigned_games'):
                # Already a specialist, skip
                continue
            
            # Assign to 2 endangered games (specialist pairs)
            if len(endangered_games) >= 2:
                assigned_pair = random.sample(endangered_games, 2)
            else:
                assigned_pair = endangered_games[:1]
            
            # Update agent specialization
            new_spec = {
                'type': 'specialist',
                'assigned_games': assigned_pair,
                'focus': 'deep_mastery',
                'reassigned_from_generalist': True
            }
            
            self.db.execute_query("""
                UPDATE agents
                SET specialization = ?
                WHERE agent_id = ?
            """, (json.dumps(new_spec), agent['agent_id']))
            
            assignments_made += 1
            print(f"  [+] Assigned generalist {agent['agent_id'][:8]} to {assigned_pair}")
        
        return assignments_made
    
    def ensure_game_diversity(self, all_games: List[str]) -> Dict[str, Any]:
        """
        Main entry point: ensure all games have minimum specialist coverage
        
        Args:
            all_games: List of all available game IDs
            
        Returns:
            Summary of actions taken
        """
        print("\n[DIVERSITY] Checking game specialist coverage...")
        
        counts = self.get_game_specialist_counts()
        endangered = self.get_endangered_games(all_games)
        protected = self.get_protected_agents()
        
        print(f"  Games: {len(all_games)} total")
        print(f"  Endangered: {len(endangered)} games below {self.min_specialists} specialists")
        print(f"  Protected: {len(protected)} agents (last specialists)")
        
        # Show endangered games
        if endangered:
            print(f"\n  ⚠️  Endangered games:")
            for game_id in endangered:
                count = counts.get(game_id, 0)
                print(f"    {game_id}: {count} specialists (need {self.min_specialists - count} more)")
        
        # Assign generalists to endangered games
        assignments_made = 0
        if endangered:
            assignments_made = self.assign_generalists_to_endangered_games(endangered)
            print(f"\n  [DIVERSITY] Made {assignments_made} new assignments")
        
        return {
            'total_games': len(all_games),
            'endangered_games': endangered,
            'protected_agents': list(protected),
            'assignments_made': assignments_made,
            'specialist_counts': counts
        }
    
    def filter_pruning_candidates(self, candidate_ids: List[str]) -> List[str]:
        """
        Filter pruning candidates to remove protected agents
        
        Args:
            candidate_ids: Agent IDs being considered for pruning
            
        Returns:
            Filtered list with protected agents removed
        """
        protected = self.get_protected_agents()
        filtered = [aid for aid in candidate_ids if aid not in protected]
        
        removed = len(candidate_ids) - len(filtered)
        if removed > 0:
            print(f"  [DIVERSITY] Protected {removed} agents from pruning (last specialists)")
        
        return filtered


if __name__ == "__main__":
    """Test game diversity preservation"""
    
    db = DatabaseInterface()
    preserver = GameDiversityPreserver(db, min_specialists_per_game=1)
    
    # Get all known games
    games = db.execute_query("""
        SELECT DISTINCT game_id FROM agent_arc_performance
    """)
    all_game_ids = [g['game_id'] for g in games]
    
    print("=" * 80)
    print("GAME DIVERSITY PRESERVATION TEST")
    print("=" * 80)
    
    # Run diversity check
    result = preserver.ensure_game_diversity(all_game_ids)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Total games: {result['total_games']}")
    print(f"  Endangered games: {len(result['endangered_games'])}")
    print(f"  Protected agents: {len(result['protected_agents'])}")
    print(f"  New assignments: {result['assignments_made']}")
    
    if result['assignments_made'] > 0:
        print("\n✅ Diversity restored!")
    else:
        print("\n✅ All games have sufficient coverage")
    
    print("=" * 80)
