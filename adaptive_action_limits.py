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
from typing import Dict, Tuple, Any
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
        self.MAX_ACTIONS_PER_LEVEL = 1500  # Ceiling (INCREASED: 300 → 1500, level 3 requires 5000+ total)
        self.MIN_TOTAL_ACTIONS = 1000     # Minimum total
        self.MAX_TOTAL_ACTIONS = 8000     # Maximum total (INCREASED: 1500 → 8000, level 3 empirically needs 5000+)
        
        # BREAKTHROUGH UNLOCKED: Level 3+ action requirements discovered
        # Empirical data: L1=389 actions, L2=653 actions, L3=5017 actions (7.7x jump!)
        # Old limit (1500) was blocking 99.5% of level 3 attempts
        # New limit (8000) allows deep exploration while maintaining efficiency pressure
        
        # Starting defaults (INCREASED to allow level 3 breakthrough attempts)
        self.current_actions_per_level = 800   # INCREASED: 250 → 800 (allows L3 exploration)
        self.current_total_actions = 5000      # INCREASED: 1250 → 5000 (matches L3 empirical requirement)
        
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
        print(f"\n[CHART] Adaptive Action Limits:")
        print(f"   Per-level: {self.current_actions_per_level} (floor: {self.MIN_ACTIONS_PER_LEVEL}, ceiling: {self.MAX_ACTIONS_PER_LEVEL})")
        print(f"   Total: {self.current_total_actions} (min: {self.MIN_TOTAL_ACTIONS}, max: {self.MAX_TOTAL_ACTIONS})")
    
    # ========================================================================
    # PHASE 2: PER-AGENT ACTION ECONOMY (ECOSYSTEM METABOLISM)
    # Actions = Metabolic Currency (ATP), NOT just agent salary
    # CRITICAL: Keep prestige (social capital) COMPLETELY SEPARATE
    # ========================================================================
    
    def calculate_agent_salary(self, agent_id: str, generation: int) -> Dict[str, Any]:
        """
        Calculate per-agent action budget based on PERFORMANCE (not prestige).
        
        CRITICAL DISTINCTION:
        - Prestige = Social Capital (breeding, survival, network contribution)
        - Actions = Economic Capital (metabolic energy, what you can DO)
        - These are COMPLETELY SEPARATE currencies
        
        Salary Formula:
        - Base metabolism: MIN_ACTIONS (survival level)
        - Performance bonus: Based on percentile rank (0x to 3x multiplier)
        - High performers get MORE actions (metabolic energy)
        - Low performers get baseline (limited energy)
        
        Args:
            agent_id: Agent to calculate salary for
            generation: Current generation
            
        Returns:
            Dictionary with:
                - action_allowance_per_level: Actions per level
                - action_allowance_total: Total actions per game
                - budget_multiplier: Performance multiplier (0.5x to 3.0x)
        """
        # Get agent's comprehensive success (performance-based, NOT prestige)
        agent = self.db.execute_query("""
            SELECT 
                total_games_played,
                total_games_won,
                total_score_achieved,
                avg_score_per_game,
                score_efficiency,
                level_progressions_detected
            FROM agents 
            WHERE agent_id = ?
        """, (agent_id,))
        
        if not agent or agent[0]['total_games_played'] == 0:
            # New agent, give baseline budget
            return {
                'action_allowance_per_level': self.current_actions_per_level,
                'action_allowance_total': self.current_total_actions,
                'budget_multiplier': 1.0
            }
        
        # Calculate comprehensive success for THIS agent
        agent_data = agent[0]
        comprehensive_success = self._calculate_agent_comprehensive_success(agent_data)
        
        # Get performance percentile (where does this agent rank?)
        percentile = self._get_agent_performance_percentile(agent_id, generation)
        
        # Calculate budget multiplier based on percentile
        # Bottom 25%: 0.5x to 1.0x (limited metabolism)
        # Middle 50%: 1.0x to 1.5x (normal metabolism)
        # Top 25%: 1.5x to 3.0x (high metabolism)
        if percentile < 0.25:
            # Bottom quartile: 0.5x to 1.0x
            budget_multiplier = 0.5 + (percentile / 0.25) * 0.5
        elif percentile < 0.75:
            # Middle 50%: 1.0x to 1.5x
            budget_multiplier = 1.0 + ((percentile - 0.25) / 0.50) * 0.5
        else:
            # Top quartile: 1.5x to 3.0x
            budget_multiplier = 1.5 + ((percentile - 0.75) / 0.25) * 1.5
            
        # NEW: Check for unbeaten game bonus (2x multiplier for difficult games)
        unbeaten_bonus = self._check_unbeaten_game_bonus(agent_id)
        if unbeaten_bonus > 1.0:
            budget_multiplier *= unbeaten_bonus
        
        # Apply multiplier to generation baseline
        action_allowance_per_level = int(self.current_actions_per_level * budget_multiplier)
        action_allowance_total = int(self.current_total_actions * budget_multiplier)
        
        # Enforce hard constraints
        action_allowance_per_level = max(self.MIN_ACTIONS_PER_LEVEL,
                                         min(self.MAX_ACTIONS_PER_LEVEL, action_allowance_per_level))
        action_allowance_total = max(self.MIN_TOTAL_ACTIONS,
                                     min(self.MAX_TOTAL_ACTIONS, action_allowance_total))
        
        return {
            'action_allowance_per_level': action_allowance_per_level,
            'action_allowance_total': action_allowance_total,
            'budget_multiplier': budget_multiplier,
            'unbeaten_bonus': unbeaten_bonus if 'unbeaten_bonus' in locals() else 1.0
        }
    
    def _check_unbeaten_game_bonus(self, agent_id: str) -> float:
        """
        Check if agent is working on games with 0 level completions and needs action budget boost.
        
        CRITICAL: Only applies to games where NO AGENT has ever completed a level
        (not just this agent - ANY agent in the population)
        
        Returns multiplier:
        - 1.0: Normal (agent working on games that have been beaten by someone)
        - 2.0: Boost (agent assigned to games with 0 level completions by anyone)
        - 3.0: High boost (agent assigned ONLY to unbeaten games)
        """
        # Get agent's assigned games from specialization
        agent_info = self.db.execute_query("""
            SELECT specialization FROM agents WHERE agent_id = ?
        """, (agent_id,))
        
        if not agent_info:
            return 1.0
            
        try:
            import json
            
            def safe_json_parse(json_str, default=None):
                """Safely parse JSON string, returning default if invalid or empty."""
                if not json_str or json_str.strip() == '':
                    return default or {}
                try:
                    return json.loads(json_str)
                except (json.JSONDecodeError, TypeError):
                    return default or {}
            
            spec = safe_json_parse(agent_info[0]['specialization'])
            assigned_games = spec.get('assigned_games', [])
            
            if not assigned_games:
                return 1.0  # No assignment, no bonus
                
            # Check which assigned games have NEVER had level wins BY ANY AGENT
            unbeaten_count = 0
            total_assigned = len(assigned_games)
            
            for game_id in assigned_games:
                # Check if ANY agent has EVER completed a level in this game
                level_wins = self.db.execute_query("""
                    SELECT COUNT(*) as wins
                    FROM agent_arc_performance 
                    WHERE game_id = ? AND level_progressions > 0
                """, (game_id,))
                
                # If no agent has ever completed a level in this game
                if level_wins and level_wins[0]['wins'] == 0:
                    unbeaten_count += 1
                    
            # Calculate bonus based on proportion of unbeaten games
            if unbeaten_count == 0:
                return 1.0  # No unbeaten games, no bonus
            elif unbeaten_count == total_assigned:
                return 3.0  # ALL assigned games unbeaten by anyone, high boost
            else:
                return 2.0  # SOME assigned games unbeaten by anyone, moderate boost
                
        except (json.JSONDecodeError, KeyError):
            return 1.0  # Can't parse specialization, no bonus
    
    def _get_agent_performance_percentile(self, agent_id: str, generation: int) -> float:
        """
        Calculate where this agent ranks in the population (0.0 to 1.0).
        
        Args:
            agent_id: Agent to rank
            generation: Current generation
            
        Returns:
            Percentile rank (0.0 = bottom, 1.0 = top)
        """
        # Get this agent's comprehensive success
        agent = self.db.execute_query("""
            SELECT 
                total_games_played,
                total_games_won,
                total_score_achieved,
                avg_score_per_game,
                score_efficiency,
                level_progressions_detected
            FROM agents 
            WHERE agent_id = ?
        """, (agent_id,))
        
        if not agent or agent[0]['total_games_played'] == 0:
            return 0.5  # Middle of pack for new agents
        
        agent_success = self._calculate_agent_comprehensive_success(agent[0])
        
        # Get all active agents in recent generations (include last 3 gens for comparison)
        min_gen = max(0, generation - 3)
        all_agents = self.db.execute_query("""
            SELECT 
                total_games_played,
                total_games_won,
                total_score_achieved,
                avg_score_per_game,
                score_efficiency,
                level_progressions_detected
            FROM agents 
            WHERE is_active = 1 
              AND generation >= ?
              AND total_games_played > 0
        """, (min_gen,))
        
        if not all_agents or len(all_agents) < 2:
            return 0.5  # Middle if no comparison
        
        # Calculate success for all agents
        success_scores = []
        for a in all_agents:
            success = self._calculate_agent_comprehensive_success(a)
            success_scores.append(success)
        
        # Calculate percentile
        success_scores.sort()
        rank = sum(1 for s in success_scores if s < agent_success)
        percentile = rank / len(success_scores)
        
        return percentile
    
    def _calculate_agent_comprehensive_success(self, agent: Dict) -> float:
        """
        Calculate comprehensive success score for an agent.
        Same formula as calculate_generation_performance() but for one agent.
        
        Args:
            agent: Agent data dict with performance fields
            
        Returns:
            Comprehensive success score (0.0 to 1.0)
        """
        total_games = agent['total_games_played']
        if total_games == 0:
            return 0.0
        
        # Get detailed performance if available
        game_win_rate = agent['total_games_won'] / total_games
        
        # Score progress rate (if they're scoring at all)
        score_progress = 1.0 if agent['avg_score_per_game'] > 0 else 0.0
        
        # Level success (assume 3 levels per game)
        level_success_rate = min(1.0, agent['level_progressions_detected'] / (total_games * 3))
        
        # High score rate (approximation: if avg_score > 1.0, they're doing well)
        high_score_rate = min(1.0, agent['avg_score_per_game'] / 2.0)
        
        # Path efficiency
        path_efficiency = min(1.0, agent['score_efficiency'] * 100) if agent['score_efficiency'] > 0 else 0.0
        
        # NEW WEIGHTS: 40% score, 30% wins, 15% levels, 10% high scores, 5% efficiency
        comprehensive_success = (
            score_progress * 0.40 +
            game_win_rate * 0.30 +
            level_success_rate * 0.15 +
            high_score_rate * 0.10 +
            path_efficiency * 0.05
        )
        
        return comprehensive_success
    
    # ========================================================================
    # PHASE 2: ECOSYSTEM METABOLISM TRACKING (NETWORK-LEVEL RESOURCE FLOW)
    # Biome Theory: Track the metabolic health of the entire network organism
    # ========================================================================
    
    def track_ecosystem_metabolism(self, generation: int) -> Dict[str, Any]:
        """
        Track network-level metabolic health.
        
        PHASE 2: Ecosystem metabolism - the "vital signs" of the network organism.
        Just as biomes track energy flow (sunlight → plants → herbivores → carnivores),
        we track action flow (salary → budgets → games → scores).
        
        Args:
            generation: Current generation
            
        Returns:
            Metabolism snapshot dictionary
        """
        import uuid
        from datetime import datetime
        
        try:
            # Get total budget allocated (network ATP pool)
            budget_data = self.db.execute_query("""
                SELECT 
                    COUNT(*) as agent_count,
                    SUM(action_allowance_total) as total_budgeted,
                    AVG(action_allowance_total) as avg_budget,
                    MIN(action_allowance_total) as min_budget,
                    MAX(action_allowance_total) as max_budget
                FROM agents 
                WHERE is_active = 1
            """)
            
            if not budget_data or not budget_data[0]:
                return {}
            
            budget_stats = budget_data[0]
            total_budgeted = budget_stats['total_budgeted'] or 0
            agent_count = budget_stats['agent_count'] or 0
            
            # Get total actions actually spent this generation
            spent_data = self.db.execute_query("""
                SELECT 
                    COALESCE(SUM(actions_spent), 0) as total_spent,
                    COALESCE(SUM(final_score), 0) as total_score,
                    COUNT(*) as game_count
                FROM agent_arc_performance
                WHERE game_timestamp >= datetime('now', '-1 hour')
            """)
            
            total_spent = 0
            total_score = 0
            if spent_data and spent_data[0]:
                total_spent = spent_data[0]['total_spent'] or 0
                total_score = spent_data[0]['total_score'] or 0
            
            # Calculate metrics
            total_available = total_budgeted
            total_wasted = max(0, total_budgeted - total_spent)
            
            # Metabolic efficiency (score per action)
            metabolic_efficiency = total_score / max(total_spent, 1)
            
            # Resource scarcity (how constrained is the network?)
            # 0 = abundant resources, 1 = critical scarcity
            utilization = total_spent / max(total_budgeted, 1)
            resource_scarcity = min(1.0, utilization)
            
            # Budget distribution (Gini coefficient for inequality)
            budgets = self.db.execute_query("""
                SELECT action_allowance_total 
                FROM agents 
                WHERE is_active = 1
            """)
            
            gini = 0.0
            if budgets and len(budgets) > 1:
                budget_values = [b['action_allowance_total'] for b in budgets]
                gini = self._calculate_gini(budget_values)
            
            # Top/bottom distribution
            if agent_count > 0:
                top_10_count = max(1, agent_count // 10)
                bottom_50_count = agent_count // 2
                
                top_budgets = self.db.execute_query(f"""
                    SELECT SUM(action_allowance_total) as top_total
                    FROM (
                        SELECT action_allowance_total 
                        FROM agents 
                        WHERE is_active = 1
                        ORDER BY action_allowance_total DESC
                        LIMIT {top_10_count}
                    )
                """)
                
                bottom_budgets = self.db.execute_query(f"""
                    SELECT SUM(action_allowance_total) as bottom_total
                    FROM (
                        SELECT action_allowance_total 
                        FROM agents 
                        WHERE is_active = 1
                        ORDER BY action_allowance_total ASC
                        LIMIT {bottom_50_count}
                    )
                """)
                
                top_10_share = (top_budgets[0]['top_total'] / max(total_budgeted, 1)) if top_budgets and top_budgets[0]['top_total'] else 0
                bottom_50_share = (bottom_budgets[0]['bottom_total'] / max(total_budgeted, 1)) if bottom_budgets and bottom_budgets[0]['bottom_total'] else 0
            else:
                top_10_share = 0
                bottom_50_share = 0
            
            # Agent distribution
            agents_above = self.db.execute_query("""
                SELECT COUNT(*) as count 
                FROM agents 
                WHERE is_active = 1 AND action_budget_multiplier > 1.0
            """)
            agents_below = self.db.execute_query("""
                SELECT COUNT(*) as count 
                FROM agents 
                WHERE is_active = 1 AND action_budget_multiplier < 1.0
            """)
            
            agents_above_baseline = agents_above[0]['count'] if agents_above and agents_above[0] else 0
            agents_below_baseline = agents_below[0]['count'] if agents_below and agents_below[0] else 0
            
            # Create snapshot
            snapshot = {
                'snapshot_id': f"metabolism_{generation}_{uuid.uuid4().hex[:8]}",
                'generation': generation,
                'snapshot_timestamp': datetime.now().isoformat(),
                'total_actions_available': total_available,
                'total_actions_budgeted': total_budgeted,
                'total_actions_spent': total_spent,
                'total_actions_wasted': total_wasted,
                'gini_coefficient': gini,
                'top_10_percent_share': top_10_share,
                'bottom_50_percent_share': bottom_50_share,
                'action_creation_rate': total_budgeted / max(agent_count, 1),  # Actions per agent
                'action_destruction_rate': total_spent / max(agent_count, 1),   # Spent per agent
                'metabolic_efficiency': metabolic_efficiency,
                'resource_scarcity_index': resource_scarcity,
                'budget_inflation_rate': 0.0,  # Will calculate in future with historical data
                'active_agent_count': agent_count,
                'agents_above_baseline': agents_above_baseline,
                'agents_below_baseline': agents_below_baseline
            }
            
            # Store snapshot in database
            self.db.execute_query("""
                INSERT INTO ecosystem_metabolism_snapshots (
                    snapshot_id, generation, snapshot_timestamp,
                    total_actions_available, total_actions_budgeted, 
                    total_actions_spent, total_actions_wasted,
                    gini_coefficient, top_10_percent_share, bottom_50_percent_share,
                    action_creation_rate, action_destruction_rate, metabolic_efficiency,
                    resource_scarcity_index, budget_inflation_rate,
                    active_agent_count, agents_above_baseline, agents_below_baseline
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot['snapshot_id'], snapshot['generation'], snapshot['snapshot_timestamp'],
                snapshot['total_actions_available'], snapshot['total_actions_budgeted'],
                snapshot['total_actions_spent'], snapshot['total_actions_wasted'],
                snapshot['gini_coefficient'], snapshot['top_10_percent_share'], snapshot['bottom_50_percent_share'],
                snapshot['action_creation_rate'], snapshot['action_destruction_rate'], snapshot['metabolic_efficiency'],
                snapshot['resource_scarcity_index'], snapshot['budget_inflation_rate'],
                snapshot['active_agent_count'], snapshot['agents_above_baseline'], snapshot['agents_below_baseline']
            ))
            
            return snapshot
            
        except Exception as e:
            print(f"[WARN] Ecosystem metabolism tracking failed: {e}")
            return {}
    
    def _calculate_gini(self, values: list) -> float:
        """Calculate Gini coefficient for inequality measurement."""
        if not values or len(values) < 2:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = 0
        
        for i, val in enumerate(sorted_values):
            cumsum += (2 * (i + 1) - n - 1) * val
        
        gini = cumsum / (n * sum(sorted_values))
        return abs(gini)
    
    def display_ecosystem_metabolism_report(self, generation: int):
        """
        Display ecosystem metabolism dashboard.
        
        PHASE 2: Network-level "vital signs" - the metabolic health of the organism.
        """
        try:
            # Get latest snapshot
            snapshot = self.db.execute_query("""
                SELECT * FROM ecosystem_metabolism_snapshots
                WHERE generation = ?
                ORDER BY snapshot_timestamp DESC
                LIMIT 1
            """, (generation,))
            
            if not snapshot or not snapshot[0]:
                print("\n[METABOLISM] No metabolism data available yet")
                return
            
            data = snapshot[0]
            
            print(f"\n{'='*80}")
            print(f"[METABOLISM] ECOSYSTEM VITAL SIGNS - Generation {generation}")
            print(f"{'='*80}")
            
            # Network ATP pool
            print(f"\nNetwork ATP Pool (Action Budget):")
            print(f"  Total Available: {data['total_actions_available']:,.0f} actions")
            print(f"  Total Budgeted: {data['total_actions_budgeted']:,.0f} actions")
            print(f"  Total Spent: {data['total_actions_spent']:,.0f} actions ({data['total_actions_spent']/max(data['total_actions_budgeted'],1)*100:.1f}% utilization)")
            print(f"  Total Wasted: {data['total_actions_wasted']:,.0f} actions (unused budget)")
            
            # Metabolic rates
            print(f"\nMetabolic Rates:")
            print(f"  Creation Rate: {data['action_creation_rate']:.0f} actions/agent (salary)")
            print(f"  Destruction Rate: {data['action_destruction_rate']:.0f} actions/agent (spending)")
            print(f"  Efficiency: {data['metabolic_efficiency']:.4f} score/action")
            
            # Resource distribution
            print(f"\nResource Distribution:")
            print(f"  Inequality (Gini): {data['gini_coefficient']:.3f}")
            print(f"  Top 10% Share: {data['top_10_percent_share']*100:.1f}% of total budget")
            print(f"  Bottom 50% Share: {data['bottom_50_percent_share']*100:.1f}% of total budget")
            
            # Population economics
            print(f"\nPopulation Economics:")
            print(f"  Active Agents: {data['active_agent_count']}")
            print(f"  Above Baseline (>1.0x): {data['agents_above_baseline']} ({data['agents_above_baseline']/max(data['active_agent_count'],1)*100:.1f}%)")
            print(f"  Below Baseline (<1.0x): {data['agents_below_baseline']} ({data['agents_below_baseline']/max(data['active_agent_count'],1)*100:.1f}%)")
            
            # Network health assessment
            scarcity = data['resource_scarcity_index']
            if scarcity < 0.3:
                health_status = "ABUNDANT (low utilization)"
            elif scarcity < 0.7:
                health_status = "HEALTHY (moderate utilization)"
            elif scarcity < 0.9:
                health_status = "STRESSED (high utilization)"
            else:
                health_status = "CRITICAL (near-exhaustion)"
            
            print(f"\nNetwork Health: {health_status}")
            print(f"  Resource Scarcity: {scarcity:.3f} (0=abundant, 1=critical)")
            
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"[WARN] Metabolism report display failed: {e}")

