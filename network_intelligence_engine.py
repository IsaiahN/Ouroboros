import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Network Intelligence Engine
Treats the DATABASE as the primary organism, with agents as temporary cellular components.
Tracks ecosystem-level health: knowledge diversity, information flow, resilience.

Following Rule 2: Database-Only Storage
Following Roadmap: Network Foundation (prerequisite for all other systems)
"""

import json
import math
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import Counter
import logging

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class NetworkIntelligenceEngine:
    """
    Monitors and analyzes the health of the distributed intelligence network.
    
    The network is the REAL organism. Agents are temporary expressions.
    This engine tracks:
    - Knowledge diversity (how varied is the information)
    - Information flow rate (how fast knowledge spreads)
    - Resilience (how redundant is critical knowledge)
    - Metabolic health (is the network growing or declining)
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.logger = logger
    
    def capture_ecosystem_snapshot(self, generation: int) -> Dict:
        """
        Take vital signs of the meta-organism (the network).
        
        This is THE primary health metric, not individual agent performance.
        
        Args:
            generation: Current evolution generation
            
        Returns:
            Dict with all ecosystem health metrics
        """
        self.logger.info(f"[🌐 NETWORK] Capturing ecosystem snapshot for generation {generation}")
        
        snapshot_id = f"snapshot_{generation}_{uuid.uuid4().hex[:8]}"
        
        # Knowledge metrics (the organism's "knowledge base")
        knowledge_metrics = self._calculate_knowledge_metrics(generation)
        
        # Information flow metrics (the organism's "metabolism")
        flow_metrics = self._calculate_information_flow_metrics(generation)
        
        # Resilience metrics (the organism's "immune system")
        resilience_metrics = self._calculate_resilience_metrics()

        # Persona reliability metrics (per persona submodeling proposal)
        persona_metrics = self._calculate_persona_metrics()
        
        # Population metrics (temporary agent expressions)
        population_metrics = self._calculate_population_metrics(generation)
        
        # Metabolic health indicators
        health_indicators = self._calculate_metabolic_health(
            knowledge_metrics, flow_metrics, population_metrics
        )
        
        # Overall health assessment
        health_status, health_score = self._assess_overall_health(
            knowledge_metrics, flow_metrics, resilience_metrics, 
            population_metrics, health_indicators
        )
        
        # Store snapshot in database
        snapshot = {
            'snapshot_id': snapshot_id,
            'generation': generation,
            **knowledge_metrics,
            **flow_metrics,
            **resilience_metrics,
            **persona_metrics,
            **population_metrics,
            **health_indicators,
            'health_status': health_status,
            'health_score': health_score
        }
        
        self._store_snapshot(snapshot)
        
        self.logger.info(f"[🌐 NETWORK] Snapshot captured: {health_status} (score: {health_score:.3f})")
        
        return snapshot
    
    def _calculate_knowledge_metrics(self, generation: int) -> Dict:
        """Calculate metrics about the knowledge base."""
        
        # Total knowledge in the network
        total_sequences = self.db.execute_query(
            "SELECT COUNT(*) as count FROM winning_sequences"
        )[0]['count'] or 0
        
        total_patterns = self.db.execute_query(
            "SELECT COUNT(*) as count FROM discovered_patterns"
        )[0]['count'] or 0
        
        total_rules = self.db.execute_query(
            "SELECT COUNT(*) as count FROM learned_rules"
        )[0]['count'] or 0
        
        unique_games_solved = self.db.execute_query(
            "SELECT COUNT(DISTINCT game_id) as count FROM winning_sequences"
        )[0]['count'] or 0
        
        # Knowledge diversity (Shannon entropy)
        diversity_index = self._calculate_knowledge_diversity()
        
        return {
            'total_sequences': total_sequences,
            'total_patterns': total_patterns,
            'total_learned_rules': total_rules,
            'unique_games_solved': unique_games_solved,
            'knowledge_diversity_index': diversity_index
        }
    
    def _calculate_information_flow_metrics(self, generation: int) -> Dict:
        """Calculate how fast information is being created and spread."""
        
        # Sequences created this generation
        sequences_created = self.db.execute_query("""
            SELECT COUNT(*) as count FROM winning_sequences
            WHERE discovered_at >= datetime('now', '-1 day')
        """)[0]['count'] or 0
        
        # Sequences validated this generation
        sequences_validated = self.db.execute_query("""
            SELECT COUNT(*) as count FROM sequence_validation_attempts
            WHERE attempted_at >= datetime('now', '-1 day')
        """)[0]['count'] or 0
        
        # Sequences reused (not first discovery)
        sequences_reused = self.db.execute_query("""
            SELECT SUM(times_referenced) as count FROM winning_sequences
            WHERE times_referenced > 0
        """)[0]['count'] or 0
        
        # Rules learned this generation
        rules_learned = self.db.execute_query("""
            SELECT COUNT(*) as count FROM learned_rules
            WHERE created_at >= datetime('now', '-1 day')
        """)[0]['count'] or 0
        
        # Rules transferred this generation
        rules_transferred = self.db.execute_query("""
            SELECT COUNT(*) as count FROM rule_transfers
            WHERE transfer_timestamp >= datetime('now', '-1 day')
            AND transfer_successful = TRUE
        """)[0]['count'] or 0
        
        # Calculate rates
        active_agents = self.db.execute_query("""
            SELECT COUNT(*) as count FROM agents WHERE is_active = TRUE
        """)[0]['count'] or 1
        
        games_this_gen = self.db.execute_query("""
            SELECT COUNT(*) as count FROM agent_arc_performance
            WHERE game_timestamp >= datetime('now', '-1 day')
        """)[0]['count'] or 1
        
        knowledge_creation_rate = sequences_created / max(games_this_gen, 1)
        
        validation_rate = 0.0
        if sequences_validated > 0:
            successful_validations = self.db.execute_query("""
                SELECT COUNT(*) as count FROM sequence_validation_attempts
                WHERE attempted_at >= datetime('now', '-1 day')
                AND validation_success = TRUE
            """)[0]['count'] or 0
            validation_rate = successful_validations / sequences_validated
        
        # NETWORK LEVEL PROGRESS METRICS (BIOME THEORY: Gradual Evolution)
        # Track incremental progress across the entire network
        level_progress = self.db.execute_query("""
            SELECT 
                SUM(final_score) as total_levels,
                AVG(final_score) as avg_levels,
                SUM(total_actions) as total_actions,
                COUNT(*) as game_count
            FROM agent_arc_performance
            WHERE game_timestamp >= datetime('now', '-1 day')
        """)[0]
        
        total_levels_this_gen = level_progress['total_levels'] or 0
        avg_levels_per_game = level_progress['avg_levels'] or 0.0
        total_actions_this_gen = level_progress['total_actions'] or 1
        
        # Metabolic efficiency: levels per action (network-wide)
        avg_actions_per_level = total_actions_this_gen / max(total_levels_this_gen, 1)
        
        # Network learning rate: change in levels/game over last N generations
        prev_gen_data = self.db.execute_query("""
            SELECT avg_levels_per_game FROM ecosystem_health_snapshots
            WHERE generation < ?
            ORDER BY generation DESC LIMIT 1
        """, (generation,))
        
        network_learning_rate = 0.0
        if prev_gen_data and prev_gen_data[0]['avg_levels_per_game']:
            prev_avg = prev_gen_data[0]['avg_levels_per_game']
            network_learning_rate = (avg_levels_per_game - prev_avg) / max(prev_avg, 0.01)
        
        return {
            'sequences_created_this_gen': sequences_created,
            'sequences_validated_this_gen': sequences_validated,
            'sequences_reused_this_gen': sequences_reused,
            'rules_learned_this_gen': rules_learned,
            'rules_transferred_this_gen': rules_transferred,
            'knowledge_creation_rate': knowledge_creation_rate,
            'validation_rate': validation_rate,
            # NEW: Network-level progress tracking
            'total_levels_completed_this_gen': total_levels_this_gen,
            'avg_levels_per_game': avg_levels_per_game,
            'avg_actions_per_level': avg_actions_per_level,
            'network_learning_rate': network_learning_rate
        }

    def _calculate_persona_metrics(self) -> Dict:
        """Aggregate persona health metrics for persona submodeling."""
        try:
            total_personas = self.db.execute_query(
                "SELECT COUNT(*) as count FROM persona_profiles"
            )[0]['count'] or 0

            active_personas = self.db.execute_query(
                "SELECT COUNT(*) as count FROM persona_proposals WHERE created_at >= datetime('now', '-1 day')"
            )[0]['count'] or 0

            avg_reliability_row = self.db.execute_query(
                "SELECT AVG(reliability_score) as avg_rel FROM persona_context_reliability"
            )[0]
            avg_reliability = avg_reliability_row['avg_rel'] if avg_reliability_row and avg_reliability_row['avg_rel'] is not None else 0.5

            return {
                'persona_count': total_personas,
                'persona_active_24h': active_personas,
                'persona_avg_context_reliability': avg_reliability,
            }
        except Exception as exc:
            self.logger.debug(f"Persona metrics skipped: {exc}")
            return {
                'persona_count': 0,
                'persona_active_24h': 0,
                'persona_avg_context_reliability': 0.5,
            }
    
    def _calculate_resilience_metrics(self) -> Dict:
        """Calculate how resilient the network's knowledge is."""
        
        # Critical sequences (>80% reliability)
        critical_sequences = self.db.execute_query("""
            SELECT COUNT(*) as count FROM sequence_reputation
            WHERE reliability_score > 0.8
        """)[0]['count'] or 0
        
        # Orphan sequences (0 validations)
        orphan_sequences = self.db.execute_query("""
            SELECT COUNT(*) as count FROM sequence_reputation
            WHERE total_validation_attempts = 0
        """)[0]['count'] or 0
        
        # Redundancy index (avg validations per sequence)
        redundancy = self.db.execute_query("""
            SELECT AVG(total_validation_attempts) as avg_validations
            FROM sequence_reputation
        """)[0]['avg_validations'] or 0.0
        
        # Knowledge backup ratio (% with multiple carriers)
        total_knowledge = self.db.execute_query("""
            SELECT COUNT(*) as count FROM knowledge_redundancy
        """)[0]['count'] or 1
        
        backed_up_knowledge = self.db.execute_query("""
            SELECT COUNT(*) as count FROM knowledge_redundancy
            WHERE agents_who_know > 1
        """)[0]['count'] or 0
        
        backup_ratio = backed_up_knowledge / max(total_knowledge, 1)
        
        return {
            'critical_sequences_count': critical_sequences,
            'orphan_sequences_count': orphan_sequences,
            'redundancy_index': redundancy,
            'knowledge_backup_ratio': backup_ratio
        }
    
    def _calculate_population_metrics(self, generation: int) -> Dict:
        """Calculate metrics about the agent population (temporary expressions)."""
        
        active_agents = self.db.execute_query("""
            SELECT COUNT(*) as count FROM agents WHERE is_active = TRUE
        """)[0]['count'] or 0
        
        # Agent diversity (type distribution)
        agent_types = self.db.execute_query("""
            SELECT agent_type, COUNT(*) as count FROM agents
            WHERE is_active = TRUE
            GROUP BY agent_type
        """)
        
        agent_diversity = self._calculate_diversity_index([a['count'] for a in agent_types])
        
        # Average agent lifespan
        avg_lifespan = self.db.execute_query("""
            SELECT AVG(a.generation - p.generation) as avg_lifespan
            FROM (
                SELECT a.generation,
                       CAST(json_extract(a.parent_ids, '$[0]') AS TEXT) as parent_id
                FROM agents a
                WHERE a.parent_ids IS NOT NULL AND a.parent_ids != '[]'
            ) AS agent_parents
            LEFT JOIN agents a ON agent_parents.generation = a.generation
            LEFT JOIN agents p ON agent_parents.parent_id = p.agent_id
            WHERE p.generation IS NOT NULL
        """)
        
        avg_lifespan_value = avg_lifespan[0]['avg_lifespan'] if avg_lifespan and avg_lifespan[0]['avg_lifespan'] else 1.0
        
        # Agent turnover (how many retired vs created)
        retired_this_gen = self.db.execute_query("""
            SELECT COUNT(*) as count FROM agents
            WHERE is_active = FALSE
            AND retirement_reason IS NOT NULL
            AND last_performance_update >= datetime('now', '-1 day')
        """)[0]['count'] or 0
        
        turnover_rate = retired_this_gen / max(active_agents, 1)
        
        return {
            'active_agents': active_agents,
            'agent_diversity_index': agent_diversity,
            'avg_agent_lifespan_generations': avg_lifespan_value,
            'agent_turnover_rate': turnover_rate
        }
    
    def _calculate_metabolic_health(self, knowledge_metrics: Dict, 
                                   flow_metrics: Dict, population_metrics: Dict) -> Dict:
        """Calculate overall metabolic health of the network."""
        
        # Network growth rate (knowledge growth vs population)
        knowledge_total = (knowledge_metrics['total_sequences'] + 
                          knowledge_metrics['total_patterns'] + 
                          knowledge_metrics['total_learned_rules'])
        
        network_growth_rate = knowledge_total / max(population_metrics['active_agents'], 1)
        
        # Innovation vs exploitation ratio
        new_sequences = flow_metrics['sequences_created_this_gen']
        reused_sequences = flow_metrics['sequences_reused_this_gen']
        
        if new_sequences + reused_sequences > 0:
            innovation_ratio = new_sequences / (new_sequences + reused_sequences)
        else:
            innovation_ratio = 0.5
        
        # Transfer learning rate
        rules_transferred = flow_metrics['rules_transferred_this_gen']
        transfer_rate = rules_transferred / max(population_metrics['active_agents'], 1)
        
        # System entropy (measure of disorder)
        entropy = self._calculate_system_entropy(knowledge_metrics, population_metrics)
        
        return {
            'network_growth_rate': network_growth_rate,
            'innovation_vs_exploitation': innovation_ratio,
            'transfer_learning_rate': transfer_rate,
            'system_entropy': entropy
        }
    
    def _assess_overall_health(self, knowledge_metrics: Dict, flow_metrics: Dict,
                              resilience_metrics: Dict, population_metrics: Dict,
                              health_indicators: Dict) -> Tuple[str, float]:
        """
        Assess overall network health.
        
        Returns:
            (status_string, health_score)
            status: 'critical', 'poor', 'fair', 'good', 'excellent'
            score: 0.0 to 1.0
        """
        
        # Component scores (0.0 to 1.0 each)
        
        # Knowledge diversity score
        diversity_score = min(knowledge_metrics['knowledge_diversity_index'] / 3.0, 1.0)
        
        # Information flow score
        flow_score = min(flow_metrics['knowledge_creation_rate'] * 2.0, 1.0)
        
        # Resilience score
        resilience_score = resilience_metrics['knowledge_backup_ratio']
        
        # Validation quality score
        validation_score = flow_metrics['validation_rate']
        
        # Growth score
        growth_score = min(health_indicators['network_growth_rate'] / 10.0, 1.0)
        
        # Overall health (weighted average)
        health_score = (
            diversity_score * 0.25 +
            flow_score * 0.20 +
            resilience_score * 0.20 +
            validation_score * 0.15 +
            growth_score * 0.20
        )
        
        # Determine status
        if health_score >= 0.8:
            status = '[STAR] EXCELLENT'
        elif health_score >= 0.6:
            status = '[OK] GOOD'
        elif health_score >= 0.4:
            status = '[WARN] FAIR'
        elif health_score >= 0.2:
            status = '[WARN] POOR'
        else:
            status = '[CRITICAL] CRITICAL'
        
        return status, health_score
    
    def _calculate_knowledge_diversity(self) -> float:
        """Calculate Shannon entropy of knowledge distribution."""
        
        # Get pattern tag distribution
        patterns = self.db.execute_query("""
            SELECT pattern_tags FROM winning_sequences
            WHERE pattern_tags IS NOT NULL
        """)
        
        if not patterns:
            return 0.0
        
        # Count pattern occurrences
        tag_counts = Counter()
        for p in patterns:
            if p['pattern_tags']:
                try:
                    tags = json.loads(p['pattern_tags'])
                    tag_counts.update(tags)
                except:
                    pass
        
        if not tag_counts:
            return 0.0
        
        return self._calculate_diversity_index(list(tag_counts.values()))
    
    def _calculate_diversity_index(self, counts: List[int]) -> float:
        """Calculate Shannon entropy for diversity measurement."""
        
        if not counts or sum(counts) == 0:
            return 0.0
        
        total = sum(counts)
        entropy = 0.0
        
        for count in counts:
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        return entropy
    
    def _calculate_system_entropy(self, knowledge_metrics: Dict, 
                                  population_metrics: Dict) -> float:
        """Calculate overall system disorder/chaos measure."""
        
        # High entropy = chaotic, low entropy = ordered
        # We want moderate entropy (healthy chaos for evolution)
        
        # Agent diversity entropy
        agent_entropy = population_metrics['agent_diversity_index']
        
        # Knowledge diversity entropy  
        knowledge_entropy = knowledge_metrics['knowledge_diversity_index']
        
        # Combine (want both to be moderate)
        system_entropy = (agent_entropy + knowledge_entropy) / 2.0
        
        return system_entropy
    
    def _store_snapshot(self, snapshot: Dict):
        """Store ecosystem snapshot in database."""
        
        columns = ', '.join(snapshot.keys())
        placeholders = ', '.join(['?' for _ in snapshot])
        
        query = f"""
            INSERT INTO ecosystem_health_snapshots ({columns})
            VALUES ({placeholders})
        """
        
        try:
            self.db.execute_query(query, tuple(snapshot.values()))
            self.logger.debug(f"[NETWORK] Snapshot stored: {snapshot['snapshot_id']}")
        except Exception as e:
            self.logger.error(f"[NETWORK] Failed to store snapshot: {e}")
    
    def update_knowledge_redundancy(self, sequence_id: str, generation: int):
        """
        Update redundancy tracking for a sequence when it's used/validated.
        
        This tracks the "viral backup system" - how many agents carry this knowledge.
        """
        
        # Check if already tracked
        existing = self.db.execute_query("""
            SELECT * FROM knowledge_redundancy WHERE sequence_id = ?
        """, (sequence_id,))
        
        if not existing:
            # Get sequence discovery info
            seq_info = self.db.execute_query("""
                SELECT discovered_at, agent_id FROM winning_sequences
                WHERE sequence_id = ?
            """, (sequence_id,))
            
            if not seq_info:
                return
            
            # Create new redundancy entry
            discovery_gen = self.db.execute_query("""
                SELECT generation FROM agents WHERE agent_id = ?
            """, (seq_info[0]['agent_id'],))
            
            gen = discovery_gen[0]['generation'] if discovery_gen else generation
            
            self.db.execute_query("""
                INSERT INTO knowledge_redundancy 
                (sequence_id, discovery_timestamp, discovery_generation, 
                 agents_who_know, agent_carriers, last_used_generation)
                VALUES (?, ?, ?, 1, ?, ?)
            """, (sequence_id, seq_info[0]['discovered_at'], gen,
                  json.dumps([seq_info[0]['agent_id']]), generation))
        
        else:
            # Update existing entry
            # Get agents who successfully used this
            users = self.db.execute_query("""
                SELECT DISTINCT agent_id FROM sequence_validation_attempts
                WHERE sequence_id = ? AND validation_success = TRUE
            """, (sequence_id,))
            
            agent_ids = [u['agent_id'] for u in users]
            agents_who_know = len(agent_ids)
            
            # Calculate criticality
            games_solved = self.db.execute_query("""
                SELECT COUNT(DISTINCT game_id) as count FROM winning_sequences
                WHERE sequence_id = ?
            """, (sequence_id,))[0]['count'] or 0
            
            # Check generations survived
            gens_survived = generation - existing[0]['discovery_generation']
            
            # Risk of loss (inverse of redundancy)
            risk = 1.0 / max(agents_who_know, 1)
            
            # Criticality score
            criticality = (games_solved * 0.5 + agents_who_know * 0.3 + gens_survived * 0.2) / 10.0
            
            self.db.execute_query("""
                UPDATE knowledge_redundancy
                SET agents_who_know = ?,
                    agent_carriers = ?,
                    games_solved_by_this = ?,
                    generations_survived = ?,
                    last_used_generation = ?,
                    last_used_timestamp = CURRENT_TIMESTAMP,
                    risk_of_loss = ?,
                    criticality_score = ?
                WHERE sequence_id = ?
            """, (agents_who_know, json.dumps(agent_ids), games_solved,
                  gens_survived, generation, risk, criticality, sequence_id))


def display_network_intelligence_dashboard(generation: int):
    """
    Display the health of the distributed intelligence network.
    
    This is the PRIMARY metric - not individual agent performance.
    """
    db = DatabaseInterface()
    
    snapshot = db.execute_query("""
        SELECT * FROM ecosystem_health_snapshots
        WHERE generation = ?
        ORDER BY snapshot_timestamp DESC
        LIMIT 1
    """, (generation,))
    
    if not snapshot:
        print("\n[WARN]  No network data available yet for this generation.")
        return
    
    s = snapshot[0]
    
    print("\n" + "=" * 80)
    print("[NETWORK] NETWORK INTELLIGENCE DASHBOARD")
    print("=" * 80)
    print(f"Generation: {s['generation']}")
    print(f"Snapshot Time: {s['snapshot_timestamp']}")
    print()
    
    print("[BOOK] KNOWLEDGE BASE (The Persistent Organism)")
    print(f"  Total Sequences: {s['total_sequences']}")
    print(f"  Total Patterns: {s['total_patterns']}")
    print(f"  Total Learned Rules: {s['total_learned_rules']}")
    print(f"  Unique Games Solved: {s['unique_games_solved']}")
    print(f"  Diversity Index: {s['knowledge_diversity_index']:.3f} (Shannon entropy)")
    print()
    
    print("[CYCLE] METABOLISM (Information Flow)")
    print(f"  Sequences Created: {s['sequences_created_this_gen']}")
    print(f"  Sequences Validated: {s['sequences_validated_this_gen']}")
    print(f"  Sequences Reused: {s['sequences_reused_this_gen']}")
    print(f"  Rules Learned: {s['rules_learned_this_gen']}")
    print(f"  Rules Transferred: {s['rules_transferred_this_gen']}")
    print(f"  Creation Rate: {s['knowledge_creation_rate']:.3f} per agent-game")
    print(f"  Validation Success Rate: {s['validation_rate']:.1%}")
    print()
    print("  [PROGRESS] Network-Level Achievement (Biome Theory)")
    print(f"    Total Levels Completed: {s.get('total_levels_completed_this_gen', 0)}")
    print(f"    Avg Levels/Game: {s.get('avg_levels_per_game', 0.0):.2f}")
    print(f"    Avg Actions/Level: {s.get('avg_actions_per_level', 0.0):.1f}")
    print(f"    Network Learning Rate: {s.get('network_learning_rate', 0.0):.2%}")
    print()
    
    print("[SHIELD] RESILIENCE (Viral Redundancy)")
    print(f"  Critical Sequences: {s['critical_sequences_count']} (>80% reliability)")
    print(f"  Orphan Sequences: {s['orphan_sequences_count']} (0 validations)")
    print(f"  Redundancy Index: {s['redundancy_index']:.2f} backups/sequence")
    print(f"  Knowledge Backup Ratio: {s['knowledge_backup_ratio']:.1%}")
    print()
    
    print("[MICROSCOPE] POPULATION (Temporary Expressions)")
    print(f"  Active Agents: {s['active_agents']}")
    print(f"  Agent Diversity: {s['agent_diversity_index']:.3f}")
    print(f"  Avg Agent Lifespan: {s['avg_agent_lifespan_generations']:.1f} generations")
    print(f"  Agent Turnover Rate: {s['agent_turnover_rate']:.1%}")
    print()
    
    print("[HEART] HEALTH INDICATORS")
    print(f"  Network Growth Rate: {s['network_growth_rate']:.2f} knowledge/agent")
    print(f"  Innovation vs Exploitation: {s['innovation_vs_exploitation']:.2f}")
    print(f"  Transfer Learning Rate: {s['transfer_learning_rate']:.3f}")
    print(f"  System Entropy: {s['system_entropy']:.3f}")
    print()
    
    print(f"  Overall Health: {s['health_status']}")
    print(f"  Health Score: {s['health_score']:.3f} / 1.0")
    print("=" * 80)
    print()
    print("  [INFO] Agents are TEMPORARY. The network is PERMANENT.")
    print("=" * 80)


def assess_network_health(snapshot: Dict) -> Dict:
    """
    Assess network health and provide recommendations.
    
    Returns:
        Dict with status and message
    """
    health_score = snapshot['health_score']
    
    if health_score < 0.2:
        return {
            'status': '[CRITICAL] CRITICAL',
            'message': 'Network health is critical. Immediate intervention needed.'
        }
    elif health_score < 0.4:
        return {
            'status': '[WARN] POOR',
            'message': 'Network struggling. Consider increasing mutation rate or diversity.'
        }
    elif health_score < 0.6:
        return {
            'status': '[WARN] FAIR',
            'message': 'Network stable but room for improvement.'
        }
    elif health_score < 0.8:
        return {
            'status': '[OK] GOOD',
            'message': 'Network healthy and growing.'
        }
    else:
        return {
            'status': '[STAR] EXCELLENT',
            'message': 'Network thriving with excellent knowledge diversity and flow.'
        }


# ============================================================================
# SOCIETAL METRICS SYSTEM - EMERGENCE GAIN
# Part of autopoiesis monitoring for self-regulation
# ============================================================================

def calculate_emergence_gain(db: DatabaseInterface, generation: int) -> float:
    """
    Calculate if network intelligence exceeds sum of individual agents.
    
    Emergence Gain > 1.0 means collective intelligence is working.
    
    Formula:
        network_wins_using_shared_knowledge / max(solo_discoveries, 1)
    
    Where:
        network_wins = Levels beaten using sequences from other agents
        solo_discoveries = Levels beaten without any shared knowledge
    
    Args:
        db: DatabaseInterface instance
        generation: Current evolution generation
        
    Returns:
        Emergence gain ratio (>1.0 = emergence working)
        
    Part of the Societal Metrics System.
    See DOCS/Societal_Metrics_Implementation_Analysis.md for design rationale.
    """
    try:
        # Network level: Wins where agent used sequence discovered by another
        network_wins_result = db.execute_query("""
            SELECT COUNT(*) as count
            FROM agent_arc_performance aap
            WHERE aap.game_timestamp > datetime('now', '-7 days')
              AND EXISTS (
                  SELECT 1 FROM winning_sequences ws
                  WHERE ws.game_id = aap.game_id
                    AND ws.discovered_by_agent_id != aap.agent_id
                    AND ws.times_referenced > 0
              )
        """)
        network_wins = network_wins_result[0]['count'] if network_wins_result else 0
        
        # Individual level: Sequences discovered that were never shared/reused
        solo_result = db.execute_query("""
            SELECT COUNT(DISTINCT sequence_id) as count
            FROM winning_sequences
            WHERE discovered_at > datetime('now', '-7 days')
              AND times_referenced = 0
        """)
        solo_discoveries = max(solo_result[0]['count'] if solo_result else 1, 1)
        
        emergence_gain = network_wins / solo_discoveries
        
        # Store metric in ecosystem_metrics table
        _store_emergence_metric(db, generation, emergence_gain)
        
        logger.info(f"[EMERGENCE] Generation {generation}: "
                   f"gain={emergence_gain:.2f} "
                   f"(network_wins={network_wins}, solo={solo_discoveries})")
        
        return emergence_gain
        
    except Exception as e:
        logger.error(f"Error calculating emergence gain: {e}")
        return 1.0  # Neutral on error


def _store_emergence_metric(db: DatabaseInterface, generation: int, 
                            emergence_gain: float):
    """Store emergence gain in ecosystem_metrics table for tracking."""
    try:
        # Ensure table exists
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS ecosystem_metrics (
                metric_name TEXT NOT NULL,
                generation INTEGER NOT NULL,
                value REAL NOT NULL,
                measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                PRIMARY KEY (metric_name, generation)
            )
        """)
        
        db.execute_query("""
            INSERT INTO ecosystem_metrics (metric_name, generation, value)
            VALUES ('emergence_gain', ?, ?)
            ON CONFLICT(metric_name, generation) DO UPDATE SET 
                value = excluded.value,
                measured_at = CURRENT_TIMESTAMP
        """, (generation, emergence_gain))
        
    except Exception as e:
        logger.error(f"Error storing emergence metric: {e}")
