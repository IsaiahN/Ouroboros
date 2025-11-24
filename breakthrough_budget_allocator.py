#!/usr/bin/env python3
"""
Breakthrough Budget Allocator
==============================

Dynamic per-game action allocation based on breakthrough potential.
Tier 1 Improvement #1: +50% expected gain

Games with 0 level wins → HIGH budget (discovery phase)
Games with 1-2 level wins → MEDIUM budget (expansion phase)  
Games with 3+ level wins → LOW budget (exploitation phase)
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from typing import Optional
from database_interface import DatabaseInterface
import logging

logger = logging.getLogger(__name__)


class BreakthroughBudgetAllocator:
    """Allocate action budgets based on game breakthrough potential."""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        
        # Budget levels by discovery phase
        self.DISCOVERY_BUDGET = 800    # High: unbeaten games need exploration
        self.EXPANSION_BUDGET = 400    # Medium: partial wins, expand knowledge
        self.EXPLOITATION_BUDGET = 150 # Low: beaten games, just optimize
        
        # Per-level budgets (total budget / expected levels)
        self.DISCOVERY_PER_LEVEL = 300
        self.EXPANSION_PER_LEVEL = 200
        self.EXPLOITATION_PER_LEVEL = 100
        
    def calculate_game_budget(self, game_id: str, agent_id: Optional[str] = None) -> dict:
        """
        Calculate optimal action budget for a specific game.
        
        Args:
            game_id: Game to allocate budget for
            agent_id: Optional agent ID for personalization
            
        Returns:
            Dictionary with action_allowance_per_level, action_allowance_total, phase
        """
        # Get network-wide level completion stats for this game
        level_wins = self.get_network_level_wins(game_id)
        
        # Determine phase based on progress
        if level_wins == 0:
            phase = 'DISCOVERY'
            per_level = self.DISCOVERY_PER_LEVEL
            total = self.DISCOVERY_BUDGET
            reason = "Unbeaten game - maximum exploration budget"
        elif level_wins < 3:
            phase = 'EXPANSION'
            per_level = self.EXPANSION_PER_LEVEL
            total = self.EXPANSION_BUDGET
            reason = f"Partial progress ({level_wins} levels) - medium budget"
        else:
            phase = 'EXPLOITATION'
            per_level = self.EXPLOITATION_PER_LEVEL
            total = self.EXPLOITATION_BUDGET
            reason = f"Beaten game ({level_wins}+ levels) - optimization budget"
        
        logger.info(f"🎯 Budget for {game_id}: {total} total, {per_level}/level ({phase})")
        logger.debug(f"   Reason: {reason}")
        
        return {
            'action_allowance_per_level': per_level,
            'action_allowance_total': total,
            'phase': phase,
            'reason': reason,
            'network_level_wins': level_wins
        }
    
    def get_network_level_wins(self, game_id: str) -> int:
        """
        Get total unique level wins across ALL agents for this game.
        
        Returns:
            Count of unique levels that have been completed by anyone
        """
        try:
            result = self.db.execute_query("""
                SELECT COUNT(DISTINCT level_number) as level_wins
                FROM winning_sequences
                WHERE game_id = ?
            """, (game_id,))
            
            if result and result[0]:
                return result[0]['level_wins']
            else:
                return 0
                
        except Exception as e:
            logger.warning(f"Error checking network level wins for {game_id}: {e}")
            return 0
    
    def get_batch_budgets(self, game_ids: list) -> dict:
        """
        Calculate budgets for multiple games efficiently.
        
        Args:
            game_ids: List of game IDs
            
        Returns:
            Dictionary mapping game_id -> budget dict
        """
        budgets = {}
        for game_id in game_ids:
            budgets[game_id] = self.calculate_game_budget(game_id)
        
        return budgets
    
    def log_budget_distribution(self, game_ids: list):
        """Log budget allocation summary for a batch of games."""
        budgets = self.get_batch_budgets(game_ids)
        
        discovery_count = sum(1 for b in budgets.values() if b['phase'] == 'DISCOVERY')
        expansion_count = sum(1 for b in budgets.values() if b['phase'] == 'EXPANSION')
        exploitation_count = sum(1 for b in budgets.values() if b['phase'] == 'EXPLOITATION')
        
        total_budget = sum(b['action_allowance_total'] for b in budgets.values())
        avg_budget = total_budget / len(budgets) if budgets else 0
        
        logger.info(f"\n📊 BUDGET ALLOCATION SUMMARY:")
        logger.info(f"   Total Games: {len(game_ids)}")
        logger.info(f"   DISCOVERY ({discovery_count}): {discovery_count/len(game_ids)*100:.1f}% @ {self.DISCOVERY_BUDGET} actions")
        logger.info(f"   EXPANSION ({expansion_count}): {expansion_count/len(game_ids)*100:.1f}% @ {self.EXPANSION_BUDGET} actions")
        logger.info(f"   EXPLOITATION ({exploitation_count}): {exploitation_count/len(game_ids)*100:.1f}% @ {self.EXPLOITATION_BUDGET} actions")
        logger.info(f"   Average Budget: {avg_budget:.0f} actions/game")
        logger.info(f"   Total Budget Pool: {total_budget:,} actions\n")


if __name__ == "__main__":
    # Quick test
    db = DatabaseInterface()
    allocator = BreakthroughBudgetAllocator(db)
    
    # Test on a few games
    test_games = db.execute_query("""
        SELECT DISTINCT game_id 
        FROM game_results 
        LIMIT 10
    """)
    
    if test_games:
        game_ids = [g['game_id'] for g in test_games]
        allocator.log_budget_distribution(game_ids)
        
        print("\n✅ Breakthrough Budget Allocator test complete")
    else:
        print("⚠️  No games found in database")
