"""
Knowledge Recombination Engine - Phase 2.5
Enables viral-style horizontal gene transfer through sequence chaining and pattern synthesis.

This is the "viral evolution accelerator" that transforms linear discovery into 
exponential knowledge growth through combinatorial exploration.

CRITICAL: This is OPPORTUNISTIC and AUTOMATIC - runs after EVERY game, not optional.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from database_interface import DatabaseInterface


class KnowledgeRecombinationEngine:
    """
    Enables viral-style recombination of knowledge.
    
    This is the horizontal gene transfer mechanism from biome theory - 
    sequences and patterns can be COMBINED to create new knowledge,
    not just mutated or inherited.
    
    Key Concepts:
    - Sequence Chaining: Combine two successful sequences into longer one
    - Pattern Synthesis: Merge abstract patterns into meta-patterns
    - Dependency Tracking: Know which sequences build on which
    - Viral Spread: Successful recombinations spread horizontally
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
    
    def attempt_sequence_chain(
        self, 
        agent_id: str, 
        game_id: str,
        level_index: int,
        seq_a_id: str, 
        seq_b_id: str,
        generation: int
    ) -> Optional[Dict[str, Any]]:
        """
        Try to chain two sequences into a longer combined sequence.
        
        This is the core recombination operation - takes two working sequences
        and attempts to combine them into a single more powerful sequence.
        
        Args:
            agent_id: Agent attempting recombination
            game_id: Game context for recombination
            level_index: Which level (0-based) to test on
            seq_a_id: First sequence to combine
            seq_b_id: Second sequence to combine
            generation: Current generation
        
        Returns:
            Dict with recombination result if successful, None if failed
        """
        # Get both sequences
        seq_a_result = self.db.execute_query("""
            SELECT sequence_id, actions, score_achieved, actions_count, game_id
            FROM winning_sequences WHERE sequence_id = ?
        """, (seq_a_id,))
        
        seq_b_result = self.db.execute_query("""
            SELECT sequence_id, actions, score_achieved, actions_count, game_id
            FROM winning_sequences WHERE sequence_id = ?
        """, (seq_b_id,))
        
        if not seq_a_result or not seq_b_result:
            return None
        
        seq_a = seq_a_result[0]
        seq_b = seq_b_result[0]
        
        # Parse action sequences
        try:
            actions_a = json.loads(seq_a['actions'])
            actions_b = json.loads(seq_b['actions'])
        except (json.JSONDecodeError, TypeError):
            # Warning: Failed to parse sequences
            return None
        
        # Simple chaining strategy: concatenate actions
        combined_actions = actions_a + actions_b
        
        # Generate unique ID for combined sequence
        chain_id = f"chain_{uuid.uuid4().hex[:8]}_{seq_a_id[:6]}_{seq_b_id[:6]}"
        
        # Calculate efficiency metrics
        parent_efficiency = (seq_a['score_achieved'] + seq_b['score_achieved']) / (seq_a['actions_count'] + seq_b['actions_count'])
        
        # For now, we'll mark this as an untested chain
        # The actual testing happens when agents try to USE this sequence
        # This is different from roadmap spec - we're creating "hypothetical" chains
        # that get validated through community use (more viral-like)
        
        result = {
            'chain_id': chain_id,
            'parent_a': seq_a_id,
            'parent_b': seq_b_id,
            'combined_actions': combined_actions,
            'combined_length': len(combined_actions),
            'parent_efficiency': parent_efficiency,
            'discovery_agent': agent_id,
            'discovery_generation': generation
        }
        
        return result
    
    def store_sequence_chain(
        self, 
        chain_result: Dict[str, Any],
        game_id: str,
        level_index: int
    ) -> str:
        """
        Store a discovered sequence chain in the database.
        
        Returns:
            sequence_id of the stored chain
        """
        chain_id = chain_result['chain_id']
        
        # Store in winning_sequences (marked as untested recombination)
        self.db.execute_query("""
            INSERT OR IGNORE INTO winning_sequences
            (sequence_id, game_id, level_index, actions, actions_count,
             score_achieved, discovered_by_agent, discovery_generation,
             is_recombination, times_used, success_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0)
        """, (
            chain_id,
            game_id,
            level_index,
            json.dumps(chain_result['combined_actions']),
            chain_result['combined_length'],
            0,  # Unknown score until tested
            chain_result['discovery_agent'],
            chain_result['discovery_generation']
        ))
        
        # Store dependency relationships
        for parent_id in [chain_result['parent_a'], chain_result['parent_b']]:
            dep_id = f"dep_{uuid.uuid4().hex[:12]}"
            self.db.execute_query("""
                INSERT OR IGNORE INTO sequence_dependencies
                (dependency_id, parent_sequence_id, child_sequence_id,
                 dependency_type, discovery_agent_id, discovery_generation,
                 combined_efficiency, improvement_over_parent)
                VALUES (?, ?, ?, 'chain', ?, ?, ?, 0.0)
            """, (
                dep_id,
                parent_id,
                chain_id,
                chain_result['discovery_agent'],
                chain_result['discovery_generation'],
                chain_result['parent_efficiency']
            ))
        
        # Info: Stored sequence chain combining parent sequences
        
        return chain_id
    
    def discover_sequence_combinations(
        self, 
        agent_id: str, 
        game_id: str,
        level_index: int,
        generation: int,
        max_attempts: int = 5
    ) -> List[str]:
        """
        Systematically explore combinations of known sequences.
        
        This is COMBINATORIAL EXPLORATION, not random mutation.
        After each game, the agent tries to combine successful sequences
        to create new hypothetical sequences for the network to test.
        
        Args:
            agent_id: Agent attempting recombination
            game_id: Game context
            level_index: Which level to combine sequences for
            generation: Current generation
            max_attempts: Maximum pairwise combinations to try
        
        Returns:
            List of newly created sequence_ids
        """
        # Get all validated sequences for this game and level
        # Prioritize high-reliability sequences (community validated)
        known_sequences = self.db.execute_query("""
            SELECT ws.sequence_id, ws.actions_count, ws.score_achieved,
                   COALESCE(
                       (sv.success_count + 2.0) / (sv.total_attempts + 4.0),
                       0.5
                   ) as reliability
            FROM winning_sequences ws
            LEFT JOIN sequence_validation sv ON ws.sequence_id = sv.sequence_id
            WHERE ws.game_id = ? AND ws.level_index = ?
            ORDER BY reliability DESC, ws.score_achieved DESC
            LIMIT 10
        """, (game_id, level_index))
        
        if len(known_sequences) < 2:
            # Need at least 2 sequences to combine
            return []
        
        new_discoveries = []
        attempts_made = 0
        
        # Try pairwise combinations (avoiding duplicate pairs)
        for i, seq_a in enumerate(known_sequences):
            if attempts_made >= max_attempts:
                break
            
            for seq_b in known_sequences[i+1:]:
                if attempts_made >= max_attempts:
                    break
                
                # Log attempt
                attempt_id = f"attempt_{uuid.uuid4().hex[:12]}"
                
                # Attempt chain
                chain_result = self.attempt_sequence_chain(
                    agent_id=agent_id,
                    game_id=game_id,
                    level_index=level_index,
                    seq_a_id=seq_a['sequence_id'],
                    seq_b_id=seq_b['sequence_id'],
                    generation=generation
                )
                
                attempts_made += 1
                
                if chain_result:
                    # Store the chain
                    chain_id = self.store_sequence_chain(
                        chain_result, game_id, level_index
                    )
                    new_discoveries.append(chain_id)
                    
                    # Log successful attempt
                    self.db.execute_query("""
                        INSERT INTO recombination_attempts
                        (attempt_id, agent_id, game_id, generation,
                         sequence_a_id, sequence_b_id, combination_type,
                         was_successful, resulting_sequence_id, actions_used)
                        VALUES (?, ?, ?, ?, ?, ?, 'chain', 1, ?, ?)
                    """, (
                        attempt_id,
                        agent_id,
                        game_id,
                        generation,
                        seq_a['sequence_id'],
                        seq_b['sequence_id'],
                        chain_id,
                        chain_result['combined_length']
                    ))
                else:
                    # Log failed attempt
                    self.db.execute_query("""
                        INSERT INTO recombination_attempts
                        (attempt_id, agent_id, game_id, generation,
                         sequence_a_id, sequence_b_id, combination_type,
                         was_successful, failure_reason)
                        VALUES (?, ?, ?, ?, ?, ?, 'chain', 0, 'combination_failed')
                    """, (
                        attempt_id,
                        agent_id,
                        game_id,
                        generation,
                        seq_a['sequence_id'],
                        seq_b['sequence_id']
                    ))
        
        # Update agent recombination stats
        if new_discoveries:
            self.db.execute_query("""
                UPDATE agents
                SET recombination_discoveries = recombination_discoveries + ?,
                    successful_recombinations = successful_recombinations + ?
                WHERE agent_id = ?
            """, (len(new_discoveries), len(new_discoveries), agent_id))
        
        # Update recombination success rate
        self.db.execute_query("""
            UPDATE agents
            SET recombination_success_rate = 
                CAST(successful_recombinations AS REAL) / 
                NULLIF(recombination_discoveries + ?, 1)
            WHERE agent_id = ?
        """, (attempts_made, agent_id))
        
        # Log successful recombinations (Phase 2.5)
        if new_discoveries:
            pass  # Info: Agent created N sequence chains
        
        return new_discoveries
    
    def get_recombination_stats(self, agent_id: Optional[str] = None, generation: Optional[int] = None) -> Dict[str, Any]:
        """
        Get recombination statistics for an agent or entire network.
        
        Args:
            agent_id: Specific agent to analyze (None = entire network)
            generation: Specific generation (None = all time)
        
        Returns:
            Dictionary with recombination metrics
        """
        if agent_id:
            # Agent-specific stats
            agent_stats = self.db.execute_query("""
                SELECT recombination_discoveries, successful_recombinations,
                       recombination_success_rate
                FROM agents WHERE agent_id = ?
            """, (agent_id,))
            
            if not agent_stats:
                return {}
            
            return agent_stats[0]
        
        # Network-wide stats
        where_clause = ""
        params = ()
        if generation is not None:
            where_clause = "WHERE generation = ?"
            params = (generation,)
        
        network_stats = self.db.execute_query(f"""
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN was_successful THEN 1 ELSE 0 END) as successful_chains,
                COUNT(DISTINCT agent_id) as agents_attempting,
                COUNT(DISTINCT resulting_sequence_id) as unique_chains_created
            FROM recombination_attempts
            {where_clause}
        """, params)
        
        if not network_stats or not network_stats[0]:
            return {
                'total_attempts': 0,
                'successful_chains': 0,
                'agents_attempting': 0,
                'unique_chains_created': 0,
                'success_rate': 0.0
            }
        
        stats = network_stats[0]
        total = stats.get('total_attempts') or 0
        successful = stats.get('successful_chains') or 0
        stats['success_rate'] = successful / max(total, 1)
        
        return stats
    
    def get_most_foundational_sequences(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find sequences that are most frequently used as parents in recombination.
        
        These are the "foundational" sequences that enable viral knowledge growth.
        
        Returns:
            List of sequences ordered by how many descendants they have
        """
        foundational = self.db.execute_query("""
            SELECT 
                ws.sequence_id,
                ws.game_id,
                ws.level_index,
                ws.discovered_by_agent,
                COUNT(DISTINCT sd.child_sequence_id) as descendant_count,
                COUNT(DISTINCT sd.discovery_agent_id) as recombined_by_agents
            FROM winning_sequences ws
            JOIN sequence_dependencies sd ON ws.sequence_id = sd.parent_sequence_id
            GROUP BY ws.sequence_id
            ORDER BY descendant_count DESC, recombined_by_agents DESC
            LIMIT ?
        """, (limit,))
        
        return foundational

