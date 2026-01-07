#!/usr/bin/env python3
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Sensation Engine - Phase 4.5 Emotional Intelligence System

Core system for sensation-based navigation that adds emotional context to actions 1-7.
Agents learn "how to feel" about different objects and situations, enabling
context-aware navigation that dramatically improves learning and knowledge transfer.

Key Innovation: Actions get semantic understanding through sensation scores.
- Perceive object → Recall sensation → Update internal state → Bias action → Act → Learn from outcome

This creates the missing "sensation layer" in the biome theory - like bacterial
chemotaxis but for ARC patterns and objects.

Database Rule: All sensation tracking stored in SQLite database.
Environment Rule: Set PYTHONDONTWRITEBYTECODE=1 to prevent .pyc files.
Integration Rule: Enhance existing systems, don't replace them.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be FIRST before other imports

import json
import math
import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from database_interface import DatabaseInterface

def safe_json_parse(json_str, default=None):
    """Safely parse JSON string, returning default if invalid or empty."""
    if not json_str or json_str.strip() == '':
        return default or {}
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default or {}


def get_sensation_mode(agent_role: str, is_frontier: bool) -> dict:
    """
    Determine sensation configuration based on role and context.
    
    Per AGI Unified Theory: Sensation is a "multiplier" for learning.
    Q2 (reward/punishment) requires sensation for ALL agents.
    
    Pioneers on frontier: Network sensation isolated (no inherited bias),
    but personal sensation active (can feel rewards/punishments).
    
    Args:
        agent_role: 'pioneer', 'optimizer', 'generalist', 'exploiter'
        is_frontier: True if on unexplored level (network_max < current_level)
        
    Returns:
        dict with sensation mode configuration:
        - network_sensation_read: Whether to read from network mappings
        - personal_sensation_active: Whether to feel rewards/punishments
        - sensation_write_to_network: Whether to export discoveries
    """
    if agent_role == 'pioneer':
        if is_frontier:
            # Pioneer on frontier: isolated from network bias, but can feel
            return {
                'network_sensation_read': False,   # Don't inherit biases
                'personal_sensation_active': True,  # Feel rewards/punishments
                'sensation_write_to_network': True  # Export discoveries when solved
            }
        else:
            # Pioneer on beaten level: acts like generalist
            return {
                'network_sensation_read': True,
                'personal_sensation_active': True,
                'sensation_write_to_network': True
            }
    elif agent_role == 'optimizer':
        return {
            'network_sensation_read': True,
            'personal_sensation_active': True,
            'sensation_write_to_network': True
        }
    elif agent_role == 'exploiter':
        return {
            'network_sensation_read': True,
            'personal_sensation_active': True,
            'sensation_write_to_network': True
        }
    else:  # generalist or unknown
        return {
            'network_sensation_read': True,
            'personal_sensation_active': True,
            'sensation_write_to_network': True
        }

class SensationEngine:
    """
    Core engine for sensation-based navigation and emotional learning.
    
    Implements the sensation-object mapping system where agents develop
    emotional associations with different game elements and use these
    emotions to bias their navigation actions (1-7).
    
    Three-Layer Integration:
    - Layer 1 (Genome): Basic sensation sensitivity (inherited)
    - Layer 2 (Epigenetic): Sensation learning rates, biases (inherited with decay)
    - Layer 3 (Somatic): Specific object-sensation mappings (community database)
    """
    
    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        
        # Sensation parameters
        self.sensation_range = (-1.0, 1.0)  # Negative=avoid, Positive=approach
        self.learning_rate_base = 0.3  # Base learning rate for sensation updates
        self.state_decay_rate = 0.1  # How fast navigation state decays to neutral
        self.confidence_threshold = 0.6  # Minimum confidence for strong biasing
        
        # Action mapping for navigation (1-7 only)
        self.navigation_actions = {1, 2, 3, 4, 5, 6, 7}
        
        # Emotional states mapping
        self.emotion_states = {
            (-1.0, -0.5): 'frustrated',
            (-0.5, -0.1): 'cautious', 
            (-0.1, 0.1): 'neutral',
            (0.1, 0.5): 'curious',
            (0.5, 1.0): 'confident'
        }
    
    def initialize_agent_sensations(self, agent_id: str, agent_type: str) -> Dict[str, Any]:
        """
        Initialize sensation profile for new agent based on agent type.
        
        Creates initial object-sensation mappings and navigation parameters.
        These go into Layer 2 (epigenetic) - inherited but with decay.
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Agent type determines initial sensation biases
            
        Returns:
            Dictionary with initialized sensation profile
        """
        
        # Base sensation profile structure
        sensation_profile = {
            'object_sensations': {},
            'navigation_preferences': {},
            'learning_history': {
                'total_sensation_events': 0,
                'successful_learnings': 0,
                'emotional_intelligence_score': 0.0
            }
        }
        
        # Agent type-specific sensation initialization
        type_biases = {
            'pattern_specialist': {
                'geometric_shapes': 0.3,
                'color_patterns': 0.2,
                'spatial_relationships': 0.4
            },
            'score_optimizer': {
                'high_value_targets': 0.5,
                'score_multipliers': 0.4,
                'efficiency_indicators': 0.3
            },
            'exploration_agent': {
                'unknown_objects': 0.2,
                'complex_patterns': 0.1,
                'novel_configurations': 0.3
            },
            'win_focused_agent': {
                'completion_indicators': 0.6,
                'progress_markers': 0.4,
                'solution_patterns': 0.5
            }
        }
        
        # Initialize with type-specific biases
        if agent_type in type_biases:
            sensation_profile['object_sensations'] = type_biases[agent_type].copy()
        else:
            # Default neutral sensations
            sensation_profile['object_sensations'] = {
                'unknown_object': 0.0,
                'familiar_pattern': 0.1
            }
        
        # Navigation action preferences (random initialization)
        sensation_profile['navigation_preferences'] = {
            str(action): random.uniform(-0.2, 0.2) for action in self.navigation_actions
        }
        
        return sensation_profile
    
    def perceive_object(self, agent_id: str, object_type: str, object_data: Dict[str, Any]) -> float:
        """
        Agent perceives an object and recalls associated sensation score.
        
        This is the "Perceive → Recall" step in the sensation loop.
        
        Args:
            agent_id: Agent doing the perceiving
            object_type: Type of object being perceived
            object_data: Object characteristics (color, size, etc.)
            
        Returns:
            Sensation score for this object (-1.0 to 1.0)
        """
        
        # Get agent's sensation profile
        agent_result = self.db.execute_query(
            "SELECT sensation_profile FROM agents WHERE agent_id = ?",
            (agent_id,)
        )
        
        if not agent_result:
            return 0.0  # Neutral if agent not found
        
        sensation_profile = safe_json_parse(agent_result[0]['sensation_profile'])
        object_sensations = sensation_profile.get('object_sensations', {})
        
        # Direct object type match
        if object_type in object_sensations:
            return object_sensations[object_type]
        
        # Fuzzy matching based on object characteristics
        sensation_score = 0.0
        match_count = 0
        
        for known_object, known_score in object_sensations.items():
            # Simple similarity check (can be enhanced later)
            if object_type.lower() in known_object.lower() or known_object.lower() in object_type.lower():
                sensation_score += known_score
                match_count += 1
        
        if match_count > 0:
            sensation_score /= match_count
        
        # Clamp to sensation range
        return max(self.sensation_range[0], min(self.sensation_range[1], sensation_score))
    
    def update_navigation_state(self, agent_id: str, sensation_score: float, context: Dict[str, Any]) -> float:
        """
        Update agent's internal navigation state based on sensation.
        
        This is the "Update internal state" step in the sensation loop.
        
        Args:
            agent_id: Agent whose state to update
            sensation_score: Sensation from perceiving object
            context: Game context (score, recent success, etc.)
            
        Returns:
            New navigation state (-1.0 to 1.0)
        """
        
        # Get current navigation state
        agent_result = self.db.execute_query(
            "SELECT navigation_state, state_update_sensitivity FROM agents WHERE agent_id = ?",
            (agent_id,)
        )
        
        if not agent_result:
            return 0.0
        
        current_state = agent_result[0]['navigation_state']
        sensitivity = agent_result[0]['state_update_sensitivity']
        
        # Calculate state change based on sensation and context
        sensation_influence = sensation_score * sensitivity
        
        # Context modifiers
        context_modifier = 0.0
        if 'recent_success_rate' in context:
            success_rate = context['recent_success_rate']
            if success_rate > 0.7:
                context_modifier = 0.2  # Success boosts confidence
            elif success_rate < 0.3:
                context_modifier = -0.2  # Failure increases frustration
        
        # Update navigation state with decay toward neutral
        new_state = current_state * (1.0 - self.state_decay_rate) + sensation_influence + context_modifier
        
        # Clamp to valid range
        new_state = max(-1.0, min(1.0, new_state))
        
        # Store new state in database
        self.db.execute_query(
            "UPDATE agents SET navigation_state = ? WHERE agent_id = ?",
            (new_state, agent_id)
        )
        
        # Log navigation state change
        emotion = self._get_emotion_from_state(new_state)
        state_change_trigger = f"sensation_{sensation_score:.2f}_context_{context_modifier:.2f}"
        
        self.db.execute_query("""
            INSERT INTO navigation_state_history 
            (history_id, agent_id, game_id, generation, navigation_state, dominant_emotion, 
             state_change_trigger, previous_state, state_change_magnitude, game_score, recent_success_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), agent_id, context.get('game_id', ''), context.get('generation', 0),
            new_state, emotion, state_change_trigger, current_state, abs(new_state - current_state),
            context.get('game_score', 0), context.get('recent_success_rate', None)
        ))
        
        return new_state
    
    def bias_action_selection(self, agent_id: str, available_actions: List[int], navigation_state: float) -> List[Tuple[int, float]]:
        """
        Apply sensation-based biasing to action selection for navigation actions (1-7).
        
        This is the "Bias action" step in the sensation loop.
        
        Args:
            agent_id: Agent selecting actions
            available_actions: List of available action numbers
            navigation_state: Current emotional state of agent
            
        Returns:
            List of (action, bias_score) tuples for navigation actions only
        """
        
        # Filter to navigation actions only (1-7)
        nav_actions = [action for action in available_actions if action in self.navigation_actions]
        
        if not nav_actions:
            return []
        
        # Get agent's action preferences
        agent_result = self.db.execute_query(
            "SELECT action_biases FROM agents WHERE agent_id = ?",
            (agent_id,)
        )
        
        if not agent_result:
            return [(action, 0.0) for action in nav_actions]
        
        action_biases = safe_json_parse(agent_result[0]['action_biases'])
        
        # Calculate biased action preferences
        biased_actions = []
        
        for action in nav_actions:
            # Base bias from learned preferences
            base_bias = action_biases.get(str(action), 0.0)
            
            # Emotional state influence
            emotional_modifier = self._calculate_emotional_modifier(action, navigation_state)
            
            # Combined bias score
            total_bias = base_bias + emotional_modifier
            
            biased_actions.append((action, total_bias))
        
        return biased_actions
    
    def learn_from_outcome(self, agent_id: str, object_type: str, action_taken: int, 
                          outcome: Dict[str, Any], navigation_state: float) -> bool:
        """
        Learn from action outcome and update sensation mappings.
        
        This is the "Learn from outcome" step in the sensation loop.
        
        Args:
            agent_id: Agent that took the action
            object_type: Object that was acted upon
            action_taken: Action number that was executed
            outcome: Action outcome (success, score_change, etc.)
            navigation_state: Emotional state when action was taken
            
        Returns:
            True if learning occurred, False otherwise
        """
        
        if action_taken not in self.navigation_actions:
            return False  # Only learn from navigation actions
        
        # Calculate reward signal
        reward = self._calculate_reward_signal(outcome)
        
        # Get current sensation mapping for this object
        current_sensation = self.perceive_object(agent_id, object_type, {})
        
        # Calculate sensation adjustment based on reward and confidence
        agent_result = self.db.execute_query(
            "SELECT sensation_learning_rate FROM agents WHERE agent_id = ?",
            (agent_id,)
        )
        
        if not agent_result:
            return False
        
        learning_rate = agent_result[0]['sensation_learning_rate']
        
        # Positive reward strengthens positive sensation, negative reward creates negative sensation
        target_sensation = 0.5 * reward  # Scale reward to sensation range
        sensation_adjustment = learning_rate * (target_sensation - current_sensation)
        
        # Update object sensation mapping
        new_sensation = current_sensation + sensation_adjustment
        new_sensation = max(self.sensation_range[0], min(self.sensation_range[1], new_sensation))
        
        self._update_object_sensation_mapping(agent_id, object_type, new_sensation, outcome)
        
        # Update action bias
        self._update_action_bias(agent_id, action_taken, reward, navigation_state)
        
        # Log learning event
        learning_success = abs(sensation_adjustment) > 0.05  # Significant learning threshold
        
        self.db.execute_query("""
            INSERT INTO sensation_learning_events
            (event_id, agent_id, game_id, generation, object_type, pre_sensation_score, 
             post_sensation_score, pre_navigation_state, post_navigation_state, action_taken, 
             reward_received, sensation_adjustment, learning_success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), agent_id, outcome.get('game_id', ''), outcome.get('generation', 0),
            object_type, current_sensation, new_sensation, navigation_state, navigation_state,
            action_taken, reward, sensation_adjustment, learning_success
        ))
        
        return learning_success
    
    def get_agent_emotional_intelligence(self, agent_id: str) -> float:
        """
        Calculate agent's current emotional intelligence score.
        
        Based on sensation learning effectiveness, consistency, and adaptability.
        
        Args:
            agent_id: Agent to assess
            
        Returns:
            Emotional intelligence score (0.0 to 1.0)
        """
        
        # Get learning statistics
        learning_stats = self.db.execute_query("""
            SELECT 
                COUNT(*) as total_events,
                AVG(CASE WHEN learning_success THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(ABS(sensation_adjustment)) as avg_adjustment,
                COUNT(DISTINCT object_type) as object_diversity
            FROM sensation_learning_events 
            WHERE agent_id = ? AND event_timestamp > datetime('now', '-24 hours')
        """, (agent_id,))
        
        if not learning_stats or learning_stats[0]['total_events'] == 0:
            return 0.0
        
        stats = learning_stats[0]
        
        # Calculate EI components
        learning_effectiveness = stats['success_rate']  # How often learning is successful
        learning_activity = min(1.0, stats['total_events'] / 10.0)  # Learning frequency (capped)
        adaptability = min(1.0, stats['avg_adjustment'] * 5.0)  # How much agent adapts (capped)
        diversity = min(1.0, stats['object_diversity'] / 5.0)  # Object type diversity (capped)
        
        # Weighted EI score
        ei_score = (
            learning_effectiveness * 0.4 +
            learning_activity * 0.2 +
            adaptability * 0.2 +
            diversity * 0.2
        )
        
        # Update agent's EI score in database
        self.db.execute_query(
            "UPDATE agents SET emotional_intelligence_score = ? WHERE agent_id = ?",
            (ei_score, agent_id)
        )
        
        return ei_score
    
    def get_agent_sensation_state(self, agent_id: str) -> Optional[Dict[str, float]]:
        """
        Get agent's current sensation/emotional state.
        
        Returns frustration and satisfaction levels derived from navigation_state.
        Navigation state ranges from -1.0 (frustrated) to +1.0 (satisfied).
        
        Args:
            agent_id: Agent to query
            
        Returns:
            Dictionary with 'frustration' and 'satisfaction' (0.0 to 1.0 each),
            or None if agent not found
        """
        try:
            result = self.db.execute_query(
                "SELECT navigation_state FROM agents WHERE agent_id = ?",
                (agent_id,)
            )
            
            if not result:
                return None
            
            nav_state = result[0].get('navigation_state', 0.0) or 0.0
            
            # Convert navigation_state (-1 to +1) to frustration/satisfaction (0 to 1)
            # Negative nav_state = frustration, positive = satisfaction
            if nav_state < 0:
                frustration = abs(nav_state)  # -0.5 -> 0.5 frustration
                satisfaction = 0.0
            else:
                frustration = 0.0
                satisfaction = nav_state  # +0.5 -> 0.5 satisfaction
            
            return {
                'frustration': frustration,
                'satisfaction': satisfaction,
                'navigation_state': nav_state
            }
            
        except Exception as e:
            logger.debug(f"Failed to get agent sensation state: {e}")
            return None
    
    def get_network_emotional_intelligence(self, generation: Optional[int] = None) -> Dict[str, float]:
        """
        Calculate network-level emotional intelligence metrics.
        
        Assesses collective emotional learning and sensation-based capabilities.
        
        Args:
            generation: Generation to analyze (None for current)
            
        Returns:
            Dictionary with network EI metrics
        """
        
        generation_filter = ""
        params = []
        
        if generation is not None:
            generation_filter = "AND generation = ?"
            params.append(generation)
        
        # Network learning metrics
        network_stats = self.db.execute_query(f"""
            SELECT 
                AVG(emotional_intelligence_score) as avg_ei_score,
                COUNT(DISTINCT agent_id) as active_agents,
                AVG(sensation_learning_rate) as avg_learning_rate,
                AVG(ABS(navigation_state)) as avg_emotional_intensity
            FROM agents 
            WHERE is_active = TRUE {generation_filter}
        """, tuple(params))
        
        # Recent learning activity
        learning_activity = self.db.execute_query(f"""
            SELECT 
                COUNT(*) as total_events,
                AVG(CASE WHEN learning_success THEN 1.0 ELSE 0.0 END) as network_success_rate,
                COUNT(DISTINCT agent_id) as learning_agents,
                COUNT(DISTINCT object_type) as object_diversity
            FROM sensation_learning_events
            WHERE event_timestamp > datetime('now', '-1 hour') {generation_filter}
        """, tuple(params))
        
        if not network_stats or not learning_activity:
            return {
                'network_ei_score': 0.0,
                'emotional_activity': 0.0,
                'learning_diversity': 0.0,
                'network_coherence': 0.0
            }
        
        net_stats = network_stats[0]
        learning_stats = learning_activity[0]
        
        # Calculate network EI metrics
        network_ei = net_stats['avg_ei_score'] or 0.0
        emotional_activity = min(1.0, (learning_stats['total_events'] or 0) / 50.0)
        learning_diversity = min(1.0, (learning_stats['object_diversity'] or 0) / 10.0)
        
        # Network coherence: how aligned are emotional states
        coherence_stats = self.db.execute_query(f"""
            SELECT 
                (1.0 - (MAX(navigation_state) - MIN(navigation_state)) / 2.0) as coherence
            FROM agents 
            WHERE is_active = TRUE {generation_filter}
        """, tuple(params))
        
        network_coherence = coherence_stats[0]['coherence'] if coherence_stats else 0.0
        
        return {
            'network_ei_score': network_ei,
            'emotional_activity': emotional_activity,
            'learning_diversity': learning_diversity,
            'network_coherence': max(0.0, network_coherence),
            'active_agents': net_stats['active_agents'] or 0,
            'learning_agents': learning_stats['learning_agents'] or 0
        }
    
    def _get_emotion_from_state(self, navigation_state: float) -> str:
        """Get emotion label from navigation state value."""
        for (min_val, max_val), emotion in self.emotion_states.items():
            if min_val <= navigation_state < max_val:
                return emotion
        return 'neutral'
    
    def _calculate_emotional_modifier(self, action: int, navigation_state: float) -> float:
        """Calculate how emotional state modifies action preferences."""
        
        # Action-specific emotional modifiers
        action_emotion_map = {
            1: {'confident': 0.3, 'frustrated': -0.2},  # Move up - confident agents prefer
            2: {'confident': 0.3, 'frustrated': -0.2},  # Move down
            3: {'curious': 0.4, 'cautious': -0.1},      # Move left - exploration
            4: {'curious': 0.4, 'cautious': -0.1},      # Move right - exploration
            5: {'cautious': 0.3, 'frustrated': -0.3},   # Stay - cautious preference
            6: {'confident': 0.5, 'frustrated': 0.2},   # Submit - confident or desperate
            7: {'frustrated': 0.4, 'confident': -0.1}   # Reset - frustration response
        }
        
        emotion = self._get_emotion_from_state(navigation_state)
        action_modifiers = action_emotion_map.get(action, {})
        
        return action_modifiers.get(emotion, 0.0)
    
    def _calculate_reward_signal(self, outcome: Dict[str, Any]) -> float:
        """Calculate reward signal from action outcome."""
        
        reward = 0.0
        
        # Score-based reward
        if 'score_change' in outcome:
            score_change = outcome['score_change']
            reward += score_change * 0.01  # Scale score to reward range
        
        # Success-based reward
        if 'action_success' in outcome:
            reward += 1.0 if outcome['action_success'] else -0.5
        
        # Game completion reward
        if 'game_won' in outcome and outcome['game_won']:
            reward += 2.0
        
        # Clamp to reasonable range
        return max(-2.0, min(2.0, reward))
    
    def _update_object_sensation_mapping(self, agent_id: str, object_type: str, 
                                       new_sensation: float, outcome: Dict[str, Any]) -> None:
        """Update object sensation mapping in database."""
        
        # Check if mapping exists
        existing = self.db.execute_query(
            "SELECT mapping_id, success_count, failure_count FROM object_sensation_mappings WHERE agent_id = ? AND object_type = ?",
            (agent_id, object_type)
        )
        
        success = outcome.get('action_success', False)
        
        if existing:
            # Update existing mapping
            mapping_id = existing[0]['mapping_id']
            success_count = existing[0]['success_count'] + (1 if success else 0)
            failure_count = existing[0]['failure_count'] + (0 if success else 1)
            
            self.db.execute_query("""
                UPDATE object_sensation_mappings 
                SET sensation_score = ?, success_count = ?, failure_count = ?, 
                    learn_count = learn_count + 1, last_updated = CURRENT_TIMESTAMP
                WHERE mapping_id = ?
            """, (new_sensation, success_count, failure_count, mapping_id))
        else:
            # Create new mapping
            self.db.execute_query("""
                INSERT INTO object_sensation_mappings
                (mapping_id, agent_id, generation, object_type, sensation_score, 
                 success_count, failure_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), agent_id, outcome.get('generation', 0), object_type,
                new_sensation, 1 if success else 0, 0 if success else 1
            ))
    
    def _update_action_bias(self, agent_id: str, action: int, reward: float, navigation_state: float) -> None:
        """Update action bias based on outcome."""
        
        # Get current action biases
        agent_result = self.db.execute_query(
            "SELECT action_biases FROM agents WHERE agent_id = ?",
            (agent_id,)
        )
        
        if not agent_result:
            return
        
        action_biases = safe_json_parse(agent_result[0]['action_biases'])
        
        # Update bias for this action
        current_bias = action_biases.get(str(action), 0.0)
        bias_adjustment = 0.1 * reward  # Small learning rate for bias updates
        new_bias = current_bias + bias_adjustment
        
        # Clamp bias to reasonable range
        new_bias = max(-1.0, min(1.0, new_bias))
        action_biases[str(action)] = new_bias
        
        # Store updated biases
        self.db.execute_query(
            "UPDATE agents SET action_biases = ? WHERE agent_id = ?",
            (json.dumps(action_biases), agent_id)
        )
    
    # ========================================================================
    # TWO-STREAMS: SEMANTIC IMPRESSIONS
    # ========================================================================
    
    def form_semantic_impression(
        self,
        agent_id: str,
        object_type: str,
        association: str,
        memory_context: str,
        outcome: Dict[str, Any]
    ) -> None:
        """
        Form a personal semantic impression for an object.
        
        Two-Streams Philosophy: Agents develop personal meanings for objects
        based on their unique experiences. This is part of the "semantic network"
        that influences action decisions.
        
        Args:
            agent_id: Agent forming the impression
            object_type: Type of object
            association: What the object means ('danger', 'opportunity', 'neutral', etc.)
            memory_context: Why the agent formed this impression
            outcome: Context from the action that led to this impression
        """
        # Get existing mapping or create new one
        existing = self.db.execute_query("""
            SELECT mapping_id, impression_strength, learn_count
            FROM object_sensation_mappings 
            WHERE agent_id = ? AND object_type = ?
        """, (agent_id, object_type))
        
        personal_meaning = json.dumps({
            'association': association,
            'memory': memory_context,
            'formed_at': datetime.now().isoformat(),
            'game_context': outcome.get('game_id', '')
        })
        
        if existing:
            # Update existing mapping with stronger impression
            mapping = existing[0]
            new_strength = min(1.0, (mapping['impression_strength'] or 0.5) + 0.1)
            
            self.db.execute_query("""
                UPDATE object_sensation_mappings
                SET personal_meaning = ?, impression_strength = ?, 
                    learn_count = learn_count + 1, last_updated = CURRENT_TIMESTAMP
                WHERE mapping_id = ?
            """, (personal_meaning, new_strength, mapping['mapping_id']))
        else:
            # Create new mapping with initial impression
            self.db.execute_query("""
                INSERT INTO object_sensation_mappings
                (mapping_id, agent_id, generation, object_type, sensation_score,
                 personal_meaning, impression_strength, success_count, failure_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), agent_id, outcome.get('generation', 0),
                object_type, 0.0, personal_meaning, 0.5, 0, 0
            ))
    
    def query_personal_impression(
        self,
        agent_id: str,
        object_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Query agent's personal impression of an object.
        
        Returns the semantic meaning the agent has associated with this object,
        which can be used to override or weight network recommendations.
        
        Args:
            agent_id: Agent to query
            object_type: Object type to check
            
        Returns:
            Dictionary with impression data or None if no impression exists
        """
        result = self.db.execute_query("""
            SELECT personal_meaning, impression_strength, sensation_score,
                   success_count, failure_count
            FROM object_sensation_mappings
            WHERE agent_id = ? AND object_type = ?
        """, (agent_id, object_type))
        
        if not result or not result[0]['personal_meaning']:
            return None
        
        r = result[0]
        personal_meaning = safe_json_parse(r['personal_meaning'], {})
        
        return {
            'association': personal_meaning.get('association', 'unknown'),
            'memory': personal_meaning.get('memory', ''),
            'impression_strength': r['impression_strength'] or 0.5,
            'sensation_score': r['sensation_score'] or 0.0,
            'success_rate': (r['success_count'] or 0) / max(1, (r['success_count'] or 0) + (r['failure_count'] or 0))
        }
    
    def get_impression_action_bias(
        self,
        agent_id: str,
        perceived_objects: List[str]
    ) -> float:
        """
        Calculate aggregate action bias from agent's impressions of perceived objects.
        
        Strong negative impressions should bias agent away from actions,
        strong positive impressions should encourage approach.
        
        Args:
            agent_id: Agent perceiving objects
            perceived_objects: List of object types perceived
            
        Returns:
            Aggregate bias (-1.0 to 1.0) where negative=avoid, positive=approach
        """
        if not perceived_objects:
            return 0.0
        
        total_bias = 0.0
        weight_sum = 0.0
        
        for obj_type in perceived_objects:
            impression = self.query_personal_impression(agent_id, obj_type)
            
            if impression:
                strength = impression['impression_strength']
                association = impression['association']
                
                # Map association to bias
                association_map = {
                    'danger': -1.0,
                    'obstacle': -0.5,
                    'neutral': 0.0,
                    'opportunity': 0.5,
                    'goal': 1.0,
                    'success': 0.8
                }
                
                base_bias = association_map.get(association, 0.0)
                weighted_bias = base_bias * strength
                
                total_bias += weighted_bias
                weight_sum += strength
        
        if weight_sum > 0:
            return total_bias / weight_sum
        
        return 0.0

    def get_tetrahedral_sensation(
        self,
        agent_id: str,
        object_info: dict,
        control_data: Optional[dict] = None
    ) -> dict:
        """
        Calculate four-axis tetrahedral sensation for an object.
        
        Implements the McGuffin grammar: Structure >< Function >< Method >< Interpretation
        Each object is perceived through all four axes simultaneously.
        
        Args:
            agent_id: The perceiving agent
            object_info: Dict with keys:
                - 'object_type': str (e.g., 'controlled_object_color_4')
                - 'position': tuple (x, y) 
                - 'color': int (0-9)
                - 'shape': str (optional)
            control_data: Optional control hypothesis from self-model
                - 'is_controlled': bool
                - 'confidence': float
                - 'control_method': str
                
        Returns:
            Tetrahedral sensation dict:
            {
                'structure': {  # What IS it (invariant form)
                    'identity': str,  # Object type/class
                    'position': tuple,  # Spatial coordinates
                    'properties': dict,  # Color, shape, size
                    'stability': float  # How fixed/stable (0-1)
                },
                'function': {  # What does it DO (relational dynamics)
                    'sensation_score': float,  # Emotional valence (-1 to 1)
                    'attraction': float,  # Draw toward/away (-1 to 1)
                    'association': str,  # danger/obstacle/neutral/opportunity/goal
                    'predicted_behavior': str  # What we expect it to do
                },
                'method': {  # HOW we interact (procedural knowledge)
                    'is_controlled': bool,  # Do we control it?
                    'control_method': str,  # How we control (if applicable)
                    'approach_actions': List[int],  # Actions to approach
                    'avoid_actions': List[int],  # Actions to avoid
                    'interaction_history': int  # Times interacted
                },
                'interpretation': {  # WHY it matters (semantic meaning)
                    'semantic_role': str,  # self/tool/goal/obstacle/environment
                    'goal_relevance': float,  # How relevant to current goal (-1 to 1)
                    'threat_level': float,  # Danger assessment (0-1)
                    'curiosity': float,  # Novelty/exploration value (0-1)
                    'personal_meaning': str  # Agent's personal interpretation
                },
                'balance': float,  # How balanced the four axes are (0-1)
                'dominant_axis': str  # Which axis dominates perception
            }
        """
        object_type = object_info.get('object_type', 'unknown')
        position = object_info.get('position', (0, 0))
        color = object_info.get('color', 0)
        
        # STRUCTURE AXIS - What IS it
        structure = {
            'identity': object_type,
            'position': position,
            'properties': {
                'color': color,
                'shape': object_info.get('shape', 'unknown')
            },
            'stability': 1.0 if 'wall' in object_type or 'boundary' in object_type else 0.5
        }
        
        # FUNCTION AXIS - What does it DO (from sensation/impression data)
        impression = self.query_personal_impression(agent_id, object_type)
        
        if impression:
            function = {
                'sensation_score': impression.get('sensation_score', 0.0),
                'attraction': self._calculate_attraction(impression),
                'association': impression.get('association', 'neutral'),
                'predicted_behavior': self._predict_object_behavior(object_type, impression)
            }
        else:
            # Default function for unknown objects
            function = {
                'sensation_score': 0.0,
                'attraction': 0.0,
                'association': 'neutral',
                'predicted_behavior': 'unknown'
            }
        
        # METHOD AXIS - HOW we interact (from control data)
        if control_data:
            method = {
                'is_controlled': control_data.get('is_controlled', False),
                'control_method': control_data.get('control_method', 'none'),
                'approach_actions': control_data.get('approach_actions', []),
                'avoid_actions': control_data.get('avoid_actions', []),
                'interaction_history': control_data.get('interaction_count', 0)
            }
        else:
            method = {
                'is_controlled': False,
                'control_method': 'none',
                'approach_actions': [],
                'avoid_actions': [],
                'interaction_history': 0
            }
        
        # INTERPRETATION AXIS - WHY it matters
        interpretation = self._calculate_interpretation(
            agent_id, object_type, structure, function, method
        )
        
        # Calculate balance and dominant axis
        axis_strengths = {
            'structure': structure['stability'],
            'function': abs(function['sensation_score']),
            'method': 1.0 if method['is_controlled'] else 0.3,
            'interpretation': interpretation['goal_relevance']
        }
        
        max_strength = max(axis_strengths.values())
        min_strength = min(axis_strengths.values())
        balance = 1.0 - (max_strength - min_strength) if max_strength > 0 else 0.5
        
        dominant_axis = max(axis_strengths, key=axis_strengths.get)
        
        return {
            'structure': structure,
            'function': function,
            'method': method,
            'interpretation': interpretation,
            'balance': balance,
            'dominant_axis': dominant_axis
        }
    
    def _calculate_attraction(self, impression: dict) -> float:
        """Calculate attraction score from impression data."""
        association = impression.get('association', 'neutral')
        strength = impression.get('impression_strength', 0.5)
        
        attraction_map = {
            'goal': 1.0,
            'success': 0.8,
            'opportunity': 0.5,
            'neutral': 0.0,
            'obstacle': -0.3,
            'danger': -1.0
        }
        
        base = attraction_map.get(association, 0.0)
        return base * strength
    
    def _predict_object_behavior(self, object_type: str, impression: dict) -> str:
        """Predict what this object will do based on type and history."""
        association = impression.get('association', 'neutral')
        
        if 'wall' in object_type or 'boundary' in object_type:
            return 'static_blocking'
        elif 'goal' in object_type or association == 'goal':
            return 'static_target'
        elif association == 'danger':
            return 'potentially_harmful'
        elif 'moving' in object_type or 'enemy' in object_type:
            return 'dynamic_unpredictable'
        else:
            return 'passive'
    
    def _calculate_interpretation(
        self,
        agent_id: str,
        object_type: str,
        structure: dict,
        function: dict,
        method: dict
    ) -> dict:
        """
        Calculate the Interpretation/Void axis - semantic meaning.
        
        This is the 'D' axis of the McGuffin tetrahedron that provides
        the WHY - why does this object matter to the agent's goals?
        """
        # Determine semantic role
        if method['is_controlled']:
            semantic_role = 'self'
        elif function['association'] == 'goal':
            semantic_role = 'goal'
        elif function['association'] in ('danger', 'obstacle'):
            semantic_role = 'obstacle'
        elif function['attraction'] > 0.3:
            semantic_role = 'tool'
        else:
            # HEURISTIC GOAL DETECTION for new objects with neutral association
            # In ARC games, rare-colored objects are often goals or interactive elements
            inferred_goal = self._infer_goal_heuristically(object_type, structure, function)
            if inferred_goal:
                semantic_role = 'goal'
            else:
                semantic_role = 'environment'
        
        # Goal relevance from function data
        goal_relevance = function['attraction'] if function['attraction'] > 0 else 0.0
        if semantic_role == 'goal':
            goal_relevance = 1.0
        elif semantic_role == 'self':
            goal_relevance = 0.8  # Self is highly relevant
        
        # Threat level
        if function['association'] == 'danger':
            threat_level = 0.9
        elif function['association'] == 'obstacle':
            threat_level = 0.4
        else:
            threat_level = 0.0
        
        # Curiosity - novelty value for unknown/neutral objects
        curiosity = 0.0
        if function['association'] == 'neutral' and method['interaction_history'] < 3:
            curiosity = 0.7
        elif function['association'] == 'unknown':
            curiosity = 1.0
        
        # Personal meaning - retrieve or generate
        personal_meaning = self._get_personal_meaning(agent_id, object_type)
        
        return {
            'semantic_role': semantic_role,
            'goal_relevance': goal_relevance,
            'threat_level': threat_level,
            'curiosity': curiosity,
            'personal_meaning': personal_meaning
        }
    
    def _infer_goal_heuristically(
        self,
        object_type: str,
        structure: dict,
        function: dict
    ) -> bool:
        """
        Infer whether an object is likely a goal based on heuristics.
        
        In ARC games, goals often have these characteristics:
        - Rare colors (appear infrequently in the grid)
        - Small, distinct objects (1-4 cells)
        - Not background colors (0, 1 common backgrounds)
        
        Returns True if object appears to be a goal candidate.
        """
        try:
            # Only apply heuristics to objects with neutral/unknown association
            if function.get('association') not in ('neutral', 'unknown'):
                return False
            
            # Extract color from object_type (e.g., "object_color_3" -> 3)
            color = 0
            if 'color_' in object_type:
                try:
                    color = int(object_type.split('color_')[-1])
                except (ValueError, IndexError):
                    pass
            
            # HEURISTIC 1: Rare colors (not common background colors)
            # Colors 0 (black) and 1 (blue) are often backgrounds
            # Colors 2-9 when rare are often goals
            rare_color = color >= 2
            
            # HEURISTIC 2: Small, distinct size (goals are usually small targets)
            size = structure.get('size', (0, 0))
            if isinstance(size, (list, tuple)) and len(size) >= 2:
                area = size[0] * size[1]
            else:
                area = 10  # Default to non-small if size unknown
            small_target = area <= 16  # 4x4 or smaller
            
            # HEURISTIC 3: Low interaction history (new, unexplored)
            # If agent hasn't interacted with this type much, it could be goal
            
            # Return True if object has rare color AND is small
            # This bootstraps goal detection for pioneers on new games
            return rare_color and small_target
            
        except Exception:
            return False

    def _get_personal_meaning(self, agent_id: str, object_type: str) -> str:
        """Get agent's personal meaning for an object type."""
        impression = self.query_personal_impression(agent_id, object_type)
        
        if impression and impression.get('memory'):
            return impression['memory']
        
        # Default meanings based on object type
        if 'goal' in object_type:
            return 'target to reach'
        elif 'wall' in object_type:
            return 'immovable barrier'
        elif 'enemy' in object_type or 'danger' in object_type:
            return 'threat to avoid'
        else:
            return 'unknown significance'