import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Evolutionary Engine - Handles agent breeding, mutation, and selection
Based on ARC performance data following Ouroboros principles
All operations use database storage (Rule 2)
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

import json
import uuid
import random
import copy
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from database_interface import DatabaseInterface
from engines.social.prestige_engine import PrestigeEngine
from agent_operating_mode_system import AgentOperatingModeSystem

# Phase 4.5: Import sensation engine for emotional intelligence inheritance
try:
    from engines.consciousness.sensation_engine import SensationEngine
    SENSATION_AVAILABLE = True
except ImportError:
    SENSATION_AVAILABLE = False

def safe_json_parse(json_str, default=None):
    """Safely parse JSON string, returning default if invalid or empty."""
    if not json_str or json_str.strip() == '':
        return default or {}
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default or {}


def calculate_youth_bonus(agent_generation: int, current_generation: int) -> float:
    """
    Calculate youth bonus (opportunity multiplier) for agent selection.
    
    Philosophy (from Unified Theory):
    - The network gets stronger each generation
    - Newer agents inherit better "DNA" from evolved network
    - They deserve more OPPORTUNITIES to prove themselves
    - This is NOT unearned prestige - just more chances to demonstrate value
    
    Args:
        agent_generation: The generation the agent was born in
        current_generation: The current evolution generation
    
    Returns:
        float: Multiplier from 1.0 (no bonus) to 1.5 (50% bonus)
        
    Decay Schedule:
        Age 0 (newborn): 1.5x (50% more likely to be selected)
        Age 1: 1.4x
        Age 2: 1.3x
        Age 3: 1.2x
        Age 4: 1.1x
        Age 5+: 1.0x (no bonus, compete purely on merit)
    """
    MAX_YOUTH_BONUS = 1.5  # 50% boost for newborns
    DECAY_GENERATIONS = 5  # Full decay over 5 generations
    
    age = current_generation - agent_generation
    
    if age <= 0:
        return MAX_YOUTH_BONUS  # Newborns get max bonus
    elif age >= DECAY_GENERATIONS:
        return 1.0  # Mature agents get no bonus
    else:
        # Linear decay: 1.5 -> 1.0 over DECAY_GENERATIONS
        decay_per_gen = (MAX_YOUTH_BONUS - 1.0) / DECAY_GENERATIONS
        return MAX_YOUTH_BONUS - (decay_per_gen * age)


class EvolutionaryEngine:
    """
    Executes evolution operations based on Claude Code decisions
    Uses ARC game performance as primary fitness measure
    """

    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        self.prestige_engine = PrestigeEngine(database_interface)  # Phase 1: Prestige system
        self.crossover_ops = CrossoverOperations(database_interface)  # Pass DB for sensation access
        self.mutation_strategies = MutationStrategies(database_interface)  # Pass DB for sensation access
        self.engine_id = f"evol_{uuid.uuid4().hex[:8]}"
        
        # Phase 4.5: Initialize sensation engine if available
        if SENSATION_AVAILABLE:
            self.sensation_engine = SensationEngine(database_interface)
        else:
            self.sensation_engine = None
        
        # Dynamic Role System: Initialize operating mode coordinator
        self.operating_mode_system = AgentOperatingModeSystem(database_interface)

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
            # CRITICAL: Sync agent performance before calculating fitness
            # This ensures fitness calculations use latest game results
            agents_synced = self.db.sync_agent_performance_to_agents_table()
            if agents_synced > 0:
                self._log_evolution_event("agent_performance_synced", {
                    "agents_updated": agents_synced,
                    "generation": generation
                })
            
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
            
            # Phase 1: Calculate and apply prestige for all agents
            try:
                self._log_evolution_event("prestige_calculation_started", {
                    "generation": generation,
                    "population_size": len(new_population)
                })
                
                prestige_benefits = self.prestige_engine.update_all_agent_prestige(generation)
                
                self._log_evolution_event("prestige_calculation_completed", {
                    "generation": generation,
                    "agents_updated": len(prestige_benefits),
                    "avg_prestige": sum(b['prestige'] for b in prestige_benefits.values()) / len(prestige_benefits) if prestige_benefits else 0
                })
            except Exception as e:
                self._log_evolution_event("prestige_calculation_error", {
                    "generation": generation,
                    "error": str(e)
                })

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
                # SPECIALIST MODE DISABLED - This branch never executes
                # Specialist system replaced by prestige + operating modes
                # Keeping code for reference but specialist_mode is always False
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
                    SUM(CASE WHEN win_achieved THEN 1 ELSE 0 END) as game_wins,
                    SUM(final_score) as total_levels_completed,
                    AVG(final_score) as avg_levels_per_game,
                    SUM(total_actions) as total_actions_sum,
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
            game_wins = perf['game_wins'] or 0
            total_levels_completed = perf['total_levels_completed'] or 0
            avg_levels_per_game = perf['avg_levels_per_game'] or 0.0
            total_actions_sum = perf['total_actions_sum'] or 1.0
            avg_efficiency = perf['avg_efficiency'] or 0.0
            best_score = perf['best_score'] or 0.0
            
            # USE LEVEL PROGRESS FORMULA (same as learning speed fitness)
            # Formula: (total_levels^1.5 / age_factor) * execution_efficiency * consistency
            # Rewards specialists who complete MORE LEVELS on their assigned games
            
            import math
            
            # Age factor: log(games_played + 1) - penalizes agents who need many games to learn
            age_factor = math.log(games_played + 1)
            
            # Levels component: total_levels^1.5 rewards more levels exponentially
            levels_component = (total_levels_completed ** 1.5) / age_factor if age_factor > 0 and total_levels_completed > 0 else 0.0
            
            # Execution efficiency: LEVELS per ACTION (not score per action)
            # BIOME THEORY: Metabolic efficiency in specialist niche
            execution_efficiency = total_levels_completed / total_actions_sum if total_actions_sum > 0 else 0.0
            execution_efficiency = min(1.0, execution_efficiency * 1000)  # Normalize
            
            # Calculate consistency on assigned games
            # Get all scores for consistency calculation
            score_records = self.db.execute_query(f"""
                SELECT final_score FROM agent_arc_performance
                WHERE agent_id = ? AND game_id IN ({placeholders})
            """, (agent_id, *assigned_games))
            
            if len(score_records) > 1:
                scores = [s['final_score'] for s in score_records]
                mean = sum(scores) / len(scores)
                variance = sum((s - mean) ** 2 for s in scores) / len(scores)
                std_dev = math.sqrt(variance)
                
                # Consistency: inverse of coefficient of variation
                if mean > 0:
                    cv = std_dev / mean
                    consistency = 1.0 / (1.0 + cv)
                else:
                    consistency = 0.5
            else:
                consistency = 0.5  # Neutral for single game
            
            # Apply the learning speed formula (Task 6 - modified for LEVEL PROGRESS)
            # This rewards agents who complete MORE LEVELS FAST and efficiently
            specialist_fitness = levels_component * execution_efficiency * consistency
            
            # Bonus for deep mastery (achieving high scores quickly)
            if best_score >= 3.0 and games_played <= 15:
                specialist_fitness *= 1.3  # 30% bonus for fast mastery
            elif best_score >= 2.0 and games_played <= 10:
                specialist_fitness *= 1.15  # 15% bonus for quick learning
            
            # Log detailed metrics
            self._log_evolution_event("specialist_fitness_calculated", {
                "agent_id": agent_id,
                "assigned_games": assigned_games,
                "games_played": games_played,
                "game_wins": game_wins,
                "total_levels_completed": total_levels_completed,
                "avg_levels_per_game": avg_levels_per_game,
                "age_factor": age_factor,
                "levels_component": levels_component,
                "execution_efficiency": execution_efficiency,
                "execution_efficiency_raw": total_levels_completed / total_actions_sum if total_actions_sum > 0 else 0.0,
                "consistency": consistency,
                "specialist_fitness": specialist_fitness
            })
            
            return min(specialist_fitness, 2.0)  # Cap at 2.0 to allow specialists to dominate
            
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
            from manual_tools.analysis.performance_analyzer import PerformanceAnalyzer
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

    def _select_breeding_pairs(self, population: List[Dict[str, Any]],
                             fitness_scores: Dict[str, float],
                             evolution_strategy: Dict[str, Any]) -> List[Tuple[Dict, Dict]]:
        """
        Select breeding pairs based on ARC performance
        Uses tournament selection with fitness-based pairing
        Youth bonus gives newer agents more breeding opportunities
        """
        selection_pressure = evolution_strategy.get('selection_pressure', 0.5)
        crossover_rate = evolution_strategy.get('crossover_rate', 0.6)
        current_generation = evolution_strategy.get('generation', 0)

        # Number of breeding pairs needed
        num_pairs = int(len(population) * crossover_rate / 2)

        breeding_pairs = []

        for _ in range(num_pairs):
            # Tournament selection for first parent (with youth bonus)
            parent1 = self._tournament_selection(
                population, fitness_scores, selection_pressure, current_generation
            )

            # Tournament selection for second parent (ensure different from first)
            parent2 = self._tournament_selection(
                [p for p in population if p['agent_id'] != parent1['agent_id']],
                fitness_scores,
                selection_pressure,
                current_generation
            )

            if parent2:  # Ensure we found a second parent
                breeding_pairs.append((parent1, parent2))

        return breeding_pairs

    def _tournament_selection(self, population: List[Dict[str, Any]],
                            fitness_scores: Dict[str, float],
                            selection_pressure: float,
                            current_generation: int = 0) -> Dict[str, Any]:
        """
        Tournament selection based on ARC fitness with prestige and youth weighting.
        
        Multipliers applied to fitness:
        - Phase 1: breeding_priority (1.0x to 3.0x) - prestige-based
        - Youth Bonus (1.0x to 1.5x) - opportunity for newer agents
        
        Higher selection pressure = more emphasis on fitness
        """
        tournament_size = max(2, int(len(population) * selection_pressure))
        tournament_size = min(tournament_size, len(population))

        # Select random candidates for tournament
        tournament_candidates = random.sample(population, tournament_size)

        # Apply all multipliers to fitness scores
        # - Prestige breeding priority (1.0x to 3.0x): social capital from network contribution
        # - Youth bonus (1.0x to 1.5x): opportunity for newer agents to prove themselves
        def effective_fitness(agent):
            base_fitness = fitness_scores.get(agent['agent_id'], 0.0)
            breeding_priority = agent.get('breeding_priority', 1.0)
            
            # Youth bonus: newer agents get more opportunities
            agent_gen = agent.get('generation', 0)
            youth_bonus = calculate_youth_bonus(agent_gen, current_generation)
            
            return base_fitness * breeding_priority * youth_bonus

        # Select winner based on weighted fitness
        winner = max(tournament_candidates, key=effective_fitness)

        return winner

    def _generate_offspring(self, breeding_pairs: List[Tuple[Dict, Dict]],
                          evolution_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate offspring through crossover of parent genomes
        Includes epigenetic inheritance (Layer 2) calculation
        """
        offspring = []

        for parent1, parent2 in breeding_pairs:
            # Create two offspring from each breeding pair
            offspring1 = self.crossover_ops.crossover_genomes(parent1, parent2)
            offspring2 = self.crossover_ops.crossover_genomes(parent2, parent1)  # Reversed order

            # Calculate epigenetic inheritance for both offspring (Layer 2: Epigenetic)
            # This inherits LEARNING CAPACITY (attention weights, learning rates) NOT SOLUTIONS
            epigenetics1 = self.calculate_epigenetic_inheritance(parent1, parent2)
            epigenetics2 = self.calculate_epigenetic_inheritance(parent2, parent1)

            # Mark as offspring for tracking
            offspring1['parent_ids'] = [parent1['agent_id'], parent2['agent_id']]
            offspring2['parent_ids'] = [parent1['agent_id'], parent2['agent_id']]
            offspring1['generation'] = evolution_strategy.get('generation', 0)
            offspring2['generation'] = evolution_strategy.get('generation', 0)
            
            # Add epigenetic inheritance (Layer 2)
            offspring1['epigenetics'] = json.dumps(epigenetics1)
            offspring2['epigenetics'] = json.dumps(epigenetics2)

            offspring.extend([offspring1, offspring2])

        return offspring

    def _apply_mutations(self, offspring: List[Dict[str, Any]],
                        evolution_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply mutations to offspring to explore strategy space
        
        DYNAMIC ROLE SYSTEM: Each agent has per-deployment operating mode
        - Pioneers: 5x mutation rate
        - Optimizers: 0.5x mutation rate
        - Generalists: 1.0x mutation rate
        """
        base_mutation_rate = evolution_strategy.get('mutation_rate', 0.2)
        strategy_focus = evolution_strategy.get('focus', 'balanced')
        generation = evolution_strategy.get('generation', 0)

        mutated_offspring = []

        for agent in offspring:
            agent_id = agent.get('agent_id')
            
            # Get agent's operating mode for this generation
            if agent_id:
                mode_params = self.operating_mode_system.get_mode_parameters(agent_id, generation)
                operating_mode = mode_params.get('mode', 'generalist')
                mode_multiplier = mode_params.get('mutation_multiplier', 1.0)
            else:
                # Fallback if agent_id missing
                operating_mode = 'generalist'
                mode_multiplier = 1.0
            
            # Apply mode-specific mutation rate
            agent_mutation_rate = base_mutation_rate * mode_multiplier
            
            # Clamp to reasonable range (0.01 to 0.99)
            agent_mutation_rate = max(0.01, min(0.99, agent_mutation_rate))
            
            if random.random() < agent_mutation_rate:
                # Apply mutation based on strategy focus
                mutated_agent = self.mutation_strategies.mutate_genome(
                    agent,
                    strategy_focus
                )
                mutated_agent['mutated'] = True
                mutated_agent['mutation_count'] = mutated_agent.get('mutation_count', 0) + 1
                mutated_agent['operating_mode'] = operating_mode  # Track mode used
                mutated_agent['mode_multiplier'] = mode_multiplier
                mutated_offspring.append(mutated_agent)
            else:
                agent['mutated'] = False
                agent['operating_mode'] = operating_mode
                agent['mode_multiplier'] = mode_multiplier
                mutated_offspring.append(agent)

        return mutated_offspring

    def _select_new_population(self, current_population: List[Dict[str, Any]],
                             offspring: List[Dict[str, Any]],
                             fitness_scores: Dict[str, float],
                             evolution_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Select new population from current population + offspring.
        Phase 1: Applies survival_protection from prestige (0% to 80% protection).
        Maintains population size while favoring high-fitness agents.
        """
        # Use population_size from strategy, or default to reasonable size
        target_population_size = evolution_strategy.get('population_size', 50)
        
        # NEVER let population exceed 500 agents (safety limit)
        # Increased from 200 to support larger network populations
        target_population_size = min(target_population_size, 500)

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

        # Phase 1: Separate agents with survival protection
        protected_agents = []
        unprotected_agents = []
        
        for agent in all_candidates:
            survival_protection = agent.get('survival_protection', 0.0)
            
            # Roll for protection (0% to 80% chance of automatic survival)
            if survival_protection > 0 and random.random() < survival_protection:
                protected_agents.append(agent)
            else:
                unprotected_agents.append(agent)
        
        # Sort unprotected by fitness
        sorted_unprotected = sorted(
            unprotected_agents,
            key=lambda agent: fitness_scores.get(agent['agent_id'], 0.0),
            reverse=True
        )
        
        # Fill population: protected agents first, then best unprotected
        slots_remaining = target_population_size - len(protected_agents)
        
        if slots_remaining > 0:
            new_population = protected_agents + sorted_unprotected[:slots_remaining]
        else:
            # Too many protected agents - sort by fitness and take top
            sorted_protected = sorted(
                protected_agents,
                key=lambda agent: fitness_scores.get(agent['agent_id'], 0.0),
                reverse=True
            )
            new_population = sorted_protected[:target_population_size]

        return new_population

    def _load_population_from_database(self) -> List[Dict[str, Any]]:
        """Load current active population from database"""
        return self.db.get_active_agents()

    def _update_population_database(self, new_population: List[Dict[str, Any]], generation: int):
        """Update population in database - store new agents and deactivate culled ones"""
        import json

        # Get IDs of agents that made it to new population
        selected_ids = {agent['agent_id'] for agent in new_population}
        
        # Deactivate agents that were NOT selected (culled from population)
        # This is CRITICAL to prevent population explosion
        with self.db._get_connection() as conn:
            conn.execute("""
                UPDATE agents 
                SET is_active = 0 
                WHERE is_active = 1 
                AND generation = ?
                AND agent_id NOT IN ({})
            """.format(','.join('?' * len(selected_ids))), 
            [generation] + list(selected_ids))
            conn.commit()

        # Store new agents or update existing
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

    def calculate_epigenetic_inheritance(self, parent1: Dict[str, Any], 
                                        parent2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate epigenetic inheritance from parent performance data.
        Inherits LEARNING CAPACITY (hardware) not SOLUTIONS (software).
        
        Layer 2 (Epigenetic): Inherits attention biases, learning rates, exploration settings
        Layer 3 (Somatic): Winning sequences stay in community database, NOT inherited
        
        Returns epigenetic dict with decay applied (0.95 per generation)
        """
        # Parse parent epigenetics if they exist
        p1_epigenetics = parent1.get('epigenetics')
        if isinstance(p1_epigenetics, str):
            p1_epigenetics = json.loads(p1_epigenetics) if p1_epigenetics else None
        
        p2_epigenetics = parent2.get('epigenetics')
        if isinstance(p2_epigenetics, str):
            p2_epigenetics = json.loads(p2_epigenetics) if p2_epigenetics else None
        
        # Get parent performance data from database
        p1_performance = self._get_agent_performance_summary(parent1['agent_id'])
        p2_performance = self._get_agent_performance_summary(parent2['agent_id'])
        
        # Initialize offspring epigenetics with default structure
        offspring_epigenetics = {
            'feature_attention_weights': {
                'edges': 1.0,
                'symmetry': 1.0,
                'color_patterns': 1.0,
                'spatial_relations': 1.0
            },
            'learning_rate_modifiers': {
                'visual_learning': 1.0,
                'symbolic_learning': 1.0,
                'motor_learning': 1.0
            },
            'exploration_settings': {
                'exploration_ratio': 0.5,
                'novelty_seeking': 0.5,
                'risk_tolerance': 0.5
            },
            'meta_capacities': {
                'problem_decomposition_tendency': 1.0,
                'abstraction_capacity': 1.0,
                'transfer_learning_ability': 1.0
            },
            'inheritance_strength': 1.0,
            'generation_depth': 0,
            'decay_rate': 0.95
        }
        
        # Calculate which parent was more successful (higher fitness parent gets more weight)
        p1_fitness = p1_performance.get('fitness', 0.0)
        p2_fitness = p2_performance.get('fitness', 0.0)
        total_fitness = p1_fitness + p2_fitness
        
        if total_fitness > 0:
            p1_weight = p1_fitness / total_fitness
            p2_weight = p2_fitness / total_fitness
        else:
            p1_weight = 0.5
            p2_weight = 0.5
        
        # Inherit feature attention weights based on parent performance
        if p1_epigenetics and p2_epigenetics:
            for feature in offspring_epigenetics['feature_attention_weights'].keys():
                p1_val = p1_epigenetics.get('feature_attention_weights', {}).get(feature, 1.0)
                p2_val = p2_epigenetics.get('feature_attention_weights', {}).get(feature, 1.0)
                
                # Weighted average based on fitness, with small mutation
                inherited_val = (p1_val * p1_weight + p2_val * p2_weight)
                mutation = random.uniform(-0.1, 0.1)
                offspring_epigenetics['feature_attention_weights'][feature] = max(0.5, min(1.6, inherited_val + mutation))
        
        # Inherit learning rate modifiers
        if p1_epigenetics and p2_epigenetics:
            for modifier in offspring_epigenetics['learning_rate_modifiers'].keys():
                p1_val = p1_epigenetics.get('learning_rate_modifiers', {}).get(modifier, 1.0)
                p2_val = p2_epigenetics.get('learning_rate_modifiers', {}).get(modifier, 1.0)
                
                inherited_val = (p1_val * p1_weight + p2_val * p2_weight)
                mutation = random.uniform(-0.1, 0.1)
                offspring_epigenetics['learning_rate_modifiers'][modifier] = max(0.5, min(1.6, inherited_val + mutation))
        
        # Inherit exploration settings (influenced by parent success patterns)
        if p1_performance.get('games_played', 0) > 5 and p2_performance.get('games_played', 0) > 5:
            # Use performance data to adjust exploration
            p1_win_rate = p1_performance.get('win_rate', 0.0)
            p2_win_rate = p2_performance.get('win_rate', 0.0)
            
            if p1_epigenetics and p2_epigenetics:
                # If parents had high win rates, offspring can be less exploratory
                avg_win_rate = (p1_win_rate + p2_win_rate) / 2
                
                p1_explore = p1_epigenetics.get('exploration_settings', {}).get('exploration_ratio', 0.5)
                p2_explore = p2_epigenetics.get('exploration_settings', {}).get('exploration_ratio', 0.5)
                
                inherited_explore = (p1_explore * p1_weight + p2_explore * p2_weight)
                
                # Adjust based on success - successful parents pass down refined exploration
                if avg_win_rate > 0.3:
                    inherited_explore *= 0.9  # Slightly more exploitative
                else:
                    inherited_explore *= 1.1  # Slightly more exploratory
                
                offspring_epigenetics['exploration_settings']['exploration_ratio'] = max(0.2, min(0.8, inherited_explore))
                
                # Inherit novelty seeking and risk tolerance similarly
                for setting in ['novelty_seeking', 'risk_tolerance']:
                    p1_val = p1_epigenetics.get('exploration_settings', {}).get(setting, 0.5)
                    p2_val = p2_epigenetics.get('exploration_settings', {}).get(setting, 0.5)
                    inherited_val = (p1_val * p1_weight + p2_val * p2_weight)
                    mutation = random.uniform(-0.05, 0.05)
                    offspring_epigenetics['exploration_settings'][setting] = max(0.2, min(0.8, inherited_val + mutation))
        
        # Inherit meta capacities
        if p1_epigenetics and p2_epigenetics:
            for capacity in offspring_epigenetics['meta_capacities'].keys():
                p1_val = p1_epigenetics.get('meta_capacities', {}).get(capacity, 1.0)
                p2_val = p2_epigenetics.get('meta_capacities', {}).get(capacity, 1.0)
                
                inherited_val = (p1_val * p1_weight + p2_val * p2_weight)
                mutation = random.uniform(-0.05, 0.05)
                offspring_epigenetics['meta_capacities'][capacity] = max(0.7, min(1.3, inherited_val + mutation))
        
        # Calculate generation depth and inheritance strength with decay
        max_parent_gen = max(
            p1_epigenetics.get('generation_depth', 0) if p1_epigenetics else 0,
            p2_epigenetics.get('generation_depth', 0) if p2_epigenetics else 0
        )
        
        offspring_epigenetics['generation_depth'] = max_parent_gen + 1
        
        # Apply decay to inheritance strength (0.95 per generation)
        base_strength = (
            (p1_epigenetics.get('inheritance_strength', 1.0) if p1_epigenetics else 1.0) * p1_weight +
            (p2_epigenetics.get('inheritance_strength', 1.0) if p2_epigenetics else 1.0) * p2_weight
        )
        offspring_epigenetics['inheritance_strength'] = base_strength * 0.95
        
        return offspring_epigenetics

    def _get_agent_performance_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get performance summary for an agent from database"""
        try:
            query = """
                SELECT 
                    COUNT(*) as games_played,
                    SUM(CASE WHEN win_achieved = 1 THEN 1 ELSE 0 END) as games_won,
                    AVG(final_score) as avg_score,
                    AVG(total_actions) as avg_actions,
                    AVG(CASE WHEN total_actions > 0 THEN CAST(final_score AS FLOAT) / total_actions ELSE 0 END) as score_efficiency
                FROM agent_arc_performance
                WHERE agent_id = ?
            """
            
            result = self.db.execute_query(query, (agent_id,))
            
            if result and len(result) > 0:
                row = result[0]
                games_played = row.get('games_played', 0)
                games_won = row.get('games_won', 0)
                
                return {
                    'games_played': games_played,
                    'games_won': games_won,
                    'win_rate': games_won / games_played if games_played > 0 else 0.0,
                    'avg_score': row.get('avg_score', 0.0),
                    'avg_actions': row.get('avg_actions', 0.0),
                    'score_efficiency': row.get('score_efficiency', 0.0),
                    'fitness': (games_won / games_played * 0.7 + row.get('score_efficiency', 0.0) * 0.3) if games_played > 0 else 0.0
                }
            else:
                return {
                    'games_played': 0,
                    'games_won': 0,
                    'win_rate': 0.0,
                    'avg_score': 0.0,
                    'avg_actions': 0.0,
                    'score_efficiency': 0.0,
                    'fitness': 0.0
                }
        except Exception as e:
            self._log_evolution_event("performance_summary_error", {
                "agent_id": agent_id,
                "error": str(e)
            })
            return {
                'games_played': 0,
                'games_won': 0,
                'win_rate': 0.0,
                'avg_score': 0.0,
                'avg_actions': 0.0,
                'score_efficiency': 0.0,
                'fitness': 0.0
            }

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
    
    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        
        # Phase 4.5: Initialize sensation engine if available
        if SENSATION_AVAILABLE:
            self.sensation_engine = SensationEngine(database_interface)
        else:
            self.sensation_engine = None

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

        # Phase 4.5: Perform sensation profile crossover (Layer 2 - Epigenetic inheritance)
        offspring_sensation_data = self._crossover_sensation_profiles(parent1, parent2)

        # Create offspring agent
        offspring = {
            'agent_id': offspring_genome['agent_id'],
            'agent_type': self._determine_offspring_type(parent1, parent2),
            'genome': offspring_genome,
            'generation': parent1.get('generation', 0) + 1,
            'specialization': self._determine_offspring_specialization(parent1, parent2),
            'crossover_count': 1
        }
        
        # Phase 4.5: Add sensation profile data to offspring
        if offspring_sensation_data:
            offspring.update(offspring_sensation_data)

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

    def _crossover_sensation_profiles(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crossover sensation profiles between parents (Layer 2 - Epigenetic inheritance).
        
        Phase 4.5: FITNESS-WEIGHTED inheritance with 0.95 decay per Ouroboros Three-Layer Architecture.
        Inherits HOW to learn (learning capacity), not WHAT was learned (specific sensations).
        """
        if not self.sensation_engine:
            return {}
        
        try:
            # Get parent fitness scores for weighted inheritance
            p1_fitness = parent1.get('fitness_score', 0.5)
            p2_fitness = parent2.get('fitness_score', 0.5)
            total_fitness = p1_fitness + p2_fitness
            
            if total_fitness == 0:
                p1_weight = 0.5
                p2_weight = 0.5
            else:
                p1_weight = p1_fitness / total_fitness
                p2_weight = p2_fitness / total_fitness
            
            # Get parent sensation profiles from database
            p1_profile = self._get_agent_sensation_profile(parent1['agent_id'])
            p2_profile = self._get_agent_sensation_profile(parent2['agent_id'])
            
            if not p1_profile and not p2_profile:
                # No sensation data from parents - initialize fresh
                return self._initialize_offspring_sensation_profile(parent1, parent2)
            
            # Ensure we have valid profiles (use defaults if None)
            p1_profile = p1_profile or {}
            p2_profile = p2_profile or {}
            
            # Fitness-weighted crossover of epigenetic traits (learning capacity)
            offspring_profile = {
                'sensation_learning_rate': (
                    p1_profile.get('sensation_learning_rate', 0.3) * p1_weight +
                    p2_profile.get('sensation_learning_rate', 0.3) * p2_weight
                ) * 0.95,  # Epigenetic decay
                
                'state_update_sensitivity': (
                    p1_profile.get('state_update_sensitivity', 0.7) * p1_weight +
                    p2_profile.get('state_update_sensitivity', 0.7) * p2_weight
                ) * 0.95,  # Epigenetic decay
                
                'navigation_state': 0.0,  # Reset emotional state for offspring
                'emotional_intelligence_score': 0.0,  # Will be learned, not inherited
                
                # Action biases - inherit learning patterns, not specific biases
                'action_biases': json.dumps({}),  # Start fresh - Layer 3 (somatic) not inherited
                
                # Sensation profile - inherit learning capacity, not specific mappings
                'sensation_profile': json.dumps(
                    self._inherit_sensation_learning_capacity(p1_profile, p2_profile, p1_weight, p2_weight)
                )
            }
            
            return offspring_profile
            
        except Exception as e:
            # Fallback to fresh initialization if crossover fails
            return self._initialize_offspring_sensation_profile(parent1, parent2)

    def _get_agent_sensation_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent's sensation profile from database."""
        try:
            result = self.db.execute_query("""
                SELECT sensation_profile, sensation_learning_rate, state_update_sensitivity,
                       navigation_state, action_biases, emotional_intelligence_score
                FROM agents WHERE agent_id = ?
            """, (agent_id,))
            
            if result:
                profile = result[0]
                # Parse JSON fields
                if profile['sensation_profile']:
                    profile['sensation_profile_data'] = safe_json_parse(profile['sensation_profile'])
                if profile['action_biases']:
                    profile['action_biases_data'] = safe_json_parse(profile['action_biases'])
                
                return profile
            return None
            
        except Exception:
            return None

    def _inherit_sensation_learning_capacity(self, p1_profile: Dict[str, Any], p2_profile: Dict[str, Any],
                                           p1_weight: float, p2_weight: float) -> Dict[str, Any]:
        """
        Inherit sensation learning capacity (Layer 2) without inheriting specific sensations (Layer 3).
        
        This creates agents that are 'prepared to learn' without giving them solutions.
        """
        # Get parent sensation profiles
        p1_sensation_data = p1_profile.get('sensation_profile_data', {})
        p2_sensation_data = p2_profile.get('sensation_profile_data', {})
        
        # Initialize offspring with capacity to learn, not learned sensations
        offspring_sensation_profile = {
            'object_sensations': {},  # Start fresh - specific sensations not inherited
            'navigation_preferences': {},  # Start fresh - specific preferences not inherited
            'learning_history': {
                'total_sensation_events': 0,
                'successful_learnings': 0,
                'emotional_intelligence_score': 0.0
            }
        }
        
        # Inherit meta-learning patterns (HOW to learn, not WHAT was learned)
        p1_learning = p1_sensation_data.get('learning_history', {})
        p2_learning = p2_sensation_data.get('learning_history', {})
        
        # Inherit learning efficiency tendencies (fitness-weighted)
        if p1_learning and p2_learning:
            p1_ei = p1_learning.get('emotional_intelligence_score', 0.0)
            p2_ei = p2_learning.get('emotional_intelligence_score', 0.0)
            
            # Inherit potential for emotional intelligence (capacity), not achievement
            offspring_ei_potential = (p1_ei * p1_weight + p2_ei * p2_weight) * 0.95 * 0.3  # Decay + reduced to potential
            
            offspring_sensation_profile['learning_history']['ei_potential'] = offspring_ei_potential
        
        return offspring_sensation_profile

    def _initialize_offspring_sensation_profile(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize sensation profile for offspring when parents have no sensation data."""
        
        # Determine offspring agent type for type-specific initialization
        offspring_type = self._determine_offspring_type(parent1, parent2)
        
        # Use sensation engine to initialize fresh profile
        if self.sensation_engine:
            temp_agent_id = f"temp_{uuid.uuid4().hex[:8]}"
            sensation_profile = self.sensation_engine.initialize_agent_sensations(temp_agent_id, offspring_type)
            
            return {
                'sensation_learning_rate': 0.3,
                'state_update_sensitivity': 0.7,
                'navigation_state': 0.0,
                'emotional_intelligence_score': 0.0,
                'action_biases': json.dumps({}),
                'sensation_profile': json.dumps(sensation_profile)
            }
        
        return {}


class MutationStrategies:
    """Handles mutation operations for genome exploration"""
    
    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        
        # Phase 4.5: Initialize sensation engine if available
        if SENSATION_AVAILABLE:
            self.sensation_engine = SensationEngine(database_interface)
        else:
            self.sensation_engine = None

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