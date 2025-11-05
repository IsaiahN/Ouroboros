"""
Prestige Engine - Phase 1 of Roadmap
=====================================
Implements network contribution currency (prestige) separate from action budgets.

CRITICAL DISTINCTION:
- Prestige = Social capital (network contribution, teaching, validation)
- Action budgets = Economic capital (performance, wins, efficiency)

Prestige affects:
- breeding_priority (1.0x to 3.0x)
- survival_protection (0% to 80%)
- bonus_game_slots (+0 to +10)

Prestige NEVER affects:
- action_allowance_per_level
- action_allowance_total

This separation ensures:
1. High-performing agents don't dominate breeding just because they win
2. Knowledge-sharing agents get reproductive advantage
3. Network health improves through social incentives
4. Diversity maintained by separating performance from contribution
"""

import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import uuid

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class PrestigeEngine:
    """
    Calculates and applies prestige system for network contribution rewards.
    
    Prestige Formula (from Roadmap Phase 1.3):
    prestige = (network_enrichment * 0.35) + (viral_spread * 0.25) + 
               (persistence * 0.25) + (validation_quality * 0.15)
    
    Components:
    - network_enrichment: Discovery count * innovation score
    - viral_spread: Times used by others * success rate when used
    - persistence: Generations discovery has survived
    - validation_quality: Success rate at using others' discoveries
    """
    
    def __init__(self, db: DatabaseInterface):
        """
        Initialize prestige engine.
        
        Args:
            db: Database interface for querying metrics
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def calculate_agent_prestige(self, agent_id: str, current_generation: int) -> float:
        """
        Calculate prestige score for an agent based on network contributions.
        
        Args:
            agent_id: Agent to calculate prestige for
            current_generation: Current generation number (for persistence calculation)
        
        Returns:
            Prestige score (0.0 to unbounded, typically 0-10 range)
        """
        try:
            # Component 1: Network Enrichment (35%)
            # Discoveries * innovation value
            enrichment_query = """
                SELECT 
                    COUNT(*) as discovery_count,
                    COALESCE(SUM(innovation_value), 0.0) as total_innovation,
                    COALESCE(SUM(network_enrichment_score), 0.0) as total_enrichment
                FROM agent_discoveries
                WHERE agent_id = ?
            """
            enrichment_result = self.db.execute_query(enrichment_query, (agent_id,))
            
            if enrichment_result and len(enrichment_result) > 0:
                discovery_count = enrichment_result[0]['discovery_count']
                total_innovation = enrichment_result[0]['total_innovation']
                total_enrichment = enrichment_result[0]['total_enrichment']
            else:
                discovery_count = 0
                total_innovation = 0.0
                total_enrichment = 0.0
            
            # Network enrichment score (discoveries weighted by innovation and enrichment)
            network_enrichment = (discovery_count * 0.3) + total_innovation + total_enrichment
            
            # Component 2: Viral Spread (25%)
            # How many times have others used this agent's discoveries successfully?
            viral_query = """
                SELECT 
                    COALESCE(SUM(times_used_by_others), 0) as total_uses,
                    COALESCE(AVG(success_rate_by_others), 0.0) as avg_success_rate,
                    COALESCE(SUM(citations), 0) as total_citations
                FROM agent_discoveries
                WHERE agent_id = ?
            """
            viral_result = self.db.execute_query(viral_query, (agent_id,))
            
            if viral_result and len(viral_result) > 0:
                total_uses = viral_result[0]['total_uses']
                avg_success_rate = viral_result[0]['avg_success_rate']
                total_citations = viral_result[0]['total_citations']
            else:
                total_uses = 0
                avg_success_rate = 0.0
                total_citations = 0
            
            # Viral spread score (usage * quality + citations)
            viral_spread = (total_uses * avg_success_rate) + (total_citations * 0.5)
            
            # Component 3: Persistence (25%)
            # How long have discoveries survived in the network?
            persistence_query = """
                SELECT 
                    COALESCE(AVG(generations_persisted), 0.0) as avg_persistence,
                    COALESCE(MAX(generations_persisted), 0) as max_persistence
                FROM agent_discoveries
                WHERE agent_id = ?
            """
            persistence_result = self.db.execute_query(persistence_query, (agent_id,))
            
            if persistence_result and len(persistence_result) > 0:
                avg_persistence = persistence_result[0]['avg_persistence']
                max_persistence = persistence_result[0]['max_persistence']
            else:
                avg_persistence = 0.0
                max_persistence = 0
            
            # Persistence score (average persistence + bonus for max)
            persistence = avg_persistence + (max_persistence * 0.1)
            
            # Component 4: Validation Quality (15%)
            # How good is agent at using others' discoveries?
            validation_query = """
                SELECT 
                    validation_success_rate,
                    improvement_contributions,
                    teaching_events
                FROM agent_validation_performance
                WHERE agent_id = ?
            """
            validation_result = self.db.execute_query(validation_query, (agent_id,))
            
            if validation_result and len(validation_result) > 0:
                validation_success_rate = validation_result[0]['validation_success_rate'] or 0.0
                improvement_contributions = validation_result[0]['improvement_contributions'] or 0
                teaching_events = validation_result[0]['teaching_events'] or 0
            else:
                validation_success_rate = 0.0
                improvement_contributions = 0
                teaching_events = 0
            
            # Validation quality score (success rate + improvements + teaching)
            validation_quality = (validation_success_rate * 5.0) + \
                               (improvement_contributions * 0.5) + \
                               (teaching_events * 0.3)
            
            # Calculate total prestige with weighted components
            total_prestige = (
                (network_enrichment * 0.35) +
                (viral_spread * 0.25) +
                (persistence * 0.25) +
                (validation_quality * 0.15)
            )
            
            self.logger.info(
                f"Prestige calculated for agent {agent_id}: {total_prestige:.3f} "
                f"(enrichment={network_enrichment:.2f}, viral={viral_spread:.2f}, "
                f"persistence={persistence:.2f}, validation={validation_quality:.2f})"
            )
            
            return total_prestige
            
        except Exception as e:
            self.logger.error(f"Error calculating prestige for agent {agent_id}: {e}")
            return 0.0
    
    def apply_prestige_benefits(
        self, 
        agent_id: str, 
        prestige: float, 
        generation_agents: List[Tuple[str, float]]
    ) -> Dict[str, float]:
        """
        Convert prestige into status benefits (breeding priority, survival protection, bonus slots).
        
        CRITICAL: This does NOT affect action budgets - only social status benefits.
        
        Args:
            agent_id: Agent to apply benefits to
            prestige: Agent's prestige score
            generation_agents: List of (agent_id, prestige) tuples for percentile calculation
        
        Returns:
            Dictionary with applied benefits
        """
        try:
            # Calculate prestige percentile within generation
            if len(generation_agents) <= 1:
                percentile = 0.5  # Default for single agent
            else:
                # Sort by prestige
                sorted_agents = sorted(generation_agents, key=lambda x: x[1])
                agent_rank = next(
                    (i for i, (aid, _) in enumerate(sorted_agents) if aid == agent_id),
                    len(sorted_agents) // 2
                )
                percentile = agent_rank / (len(sorted_agents) - 1)
            
            # Convert percentile to benefits
            # Breeding priority: 1.0x (low prestige) to 3.0x (high prestige)
            breeding_priority = 1.0 + (percentile * 2.0)
            
            # Survival protection: 0% (low prestige) to 80% (high prestige)
            # High prestige agents get strong protection from culling
            survival_protection = min(0.8, percentile * 0.8)
            
            # Bonus game slots: +0 (low prestige) to +10 (high prestige)
            # High prestige agents get more chances to demonstrate teaching
            bonus_game_slots = int(percentile * 10)
            
            # Update database
            update_query = """
                UPDATE agents
                SET 
                    discovery_prestige = ?,
                    breeding_priority = ?,
                    survival_protection = ?,
                    bonus_game_slots = ?
                WHERE agent_id = ?
            """
            self.db.execute_query(
                update_query,
                (prestige, breeding_priority, survival_protection, bonus_game_slots, agent_id)
            )
            
            benefits = {
                'prestige': prestige,
                'percentile': percentile,
                'breeding_priority': breeding_priority,
                'survival_protection': survival_protection,
                'bonus_game_slots': bonus_game_slots
            }
            
            self.logger.info(
                f"Applied prestige benefits to {agent_id}: "
                f"priority={breeding_priority:.2f}x, protection={survival_protection*100:.1f}%, "
                f"bonus_slots=+{bonus_game_slots}"
            )
            
            return benefits
            
        except Exception as e:
            self.logger.error(f"Error applying prestige benefits for {agent_id}: {e}")
            return {
                'prestige': prestige,
                'percentile': 0.5,
                'breeding_priority': 1.0,
                'survival_protection': 0.0,
                'bonus_game_slots': 0
            }
    
    def update_all_agent_prestige(self, current_generation: int) -> Dict[str, Dict]:
        """
        Calculate and apply prestige for all active agents in current generation.
        
        Args:
            current_generation: Current generation number
        
        Returns:
            Dictionary of agent_id -> benefits mapping
        """
        try:
            # Get all active agents
            agents_query = """
                SELECT agent_id
                FROM agents
                WHERE is_active = TRUE AND generation <= ?
                ORDER BY generation DESC
            """
            agents = self.db.execute_query(agents_query, (current_generation,))
            
            if not agents:
                self.logger.warning(f"No active agents found for generation {current_generation}")
                return {}
            
            # Calculate prestige for all agents
            agent_prestige_list = []
            for (agent_id,) in agents:
                prestige = self.calculate_agent_prestige(agent_id, current_generation)
                agent_prestige_list.append((agent_id, prestige))
            
            # Apply benefits to all agents
            benefits_map = {}
            for agent_id, prestige in agent_prestige_list:
                benefits = self.apply_prestige_benefits(
                    agent_id, 
                    prestige, 
                    agent_prestige_list
                )
                benefits_map[agent_id] = benefits
            
            self.logger.info(
                f"Updated prestige for {len(benefits_map)} agents in generation {current_generation}"
            )
            
            return benefits_map
            
        except Exception as e:
            self.logger.error(f"Error updating all agent prestige: {e}")
            return {}
    
    def record_discovery(
        self,
        agent_id: str,
        discovery_type: str,
        sequence_id: Optional[str] = None,
        pattern_id: Optional[str] = None,
        rule_id: Optional[str] = None,
        innovation_value: float = 0.0,
        network_enrichment_score: float = 0.0
    ) -> str:
        """
        Record a new discovery by an agent.
        
        Args:
            agent_id: Agent making the discovery
            discovery_type: Type of discovery ('winning_sequence', 'pattern', 'rule')
            sequence_id: Optional sequence ID
            pattern_id: Optional pattern ID
            rule_id: Optional rule ID
            innovation_value: Novelty score (0.0 to 1.0)
            network_enrichment_score: Value added to network
        
        Returns:
            Discovery ID
        """
        try:
            discovery_id = f"disc_{uuid.uuid4().hex[:16]}"
            
            insert_query = """
                INSERT INTO agent_discoveries (
                    discovery_id, agent_id, discovery_type,
                    sequence_id, pattern_id, rule_id,
                    innovation_value, network_enrichment_score,
                    discovery_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(
                insert_query,
                (
                    discovery_id, agent_id, discovery_type,
                    sequence_id, pattern_id, rule_id,
                    innovation_value, network_enrichment_score,
                    datetime.now().isoformat()
                )
            )
            
            # Update agent discovery count
            update_count_query = """
                UPDATE agents
                SET sequence_discovery_count = sequence_discovery_count + 1
                WHERE agent_id = ?
            """
            self.db.execute_query(update_count_query, (agent_id,))
            
            self.logger.info(
                f"Recorded {discovery_type} discovery {discovery_id} for agent {agent_id}"
            )
            
            return discovery_id
            
        except Exception as e:
            self.logger.error(f"Error recording discovery for {agent_id}: {e}")
            return ""
    
    def record_validation_attempt(
        self,
        agent_id: str,
        sequence_id: str,
        success: bool,
        efficiency_vs_original: float = 1.0
    ):
        """
        Record a sequence validation attempt by an agent.
        
        CRITICAL FOR PRESTIGE: This updates viral spread metrics when agents
        use each other's sequences.
        
        Args:
            agent_id: Agent attempting validation
            sequence_id: Sequence being validated
            success: Whether validation succeeded
            efficiency_vs_original: Efficiency ratio (<1.0 = improved, >1.0 = worse)
        """
        try:
            # Ensure agent has validation performance record
            check_query = """
                SELECT agent_id FROM agent_validation_performance WHERE agent_id = ?
            """
            existing = self.db.execute_query(check_query, (agent_id,))
            
            if not existing:
                # Create initial record
                create_query = """
                    INSERT INTO agent_validation_performance (agent_id)
                    VALUES (?)
                """
                self.db.execute_query(create_query, (agent_id,))
            
            # Update validation metrics
            update_query = """
                UPDATE agent_validation_performance
                SET 
                    sequences_attempted = sequences_attempted + 1,
                    sequences_succeeded = sequences_succeeded + ?,
                    validation_success_rate = 
                        CAST(sequences_succeeded + ? AS REAL) / (sequences_attempted + 1),
                    avg_efficiency_vs_original = 
                        ((avg_efficiency_vs_original * sequences_attempted) + ?) / (sequences_attempted + 1),
                    improvement_contributions = improvement_contributions + ?
                WHERE agent_id = ?
            """
            
            improved = 1 if efficiency_vs_original < 1.0 else 0
            success_int = 1 if success else 0
            
            self.db.execute_query(
                update_query,
                (success_int, success_int, efficiency_vs_original, improved, agent_id)
            )
            
            # CRITICAL: Update viral spread metrics for the ORIGINAL DISCOVERER
            # Find who discovered this sequence
            discoverer_query = """
                SELECT agent_id as discoverer_id
                FROM winning_sequences
                WHERE sequence_id = ?
            """
            discoverer_result = self.db.execute_query(discoverer_query, (sequence_id,))
            
            if discoverer_result and discoverer_result[0]['discoverer_id']:
                discoverer_id = discoverer_result[0]['discoverer_id']
                
                # Only count if different agent is using the sequence
                if discoverer_id != agent_id:
                    # Find the discovery record
                    discovery_query = """
                        SELECT discovery_id, times_used_by_others, success_rate_by_others
                        FROM agent_discoveries
                        WHERE agent_id = ? AND sequence_id = ?
                        LIMIT 1
                    """
                    discovery_result = self.db.execute_query(
                        discovery_query, 
                        (discoverer_id, sequence_id)
                    )
                    
                    if discovery_result:
                        # Update existing discovery record with viral spread
                        current_uses = discovery_result[0]['times_used_by_others'] or 0
                        current_success_rate = discovery_result[0]['success_rate_by_others'] or 0.0
                        
                        new_uses = current_uses + 1
                        # Running average of success rate
                        new_success_rate = (
                            (current_success_rate * current_uses + success_int) / new_uses
                        )
                        
                        update_discovery_query = """
                            UPDATE agent_discoveries
                            SET 
                                times_used_by_others = ?,
                                success_rate_by_others = ?
                            WHERE agent_id = ? AND sequence_id = ?
                        """
                        self.db.execute_query(
                            update_discovery_query,
                            (new_uses, new_success_rate, discoverer_id, sequence_id)
                        )
                        
                        self.logger.info(
                            f"🦠 VIRAL SPREAD: Agent {agent_id[:8]} used {discoverer_id[:8]}'s "
                            f"sequence {sequence_id[:8]} - "
                            f"{'SUCCESS' if success else 'FAILED'} "
                            f"(total uses: {new_uses}, success rate: {new_success_rate:.1%})"
                        )
            
            self.logger.debug(
                f"Recorded validation attempt for {agent_id}: "
                f"success={success}, efficiency={efficiency_vs_original:.3f}"
            )
            
        except Exception as e:
            self.logger.error(f"Error recording validation attempt for {agent_id}: {e}")
    
    def get_prestige_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Get top agents by prestige score.
        
        Args:
            limit: Number of top agents to return
        
        Returns:
            List of agent prestige info dictionaries
        """
        try:
            query = """
                SELECT 
                    a.agent_id,
                    a.agent_type,
                    a.generation,
                    a.discovery_prestige,
                    a.breeding_priority,
                    a.survival_protection,
                    a.bonus_game_slots,
                    a.sequence_discovery_count,
                    a.validation_reputation,
                    a.total_games_won,
                    a.avg_score_per_game
                FROM agents a
                WHERE a.is_active = TRUE
                ORDER BY a.discovery_prestige DESC
                LIMIT ?
            """
            
            results = self.db.execute_query(query, (limit,))
            
            if not results:
                return []
            
            leaderboard = []
            for row in results:
                leaderboard.append({
                    'agent_id': row['agent_id'],
                    'agent_type': row['agent_type'],
                    'generation': row['generation'],
                    'prestige': row['discovery_prestige'],
                    'breeding_priority': row['breeding_priority'],
                    'survival_protection': row['survival_protection'],
                    'bonus_game_slots': row['bonus_game_slots'],
                    'discoveries': row['sequence_discovery_count'],
                    'validation_reputation': row['validation_reputation'],
                    'games_won': row['total_games_won'],
                    'avg_score': row['avg_score_per_game']
                })
            
            return leaderboard
            
        except Exception as e:
            self.logger.error(f"Error getting prestige leaderboard: {e}")
            return []


def display_prestige_leaderboard(db: DatabaseInterface, limit: int = 10):
    """
    Display prestige leaderboard with network contribution emphasis.
    
    Args:
        db: Database interface
        limit: Number of top agents to show
    """
    engine = PrestigeEngine(db)
    leaderboard = engine.get_prestige_leaderboard(limit)
    
    if not leaderboard:
        print("\n[!] No agents with prestige data found")
        return
    
    print("\n" + "="*80)
    print("PRESTIGE LEADERBOARD - Network Contribution Rankings")
    print("="*80)
    print("\nNOTE: Prestige rewards NETWORK CONTRIBUTION (teaching, sharing, validation)")
    print("      NOT individual performance (wins, scores)")
    print("-"*80)
    
    for i, agent in enumerate(leaderboard, 1):
        print(f"\n#{i} Agent: {agent['agent_id'][:12]}... (Gen {agent['generation']})")
        print(f"   Type: {agent['agent_type']}")
        print(f"   Prestige: {agent['prestige']:.3f}")
        print(f"   Status Benefits:")
        print(f"      - Breeding Priority: {agent['breeding_priority']:.2f}x")
        print(f"      - Survival Protection: {agent['survival_protection']*100:.1f}%")
        print(f"      - Bonus Game Slots: +{agent['bonus_game_slots']}")
        print(f"   Network Contributions:")
        print(f"      - Discoveries Shared: {agent['discoveries']}")
        print(f"      - Validation Reputation: {agent['validation_reputation']:.3f}")
        print(f"   Performance (for context):")
        print(f"      - Games Won: {agent['games_won']}")
        print(f"      - Avg Score: {agent['avg_score']:.2f}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Test prestige engine
    import sys
    
    db = DatabaseInterface()
    engine = PrestigeEngine(db)
    
    if len(sys.argv) > 1 and sys.argv[1] == "leaderboard":
        display_prestige_leaderboard(db, limit=15)
    else:
        # Update all agent prestige
        print("[*] Calculating prestige for all active agents...")
        
        # Get current generation
        gen_query = "SELECT MAX(generation) as gen FROM agents WHERE is_active = TRUE"
        result = db.execute_query(gen_query)
        current_gen = result[0]['gen'] if result and result[0]['gen'] else 0
        
        benefits_map = engine.update_all_agent_prestige(current_gen)
        
        print(f"[+] Updated prestige for {len(benefits_map)} agents")
        
        # Show leaderboard
        display_prestige_leaderboard(db, limit=10)
