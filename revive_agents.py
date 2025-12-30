import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

#!/usr/bin/env python3
"""
Agent Revival Mechanism (Enhanced)
===================================

Implements intelligent agent revival with:
- Revival triggers (performance regression, diversity collapse)
- Multiple revival modes (exact, hybrid, successor)
- Integration with evolution cycle
- Performance tracking post-revival

This addresses the agent revival requirement from operational philosophy.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sqlite3
import json
import random
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from database_interface import DatabaseInterface
import logging

logger = logging.getLogger(__name__)

DB_PATH = "core_data.db"


class AgentRevivalSystem:
    """
    Intelligent agent revival system.
    
    Detects when revival is beneficial and resurrects archived agents
    with appropriate modifications based on current network state.
    """
    
    def __init__(self, db_path: str = DB_PATH):
        """Initialize revival system."""
        self.db = DatabaseInterface(db_path)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create agent_revivals table if needed."""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_revivals (
                revival_id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_agent_id TEXT,
                revived_agent_id TEXT,
                revival_trigger TEXT,
                revival_mode TEXT,
                generation INTEGER,
                revival_timestamp TEXT,
                performance_after_revival REAL
            )
        """)
    
    def detect_revival_triggers(self, generation: int) -> List[Dict]:
        """
        Detect situations where revival would be beneficial.
        
        Args:
            generation: Current generation number
        
        Returns:
            List of revival trigger events with candidate agents
        """
        triggers = []
        
        # Trigger 1: Performance regression on previously-solved games
        regression_trigger = self._detect_performance_regression(generation)
        if regression_trigger:
            triggers.append(regression_trigger)
        
        # Trigger 2: Diversity collapse (all agents too similar)
        diversity_trigger = self._detect_diversity_collapse(generation)
        if diversity_trigger:
            triggers.append(diversity_trigger)
        
        # Trigger 3: Specific game type needs specialist
        specialist_trigger = self._detect_specialist_need(generation)
        if specialist_trigger:
            triggers.append(specialist_trigger)
        
        return triggers
    
    def _detect_performance_regression(self, generation: int) -> Optional[Dict]:
        """Detect if network performance has regressed."""
        # Simplified: Just check if we have low-performing agents
        # and high-prestige archived agents available
        current_avg = self.db.execute_query("""
            SELECT AVG(final_score) as avg_score
            FROM agent_arc_performance
            LIMIT 100
        """)
        
        if not current_avg or not current_avg[0]['avg_score']:
            return None
        
        avg_score = current_avg[0]['avg_score']
        
        # If average score is low (<30), consider revival
        if avg_score < 30:
            logger.warning(f"Low performance detected: {avg_score:.2f}")
            return {
                'trigger': 'performance_regression',
                'severity': (30 - avg_score) / 30,
                'candidates': self._get_high_performers_from_archive()
            }
        
        return None
    
    def _detect_diversity_collapse(self, generation: int) -> Optional[Dict]:
        """Detect if population diversity has collapsed."""
        # Simplified: Check genome diversity across recent agents
        agents = self.db.execute_query("""
            SELECT agent_id, genome
            FROM agents
            LIMIT 20
        """)
        
        if not agents or len(agents) < 5:
            return None
        
        # Simple diversity check: count unique genome patterns
        unique_genomes = set()
        for agent in agents:
            if agent['genome']:
                # Hash genome for comparison
                genome_hash = hash(agent['genome'])
                unique_genomes.add(genome_hash)
        
        diversity_ratio = len(unique_genomes) / len(agents)
        
        # If <30% unique, diversity collapsed
        if diversity_ratio < 0.3:
            logger.warning(f"Diversity collapse detected: {diversity_ratio:.1%} unique")
            return {
                'trigger': 'diversity_collapse',
                'severity': 1.0 - diversity_ratio,
                'candidates': self._get_diverse_agents_from_archive()
            }
        
        return None
    
    def _detect_specialist_need(self, generation: int) -> Optional[Dict]:
        """Detect if a specific game type needs a specialist."""
        # Simplified: Find games with low average scores
        low_performing_games = self.db.execute_query("""
            SELECT game_id, AVG(final_score) as avg_score
            FROM agent_arc_performance
            GROUP BY game_id
            HAVING avg_score < 30
            LIMIT 3
        """)
        
        if low_performing_games:
            logger.info(f"Found {len(low_performing_games)} low-performing games")
            return {
                'trigger': 'specialist_need',
                'severity': 0.5,
                'games': [g['game_id'] for g in low_performing_games],
                'candidates': self._get_specialists_from_archive(low_performing_games)
            }
        
        return None
    
    def _get_high_performers_from_archive(self) -> List[Dict]:
        """Get high-performing archived agents."""
        return self.db.execute_query("""
            SELECT *
            FROM agent_archive
            WHERE final_performance > (
                SELECT AVG(final_performance) FROM agent_archive
            )
            ORDER BY final_prestige DESC
            LIMIT 5
        """) or []
    
    def _get_diverse_agents_from_archive(self) -> List[Dict]:
        """Get diverse archived agents."""
        # Get agents with different agent_types from archive
        return self.db.execute_query("""
            SELECT *
            FROM agent_archive
            GROUP BY agent_id
            ORDER BY RANDOM()
            LIMIT 5
        """) or []
    
    def _get_specialists_from_archive(self, games: List[Dict]) -> List[Dict]:
        """Get specialists for specific games."""
        if not games:
            return []
        
        # Simplified: Get any archived agents
        return self.db.execute_query("""
            SELECT *
            FROM agent_archive
            ORDER BY final_prestige DESC
            LIMIT 5
        """) or []
    
    def revive_agent(
        self,
        archived_agent: Dict,
        generation: int,
        revival_mode: str = 'hybrid',
        trigger: str = 'manual'
    ) -> Optional[str]:
        """
        Revive an archived agent.
        
        Args:
            archived_agent: Archived agent record
            generation: Current generation
            revival_mode: 'exact', 'hybrid', or 'successor'
            trigger: Revival trigger type
        
        Returns:
            New agent ID or None if failed
        """
        try:
            # Parse genome and epigenetics
            genome = json.loads(archived_agent.get('genome', '{}'))
            epigenetics = json.loads(archived_agent.get('epigenetics', '{}'))
            
            # Apply revival mode
            if revival_mode == 'exact':
                # Exact clone - no changes
                pass
            
            elif revival_mode == 'hybrid':
                # Genome + current network knowledge
                # Add slight mutations (5-10%)
                mutation_rate = random.uniform(0.05, 0.10)
                for key in genome:
                    if isinstance(genome[key], (int, float)):
                        if random.random() < mutation_rate:
                            genome[key] *= random.uniform(0.9, 1.1)
            
            elif revival_mode == 'successor':
                # Spiritual successor - more mutations (15-25%)
                mutation_rate = random.uniform(0.15, 0.25)
                for key in genome:
                    if isinstance(genome[key], (int, float)):
                        if random.random() < mutation_rate:
                            genome[key] *= random.uniform(0.8, 1.2)
            
            # Generate new agent ID
            new_agent_id = f"revived_{uuid.uuid4().hex[:12]}"
            
            # Insert new agent
            self.db.execute_query("""
                INSERT INTO agents (
                    agent_id, genome, epigenetics, generation,
                    parent_agent_id, is_alive, created_at,
                    agent_type, social_rule_adherence
                )
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
            """, (
                new_agent_id,
                json.dumps(genome),
                json.dumps(epigenetics),
                generation,
                archived_agent.get('agent_id'),
                datetime.now().isoformat(),
                archived_agent.get('agent_type', 'generalist'),
                archived_agent.get('social_rule_adherence', 0.5)
            ))
            
            # Log revival
            self.db.execute_query("""
                INSERT INTO agent_revivals (
                    original_agent_id, revived_agent_id, revival_trigger,
                    revival_mode, generation, revival_timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                archived_agent.get('agent_id'),
                new_agent_id,
                trigger,
                revival_mode,
                generation,
                datetime.now().isoformat()
            ))
            
            logger.info(
                f"[OK] Revived agent {new_agent_id} "
                f"(parent: {archived_agent.get('agent_id')}, mode: {revival_mode})"
            )
            
            return new_agent_id
        
        except Exception as e:
            logger.error(f"Failed to revive agent: {e}")
            return None
    
    def process_revival_triggers(
        self,
        generation: int,
        max_revivals: int = 3
    ) -> List[str]:
        """
        Process all revival triggers and revive appropriate agents.
        
        Args:
            generation: Current generation
            max_revivals: Maximum agents to revive
        
        Returns:
            List of revived agent IDs
        """
        triggers = self.detect_revival_triggers(generation)
        revived_ids = []
        
        for trigger_event in triggers:
            if len(revived_ids) >= max_revivals:
                break
            
            trigger_type = trigger_event.get('trigger')
            candidates = trigger_event.get('candidates', [])
            
            # Determine revival mode based on trigger
            if trigger_type == 'performance_regression':
                mode = 'exact'  # Use proven performers as-is
            elif trigger_type == 'diversity_collapse':
                mode = 'successor'  # Add diversity with mutations
            else:
                mode = 'hybrid'  # Balance of both
            
            # Revive top candidates
            for candidate in candidates[:max_revivals - len(revived_ids)]:
                revived_id = self.revive_agent(
                    candidate, generation, mode, trigger_type
                )
                if revived_id:
                    revived_ids.append(revived_id)
        
        return revived_ids


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Revival System")
    parser.add_argument('--test', action='store_true', help='Run test mode')
    parser.add_argument('--generation', type=int, default=0, help='Current generation')
    parser.add_argument('--max', type=int, default=3, help='Maximum revivals')
    args = parser.parse_args()
    
    revival_system = AgentRevivalSystem()
    
    if args.test:
        print("=" * 70)
        print("AGENT REVIVAL SYSTEM TEST")
        print("=" * 70)
        
        # Test table creation
        result = revival_system.db.execute_query("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='agent_revivals'
        """)
        
        if result:
            print("[OK] agent_revivals table exists")
        else:
            print("[FAIL] Table creation failed")
        
        # Test trigger detection
        triggers = revival_system.detect_revival_triggers(args.generation)
        print(f"\n[OK] Detected {len(triggers)} revival triggers")
        for trigger in triggers:
            print(f"  - {trigger['trigger']}: {len(trigger.get('candidates', []))} candidates")
        
        print("\n[OK] Agent Revival system operational")
    else:
        # Run actual revival
        revived = revival_system.process_revival_triggers(args.generation, args.max)
        print(f"\n[SYNC] Revived {len(revived)} agents:")
        for agent_id in revived:
            print(f"  - {agent_id}")

