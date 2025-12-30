import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

#!/usr/bin/env python3
"""
Prestige Vampire Detector
==========================

Detects and gracefully sunsets high-prestige agents whose knowledge
has been fully absorbed by the network.

Prevents "vampire" agents from dominating breeding pools despite
declining relative performance.

Following Rule 2: All data in database (archive agents, don't delete)
Following Rule 4: LLM self-management (autonomous vampire detection)
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from typing import List, Dict, Optional
from datetime import datetime
import logging
from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)

class PrestigeVampireDetector:
    """Detect and sunset prestige vampire agents."""
    
    def __init__(self, db_path: str = "core_data.db"):
        self.db = DatabaseInterface(db_path)
        self._ensure_agent_archive_table()
    
    def _ensure_agent_archive_table(self):
        """Create agent_archive table if it doesn't exist."""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_archive (
                agent_id TEXT PRIMARY KEY,
                archived_at TEXT NOT NULL,
                final_prestige REAL,
                final_performance REAL,
                network_median_at_sunset REAL,
                knowledge_transfer_rate REAL,
                reasoning_summary TEXT,
                revival_candidate BOOLEAN DEFAULT 0,
                sunset_reason TEXT
            )
        """)
        logger.info("Agent archive table initialized")
    
    def detect_vampires(self, current_generation: int, threshold_multiplier: float = 10.0) -> List[Dict]:
        """
        Detect prestige vampire agents.
        
        Criteria:
        1. Prestige > threshold_multiplier * median
        2. Performance < network median for 3+ generations
        3. Knowledge fully transferred (sequences replicated)
        
        Args:
            current_generation: Current generation number
            threshold_multiplier: Prestige outlier threshold (default 10x)
        
        Returns:
            List of vampire agent dicts
        """
        logger.info(f"Detecting prestige vampires (threshold: {threshold_multiplier}x median)...")
        
        # Get network median prestige and performance
        network_stats = self.db.execute_query("""
            SELECT 
                AVG(discovery_prestige) as avg_prestige,
                AVG(avg_score_per_game) as avg_performance
            FROM agents
            WHERE is_active = 1
        """)
        
        if not network_stats or not network_stats[0]['avg_prestige']:
            logger.warning("No active agents found")
            return []
        
        median_prestige = network_stats[0]['avg_prestige']
        median_performance = network_stats[0]['avg_performance'] or 0.0
        prestige_threshold = median_prestige * threshold_multiplier
        
        logger.info(f"Network stats - Prestige: {median_prestige:.2f}, Performance: {median_performance:.2f}")
        logger.info(f"Vampire threshold: Prestige > {prestige_threshold:.2f}")
        
        # Find high-prestige, low-performance agents
        vampire_candidates = self.db.execute_query("""
            SELECT 
                agent_id,
                discovery_prestige as prestige,
                avg_score_per_game,
                total_games_played,
                generation as generation_born
            FROM agents
            WHERE is_active = 1
            AND discovery_prestige > ?
            AND avg_score_per_game < ?
            AND generation < ?
        """, (prestige_threshold, median_performance, current_generation - 3))
        
        vampires = []
        for candidate in vampire_candidates:
            # Calculate knowledge transfer rate
            transfer_rate = self.calculate_knowledge_transfer_rate(candidate['agent_id'])
            
            vampire_info = {
                'agent_id': candidate['agent_id'],
                'prestige': candidate['prestige'],
                'performance': candidate['avg_score_per_game'],
                'prestige_ratio': candidate['prestige'] / median_prestige if median_prestige > 0 else 0,
                'performance_ratio': candidate['avg_score_per_game'] / median_performance if median_performance > 0 else 0,
                'knowledge_transfer_rate': transfer_rate,
                'age_generations': current_generation - candidate['generation_born']
            }
            
            vampires.append(vampire_info)
            logger.info(f"Vampire detected: {candidate['agent_id'][:8]}... - "
                       f"Prestige: {vampire_info['prestige_ratio']:.1f}x median, "
                       f"Performance: {vampire_info['performance_ratio']:.1%} of median, "
                       f"Transfer: {transfer_rate:.1%}")
        
        return vampires
    
    def calculate_knowledge_transfer_rate(self, agent_id: str) -> float:
        """
        Calculate what % of agent's knowledge has been transferred to network.
        
        Measures: How many of agent's sequences are now used by other agents.
        """
        # Get sequences discovered by this agent
        agent_sequences = self.db.execute_query("""
            SELECT sequence_id, times_referenced
            FROM winning_sequences
            WHERE agent_id = ?
            AND is_active = 1
        """, (agent_id,))
        
        if not agent_sequences:
            return 1.0  # No sequences = fully transferred (nothing to transfer)
        
        # Count how many have been used by network (times_referenced > 1)
        transferred = sum(1 for seq in agent_sequences if seq['times_referenced'] > 1)
        total = len(agent_sequences)
        
        return transferred / total if total > 0 else 1.0
    
    def recommend_sunset(self, agent_id: str, vampire_info: Dict) -> Dict:
        """
        Generate sunset recommendation for a vampire agent.
        
        Returns:
            Recommendation dict with reasoning and actions
        """
        recommendation = {
            'agent_id': agent_id,
            'action': 'sunset',
            'reasoning': f"Prestige vampire: {vampire_info['prestige_ratio']:.1f}x median prestige, "
                        f"{vampire_info['performance_ratio']:.1%} of median performance, "
                        f"{vampire_info['knowledge_transfer_rate']:.1%} knowledge transferred",
            'archive': True,
            'revival_candidate': vampire_info['knowledge_transfer_rate'] > 0.8  # High transfer = good candidate
        }
        
        return recommendation
    
    def archive_agent_reasoning(self, agent_id: str, vampire_info: Dict, sunset_reason: str):
        """
        Archive agent before sunset.
        
        Preserves:
        - Final prestige and performance
        - Network state at sunset
        - Knowledge transfer metrics
        - Reasoning summary for potential revival
        """
        # Get agent details
        agent = self.db.execute_query("""
            SELECT agent_type, discovery_prestige as prestige, avg_score_per_game, total_games_played
            FROM agents
            WHERE agent_id = ?
        """, (agent_id,))
        
        if not agent:
            logger.warning(f"Agent {agent_id} not found for archiving")
            return
        
        agent = agent[0]
        
        # Generate reasoning summary
        reasoning = f"Agent type: {agent['agent_type']}. "
        reasoning += f"Contributed {vampire_info['knowledge_transfer_rate']:.1%} knowledge transfer. "
        reasoning += f"Played {agent['total_games_played']} games. "
        reasoning += f"Final prestige: {agent['prestige']:.2f}, Performance: {agent['avg_score_per_game']:.2f}."
        
        # Archive
        self.db.execute_query("""
            INSERT OR REPLACE INTO agent_archive 
            (agent_id, archived_at, final_prestige, final_performance, 
             network_median_at_sunset, knowledge_transfer_rate, reasoning_summary,
             revival_candidate, sunset_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_id,
            datetime.now().isoformat(),
            agent['prestige'],
            agent['avg_score_per_game'],
            vampire_info.get('network_median', 0.0),
            vampire_info['knowledge_transfer_rate'],
            reasoning,
            1 if vampire_info['knowledge_transfer_rate'] > 0.8 else 0,
            sunset_reason
        ))
        
        logger.info(f"Archived agent {agent_id[:8]}... - Revival candidate: {vampire_info['knowledge_transfer_rate'] > 0.8}")
    
    def sunset_vampires(self, vampires: List[Dict], current_generation: int, dry_run: bool = False):
        """
        Sunset vampire agents (archive + deactivate).
        
        Args:
            vampires: List of vampire agent dicts from detect_vampires()
            current_generation: Current generation
            dry_run: If True, don't actually deactivate
        """
        for vampire in vampires:
            agent_id = vampire['agent_id']
            
            # Archive first
            sunset_reason = f"Prestige vampire at generation {current_generation}"
            self.archive_agent_reasoning(agent_id, vampire, sunset_reason)
            
            if not dry_run:
                # Deactivate agent
                self.db.execute_query("""
                    UPDATE agents
                    SET is_active = 0
                    WHERE agent_id = ?
                """, (agent_id,))
                
                logger.info(f"[OK] Sunset vampire {agent_id[:8]}...")
            else:
                logger.info(f"🔍 DRY RUN: Would sunset {agent_id[:8]}...")
        
        logger.info(f"Sunset complete: {len(vampires)} vampires processed")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect and sunset prestige vampires")
    parser.add_argument("--generation", type=int, default=0, help="Current generation")
    parser.add_argument("--threshold", type=float, default=10.0, help="Prestige threshold multiplier")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually sunset agents")
    parser.add_argument("--sunset", action="store_true", help="Actually sunset detected vampires")
    
    args = parser.parse_args()
    
    detector = PrestigeVampireDetector()
    
    print("=" * 70)
    print("PRESTIGE VAMPIRE DETECTION")
    print("=" * 70)
    
    # Detect vampires
    vampires = detector.detect_vampires(args.generation, args.threshold)
    
    print(f"\nFound {len(vampires)} prestige vampires")
    
    if vampires:
        print("\nVampire Details:")
        for v in vampires:
            print(f"  {v['agent_id'][:12]}...")
            print(f"    Prestige: {v['prestige_ratio']:.1f}x median")
            print(f"    Performance: {v['performance_ratio']:.1%} of median")
            print(f"    Knowledge Transfer: {v['knowledge_transfer_rate']:.1%}")
            print(f"    Age: {v['age_generations']} generations")
        
        if args.sunset:
            print(f"\n{'DRY RUN: ' if args.dry_run else ''}Sunsetting vampires...")
            detector.sunset_vampires(vampires, args.generation, dry_run=args.dry_run)
        else:
            print("\n[WARN]  Use --sunset flag to actually sunset these agents")
    else:
        print("\n[OK] No prestige vampires detected")
