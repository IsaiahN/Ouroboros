#!/usr/bin/env python3
"""
SELF-MODIFYING EVOLUTION ENGINE
===============================
Revolutionary genetic programming system for evolving self-modifying algorithms and strategies.

This system implements advanced evolutionary computation with:
- Genetic programming for algorithm evolution
- Self-modifying code generation and optimization
- Multi-objective fitness evaluation
- Advanced crossover and mutation operations
- Meta-evolution of evolutionary parameters
- Dynamic strategy synthesis and adaptation
"""

import os
import sys

# Disable Python bytecode generation
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import ast
import copy
import json
import time
import logging
import sqlite3
import random
import math
import inspect
from typing import Dict, List, Tuple, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import threading
import hashlib
import numpy as np

logger = logging.getLogger(__name__)

class EvolutionTarget(Enum):
    """Targets for evolutionary optimization."""
    STRATEGY_FUNCTION = "strategy_function"
    DECISION_TREE = "decision_tree"
    PARAMETER_SET = "parameter_set"
    ACTION_SEQUENCE = "action_sequence"
    COORDINATION_LOGIC = "coordination_logic"

class GeneticOperator(Enum):
    """Types of genetic operators."""
    CROSSOVER = "crossover"
    MUTATION = "mutation"
    SELECTION = "selection"
    REPRODUCTION = "reproduction"

class FitnessMetric(Enum):
    """Fitness evaluation metrics."""
    SCORE_IMPROVEMENT = "score_improvement"
    WIN_RATE = "win_rate"
    EFFICIENCY = "efficiency"
    ADAPTABILITY = "adaptability"
    ROBUSTNESS = "robustness"
    NOVELTY = "novelty"

@dataclass
class Gene:
    """Basic unit of genetic information."""
    gene_id: str
    gene_type: str
    content: Any
    metadata: Dict[str, Any]
    fitness_contribution: float

@dataclass
class Chromosome:
    """Collection of genes representing a complete solution."""
    chromosome_id: str
    genes: List[Gene]
    phenotype: str  # Generated code/strategy
    fitness_scores: Dict[FitnessMetric, float]
    generation: int
    parent_ids: List[str]
    creation_method: str

@dataclass
class Individual:
    """Single individual in the evolutionary population."""
    individual_id: str
    chromosome: Chromosome
    age: int
    performance_history: List[float]
    specialization: str
    adaptation_rate: float

class GeneticProgrammingEngine:
    """Core genetic programming engine for code evolution."""

    def __init__(self):
        """Initialize genetic programming engine."""
        self.function_primitives = [
            'if', 'elif', 'else', 'for', 'while',
            'def', 'return', 'and', 'or', 'not',
            '+', '-', '*', '/', '%', '**',
            '>', '<', '>=', '<=', '==', '!=',
            'min', 'max', 'abs', 'round', 'len'
        ]

        self.terminal_primitives = [
            'score', 'action_number', 'available_actions',
            'game_progress', 'coordinates', 'random_value',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            '0.1', '0.5', '1.0', 'True', 'False'
        ]

        self.code_templates = {
            'action_selector': """
def evolved_action_selector(context):
    score = context.get('score', 0)
    actions = context.get('available_actions', [])
    progress = context.get('game_progress', 0)

    {evolved_logic}

    return actions[0] if actions else 1
""",
            'coordinate_generator': """
def evolved_coordinate_generator(context):
    score = context.get('score', 0)
    progress = context.get('game_progress', 0)
    history = context.get('coordinate_history', [])

    {evolved_logic}

    return (32, 32)  # Default fallback
""",
            'strategy_evaluator': """
def evolved_strategy_evaluator(context, action, coordinates):
    {evolved_logic}

    return 0.5  # Default evaluation
"""
        }

    def generate_random_expression(self, depth: int = 3, expression_type: str = 'condition') -> str:
        """Generate random code expression."""
        if depth <= 0:
            return random.choice(self.terminal_primitives)

        if expression_type == 'condition':
            left = self.generate_random_expression(depth - 1, 'value')
            operator = random.choice(['>', '<', '>=', '<=', '==', '!='])
            right = self.generate_random_expression(depth - 1, 'value')
            return f"({left} {operator} {right})"

        elif expression_type == 'value':
            if random.random() < 0.3:  # Terminal
                return random.choice(self.terminal_primitives)
            else:  # Function
                func = random.choice(['+', '-', '*', '/', 'min', 'max'])
                if func in ['+', '-', '*', '/']:
                    left = self.generate_random_expression(depth - 1, 'value')
                    right = self.generate_random_expression(depth - 1, 'value')
                    return f"({left} {func} {right})"
                else:
                    arg1 = self.generate_random_expression(depth - 1, 'value')
                    arg2 = self.generate_random_expression(depth - 1, 'value')
                    return f"{func}({arg1}, {arg2})"

        return "1"  # Fallback

    def generate_random_code_block(self, template: str, complexity: int = 3) -> str:
        """Generate random code block based on template."""
        logic_parts = []

        # Generate conditional logic
        for i in range(complexity):
            condition = self.generate_random_expression(2, 'condition')
            action_logic = self.generate_action_logic()

            if i == 0:
                logic_parts.append(f"    if {condition}:")
            else:
                logic_parts.append(f"    elif {condition}:")

            logic_parts.append(f"        {action_logic}")

        # Add final else clause
        default_logic = self.generate_action_logic()
        logic_parts.append(f"    else:")
        logic_parts.append(f"        {default_logic}")

        evolved_logic = '\n'.join(logic_parts)
        return template.format(evolved_logic=evolved_logic)

    def generate_action_logic(self) -> str:
        """Generate action selection logic."""
        options = [
            "return actions[0] if actions else 1",
            "return random.choice(actions) if actions else 1",
            "return actions[int(score) % len(actions)] if actions else 1",
            "return actions[int(progress * len(actions))] if actions else 1",
            "return min(actions) if actions else 1",
            "return max(actions) if actions else 1"
        ]
        return random.choice(options)

    def crossover_code(self, parent1_code: str, parent2_code: str) -> str:
        """Perform crossover between two code strings."""
        try:
            # Parse code into AST
            tree1 = ast.parse(parent1_code)
            tree2 = ast.parse(parent2_code)

            # Find function definitions
            func1 = None
            func2 = None

            for node in ast.walk(tree1):
                if isinstance(node, ast.FunctionDef):
                    func1 = node
                    break

            for node in ast.walk(tree2):
                if isinstance(node, ast.FunctionDef):
                    func2 = node
                    break

            if func1 and func2:
                # Simple crossover: swap parts of function bodies
                if len(func1.body) > 1 and len(func2.body) > 1:
                    crossover_point1 = random.randint(1, len(func1.body) - 1)
                    crossover_point2 = random.randint(1, len(func2.body) - 1)

                    # Create offspring
                    new_body = func1.body[:crossover_point1] + func2.body[crossover_point2:]
                    func1.body = new_body

                    # Generate code from modified AST
                    return ast.unparse(tree1)

        except Exception as e:
            logger.debug(f"Crossover failed, using mutation: {e}")

        # Fallback to mutation if crossover fails
        return self.mutate_code(parent1_code)

    def mutate_code(self, code: str, mutation_rate: float = 0.3) -> str:
        """Mutate code by randomly modifying parts."""
        try:
            tree = ast.parse(code)

            # Find nodes that can be mutated
            mutable_nodes = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.Constant, ast.Compare, ast.BinOp)):
                    mutable_nodes.append(node)

            if mutable_nodes and random.random() < mutation_rate:
                # Randomly select a node to mutate
                target_node = random.choice(mutable_nodes)

                if isinstance(target_node, ast.Constant):
                    # Mutate constant values
                    if isinstance(target_node.value, (int, float)):
                        target_node.value += random.uniform(-1, 1)
                elif isinstance(target_node, ast.Compare):
                    # Mutate comparison operators
                    ops = [ast.Lt(), ast.Gt(), ast.LtE(), ast.GtE(), ast.Eq(), ast.NotEq()]
                    target_node.ops = [random.choice(ops)]

                return ast.unparse(tree)

        except Exception as e:
            logger.debug(f"Mutation failed: {e}")

        return code  # Return original if mutation fails

class FitnessEvaluator:
    """Evaluates fitness of evolved solutions."""

    def __init__(self):
        """Initialize fitness evaluator."""
        self.evaluation_history = defaultdict(list)
        self.baseline_performance = {
            FitnessMetric.SCORE_IMPROVEMENT: 0.1,
            FitnessMetric.WIN_RATE: 0.05,
            FitnessMetric.EFFICIENCY: 0.3,
            FitnessMetric.ADAPTABILITY: 0.5,
            FitnessMetric.ROBUSTNESS: 0.4,
            FitnessMetric.NOVELTY: 0.5
        }

    def evaluate_individual(self, individual: Individual,
                          performance_data: Dict[str, Any]) -> Dict[FitnessMetric, float]:
        """Evaluate fitness of an individual."""
        fitness_scores = {}

        # Score improvement fitness
        score_improvement = performance_data.get('score_change', 0.0)
        fitness_scores[FitnessMetric.SCORE_IMPROVEMENT] = self._normalize_fitness(
            score_improvement, self.baseline_performance[FitnessMetric.SCORE_IMPROVEMENT]
        )

        # Win rate fitness
        win_rate = performance_data.get('win_rate', 0.0)
        fitness_scores[FitnessMetric.WIN_RATE] = self._normalize_fitness(
            win_rate, self.baseline_performance[FitnessMetric.WIN_RATE]
        )

        # Efficiency fitness (score per action)
        efficiency = performance_data.get('efficiency', 0.0)
        fitness_scores[FitnessMetric.EFFICIENCY] = self._normalize_fitness(
            efficiency, self.baseline_performance[FitnessMetric.EFFICIENCY]
        )

        # Adaptability fitness (performance across different contexts)
        adaptability = self._calculate_adaptability(individual, performance_data)
        fitness_scores[FitnessMetric.ADAPTABILITY] = adaptability

        # Robustness fitness (consistency of performance)
        robustness = self._calculate_robustness(individual)
        fitness_scores[FitnessMetric.ROBUSTNESS] = robustness

        # Novelty fitness (how different from existing solutions)
        novelty = self._calculate_novelty(individual)
        fitness_scores[FitnessMetric.NOVELTY] = novelty

        return fitness_scores

    def _normalize_fitness(self, value: float, baseline: float) -> float:
        """Normalize fitness value relative to baseline."""
        if baseline <= 0:
            return 0.5

        normalized = value / baseline
        return min(max(normalized, 0.0), 2.0) / 2.0  # Scale to [0, 1]

    def _calculate_adaptability(self, individual: Individual,
                              performance_data: Dict[str, Any]) -> float:
        """Calculate adaptability based on performance across contexts."""
        context_performances = performance_data.get('context_performances', [])

        if len(context_performances) < 2:
            return 0.5  # Neutral if insufficient data

        # Adaptability is high if performance is consistent across contexts
        variance = np.var(context_performances)
        mean_performance = np.mean(context_performances)

        # Lower variance and higher mean = better adaptability
        adaptability = mean_performance * (1.0 - min(variance, 1.0))
        return min(max(adaptability, 0.0), 1.0)

    def _calculate_robustness(self, individual: Individual) -> float:
        """Calculate robustness based on performance consistency."""
        if len(individual.performance_history) < 3:
            return 0.5

        # Robustness is inverse of performance variance
        variance = np.var(individual.performance_history)
        robustness = 1.0 / (1.0 + variance)
        return min(max(robustness, 0.0), 1.0)

    def _calculate_novelty(self, individual: Individual) -> float:
        """Calculate novelty by comparing to previously evaluated individuals."""
        # Simple novelty based on code similarity
        code_hash = hashlib.md5(individual.chromosome.phenotype.encode()).hexdigest()

        # Check against recent evaluations
        recent_hashes = self.evaluation_history.get('code_hashes', [])

        if code_hash in recent_hashes:
            novelty = 0.1  # Low novelty for duplicate code
        else:
            novelty = 1.0 - (len(recent_hashes) / 100.0)  # Decrease novelty as population grows
            recent_hashes.append(code_hash)

            # Keep only recent hashes
            if len(recent_hashes) > 100:
                self.evaluation_history['code_hashes'] = recent_hashes[-100:]

        return min(max(novelty, 0.0), 1.0)

class SelfModifyingEvolutionEngine:
    """Revolutionary self-modifying evolution engine."""

    def __init__(self, db_path: str = "core_data.db"):
        """Initialize the self-modifying evolution engine."""
        self.db_path = db_path

        # Evolution components
        self.genetic_engine = GeneticProgrammingEngine()
        self.fitness_evaluator = FitnessEvaluator()

        # Population management
        self.population: Dict[str, Individual] = {}
        self.population_size = 50
        self.generation = 0
        self.elite_size = 10

        # Evolution parameters (self-modifying)
        self.evolution_params = {
            'mutation_rate': 0.2,
            'crossover_rate': 0.7,
            'selection_pressure': 0.8,
            'elite_preservation': 0.2,
            'novelty_weight': 0.3,
            'complexity_penalty': 0.1
        }

        # Performance tracking
        self.generation_stats = []
        self.best_individuals = deque(maxlen=100)
        self.evolution_history = deque(maxlen=1000)

        # Active evolved solutions
        self.active_solutions: Dict[str, Callable] = {}
        self.solution_performance: Dict[str, List[float]] = defaultdict(list)

        logger.info("SelfModifyingEvolutionEngine initialized with genetic programming capabilities")

    def initialize_population(self):
        """Initialize the starting population with random individuals."""
        for i in range(self.population_size):
            individual = self._create_random_individual(f"gen0_ind{i:03d}")
            self.population[individual.individual_id] = individual

        logger.info(f"Initialized population with {len(self.population)} individuals")

    def _create_random_individual(self, individual_id: str) -> Individual:
        """Create a random individual."""
        # Randomly select evolution target
        target = random.choice(list(EvolutionTarget))

        # Generate random genes
        genes = []
        for j in range(random.randint(3, 8)):
            gene = Gene(
                gene_id=f"{individual_id}_gene_{j}",
                gene_type=random.choice(['logic', 'parameter', 'condition']),
                content=self.genetic_engine.generate_random_expression(),
                metadata={'position': j, 'active': True},
                fitness_contribution=0.0
            )
            genes.append(gene)

        # Generate phenotype (code)
        template = random.choice(list(self.genetic_engine.code_templates.values()))
        phenotype = self.genetic_engine.generate_random_code_block(template)

        # Create chromosome
        chromosome = Chromosome(
            chromosome_id=f"{individual_id}_chr",
            genes=genes,
            phenotype=phenotype,
            fitness_scores={},
            generation=self.generation,
            parent_ids=[],
            creation_method='random'
        )

        # Create individual
        individual = Individual(
            individual_id=individual_id,
            chromosome=chromosome,
            age=0,
            performance_history=[],
            specialization=target.value,
            adaptation_rate=random.uniform(0.1, 0.5)
        )

        return individual

    def evolve_generation(self, performance_data: Dict[str, Dict[str, Any]]):
        """Evolve one generation of the population."""
        # Evaluate current population
        self._evaluate_population(performance_data)

        # Select parents for next generation
        parents = self._select_parents()

        # Create new generation
        new_population = {}

        # Preserve elite individuals
        elite_count = int(self.population_size * self.evolution_params['elite_preservation'])
        elite_individuals = sorted(
            self.population.values(),
            key=lambda x: self._calculate_overall_fitness(x),
            reverse=True
        )[:elite_count]

        for individual in elite_individuals:
            individual.age += 1
            new_population[individual.individual_id] = individual

        # Generate offspring
        while len(new_population) < self.population_size:
            if random.random() < self.evolution_params['crossover_rate']:
                # Crossover
                parent1, parent2 = random.sample(parents, 2)
                offspring = self._crossover(parent1, parent2)
            else:
                # Mutation only
                parent = random.choice(parents)
                offspring = self._mutate(parent)

            new_population[offspring.individual_id] = offspring

        # Update population
        self.population = new_population
        self.generation += 1

        # Update evolution parameters (self-modification)
        self._adapt_evolution_parameters()

        # Track generation statistics
        self._record_generation_stats()

        logger.info(f"Evolved generation {self.generation}: {len(self.population)} individuals")

    def _evaluate_population(self, performance_data: Dict[str, Dict[str, Any]]):
        """Evaluate fitness of all individuals in population."""
        for individual in self.population.values():
            # Get performance data for this individual
            individual_data = performance_data.get(individual.individual_id, {})

            # Evaluate fitness
            fitness_scores = self.fitness_evaluator.evaluate_individual(individual, individual_data)
            individual.chromosome.fitness_scores = fitness_scores

            # Update performance history
            overall_fitness = self._calculate_overall_fitness(individual)
            individual.performance_history.append(overall_fitness)

            # Limit history size
            if len(individual.performance_history) > 50:
                individual.performance_history = individual.performance_history[-50:]

    def _calculate_overall_fitness(self, individual: Individual) -> float:
        """Calculate overall fitness score for an individual."""
        fitness_scores = individual.chromosome.fitness_scores

        if not fitness_scores:
            return 0.0

        # Weighted combination of fitness metrics
        weights = {
            FitnessMetric.SCORE_IMPROVEMENT: 0.3,
            FitnessMetric.WIN_RATE: 0.25,
            FitnessMetric.EFFICIENCY: 0.2,
            FitnessMetric.ADAPTABILITY: 0.1,
            FitnessMetric.ROBUSTNESS: 0.1,
            FitnessMetric.NOVELTY: 0.05
        }

        overall_fitness = 0.0
        for metric, weight in weights.items():
            fitness_value = fitness_scores.get(metric, 0.0)
            overall_fitness += fitness_value * weight

        # Apply complexity penalty
        code_complexity = len(individual.chromosome.phenotype) / 1000.0  # Normalize by code length
        complexity_penalty = self.evolution_params['complexity_penalty'] * code_complexity
        overall_fitness = max(0.0, overall_fitness - complexity_penalty)

        return overall_fitness

    def _select_parents(self) -> List[Individual]:
        """Select parents for reproduction using tournament selection."""
        parents = []
        tournament_size = 3

        for _ in range(self.population_size):
            # Tournament selection
            tournament = random.sample(list(self.population.values()), tournament_size)
            winner = max(tournament, key=self._calculate_overall_fitness)
            parents.append(winner)

        return parents

    def _crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """Create offspring through crossover."""
        offspring_id = f"gen{self.generation + 1}_cross_{random.randint(1000, 9999)}"

        # Crossover phenotypes (code)
        offspring_phenotype = self.genetic_engine.crossover_code(
            parent1.chromosome.phenotype,
            parent2.chromosome.phenotype
        )

        # Combine genes from parents
        offspring_genes = []
        parent1_genes = parent1.chromosome.genes
        parent2_genes = parent2.chromosome.genes

        crossover_point = random.randint(1, min(len(parent1_genes), len(parent2_genes)) - 1)

        offspring_genes.extend(parent1_genes[:crossover_point])
        offspring_genes.extend(parent2_genes[crossover_point:])

        # Create offspring chromosome
        offspring_chromosome = Chromosome(
            chromosome_id=f"{offspring_id}_chr",
            genes=offspring_genes,
            phenotype=offspring_phenotype,
            fitness_scores={},
            generation=self.generation + 1,
            parent_ids=[parent1.individual_id, parent2.individual_id],
            creation_method='crossover'
        )

        # Create offspring individual
        offspring = Individual(
            individual_id=offspring_id,
            chromosome=offspring_chromosome,
            age=0,
            performance_history=[],
            specialization=random.choice([parent1.specialization, parent2.specialization]),
            adaptation_rate=(parent1.adaptation_rate + parent2.adaptation_rate) / 2.0
        )

        return offspring

    def _mutate(self, parent: Individual) -> Individual:
        """Create offspring through mutation."""
        offspring_id = f"gen{self.generation + 1}_mut_{random.randint(1000, 9999)}"

        # Mutate phenotype (code)
        offspring_phenotype = self.genetic_engine.mutate_code(
            parent.chromosome.phenotype,
            self.evolution_params['mutation_rate']
        )

        # Mutate genes
        offspring_genes = []
        for gene in parent.chromosome.genes:
            if random.random() < self.evolution_params['mutation_rate']:
                # Mutate this gene
                mutated_gene = Gene(
                    gene_id=f"{offspring_id}_gene_{len(offspring_genes)}",
                    gene_type=gene.gene_type,
                    content=self.genetic_engine.generate_random_expression(),
                    metadata=gene.metadata.copy(),
                    fitness_contribution=gene.fitness_contribution
                )
                offspring_genes.append(mutated_gene)
            else:
                # Keep original gene
                offspring_genes.append(copy.deepcopy(gene))

        # Create offspring chromosome
        offspring_chromosome = Chromosome(
            chromosome_id=f"{offspring_id}_chr",
            genes=offspring_genes,
            phenotype=offspring_phenotype,
            fitness_scores={},
            generation=self.generation + 1,
            parent_ids=[parent.individual_id],
            creation_method='mutation'
        )

        # Create offspring individual
        offspring = Individual(
            individual_id=offspring_id,
            chromosome=offspring_chromosome,
            age=0,
            performance_history=[],
            specialization=parent.specialization,
            adaptation_rate=parent.adaptation_rate
        )

        return offspring

    def _adapt_evolution_parameters(self):
        """Adapt evolution parameters based on population performance (meta-evolution)."""
        if self.generation < 5:
            return  # Need some history to adapt

        # Analyze recent performance trends
        recent_best_fitness = []
        for stats in self.generation_stats[-5:]:
            recent_best_fitness.append(stats.get('best_fitness', 0.0))

        if len(recent_best_fitness) >= 3:
            # Calculate improvement trend
            improvement = recent_best_fitness[-1] - recent_best_fitness[0]

            # Adapt mutation rate
            if improvement < 0.01:  # Stagnation
                self.evolution_params['mutation_rate'] = min(0.5, self.evolution_params['mutation_rate'] * 1.2)
                self.evolution_params['novelty_weight'] = min(0.5, self.evolution_params['novelty_weight'] * 1.1)
            elif improvement > 0.05:  # Good progress
                self.evolution_params['mutation_rate'] = max(0.1, self.evolution_params['mutation_rate'] * 0.9)

            # Adapt crossover rate
            avg_diversity = self._calculate_population_diversity()
            if avg_diversity < 0.3:  # Low diversity
                self.evolution_params['crossover_rate'] = min(0.9, self.evolution_params['crossover_rate'] * 1.1)
            elif avg_diversity > 0.8:  # High diversity
                self.evolution_params['crossover_rate'] = max(0.5, self.evolution_params['crossover_rate'] * 0.9)

        logger.debug(f"Adapted evolution parameters: {self.evolution_params}")

    def _calculate_population_diversity(self) -> float:
        """Calculate diversity of current population."""
        if len(self.population) < 2:
            return 0.0

        # Simple diversity measure based on phenotype differences
        phenotypes = [ind.chromosome.phenotype for ind in self.population.values()]
        unique_phenotypes = set(phenotypes)

        diversity = len(unique_phenotypes) / len(phenotypes)
        return diversity

    def _record_generation_stats(self):
        """Record statistics for current generation."""
        fitness_values = [self._calculate_overall_fitness(ind) for ind in self.population.values()]

        stats = {
            'generation': self.generation,
            'timestamp': time.time(),
            'population_size': len(self.population),
            'best_fitness': max(fitness_values) if fitness_values else 0.0,
            'avg_fitness': np.mean(fitness_values) if fitness_values else 0.0,
            'fitness_std': np.std(fitness_values) if fitness_values else 0.0,
            'diversity': self._calculate_population_diversity(),
            'evolution_params': self.evolution_params.copy()
        }

        self.generation_stats.append(stats)

        # Keep best individual
        if fitness_values:
            best_individual = max(self.population.values(), key=self._calculate_overall_fitness)
            self.best_individuals.append(best_individual)

        logger.info(f"Generation {self.generation} stats: "
                   f"Best fitness: {stats['best_fitness']:.3f}, "
                   f"Avg fitness: {stats['avg_fitness']:.3f}, "
                   f"Diversity: {stats['diversity']:.3f}")

    def get_best_solutions(self, count: int = 5) -> List[Individual]:
        """Get the best evolved solutions."""
        all_individuals = list(self.population.values())
        all_individuals.sort(key=self._calculate_overall_fitness, reverse=True)
        return all_individuals[:count]

    def deploy_solution(self, individual: Individual) -> str:
        """Deploy an evolved solution for active use."""
        try:
            # Attempt to compile and execute the evolved code
            compiled_code = compile(individual.chromosome.phenotype, '<evolved>', 'exec')

            # Create execution environment
            exec_globals = {
                'random': random,
                'min': min,
                'max': max,
                'abs': abs,
                'len': len,
                'range': range
            }

            exec(compiled_code, exec_globals)

            # Extract the evolved function
            evolved_function = None
            for name, obj in exec_globals.items():
                if callable(obj) and name.startswith('evolved_'):
                    evolved_function = obj
                    break

            if evolved_function:
                solution_id = f"solution_{individual.individual_id}"
                self.active_solutions[solution_id] = evolved_function

                logger.info(f"Deployed evolved solution: {solution_id}")
                return solution_id

        except Exception as e:
            logger.error(f"Failed to deploy solution: {e}")

        return ""

    def get_evolution_status(self) -> Dict[str, Any]:
        """Get current evolution system status."""
        return {
            "self_modifying_evolution_active": True,
            "generation": self.generation,
            "population_size": len(self.population),
            "active_solutions": len(self.active_solutions),
            "evolution_parameters": self.evolution_params,
            "recent_performance": {
                "best_fitness": self.generation_stats[-1]['best_fitness'] if self.generation_stats else 0.0,
                "avg_fitness": self.generation_stats[-1]['avg_fitness'] if self.generation_stats else 0.0,
                "diversity": self.generation_stats[-1]['diversity'] if self.generation_stats else 0.0
            },
            "best_individuals_count": len(self.best_individuals),
            "generations_evolved": len(self.generation_stats)
        }

# Global instance
evolution_engine = SelfModifyingEvolutionEngine()

def initialize_evolution_system():
    """Initialize the evolution system with initial population."""
    evolution_engine.initialize_population()

def evolve_new_generation(performance_data: Dict[str, Dict[str, Any]]):
    """Evolve a new generation based on performance data."""
    evolution_engine.evolve_generation(performance_data)

def get_best_evolved_solutions(count: int = 3) -> List[Dict[str, Any]]:
    """Get the best evolved solutions."""
    best_individuals = evolution_engine.get_best_solutions(count)

    solutions = []
    for individual in best_individuals:
        solution = {
            'individual_id': individual.individual_id,
            'fitness': evolution_engine._calculate_overall_fitness(individual),
            'specialization': individual.specialization,
            'generation': individual.chromosome.generation,
            'code': individual.chromosome.phenotype,
            'performance_history': individual.performance_history
        }
        solutions.append(solution)

    return solutions

def deploy_evolved_solution(individual_id: str) -> str:
    """Deploy an evolved solution for active use."""
    if individual_id in evolution_engine.population:
        individual = evolution_engine.population[individual_id]
        return evolution_engine.deploy_solution(individual)
    return ""

def get_evolution_system_status() -> Dict[str, Any]:
    """Get current evolution system status."""
    return evolution_engine.get_evolution_status()

if __name__ == "__main__":
    # Test the self-modifying evolution engine
    print("=== SELF-MODIFYING EVOLUTION ENGINE TEST ===")

    # Initialize evolution system
    initialize_evolution_system()

    # Simulate several generations of evolution
    for gen in range(5):
        # Create mock performance data
        performance_data = {}
        for individual_id in evolution_engine.population.keys():
            performance_data[individual_id] = {
                'score_change': random.uniform(-0.5, 1.0),
                'win_rate': random.uniform(0.0, 0.3),
                'efficiency': random.uniform(0.1, 0.8),
                'context_performances': [random.uniform(0.2, 0.9) for _ in range(5)]
            }

        # Evolve generation
        evolve_new_generation(performance_data)

        # Print generation results
        status = get_evolution_system_status()
        print(f"Generation {status['generation']}:")
        print(f"  Best Fitness: {status['recent_performance']['best_fitness']:.3f}")
        print(f"  Avg Fitness: {status['recent_performance']['avg_fitness']:.3f}")
        print(f"  Diversity: {status['recent_performance']['diversity']:.3f}")

    # Get best solutions
    best_solutions = get_best_evolved_solutions(3)
    print(f"\nBest Evolved Solutions:")
    for i, solution in enumerate(best_solutions):
        print(f"  Solution {i+1}:")
        print(f"    ID: {solution['individual_id']}")
        print(f"    Fitness: {solution['fitness']:.3f}")
        print(f"    Specialization: {solution['specialization']}")
        print(f"    Generation: {solution['generation']}")

    # Try to deploy best solution
    if best_solutions:
        solution_id = deploy_evolved_solution(best_solutions[0]['individual_id'])
        print(f"\nDeployed solution: {solution_id}")

    # Final status
    final_status = get_evolution_system_status()
    print(f"\nFinal Evolution Status:")
    print(f"  Active Solutions: {final_status['active_solutions']}")
    print(f"  Generations Evolved: {final_status['generations_evolved']}")
    print(f"  Evolution Parameters: {final_status['evolution_parameters']}")