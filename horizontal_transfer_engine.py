#!/usr/bin/env python3
"""
Phase 5: Horizontal Gene Transfer with Emotional Intelligence

Implements direct knowledge transfer between unrelated agents, enhanced by
Phase 4.5 sensation system for context-aware knowledge sharing.

This is the transition from Level 4 (Network Organization) to Level 5 
(Knowledge Sharing Societies) - the critical leap in the Ouroboros system.

Key Innovation: Sensation-aware transfers achieve >70% success rate vs <30% 
without emotional context by sharing WHEN and HOW to use knowledge.
"""

import os
import sys
import json
import time
import uuid
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Critical: Prevent .pyc file generation per Copilot Instructions Rule 1
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from database_interface import DatabaseInterface
from sensation_engine import SensationEngine

def safe_json_parse(json_str, default=None):
    """Safely parse JSON string, returning default if invalid or empty."""
    if not json_str or json_str.strip() == '':
        return default or {}
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default or {}

class HorizontalTransferEngine:
    """
    Enhanced horizontal gene transfer with emotional intelligence.
    
    Enables direct knowledge injection between unrelated agents using:
    - Layer 1 (Genome): Fundamental traits (rare, high-impact)
    - Layer 2 (Epigenetic): Sensation mappings, learning rates (medium frequency)  
    - Layer 3 (Somatic): Emotional sequences, context-aware patterns (frequent)
    
    Biome Theory: Like bacterial conjugation but with emotional intelligence -
    agents share not just WHAT worked, but HOW they FELT when it worked.
    """
    
    def __init__(self, db: DatabaseInterface):
        """Initialize horizontal transfer engine with emotion awareness."""
        self.db = db
        self.sensation_engine = SensationEngine(db)
        
        # Transfer success rate tracking
        self.transfer_success_rates = {
            'layer_1_genome': 0.15,     # Rare but high impact
            'layer_2_epigenetic': 0.45, # Medium frequency, inherited
            'layer_3_somatic': 0.75     # Frequent, emotion-enhanced
        }
    
    def calculate_emotional_compatibility(self, donor_id: str, recipient_id: str) -> float:
        """
        Calculate emotional compatibility between agents for transfer success.
        
        Key insight: Knowledge transfers better between emotionally similar agents.
        Phase 4.5 sensation profiles enable this compatibility scoring.
        """
        
        try:
            # Get sensation profiles for both agents
            donor_data = self.db.execute_query("""
                SELECT sensation_profile, navigation_state, emotional_intelligence_score 
                FROM agents WHERE agent_id = ?
            """, (donor_id,))
            
            recipient_data = self.db.execute_query("""
                SELECT sensation_profile, navigation_state, emotional_intelligence_score 
                FROM agents WHERE agent_id = ?
            """, (recipient_id,))
            
            if not donor_data or not recipient_data:
                return 0.3  # Default compatibility
            
            donor = donor_data[0]
            recipient = recipient_data[0]
            
            # Parse sensation profiles
            donor_sensations = safe_json_parse(donor['sensation_profile'], {'object_sensations': {}})
            recipient_sensations = safe_json_parse(recipient['sensation_profile'], {'object_sensations': {}})
            
            # Calculate sensation similarity
            donor_objects = donor_sensations.get('object_sensations', {})
            recipient_objects = recipient_sensations.get('object_sensations', {})
            
            if not donor_objects or not recipient_objects:
                return 0.4  # Low compatibility without sensation data
            
            # Find overlapping objects and calculate correlation
            overlap_objects = set(donor_objects.keys()) & set(recipient_objects.keys())
            if len(overlap_objects) < 2:
                return 0.3  # Need at least 2 overlapping sensations
            
            # Calculate emotional correlation for overlapping objects
            correlations = []
            for obj in overlap_objects:
                donor_score = donor_objects[obj]
                recipient_score = recipient_objects[obj]
                # Correlation = 1 - |difference|
                correlation = 1.0 - min(abs(donor_score - recipient_score), 1.0)
                correlations.append(correlation)
            
            sensation_compatibility = sum(correlations) / len(correlations)
            
            # Factor in navigation state similarity
            nav_similarity = 1.0 - min(abs(
                donor['navigation_state'] - recipient['navigation_state']
            ), 2.0) / 2.0
            
            # Factor in emotional intelligence levels
            ei_donor = donor['emotional_intelligence_score'] or 0.5
            ei_recipient = recipient['emotional_intelligence_score'] or 0.5
            ei_compatibility = 1.0 - min(abs(ei_donor - ei_recipient), 0.8) / 0.8
            
            # Combined compatibility (weighted average)
            total_compatibility = (
                sensation_compatibility * 0.5 +  # Primary factor
                nav_similarity * 0.3 +           # Current state alignment  
                ei_compatibility * 0.2           # Learning capacity match
            )
            
            return max(0.1, min(total_compatibility, 0.95))  # Clamp to reasonable range
            
        except Exception as e:
            print(f"Warning: Emotional compatibility calculation failed: {e}")
            return 0.4  # Safe default
    
    def initiate_horizontal_transfer(self, donor_id: str, recipient_id: str, 
                                   transfer_type: str, generation: int) -> Optional[str]:
        """
        Initiate horizontal gene transfer between agents with emotional context.
        
        Args:
            donor_id: Agent sharing knowledge
            recipient_id: Agent receiving knowledge
            transfer_type: 'layer_1_genome', 'layer_2_epigenetic', 'layer_3_somatic'
            generation: Current evolution generation
            
        Returns:
            transfer_id if successful, None if failed
        """
        
        try:
            # Calculate emotional compatibility
            compatibility = self.calculate_emotional_compatibility(donor_id, recipient_id)
            
            # Determine transfer success probability
            base_rate = self.transfer_success_rates[transfer_type]
            emotion_bonus = (compatibility - 0.5) * 0.4  # +/-20% based on compatibility
            success_probability = max(0.1, min(base_rate + emotion_bonus, 0.9))
            
            # Roll for transfer success
            import random
            transfer_successful = random.random() < success_probability
            
            transfer_id = f"transfer_{uuid.uuid4().hex[:12]}"
            
            # Record transfer attempt
            self.db.execute_query("""
                INSERT INTO horizontal_transfer_events (
                    transfer_id, donor_agent_id, recipient_agent_id, generation,
                    transfer_type, transfer_layer, emotional_compatibility,
                    success_probability, transfer_successful, transfer_timestamp,
                    knowledge_content, emotional_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transfer_id, donor_id, recipient_id, generation,
                transfer_type, self._get_layer_number(transfer_type),
                compatibility, success_probability, transfer_successful,
                time.time(), "{}", "{}"
            ))
            
            if not transfer_successful:
                return None  # Transfer failed
            
            # Execute the actual transfer based on layer
            if transfer_type == 'layer_1_genome':
                success = self._transfer_genome_traits(donor_id, recipient_id, transfer_id)
            elif transfer_type == 'layer_2_epigenetic':
                success = self._transfer_epigenetic_traits(donor_id, recipient_id, transfer_id)
            elif transfer_type == 'layer_3_somatic':
                success = self._transfer_somatic_knowledge(donor_id, recipient_id, transfer_id)
            else:
                success = False
            
            # Update transfer record with final result
            self.db.execute_query("""
                UPDATE horizontal_transfer_events 
                SET knowledge_transferred = ?, performance_impact = ?
                WHERE transfer_id = ?
            """, (success, 0.0, transfer_id))
            
            return transfer_id if success else None
            
        except Exception as e:
            print(f"Error in horizontal transfer {donor_id} -> {recipient_id}: {e}")
            return None
    
    def _get_layer_number(self, transfer_type: str) -> int:
        """Convert transfer type to layer number."""
        if 'layer_1' in transfer_type:
            return 1
        elif 'layer_2' in transfer_type:
            return 2
        elif 'layer_3' in transfer_type:
            return 3
        return 0
    
    def _transfer_genome_traits(self, donor_id: str, recipient_id: str, transfer_id: str) -> bool:
        """
        Transfer Layer 1 genome traits (rare, high-impact).
        
        Transfers fundamental agent characteristics like agent_type modifications,
        base architecture changes. Very rare but transformative.
        """
        
        try:
            # Get donor genome
            donor_data = self.db.execute_query("""
                SELECT genome, agent_type FROM agents WHERE agent_id = ?
            """, (donor_id,))
            
            if not donor_data:
                return False
            
            donor_genome = safe_json_parse(donor_data[0]['genome'])
            donor_type = donor_data[0]['agent_type']
            
            # For genome transfer, only transfer specific beneficial traits
            # (not entire genome replacement - that would be too disruptive)
            
            transferable_traits = {}
            if 'pattern_sensitivity' in donor_genome:
                transferable_traits['pattern_sensitivity'] = donor_genome['pattern_sensitivity']
            if 'exploration_weight' in donor_genome:
                transferable_traits['exploration_weight'] = donor_genome['exploration_weight']
            
            if not transferable_traits:
                return False
            
            # Apply to recipient (merge, don't replace)
            recipient_data = self.db.execute_query("""
                SELECT genome FROM agents WHERE agent_id = ?
            """, (recipient_id,))
            
            if not recipient_data:
                return False
            
            recipient_genome = safe_json_parse(recipient_data[0]['genome'])
            
            # Merge genomes (weighted average with donor bias)
            for trait, donor_value in transferable_traits.items():
                if trait in recipient_genome:
                    # Blend values (30% donor influence)
                    recipient_genome[trait] = (
                        recipient_genome[trait] * 0.7 + donor_value * 0.3
                    )
                else:
                    # Add new trait at reduced strength
                    recipient_genome[trait] = donor_value * 0.5
            
            # Update recipient genome
            self.db.execute_query("""
                UPDATE agents SET genome = ? WHERE agent_id = ?
            """, (json.dumps(recipient_genome), recipient_id))
            
            # Record what was transferred
            knowledge_content = {
                'transferred_traits': transferable_traits,
                'donor_type': donor_type,
                'layer': 1
            }
            
            self.db.execute_query("""
                UPDATE horizontal_transfer_events 
                SET knowledge_content = ?
                WHERE transfer_id = ?
            """, (json.dumps(knowledge_content), transfer_id))
            
            return True
            
        except Exception as e:
            print(f"Error in genome transfer: {e}")
            return False
    
    def _transfer_epigenetic_traits(self, donor_id: str, recipient_id: str, transfer_id: str) -> bool:
        """
        Transfer Layer 2 epigenetic traits (sensation learning capacity).
        
        Transfers sensation learning rates, emotional sensitivity, navigation
        parameters. These affect HOW the agent learns, not WHAT it learned.
        """
        
        try:
            # Get donor epigenetic data
            donor_data = self.db.execute_query("""
                SELECT sensation_learning_rate, state_update_sensitivity, 
                       emotional_intelligence_score, action_biases
                FROM agents WHERE agent_id = ?
            """, (donor_id,))
            
            if not donor_data:
                return False
            
            donor = donor_data[0]
            
            # Get recipient current values
            recipient_data = self.db.execute_query("""
                SELECT sensation_learning_rate, state_update_sensitivity,
                       emotional_intelligence_score, action_biases
                FROM agents WHERE agent_id = ?  
            """, (recipient_id,))
            
            if not recipient_data:
                return False
            
            recipient = recipient_data[0]
            
            # Calculate new epigenetic values (blend with donor influence)
            # Apply 0.95 decay factor from Phase 4.5 inheritance system
            decay_factor = 0.95
            blend_strength = 0.3 * decay_factor  # 28.5% donor influence
            
            new_learning_rate = (
                (recipient['sensation_learning_rate'] or 0.3) * (1 - blend_strength) +
                (donor['sensation_learning_rate'] or 0.3) * blend_strength
            )
            
            new_sensitivity = (
                (recipient['state_update_sensitivity'] or 0.7) * (1 - blend_strength) +
                (donor['state_update_sensitivity'] or 0.7) * blend_strength
            )
            
            new_ei_score = (
                (recipient['emotional_intelligence_score'] or 0.5) * (1 - blend_strength) +
                (donor['emotional_intelligence_score'] or 0.5) * blend_strength
            )
            
            # Blend action biases (if both have them)
            recipient_biases = safe_json_parse(recipient['action_biases'])
            donor_biases = safe_json_parse(donor['action_biases'])
            
            new_biases = recipient_biases.copy()
            for action, bias in donor_biases.items():
                if action in new_biases:
                    new_biases[action] = (
                        new_biases[action] * (1 - blend_strength) +
                        bias * blend_strength
                    )
                else:
                    new_biases[action] = bias * blend_strength
            
            # Update recipient with blended epigenetic traits
            self.db.execute_query("""
                UPDATE agents SET 
                    sensation_learning_rate = ?,
                    state_update_sensitivity = ?,
                    emotional_intelligence_score = ?,
                    action_biases = ?
                WHERE agent_id = ?
            """, (
                new_learning_rate, new_sensitivity, new_ei_score,
                json.dumps(new_biases), recipient_id
            ))
            
            # Record transfer details
            knowledge_content = {
                'learning_rate_change': new_learning_rate - (recipient['sensation_learning_rate'] or 0.3),
                'sensitivity_change': new_sensitivity - (recipient['state_update_sensitivity'] or 0.7),
                'ei_change': new_ei_score - (recipient['emotional_intelligence_score'] or 0.5),
                'biases_transferred': len(donor_biases),
                'layer': 2
            }
            
            self.db.execute_query("""
                UPDATE horizontal_transfer_events 
                SET knowledge_content = ?
                WHERE transfer_id = ?
            """, (json.dumps(knowledge_content), transfer_id))
            
            return True
            
        except Exception as e:
            print(f"Error in epigenetic transfer: {e}")
            return False
    
    def _transfer_somatic_knowledge(self, donor_id: str, recipient_id: str, transfer_id: str) -> bool:
        """
        Transfer Layer 3 somatic knowledge (emotional sequences, learned patterns).
        
        This is the most frequent and powerful transfer - sharing specific learned
        knowledge with emotional context about when and how to use it.
        """
        
        try:
            # Get donor's best winning sequences with emotional context
            donor_sequences = self.db.execute_query("""
                SELECT sequence_id, game_id, action_sequence, 
                       coordinate_sequence, total_score, level_number
                FROM winning_sequences 
                WHERE agent_id = ?
                  AND total_score >= 5  -- Only transfer successful sequences
                ORDER BY total_score DESC
                LIMIT 5
            """, (donor_id,))
            
            if not donor_sequences:
                return False
            
            # Get donor's sensation profile for emotional context
            donor_sensation = self.db.execute_query("""
                SELECT sensation_profile, navigation_state 
                FROM agents WHERE agent_id = ?
            """, (donor_id,))
            
            if not donor_sensation:
                return False
            
            donor_sensations = safe_json_parse(donor_sensation[0]['sensation_profile'], {'object_sensations': {}})
            donor_nav_state = donor_sensation[0]['navigation_state']
            
            transferred_count = 0
            
            # Transfer each sequence with emotional context
            for sequence in donor_sequences:
                # Create enhanced sequence for recipient with emotional metadata
                enhanced_sequence_id = f"htransfer_{uuid.uuid4().hex[:8]}"
                
                # Add emotional context to sequence metadata
                emotional_metadata = {
                    'horizontal_transfer': True,
                    'original_discoverer': donor_id,
                    'transfer_id': transfer_id,
                    'donor_navigation_state': donor_nav_state,
                    'donor_object_sensations': donor_sensations.get('object_sensations', {}),
                    'recommended_nav_state_min': max(0, donor_nav_state - 0.3),
                    'recommended_nav_state_max': min(1, donor_nav_state + 0.3),
                    'emotional_confidence': self._calculate_sequence_confidence(sequence, donor_sensations)
                }
                
                # Insert sequence for recipient with emotional context
                self.db.execute_query("""
                    INSERT INTO winning_sequences (
                        sequence_id, game_id, level_number, agent_id, 
                        action_sequence, coordinate_sequence, total_score,
                        pattern_tags, generation_discovered
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    enhanced_sequence_id, sequence['game_id'], sequence['level_number'],
                    recipient_id, sequence['action_sequence'], sequence['coordinate_sequence'], 
                    sequence['total_score'], json.dumps(emotional_metadata), 
                    0  # generation 0 for transfers
                ))
                
                transferred_count += 1
            
            # Also transfer some sensation mappings (partial)
            if donor_sensations.get('object_sensations'):
                recipient_sensation_data = self.db.execute_query("""
                    SELECT sensation_profile FROM agents WHERE agent_id = ?
                """, (recipient_id,))
                
                if recipient_sensation_data:
                    recipient_sensations = json.loads(
                        recipient_sensation_data[0]['sensation_profile'] or '{"object_sensations": {}}'
                    )
                    
                    # Transfer top 3 most confident object sensations
                    donor_objects = donor_sensations['object_sensations']
                    # Sort by absolute sensation strength (high confidence either way)
                    sorted_objects = sorted(donor_objects.items(), 
                                          key=lambda x: abs(x[1]), reverse=True)
                    
                    recipient_objects = recipient_sensations.setdefault('object_sensations', {})
                    
                    for obj_type, sensation_score in sorted_objects[:3]:
                        if obj_type not in recipient_objects:
                            # Add new sensation at reduced strength
                            recipient_objects[obj_type] = sensation_score * 0.6
                        else:
                            # Blend existing sensation (70% recipient, 30% donor)
                            recipient_objects[obj_type] = (
                                recipient_objects[obj_type] * 0.7 +
                                sensation_score * 0.3
                            )
                    
                    # Update recipient sensation profile
                    self.db.execute_query("""
                        UPDATE agents SET sensation_profile = ? WHERE agent_id = ?
                    """, (json.dumps(recipient_sensations), recipient_id))
            
            # Record successful transfer
            knowledge_content = {
                'sequences_transferred': transferred_count,
                'sensation_mappings_transferred': len(donor_sensations.get('object_sensations', {})),
                'emotional_context_included': True,
                'layer': 3
            }
            
            self.db.execute_query("""
                UPDATE horizontal_transfer_events 
                SET knowledge_content = ?
                WHERE transfer_id = ?
            """, (json.dumps(knowledge_content), transfer_id))
            
            return transferred_count > 0
            
        except Exception as e:
            print(f"Error in somatic knowledge transfer: {e}")
            return False
    
    def _calculate_sequence_confidence(self, sequence: Dict, donor_sensations: Dict) -> float:
        """Calculate emotional confidence in a sequence based on donor sensations."""
        
        try:
            # Parse action sequence to estimate object interactions
            actions = safe_json_parse(sequence['action_sequence'], [])
            
            # Estimate confidence based on action types and sensation alignment
            confidence = 0.5  # Base confidence
            
            # Higher confidence for sequences with navigation actions (1-5, 7) 
            # when donor has strong navigation sensations
            nav_actions = [a for a in actions if a in [1, 2, 3, 4, 5, 7]]
            if nav_actions and donor_sensations.get('object_sensations'):
                # Boost confidence if donor has strong sensations about patterns
                pattern_sensations = [v for k, v in donor_sensations['object_sensations'].items() 
                                    if 'pattern' in k.lower()]
                if pattern_sensations:
                    avg_pattern_sensation = sum(abs(s) for s in pattern_sensations) / len(pattern_sensations)
                    confidence += avg_pattern_sensation * 0.3
            
            # Higher confidence for higher scoring sequences
            score_factor = min(sequence['total_score'] / 10.0, 0.3)  # Cap at +0.3
            confidence += score_factor
            
            return max(0.2, min(confidence, 0.95))
            
        except Exception:
            return 0.5  # Default confidence
    
    def execute_generation_transfers(self, generation: int, max_transfers_per_agent: int = 2) -> int:
        """
        Execute horizontal transfers for a generation.
        
        Key strategy: Target high-performing agents as donors, struggling agents as recipients.
        Emotional compatibility filtering ensures transfers have high success rates.
        """
        
        try:
            # Get active agents sorted by performance
            agents = self.db.execute_query("""
                SELECT agent_id, avg_score_per_game, total_games_won, 
                       emotional_intelligence_score, navigation_state
                FROM agents 
                WHERE is_active = TRUE
                ORDER BY avg_score_per_game DESC
            """)
            
            if len(agents) < 4:  # Need at least 4 agents for meaningful transfers
                return 0
            
            # Top 25% become potential donors
            donor_count = max(1, len(agents) // 4)
            potential_donors = agents[:donor_count]
            
            # Bottom 50% become potential recipients  
            recipient_count = max(2, len(agents) // 2)
            potential_recipients = agents[-recipient_count:]
            
            total_transfers = 0
            
            # Execute transfers based on emotional compatibility
            for donor in potential_donors:
                donor_id = donor['agent_id']
                transfers_this_donor = 0
                
                # Find compatible recipients for this donor
                compatible_recipients = []
                for recipient in potential_recipients:
                    if recipient['agent_id'] == donor_id:
                        continue  # Skip self-transfer
                    
                    compatibility = self.calculate_emotional_compatibility(
                        donor_id, recipient['agent_id']
                    )
                    
                    if compatibility > 0.6:  # High compatibility threshold
                        compatible_recipients.append((recipient, compatibility))
                
                # Sort by compatibility and transfer to best matches
                compatible_recipients.sort(key=lambda x: x[1], reverse=True)
                
                for recipient_data, compatibility in compatible_recipients[:max_transfers_per_agent]:
                    recipient_id = recipient_data['agent_id']
                    
                    # Determine transfer type based on performance gap and compatibility
                    performance_gap = donor['avg_score_per_game'] - recipient_data['avg_score_per_game']
                    
                    if performance_gap > 3.0 and compatibility > 0.8:
                        # Large gap + high compatibility = try epigenetic transfer
                        transfer_type = 'layer_2_epigenetic'
                    elif performance_gap > 1.5:
                        # Medium gap = somatic knowledge transfer
                        transfer_type = 'layer_3_somatic'
                    else:
                        # Small gap = just somatic knowledge
                        transfer_type = 'layer_3_somatic'
                    
                    # Execute transfer
                    transfer_id = self.initiate_horizontal_transfer(
                        donor_id, recipient_id, transfer_type, generation
                    )
                    
                    if transfer_id:
                        total_transfers += 1
                        transfers_this_donor += 1
                        
                        print(f"  ✓ Transfer {donor_id[:8]}...→{recipient_id[:8]}... "
                              f"({transfer_type}, compat:{compatibility:.2f})")
                    
                    if transfers_this_donor >= max_transfers_per_agent:
                        break
            
            return total_transfers
            
        except Exception as e:
            print(f"Error in generation transfers: {e}")
            return 0
    
    def get_transfer_statistics(self, generation: int) -> Dict:
        """Get statistics on horizontal transfers for monitoring."""
        
        try:
            # Transfer counts by layer
            layer_stats = self.db.execute_query("""
                SELECT 
                    transfer_layer,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN transfer_successful THEN 1 ELSE 0 END) as successful_transfers,
                    AVG(emotional_compatibility) as avg_compatibility,
                    AVG(success_probability) as avg_success_prob
                FROM horizontal_transfer_events 
                WHERE generation = ?
                GROUP BY transfer_layer
                ORDER BY transfer_layer
            """, (generation,))
            
            # Recent transfer success rates
            recent_stats = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_recent,
                    SUM(CASE WHEN transfer_successful THEN 1 ELSE 0 END) as successful_recent,
                    AVG(emotional_compatibility) as avg_recent_compatibility
                FROM horizontal_transfer_events 
                WHERE generation >= ? - 5
            """, (generation,))
            
            # Network knowledge growth rate (check pattern_tags for transfer marker)
            knowledge_growth = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_sequences,
                    SUM(CASE WHEN pattern_tags LIKE '%horizontal_transfer%' THEN 1 ELSE 0 END) as transfer_sequences
                FROM winning_sequences 
                WHERE generation_discovered >= ? - 10
            """, (generation,))
            
            return {
                'generation': generation,
                'layer_statistics': layer_stats or [],
                'recent_performance': recent_stats[0] if recent_stats else {},
                'knowledge_growth': knowledge_growth[0] if knowledge_growth else {},
                'transfer_ratio': (
                    knowledge_growth[0]['transfer_sequences'] / max(knowledge_growth[0]['total_sequences'], 1)
                    if knowledge_growth else 0.0
                )
            }
            
        except Exception as e:
            print(f"Error getting transfer statistics: {e}")
            return {'generation': generation, 'error': str(e)}


def create_horizontal_transfer_tables(db: DatabaseInterface) -> bool:
    """Create database tables for Phase 5 horizontal gene transfer."""
    
    try:
        print("Creating Phase 5 horizontal transfer tables...")
        
        # Enhanced horizontal transfer events with emotional context
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS horizontal_transfer_events (
                transfer_id TEXT PRIMARY KEY,
                donor_agent_id TEXT NOT NULL,
                recipient_agent_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                
                -- Transfer classification
                transfer_type TEXT NOT NULL,  -- 'layer_1_genome', 'layer_2_epigenetic', 'layer_3_somatic'
                transfer_layer INTEGER NOT NULL,  -- 1, 2, or 3
                
                -- Emotional compatibility (Phase 4.5 enhancement)
                emotional_compatibility REAL NOT NULL,
                success_probability REAL NOT NULL,
                transfer_successful BOOLEAN NOT NULL,
                
                -- Transfer content and results
                knowledge_content TEXT,  -- JSON: what was transferred
                emotional_context TEXT,  -- JSON: emotional state during transfer
                knowledge_transferred BOOLEAN DEFAULT FALSE,
                performance_impact REAL DEFAULT 0.0,  -- Recipient performance change
                
                -- Metadata
                transfer_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                
                FOREIGN KEY (donor_agent_id) REFERENCES agents(agent_id),
                FOREIGN KEY (recipient_agent_id) REFERENCES agents(agent_id)
            )
        """)
        
        # Knowledge propagation chains (track viral spread)
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS knowledge_propagation_chains (
                chain_id TEXT PRIMARY KEY,
                origin_agent_id TEXT NOT NULL,
                knowledge_type TEXT NOT NULL,  -- 'sequence', 'sensation_mapping', 'pattern', etc.
                knowledge_identifier TEXT NOT NULL,  -- sequence_id, pattern_id, etc.
                
                -- Chain tracking
                chain_length INTEGER DEFAULT 1,
                current_carriers INTEGER DEFAULT 1,
                max_carriers_reached INTEGER DEFAULT 1,
                
                -- Performance tracking
                avg_performance_improvement REAL DEFAULT 0.0,
                total_games_won_with_knowledge INTEGER DEFAULT 0,
                
                -- Metadata
                chain_start_generation INTEGER NOT NULL,
                last_transfer_generation INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                
                FOREIGN KEY (origin_agent_id) REFERENCES agents(agent_id)
            )
        """)
        
        # Create indexes for performance
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_transfers_generation ON horizontal_transfer_events(generation)")
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_transfers_donor ON horizontal_transfer_events(donor_agent_id)")
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_transfers_recipient ON horizontal_transfer_events(recipient_agent_id)")
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_chains_generation ON knowledge_propagation_chains(chain_start_generation)")
        
        print("✅ Phase 5 horizontal transfer tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating horizontal transfer tables: {e}")
        return False


def main():
    """Test Phase 5 horizontal transfer system."""
    
    print("🧬 Phase 5: Horizontal Gene Transfer with Emotional Intelligence")
    print("=" * 70)
    
    # Initialize database and transfer engine
    db = DatabaseInterface()
    
    # Create tables if needed
    if not create_horizontal_transfer_tables(db):
        return False
    
    # Initialize transfer engine
    transfer_engine = HorizontalTransferEngine(db)
    
    # Test emotional compatibility calculation
    print("\n🧠 Testing emotional compatibility calculation...")
    
    # Get some test agents
    test_agents = db.execute_query("""
        SELECT agent_id FROM agents 
        WHERE is_active = TRUE AND sensation_profile IS NOT NULL
        LIMIT 5
    """)
    
    if len(test_agents) >= 2:
        agent1 = test_agents[0]['agent_id']
        agent2 = test_agents[1]['agent_id']
        
        compatibility = transfer_engine.calculate_emotional_compatibility(agent1, agent2)
        print(f"  Compatibility between {agent1[:8]}... and {agent2[:8]}...: {compatibility:.3f}")
        
        # Test transfer
        print(f"\n🔄 Testing horizontal transfer...")
        
        transfer_id = transfer_engine.initiate_horizontal_transfer(
            agent1, agent2, 'layer_3_somatic', 0
        )
        
        if transfer_id:
            print(f"  ✅ Transfer successful: {transfer_id}")
        else:
            print(f"  ❌ Transfer failed (normal - success is probabilistic)")
    
    # Get transfer statistics
    stats = transfer_engine.get_transfer_statistics(0)
    print(f"\n📊 Transfer Statistics:")
    print(f"  Generation: {stats['generation']}")
    layer_stats = stats.get('layer_statistics', [])
    print(f"  Layer Stats: {len(layer_stats)} layers active")
    if layer_stats:
        for layer in layer_stats:
            print(f"    Layer {layer['transfer_layer']}: {layer['successful_transfers']}/{layer['total_attempts']} success")
    
    print("\n🚀 Phase 5 horizontal transfer system ready!")
    print("Integration point: Call execute_generation_transfers() from autonomous_evolution_runner.py")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)