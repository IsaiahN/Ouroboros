"""
Evolution Manager

Central coordinator for the algorithmic evolution system that orchestrates:
- Genetic Programming operations and population management
- Variational Autoencoder training and algorithm generation
- Multi-Armed Bandit algorithm selection
- Database persistence and system state management
- Evolution cycles and performance tracking
"""

import logging
import random
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import asyncio

from algorithm_representations import AlgorithmRepresentation, AlgorithmBuilder
from genetic_programming import GeneticProgrammingEngine, GPConfig
from variational_autoencoder import SimpleVariationalAutoencoder, VAEConfig
from multi_armed_bandit import MultiArmedBandit, MABConfig
from algorithm_evaluator import AlgorithmEvaluator, GameContext

logger = logging.getLogger(__name__)


@dataclass
class EvolutionConfig:
    """Configuration for the evolution manager."""
    # Population management
    population_size: int = 30
    elite_preservation: int = 5
    max_generations: int = 50

    # Component integration
    gp_weight: float = 0.6  # Genetic programming contribution
    vae_weight: float = 0.2  # VAE generation contribution
    mab_weight: float = 0.2  # MAB guided selection contribution

    # Evolution triggers
    evolution_frequency: int = 5  # Evolve every N games
    min_games_for_evolution: int = 10  # Minimum games before first evolution
    performance_stagnation_threshold: int = 15  # Games without improvement

    # VAE training
    vae_training_frequency: int = 10  # Train VAE every N generations
    vae_training_data_size: int = 100  # Max algorithms for VAE training

    # Algorithm lifecycle
    algorithm_retirement_age: int = 50  # Retire algorithms after N games
    min_performance_threshold: float = 10.0  # Minimum performance to keep algorithm

    # System behavior
    exploration_boost_period: int = 10  # Boost exploration for first N generations
    diversity_enforcement: bool = True  # Enforce population diversity
    adaptive_parameters: bool = True  # Automatically adjust parameters


@dataclass
class EvolutionState:
    """Current state of the evolution system."""
    current_generation: int = 0
    total_algorithms_created: int = 0
    total_games_played: int = 0
    best_fitness_ever: float = 0.0
    last_evolution_time: Optional[datetime] = None
    stagnation_counter: int = 0
    system_startup_time: Optional[datetime] = None

    def __post_init__(self):
        if self.system_startup_time is None:
            self.system_startup_time = datetime.now()


class EvolutionManager:
    """Central coordinator for the algorithmic evolution system."""

    def __init__(self, config: EvolutionConfig = None, database_interface=None):
        self.config = config or EvolutionConfig()
        self.db = database_interface
        self.state = EvolutionState()

        # Initialize core components
        self.gp_engine = GeneticProgrammingEngine(
            GPConfig(population_size=self.config.population_size)
        )

        self.vae = SimpleVariationalAutoencoder(
            VAEConfig(), database_interface
        )

        self.mab = MultiArmedBandit(
            MABConfig(), database_interface
        )

        self.evaluator = AlgorithmEvaluator()

        # Population management
        self.active_population: List[AlgorithmRepresentation] = []
        self.retired_algorithms: List[AlgorithmRepresentation] = []
        self.performance_history: Dict[str, List[float]] = {}

        # Current algorithm for gameplay
        self.current_algorithm: Optional[AlgorithmRepresentation] = None

        # System metrics
        self.evolution_metrics = []

        logger.info("Evolution Manager initialized")

    async def initialize_system(self) -> Dict[str, Any]:
        """Initialize the evolution system with an initial population.

        Returns:
            Initialization summary
        """
        logger.info("Initializing evolution system...")

        try:
            # Load existing data from database if available
            if self.db:
                await self._load_from_database()

            # Create initial population if none exists
            if not self.active_population:
                logger.info("Creating initial population...")
                self.active_population = self.gp_engine.initialize_population()

                # Add all algorithms to MAB
                for algorithm in self.active_population:
                    self.mab.add_algorithm(algorithm)

                # Save initial population to database
                if self.db:
                    await self._save_population_to_database()

            # Select initial algorithm for gameplay
            self.current_algorithm = await self._select_algorithm_for_gameplay()

            self.state.system_startup_time = datetime.now()

            summary = {
                "population_size": len(self.active_population),
                "initial_algorithm": self.current_algorithm.algorithm_id if self.current_algorithm else None,
                "generation": self.state.current_generation,
                "system_ready": True,
                "timestamp": self.state.system_startup_time.isoformat()
            }

            logger.info(f"Evolution system initialized: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Failed to initialize evolution system: {e}")
            return {"system_ready": False, "error": str(e)}

    async def get_current_algorithm(self) -> Optional[AlgorithmRepresentation]:
        """Get the current algorithm for gameplay.

        Returns:
            Current algorithm or None if not set
        """
        if not self.current_algorithm and self.active_population:
            self.current_algorithm = await self._select_algorithm_for_gameplay()

        return self.current_algorithm

    async def update_algorithm_performance(self, algorithm_id: str,
                                         game_result: Dict[str, Any]):
        """Update algorithm performance with game results.

        Args:
            algorithm_id: ID of the algorithm that was used
            game_result: Game result dictionary
        """
        try:
            # Calculate fitness from game result
            fitness = self.evaluator.calculate_fitness(
                None, [game_result]  # Single game result
            )

            # Update performance history
            if algorithm_id not in self.performance_history:
                self.performance_history[algorithm_id] = []
            self.performance_history[algorithm_id].append(fitness)

            # Update MAB with reward (normalized fitness)
            reward = min(100.0, max(0.0, fitness)) / 100.0
            self.mab.update_reward(algorithm_id, reward, {"game_result": game_result})

            # Update algorithm fitness in population
            for algorithm in self.active_population:
                if algorithm.algorithm_id == algorithm_id:
                    algorithm.fitness_score = fitness
                    break

            # Save performance to database
            if self.db:
                await self._save_performance_to_database(algorithm_id, game_result, fitness)

            # Update system state
            self.state.total_games_played += 1
            if fitness > self.state.best_fitness_ever:
                self.state.best_fitness_ever = fitness
                self.state.stagnation_counter = 0
            else:
                self.state.stagnation_counter += 1

            # Check if evolution should be triggered
            await self._check_evolution_triggers()

            logger.debug(f"Updated performance for {algorithm_id}: fitness={fitness:.2f}")

        except Exception as e:
            logger.error(f"Error updating algorithm performance: {e}")

    async def _check_evolution_triggers(self):
        """Check if evolution should be triggered based on current conditions."""
        should_evolve = False
        reason = ""

        # Check frequency-based trigger
        if self.state.total_games_played % self.config.evolution_frequency == 0:
            if self.state.total_games_played >= self.config.min_games_for_evolution:
                should_evolve = True
                reason = "frequency-based evolution"

        # Check stagnation trigger
        elif self.state.stagnation_counter >= self.config.performance_stagnation_threshold:
            should_evolve = True
            reason = "performance stagnation"

        # Check if population needs refresh
        elif len(self.active_population) < self.config.population_size // 2:
            should_evolve = True
            reason = "population depletion"

        if should_evolve:
            logger.info(f"Triggering evolution: {reason}")
            await self.evolve_population()

    async def evolve_population(self) -> Dict[str, Any]:
        """Evolve the current population using all available components.

        Returns:
            Evolution summary
        """
        logger.info(f"Starting evolution for generation {self.state.current_generation + 1}")

        try:
            evolution_start = datetime.now()

            # Collect fitness scores for current population
            fitness_scores = []
            valid_algorithms = []

            for algorithm in self.active_population:
                if algorithm.algorithm_id in self.performance_history:
                    # Use recent average performance
                    recent_performance = self.performance_history[algorithm.algorithm_id][-5:]
                    avg_fitness = sum(recent_performance) / len(recent_performance)
                    fitness_scores.append(avg_fitness)
                    valid_algorithms.append(algorithm)
                else:
                    # No performance data - assign low fitness
                    fitness_scores.append(0.0)
                    valid_algorithms.append(algorithm)

            if not valid_algorithms:
                logger.warning("No valid algorithms for evolution")
                return {"error": "No valid algorithms for evolution"}

            # Evolve using genetic programming
            gp_offspring = await self._genetic_programming_evolution(valid_algorithms, fitness_scores)

            # Generate new algorithms using VAE
            vae_offspring = await self._vae_generation()

            # Combine offspring
            all_offspring = gp_offspring + vae_offspring

            # Select new population using MAB-guided selection
            new_population = await self._select_new_population(
                valid_algorithms, all_offspring, fitness_scores
            )

            # Update population
            self.active_population = new_population

            # Retire old algorithms
            await self._retire_old_algorithms()

            # Train VAE if scheduled
            if (self.state.current_generation + 1) % self.config.vae_training_frequency == 0:
                await self._train_vae()

            # Update system state
            self.state.current_generation += 1
            self.state.last_evolution_time = datetime.now()

            # Save evolution results
            if self.db:
                await self._save_evolution_to_database()

            # Calculate evolution metrics
            evolution_duration = (datetime.now() - evolution_start).total_seconds()
            metrics = await self._calculate_evolution_metrics(evolution_duration)
            self.evolution_metrics.append(metrics)

            # Select new current algorithm
            self.current_algorithm = await self._select_algorithm_for_gameplay()

            logger.info(f"Evolution completed: generation {self.state.current_generation}, "
                       f"population size: {len(self.active_population)}")

            return metrics

        except Exception as e:
            logger.error(f"Evolution failed: {e}")
            return {"error": str(e), "generation": self.state.current_generation}

    async def _genetic_programming_evolution(self, algorithms: List[AlgorithmRepresentation],
                                           fitness_scores: List[float]) -> List[AlgorithmRepresentation]:
        """Evolve algorithms using genetic programming.

        Args:
            algorithms: Current population
            fitness_scores: Fitness scores for each algorithm

        Returns:
            List of offspring algorithms
        """
        # Update GP engine population
        self.gp_engine.population = algorithms.copy()

        # Evolve population
        evolved_population = self.gp_engine.evolve_population(fitness_scores)

        # Calculate number of offspring to return
        gp_count = int(len(evolved_population) * self.config.gp_weight)

        # Return best offspring
        offspring = []
        for i, algorithm in enumerate(evolved_population):
            if i < gp_count:
                # Create new algorithm ID for offspring
                algorithm.algorithm_id = f"gen{self.state.current_generation + 1}_gp_{i:03d}"
                self.state.total_algorithms_created += 1
                offspring.append(algorithm)

        logger.debug(f"GP evolution produced {len(offspring)} offspring")
        return offspring

    async def _vae_generation(self) -> List[AlgorithmRepresentation]:
        """Generate new algorithms using VAE.

        Returns:
            List of VAE-generated algorithms
        """
        try:
            # Calculate number of VAE algorithms to generate
            vae_count = int(self.config.population_size * self.config.vae_weight)

            if vae_count == 0:
                return []

            offspring = []
            for i in range(vae_count):
                # Generate algorithm from VAE
                algorithm = self.vae.generate_algorithm()
                algorithm.algorithm_id = f"gen{self.state.current_generation + 1}_vae_{i:03d}"
                algorithm.generation = self.state.current_generation + 1
                algorithm.metadata["generated_by"] = "VAE"

                self.state.total_algorithms_created += 1
                offspring.append(algorithm)

            logger.debug(f"VAE generation produced {len(offspring)} offspring")
            return offspring

        except Exception as e:
            logger.warning(f"VAE generation failed: {e}")
            return []

    async def _select_new_population(self, parents: List[AlgorithmRepresentation],
                                   offspring: List[AlgorithmRepresentation],
                                   parent_fitness: List[float]) -> List[AlgorithmRepresentation]:
        """Select new population from parents and offspring.

        Args:
            parents: Parent algorithms
            offspring: Offspring algorithms
            parent_fitness: Fitness scores for parents

        Returns:
            New population
        """
        # Combine parents and offspring
        all_algorithms = parents + offspring
        all_fitness = parent_fitness + [0.0] * len(offspring)  # Offspring start with 0 fitness

        # Elite selection - keep best performers
        elite_indices = sorted(range(len(parent_fitness)),
                             key=lambda i: parent_fitness[i], reverse=True)
        elite_count = min(self.config.elite_preservation, len(parents))

        new_population = []

        # Add elites
        for i in range(elite_count):
            elite_idx = elite_indices[i]
            elite = parents[elite_idx].copy() if hasattr(parents[elite_idx], 'copy') else parents[elite_idx]
            elite.algorithm_id = f"gen{self.state.current_generation + 1}_elite_{i:03d}"
            new_population.append(elite)

        # Add offspring
        remaining_slots = self.config.population_size - len(new_population)
        if offspring and remaining_slots > 0:
            # Randomly select from offspring (could be improved with MAB guidance)
            selected_offspring = random.sample(offspring, min(remaining_slots, len(offspring)))
            new_population.extend(selected_offspring)

        # Fill remaining slots with random selection from all algorithms
        while len(new_population) < self.config.population_size:
            if all_algorithms:
                selected = random.choice(all_algorithms)
                selected_copy = selected.copy() if hasattr(selected, 'copy') else selected
                selected_copy.algorithm_id = f"gen{self.state.current_generation + 1}_fill_{len(new_population):03d}"
                new_population.append(selected_copy)
            else:
                # Create new random algorithm as last resort
                new_alg = AlgorithmBuilder.create_random_action_algorithm()
                new_alg.algorithm_id = f"gen{self.state.current_generation + 1}_random_{len(new_population):03d}"
                new_population.append(new_alg)

        # Ensure diversity if configured
        if self.config.diversity_enforcement:
            new_population = await self._enforce_diversity(new_population)

        # Add all new algorithms to MAB
        for algorithm in new_population:
            self.mab.add_algorithm(algorithm)

        return new_population

    async def _enforce_diversity(self, population: List[AlgorithmRepresentation]) -> List[AlgorithmRepresentation]:
        """Enforce diversity in the population by replacing similar algorithms.

        Args:
            population: Current population

        Returns:
            Diversified population
        """
        try:
            # Simple diversity enforcement based on algorithm signatures
            signatures = {}
            diverse_population = []

            for algorithm in population:
                signature = self.evaluator.get_algorithm_signature(algorithm)

                if signature not in signatures:
                    signatures[signature] = algorithm
                    diverse_population.append(algorithm)
                elif len(diverse_population) < self.config.population_size * 0.8:
                    # Keep some duplicates but not too many
                    diverse_population.append(algorithm)

            # Fill remaining slots with new random algorithms if needed
            while len(diverse_population) < self.config.population_size:
                new_alg = AlgorithmBuilder.create_random_action_algorithm()
                new_alg.algorithm_id = f"gen{self.state.current_generation + 1}_diversity_{len(diverse_population):03d}"
                diverse_population.append(new_alg)

            return diverse_population

        except Exception as e:
            logger.warning(f"Diversity enforcement failed: {e}")
            return population

    async def _retire_old_algorithms(self):
        """Retire old or poorly performing algorithms."""
        retirement_candidates = []

        for algorithm in self.active_population:
            # Check age
            if (algorithm.algorithm_id in self.performance_history and
                len(self.performance_history[algorithm.algorithm_id]) >= self.config.algorithm_retirement_age):
                retirement_candidates.append(algorithm)

            # Check performance
            elif (algorithm.algorithm_id in self.performance_history and
                  algorithm.fitness_score < self.config.min_performance_threshold):
                retirement_candidates.append(algorithm)

        # Retire candidates (but keep minimum population)
        for candidate in retirement_candidates:
            if len(self.active_population) > self.config.population_size // 2:
                self.active_population.remove(candidate)
                self.retired_algorithms.append(candidate)

        if retirement_candidates:
            logger.info(f"Retired {len(retirement_candidates)} algorithms")

    async def _train_vae(self):
        """Train the VAE on recent algorithm data."""
        try:
            # Collect training data
            training_algorithms = []
            training_performances = []

            # Use active population
            for algorithm in self.active_population:
                if algorithm.algorithm_id in self.performance_history:
                    training_algorithms.append(algorithm)
                    avg_performance = sum(self.performance_history[algorithm.algorithm_id]) / \
                                    len(self.performance_history[algorithm.algorithm_id])
                    training_performances.append(avg_performance)

            # Add some retired algorithms for diversity
            for algorithm in self.retired_algorithms[-20:]:  # Last 20 retired
                if algorithm.algorithm_id in self.performance_history:
                    training_algorithms.append(algorithm)
                    avg_performance = sum(self.performance_history[algorithm.algorithm_id]) / \
                                    len(self.performance_history[algorithm.algorithm_id])
                    training_performances.append(avg_performance)

            # Limit training data size
            if len(training_algorithms) > self.config.vae_training_data_size:
                # Sample diverse algorithms for training
                indices = random.sample(range(len(training_algorithms)),
                                      self.config.vae_training_data_size)
                training_algorithms = [training_algorithms[i] for i in indices]
                training_performances = [training_performances[i] for i in indices]

            if training_algorithms:
                logger.info(f"Training VAE on {len(training_algorithms)} algorithms")
                training_stats = self.vae.train_on_algorithms(training_algorithms, training_performances)
                logger.info(f"VAE training completed: {training_stats}")
            else:
                logger.warning("No algorithms available for VAE training")

        except Exception as e:
            logger.error(f"VAE training failed: {e}")

    async def _select_algorithm_for_gameplay(self) -> Optional[AlgorithmRepresentation]:
        """Select the best algorithm for current gameplay using MAB.

        Returns:
            Selected algorithm or None if no algorithms available
        """
        if not self.active_population:
            return None

        try:
            # Use MAB to select algorithm
            selected = self.mab.select_algorithm(self.active_population)

            if selected:
                logger.debug(f"Selected algorithm for gameplay: {selected.algorithm_id}")
                return selected
            else:
                # Fallback to best performing algorithm
                best_algorithm = None
                best_fitness = float('-inf')

                for algorithm in self.active_population:
                    if algorithm.fitness_score > best_fitness:
                        best_fitness = algorithm.fitness_score
                        best_algorithm = algorithm

                return best_algorithm

        except Exception as e:
            logger.error(f"Algorithm selection failed: {e}")
            return random.choice(self.active_population) if self.active_population else None

    async def _calculate_evolution_metrics(self, duration: float) -> Dict[str, Any]:
        """Calculate metrics for the evolution process.

        Args:
            duration: Evolution duration in seconds

        Returns:
            Evolution metrics dictionary
        """
        # Calculate population statistics
        fitness_scores = [alg.fitness_score for alg in self.active_population]
        best_fitness = max(fitness_scores) if fitness_scores else 0.0
        avg_fitness = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0.0

        # Calculate diversity
        unique_signatures = set()
        for algorithm in self.active_population:
            signature = self.evaluator.get_algorithm_signature(algorithm)
            unique_signatures.add(signature)

        diversity = len(unique_signatures) / len(self.active_population) if self.active_population else 0.0

        # MAB statistics
        mab_stats = self.mab.get_arm_statistics()

        metrics = {
            "generation": self.state.current_generation,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "population_size": len(self.active_population),
            "best_fitness": best_fitness,
            "avg_fitness": avg_fitness,
            "diversity": diversity,
            "total_algorithms_created": self.state.total_algorithms_created,
            "total_games_played": self.state.total_games_played,
            "stagnation_counter": self.state.stagnation_counter,
            "mab_arms": mab_stats["total_arms"],
            "retired_algorithms": len(self.retired_algorithms)
        }

        return metrics

    async def _load_from_database(self):
        """Load evolution state from database."""
        if not self.db:
            return

        try:
            # Load algorithms
            algorithms_data = self.db.get_algorithms(limit=1000)
            for alg_data in algorithms_data:
                algorithm = AlgorithmRepresentation.from_json(alg_data['algorithm_data'])
                algorithm.fitness_score = alg_data['fitness_score']
                algorithm.generation = alg_data['generation']

                self.active_population.append(algorithm)

            # Load MAB data
            self.mab.load_from_database()

            # Load performance history
            for algorithm in self.active_population:
                performance_data = self.db.get_algorithm_performance(algorithm.algorithm_id)
                if performance_data:
                    scores = [p['final_score'] for p in performance_data]
                    self.performance_history[algorithm.algorithm_id] = scores

            logger.info(f"Loaded {len(self.active_population)} algorithms from database")

        except Exception as e:
            logger.error(f"Failed to load from database: {e}")

    async def _save_population_to_database(self):
        """Save current population to database."""
        if not self.db:
            return

        try:
            for algorithm in self.active_population:
                self.db.save_algorithm(
                    algorithm.algorithm_id,
                    "GP",  # Type - could be refined
                    algorithm.to_json(),
                    algorithm.generation,
                    algorithm.parent_ids,
                    algorithm.fitness_score
                )

            logger.debug("Population saved to database")

        except Exception as e:
            logger.error(f"Failed to save population to database: {e}")

    async def _save_performance_to_database(self, algorithm_id: str,
                                          game_result: Dict[str, Any], fitness: float):
        """Save algorithm performance to database."""
        if not self.db:
            return

        try:
            self.db.save_algorithm_performance(
                algorithm_id,
                game_result.get('game_id', 'unknown'),
                game_result.get('session_id', 'unknown'),
                game_result.get('final_score', 0.0),
                game_result.get('actions_taken', 0),
                game_result.get('win_detected', False),
                {"fitness": fitness, "timestamp": datetime.now().isoformat()}
            )

        except Exception as e:
            logger.error(f"Failed to save performance to database: {e}")

    async def _save_evolution_to_database(self):
        """Save evolution history to database."""
        if not self.db:
            return

        try:
            # Get current metrics
            fitness_scores = [alg.fitness_score for alg in self.active_population]
            best_fitness = max(fitness_scores) if fitness_scores else 0.0
            avg_fitness = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0.0

            # Save evolution history
            self.db.save_evolution_history(
                self.state.current_generation,
                len(self.active_population),
                best_fitness,
                avg_fitness,
                None,  # diversity_metric - could be calculated
                None   # operations_performed - could be tracked
            )

        except Exception as e:
            logger.error(f"Failed to save evolution to database: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status.

        Returns:
            System status dictionary
        """
        # Calculate uptime
        uptime = datetime.now() - self.state.system_startup_time if self.state.system_startup_time else timedelta()

        # Get component statuses
        gp_summary = self.gp_engine.get_evolution_summary()
        mab_stats = self.mab.get_arm_statistics()

        # Recent performance
        recent_performance = []
        for algorithm_id, performances in self.performance_history.items():
            if performances:
                recent_performance.extend(performances[-5:])  # Last 5 performances per algorithm

        avg_recent_performance = sum(recent_performance) / len(recent_performance) if recent_performance else 0.0

        status = {
            "system_uptime_seconds": uptime.total_seconds(),
            "current_generation": self.state.current_generation,
            "population_size": len(self.active_population),
            "total_algorithms_created": self.state.total_algorithms_created,
            "total_games_played": self.state.total_games_played,
            "best_fitness_ever": self.state.best_fitness_ever,
            "current_algorithm": self.current_algorithm.algorithm_id if self.current_algorithm else None,
            "stagnation_counter": self.state.stagnation_counter,
            "last_evolution": self.state.last_evolution_time.isoformat() if self.state.last_evolution_time else None,
            "avg_recent_performance": avg_recent_performance,
            "retired_algorithms": len(self.retired_algorithms),
            "gp_engine": gp_summary,
            "mab_engine": mab_stats,
            "vae_training_epoch": self.vae.training_epoch,
            "evolution_metrics_count": len(self.evolution_metrics)
        }

        return status

    def get_algorithm_recommendations(self, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get algorithm recommendations for different scenarios.

        Args:
            context: Optional context for recommendations

        Returns:
            List of algorithm recommendations
        """
        recommendations = []

        # Best overall performer
        if self.active_population:
            best_algorithm = max(self.active_population, key=lambda x: x.fitness_score)
            recommendations.append({
                "type": "best_performer",
                "algorithm_id": best_algorithm.algorithm_id,
                "fitness": best_algorithm.fitness_score,
                "description": "Highest overall fitness score"
            })

        # Most promising recent algorithms
        recent_algorithms = [alg for alg in self.active_population
                           if alg.generation >= self.state.current_generation - 2]
        if recent_algorithms:
            recent_best = max(recent_algorithms, key=lambda x: x.fitness_score)
            recommendations.append({
                "type": "recent_promise",
                "algorithm_id": recent_best.algorithm_id,
                "fitness": recent_best.fitness_score,
                "generation": recent_best.generation,
                "description": "Best performing recent algorithm"
            })

        # MAB recommendation
        mab_best = self.mab.get_best_algorithms(1)
        if mab_best:
            recommendations.append({
                "type": "mab_favorite",
                "algorithm_id": mab_best[0],
                "description": "Multi-armed bandit recommendation"
            })

        return recommendations