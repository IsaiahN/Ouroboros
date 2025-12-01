"""
Safe Agent Lifecycle Management

Implements "Megaman Net Navi" philosophy:
- Good players never deleted, just retired
- Zero-score agents pruned faster
- Permanent deletion only after 500+ generations of inactivity
- Agent data preserved for historical analysis

Author: Claude Code (Ouroboros System)
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentLifecycleManager:
    """
    Manage agent lifecycle from birth → retirement → eventual deletion.
    
    Philosophy: Net Navis should live their lives. Don't delete good players.
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        
        # Lifecycle thresholds
        self.permanent_deletion_generations = 500  # Only delete after 500+ generations inactive
        self.zero_score_deletion_generations = 50  # Zero-score agents deleted faster
        self.good_player_threshold = 1.0  # Score >= 1.0 = completed at least one level
        
    def retire_underperformers(self, generation: int, culling_config: Dict[str, Any]) -> Dict[str, int]:
        """
        Retire (deactivate) underperforming agents without deleting them.
        
        This is the normal evolutionary pressure mechanism.
        Agents stay in database for analysis/revival.
        
        Args:
            generation: Current generation
            culling_config: Configuration for culling (kept for compatibility)
            
        Returns:
            Dict with retirement stats
        """
        # This function is now a wrapper - actual retirement happens in evolutionary_engine
        # and autonomous_evolution_runner. This just tracks stats.
        
        with self.db._get_connection() as conn:
            # Count recently retired agents
            cursor = conn.execute("""
                SELECT COUNT(*) 
                FROM agents 
                WHERE generation = ? AND is_active = 0
            """, (generation,))
            
            retired_count = cursor.fetchone()[0]
            
            return {
                'retired': retired_count,
                'generation': generation,
                'permanent_deletions': 0  # Not done here
            }
    
    def cleanup_ancient_inactive_agents(self, current_generation: int, dry_run: bool = False) -> Dict[str, Any]:
        """
        Permanently delete ancient inactive agents.
        
        Deletion rules (safest possible):
        1. Zero-score agents: Deleted after 50 generations inactive
        2. Low-score agents (< 1.0): Deleted after 200 generations inactive  
        3. Good players (>= 1.0): Deleted after 500 generations inactive
        4. High prestige agents: NEVER deleted (archived permanently)
        
        Args:
            current_generation: Current generation number
            dry_run: If True, only report what would be deleted
            
        Returns:
            Deletion statistics
        """
        logger.info(f"🗑️  Agent cleanup: Generation {current_generation}")
        
        stats = {
            'zero_score_deleted': 0,
            'low_score_deleted': 0,
            'good_player_deleted': 0,
            'high_prestige_archived': 0,
            'total_deleted': 0
        }
        
        with self.db._get_connection() as conn:
            # 1. Find ancient zero-score agents (never contributed)
            zero_score_threshold = current_generation - self.zero_score_deletion_generations
            
            cursor = conn.execute("""
                SELECT agent_id, generation, best_single_game_score, discovery_prestige
                FROM agents
                WHERE is_active = 0
                    AND generation <= ?
                    AND COALESCE(best_single_game_score, 0) = 0
                    AND COALESCE(total_games_won, 0) = 0
                    AND COALESCE(discovery_prestige, 0) < 10  -- Low prestige
            """, (zero_score_threshold,))
            
            zero_score_agents = cursor.fetchall()
            
            if not dry_run and zero_score_agents:
                for agent_id, gen, score, prestige in zero_score_agents:
                    conn.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
                    logger.debug(f"  Deleted zero-score agent: {agent_id} (Gen {gen})")
                conn.commit()
            
            stats['zero_score_deleted'] = len(zero_score_agents)
            
            # 2. Find ancient low-score agents (minimal contribution)
            low_score_threshold = current_generation - 200  # More lenient
            
            cursor = conn.execute("""
                SELECT agent_id, generation, best_single_game_score, discovery_prestige
                FROM agents
                WHERE is_active = 0
                    AND generation <= ?
                    AND COALESCE(best_single_game_score, 0) > 0
                    AND COALESCE(best_single_game_score, 0) < 1.0
                    AND COALESCE(discovery_prestige, 0) < 50  -- Medium prestige
            """, (low_score_threshold,))
            
            low_score_agents = cursor.fetchall()
            
            if not dry_run and low_score_agents:
                for agent_id, gen, score, prestige in low_score_agents:
                    conn.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
                    logger.debug(f"  Deleted low-score agent: {agent_id} (Gen {gen}, Score: {score:.2f})")
                conn.commit()
            
            stats['low_score_deleted'] = len(low_score_agents)
            
            # 3. Find ancient good players (respectful deletion)
            good_player_threshold = current_generation - self.permanent_deletion_generations
            
            cursor = conn.execute("""
                SELECT agent_id, generation, best_single_game_score, discovery_prestige
                FROM agents
                WHERE is_active = 0
                    AND generation <= ?
                    AND COALESCE(best_single_game_score, 0) >= 1.0
                    AND COALESCE(discovery_prestige, 0) < 100  -- Not elite
            """, (good_player_threshold,))
            
            good_player_agents = cursor.fetchall()
            
            if not dry_run and good_player_agents:
                for agent_id, gen, score, prestige in good_player_agents:
                    conn.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
                    logger.debug(f"  Deleted good player (ancient): {agent_id} (Gen {gen}, Score: {score:.2f})")
                conn.commit()
            
            stats['good_player_deleted'] = len(good_player_agents)
            
            # 4. Archive high-prestige agents (never delete)
            cursor = conn.execute("""
                SELECT COUNT(*)
                FROM agents
                WHERE is_active = 0
                    AND COALESCE(discovery_prestige, 0) >= 100
            """)
            
            stats['high_prestige_archived'] = cursor.fetchone()[0]
            
            stats['total_deleted'] = (
                stats['zero_score_deleted'] + 
                stats['low_score_deleted'] + 
                stats['good_player_deleted']
            )
        
        # Logging
        if dry_run:
            logger.info(f"  [DRY RUN] Would delete {stats['total_deleted']} agents:")
        else:
            logger.info(f"  Deleted {stats['total_deleted']} ancient agents:")
        
        logger.info(f"    Zero-score (50+ gen old): {stats['zero_score_deleted']}")
        logger.info(f"    Low-score (200+ gen old): {stats['low_score_deleted']}")
        logger.info(f"    Good players (500+ gen old): {stats['good_player_deleted']}")
        logger.info(f"    High prestige archived: {stats['high_prestige_archived']} (NEVER deleted)")
        
        return stats
    
    def get_lifecycle_stats(self) -> Dict[str, Any]:
        """Get current agent lifecycle statistics."""
        
        with self.db._get_connection() as conn:
            # Active agents
            cursor = conn.execute("SELECT COUNT(*) FROM agents WHERE is_active = 1")
            active_count = cursor.fetchone()[0]
            
            # Retired agents (inactive but not deleted)
            cursor = conn.execute("SELECT COUNT(*) FROM agents WHERE is_active = 0")
            retired_count = cursor.fetchone()[0]
            
            # Retired by score category
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE COALESCE(best_single_game_score, 0) = 0) as zero_score,
                    COUNT(*) FILTER (WHERE COALESCE(best_single_game_score, 0) > 0 AND COALESCE(best_single_game_score, 0) < 1.0) as low_score,
                    COUNT(*) FILTER (WHERE COALESCE(best_single_game_score, 0) >= 1.0) as good_players,
                    COUNT(*) FILTER (WHERE COALESCE(discovery_prestige, 0) >= 100) as high_prestige
                FROM agents
                WHERE is_active = 0
            """)
            
            result = cursor.fetchone()
            
            return {
                'active_agents': active_count,
                'retired_agents': retired_count,
                'retired_breakdown': {
                    'zero_score': result[0],
                    'low_score': result[1],
                    'good_players': result[2],
                    'high_prestige': result[3]
                },
                'total_agents': active_count + retired_count
            }


if __name__ == "__main__":
    """Test lifecycle management"""
    
    db = DatabaseInterface()
    manager = AgentLifecycleManager(db)
    
    # Get current stats
    stats = manager.get_lifecycle_stats()
    
    print("=" * 80)
    print("AGENT LIFECYCLE STATS")
    print("=" * 80)
    print(f"Active agents: {stats['active_agents']:,}")
    print(f"Retired agents: {stats['retired_agents']:,}")
    print(f"Total agents: {stats['total_agents']:,}")
    print()
    print("Retired breakdown:")
    print(f"  Zero-score: {stats['retired_breakdown']['zero_score']:,}")
    print(f"  Low-score: {stats['retired_breakdown']['low_score']:,}")
    print(f"  Good players: {stats['retired_breakdown']['good_players']:,}")
    print(f"  High prestige (archived): {stats['retired_breakdown']['high_prestige']:,}")
    print()
    
    # Check what would be deleted
    cursor = db.execute_query("SELECT MAX(generation) FROM agents")
    current_gen = cursor[0]['MAX(generation)'] if cursor else 0
    
    print(f"Current generation: {current_gen}")
    print()
    print("Checking cleanup eligibility (DRY RUN)...")
    cleanup_stats = manager.cleanup_ancient_inactive_agents(current_gen, dry_run=True)
    print("=" * 80)
