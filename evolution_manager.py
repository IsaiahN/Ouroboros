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
            # Find the algorithm object by ID
            algorithm = None
            for alg in self.active_population:
                if alg.algorithm_id == algorithm_id:
                    algorithm = alg
                    break

            if algorithm is None:
                logger.warning(f"Algorithm {algorithm_id} not found in active population")
                return

            # Calculate fitness from game result
            fitness = self.evaluator.calculate_fitness(
                algorithm, [game_result]  # Pass the actual algorithm object
            )

            # Update performance history
            if algorithm_id not in self.performance_history:
                self.performance_history[algorithm_id] = []
            self.performance_history[algorithm_id].append(fitness)

            # Update MAB with reward (normalized fitness)
            reward = min(100.0, max(0.0, fitness)) / 100.0
            self.mab.update_reward(algorithm_id, reward, {"game_result": game_result})

            # Update algorithm fitness in population
            algorithm.fitness_score = fitness

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
            import traceback
            logger.error(traceback.format_exc())

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

    # ========================================================================
    # SEEDED ALGORITHMS AND ROUTINES INTEGRATION
    # ========================================================================

    def initialize_seeded_algorithms(self) -> Dict[str, Any]:
        """Initialize seeded algorithms from the builder.
        
        Returns:
            Dictionary containing initialization results
        """
        try:
            from seeded_algorithm_builders import SeededAlgorithmBuilder
            from routine_manager import RoutineManager
            
            # Initialize routine manager
            self.routine_manager = RoutineManager(self.db)
            
            builder = SeededAlgorithmBuilder()
            seeded_count = 0
            errors = []
            
            # Get all algorithm building methods from SeededAlgorithmBuilder
            algorithm_methods = [method for method in dir(builder) 
                               if method.startswith('create_') and callable(getattr(builder, method))]
            
            logger.info(f"Found {len(algorithm_methods)} seeded algorithm builders")
            
            for method_name in algorithm_methods:
                try:
                    # Get algorithm representation
                    algorithm_method = getattr(builder, method_name)
                    algorithm_repr = algorithm_method()
                    
                    if algorithm_repr:
                        # Save to population
                        algorithm_data = algorithm_repr.to_json()
                        self.db.save_algorithm(
                            algorithm_id=algorithm_repr.algorithm_id,
                            algorithm_type="seeded",
                            algorithm_data=algorithm_data,
                            generation=0
                        )
                        
                        # Save metadata
                        original_name = algorithm_repr.name.replace('_', ' ').title()
                        category = self._extract_category_from_method(method_name)
                        adaptability_score = self._estimate_adaptability(algorithm_repr)
                        complexity_level = self._estimate_complexity(algorithm_repr)
                        
                        self.db.save_seeded_algorithm_meta(
                            algorithm_id=algorithm_repr.algorithm_id,
                            original_name=original_name,
                            category=category,
                            adaptability_score=adaptability_score,
                            complexity_level=complexity_level,
                            adaptation_notes=f"Adapted from {original_name} algorithm"
                        )
                        
                        # Add to active population if space available
                        if len(self.active_population) < self.config.population_size:
                            self.active_population.append(algorithm_repr)
                        
                        seeded_count += 1
                        logger.debug(f"Seeded algorithm: {algorithm_repr.algorithm_id} ({original_name})")
                        
                except Exception as e:
                    error_msg = f"Failed to create {method_name}: {e}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
            
            result = {
                'seeded_count': seeded_count,
                'total_methods': len(algorithm_methods),
                'errors': errors,
                'population_size': len(self.active_population)
            }
            
            logger.info(f"Seeded algorithm initialization complete: {seeded_count}/{len(algorithm_methods)} algorithms")
            return result
            
        except ImportError as e:
            error_msg = f"Failed to import seeded algorithm components: {e}"
            logger.error(error_msg)
            return {'error': error_msg, 'seeded_count': 0}
        except Exception as e:
            error_msg = f"Seeded algorithm initialization failed: {e}"
            logger.error(error_msg)
            return {'error': error_msg, 'seeded_count': 0}

    def _extract_category_from_method(self, method_name: str) -> str:
        """Extract algorithm category from method name."""
        # Map method names to categories
        category_mapping = {
            'astar': 'Search & Optimization',
            'dijkstra': 'Graph & Network Algorithms',
            'bfs': 'Search & Optimization',
            'dfs': 'Search & Optimization',
            'hill_climbing': 'Search & Optimization',
            'simulated_annealing': 'Search & Optimization',
            'gradient_descent': 'Search & Optimization',
            'gradient_ascent': 'Search & Optimization',
            'decision_tree': 'Machine Learning',
            'knn': 'Machine Learning',
            'kmeans': 'Machine Learning',
            'quick_sort': 'Sorting & Ordering',
            'merge_sort': 'Sorting & Ordering',
            'binary_search': 'Search & Optimization',
            'pagerank': 'Graph & Network Algorithms',
            'rsa': 'Cryptography & Hashing',
            'bloom_filter': 'Cryptography & Hashing',
        }
        
        method_lower = method_name.lower()
        for key, category in category_mapping.items():
            if key in method_lower:
                return category
        
        return 'General Purpose'

    def _estimate_adaptability(self, algorithm: 'AlgorithmRepresentation') -> float:
        """Estimate how well an algorithm can adapt to game scenarios."""
        # Simple heuristic based on algorithm structure
        adaptability = 0.5  # Base score
        
        # Count decision points (increases adaptability)
        if hasattr(algorithm, 'root_node'):
            decision_count = self._count_decision_nodes(algorithm.root_node)
            adaptability += min(decision_count * 0.1, 0.3)
        
        # Complexity penalty (very complex algorithms are harder to adapt)
        complexity = len(str(algorithm)) / 1000.0  # Rough measure
        adaptability -= min(complexity * 0.1, 0.2)
        
        return max(0.1, min(1.0, adaptability))

    def _estimate_complexity(self, algorithm: 'AlgorithmRepresentation') -> str:
        """Estimate algorithm complexity level."""
        if hasattr(algorithm, 'root_node'):
            node_count = self._count_total_nodes(algorithm.root_node)
            if node_count < 5:
                return 'simple'
            elif node_count < 15:
                return 'moderate'
            else:
                return 'complex'
        return 'moderate'

    def _count_decision_nodes(self, node) -> int:
        """Count decision/conditional nodes in algorithm tree."""
        count = 0
        if hasattr(node, 'node_type') and 'condition' in node.node_type.lower():
            count = 1
        
        if hasattr(node, 'children'):
            for child in node.children:
                count += self._count_decision_nodes(child)
        
        return count

    def _count_total_nodes(self, node) -> int:
        """Count total nodes in algorithm tree."""
        count = 1
        if hasattr(node, 'children'):
            for child in node.children:
                count += self._count_total_nodes(child)
        return count

    def get_routine_for_game(self, game_id: str) -> Optional['AlgorithmRoutine']:
        """Get the best routine for a specific game.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Best routine for the game type or None
        """
        if not hasattr(self, 'routine_manager'):
            return None
            
        game_type = self.routine_manager.extract_game_type(game_id)
        return self.routine_manager.get_best_routine_for_game_type(game_type)

    def start_game_with_routine(self, game_id: str) -> Dict[str, Any]:
        """Start a game with appropriate routine selection.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Dictionary with routine and algorithm information
        """
        if not hasattr(self, 'routine_manager'):
            return {'error': 'Routine manager not initialized'}
            
        try:
            # Get best routine for game type
            routine = self.get_routine_for_game(game_id)
            
            if not routine:
                # Create default routine from available algorithms
                game_type = self.routine_manager.extract_game_type(game_id)
                available_algorithms = [algo.algorithm_id for algo in self.active_population[:4]]
                
                if available_algorithms:
                    routine = self.routine_manager.create_default_routine(game_type, available_algorithms)
                    self.routine_manager.save_routine(routine)
                    logger.info(f"Created default routine for game type {game_type}")
                else:
                    return {'error': 'No algorithms available for routine creation'}
            
            # Start the routine
            routine_state = self.routine_manager.start_routine(game_id, routine)
            
            # Get initial algorithm
            current_algorithm_id = self.routine_manager.get_current_algorithm(game_id)
            current_algorithm = self._find_algorithm_by_id(current_algorithm_id)
            
            return {
                'routine': routine,
                'current_algorithm': current_algorithm,
                'routine_state': routine_state,
                'game_type': routine.game_type
            }
            
        except Exception as e:
            logger.error(f"Failed to start game with routine: {e}")
            return {'error': str(e)}

    def _find_algorithm_by_id(self, algorithm_id: str) -> Optional['AlgorithmRepresentation']:
        """Find algorithm in active population by ID."""
        for algorithm in self.active_population:
            if algorithm.algorithm_id == algorithm_id:
                return algorithm
        return None

    def update_routine_context(self, game_id: str, current_score: float, 
                             actions_taken: int) -> Optional['AlgorithmRepresentation']:
        """Update routine context and check for algorithm switching.
        
        Args:
            game_id: Game identifier
            current_score: Current game score
            actions_taken: Number of actions taken
            
        Returns:
            New algorithm if switch occurred, None otherwise
        """
        if not hasattr(self, 'routine_manager'):
            return None
            
        try:
            # CRITICAL FIX: Ensure current_score is numeric before passing to routine manager
            if isinstance(current_score, (list, tuple)):
                logger.warning(f"[EVOLUTION] Current score is list/tuple: {current_score}, taking first element")
                current_score = current_score[0] if len(current_score) > 0 else 0.0
            elif not isinstance(current_score, (int, float)):
                logger.warning(f"[EVOLUTION] Current score is not numeric: {type(current_score)} {current_score}, using 0.0")
                current_score = 0.0
            current_score = float(current_score)
            
            # Check if we should switch algorithms
            should_switch, reason = self.routine_manager.should_switch_algorithm(
                game_id, current_score, actions_taken
            )
            
            if should_switch:
                # Switch to next algorithm in routine
                new_algorithm_id = self.routine_manager.switch_to_next_algorithm(game_id)
                logger.info(f"Switched algorithm for game {game_id}: {reason}")
                
                if new_algorithm_id:
                    new_algorithm = self._find_algorithm_by_id(new_algorithm_id)
                    if new_algorithm:
                        self.current_algorithm = new_algorithm
                        return new_algorithm
                    else:
                        logger.warning(f"Algorithm {new_algorithm_id} not found in active population")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to update routine context: {e}")
            return None

    def complete_game_with_routine(self, game_id: str, final_score: float,
                                 actions_taken: int, levels_completed: int,
                                 win_detected: bool) -> None:
        """Complete a game and update routine performance.
        
        Args:
            game_id: Game identifier
            final_score: Final game score
            actions_taken: Total actions taken
            levels_completed: Number of levels completed
            win_detected: Whether the game was won
        """
        if not hasattr(self, 'routine_manager'):
            return
            
        try:
            # Update routine performance
            self.routine_manager.update_routine_performance(
                game_id, final_score, actions_taken, levels_completed, win_detected
            )
            
            # Update seeded algorithm performance if applicable
            current_algorithm_id = self.routine_manager.get_current_algorithm(game_id)
            if current_algorithm_id:
                # Calculate performance score
                performance_score = self._calculate_performance_score(
                    final_score, actions_taken, levels_completed, win_detected
                )
                
                self.db.update_seeded_algorithm_performance(
                    current_algorithm_id, performance_score
                )
                
                # Save game type performance
                game_type = self.routine_manager.extract_game_type(game_id)
                success_rate = 1.0 if win_detected else min(levels_completed / 10.0, 0.8)
                
                self.db.save_game_type_performance(
                    game_type=game_type,
                    algorithm_id=current_algorithm_id,
                    levels_completed=levels_completed,
                    total_actions=actions_taken,
                    success_rate=success_rate
                )
            
            logger.info(f"Completed game {game_id} with routine performance update")
            
        except Exception as e:
            logger.error(f"Failed to complete game with routine: {e}")

    def _calculate_performance_score(self, final_score: float, actions_taken: int,
                                   levels_completed: int, win_detected: bool) -> float:
        """Calculate normalized performance score for seeded algorithms."""
        # Base score from win/completion
        if win_detected:
            base_score = 1.0
        elif levels_completed > 0:
            base_score = min(levels_completed / 10.0, 0.8)  # Max 0.8 for partial completion
        else:
            base_score = 0.1  # Minimum for attempting
        
        # Efficiency bonus (fewer actions = better)
        if levels_completed > 0:
            actions_per_level = actions_taken / levels_completed
            efficiency_bonus = max(0, (50 - actions_per_level) / 50 * 0.2)  # Up to 0.2 bonus
            base_score += efficiency_bonus
        
        # Score bonus (higher scores = better)
        score_bonus = min(final_score / 1000.0, 0.1)  # Up to 0.1 bonus
        base_score += score_bonus
        
        return max(0.0, min(1.0, base_score))

    def create_hybrid_algorithm(self, parent_algorithms: List['AlgorithmRepresentation'],
                              mutation_rate: float = 0.1) -> Optional['AlgorithmRepresentation']:
        """Create a hybrid algorithm from multiple parents with proper inheritance naming.
        
        Args:
            parent_algorithms: List of parent algorithms
            mutation_rate: Rate of mutation for the hybrid
            
        Returns:
            New hybrid algorithm with inheritance naming
        """
        if len(parent_algorithms) < 2:
            return None
            
        try:
            # Use genetic programming to create hybrid
            hybrid = self.gp_engine.crossover(parent_algorithms[0], parent_algorithms[1])
            
            if mutation_rate > 0:
                hybrid = self.gp_engine.mutate(hybrid, mutation_rate)
            
            # Create inheritance naming
            parent_ids = [algo.algorithm_id for algo in parent_algorithms]
            original_names = []
            
            # Get original names from seeded algorithm metadata
            for parent_id in parent_ids:
                try:
                    seeded_algos = self.db.get_seeded_algorithms()
                    for seeded in seeded_algos:
                        if seeded['algorithm_id'] == parent_id:
                            original_names.append(seeded['original_name'].replace(' ', ''))
                            break
                    else:
                        # Fallback to algorithm ID
                        original_names.append(parent_id.split('_')[0])
                except:
                    original_names.append(parent_id.split('_')[0])
            
            # Create hybrid with inheritance naming
            final_algorithm_id = self.db.create_algorithm_with_inheritance(
                algorithm_id=hybrid.algorithm_id,
                algorithm_type="hybrid",
                algorithm_data=hybrid.to_json(),
                parent_ids=parent_ids,
                original_names=original_names
            )
            
            # Update the algorithm ID
            hybrid.algorithm_id = final_algorithm_id
            
            logger.info(f"Created hybrid algorithm: {final_algorithm_id} from parents: {parent_ids[:2]}")
            return hybrid
            
        except Exception as e:
            logger.error(f"Failed to create hybrid algorithm: {e}")
            return None

    def get_seeded_algorithm_recommendations(self, game_type: str = None,
                                           category: str = None,
                                           limit: int = 5) -> List[Dict[str, Any]]:
        """Get recommended seeded algorithms based on performance.
        
        Args:
            game_type: Filter by game type performance
            category: Filter by algorithm category
            limit: Maximum number of recommendations
            
        Returns:
            List of algorithm recommendations
        """
        try:
            recommendations = []
            
            # Get best seeded algorithms by category
            if category:
                seeded_algos = self.db.get_seeded_algorithms(category=category, limit=limit)
            else:
                seeded_algos = self.db.get_best_algorithms_by_category(limit=limit)
            
            for algo_data in seeded_algos:
                recommendation = {
                    'algorithm_id': algo_data['algorithm_id'],
                    'original_name': algo_data['original_name'],
                    'category': algo_data['category'],
                    'adaptability_score': algo_data['adaptability_score'],
                    'avg_performance': algo_data['avg_performance'],
                    'fitness_score': algo_data['fitness_score'],
                    'games_evaluated': algo_data['games_evaluated']
                }
                
                # Add game type specific performance if available
                if game_type:
                    game_performance = self.db.get_game_type_performance(
                        game_type=game_type,
                        algorithm_id=algo_data['algorithm_id'],
                        limit=1
                    )
                    if game_performance:
                        recommendation['game_type_performance'] = game_performance[0]
                
                recommendations.append(recommendation)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get seeded algorithm recommendations: {e}")
            return []

    def get_seeded_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the seeded algorithm system.
        
        Returns:
            Dictionary containing seeded system statistics
        """
        try:
            status = {}
            
            # Get seeded algorithm statistics
            status['seeded_algorithms'] = self.db.get_seeded_algorithm_stats()
            
            # Get routine manager status
            if hasattr(self, 'routine_manager'):
                status['routines'] = self.routine_manager.get_system_status()
            else:
                status['routines'] = {'error': 'Routine manager not initialized'}
            
            # Get algorithm inheritance information
            total_algorithms = len(self.active_population)
            hybrid_count = sum(1 for algo in self.active_population 
                             if hasattr(algo, 'algorithm_type') and algo.algorithm_type == 'hybrid')
            
            status['population'] = {
                'total_algorithms': total_algorithms,
                'hybrid_algorithms': hybrid_count,
                'seeded_algorithms': total_algorithms - hybrid_count
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get seeded system status: {e}")
            return {'error': str(e)}
