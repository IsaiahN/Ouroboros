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

        self._log_evolution_event("evolution_cycle_started", {
            "generation": generation,
            "strategy": evolution_strategy
        })

        try:
            # 1. Load current population from database (Rule 2)
            current_population = self._load_population_from_database()

            # 2. Calculate ARC-based fitness scores
            fitness_scores = self._calculate_arc_fitness(current_population)

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

    def _calculate_arc_fitness(self, population: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate fitness based on ARC game performance only
        Uses ARC-native rewards: wins, scores, efficiency
        """
        fitness_scores = {}

        for agent in population:
            agent_id = agent['agent_id']

            # Get ARC performance from database
            arc_performance = self.db.get_agent_arc_performance(agent_id)

            if not arc_performance:
                # New agent with no performance data
                fitness_scores[agent_id] = 0.0
                continue

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

            fitness_scores[agent_id] = fitness

        return fitness_scores

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