"""
Genetic Programming Module

Implements evolutionary operations for algorithm representations including:
- Population initialization
- Selection mechanisms (tournament, fitness-proportional)
- Crossover operations (subtree exchange)
- Mutation operations (point mutations, subtree replacement)
- Population management and evolution cycles
"""

import random
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import copy
import json

from algorithm_representations import (
    AlgorithmRepresentation, AlgorithmNode, ActionNode, ConditionalNode,
    SequenceNode, ConditionNode, RandomChoiceNode, RepeatNode,
    AlgorithmBuilder, ACTION_TYPES, CONDITION_TYPES
)

logger = logging.getLogger(__name__)


@dataclass
class GPConfig:
    """Configuration for genetic programming operations."""
    population_size: int = 50
    max_depth: int = 8
    max_generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elitism_rate: float = 0.1
    tournament_size: int = 3
    max_tree_size: int = 100


class GeneticProgrammingEngine:
    """Main engine for genetic programming operations."""

    def __init__(self, config: GPConfig = None):
        self.config = config or GPConfig()
        self.population: List[AlgorithmRepresentation] = []
        self.generation = 0
        self.evolution_stats = []

    def initialize_population(self) -> List[AlgorithmRepresentation]:
        """Initialize the population with diverse algorithms."""
        logger.info(f"Initializing population of size {self.config.population_size}")

        self.population = []

        # Create diverse initial population
        for i in range(self.config.population_size):
            if i % 3 == 0:
                # Simple random algorithms
                algorithm = AlgorithmBuilder.create_random_action_algorithm()
            elif i % 3 == 1:
                # Score-based algorithms
                algorithm = AlgorithmBuilder.create_score_based_algorithm()
            else:
                # Adaptive algorithms
                algorithm = AlgorithmBuilder.create_adaptive_algorithm()

            algorithm.generation = 0
            algorithm.algorithm_id = f"gen0_algo_{i:03d}"
            self.population.append(algorithm)

        # Add some completely random algorithms for diversity
        random_count = self.config.population_size // 4
        for i in range(random_count):
            algorithm = self._create_random_algorithm()
            algorithm.generation = 0
            algorithm.algorithm_id = f"gen0_random_{i:03d}"
            self.population.append(algorithm)

        # Trim to exact population size
        self.population = self.population[:self.config.population_size]

        logger.info(f"Created initial population with {len(self.population)} algorithms")
        return self.population

    def _create_random_algorithm(self) -> AlgorithmRepresentation:
        """Create a completely random algorithm."""
        depth = random.randint(2, self.config.max_depth)
        root_node = self._create_random_node(depth)
        return AlgorithmRepresentation(root_node)

    def _create_random_node(self, max_depth: int) -> AlgorithmNode:
        """Create a random algorithm node."""
        if max_depth <= 1:
            # Terminal nodes only
            return self._create_terminal_node()

        # Choose node type
        node_types = ["action", "conditional", "sequence", "random_choice"]
        if max_depth > 3:  # Only allow complex nodes if we have enough depth
            node_types.extend(["repeat"])

        node_type = random.choice(node_types)

        if node_type == "action":
            return self._create_terminal_node()

        elif node_type == "conditional":
            condition = self._create_condition_node()
            true_branch = self._create_random_node(max_depth - 1)
            false_branch = self._create_random_node(max_depth - 1)
            return ConditionalNode("conditional", condition=condition,
                                 true_branch=true_branch, false_branch=false_branch)

        elif node_type == "sequence":
            child_count = random.randint(2, 4)
            children = [self._create_random_node(max_depth - 1) for _ in range(child_count)]
            return SequenceNode("sequence", children=children)

        elif node_type == "random_choice":
            choice_count = random.randint(2, 5)
            choices = [self._create_random_node(max_depth - 1) for _ in range(choice_count)]
            return RandomChoiceNode("random_choice", choices=choices)

        elif node_type == "repeat":
            child = self._create_random_node(max_depth - 1)
            repeat_count = random.randint(1, 3)
            return RepeatNode("repeat", child=child, repeat_count=repeat_count)

        else:
            return self._create_terminal_node()

    def _create_terminal_node(self) -> AlgorithmNode:
        """Create a terminal (leaf) node."""
        action_type = random.choice(ACTION_TYPES)

        if action_type == "ACTION6":
            # Add random coordinates for ACTION6
            coordinates = {
                "x": random.randint(0, 63),
                "y": random.randint(0, 63)
            }
            return ActionNode("action", action_type=action_type, coordinates=coordinates)
        else:
            return ActionNode("action", action_type=action_type)

    def _create_condition_node(self) -> ConditionNode:
        """Create a random condition node."""
        condition_type = random.choice(list(CONDITION_TYPES.keys()))
        condition_info = CONDITION_TYPES[condition_type]

        parameters = {}
        if condition_type == "score_threshold":
            parameters = {
                "threshold": random.randint(10, 100),
                "operator": random.choice(["greater_than", "less_than", "equal"])
            }
        elif condition_type == "action_count":
            parameters = {
                "count": random.randint(1, 20),
                "operator": random.choice(["greater_than", "less_than", "equal"])
            }
        elif condition_type == "frame_changed":
            parameters = {
                "within_last_actions": random.randint(1, 5)
            }
        elif condition_type == "available_actions":
            required_actions = random.sample(ACTION_TYPES, random.randint(1, 3))
            parameters = {
                "required_actions": required_actions
            }
        elif condition_type == "coordinate_success":
            parameters = {
                "success_rate_threshold": random.uniform(0.3, 0.9)
            }

        return ConditionNode("condition", condition_type=condition_type, parameters=parameters)

    def evolve_population(self, fitness_scores: List[float]) -> List[AlgorithmRepresentation]:
        """Evolve the population for one generation."""
        if len(fitness_scores) != len(self.population):
            raise ValueError("Fitness scores must match population size")

        logger.info(f"Evolving generation {self.generation}")

        # Update fitness scores
        for i, algorithm in enumerate(self.population):
            algorithm.fitness_score = fitness_scores[i]

        # Calculate statistics
        stats = self._calculate_evolution_stats()
        self.evolution_stats.append(stats)

        # Create new population
        new_population = []

        # Elitism: keep best algorithms
        elite_count = int(self.config.population_size * self.config.elitism_rate)
        sorted_population = sorted(self.population, key=lambda x: x.fitness_score, reverse=True)

        for i in range(elite_count):
            elite = copy.deepcopy(sorted_population[i])
            elite.generation = self.generation + 1
            elite.algorithm_id = f"gen{self.generation + 1}_elite_{i:03d}"
            new_population.append(elite)

        # Generate offspring through crossover and mutation
        while len(new_population) < self.config.population_size:
            if random.random() < self.config.crossover_rate:
                # Crossover
                parent1 = self._tournament_selection()
                parent2 = self._tournament_selection()
                offspring1, offspring2 = self._crossover(parent1, parent2)

                new_population.extend([offspring1, offspring2])
            else:
                # Copy and mutate
                parent = self._tournament_selection()
                offspring = self._mutate(copy.deepcopy(parent))
                new_population.append(offspring)

        # Trim to exact population size
        new_population = new_population[:self.config.population_size]

        # Update generation and IDs
        for i, algorithm in enumerate(new_population):
            if algorithm.generation != self.generation + 1:  # Skip elites
                algorithm.generation = self.generation + 1
                algorithm.algorithm_id = f"gen{self.generation + 1}_algo_{i:03d}"

        self.generation += 1
        self.population = new_population

        logger.info(f"Generation {self.generation} complete. "
                   f"Best fitness: {stats['best_fitness']:.3f}, "
                   f"Avg fitness: {stats['avg_fitness']:.3f}")

        return self.population

    def _tournament_selection(self) -> AlgorithmRepresentation:
        """Select an algorithm using tournament selection."""
        tournament = random.sample(self.population, min(self.config.tournament_size, len(self.population)))
        return max(tournament, key=lambda x: x.fitness_score)

    def _crossover(self, parent1: AlgorithmRepresentation,
                  parent2: AlgorithmRepresentation) -> Tuple[AlgorithmRepresentation, AlgorithmRepresentation]:
        """Perform crossover between two parent algorithms."""
        offspring1 = copy.deepcopy(parent1)
        offspring2 = copy.deepcopy(parent2)

        # Get all nodes from both parents
        nodes1 = offspring1.get_all_nodes()
        nodes2 = offspring2.get_all_nodes()

        if len(nodes1) < 2 or len(nodes2) < 2:
            # Can't perform crossover, return mutated copies
            return self._mutate(offspring1), self._mutate(offspring2)

        # Select crossover points (avoid root nodes)
        crossover_node1 = random.choice(nodes1[1:]) if len(nodes1) > 1 else nodes1[0]
        crossover_node2 = random.choice(nodes2[1:]) if len(nodes2) > 1 else nodes2[0]

        # Perform subtree exchange
        try:
            self._exchange_subtrees(offspring1, crossover_node1.node_id, offspring2, crossover_node2.node_id)
        except Exception as e:
            logger.warning(f"Crossover failed: {e}. Returning mutated parents.")
            return self._mutate(offspring1), self._mutate(offspring2)

        # Update metadata
        offspring1.parent_ids = [parent1.algorithm_id, parent2.algorithm_id]
        offspring2.parent_ids = [parent1.algorithm_id, parent2.algorithm_id]

        return offspring1, offspring2

    def _exchange_subtrees(self, alg1: AlgorithmRepresentation, node_id1: str,
                          alg2: AlgorithmRepresentation, node_id2: str):
        """Exchange subtrees between two algorithms."""
        # This is a simplified implementation
        # In practice, this would need more sophisticated tree manipulation
        node1 = self._find_node_by_id(alg1.root_node, node_id1)
        node2 = self._find_node_by_id(alg2.root_node, node_id2)

        if node1 and node2:
            # Simple exchange - replace the entire nodes
            parent1 = self._find_parent_node(alg1.root_node, node_id1)
            parent2 = self._find_parent_node(alg2.root_node, node_id2)

            if parent1 and parent2:
                self._replace_child_node(parent1, node_id1, copy.deepcopy(node2))
                self._replace_child_node(parent2, node_id2, copy.deepcopy(node1))

    def _find_node_by_id(self, root: AlgorithmNode, node_id: str) -> Optional[AlgorithmNode]:
        """Find a node by its ID in the tree."""
        if root.node_id == node_id:
            return root

        if isinstance(root, ConditionalNode):
            result = self._find_node_by_id(root.condition, node_id)
            if result:
                return result
            result = self._find_node_by_id(root.true_branch, node_id)
            if result:
                return result
            return self._find_node_by_id(root.false_branch, node_id)

        elif isinstance(root, SequenceNode):
            for child in root.children:
                result = self._find_node_by_id(child, node_id)
                if result:
                    return result

        elif isinstance(root, RandomChoiceNode):
            for choice in root.choices:
                result = self._find_node_by_id(choice, node_id)
                if result:
                    return result

        elif isinstance(root, RepeatNode):
            return self._find_node_by_id(root.child, node_id)

        return None

    def _find_parent_node(self, root: AlgorithmNode, target_id: str) -> Optional[AlgorithmNode]:
        """Find the parent of a node with the given ID."""
        if isinstance(root, ConditionalNode):
            if (root.condition.node_id == target_id or
                root.true_branch.node_id == target_id or
                root.false_branch.node_id == target_id):
                return root

            result = self._find_parent_node(root.condition, target_id)
            if result:
                return result
            result = self._find_parent_node(root.true_branch, target_id)
            if result:
                return result
            return self._find_parent_node(root.false_branch, target_id)

        elif isinstance(root, SequenceNode):
            for child in root.children:
                if child.node_id == target_id:
                    return root
                result = self._find_parent_node(child, target_id)
                if result:
                    return result

        elif isinstance(root, RandomChoiceNode):
            for choice in root.choices:
                if choice.node_id == target_id:
                    return root
                result = self._find_parent_node(choice, target_id)
                if result:
                    return result

        elif isinstance(root, RepeatNode):
            if root.child.node_id == target_id:
                return root
            return self._find_parent_node(root.child, target_id)

        return None

    def _replace_child_node(self, parent: AlgorithmNode, old_id: str, new_node: AlgorithmNode):
        """Replace a child node with a new node."""
        if isinstance(parent, ConditionalNode):
            if parent.condition.node_id == old_id:
                parent.condition = new_node
            elif parent.true_branch.node_id == old_id:
                parent.true_branch = new_node
            elif parent.false_branch.node_id == old_id:
                parent.false_branch = new_node

        elif isinstance(parent, SequenceNode):
            for i, child in enumerate(parent.children):
                if child.node_id == old_id:
                    parent.children[i] = new_node
                    break

        elif isinstance(parent, RandomChoiceNode):
            for i, choice in enumerate(parent.choices):
                if choice.node_id == old_id:
                    parent.choices[i] = new_node
                    break

        elif isinstance(parent, RepeatNode):
            if parent.child.node_id == old_id:
                parent.child = new_node

    def _mutate(self, algorithm: AlgorithmRepresentation) -> AlgorithmRepresentation:
        """Apply mutation to an algorithm."""
        if random.random() > self.config.mutation_rate:
            return algorithm

        nodes = algorithm.get_all_nodes()
        if not nodes:
            return algorithm

        mutation_type = random.choice(["point_mutation", "subtree_replacement", "parameter_mutation"])

        try:
            if mutation_type == "point_mutation":
                self._point_mutation(algorithm, nodes)
            elif mutation_type == "subtree_replacement":
                self._subtree_replacement(algorithm, nodes)
            elif mutation_type == "parameter_mutation":
                self._parameter_mutation(algorithm, nodes)
        except Exception as e:
            logger.warning(f"Mutation failed: {e}")

        return algorithm

    def _point_mutation(self, algorithm: AlgorithmRepresentation, nodes: List[AlgorithmNode]):
        """Perform point mutation on a random node."""
        node = random.choice(nodes)

        if isinstance(node, ActionNode):
            # Change action type
            node.action_type = random.choice(ACTION_TYPES)
            if node.action_type == "ACTION6":
                node.coordinates = {
                    "x": random.randint(0, 63),
                    "y": random.randint(0, 63)
                }
            else:
                node.coordinates = None

        elif isinstance(node, ConditionNode):
            # Change condition parameters
            if node.condition_type == "score_threshold":
                node.parameters["threshold"] = random.randint(10, 100)
            elif node.condition_type == "action_count":
                node.parameters["count"] = random.randint(1, 20)

    def _subtree_replacement(self, algorithm: AlgorithmRepresentation, nodes: List[AlgorithmNode]):
        """Replace a subtree with a new random subtree."""
        if len(nodes) < 2:
            return

        # Don't replace root node
        node = random.choice(nodes[1:])
        parent = self._find_parent_node(algorithm.root_node, node.node_id)

        if parent:
            new_subtree = self._create_random_node(3)  # Small subtree
            self._replace_child_node(parent, node.node_id, new_subtree)

    def _parameter_mutation(self, algorithm: AlgorithmRepresentation, nodes: List[AlgorithmNode]):
        """Mutate parameters of existing nodes."""
        condition_nodes = [n for n in nodes if isinstance(n, ConditionNode)]
        action_nodes = [n for n in nodes if isinstance(n, ActionNode)]

        if condition_nodes and random.random() < 0.5:
            node = random.choice(condition_nodes)
            if node.condition_type == "score_threshold":
                # Mutate threshold
                current = node.parameters.get("threshold", 50)
                mutation = random.randint(-20, 20)
                node.parameters["threshold"] = max(0, min(100, current + mutation))

        if action_nodes and random.random() < 0.5:
            node = random.choice(action_nodes)
            if node.action_type == "ACTION6" and node.coordinates:
                # Mutate coordinates
                node.coordinates["x"] = max(0, min(63, node.coordinates["x"] + random.randint(-10, 10)))
                node.coordinates["y"] = max(0, min(63, node.coordinates["y"] + random.randint(-10, 10)))

    def _calculate_evolution_stats(self) -> Dict[str, Any]:
        """Calculate statistics for the current generation."""
        fitness_scores = [alg.fitness_score for alg in self.population]

        stats = {
            "generation": self.generation,
            "population_size": len(self.population),
            "best_fitness": max(fitness_scores) if fitness_scores else 0.0,
            "worst_fitness": min(fitness_scores) if fitness_scores else 0.0,
            "avg_fitness": sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0.0,
            "diversity_metric": self._calculate_diversity(),
            "avg_depth": sum(alg.get_depth() for alg in self.population) / len(self.population),
            "avg_nodes": sum(len(alg.get_all_nodes()) for alg in self.population) / len(self.population)
        }

        return stats

    def _calculate_diversity(self) -> float:
        """Calculate population diversity metric."""
        # Simple diversity measure based on algorithm structure differences
        total_comparisons = 0
        different_structures = 0

        for i in range(len(self.population)):
            for j in range(i + 1, len(self.population)):
                total_comparisons += 1
                if self._are_structurally_different(self.population[i], self.population[j]):
                    different_structures += 1

        return different_structures / total_comparisons if total_comparisons > 0 else 0.0

    def _are_structurally_different(self, alg1: AlgorithmRepresentation,
                                   alg2: AlgorithmRepresentation) -> bool:
        """Check if two algorithms are structurally different."""
        # Simple check based on tree depth and node count
        return (abs(alg1.get_depth() - alg2.get_depth()) > 1 or
                abs(len(alg1.get_all_nodes()) - len(alg2.get_all_nodes())) > 2)

    def get_best_algorithms(self, count: int = 5) -> List[AlgorithmRepresentation]:
        """Get the best performing algorithms from current population."""
        sorted_population = sorted(self.population, key=lambda x: x.fitness_score, reverse=True)
        return sorted_population[:count]

    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of evolution progress."""
        if not self.evolution_stats:
            return {"message": "No evolution data available"}

        return {
            "total_generations": len(self.evolution_stats),
            "current_generation": self.generation,
            "best_ever_fitness": max(stat["best_fitness"] for stat in self.evolution_stats),
            "final_avg_fitness": self.evolution_stats[-1]["avg_fitness"] if self.evolution_stats else 0.0,
            "diversity_trend": [stat["diversity_metric"] for stat in self.evolution_stats[-10:]],
            "fitness_trend": [stat["best_fitness"] for stat in self.evolution_stats[-10:]],
            "population_size": self.config.population_size
        }