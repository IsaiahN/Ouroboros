"""
Agent Factory - Creates specialized agents that integrate with existing GameplayEngine
Following Rule 3: Clean integration with existing codebase
Rule 7: All agents use real ARC actions through existing ActionHandler
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from database_interface import DatabaseInterface


class AgentFactory:
    """
    Creates ARC-specialized agents using existing codebase integration
    All agents work with existing GameplayEngine and ActionHandler
    """

    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        self.factory_id = f"factory_{uuid.uuid4().hex[:8]}"

    def create_agent(self, agent_type: str, genome: Dict[str, Any], 
                    epigenetics: Optional[Dict[str, Any]] = None) -> 'ARCAgent':
        """
        Create agent that uses existing ActionHandler and GameplayEngine
        Rule 3: Enhances existing code rather than replacing it
        
        Args:
            agent_type: Type of agent to create
            genome: Static genome (Layer 1 - slow evolution)
            epigenetics: Epigenetic layer (Layer 2 - adaptive preparedness)
        """
        agent_types = {
            'pattern_specialist': self._create_pattern_specialist,
            'score_optimizer': self._create_score_optimizer,
            'exploration_agent': self._create_exploration_agent,
            'win_focused_agent': self._create_win_focused_agent,
            'hybrid_agent': self._create_hybrid_agent
        }

        if agent_type not in agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}. Available types: {list(agent_types.keys())}")

        # Create agent using appropriate factory method
        agent = agent_types[agent_type](genome, epigenetics)

        # Store agent in database (Rule 2)
        self.db.store_agent(agent.to_dict())

        self._log_factory_event("agent_created", {
            "agent_id": agent.agent_id,
            "agent_type": agent_type,
            "genome_hash": hash(str(genome)),
            "has_epigenetics": epigenetics is not None
        })

        return agent

    def _create_pattern_specialist(self, genome: Dict[str, Any], 
                                   epigenetics: Optional[Dict[str, Any]] = None) -> 'ARCAgent':
        """Agent specializing in ARC pattern recognition"""
        agent_id = self._generate_agent_id()

        specialization_config = {
            'pattern_recognition_sensitivity': genome.get('pattern_sensitivity', 0.7),
            'coordinate_exploration_pattern': genome.get('coord_pattern', 'spiral'),
            'action_diversity_preference': genome.get('action_diversity', 0.6),
            'visual_analysis_depth': genome.get('visual_depth', 0.8),
            'pattern_memory_retention': genome.get('pattern_memory', 0.7)
        }

        return ARCAgent(
            agent_id=agent_id,
            agent_type='pattern_specialist',
            genome=genome,
            specialization_config=specialization_config,
            database_interface=self.db,
            epigenetics=epigenetics
        )

    def _create_score_optimizer(self, genome: Dict[str, Any],
                               epigenetics: Optional[Dict[str, Any]] = None) -> 'ARCAgent':
        """Agent focused on ARC score maximization"""
        agent_id = self._generate_agent_id()

        specialization_config = {
            'score_optimization_priority': genome.get('score_priority', 0.8),
            'action_efficiency_preference': genome.get('efficiency_pref', 0.7),
            'win_focus_threshold': genome.get('win_threshold', 0.85),
            'score_tracking_precision': genome.get('score_precision', 0.9),
            'risk_tolerance': genome.get('risk_tolerance', 0.3)
        }

        return ARCAgent(
            agent_id=agent_id,
            agent_type='score_optimizer',
            genome=genome,
            specialization_config=specialization_config,
            database_interface=self.db,
            epigenetics=epigenetics
        )

    def _create_exploration_agent(self, genome: Dict[str, Any],
                                  epigenetics: Optional[Dict[str, Any]] = None) -> 'ARCAgent':
        """Agent focused on exploration and strategy discovery"""
        agent_id = self._generate_agent_id()

        specialization_config = {
            'exploration_weight': genome.get('exploration_weight', 0.8),
            'action_diversity': genome.get('action_diversity', 0.9),
            'novelty_seeking': genome.get('novelty_seeking', 0.7),
            'coordinate_exploration_range': genome.get('coord_range', 0.8),
            'strategy_switching_rate': genome.get('strategy_switch', 0.6)
        }

        return ARCAgent(
            agent_id=agent_id,
            agent_type='exploration_agent',
            genome=genome,
            specialization_config=specialization_config,
            database_interface=self.db,
            epigenetics=epigenetics
        )

    def _create_win_focused_agent(self, genome: Dict[str, Any],
                                  epigenetics: Optional[Dict[str, Any]] = None) -> 'ARCAgent':
        """Agent singularly focused on winning ARC games"""
        agent_id = self._generate_agent_id()

        specialization_config = {
            'win_focus_threshold': genome.get('win_threshold', 0.9),
            'win_strategy_persistence': genome.get('win_persistence', 0.8),
            'conservative_bias': genome.get('conservative_bias', 0.7),
            'goal_oriented_planning': genome.get('goal_planning', 0.9),
            'endgame_optimization': genome.get('endgame_opt', 0.8)
        }

        return ARCAgent(
            agent_id=agent_id,
            agent_type='win_focused_agent',
            genome=genome,
            specialization_config=specialization_config,
            database_interface=self.db,
            epigenetics=epigenetics
        )

    def _create_hybrid_agent(self, genome: Dict[str, Any],
                            epigenetics: Optional[Dict[str, Any]] = None) -> 'ARCAgent':
        """Agent combining multiple specializations"""
        agent_id = self._generate_agent_id()

        # Hybrid agents balance multiple approaches
        specialization_config = {
            'pattern_recognition_weight': genome.get('pattern_weight', 0.4),
            'score_optimization_weight': genome.get('score_weight', 0.3),
            'exploration_weight': genome.get('exploration_weight', 0.2),
            'win_focus_weight': genome.get('win_weight', 0.4),
            'adaptation_rate': genome.get('adaptation_rate', 0.6),
            'strategy_balancing': genome.get('strategy_balance', 0.5)
        }

        return ARCAgent(
            agent_id=agent_id,
            agent_type='hybrid_agent',
            genome=genome,
            specialization_config=specialization_config,
            database_interface=self.db,
            epigenetics=epigenetics
        )

    def _generate_agent_id(self) -> str:
        """Generate unique agent ID"""
        return f"agent_{uuid.uuid4().hex[:12]}"

    def create_agent_from_parents(self, parent1_id: str, parent2_id: str,
                                 crossover_config: Dict[str, Any]) -> 'ARCAgent':
        """Create agent through crossover of two parent agents"""
        # Get parent agents from database
        parent1 = self.db.get_agent(parent1_id)
        parent2 = self.db.get_agent(parent2_id)

        if not parent1 or not parent2:
            raise ValueError("One or both parent agents not found")

        # Determine offspring type and genome through crossover
        offspring_type = self._determine_offspring_type(parent1, parent2)
        offspring_genome = self._crossover_genomes(
            parent1['genome'], parent2['genome'], crossover_config
        )

        # Add parent tracking
        offspring_genome['parent_ids'] = [parent1_id, parent2_id]
        offspring_genome['generation'] = max(
            parent1.get('generation', 0),
            parent2.get('generation', 0)
        ) + 1

        return self.create_agent(offspring_type, offspring_genome)

    def _determine_offspring_type(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> str:
        """Determine offspring agent type based on parents"""
        type1 = parent1['agent_type']
        type2 = parent2['agent_type']

        # Same type inheritance
        if type1 == type2:
            return type1

        # Cross-type breeding creates hybrids
        return 'hybrid_agent'

    def _crossover_genomes(self, genome1: Dict[str, Any], genome2: Dict[str, Any],
                          crossover_config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform genome crossover operation"""
        # This will be handled by the EvolutionaryEngine's CrossoverOperations
        # For now, return a simple blend
        offspring_genome = {}

        # Blend numerical parameters
        for key in ['exploration_weight', 'conservative_bias', 'action_diversity',
                   'score_optimization_priority', 'win_focus_threshold']:
            if key in genome1 and key in genome2:
                # Weighted average with some randomness
                import random
                weight = random.uniform(0.3, 0.7)
                offspring_genome[key] = genome1[key] * weight + genome2[key] * (1 - weight)

        return offspring_genome

    def _log_factory_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log factory events to database (Rule 2: no log files)"""
        self.db.store_factory_log({
            'event_type': event_type,
            'event_data': json.dumps(event_data),
            'factory_id': self.factory_id,
            'timestamp': datetime.now().isoformat()
        })


class ARCAgent:
    """
    Individual ARC agent that integrates with existing GameplayEngine
    Rule 3: Clean integration - uses existing ActionHandler for all ARC interactions
    Rule 7: Real actions only - all actions go through existing ARC API systems
    """

    def __init__(self, agent_id: str, agent_type: str, genome: Dict[str, Any],
                 specialization_config: Dict[str, Any], database_interface: DatabaseInterface,
                 epigenetics: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.genome = genome
        self.specialization_config = specialization_config
        self.db = database_interface

        # EPIGENETIC LAYER - Inherited adaptive preparedness from parent's experience
        # This is what makes agents "prepared to learn" without inheriting solutions
        self.epigenetics = epigenetics or self._initialize_default_epigenetics()

        # Performance tracking
        self.games_played = 0
        self.wins = 0
        self.total_score = 0.0
        self.action_history = []

        # Integration with existing systems
        self.action_handler = None  # Will be set when needed
        self.current_strategy = self._determine_initial_strategy()

    def _initialize_default_epigenetics(self) -> Dict[str, Any]:
        """
        Initialize default epigenetic layer for first-generation agents.
        Epigenetics represent "learning predispositions" not learned solutions.
        """
        return {
            # Feature attention weights (what to notice in ARC grids)
            'feature_attention_weights': {
                'edges': 1.0,           # Baseline attention to edges
                'symmetry': 1.0,        # Baseline attention to symmetry
                'color_patterns': 1.0,  # Baseline attention to colors
                'spatial_relations': 1.0  # Baseline attention to positions
            },
            
            # Learning rate adjustments (how fast to adapt)
            'learning_rate_modifiers': {
                'visual_learning': 1.0,     # Speed of visual pattern learning
                'symbolic_learning': 1.0,   # Speed of logical rule learning
                'motor_learning': 1.0       # Speed of action optimization
            },
            
            # Exploration/exploitation settings
            'exploration_settings': {
                'exploration_ratio': 0.5,    # Default 50/50 explore/exploit
                'novelty_seeking': 0.5,      # Moderate novelty preference
                'risk_tolerance': 0.5        # Moderate risk tolerance
            },
            
            # Meta-learning capacities
            'meta_capacities': {
                'problem_decomposition_tendency': 1.0,  # Ability to break down problems
                'abstraction_capacity': 1.0,            # Ability to form abstractions
                'transfer_learning_ability': 1.0        # Ability to apply learning across domains
            },
            
            # Inheritance tracking
            'inheritance_strength': 1.0,  # First generation = full strength
            'generation_depth': 0,        # Number of generations from root
            'decay_rate': 0.95            # Epigenetic fading per generation
        }

    def select_action(self, game_state: Dict[str, Any], available_actions: List[int],
                     action_handler) -> Dict[str, Any]:
        """
        Select action for current game state
        Rule 3: Uses existing ActionHandler for actual action execution
        Rule 7: Ensures real actions are sent to ARC API
        """
        # Set action handler for this game
        self.action_handler = action_handler

        # Agent-specific action selection based on specialization
        if self.agent_type == 'pattern_specialist':
            action = self._pattern_based_action_selection(game_state, available_actions)
        elif self.agent_type == 'score_optimizer':
            action = self._score_optimizing_action_selection(game_state, available_actions)
        elif self.agent_type == 'exploration_agent':
            action = self._exploration_action_selection(game_state, available_actions)
        elif self.agent_type == 'win_focused_agent':
            action = self._win_focused_action_selection(game_state, available_actions)
        elif self.agent_type == 'hybrid_agent':
            action = self._hybrid_action_selection(game_state, available_actions)
        else:
            # Fallback to balanced selection
            action = self._balanced_action_selection(game_state, available_actions)

        # Track action for learning
        self._track_action(action, game_state)

        # Use existing ActionHandler to execute (Rule 3: clean integration)
        return self.action_handler.execute_action(action)

    def _pattern_based_action_selection(self, game_state: Dict[str, Any],
                                      available_actions: List[int]) -> Dict[str, Any]:
        """Pattern specialist action selection focusing on visual analysis"""
        # Use genome parameters to influence pattern recognition
        pattern_sensitivity = self.specialization_config.get('pattern_recognition_sensitivity', 0.7)
        visual_depth = self.specialization_config.get('visual_analysis_depth', 0.8)

        # Analyze current frame for patterns
        current_frame = game_state.get('current_frame', {})

        # Prefer ACTION6 for coordinate-based pattern exploration
        if 6 in available_actions and self._should_use_coordinate_action(current_frame):
            coordinates = self._select_pattern_coordinates(current_frame, pattern_sensitivity)
            return {
                'action_type': 6,
                'coordinates': coordinates,
                'reasoning': 'pattern_analysis'
            }

        # Otherwise use existing ActionHandler's smart selection with pattern bias
        return self._use_existing_smart_selection(available_actions, 'pattern_focused')

    def _score_optimizing_action_selection(self, game_state: Dict[str, Any],
                                         available_actions: List[int]) -> Dict[str, Any]:
        """Score optimizer action selection focusing on maximum score gain"""
        score_priority = self.specialization_config.get('score_optimization_priority', 0.8)
        efficiency_pref = self.specialization_config.get('action_efficiency_preference', 0.7)

        current_score = game_state.get('current_score', 0)
        win_score = game_state.get('win_score', 100)

        # If close to winning, be more conservative
        score_ratio = current_score / max(win_score, 1)
        if score_ratio > self.specialization_config.get('win_focus_threshold', 0.85):
            return self._conservative_action_selection(available_actions)

        # Otherwise, focus on score-gaining actions
        return self._use_existing_smart_selection(available_actions, 'score_focused')

    def _exploration_action_selection(self, game_state: Dict[str, Any],
                                    available_actions: List[int]) -> Dict[str, Any]:
        """Exploration agent action selection focusing on trying new strategies"""
        exploration_weight = self.specialization_config.get('exploration_weight', 0.8)
        action_diversity = self.specialization_config.get('action_diversity', 0.9)
        novelty_seeking = self.specialization_config.get('novelty_seeking', 0.7)

        # Prefer actions that haven't been used much
        action_usage = self._get_action_usage_history()
        least_used_actions = sorted(available_actions, key=lambda a: action_usage.get(a, 0))

        # Use novelty-seeking approach
        if novelty_seeking > 0.5 and least_used_actions:
            return self._select_novel_action(least_used_actions[0], game_state)

        return self._use_existing_smart_selection(available_actions, 'exploration_focused')

    def _win_focused_action_selection(self, game_state: Dict[str, Any],
                                    available_actions: List[int]) -> Dict[str, Any]:
        """Win-focused agent action selection prioritizing game completion"""
        win_threshold = self.specialization_config.get('win_focus_threshold', 0.9)
        conservative_bias = self.specialization_config.get('conservative_bias', 0.7)

        current_score = game_state.get('current_score', 0)
        win_score = game_state.get('win_score', 100)

        # Always be conservative and goal-oriented
        return self._conservative_action_selection(available_actions)

    def _hybrid_action_selection(self, game_state: Dict[str, Any],
                               available_actions: List[int]) -> Dict[str, Any]:
        """Hybrid agent balances multiple approaches"""
        pattern_weight = self.specialization_config.get('pattern_recognition_weight', 0.4)
        score_weight = self.specialization_config.get('score_optimization_weight', 0.3)
        exploration_weight = self.specialization_config.get('exploration_weight', 0.2)
        win_weight = self.specialization_config.get('win_focus_weight', 0.4)

        # Randomly select approach based on weights
        import random
        approach_selector = random.random()

        if approach_selector < pattern_weight:
            return self._pattern_based_action_selection(game_state, available_actions)
        elif approach_selector < pattern_weight + score_weight:
            return self._score_optimizing_action_selection(game_state, available_actions)
        elif approach_selector < pattern_weight + score_weight + exploration_weight:
            return self._exploration_action_selection(game_state, available_actions)
        else:
            return self._win_focused_action_selection(game_state, available_actions)

    def _use_existing_smart_selection(self, available_actions: List[int],
                                    strategy_focus: str) -> Dict[str, Any]:
        """
        Use existing ActionHandler's smart_action_selection with agent preferences
        Rule 3: Clean integration with existing codebase
        """
        if not self.action_handler:
            # Fallback to simple selection
            import random
            action_type = random.choice(available_actions)
            return {'action_type': action_type, 'reasoning': 'fallback_selection'}

        # Convert agent genome to strategy preferences for existing system
        strategy_preferences = self._genome_to_strategy_preferences(strategy_focus)

        # Use existing smart action selection (Rule 3: enhance, don't replace)
        return self.action_handler.smart_action_selection(
            available_actions=available_actions,
            strategy_preferences=strategy_preferences
        )

    def _genome_to_strategy_preferences(self, focus: str) -> Dict[str, float]:
        """Convert agent genome to strategy preferences for existing ActionHandler"""
        base_preferences = {
            'exploration': self.genome.get('exploration_weight', 0.3),
            'conservative': self.genome.get('conservative_bias', 0.2),
            'score_focus': self.genome.get('score_optimization_priority', 0.7),
            'action_diversity': self.genome.get('action_diversity', 0.6),
            'coordinate_precision': self.genome.get('coordinate_precision', 0.5)
        }

        # Adjust based on focus
        if focus == 'pattern_focused':
            base_preferences['exploration'] *= 1.5
        elif focus == 'score_focused':
            base_preferences['score_focus'] *= 1.3
        elif focus == 'exploration_focused':
            base_preferences['exploration'] *= 1.8
            base_preferences['action_diversity'] *= 1.4

        return base_preferences

    def _select_pattern_coordinates(self, frame: Dict[str, Any], sensitivity: float) -> Dict[str, int]:
        """Select coordinates based on pattern analysis"""
        # Simple pattern-based coordinate selection
        # In a full implementation, this would use computer vision
        import random

        exploration_pattern = self.specialization_config.get('coordinate_exploration_pattern', 'spiral')

        if exploration_pattern == 'spiral':
            # Spiral outward from center
            center_x, center_y = 32, 32  # Middle of 64x64 grid
            radius = int(sensitivity * 20)
            x = center_x + random.randint(-radius, radius)
            y = center_y + random.randint(-radius, radius)
        elif exploration_pattern == 'grid':
            # Grid-based exploration
            grid_size = int(64 / (sensitivity * 8))
            x = random.randint(0, 63 // grid_size) * grid_size
            y = random.randint(0, 63 // grid_size) * grid_size
        else:  # random
            x = random.randint(0, 63)
            y = random.randint(0, 63)

        # Ensure coordinates are in valid range (Rule 7: real actions only)
        x = max(0, min(63, x))
        y = max(0, min(63, y))

        return {'x': x, 'y': y}

    def _track_action(self, action: Dict[str, Any], game_state: Dict[str, Any]):
        """Track action for agent learning and analysis"""
        action_record = {
            'action': action,
            'game_state_snapshot': {
                'current_score': game_state.get('current_score', 0),
                'action_count': game_state.get('action_count', 0)
            },
            'timestamp': datetime.now().isoformat()
        }

        self.action_history.append(action_record)

        # Store in database for analysis (Rule 2)
        self.db.store_agent_action(self.agent_id, action_record)

    def update_performance(self, game_result: Dict[str, Any]):
        """Update agent performance after game completion"""
        self.games_played += 1

        if game_result.get('win_detected', False):
            self.wins += 1

        self.total_score += game_result.get('final_score', 0.0)

        # Calculate updated metrics
        win_rate = self.wins / max(self.games_played, 1)
        avg_score = self.total_score / max(self.games_played, 1)

        # Store updated performance in database
        performance_update = {
            'agent_id': self.agent_id,
            'games_played': self.games_played,
            'wins': self.wins,
            'win_rate': win_rate,
            'total_score': self.total_score,
            'avg_score': avg_score,
            'last_game_result': game_result,
            'updated_at': datetime.now().isoformat()
        }

        self.db.update_agent_performance(self.agent_id, performance_update)

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary for database storage"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'genome': json.dumps(self.genome) if isinstance(self.genome, dict) else self.genome,
            'specialization': self.agent_type,
            'generation': self.genome.get('generation', 0),
            'parent_ids': json.dumps(self.genome.get('parent_ids', [])),
            'created_at': datetime.now().isoformat(),
            'is_active': True,
            'total_games_played': self.games_played,
            'total_games_won': self.wins,
            'total_score_achieved': self.total_score,
            'epigenetics': json.dumps(self.epigenetics) if self.epigenetics else None
        }

    # Utility methods for action selection
    def _should_use_coordinate_action(self, frame: Dict[str, Any]) -> bool:
        """Determine if coordinate-based action (ACTION6) should be used"""
        return True  # Simplified - in full implementation, analyze frame

    def _conservative_action_selection(self, available_actions: List[int]) -> Dict[str, Any]:
        """Conservative action selection for win-focused approach"""
        # Prefer lower-risk actions
        conservative_actions = [1, 2, 3]  # Example conservative action preferences
        safe_actions = [a for a in available_actions if a in conservative_actions]

        if safe_actions:
            import random
            return {'action_type': random.choice(safe_actions), 'reasoning': 'conservative'}
        else:
            import random
            return {'action_type': random.choice(available_actions), 'reasoning': 'fallback'}

    def _get_action_usage_history(self) -> Dict[int, int]:
        """Get history of action usage for exploration decisions"""
        usage = {}
        for record in self.action_history:
            action_type = record['action'].get('action_type', 0)
            usage[action_type] = usage.get(action_type, 0) + 1
        return usage

    def _select_novel_action(self, action_type: int, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Select novel action for exploration"""
        return {'action_type': action_type, 'reasoning': 'novelty_seeking'}

    def _balanced_action_selection(self, game_state: Dict[str, Any],
                                 available_actions: List[int]) -> Dict[str, Any]:
        """Balanced action selection for generic agents"""
        return self._use_existing_smart_selection(available_actions, 'balanced')

    def _determine_initial_strategy(self) -> str:
        """Determine initial strategy based on agent type and genome"""
        if self.agent_type == 'pattern_specialist':
            return 'pattern_focused'
        elif self.agent_type == 'score_optimizer':
            return 'score_focused'
        elif self.agent_type == 'exploration_agent':
            return 'exploration_focused'
        elif self.agent_type == 'win_focused_agent':
            return 'win_focused'
        else:
            return 'balanced'

# [CHECKPOINT 6 COMPLETED: AGENT FACTORY IMPLEMENTATION]
# Next: Integration with existing codebase (core_gameplay.py, action_handler.py, main_runner.py)