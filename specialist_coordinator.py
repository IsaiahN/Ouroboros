#!/usr/bin/env python3
"""
Specialist Coordinator - Matches games to specialist agents
===========================================================

Lightweight coordinator that:
1. Assigns specific games to specialist agents for deep mastery
2. Matches new games to best specialist based on game features
3. Tracks specialist performance on assigned games

Following Rule 2: All data in database
Following Rule 3: Enhances existing code, doesn't replace
Following Rule 10: No code drift - clean integration
"""

import os
import json
import random
from typing import Dict, List, Any, Optional, Tuple
from database_interface import DatabaseInterface

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


class SpecialistCoordinator:
    """
    Coordinates specialist agents and game assignments
    Simpler alternative to meta-learning for focused puzzle-solving
    """
    
    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        self.agent_assignments = {}  # Cache: agent_id -> [game_ids]
        self.game_assignments = {}   # Cache: game_id -> agent_id
        
    def initialize_specialist_assignments(self, population: List[Dict[str, Any]], 
                                         available_games: List[str],
                                         games_per_specialist: int = 2):
        """
        Assign specific games to each specialist agent
        
        Args:
            population: List of agent dictionaries
            available_games: List of available game IDs
            games_per_specialist: How many games to assign per agent
        """
        # Distribute games evenly across population
        num_agents = len(population)
        if num_agents == 0:
            return
        
        # Shuffle games for random distribution
        shuffled_games = available_games.copy()
        random.shuffle(shuffled_games)
        
        for idx, agent in enumerate(population):
            agent_id = agent['agent_id']
            
            # Assign games_per_specialist games to this agent
            start_idx = (idx * games_per_specialist) % len(shuffled_games)
            assigned = []
            
            for i in range(games_per_specialist):
                game_idx = (start_idx + i) % len(shuffled_games)
                game_id = shuffled_games[game_idx]
                assigned.append(game_id)
                
                # Track reverse mapping
                self.game_assignments[game_id] = agent_id
            
            # Store assignment
            self.agent_assignments[agent_id] = assigned
            
            # Update agent's specialization field in database
            spec_data = {
                'type': 'specialist',
                'assigned_games': assigned,
                'focus': 'deep_mastery'
            }
            
            try:
                self.db.execute_query("""
                    UPDATE agents
                    SET specialization = ?
                    WHERE agent_id = ?
                """, (json.dumps(spec_data), agent_id))
            except Exception as e:
                print(f"Warning: Could not update agent {agent_id} specialization: {e}")
        
        print(f"✓ Assigned {games_per_specialist} games to each of {num_agents} specialists")
        print(f"  Covering {len(set(self.game_assignments.keys()))} unique games")
    
    def get_specialist_for_game(self, game_id: str) -> Optional[str]:
        """
        Get the specialist agent assigned to this game
        
        Args:
            game_id: Game ID
            
        Returns:
            Agent ID of specialist, or None if no assignment
        """
        return self.game_assignments.get(game_id)
    
    def get_games_for_specialist(self, agent_id: str) -> List[str]:
        """
        Get the games assigned to this specialist
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of game IDs assigned to this specialist
        """
        # Check cache first
        if agent_id in self.agent_assignments:
            return self.agent_assignments[agent_id]
        
        # Query database
        try:
            result = self.db.execute_query("""
                SELECT specialization FROM agents WHERE agent_id = ?
            """, (agent_id,))
            
            if result and result[0]['specialization']:
                spec = result[0]['specialization']
                if isinstance(spec, str):
                    spec_data = json.loads(spec) if spec.startswith('{') else {}
                else:
                    spec_data = spec
                
                assigned = spec_data.get('assigned_games', [])
                self.agent_assignments[agent_id] = assigned
                return assigned
        except:
            pass
        
        return []
    
    def select_games_for_agent(self, agent_id: str, available_games: List[str],
                               num_games: int = 5) -> List[str]:
        """
        Select games for specialist agent (returns only assigned games)
        
        Args:
            agent_id: Agent ID
            available_games: Available game IDs
            num_games: Number of games to select
            
        Returns:
            List of game IDs (specialist's assigned games only)
        """
        assigned_games = self.get_games_for_specialist(agent_id)
        
        if not assigned_games:
            # No assignment yet - return random games
            return random.sample(available_games, min(num_games, len(available_games)))
        
        # Return only assigned games (allow repetition for mastery)
        # Repeat the assigned games list to reach num_games
        selected = []
        while len(selected) < num_games and assigned_games:
            selected.extend(assigned_games)
        
        return selected[:num_games]
    
    def get_specialist_performance_summary(self) -> Dict[str, Any]:
        """
        Get summary of all specialists and their performance
        
        Returns:
            Dictionary with specialist performance data
        """
        summaries = []
        
        for agent_id, assigned_games in self.agent_assignments.items():
            try:
                # Get performance on assigned games
                placeholders = ','.join(['?' for _ in assigned_games])
                query = f"""
                    SELECT 
                        COUNT(*) as games_played,
                        SUM(CASE WHEN win_achieved THEN 1 ELSE 0 END) as wins,
                        AVG(final_score) as avg_score,
                        MAX(final_score) as best_score
                    FROM agent_arc_performance
                    WHERE agent_id = ? AND game_id IN ({placeholders})
                """
                
                result = self.db.execute_query(query, (agent_id, *assigned_games))
                
                if result:
                    perf = result[0]
                    win_rate = (perf['wins'] / perf['games_played']) if perf['games_played'] > 0 else 0.0
                    
                    summaries.append({
                        'agent_id': agent_id,
                        'assigned_games': assigned_games,
                        'games_played': perf['games_played'],
                        'wins': perf['wins'],
                        'win_rate': win_rate,
                        'avg_score': perf['avg_score'],
                        'best_score': perf['best_score']
                    })
            except Exception as e:
                print(f"Warning: Could not get performance for {agent_id}: {e}")
        
        # Sort by win rate
        summaries.sort(key=lambda x: x['win_rate'], reverse=True)
        
        return {
            'total_specialists': len(summaries),
            'specialists': summaries,
            'top_performers': summaries[:5]
        }
    
    def print_specialist_status(self):
        """Print current specialist assignments and performance"""
        summary = self.get_specialist_performance_summary()
        
        print(f"\n[STATS] Specialist System Status:")
        print(f"   Total Specialists: {summary['total_specialists']}")
        
        if summary['top_performers']:
            print(f"\n[TROPHY] Top Performing Specialists:")
            for i, spec in enumerate(summary['top_performers'], 1):
                print(f"   {i}. Agent {spec['agent_id'][:8]}...")
                print(f"      Games: {spec['assigned_games']}")
                print(f"      Win Rate: {spec['win_rate']:.1%} ({spec['wins']}/{spec['games_played']})")
                print(f"      Best Score: {spec['best_score']:.1f}")


# [CHECKPOINT: SPECIALIST COORDINATOR COMPLETE]
# Next: Integrate into autonomous_evolution_runner.py
