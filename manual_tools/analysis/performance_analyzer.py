import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Performance Analyzer - Analyzes ARC performance data for Claude Code decision-making
Provides comprehensive analysis of agent and population performance
Following Rule 2: Database-only storage and analysis
"""

import json
import uuid
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from database_interface import DatabaseInterface


class PerformanceAnalyzer:
    """
    Analyzes ARC performance data for evolutionary decisions
    Provides Claude Code with insights for strategic evolution planning
    """

    def __init__(self, database_interface: DatabaseInterface):
        self.db = database_interface
        self.analyzer_id = f"analyzer_{uuid.uuid4().hex[:8]}"

    def analyze_population_performance(self) -> Dict[str, Any]:
        """
        Analyze current population's ARC performance for Claude Code
        Returns comprehensive analysis for evolution strategy decisions
        """
        self._log_analysis_event("population_analysis_started", {})

        try:
            # Get all active agents and their ARC performance
            population_data = self.db.get_population_performance_data()

            if not population_data:
                return self._create_empty_analysis()

            analysis = {
                'population_stats': self._calculate_population_statistics(population_data),
                'top_performers': self._identify_top_performers(population_data),
                'performance_trends': self._analyze_performance_trends(population_data),
                'strategy_effectiveness': self._analyze_strategy_effectiveness(population_data),
                'diversity_metrics': self._calculate_diversity_metrics(population_data),
                'bottlenecks_and_opportunities': self._identify_bottlenecks_and_opportunities(population_data),
                'evolution_recommendations': self._generate_evolution_recommendations(population_data)
            }

            # Store analysis in database for Claude Code reference (Rule 2)
            self.db.store_performance_analysis(analysis)

            self._log_analysis_event("population_analysis_completed", {
                "population_size": len(population_data),
                "avg_win_rate": analysis['population_stats']['average_win_rate']
            })

            return analysis

        except Exception as e:
            self._log_analysis_event("population_analysis_error", {
                "error": str(e)
            })
            raise

    def _calculate_population_statistics(self, population_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate key ARC performance statistics for the population"""
        if not population_data:
            return {}

        # Extract performance metrics
        win_rates = [agent.get('win_rate', 0.0) for agent in population_data]
        avg_scores = [agent.get('avg_score_per_game', 0.0) for agent in population_data]
        score_efficiencies = [agent.get('score_efficiency', 0.0) for agent in population_data]
        games_played = [agent.get('total_games_played', 0) for agent in population_data]
        level_progressions = [agent.get('level_progressions_detected', 0) for agent in population_data]
        
        # Calculate comprehensive success rates for all agents
        comprehensive_success_rates = []
        for agent in population_data:
            agent_id = agent.get('agent_id')
            if agent_id:
                success_metrics = self.calculate_comprehensive_success_rate(agent_id)
                comprehensive_success_rates.append(success_metrics['comprehensive_success_rate'])
            else:
                comprehensive_success_rates.append(0.0)

        # Calculate statistics
        stats = {
            'population_size': len(population_data),
            'active_agents': sum(1 for agent in population_data if agent.get('is_active', True)),

            # Win rate statistics (game wins only)
            'average_win_rate': sum(win_rates) / len(win_rates) if win_rates else 0.0,
            'best_win_rate': max(win_rates) if win_rates else 0.0,
            'worst_win_rate': min(win_rates) if win_rates else 0.0,
            'win_rate_std_dev': self._calculate_std_dev(win_rates) if win_rates else 0.0,
            
            # Comprehensive success statistics (wins + levels + scores)
            'average_comprehensive_success': sum(comprehensive_success_rates) / len(comprehensive_success_rates) if comprehensive_success_rates else 0.0,
            'best_comprehensive_success': max(comprehensive_success_rates) if comprehensive_success_rates else 0.0,
            'comprehensive_success_std_dev': self._calculate_std_dev(comprehensive_success_rates) if comprehensive_success_rates else 0.0,

            # Score statistics
            'average_score': sum(avg_scores) / len(avg_scores),
            'best_avg_score': max(avg_scores),
            'score_variance': self._calculate_variance(avg_scores),

            # Efficiency statistics
            'average_score_efficiency': sum(score_efficiencies) / len(score_efficiencies),
            'best_score_efficiency': max(score_efficiencies),
            'efficiency_variance': self._calculate_variance(score_efficiencies),

            # Experience statistics
            'total_games_played': sum(games_played),
            'avg_games_per_agent': sum(games_played) / len(games_played),
            'total_level_progressions': sum(level_progressions),

            # Performance distribution
            'agents_with_wins': sum(1 for rate in win_rates if rate > 0),
            'high_performers': sum(1 for rate in win_rates if rate > 0.2),  # >20% win rate
            'consistent_performers': sum(1 for games in games_played if games >= 10)
        }

        return stats

    def _identify_top_performers(self, population_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify top performing agents based on ARC metrics"""
        # Sort by multiple criteria for comprehensive ranking
        def performance_score(agent):
            win_rate = agent.get('win_rate', 0.0)
            score_efficiency = agent.get('score_efficiency', 0.0)
            games_played = agent.get('total_games_played', 0)

            # Composite performance score with reliability weighting
            base_score = win_rate * 0.6 + score_efficiency * 0.4
            reliability_weight = min(games_played / 10.0, 1.0)  # Full weight at 10+ games

            return base_score * reliability_weight

        # Sort and take top performers
        sorted_agents = sorted(population_data, key=performance_score, reverse=True)
        top_performers = sorted_agents[:min(5, len(sorted_agents))]

        # Add performance insights for each top performer
        for agent in top_performers:
            agent['performance_score'] = performance_score(agent)
            agent['performance_insights'] = self._analyze_agent_strengths(agent)

        return top_performers

    def _analyze_performance_trends(self, population_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        # Get historical performance data
        current_time = datetime.now()
        week_ago = current_time - timedelta(days=7)

        # Recent vs historical performance
        recent_performance = self.db.get_performance_data_since(week_ago)
        historical_performance = self.db.get_performance_data_before(week_ago)

        trends = {
            'improvement_rate': self._calculate_improvement_rate(recent_performance, historical_performance),
            'win_rate_trend': self._calculate_win_rate_trend(),
            'score_efficiency_trend': self._calculate_score_efficiency_trend(),
            'population_health_trend': self._calculate_population_health_trend(),
            'stagnation_indicators': self._detect_stagnation_indicators(population_data)
        }

        return trends

    def _calculate_improvement_rate(self, recent_performance, historical_performance):
        """Calculate improvement rate between recent and historical performance"""
        if not recent_performance or not historical_performance:
            return 0.0

        # Simple improvement calculation
        recent_avg = sum(p.get('score', 0) for p in recent_performance) / len(recent_performance)
        historical_avg = sum(p.get('score', 0) for p in historical_performance) / len(historical_performance)

        if historical_avg == 0:
            return 0.0

        return (recent_avg - historical_avg) / historical_avg

    def calculate_comprehensive_success_rate(self, agent_id: str) -> Dict[str, float]:
        """
        Calculate comprehensive success rate including:
        - Game wins (full victories)
        - Level completions (partial success)
        - Score achievements (progress toward win)
        
        Returns weighted success metrics for evolution decisions
        """
        try:
            # Get all performance data for agent
            perf_data = self.db.execute_query(
                """
                SELECT 
                    win_achieved,
                    level_progressions,
                    final_score,
                    win_score_threshold,
                    win_proximity,
                    score_efficiency
                FROM agent_arc_performance
                WHERE agent_id = ?
                ORDER BY game_timestamp DESC
                """,
                (agent_id,)
            )
            
            if not perf_data:
                return {
                    'game_win_rate': 0.0,
                    'level_success_rate': 0.0,
                    'score_achievement_rate': 0.0,
                    'comprehensive_success_rate': 0.0,
                    'total_games': 0
                }
            
            total_games = len(perf_data)
            
            # 1. Game Win Rate (full victories)
            game_wins = sum(1 for p in perf_data if p['win_achieved'])
            game_win_rate = game_wins / total_games
            
            # 2. Score Progress Rate (ANY score increase, most important!)
            # Count games where ANY score was achieved (even 0.01)
            score_progress_games = sum(1 for p in perf_data if p['final_score'] > 0)
            score_progress_rate = score_progress_games / total_games
            
            # 3. Level Success Rate (any level progression)
            level_successes = sum(1 for p in perf_data if p['level_progressions'] > 0)
            level_success_rate = level_successes / total_games
            
            # 4. High Score Achievement Rate (games reaching 50%+ of win score)
            high_score_achievements = sum(1 for p in perf_data if p['win_proximity'] >= 0.5)
            high_score_rate = high_score_achievements / total_games
            
            # 5. Path Efficiency (for wins, average efficiency)
            winning_games = [p for p in perf_data if p['win_achieved']]
            avg_path_efficiency = 0.0
            if winning_games:
                # Calculate average score_efficiency for winning games
                avg_path_efficiency = sum(p['score_efficiency'] for p in winning_games) / len(winning_games)
            
            # 6. Comprehensive Success Rate (SCORE-FOCUSED weighting)
            # NEW WEIGHTS: Score progress (40%), Wins (30%), Levels (15%), High scores (10%), Efficiency (5%)
            # Prioritizes ANY score increase as primary fitness signal
            comprehensive_success_rate = (
                score_progress_rate * 0.40 +      # ANY score increase (MOST IMPORTANT)
                game_win_rate * 0.30 +            # Full wins (important)
                level_success_rate * 0.15 +       # Level completions (good)
                high_score_rate * 0.10 +          # High scores (bonus)
                min(avg_path_efficiency * 100, 1.0) * 0.05  # Efficiency (minor)
            )
            
            return {
                'game_win_rate': game_win_rate,
                'score_progress_rate': score_progress_rate,  # NEW: ANY score > 0
                'level_success_rate': level_success_rate,
                'high_score_rate': high_score_rate,  # Renamed from score_achievement_rate
                'path_efficiency': avg_path_efficiency,
                'comprehensive_success_rate': comprehensive_success_rate,
                'total_games': total_games,
                'game_wins': game_wins,
                'score_progress_games': score_progress_games,  # NEW
                'level_completions': level_successes,
                'high_score_achievements': high_score_achievements  # Renamed
            }
            
        except Exception as e:
            self._log_analysis_event("success_rate_calculation_error", {
                "agent_id": agent_id,
                "error": str(e)
            })
            return {
                'game_win_rate': 0.0,
                'score_progress_rate': 0.0,  # NEW
                'level_success_rate': 0.0,
                'high_score_rate': 0.0,  # Renamed
                'path_efficiency': 0.0,
                'comprehensive_success_rate': 0.0,
                'total_games': 0
            }

    def calculate_diversity_fitness(self, agent_id: str) -> Dict[str, float]:
        """
        Calculate diversity-focused fitness prioritizing generalization over specialization.
        
        Diversity Fitness Weights:
        - 50% Novel Game Performance (first-time games)
        - 30% Few-Shot Learning (improvement on 2nd attempt)
        - 20% Game Diversity (unique games scored on)
        
        Args:
            agent_id: Agent ID to calculate fitness for
            
        Returns:
            Dict with diversity fitness metrics
        """
        try:
            # Get game diversity data
            diversity_data = self.db.execute_query("""
                SELECT 
                    game_id,
                    attempts,
                    first_attempt_score,
                    best_score,
                    last_attempt_score,
                    is_novel_game,
                    few_shot_improvement
                FROM agent_game_diversity
                WHERE agent_id = ?
            """, (agent_id,))
            
            if not diversity_data:
                return {
                    'diversity_fitness_score': 0.0,
                    'novel_game_performance': 0.0,
                    'few_shot_learning_rate': 0.0,
                    'game_diversity_score': 0.0,
                    'unique_games_played': 0,
                    'unique_games_scored': 0,
                    'overfitting_penalty': 0.0
                }
            
            total_games = len(diversity_data)
            
            # 1. Novel Game Performance (50% weight)
            # Average score on first-time games
            novel_games = [g for g in diversity_data if g['is_novel_game'] or g['attempts'] == 1]
            novel_game_performance = 0.0
            if novel_games:
                # Normalize scores (assume max score ~10.0 for ARC games)
                novel_scores = [min(g['first_attempt_score'] / 10.0, 1.0) for g in novel_games]
                novel_game_performance = sum(novel_scores) / len(novel_scores)
            
            # 2. Few-Shot Learning (30% weight)
            # How much agents improve from attempt 1 to 2
            few_shot_games = [g for g in diversity_data if g['attempts'] >= 2]
            few_shot_learning_rate = 0.0
            if few_shot_games:
                improvements = [g['few_shot_improvement'] for g in few_shot_games]
                # Count positive improvements
                positive_improvements = sum(1 for imp in improvements if imp > 0)
                few_shot_learning_rate = positive_improvements / len(few_shot_games)
            
            # 3. Game Diversity (20% weight)
            # Ratio of unique games scored on vs played
            unique_games_played = total_games
            unique_games_scored = sum(1 for g in diversity_data if g['best_score'] > 0)
            game_diversity_score = unique_games_scored / unique_games_played if unique_games_played > 0 else 0.0
            
            # 4. Anti-Overfitting Penalty
            # Penalize agents that play same games repeatedly
            max_attempts_on_single_game = max(g['attempts'] for g in diversity_data) if diversity_data else 0
            overfitting_penalty = 0.0
            if max_attempts_on_single_game > 10:  # Threshold for overfitting
                overfitting_penalty = min((max_attempts_on_single_game - 10) * 0.05, 0.5)  # Max 50% penalty
            
            # Calculate Diversity Fitness Score
            # 50% novel + 30% few-shot + 20% diversity - overfitting penalty
            diversity_fitness_score = (
                novel_game_performance * 0.50 +
                few_shot_learning_rate * 0.30 +
                game_diversity_score * 0.20 -
                overfitting_penalty
            )
            diversity_fitness_score = max(0.0, diversity_fitness_score)  # Ensure non-negative
            
            return {
                'diversity_fitness_score': diversity_fitness_score,
                'novel_game_performance': novel_game_performance,
                'few_shot_learning_rate': few_shot_learning_rate,
                'game_diversity_score': game_diversity_score,
                'unique_games_played': unique_games_played,
                'unique_games_scored': unique_games_scored,
                'overfitting_penalty': overfitting_penalty,
                'max_repeats_on_game': max_attempts_on_single_game
            }
            
        except Exception as e:
            self._log_analysis_event("diversity_fitness_calculation_error", {
                "agent_id": agent_id,
                "error": str(e)
            })
            return {
                'diversity_fitness_score': 0.0,
                'novel_game_performance': 0.0,
                'few_shot_learning_rate': 0.0,
                'game_diversity_score': 0.0,
                'unique_games_played': 0,
                'unique_games_scored': 0,
                'overfitting_penalty': 0.0
            }

    def _calculate_win_rate_trend(self):
        """Calculate win rate trend"""
        return 0.0  # Placeholder

    def _calculate_score_efficiency_trend(self):
        """Calculate score efficiency trend"""
        return 0.0  # Placeholder

    def _calculate_population_health_trend(self):
        """Calculate population health trend"""
        return 0.0  # Placeholder

    def _detect_stagnation_indicators(self, population_data):
        """Detect stagnation in population"""
        return []  # Placeholder

    def _analyze_strategy_effectiveness(self, population_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze effectiveness of different agent strategies"""
        strategy_performance = {}

        for agent in population_data:
            agent_type = agent.get('agent_type', 'unknown')
            specialization = agent.get('specialization', 'generalist')

            # Group by agent type
            if agent_type not in strategy_performance:
                strategy_performance[agent_type] = {
                    'agents': [],
                    'avg_win_rate': 0.0,
                    'avg_score_efficiency': 0.0,
                    'total_agents': 0
                }

            strategy_performance[agent_type]['agents'].append(agent)
            strategy_performance[agent_type]['total_agents'] += 1

        # Calculate averages for each strategy
        for strategy, data in strategy_performance.items():
            agents = data['agents']
            if agents:
                data['avg_win_rate'] = sum(a.get('win_rate', 0.0) for a in agents) / len(agents)
                data['avg_score_efficiency'] = sum(a.get('score_efficiency', 0.0) for a in agents) / len(agents)
                data['success_rate'] = sum(1 for a in agents if a.get('win_rate', 0) > 0.1) / len(agents)

        # Rank strategies by effectiveness
        ranked_strategies = sorted(
            strategy_performance.items(),
            key=lambda x: x[1]['avg_win_rate'],
            reverse=True
        )

        return {
            'strategy_performance': strategy_performance,
            'most_effective_strategy': ranked_strategies[0][0] if ranked_strategies else None,
            'least_effective_strategy': ranked_strategies[-1][0] if ranked_strategies else None,
            'strategy_recommendations': self._generate_strategy_recommendations(strategy_performance)
        }

    def _generate_strategy_recommendations(self, strategy_performance):
        """Generate strategy recommendations based on performance"""
        recommendations = []

        if not strategy_performance:
            return recommendations

        # Find best performing strategy
        best_strategy = max(strategy_performance.items(),
                          key=lambda x: x[1].get('avg_win_rate', 0))

        if best_strategy[1]['avg_win_rate'] > 0.1:
            recommendations.append(f"Focus on {best_strategy[0]} strategy (win rate: {best_strategy[1]['avg_win_rate']:.3f})")

        return recommendations

    def _calculate_diversity_metrics(self, population_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate population diversity metrics"""
        if not population_data:
            return {'genetic_diversity': 0.0}

        # Strategy type diversity
        agent_types = [agent.get('agent_type', 'unknown') for agent in population_data]
        type_distribution = {}
        for agent_type in agent_types:
            type_distribution[agent_type] = type_distribution.get(agent_type, 0) + 1

        # Calculate Shannon diversity index for strategy types
        total_agents = len(population_data)
        shannon_diversity = 0.0
        for count in type_distribution.values():
            if count > 0:
                proportion = count / total_agents
                shannon_diversity -= proportion * np.log2(proportion)

        # Performance diversity (variance in performance metrics)
        win_rates = [agent.get('win_rate', 0.0) for agent in population_data]
        score_efficiencies = [agent.get('score_efficiency', 0.0) for agent in population_data]

        performance_diversity = (
            self._calculate_variance(win_rates) +
            self._calculate_variance(score_efficiencies)
        ) / 2.0

        # Genetic diversity (based on genome parameters)
        genetic_diversity = self._calculate_genetic_diversity(population_data)

        return {
            'genetic_diversity': genetic_diversity,
            'strategy_diversity': shannon_diversity,
            'performance_diversity': performance_diversity,
            'type_distribution': type_distribution,
            'diversity_health': self._assess_diversity_health(shannon_diversity, genetic_diversity)
        }

    def _assess_diversity_health(self, shannon_diversity, genetic_diversity):
        """Assess overall diversity health of population"""
        # Simple health assessment
        if shannon_diversity > 1.5 and genetic_diversity > 0.5:
            return 'healthy'
        elif shannon_diversity > 1.0 and genetic_diversity > 0.3:
            return 'moderate'
        else:
            return 'low'

    def _calculate_genetic_diversity(self, population_data: List[Dict[str, Any]]) -> float:
        """Calculate genetic diversity based on genome parameters"""
        if not population_data:
            return 0.0

        # Collect genome parameters
        genome_params = []
        for agent in population_data:
            genome = agent.get('genome', {})
            if isinstance(genome, str):
                try:
                    genome = json.loads(genome)
                except:
                    continue

            # Extract numerical parameters for diversity calculation
            params = []
            for key in ['exploration_weight', 'conservative_bias', 'action_diversity',
                       'score_optimization_priority', 'win_focus_threshold']:
                if key in genome:
                    params.append(genome[key])

            if params:
                genome_params.append(params)

        if len(genome_params) < 2:
            return 0.0

        # Calculate average pairwise distance
        total_distance = 0.0
        comparisons = 0

        for i in range(len(genome_params)):
            for j in range(i + 1, len(genome_params)):
                distance = self._calculate_genome_distance(genome_params[i], genome_params[j])
                total_distance += distance
                comparisons += 1

        return total_distance / max(comparisons, 1)

    def _calculate_genome_distance(self, genome1: List[float], genome2: List[float]) -> float:
        """Calculate distance between two genomes"""
        if len(genome1) != len(genome2):
            return 0.0

        distance = sum((g1 - g2) ** 2 for g1, g2 in zip(genome1, genome2))
        return np.sqrt(distance) / len(genome1)

    def _identify_bottlenecks_and_opportunities(self, population_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify performance bottlenecks and improvement opportunities"""
        bottlenecks = []
        opportunities = []

        # Analyze population statistics for bottlenecks
        stats = self._calculate_population_statistics(population_data)

        # Low win rate bottleneck
        if stats['average_win_rate'] < 0.1:
            bottlenecks.append({
                'type': 'low_win_rate',
                'description': 'Population has very low win rate',
                'severity': 'high',
                'recommendation': 'Focus on exploration and strategy diversification'
            })

        # Low diversity bottleneck
        diversity = self._calculate_diversity_metrics(population_data)
        if diversity['genetic_diversity'] < 0.3:
            bottlenecks.append({
                'type': 'low_diversity',
                'description': 'Population lacks genetic diversity',
                'severity': 'medium',
                'recommendation': 'Increase mutation rate and introduce new agent types'
            })

        # Stagnation bottleneck
        if stats['win_rate_std_dev'] < 0.05:
            bottlenecks.append({
                'type': 'stagnation',
                'description': 'Population performance is stagnating',
                'severity': 'medium',
                'recommendation': 'Introduce disruptive mutations and new strategies'
            })

        # Identify opportunities
        if stats['best_win_rate'] > 0.3:
            opportunities.append({
                'type': 'high_performer_potential',
                'description': 'Some agents show high win potential',
                'value': 'high',
                'recommendation': 'Focus on exploiting successful strategies through crossover'
            })

        if stats['average_score_efficiency'] > 0.5:
            opportunities.append({
                'type': 'efficiency_strength',
                'description': 'Population shows good score efficiency',
                'value': 'medium',
                'recommendation': 'Leverage efficiency traits while improving win rate'
            })

        return {
            'bottlenecks': bottlenecks,
            'opportunities': opportunities,
            'overall_assessment': self._generate_overall_assessment(bottlenecks, opportunities)
        }

    def _generate_overall_assessment(self, bottlenecks, opportunities):
        """Generate overall assessment based on bottlenecks and opportunities"""
        if len(bottlenecks) == 0 and len(opportunities) > 0:
            return 'healthy_with_opportunities'
        elif len(bottlenecks) > 0 and len(opportunities) > 0:
            return 'mixed_with_potential'
        elif len(bottlenecks) > 0:
            return 'needs_improvement'
        else:
            return 'stable'

    def _generate_evolution_recommendations(self, population_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate specific recommendations for evolution strategy"""
        recommendations = []

        stats = self._calculate_population_statistics(population_data)
        diversity = self._calculate_diversity_metrics(population_data)

        # Recommendation logic based on current state
        if stats['average_win_rate'] < 0.05:
            recommendations.append({
                'priority': 'high',
                'strategy_focus': 'exploration',
                'mutation_rate': 0.4,
                'crossover_rate': 0.3,
                'rationale': 'Very low win rate requires aggressive exploration'
            })
        elif stats['average_win_rate'] > 0.2:
            recommendations.append({
                'priority': 'high',
                'strategy_focus': 'exploitation',
                'mutation_rate': 0.1,
                'crossover_rate': 0.8,
                'rationale': 'Good win rate should be exploited and refined'
            })
        else:
            recommendations.append({
                'priority': 'medium',
                'strategy_focus': 'balanced',
                'mutation_rate': 0.2,
                'crossover_rate': 0.6,
                'rationale': 'Moderate performance requires balanced approach'
            })

        # Diversity-based recommendations
        if diversity['genetic_diversity'] < 0.2:
            recommendations.append({
                'priority': 'high',
                'strategy_focus': 'diversification',
                'mutation_rate': 0.5,
                'crossover_rate': 0.4,
                'rationale': 'Low diversity requires immediate diversification'
            })

        return recommendations

    def analyze_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Detailed analysis of specific agent performance"""
        agent_data = self.db.get_agent_detailed_performance(agent_id)

        if not agent_data:
            return {'error': 'Agent not found'}

        analysis = {
            'agent_overview': agent_data,
            'performance_history': self.db.get_agent_performance_history(agent_id),
            'strengths': self._analyze_agent_strengths(agent_data),
            'weaknesses': self._analyze_agent_weaknesses(agent_data),
            'evolution_potential': self._assess_evolution_potential(agent_data),
            'breeding_value': self._assess_breeding_value(agent_data)
        }

        return analysis

    def _analyze_agent_strengths(self, agent_data: Dict[str, Any]) -> List[str]:
        """Analyze specific agent strengths"""
        strengths = []

        if agent_data.get('win_rate', 0) > 0.2:
            strengths.append('High win rate')

        if agent_data.get('score_efficiency', 0) > 0.5:
            strengths.append('Excellent score efficiency')

        if agent_data.get('total_games_played', 0) >= 20:
            strengths.append('Extensive experience')

        if agent_data.get('level_progressions_detected', 0) > 5:
            strengths.append('Good level progression detection')

        return strengths

    def _analyze_agent_weaknesses(self, agent_data: Dict[str, Any]) -> List[str]:
        """Analyze specific agent weaknesses"""
        weaknesses = []

        if agent_data.get('win_rate', 0) < 0.05:
            weaknesses.append('Very low win rate')

        if agent_data.get('score_efficiency', 0) < 0.2:
            weaknesses.append('Poor score efficiency')

        if agent_data.get('total_games_played', 0) < 5:
            weaknesses.append('Limited experience')

        return weaknesses

    # Utility methods
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        return np.sqrt(self._calculate_variance(values))

    def _create_empty_analysis(self) -> Dict[str, Any]:
        """Create empty analysis structure"""
        return {
            'population_stats': {'population_size': 0},
            'top_performers': [],
            'performance_trends': {},
            'strategy_effectiveness': {},
            'diversity_metrics': {'genetic_diversity': 0.0},
            'bottlenecks_and_opportunities': {'bottlenecks': [], 'opportunities': []},
            'evolution_recommendations': []
        }

    def _log_analysis_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log analysis events to database (Rule 2: no log files)"""
        self.db.store_analysis_log({
            'event_type': event_type,
            'event_data': json.dumps(event_data),
            'analyzer_id': self.analyzer_id,
            'timestamp': datetime.now().isoformat()
        })

# [CHECKPOINT 5 COMPLETED: PERFORMANCE ANALYZER IMPLEMENTATION]
# Next: Implement Agent Factory