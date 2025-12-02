"""
Hypothesis Monitoring System
============================
Monitors and validates hypotheses from deep analysis.

Each monitor tracks specific metrics to prove/disprove why system isn't achieving wins.
Results stored in database per Rule 2 (Database-Only Storage).

Created: 2025-12-02
Purpose: Validate 12 hypotheses from deep_analysis_hypotheses.md
"""

import sys
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class HypothesisResult:
    """Result of hypothesis validation."""
    hypothesis_id: str
    hypothesis_name: str
    status: str  # 'CONFIRMED', 'DISPROVED', 'INCONCLUSIVE'
    confidence: float  # 0.0 to 1.0
    evidence: Dict[str, Any]
    recommendations: List[str]
    checked_at: str


class HypothesisMonitor:
    """
    Monitors and validates hypotheses about system performance issues.
    
    Usage:
        monitor = HypothesisMonitor()
        results = monitor.run_all_checks()
        monitor.print_report(results)
    """
    
    DB_PATH = Path(__file__).parent / "core_data.db"
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize with database connection."""
        self.db_path = db_path or self.DB_PATH
        self._ensure_monitoring_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_monitoring_tables(self):
        """Create monitoring tables if they don't exist."""
        with self._get_connection() as conn:
            conn.executescript("""
                -- Frontier discovery tracking (H2)
                CREATE TABLE IF NOT EXISTS frontier_discoveries (
                    discovery_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    agent_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    actions_to_reach INTEGER NOT NULL,
                    was_captured BOOLEAN DEFAULT FALSE,
                    sequence_id TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Hypothesis validation results
                CREATE TABLE IF NOT EXISTS hypothesis_validations (
                    validation_id TEXT PRIMARY KEY,
                    hypothesis_id TEXT NOT NULL,
                    hypothesis_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Budget usage tracking (H5)
                CREATE TABLE IF NOT EXISTS budget_usage_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    generation INTEGER,
                    replay_actions_used INTEGER,
                    exploration_actions_remaining INTEGER,
                    frontier_reached BOOLEAN DEFAULT FALSE,
                    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Role distribution per generation (H1, H7)
                CREATE TABLE IF NOT EXISTS role_distribution_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generation INTEGER NOT NULL,
                    game_type TEXT NOT NULL,
                    pioneer_count INTEGER DEFAULT 0,
                    optimizer_count INTEGER DEFAULT 0,
                    generalist_count INTEGER DEFAULT 0,
                    exploiter_count INTEGER DEFAULT 0,
                    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_frontier_game ON frontier_discoveries(game_type, level_number);
                CREATE INDEX IF NOT EXISTS idx_budget_agent ON budget_usage_log(agent_id, game_id);
                CREATE INDEX IF NOT EXISTS idx_role_gen ON role_distribution_log(generation);
            """)
            conn.commit()
    
    # =========================================================================
    # HYPOTHESIS VALIDATORS
    # =========================================================================
    
    def check_h1_pioneer_role(self) -> HypothesisResult:
        """
        H1: PIONEER ROLE NOT IMPLEMENTED PROPERLY
        Check if pioneers are being assigned and exploring frontier levels.
        """
        with self._get_connection() as conn:
            # Check role distribution
            role_counts = dict(conn.execute("""
                SELECT operating_mode, COUNT(*) as cnt
                FROM agent_operating_modes
                GROUP BY operating_mode
            """).fetchall())
            
            pioneer_count = role_counts.get('pioneer', 0)
            total_modes = sum(role_counts.values())
            
            # Check if any pioneers in recent generations
            recent_pioneers = conn.execute("""
                SELECT COUNT(*) as cnt
                FROM agent_operating_modes
                WHERE operating_mode = 'pioneer'
                AND generation >= (SELECT MAX(generation) - 10 FROM agent_operating_modes)
            """).fetchone()['cnt']
            
            # Check games needing pioneers (games with unbeaten levels)
            games_needing_pioneers = conn.execute("""
                SELECT DISTINCT SUBSTR(game_id, 1, 4) as game_type,
                       COALESCE(MAX(level_number), 0) as max_sequence_level
                FROM winning_sequences
                GROUP BY SUBSTR(game_id, 1, 4)
            """).fetchall()
            
            evidence = {
                'total_pioneer_assignments': pioneer_count,
                'total_mode_assignments': total_modes,
                'pioneer_percentage': (pioneer_count / total_modes * 100) if total_modes > 0 else 0,
                'recent_10_gen_pioneers': recent_pioneers,
                'role_distribution': dict(role_counts),
                'games_with_sequence_levels': {r['game_type']: r['max_sequence_level'] for r in games_needing_pioneers}
            }
            
            # Determine status
            if pioneer_count == 0:
                status = 'CONFIRMED'
                confidence = 0.95
                recommendations = [
                    'CRITICAL: Implement pioneer role assignment in agent_operating_mode_system.py',
                    'Pioneers must be assigned to games with unbeaten levels',
                    'At least 30% of agents should be pioneers during exploration phase',
                    'Check _assign_operating_mode() logic'
                ]
            elif pioneer_count < total_modes * 0.1:
                status = 'CONFIRMED'
                confidence = 0.8
                recommendations = [
                    'Pioneer percentage too low - increase to 30%+ for exploration',
                    'Check fitness rewards for pioneer exploration'
                ]
            else:
                status = 'DISPROVED'
                confidence = 0.7
                recommendations = ['Pioneer role appears functional - check other hypotheses']
            
            return HypothesisResult(
                hypothesis_id='H1',
                hypothesis_name='PIONEER ROLE NOT IMPLEMENTED',
                status=status,
                confidence=confidence,
                evidence=evidence,
                recommendations=recommendations,
                checked_at=datetime.now().isoformat()
            )
    
    def check_h2_sequence_capture(self) -> HypothesisResult:
        """
        H2: SEQUENCE CAPTURE NOT CAPTURING FRONTIER DISCOVERIES
        Compare max levels reached by agents vs max levels with sequences.
        """
        with self._get_connection() as conn:
            # Get max levels reached by agents
            agent_levels = conn.execute("""
                SELECT SUBSTR(game_id, 1, 4) as game_type,
                       MAX(CAST(final_score AS INTEGER)) as max_level_reached
                FROM agent_arc_performance
                GROUP BY SUBSTR(game_id, 1, 4)
            """).fetchall()
            
            # Get max levels with sequences
            sequence_levels = conn.execute("""
                SELECT SUBSTR(game_id, 1, 4) as game_type,
                       MAX(level_number) as max_sequence_level
                FROM winning_sequences
                GROUP BY SUBSTR(game_id, 1, 4)
            """).fetchall()
            
            agent_level_map = {r['game_type']: r['max_level_reached'] for r in agent_levels}
            sequence_level_map = {r['game_type']: r['max_sequence_level'] for r in sequence_levels}
            
            # Find gaps
            gaps = {}
            total_gap = 0
            for game_type, agent_level in agent_level_map.items():
                seq_level = sequence_level_map.get(game_type, 0)
                gap = agent_level - seq_level
                if gap > 0:
                    gaps[game_type] = {
                        'agent_reached': agent_level,
                        'sequence_captured': seq_level,
                        'gap': gap
                    }
                    total_gap += gap
            
            evidence = {
                'agent_max_levels': agent_level_map,
                'sequence_max_levels': sequence_level_map,
                'capture_gaps': gaps,
                'total_uncaptured_levels': total_gap
            }
            
            if total_gap > 5:
                status = 'CONFIRMED'
                confidence = 0.85
                recommendations = [
                    f'CRITICAL: {total_gap} levels discovered but not captured as sequences',
                    'Add logging to _capture_winning_sequence() to track capture attempts',
                    'Check if frontier discoveries are triggering sequence capture',
                    'Verify game_id format in capture matches query format'
                ]
            elif total_gap > 0:
                status = 'INCONCLUSIVE'
                confidence = 0.5
                recommendations = [
                    f'{total_gap} levels have capture gaps - investigate',
                    'May be scoring vs level number confusion'
                ]
            else:
                status = 'DISPROVED'
                confidence = 0.7
                recommendations = ['Sequences captured for all reached levels']
            
            return HypothesisResult(
                hypothesis_id='H2',
                hypothesis_name='SEQUENCE CAPTURE NOT CAPTURING FRONTIER',
                status=status,
                confidence=confidence,
                evidence=evidence,
                recommendations=recommendations,
                checked_at=datetime.now().isoformat()
            )
    
    def check_h4_lp85_corruption(self) -> HypothesisResult:
        """
        H4: lp85 SEQUENCES ARE CORRUPT/WRONG GAME TYPE
        Check lp85 validation rates and sequence quality.
        
        NOTE: lp85 requires symbolic reasoning (object tracking, compositional goals).
        Sequences were intentionally deleted as they were corrupt.
        This check monitors if new sequences are being captured correctly.
        """
        with self._get_connection() as conn:
            # Get lp85 sequence stats
            lp85_sequences = conn.execute("""
                SELECT sequence_id, level_number, total_actions, 
                       times_referenced, 
                       COALESCE(success_rate_when_reused, 0) as success_rate
                FROM winning_sequences
                WHERE game_id LIKE 'lp85%'
            """).fetchall()
            
            # If no lp85 sequences, that's expected (deleted due to corruption)
            if len(lp85_sequences) == 0:
                return HypothesisResult(
                    hypothesis_id='H4',
                    hypothesis_name='lp85 REQUIRES SYMBOLIC REASONING',
                    status='ACKNOWLEDGED',
                    confidence=1.0,
                    evidence={
                        'note': 'lp85 sequences intentionally deleted',
                        'reason': 'Game requires symbolic reasoning: object tracking, compositional goals',
                        'solution': 'Implement symbolic reasoning layer before attempting lp85'
                    },
                    recommendations=[
                        'lp85 requires different approach than pattern matching',
                        'Need: Scene parsing, world model, explicit goal evaluation, search/planning',
                        'Focus on other 5 games first, implement symbolic layer later'
                    ],
                    checked_at=datetime.now().isoformat()
                )
            
            # Get lp85 validation attempts
            lp85_validations = conn.execute("""
                SELECT validation_success, COUNT(*) as cnt
                FROM sequence_validation_attempts
                WHERE game_id LIKE 'lp85%'
                GROUP BY validation_success
            """).fetchall()
            
            # Get lp85 game attempts
            lp85_attempts = conn.execute("""
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN CAST(final_score AS INTEGER) >= 1 THEN 1 ELSE 0 END) as with_levels
                FROM agent_arc_performance
                WHERE game_id LIKE 'lp85%'
            """).fetchone()
            
            validation_results = {str(r['validation_success']): r['cnt'] for r in lp85_validations}
            success_count = validation_results.get('1', 0) + validation_results.get('True', 0)
            fail_count = validation_results.get('0', 0) + validation_results.get('False', 0)
            total_validations = success_count + fail_count
            validation_rate = (success_count / total_validations * 100) if total_validations > 0 else 0
            
            evidence = {
                'sequence_count': len(lp85_sequences),
                'sequences': [dict(s) for s in lp85_sequences[:10]],  # First 10
                'validation_success_count': success_count,
                'validation_fail_count': fail_count,
                'validation_rate': f'{validation_rate:.1f}%',
                'total_game_attempts': lp85_attempts['total'] if lp85_attempts else 0,
                'attempts_with_levels': lp85_attempts['with_levels'] if lp85_attempts else 0
            }
            
            if validation_rate < 30:
                status = 'CONFIRMED'
                confidence = 0.9
                recommendations = [
                    f'CRITICAL: lp85 validation rate is {validation_rate:.1f}% - sequences are corrupt',
                    'DELETE all lp85 sequences and recapture from scratch',
                    'Check if lp85 has moving elements requiring fuzzy matching',
                    'May need game-specific frame comparison for lp85'
                ]
            elif validation_rate < 60:
                status = 'CONFIRMED'
                confidence = 0.7
                recommendations = [
                    f'lp85 validation rate {validation_rate:.1f}% is concerning',
                    'Prune low-success sequences',
                    'Investigate frame matching for this game type'
                ]
            else:
                status = 'DISPROVED'
                confidence = 0.6
                recommendations = ['lp85 validation rates acceptable']
            
            return HypothesisResult(
                hypothesis_id='H4',
                hypothesis_name='lp85 SEQUENCES CORRUPT',
                status=status,
                confidence=confidence,
                evidence=evidence,
                recommendations=recommendations,
                checked_at=datetime.now().isoformat()
            )
    
    def check_h5_budget_exhaustion(self) -> HypothesisResult:
        """
        H5: ACTION BUDGET EXHAUSTION BEFORE FRONTIER EXPLORATION
        Check if action budgets are sufficient for frontier exploration.
        """
        with self._get_connection() as conn:
            # Get sequence action costs
            sequence_costs = conn.execute("""
                SELECT SUBSTR(game_id, 1, 4) as game_type,
                       level_number,
                       AVG(total_actions) as avg_actions,
                       MIN(total_actions) as min_actions,
                       MAX(total_actions) as max_actions
                FROM winning_sequences
                GROUP BY SUBSTR(game_id, 1, 4), level_number
                ORDER BY SUBSTR(game_id, 1, 4), level_number
            """).fetchall()
            
            # Calculate cumulative costs to reach each level
            game_cumulative = {}
            for row in sequence_costs:
                game = row['game_type']
                if game not in game_cumulative:
                    game_cumulative[game] = []
                game_cumulative[game].append({
                    'level': row['level_number'],
                    'avg_actions': row['avg_actions'],
                    'min_actions': row['min_actions']
                })
            
            # Calculate total actions needed to reach frontier
            frontier_costs = {}
            for game, levels in game_cumulative.items():
                total_min = sum(l['min_actions'] for l in levels)
                total_avg = sum(l['avg_actions'] for l in levels)
                frontier_costs[game] = {
                    'levels_known': len(levels),
                    'min_actions_to_frontier': total_min,
                    'avg_actions_to_frontier': total_avg,
                    'budget_remaining_min': 2000 - total_min,
                    'budget_remaining_avg': 2000 - total_avg
                }
            
            # Check budget from game config
            # Default is 2000 based on earlier analysis
            max_budget = 2000
            
            games_over_budget = [g for g, c in frontier_costs.items() if c['min_actions_to_frontier'] > max_budget]
            
            evidence = {
                'assumed_max_budget': max_budget,
                'frontier_costs': frontier_costs,
                'games_exceeding_budget': games_over_budget,
                'sequence_level_costs': [dict(r) for r in sequence_costs]
            }
            
            if len(games_over_budget) > 0:
                status = 'CONFIRMED'
                confidence = 0.85
                recommendations = [
                    f'CRITICAL: {len(games_over_budget)} games require more actions than budget allows',
                    f'Games over budget: {games_over_budget}',
                    'IMMEDIATE FIX: Increase max_total_actions from 2000 to 10000+',
                    'OR: Do not count replay actions against budget',
                    'OR: Give pioneers 3x budget multiplier'
                ]
            elif any(c['budget_remaining_avg'] < 500 for c in frontier_costs.values()):
                status = 'CONFIRMED'
                confidence = 0.7
                recommendations = [
                    'Budgets are tight - less than 500 actions remaining for exploration',
                    'Increase budget to allow meaningful frontier exploration'
                ]
            else:
                status = 'DISPROVED'
                confidence = 0.6
                recommendations = ['Budgets appear sufficient based on sequence costs']
            
            return HypothesisResult(
                hypothesis_id='H5',
                hypothesis_name='BUDGET EXHAUSTION BEFORE FRONTIER',
                status=status,
                confidence=confidence,
                evidence=evidence,
                recommendations=recommendations,
                checked_at=datetime.now().isoformat()
            )
    
    def check_h6_sequence_quality(self) -> HypothesisResult:
        """
        H6: SEQUENCE QUALITY DEGRADATION (Garbage In, Garbage Out)
        Check if sequences are bloated with exploration waste.
        """
        with self._get_connection() as conn:
            # Get sequence stats by level
            level_stats = conn.execute("""
                SELECT level_number,
                       COUNT(*) as sequence_count,
                       AVG(total_actions) as avg_actions,
                       MIN(total_actions) as min_actions,
                       MAX(total_actions) as max_actions
                FROM winning_sequences
                GROUP BY level_number
                ORDER BY level_number
            """).fetchall()
            
            # Identify bloated sequences (>1000 actions for level 1 is suspicious)
            bloated = conn.execute("""
                SELECT sequence_id, game_id, level_number, total_actions
                FROM winning_sequences
                WHERE (level_number = 1 AND total_actions > 500)
                   OR (level_number = 2 AND total_actions > 1500)
                   OR (level_number = 3 AND total_actions > 3000)
                ORDER BY total_actions DESC
                LIMIT 20
            """).fetchall()
            
            # Calculate bloat ratio (avg vs min)
            bloat_ratios = {}
            for row in level_stats:
                if row['min_actions'] > 0:
                    ratio = row['avg_actions'] / row['min_actions']
                    bloat_ratios[row['level_number']] = {
                        'avg': row['avg_actions'],
                        'min': row['min_actions'],
                        'ratio': ratio,
                        'count': row['sequence_count']
                    }
            
            max_bloat_ratio = max((b['ratio'] for b in bloat_ratios.values()), default=1.0)
            
            evidence = {
                'level_statistics': [dict(r) for r in level_stats],
                'bloat_ratios': bloat_ratios,
                'max_bloat_ratio': max_bloat_ratio,
                'bloated_sequences': [dict(r) for r in bloated],
                'bloated_count': len(bloated)
            }
            
            if len(bloated) > 10 or max_bloat_ratio > 5:
                status = 'CONFIRMED'
                confidence = 0.85
                recommendations = [
                    f'CRITICAL: {len(bloated)} bloated sequences found',
                    f'Bloat ratio up to {max_bloat_ratio:.1f}x (avg/min actions)',
                    'Prune sequences with action counts > 3x minimum for same level',
                    'Implement sequence optimization to extract winning subroutine',
                    'Use sequence_abstraction.py to compress action sequences'
                ]
            elif len(bloated) > 0:
                status = 'CONFIRMED'
                confidence = 0.6
                recommendations = [
                    f'{len(bloated)} potentially bloated sequences',
                    'Consider pruning worst offenders'
                ]
            else:
                status = 'DISPROVED'
                confidence = 0.7
                recommendations = ['Sequence sizes appear reasonable']
            
            return HypothesisResult(
                hypothesis_id='H6',
                hypothesis_name='SEQUENCE QUALITY DEGRADATION',
                status=status,
                confidence=confidence,
                evidence=evidence,
                recommendations=recommendations,
                checked_at=datetime.now().isoformat()
            )
    
    def check_h7_role_balance(self) -> HypothesisResult:
        """
        H7: OPTIMIZER/EXPLOITER DOMINATING BUT NOT EXPLORING
        Check if role distribution prevents frontier exploration.
        """
        with self._get_connection() as conn:
            role_counts = conn.execute("""
                SELECT operating_mode, COUNT(*) as cnt
                FROM agent_operating_modes
                GROUP BY operating_mode
            """).fetchall()
            
            role_map = {r['operating_mode']: r['cnt'] for r in role_counts}
            total = sum(role_map.values())
            
            if total == 0:
                evidence = {'error': 'No operating mode data found'}
                return HypothesisResult(
                    hypothesis_id='H7',
                    hypothesis_name='OPTIMIZER/EXPLOITER DOMINATING',
                    status='INCONCLUSIVE',
                    confidence=0.3,
                    evidence=evidence,
                    recommendations=['No operating mode data - check agent_operating_modes table'],
                    checked_at=datetime.now().isoformat()
                )
            
            percentages = {role: (count / total * 100) for role, count in role_map.items()}
            
            exploration_roles = percentages.get('pioneer', 0) + percentages.get('generalist', 0) * 0.3
            exploitation_roles = percentages.get('optimizer', 0) + percentages.get('exploiter', 0)
            
            evidence = {
                'role_counts': role_map,
                'role_percentages': percentages,
                'exploration_capacity': f'{exploration_roles:.1f}%',
                'exploitation_capacity': f'{exploitation_roles:.1f}%',
                'total_assignments': total
            }
            
            if exploration_roles < 20:
                status = 'CONFIRMED'
                confidence = 0.8
                recommendations = [
                    f'CRITICAL: Only {exploration_roles:.1f}% exploration capacity',
                    'Increase pioneer assignment for unbeaten games',
                    'Rebalance: 30% pioneers, 30% optimizers, 30% generalists, 10% exploiters',
                    'Check game state detection (exploration vs optimization mode)'
                ]
            elif exploration_roles < 40:
                status = 'CONFIRMED'
                confidence = 0.6
                recommendations = [
                    f'Exploration capacity {exploration_roles:.1f}% is marginal',
                    'Consider increasing pioneer ratio'
                ]
            else:
                status = 'DISPROVED'
                confidence = 0.7
                recommendations = ['Role balance appears adequate for exploration']
            
            return HypothesisResult(
                hypothesis_id='H7',
                hypothesis_name='OPTIMIZER/EXPLOITER DOMINATING',
                status=status,
                confidence=confidence,
                evidence=evidence,
                recommendations=recommendations,
                checked_at=datetime.now().isoformat()
            )
    
    def check_h8_frame_matching(self) -> HypothesisResult:
        """
        H8: FRAME MATCHING TOO STRICT FOR MOVING GAMES
        Check validation rates by game type for pattern issues.
        """
        with self._get_connection() as conn:
            validation_by_game = conn.execute("""
                SELECT SUBSTR(game_id, 1, 4) as game_type,
                       SUM(CASE WHEN validation_success THEN 1 ELSE 0 END) as success,
                       COUNT(*) as total
                FROM sequence_validation_attempts
                GROUP BY SUBSTR(game_id, 1, 4)
            """).fetchall()
            
            game_rates = {}
            low_validation_games = []
            for row in validation_by_game:
                rate = (row['success'] / row['total'] * 100) if row['total'] > 0 else 0
                game_rates[row['game_type']] = {
                    'success': row['success'],
                    'total': row['total'],
                    'rate': f'{rate:.1f}%'
                }
                if rate < 75:
                    low_validation_games.append((row['game_type'], rate))
            
            evidence = {
                'validation_rates_by_game': game_rates,
                'low_validation_games': low_validation_games
            }
            
            if len(low_validation_games) >= 3:
                status = 'CONFIRMED'
                confidence = 0.75
                recommendations = [
                    f'{len(low_validation_games)} games have <75% validation rate',
                    f'Low games: {low_validation_games}',
                    'Implement fuzzy frame matching for games with moving elements',
                    'Consider game-specific comparison thresholds',
                    'Check if sequences are being validated against wrong frame'
                ]
            elif len(low_validation_games) > 0:
                status = 'INCONCLUSIVE'
                confidence = 0.5
                recommendations = [
                    f'{len(low_validation_games)} games have validation issues',
                    'Investigate frame comparison for these specific games'
                ]
            else:
                status = 'DISPROVED'
                confidence = 0.7
                recommendations = ['Frame matching appears functional across games']
            
            return HypothesisResult(
                hypothesis_id='H8',
                hypothesis_name='FRAME MATCHING TOO STRICT',
                status=status,
                confidence=confidence,
                evidence=evidence,
                recommendations=recommendations,
                checked_at=datetime.now().isoformat()
            )
    
    def check_h9_generation_stagnation(self) -> HypothesisResult:
        """
        H9: GENERATION STAGNATION
        Check if evolution is making progress over generations.
        """
        with self._get_connection() as conn:
            # Get performance by generation (last 50)
            gen_performance = conn.execute("""
                SELECT a.generation,
                       AVG(CAST(p.final_score AS FLOAT)) as avg_score,
                       MAX(CAST(p.final_score AS INTEGER)) as max_level,
                       COUNT(DISTINCT p.agent_id) as agents_played
                FROM agents a
                JOIN agent_arc_performance p ON a.agent_id = p.agent_id
                WHERE a.generation >= (SELECT MAX(generation) - 50 FROM agents)
                GROUP BY a.generation
                ORDER BY a.generation
            """).fetchall()
            
            if len(gen_performance) < 10:
                evidence = {'error': 'Insufficient generation data', 'rows': len(gen_performance)}
                return HypothesisResult(
                    hypothesis_id='H9',
                    hypothesis_name='GENERATION STAGNATION',
                    status='INCONCLUSIVE',
                    confidence=0.3,
                    evidence=evidence,
                    recommendations=['Need more generation data to assess stagnation'],
                    checked_at=datetime.now().isoformat()
                )
            
            # Calculate trend
            scores = [r['avg_score'] for r in gen_performance]
            max_levels = [r['max_level'] for r in gen_performance]
            
            # Simple linear regression for trend
            n = len(scores)
            x_mean = (n - 1) / 2
            y_mean = sum(scores) / n
            
            numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            slope = numerator / denominator if denominator != 0 else 0
            
            # Check if max levels improved
            first_10_max = max(max_levels[:10]) if len(max_levels) >= 10 else max_levels[0]
            last_10_max = max(max_levels[-10:]) if len(max_levels) >= 10 else max_levels[-1]
            level_improvement = last_10_max - first_10_max
            
            evidence = {
                'generations_analyzed': len(gen_performance),
                'score_trend_slope': slope,
                'first_10_gen_max_level': first_10_max,
                'last_10_gen_max_level': last_10_max,
                'level_improvement': level_improvement,
                'avg_score_first_10': sum(scores[:10]) / min(10, len(scores)),
                'avg_score_last_10': sum(scores[-10:]) / min(10, len(scores))
            }
            
            if slope < 0.01 and level_improvement <= 0:
                status = 'CONFIRMED'
                confidence = 0.75
                recommendations = [
                    'Evolution is stagnating - no improvement in max levels',
                    'Check fitness function rewards for frontier exploration',
                    'Consider adding novelty bonus to fitness',
                    'May need to reset and rebuild with better exploration'
                ]
            elif slope < 0.05:
                status = 'INCONCLUSIVE'
                confidence = 0.5
                recommendations = [
                    'Slow improvement detected - may need fitness tuning',
                    'Monitor for continued progress'
                ]
            else:
                status = 'DISPROVED'
                confidence = 0.6
                recommendations = ['Evolution showing positive trend']
            
            return HypothesisResult(
                hypothesis_id='H9',
                hypothesis_name='GENERATION STAGNATION',
                status=status,
                confidence=confidence,
                evidence=evidence,
                recommendations=recommendations,
                checked_at=datetime.now().isoformat()
            )
    
    # =========================================================================
    # MAIN MONITORING METHODS
    # =========================================================================
    
    def run_all_checks(self) -> List[HypothesisResult]:
        """Run all hypothesis checks and return results."""
        checks = [
            self.check_h1_pioneer_role,
            self.check_h2_sequence_capture,
            self.check_h4_lp85_corruption,
            self.check_h5_budget_exhaustion,
            self.check_h6_sequence_quality,
            self.check_h7_role_balance,
            self.check_h8_frame_matching,
            self.check_h9_generation_stagnation,
        ]
        
        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
                self._save_result(result)
            except Exception as e:
                results.append(HypothesisResult(
                    hypothesis_id=check.__name__.replace('check_', '').upper(),
                    hypothesis_name=f'ERROR: {check.__name__}',
                    status='ERROR',
                    confidence=0.0,
                    evidence={'error': str(e)},
                    recommendations=['Fix the monitoring code'],
                    checked_at=datetime.now().isoformat()
                ))
        
        return results
    
    def _save_result(self, result: HypothesisResult):
        """Save hypothesis validation result to database."""
        import json
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO hypothesis_validations
                (validation_id, hypothesis_id, hypothesis_name, status, confidence, evidence, recommendations, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{result.hypothesis_id}_{result.checked_at}",
                result.hypothesis_id,
                result.hypothesis_name,
                result.status,
                result.confidence,
                json.dumps(result.evidence),
                json.dumps(result.recommendations),
                result.checked_at
            ))
            conn.commit()
    
    def print_report(self, results: List[HypothesisResult]):
        """Print formatted report of hypothesis validation results."""
        print("\n" + "=" * 80)
        print("HYPOTHESIS VALIDATION REPORT")
        print("=" * 80)
        print(f"Checked at: {datetime.now().isoformat()}")
        print()
        
        # Group by status
        confirmed = [r for r in results if r.status == 'CONFIRMED']
        inconclusive = [r for r in results if r.status == 'INCONCLUSIVE']
        disproved = [r for r in results if r.status == 'DISPROVED']
        errors = [r for r in results if r.status == 'ERROR']
        
        print(f"SUMMARY: {len(confirmed)} CONFIRMED | {len(inconclusive)} INCONCLUSIVE | {len(disproved)} DISPROVED | {len(errors)} ERRORS")
        print()
        
        if confirmed:
            print("🔴 CONFIRMED ISSUES (Require Immediate Action):")
            print("-" * 60)
            for r in sorted(confirmed, key=lambda x: -x.confidence):
                print(f"  [{r.hypothesis_id}] {r.hypothesis_name}")
                print(f"      Confidence: {r.confidence * 100:.0f}%")
                for rec in r.recommendations[:2]:
                    print(f"      → {rec}")
                print()
        
        if inconclusive:
            print("🟡 INCONCLUSIVE (Need More Data):")
            print("-" * 60)
            for r in inconclusive:
                print(f"  [{r.hypothesis_id}] {r.hypothesis_name}")
                print(f"      Confidence: {r.confidence * 100:.0f}%")
                print()
        
        if disproved:
            print("🟢 DISPROVED (Not Current Issues):")
            print("-" * 60)
            for r in disproved:
                print(f"  [{r.hypothesis_id}] {r.hypothesis_name}")
            print()
        
        print("=" * 80)
        print("PRIORITY ACTION ITEMS:")
        print("-" * 60)
        priority = 1
        for r in sorted(confirmed, key=lambda x: -x.confidence):
            for rec in r.recommendations:
                if 'CRITICAL' in rec or 'IMMEDIATE' in rec:
                    print(f"  {priority}. {rec}")
                    priority += 1
        print("=" * 80)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for monitoring dashboard."""
        with self._get_connection() as conn:
            stats = {
                'total_agents': conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0],
                'total_generations': conn.execute("SELECT MAX(generation) FROM agents").fetchone()[0],
                'total_sequences': conn.execute("SELECT COUNT(*) FROM winning_sequences").fetchone()[0],
                'total_game_attempts': conn.execute("SELECT COUNT(*) FROM agent_arc_performance").fetchone()[0],
            }
            
            # Games with wins
            games_with_wins = conn.execute("""
                SELECT SUBSTR(game_id, 1, 4) as game_type, MAX(CAST(final_score AS INTEGER)) as max_level
                FROM agent_arc_performance
                GROUP BY SUBSTR(game_id, 1, 4)
            """).fetchall()
            stats['games_progress'] = {r['game_type']: r['max_level'] for r in games_with_wins}
            
            return stats


def main():
    """Run hypothesis monitoring and print report."""
    monitor = HypothesisMonitor()
    
    print("Running hypothesis validations...")
    results = monitor.run_all_checks()
    
    monitor.print_report(results)
    
    print("\nSummary Stats:")
    stats = monitor.get_summary_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
