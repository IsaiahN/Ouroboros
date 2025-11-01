#!/usr/bin/env python3
"""
Adaptive Action Limit Manager
=============================

Automatically adjusts max_actions_per_level and max_total_actions based on
generation performance. Gives more exploration time to successful agents/generations,
and reduces time for unproductive ones.

Rule 4: LLM Self-Management - System adjusts autonomously based on data
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from typing import Dict, Tuple
from datetime import datetime, timedelta


class AdaptiveActionLimits:
    """
    Dynamically adjusts action limits based on generation performance.
    
    Philosophy:
    - Successful agents/generations get MORE time to explore
    - Struggling agents get LESS time to speed up evolution cycles
    - Hard floor: 200 actions per level minimum
    - Adjusts every generation based on comprehensive success metrics
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        
        # Hard constraints
        self.MIN_ACTIONS_PER_LEVEL = 200  # Hard floor (never go below)
        self.MAX_ACTIONS_PER_LEVEL = 1000  # Ceiling (increased for multi-level discovery)
        self.MIN_TOTAL_ACTIONS = 1000     # Minimum total (increased from 600)
        self.MAX_TOTAL_ACTIONS = 12000     # Maximum total (increased from 3000 for multi-level runs)
        
        # Starting defaults (generous for discovery, will adapt down)
        self.current_actions_per_level = 400  # Increased from 200
        self.current_total_actions = 7000     # Increased from 1000 for multi-level discovery
        
        # Adjustment parameters
        self.ADJUSTMENT_RATE = 0.15  # 15% adjustment per generation
        self.SUCCESS_THRESHOLD = 0.10  # 10% comprehensive success = good
        self.STAGNATION_THRESHOLD = 0.02  # <2% = reduce limits
    
    def calculate_generation_performance(self, generation: int) -> Dict[str, float]:
        """
        Calculate performance metrics for a generation.
        
        Args:
            generation: Generation number
            
        Returns:
            Dictionary with performance metrics
        """
        # Get all agents in this generation
        agents = self.db.execute_query("""
            SELECT agent_id 
            FROM agents 
            WHERE generation = ? AND is_active = 1
        """, (generation,))
        
        if not agents:
            return {
                'comprehensive_success': 0.0,
                'avg_actions_used': 0.0,
                'score_rate': 0.0,
                'efficiency': 0.0,
                'sample_size': 0
            }
        
        # Get performance for all agents in generation
        total_games = 0
        total_wins = 0
        total_scores = 0  # Games with ANY score > 0
        total_high_scores = 0  # Games with win_proximity >= 0.5
        total_levels = 0
        total_actions = 0
        
        for agent in agents:
            agent_id = agent['agent_id']
            
            perf = self.db.execute_query("""
                SELECT 
                    COUNT(*) as games,
                    SUM(CASE WHEN win_achieved THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as score_progress,
                    SUM(CASE WHEN win_proximity >= 0.5 THEN 1 ELSE 0 END) as high_scores,
                    SUM(level_progressions) as levels,
                    AVG(total_actions) as avg_actions
                FROM agent_arc_performance
                WHERE agent_id = ?
            """, (agent_id,))
            
            if perf and perf[0]['games'] > 0:
                total_games += perf[0]['games']
                total_wins += perf[0]['wins'] or 0
                total_scores += perf[0]['score_progress'] or 0  # ANY score > 0
                total_high_scores += perf[0]['high_scores'] or 0  # High scores
                total_levels += perf[0]['levels'] or 0
                total_actions += (perf[0]['avg_actions'] or 0) * perf[0]['games']
        
        if total_games == 0:
            return {
                'comprehensive_success': 0.0,
                'avg_actions_used': 0.0,
                'score_progress_rate': 0.0,
                'game_win_rate': 0.0,
                'high_score_rate': 0.0,
                'path_efficiency': 0.0,
                'sample_size': 0
            }
        
        # Score-focused fitness calculation (aligned with performance_analyzer.py)
        game_win_rate = total_wins / total_games
        score_progress_rate = total_scores / total_games  # ANY score > 0 (most important)
        level_success_rate = min(1.0, total_levels / (total_games * 3))  # Assume 3 levels per game
        high_score_rate = total_high_scores / total_games  # High scores already tracked
        
        # Path efficiency (normalized)
        avg_actions = total_actions / total_games
        path_efficiency = min(1.0, 100.0 / avg_actions) if avg_actions > 0 else 0.0
        
        # NEW WEIGHTS: 40% score progress, 30% wins, 15% levels, 10% high scores, 5% efficiency
        comprehensive_success = (
            score_progress_rate * 0.40 +   # ANY score increase (MOST IMPORTANT)
            game_win_rate * 0.30 +          # Full wins
            level_success_rate * 0.15 +     # Level completions
            high_score_rate * 0.10 +        # High scores (≥50% win threshold)
            path_efficiency * 0.05          # Efficiency bonus
        )
        
        return {
            'comprehensive_success': comprehensive_success,
            'avg_actions_used': avg_actions,
            'score_progress_rate': score_progress_rate,
            'game_win_rate': game_win_rate,
            'high_score_rate': high_score_rate,
            'path_efficiency': path_efficiency,
            'sample_size': total_games
        }
    
    def adjust_limits(self, current_generation: int) -> Tuple[int, int]:
        """
        Adjust action limits based on recent generation performance.
        
        Args:
            current_generation: Current generation number
            
        Returns:
            Tuple of (actions_per_level, total_actions)
        """
        if current_generation < 1:
            # First generation, use defaults
            return self.current_actions_per_level, self.current_total_actions
        
        # Analyze last 2 generations for trend
        generations_to_analyze = [current_generation - 1]
        if current_generation >= 2:
            generations_to_analyze.append(current_generation - 2)
        
        performances = []
        for gen in generations_to_analyze:
            perf = self.calculate_generation_performance(gen)
            if perf['sample_size'] >= 5:  # Need at least 5 games for meaningful data
                performances.append(perf)
        
        if not performances:
            # Not enough data, keep current limits
            return self.current_actions_per_level, self.current_total_actions
        
        # Get most recent performance
        recent_perf = performances[0]
        comprehensive_success = recent_perf['comprehensive_success']
        avg_actions = recent_perf['avg_actions_used']
        
        # Determine adjustment direction
        adjustment_factor = 1.0
        reason = ""
        
        if comprehensive_success >= self.SUCCESS_THRESHOLD:
            # Doing well! Give MORE time to explore further
            adjustment_factor = 1.0 + self.ADJUSTMENT_RATE
            reason = f"High success ({comprehensive_success:.1%}) - increasing limits"
            
        elif comprehensive_success < self.STAGNATION_THRESHOLD:
            # Struggling badly, reduce time to speed up evolution
            adjustment_factor = 1.0 - self.ADJUSTMENT_RATE
            reason = f"Low success ({comprehensive_success:.1%}) - reducing limits"
            
        elif len(performances) >= 2:
            # Compare trend
            prev_success = performances[1]['comprehensive_success']
            if comprehensive_success > prev_success * 1.2:  # 20% improvement
                adjustment_factor = 1.0 + (self.ADJUSTMENT_RATE * 0.5)  # Modest increase
                reason = f"Improving trend ({prev_success:.1%}→{comprehensive_success:.1%}) - increasing slightly"
            elif comprehensive_success < prev_success * 0.8:  # 20% decline
                adjustment_factor = 1.0 - (self.ADJUSTMENT_RATE * 0.5)  # Modest decrease
                reason = f"Declining trend ({prev_success:.1%}→{comprehensive_success:.1%}) - reducing slightly"
            else:
                reason = f"Stable performance ({comprehensive_success:.1%}) - maintaining limits"
        else:
            reason = f"Moderate success ({comprehensive_success:.1%}) - maintaining limits"
        
        # Check efficiency - if using way less than available, can reduce
        if avg_actions > 0:
            utilization = avg_actions / self.current_total_actions
            if utilization < 0.3 and adjustment_factor >= 1.0:
                # Using <30% of available actions, don't increase
                adjustment_factor = min(adjustment_factor, 1.0)
                reason += " (low utilization, capping increase)"
        
        # Apply adjustment
        new_actions_per_level = int(self.current_actions_per_level * adjustment_factor)
        new_total_actions = int(self.current_total_actions * adjustment_factor)
        
        # Apply hard constraints
        new_actions_per_level = max(self.MIN_ACTIONS_PER_LEVEL, 
                                     min(self.MAX_ACTIONS_PER_LEVEL, new_actions_per_level))
        new_total_actions = max(self.MIN_TOTAL_ACTIONS,
                                min(self.MAX_TOTAL_ACTIONS, new_total_actions))
        
        # Ensure total is at least 3x per-level (for multi-level games)
        new_total_actions = max(new_total_actions, new_actions_per_level * 3)
        
        # Store new limits
        self.current_actions_per_level = new_actions_per_level
        self.current_total_actions = new_total_actions
        
        # Log the adjustment
        self._log_adjustment(current_generation, recent_perf, new_actions_per_level, 
                            new_total_actions, reason)
        
        return new_actions_per_level, new_total_actions
    
    def _log_adjustment(self, generation: int, performance: Dict, 
                       actions_per_level: int, total_actions: int, reason: str):
        """Log limit adjustment to database for tracking."""
        try:
            self.db.execute_query("""
                INSERT INTO system_logs (timestamp, level, logger_name, message, extra_data)
                VALUES (?, 'INFO', 'AdaptiveActionLimits', ?, ?)
            """, (
                datetime.now().isoformat(),
                f"Gen-{generation} action limits adjusted: {actions_per_level}/level, {total_actions}/game",
                f"Success: {performance['comprehensive_success']:.1%}, "
                f"Avg actions: {performance['avg_actions_used']:.0f}, "
                f"Reason: {reason}"
            ))
        except Exception as e:
            # Non-critical, just print
            print(f"  (Note: Could not log adjustment: {e})")
    
    def get_current_limits(self) -> Tuple[int, int]:
        """
        Get current action limits.
        
        Returns:
            Tuple of (actions_per_level, total_actions)
        """
        return self.current_actions_per_level, self.current_total_actions
    
    def print_status(self):
        """Print current limit status."""
        print(f"\n📊 Adaptive Action Limits:")
        print(f"   Per-level: {self.current_actions_per_level} (floor: {self.MIN_ACTIONS_PER_LEVEL}, ceiling: {self.MAX_ACTIONS_PER_LEVEL})")
        print(f"   Total: {self.current_total_actions} (min: {self.MIN_TOTAL_ACTIONS}, max: {self.MAX_TOTAL_ACTIONS})")
