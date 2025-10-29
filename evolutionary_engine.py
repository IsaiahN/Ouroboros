"""
Evolutionary Engine - Handles agent breeding, mutation, and selection
Based on ARC performance data following Ouroboros principles
All operations use database storage (Rule 2)
"""

import json
import uuid
import random
import copy
from datetime import datetime
from typing import Dict, List, Any, Tuple
from database_interface import DatabaseInterface


class EvolutionaryEngine:
    """
    Executes evolution operations based on Claude Code decisions
    Uses ARC game performance as primary fitness measure
    """

    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        self.crossover_ops = CrossoverOperations()
        self.mutation_strategies = MutationStrategies()
        self.engine_id = f"evol_{uuid.uuid4().hex[:8]}"

    def evolve_population(self, evolution_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute evolution cycle using ARC performance data
        Returns new generation of agents
        """
        generation = evolution_strategy.get('generation', 0)
        diversity_mode = evolution_strategy.get('diversity_mode', False)  # Check if in diversity mode
        specialist_mode = evolution_strategy.get('specialist_mode', False)  # NEW: Check if in specialist mode

        self._log_evolution_event("evolution_cycle_started", {
            "generation": generation,
            "strategy": evolution_strategy,
            "diversity_mode": diversity_mode,
            "specialist_mode": specialist_mode  # NEW: Log specialist mode
        })

        try:
            # 1. Load current population from database (Rule 2)
            current_population = self._load_population_from_database()

            # 2. Calculate ARC-based fitness scores (with optional diversity+meta-learning or specialist)
            fitness_scores = self._calculate_arc_fitness(
                current_population, 
                diversity_mode=diversity_mode,
                specialist_mode=specialist_mode
            )

            # 3. Select breeding pairs based on ARC performance
            breeding_pairs = self._select_breeding_pairs(
                current_population,
                fitness_scores,
                evolution_strategy
            )

            # 4. Generate offspring through crossover
            offspring = self._generate_offspring(breeding_pairs, evolution_strategy)

            # 5. Apply mutations to explore strategy space
            mutated_offspring = self._apply_mutations(offspring, evolution_strategy)

            # 6. Selection: combine parents and offspring, select best
            new_population = self._select_new_population(
                current_population,
                mutated_offspring,
                fitness_scores,
                evolution_strategy
            )

            # 7. Update population in database
            self._update_population_database(new_population, generation)

            self._log_evolution_event("evolution_cycle_completed", {
                "generation": generation,
                "new_population_size": len(new_population),
                "offspring_created": len(offspring),
                "mutations_applied": sum(1 for agent in mutated_offspring if agent.get('mutated', False))
            })

            return new_population

        except Exception as e:
            self._log_evolution_event("evolution_cycle_error", {
                "generation": generation,
                "error": str(e)
            })
            raise

    def _calculate_arc_fitness(self, population: List[Dict[str, Any]], 
                               diversity_mode: bool = False,
                               specialist_mode: bool = False) -> Dict[str, float]:
        """
        Calculate fitness based on ARC game performance
        Uses ARC-native rewards: wins, scores, efficiency
        
        Args:
            population: List of agent dictionaries
            diversity_mode: If True, use combined fitness (standard + diversity + meta-learning)
            specialist_mode: If True, focus 100% on assigned specialization games
        
        Returns:
            Dictionary mapping agent_id to fitness score
        """
        fitness_scores = {}

        for agent in population:
            agent_id = agent['agent_id']

            if specialist_mode:
                # SPECIALIST FITNESS - 100% focus on assigned games
                # No diversity penalties, deep mastery encouraged
                fitness_scores[agent_id] = self._calculate_specialist_fitness(agent_id, agent)
                
            elif diversity_mode:
                # COMBINED FITNESS for generalization
                # 30% standard (can it win?)
                # 40% diversity (can it generalize?)
                # 30% meta-learning (can it learn to learn?)
                
                standard_fitness = self._calculate_standard_fitness(agent_id)
                diversity_fitness = self._calculate_diversity_fitness_component(agent_id)
                meta_fitness = self._calculate_meta_learning_fitness(agent_id)
                
                # Weighted combination
                fitness = (
                    standard_fitness * 0.30 +
                    diversity_fitness * 0.40 +
                    meta_fitness * 0.30
                )
                
                fitness_scores[agent_id] = fitness
            else:
                # STANDARD FITNESS only (original behavior)
                fitness_scores[agent_id] = self._calculate_standard_fitness(agent_id)

        return fitness_scores
    
    def _calculate_standard_fitness(self, agent_id: str) -> float:
        """
        Calculate standard fitness based on win rate and performance
        Original fitness calculation (50% wins, 25% efficiency, 15% consistency, 10% progression)
        """
        # Get ARC performance from database
        arc_performance = self.db.get_agent_arc_performance(agent_id)

        if not arc_performance:
            # New agent with no performance data
            return 0.0

        # Calculate fitness based on ARC-native metrics
        win_rate = arc_performance.get('win_rate', 0.0)
        score_efficiency = arc_performance.get('score_efficiency', 0.0)
        consistency_score = arc_performance.get('consistency_score', 0.0)
        level_progression_rate = arc_performance.get('level_progression_rate', 0.0)

        # Weighted fitness calculation (prioritizing ARC wins)
        fitness = (
            win_rate * 0.5 +                    # 50% weight on winning games
            score_efficiency * 0.25 +           # 25% weight on score efficiency
            consistency_score * 0.15 +          # 15% weight on consistency
            level_progression_rate * 0.10       # 10% weight on level progression
        )

        # Bonus for agents with more game experience (minimum reliability)
        games_played = arc_performance.get('total_games_played', 0)
        if games_played >= 10:
            fitness *= 1.1  # 10% bonus for proven agents

        return fitness
    
    def _calculate_specialist_fitness(self, agent_id: str, agent_data: Dict[str, Any]) -> float:
        """
        Calculate specialist fitness - 100% focus on assigned games
        No diversity penalties, encourages deep mastery
        
        Args:
            agent_id: Agent ID
            agent_data: Agent dictionary with specialization field
            
        Returns:
            Specialist fitness score (0.0 to 1.0+)
        """
        # Get assigned games from specialization field
        specialization = agent_data.get('specialization', '')
        try:
            if isinstance(specialization, str) and specialization:
                spec_data = json.loads(specialization) if specialization.startswith('{') else {'assigned_games': []}
            else:
                spec_data = {}
        except:
            spec_data = {}
        
        assigned_games = spec_data.get('assigned_games', [])
        
        if not assigned_games:
            # No assignment yet - use standard fitness
            return self._calculate_standard_fitness(agent_id)
        
        # Get performance ONLY on assigned games
        try:
            # Query performance on assigned games only
            placeholders = ','.join(['?' for _ in assigned_games])
            query = f"""
                SELECT 
                    COUNT(*) as games_played,
                    SUM(CASE WHEN win_achieved THEN 1 ELSE 0 END) as wins,
                    AVG(final_score) as avg_score,
                    AVG(score_efficiency) as avg_efficiency,
                    MAX(final_score) as best_score
                FROM agent_arc_performance
                WHERE agent_id = ? AND game_id IN ({placeholders})
            """
            
            result = self.db.execute_query(query, (agent_id, *assigned_games))
            
            if not result or result[0]['games_played'] == 0:
                # No games played on assigned games yet
                return 0.0
            
            perf = result[0]
            games_played = perf['games_played']
            wins = perf['wins'] or 0
            avg_score = perf['avg_score'] or 0.0
            avg_efficiency = perf['avg_efficiency'] or 0.0
            best_score = perf['best_score'] or 0.0
            
            # Calculate specialist fitness
            # Heavy emphasis on wins and scores ON ASSIGNED GAMES
            win_rate = wins / games_played if games_played > 0 else 0.0
            
            # Normalize avg_score (assuming max score ~10.0 for ARC)
            normalized_score = min(avg_score / 10.0, 1.0)
            
            # Normalize efficiency (assuming 1.0 is excellent)
            normalized_efficiency = min(avg_efficiency, 1.0)
            
            # Specialist fitness weights:
            # 50% win rate on assigned games
            # 30% average score on assigned games  
            # 20% efficiency on assigned games
            fitness = (
                win_rate * 0.50 +
                normalized_score * 0.30 +
                normalized_efficiency * 0.20
            )
            
            # Bonus for deep mastery (high scores on assigned games)
            if best_score >= 3.0:
                fitness *= 1.3  # 30% bonus for achieving score 3+
            elif best_score >= 2.0:
                fitness *= 1.15  # 15% bonus for achieving score 2+
            
            # Bonus for consistent performance
            if games_played >= 20:
                fitness *= 1.1  # 10% bonus for experience
            
            return min(fitness, 2.0)  # Cap at 2.0 to allow specialists to dominate
            
        except Exception as e:
            self._log_evolution_event("specialist_fitness_error", {
                "agent_id": agent_id,
                "error": str(e),
                "assigned_games": assigned_games
            })
            return 0.0
    
    def _calculate_diversity_fitness_component(self, agent_id: str) -> float:
        """
        Calculate diversity fitness (novel games, few-shot learning, diversity)
        Uses performance_analyzer.calculate_diversity_fitness()
        """
        try:
            from performance_analyzer import PerformanceAnalyzer
            analyzer = PerformanceAnalyzer(self.db)
            
            diversity_metrics = analyzer.calculate_diversity_fitness(agent_id)
            return diversity_metrics.get('diversity_fitness_score', 0.0)
        except Exception as e:
            self._log_evolution_event("diversity_fitness_error", {
                "agent_id": agent_id,
                "error": str(e)
            })
            return 0.0
    
    def _calculate_meta_learning_fitness(self, agent_id: str) -> float:
        """
        Calculate meta-learning fitness (ability to learn and transfer knowledge)
        
        Metrics:
        - 25% Rule acquisition (how many rules learned)
        - 35% Transfer success rate (rules that work on new games)
        - 25% Rule generality (avg games each rule works on)
        - 15% Learning speed (rules per game)
        
        Returns:
            Meta-learning fitness score (0.0 to 1.0)
        """
        try:
            # Get meta-learning metrics from database
            meta_metrics = self.db.execute_query("""
                SELECT 
                    total_rules_learned,
                    successful_transfers,
                    failed_transfers,
                    transfer_success_rate,
                    avg_rule_generality,
                    learning_rate
                FROM agent_meta_learning
                WHERE agent_id = ?
            """, (agent_id,))
            
            if not meta_metrics or len(meta_metrics) == 0:
                # No meta-learning data yet - return 0
                return 0.0
            
            metrics = meta_metrics[0]
            
            # 1. Rule acquisition score (normalized to 0-1)
            rules_learned = metrics.get('total_rules_learned', 0)
            rule_acquisition_score = min(rules_learned / 20, 1.0)  # Cap at 20 rules
            
            # 2. Transfer success rate (already 0-1)
            transfer_success_rate = metrics.get('transfer_success_rate', 0.0)
            
            # 3. Rule generality (normalized to 0-1)
            avg_generality = metrics.get('avg_rule_generality', 0.0)
            rule_generality_score = min(avg_generality / 5, 1.0)  # Cap at 5 games per rule
            
            # 4. Learning speed (normalized to 0-1)
            learning_rate = metrics.get('learning_rate', 0.0)
            learning_speed_score = min(learning_rate * 10, 1.0)  # Cap at 0.1 rules/game
            
            # Combined meta-fitness
            meta_fitness = (
                rule_acquisition_score * 0.25 +
                transfer_success_rate * 0.35 +
                rule_generality_score * 0.25 +
                learning_speed_score * 0.15
            )
            
            # Store calculated meta-fitness back to database
            self.db.execute_query("""
                UPDATE agent_meta_learning
                SET meta_fitness_score = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE agent_id = ?
            """, (meta_fitness, agent_id))
            
            return meta_fitness
            
        except Exception as e:
            self._log_evolution_event("meta_learning_fitness_error", {
                "agent_id": agent_id,
                "error": str(e)
            })
            return 0.0
    
    def _get_agent_games_played(self, agent_id: str) -> int:
        """Get total games played by agent"""
        try:
            result = self.db.execute_query("""
                SELECT total_games_played FROM agents WHERE agent_id = ?
            """, (agent_id,))
            
            if result and len(result) > 0:
                return result[0].get('total_games_played', 0)
            return 0
        except:
            return 0

    def _select_breeding_pairs(self, population: List[Dict[str, Any]],
                             fitness_scores: Dict[str, float],
                             evolution_strategy: Dict[str, Any]) -> List[Tuple[Dict, Dict]]:
        """
        Select breeding pairs based on ARC performance
        Uses tournament selection with fitness-based pairing
        """
        selection_pressure = evolution_strategy.get('selection_pressure', 0.5)
        crossover_rate = evolution_strategy.get('crossover_rate', 0.6)

        # Number of breeding pairs needed
        num_pairs = int(len(population) * crossover_rate / 2)

        breeding_pairs = []

        for _ in range(num_pairs):
            # Tournament selection for first parent
            parent1 = self._tournament_selection(population, fitness_scores, selection_pressure)

            # Tournament selection for second parent (ensure different from first)
            parent2 = self._tournament_selection(
                [p for p in population if p['agent_id'] != parent1['agent_id']],
                fitness_scores,
                selection_pressure
            )

            if parent2:  # Ensure we found a second parent
                breeding_pairs.append((parent1, parent2))

        return breeding_pairs

    def _tournament_selection(self, population: List[Dict[str, Any]],
                            fitness_scores: Dict[str, float],
                            selection_pressure: float) -> Dict[str, Any]:
        """
        Tournament selection based on ARC fitness
        Higher selection pressure = more emphasis on fitness
        """
        tournament_size = max(2, int(len(population) * selection_pressure))
        tournament_size = min(tournament_size, len(population))

        # Select random candidates for tournament
        tournament_candidates = random.sample(population, tournament_size)

        # Select winner based on fitness
        winner = max(tournament_candidates,
                    key=lambda agent: fitness_scores.get(agent['agent_id'], 0.0))

        return winner

    def _generate_offspring(self, breeding_pairs: List[Tuple[Dict, Dict]],
                          evolution_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate offspring through crossover of parent genomes
        """
        offspring = []

        for parent1, parent2 in breeding_pairs:
            # Create two offspring from each breeding pair
            offspring1 = self.crossover_ops.crossover_genomes(parent1, parent2)
            offspring2 = self.crossover_ops.crossover_genomes(parent2, parent1)  # Reversed order

            # Mark as offspring for tracking
            offspring1['parent_ids'] = [parent1['agent_id'], parent2['agent_id']]
            offspring2['parent_ids'] = [parent1['agent_id'], parent2['agent_id']]
            offspring1['generation'] = evolution_strategy.get('generation', 0)
            offspring2['generation'] = evolution_strategy.get('generation', 0)

            offspring.extend([offspring1, offspring2])

        return offspring

    def _apply_mutations(self, offspring: List[Dict[str, Any]],
                        evolution_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply mutations to offspring to explore strategy space
        """
        mutation_rate = evolution_strategy.get('mutation_rate', 0.2)
        strategy_focus = evolution_strategy.get('focus', 'balanced')

        mutated_offspring = []

        for agent in offspring:
            if random.random() < mutation_rate:
                # Apply mutation based on strategy focus
                mutated_agent = self.mutation_strategies.mutate_genome(
                    agent,
                    strategy_focus
                )
                mutated_agent['mutated'] = True
                mutated_agent['mutation_count'] = mutated_agent.get('mutation_count', 0) + 1
                mutated_offspring.append(mutated_agent)
            else:
                agent['mutated'] = False
                mutated_offspring.append(agent)

        return mutated_offspring

    def _select_new_population(self, current_population: List[Dict[str, Any]],
                             offspring: List[Dict[str, Any]],
                             fitness_scores: Dict[str, float],
                             evolution_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Select new population from current population + offspring
        Maintains population size while favoring high-fitness agents
        """
        target_population_size = len(current_population)

        # Combine current population and offspring
        all_candidates = current_population + offspring

        # Calculate fitness for new offspring (use estimated fitness for now)
        for agent in offspring:
            if agent['agent_id'] not in fitness_scores:
                # Estimate fitness based on parent fitness
                parent_ids = agent.get('parent_ids', [])
                if parent_ids:
                    parent_fitnesses = [fitness_scores.get(pid, 0.0) for pid in parent_ids]
                    estimated_fitness = sum(parent_fitnesses) / len(parent_fitnesses)
                    # Add small random variation for estimation
                    estimated_fitness += random.uniform(-0.1, 0.1)
                    fitness_scores[agent['agent_id']] = max(0.0, estimated_fitness)
                else:
                    fitness_scores[agent['agent_id']] = 0.0

        # Sort by fitness and select top agents
        sorted_candidates = sorted(
            all_candidates,
            key=lambda agent: fitness_scores.get(agent['agent_id'], 0.0),
            reverse=True
        )

        # Select top performers, but ensure some diversity
        new_population = sorted_candidates[:target_population_size]

        return new_population

    def _load_population_from_database(self) -> List[Dict[str, Any]]:
        """Load current active population from database"""
        return self.db.get_active_agents()

    def _update_population_database(self, new_population: List[Dict[str, Any]], generation: int):
        """Update population in database"""
        import json

        # Store new agents
        for agent in new_population:
            # Ensure genome is JSON string for database storage
            if isinstance(agent.get('genome'), dict):
                agent['genome'] = json.dumps(agent['genome'])

            # Ensure parent_ids is JSON string for database storage
            if isinstance(agent.get('parent_ids'), list):
                agent['parent_ids'] = json.dumps(agent['parent_ids'])

            if not self.db.agent_exists(agent['agent_id']):
                self.db.store_agent(agent)
            else:
                self.db.update_agent(agent['agent_id'], agent)

    def _log_evolution_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log evolution events to database (Rule 2: no log files)"""
        self.db.store_evolution_log({
            'event_type': event_type,
            'event_data': json.dumps(event_data),
            'engine_id': self.engine_id,
            'timestamp': datetime.now().isoformat()
        })


class CrossoverOperations:
    """Handles genetic crossover operations for agent genomes"""

    def crossover_genomes(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create offspring by combining traits from both parents
        Focuses on strategy parameters that affect ARC performance
        """
        # Handle genome data (might be JSON string)
        import json

        p1_genome = parent1['genome']
        if isinstance(p1_genome, str):
            p1_genome = json.loads(p1_genome)

        p2_genome = parent2['genome']
        if isinstance(p2_genome, str):
            p2_genome = json.loads(p2_genome)

        # Start with parent1 as base
        offspring_genome = copy.deepcopy(p1_genome)

        # Generate unique ID for offspring
        offspring_genome['agent_id'] = f"offspring_{uuid.uuid4().hex[:8]}"

        # Crossover key strategy parameters
        strategy_params = [
            'exploration_weight', 'conservative_bias', 'action_diversity',
            'score_optimization_priority', 'win_focus_threshold',
            'action_efficiency_preference'
        ]

        for param in strategy_params:
            if param in p1_genome and param in p2_genome:
                # Random selection or averaging
                if random.random() < 0.5:
                    offspring_genome[param] = p2_genome[param]
                else:
                    # Average with small random variation
                    avg_value = (p1_genome[param] + p2_genome[param]) / 2
                    offspring_genome[param] = avg_value + random.uniform(-0.05, 0.05)
                    offspring_genome[param] = max(0.0, min(1.0, offspring_genome[param]))

        # Special handling for categorical parameters
        categorical_params = ['coordinate_exploration_pattern']
        for param in categorical_params:
            if param in p1_genome and param in p2_genome:
                # Random selection from parents
                offspring_genome[param] = random.choice([
                    p1_genome[param],
                    p2_genome[param]
                ])

        # Create offspring agent
        offspring = {
            'agent_id': offspring_genome['agent_id'],
            'agent_type': self._determine_offspring_type(parent1, parent2),
            'genome': offspring_genome,
            'generation': parent1.get('generation', 0) + 1,
            'specialization': self._determine_offspring_specialization(parent1, parent2),
            'crossover_count': 1
        }

        return offspring

    def _determine_offspring_type(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> str:
        """Determine offspring agent type based on parents"""
        # If parents are same type, offspring inherits it
        if parent1['agent_type'] == parent2['agent_type']:
            return parent1['agent_type']

        # Otherwise, random selection or create hybrid
        parent_types = [parent1['agent_type'], parent2['agent_type']]

        # Chance for hybrid type
        if random.random() < 0.3:
            return f"hybrid_{random.choice(parent_types)}"
        else:
            return random.choice(parent_types)

    def _determine_offspring_specialization(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> str:
        """Determine offspring specialization"""
        specializations = [
            parent1.get('specialization', 'generalist'),
            parent2.get('specialization', 'generalist')
        ]
        return random.choice(specializations)


class MutationStrategies:
    """Handles mutation operations for genome exploration"""

    def mutate_genome(self, agent: Dict[str, Any], strategy_focus: str) -> Dict[str, Any]:
        """
        Apply mutations based on evolution strategy focus
        """
        mutated_agent = copy.deepcopy(agent)
        genome = mutated_agent['genome']

        # Determine mutation strength based on strategy focus
        if strategy_focus == 'exploration':
            mutation_strength = 0.3  # Large mutations for exploration
        elif strategy_focus == 'exploitation':
            mutation_strength = 0.1  # Small mutations for refinement
        elif strategy_focus == 'diversification':
            mutation_strength = 0.4  # Very large mutations for diversity
        else:  # balanced
            mutation_strength = 0.2  # Medium mutations

        # Mutate numerical parameters
        numerical_params = [
            'exploration_weight', 'conservative_bias', 'action_diversity',
            'score_optimization_priority', 'win_focus_threshold',
            'action_efficiency_preference'
        ]

        for param in numerical_params:
            if param in genome and random.random() < 0.3:  # 30% chance to mutate each param
                current_value = genome[param]
                mutation = random.uniform(-mutation_strength, mutation_strength)
                new_value = current_value + mutation
                genome[param] = max(0.0, min(1.0, new_value))  # Clamp to [0, 1]

        # Mutate categorical parameters
        if random.random() < 0.2:  # 20% chance to mutate exploration pattern
            patterns = ['spiral', 'grid', 'random', 'edge_first', 'center_out']
            genome['coordinate_exploration_pattern'] = random.choice(patterns)

        # Possibility of new specialized parameters based on strategy focus
        if strategy_focus == 'exploration' and random.random() < 0.1:
            genome['exploration_bonus'] = random.uniform(0.1, 0.3)
        elif strategy_focus == 'exploitation' and random.random() < 0.1:
            genome['exploitation_focus'] = random.uniform(0.7, 0.9)

        return mutated_agent

# [CHECKPOINT 3 COMPLETED: EVOLUTION ENGINE IMPLEMENTATION]
# Next: Implement ARC RLVR Framework and Performance Analyzer