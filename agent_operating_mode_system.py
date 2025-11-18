"""
Agent Operating Mode System

Implements dynamic role assignment for agents:
EXPLORATION Phase (no full wins yet):
- 60% PIONEERS: 5x mutation rate, maximum exploration (breakthrough seekers)
- 10% OPTIMIZERS: 0.5x mutation rate, refine partial wins
- 20% GENERALISTS: 1.0x mutation rate, maintain baseline capability
- 10% EXPLOITERS: 0.1x mutation, only replay proven sequences (harvest)

OPTIMIZATION Phase (at least one full win):
- 10% PIONEERS: Continue exploring new strategies
- 50% OPTIMIZERS: 0.5x mutation rate, refine known sequences (efficiency experts)
- 25% GENERALISTS: 1.0x mutation rate, maintain diversity
- 15% EXPLOITERS: Pure exploitation of proven sequences

Modes are per-deployment (agent can switch roles between games based on performance).
Network-wide coordination ensures population maintains optimal distribution.

BIOLOGY-INSPIRED: Ant colonies, bacterial quorum sensing, neural exploration/exploitation
"""

import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random
import logging
from database_interface import DatabaseInterface

# Suppress pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

logger = logging.getLogger(__name__)


class AgentOperatingModeSystem:
    """Manages dynamic role assignment for agents (Pioneer/Optimizer/Generalist/Exploiter)"""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        
        # ADAPTIVE population distribution based on whether any games fully beaten
        # Check if any games have been completely won
        self._update_population_distribution()
        
        # Distribution will be set by _update_population_distribution():
        # EXPLORATION PHASE (no full wins): 60% PIONEER, 10% OPTIMIZER, 20% GENERALIST, 10% EXPLOITER
        # OPTIMIZATION PHASE (has full wins): 10% PIONEER, 50% OPTIMIZER, 25% GENERALIST, 15% EXPLOITER
        
        # Mode mutation multipliers
        self.PIONEER_MUTATION_MULTIPLIER = 5.0     # 5x exploration
        self.OPTIMIZER_MUTATION_MULTIPLIER = 0.5   # Half mutation
        self.GENERALIST_MUTATION_MULTIPLIER = 1.0  # Normal
        
        # Mode behavior parameters
        self.MODE_PARAMETERS = {
            'pioneer': {
                'mutation_multiplier': 5.0,
                'action_diversity': 0.95,
                'novelty_seeking': 0.9,
                'risk_tolerance': 0.9,
                'exploit_sequences': False,
                'description': 'Breakthrough seeker - maximum exploration'
            },
            'optimizer': {
                'mutation_multiplier': 0.5,
                'action_diversity': 0.3,
                'novelty_seeking': 0.1,
                'risk_tolerance': 0.2,
                'exploit_sequences': True,
                'description': 'Efficiency expert - refine known patterns'
            },
            'generalist': {
                'mutation_multiplier': 1.0,
                'action_diversity': 0.6,
                'novelty_seeking': 0.5,
                'risk_tolerance': 0.5,
                'exploit_sequences': False,
                'description': 'Balanced agent - maintain baseline capability'
            },
            'exploiter': {
                'mutation_multiplier': 0.1,
                'action_diversity': 0.0,
                'novelty_seeking': 0.0,
                'risk_tolerance': 0.0,
                'exploit_sequences': True,
                'only_use_sequences': True,
                'prefer_uber_sequences': True,
                'description': 'Pure exploiter - only replays proven sequences and uber-sequences'
            }
        }
    
    def _update_population_distribution(self):
        """
        Adaptive population distribution based on game completion status.
        
        EXPLORATION PHASE (no games fully beaten):
            60% PIONEER - MAXIMUM exploration focus to find first solutions
            10% OPTIMIZER - Minimal refinement of partial solutions
            10% EXPLOITER - Test existing sequences for reliability
            20% GENERALIST - Baseline validation
        
        OPTIMIZATION PHASE (at least one game fully beaten):
            10% PIONEER - Maintain some frontier exploration
            60% OPTIMIZER - Focus on efficiency refinement
            30% GENERALIST - Strong baseline for comparison
        """
        try:
            # Check if ANY games have been completely won (win_detected = TRUE)
            full_wins = self.db.execute_query("""
                SELECT COUNT(*) as win_count
                FROM game_results
                WHERE win_detected = TRUE
            """)
            
            has_full_wins = full_wins and full_wins[0]['win_count'] > 0
            
            if has_full_wins:
                # OPTIMIZATION PHASE: At least one game fully beaten
                self.TARGET_PIONEER_PCT = 0.10
                self.TARGET_OPTIMIZER_PCT = 0.50
                self.TARGET_GENERALIST_PCT = 0.25
                self.TARGET_EXPLOITER_PCT = 0.15  # Higher in optimization phase
                self.phase = "OPTIMIZATION"
                logger.info(f"🎯 OPTIMIZATION PHASE: {full_wins[0]['win_count']} games fully beaten")
                logger.info(f"   Distribution: 10% PIONEER, 50% OPTIMIZER, 25% GENERALIST, 15% EXPLOITER")
            else:
                # EXPLORATION PHASE: No games fully beaten yet - HEAVY PIONEER FOCUS
                self.TARGET_PIONEER_PCT = 0.60
                self.TARGET_OPTIMIZER_PCT = 0.15  # Slightly higher to refine partials
                self.TARGET_GENERALIST_PCT = 0.20
                self.TARGET_EXPLOITER_PCT = 0.05  # CRITICAL FIX: Lower in exploration (fewer sequences to exploit)
                self.phase = "EXPLORATION"
                logger.info(f"🔍 EXPLORATION PHASE: No games fully beaten yet")
                logger.info(f"   Distribution: 60% PIONEER, 15% OPTIMIZER, 20% GENERALIST, 5% EXPLOITER")
                
        except Exception as e:
            # Fallback to exploration phase if query fails
            logger.warning(f"Failed to check game completion status: {e}")
            self.TARGET_PIONEER_PCT = 0.60
            self.TARGET_OPTIMIZER_PCT = 0.15
            self.TARGET_GENERALIST_PCT = 0.20
            self.TARGET_EXPLOITER_PCT = 0.05  # CRITICAL FIX: Lower for exploration fallback
            self.phase = "EXPLORATION"
        
        # Create database table if not exists
        self._initialize_database()
        
        logger.info("[✓] Agent Operating Mode System initialized")
        logger.info(f"   Target distribution: {self.TARGET_PIONEER_PCT*100:.0f}% pioneers, {self.TARGET_OPTIMIZER_PCT*100:.0f}% optimizers, {self.TARGET_GENERALIST_PCT*100:.0f}% generalists, {self.TARGET_EXPLOITER_PCT*100:.0f}% exploiters")
    
    def _initialize_database(self):
        """Create agent_operating_modes table"""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_operating_modes (
                mode_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_id TEXT,
                generation INTEGER NOT NULL,
                assigned_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Mode assignment
                operating_mode TEXT NOT NULL,  -- 'pioneer', 'optimizer', 'generalist'
                mode_reason TEXT NOT NULL,      -- Why this mode was assigned
                
                -- Mode parameters applied
                mutation_multiplier REAL NOT NULL,
                action_diversity REAL NOT NULL,
                novelty_seeking REAL NOT NULL,
                
                -- Performance tracking
                actions_taken INTEGER DEFAULT 0,
                score_achieved REAL DEFAULT 0.0,
                win_achieved BOOLEAN DEFAULT FALSE,
                mode_effectiveness REAL DEFAULT 0.5,  -- How well this mode worked for this agent
                
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)
        
        # Index for fast agent mode lookups
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_mode_agent_gen 
            ON agent_operating_modes(agent_id, generation)
        """)
        
        logger.info("[✓] agent_operating_modes table initialized")
    
    def check_and_update_phase(self) -> bool:
        """
        Check if we should transition from EXPLORATION to OPTIMIZATION phase.
        Called at the start of each generation to adaptively adjust population mix.
        
        Returns:
            True if phase changed, False if stayed the same
        """
        old_phase = getattr(self, 'phase', 'EXPLORATION')
        
        # Re-check game completion status
        try:
            full_wins = self.db.execute_query("""
                SELECT COUNT(*) as win_count
                FROM game_results
                WHERE win_detected = TRUE
            """)
            
            has_full_wins = full_wins and full_wins[0]['win_count'] > 0
            
            if has_full_wins and old_phase == 'EXPLORATION':
                # TRANSITION: First game beaten! Switch to optimization phase
                self.TARGET_PIONEER_PCT = 0.10
                self.TARGET_OPTIMIZER_PCT = 0.60
                self.TARGET_GENERALIST_PCT = 0.30
                self.phase = "OPTIMIZATION"
                
                logger.info(f"\n{'='*80}")
                logger.info(f"🎯 PHASE TRANSITION: EXPLORATION → OPTIMIZATION")
                logger.info(f"{'='*80}")
                logger.info(f"✅ {full_wins[0]['win_count']} games fully beaten!")
                logger.info(f"📊 Old distribution: 70% PIONEER, 10% OPTIMIZER, 20% GENERALIST")
                logger.info(f"📊 New distribution: 10% PIONEER, 60% OPTIMIZER, 30% GENERALIST")
                logger.info(f"   Focus shifting from exploration to efficiency refinement")
                logger.info(f"{'='*80}\n")
                return True
            
            elif not has_full_wins and old_phase == 'OPTIMIZATION':
                # Edge case: Somehow lost all wins? Return to exploration
                self.TARGET_PIONEER_PCT = 0.70
                self.TARGET_OPTIMIZER_PCT = 0.10
                self.TARGET_GENERALIST_PCT = 0.20
                self.phase = "EXPLORATION"
                logger.warning(f"⚠️ PHASE REVERT: OPTIMIZATION → EXPLORATION (no wins found)")
                return True
                
        except Exception as e:
            logger.warning(f"Failed to check phase transition: {e}")
        
        return False
    
    def get_best_mode_for_game(self, agent_id: str, game_id: str) -> Optional[str]:
        """
        Get agent's most effective mode for a specific game based on history.
        
        Returns mode that achieved best score/action efficiency, or None if no history.
        """
        results = self.db.execute_query("""
            SELECT operating_mode, 
                   AVG(score_achieved) as avg_score,
                   AVG(score_achieved / NULLIF(actions_taken, 0)) as avg_efficiency,
                   COUNT(*) as attempts
            FROM agent_operating_modes
            WHERE agent_id = ? AND game_id = ?
            GROUP BY operating_mode
            ORDER BY avg_efficiency DESC, avg_score DESC
            LIMIT 1
        """, (agent_id, game_id))
        
        if results and results[0]['attempts'] >= 2:  # Need at least 2 attempts to trust
            best_mode = results[0]['operating_mode']
            logger.info(f"   Agent {agent_id[:8]} best mode for game {game_id}: {best_mode} "
                       f"(efficiency={results[0]['avg_efficiency']:.3f}, {results[0]['attempts']} attempts)")
            return best_mode
        
        return None
    
    def assign_population_modes(self, generation: int, active_agents: List[str], 
                                game_id: Optional[str] = None) -> Dict[str, str]:
        """
        Assign operating modes to population for this generation.
        
        PERSISTENT MODE MEMORY: If game_id provided and agent has history with that game,
        use their most effective mode. Otherwise maintain 10/60/30 distribution.
        
        Args:
            generation: Current evolution generation
            active_agents: List of active agent IDs
            game_id: Optional game ID for persistent mode lookup
            
        Returns:
            Dict mapping agent_id -> operating_mode ('pioneer', 'optimizer', 'generalist')
        """
        if not active_agents:
            return {}
        
        # Calculate target counts
        total_agents = len(active_agents)
        target_pioneers = max(1, int(total_agents * self.TARGET_PIONEER_PCT))
        target_optimizers = int(total_agents * self.TARGET_OPTIMIZER_PCT)
        target_exploiters = int(total_agents * self.TARGET_EXPLOITER_PCT)
        target_generalists = total_agents - target_pioneers - target_optimizers - target_exploiters
        
        logger.info(f"\n[MODE ASSIGNMENT] Generation {generation}: {total_agents} agents")
        if game_id:
            logger.info(f"   Game: {game_id} (using persistent mode memory)")
        logger.info(f"   Target: {target_pioneers} pioneers, {target_optimizers} optimizers, {target_generalists} generalists, {target_exploiters} exploiters")
        
        # PERSISTENT MODE MEMORY: Check if agents have proven effective modes for this game
        agents_with_memory = {}
        agents_needing_assignment = []
        
        if game_id:
            for agent_id in active_agents:
                best_mode = self.get_best_mode_for_game(agent_id, game_id)
                if best_mode:
                    agents_with_memory[agent_id] = best_mode
                else:
                    agents_needing_assignment.append(agent_id)
            
            logger.info(f"   {len(agents_with_memory)} agents have proven modes for this game")
            logger.info(f"   {len(agents_needing_assignment)} agents need new mode assignment")
        else:
            agents_needing_assignment = active_agents
        
        # Get agent performance history for smart assignment
        agent_stats = self._get_agent_performance_stats(agents_needing_assignment)
        
        # Sort agents by different criteria for role selection
        # Top performers → optimizers (exploit their strengths)
        # Struggling agents → pioneers (need exploration)
        # Middle → generalists (balanced)
        
        agents_by_performance = sorted(
            agents_needing_assignment,
            key=lambda aid: agent_stats.get(aid, {}).get('avg_score', 0.0),
            reverse=True
        )
        
        # Start with agents who have proven modes
        mode_assignments = dict(agents_with_memory)
        assigned_modes = {
            'pioneer': sum(1 for m in agents_with_memory.values() if m == 'pioneer'),
            'optimizer': sum(1 for m in agents_with_memory.values() if m == 'optimizer'),
            'generalist': sum(1 for m in agents_with_memory.values() if m == 'generalist'),
            'exploiter': sum(1 for m in agents_with_memory.values() if m == 'exploiter')
        }
        
        for agent_id in agents_by_performance:
            stats = agent_stats.get(agent_id, {})
            
            # Decision logic: What mode is best for this agent right now?
            
            # TOP PERFORMERS WITH WINNING SEQUENCES → Exploiters (pure exploitation)
            # But only if we're in optimization phase (has_full_wins) or have local wins
            if (assigned_modes['exploiter'] < target_exploiters and
                stats.get('avg_score', 0) > 0.7 and
                stats.get('total_wins', 0) > 0 and
                (self.phase == 'OPTIMIZATION' or stats.get('total_wins', 0) >= 2)):
                mode = 'exploiter'
                reason = f"Top performer (avg_score={stats.get('avg_score', 0):.2f}, wins={stats.get('total_wins', 0)}) - exploit proven sequences"
            
            # HIGH PERFORMERS → Optimizers (refine success)
            elif (assigned_modes['optimizer'] < target_optimizers and
                stats.get('avg_score', 0) > 0.5):
                mode = 'optimizer'
                reason = f"High performer (avg_score={stats.get('avg_score', 0):.2f}) - refine winning strategies"
            
            # LOW PERFORMERS → Pioneers (need breakthrough)
            elif (assigned_modes['pioneer'] < target_pioneers and
                  stats.get('avg_score', 0) < 0.3):
                mode = 'pioneer'
                reason = f"Struggling (avg_score={stats.get('avg_score', 0):.2f}) - needs exploration"
            
            # MIDDLE PERFORMERS → Generalists (flexible)
            elif assigned_modes['generalist'] < target_generalists:
                mode = 'generalist'
                reason = f"Balanced performer (avg_score={stats.get('avg_score', 0):.2f}) - maintain versatility"
            
            # Fill remaining slots (if targets weren't met)
            else:
                # Prioritize: exploiter > optimizer > generalist > pioneer
                if assigned_modes['exploiter'] < target_exploiters:
                    mode = 'exploiter'
                    reason = "Filling exploiter quota"
                elif assigned_modes['optimizer'] < target_optimizers:
                    mode = 'optimizer'
                    reason = "Filling optimizer quota"
                elif assigned_modes['generalist'] < target_generalists:
                    mode = 'generalist'
                    reason = "Filling generalist quota"
                else:
                    mode = 'pioneer'
                    reason = "Filling pioneer quota"
            
            mode_assignments[agent_id] = mode
            assigned_modes[mode] += 1
            
            # Record assignment in database (with game_id if provided)
            self._record_mode_assignment(agent_id, game_id, generation, mode, reason)
        
        # Report final distribution
        logger.info(f"   Assigned: {assigned_modes['pioneer']} pioneers, "
                   f"{assigned_modes['optimizer']} optimizers, "
                   f"{assigned_modes['generalist']} generalists, "
                   f"{assigned_modes['exploiter']} exploiters")
        
        return mode_assignments
    
    def get_mode_parameters(self, agent_id: str, generation: int) -> Dict:
        """
        Get operating mode parameters for agent in this generation.
        
        Returns mode-specific parameters (mutation multiplier, diversity, etc.)
        """
        # Query most recent mode assignment
        result = self.db.execute_query("""
            SELECT operating_mode, mutation_multiplier, action_diversity, novelty_seeking
            FROM agent_operating_modes
            WHERE agent_id = ? AND generation = ?
            ORDER BY assigned_timestamp DESC
            LIMIT 1
        """, (agent_id, generation))
        
        if result:
            mode = result[0]['operating_mode']
            return {
                'mode': mode,
                'mutation_multiplier': result[0]['mutation_multiplier'],
                'action_diversity': result[0]['action_diversity'],
                'novelty_seeking': result[0]['novelty_seeking'],
                **self.MODE_PARAMETERS[mode]
            }
        
        # Fallback: default to generalist if no assignment found
        return {
            'mode': 'generalist',
            **self.MODE_PARAMETERS['generalist']
        }
    
    def _get_agent_performance_stats(self, agent_ids: List[str]) -> Dict[str, Dict]:
        """Get recent performance stats for mode assignment decisions"""
        if not agent_ids:
            return {}
        
        # Build IN clause for SQL
        placeholders = ','.join(['?' for _ in agent_ids])
        
        query = f"""
            SELECT 
                agent_id,
                AVG(final_score) as avg_score,
                COUNT(*) as games_played,
                SUM(CASE WHEN win_achieved THEN 1 ELSE 0 END) as wins,
                AVG(score_efficiency) as avg_efficiency
            FROM agent_arc_performance
            WHERE agent_id IN ({placeholders})
            GROUP BY agent_id
        """
        
        results = self.db.execute_query(query, tuple(agent_ids))
        
        stats = {}
        for row in results:
            stats[row['agent_id']] = {
                'avg_score': row['avg_score'] or 0.0,
                'games_played': row['games_played'] or 0,
                'wins': row['wins'] or 0,
                'avg_efficiency': row['avg_efficiency'] or 0.0
            }
        
        return stats
    
    def _record_mode_assignment(self, agent_id: str, game_id: Optional[str],
                               generation: int, mode: str, reason: str):
        """Record mode assignment to database"""
        import uuid
        
        mode_id = f"mode_{uuid.uuid4().hex[:12]}"
        params = self.MODE_PARAMETERS[mode]
        
        self.db.execute_query("""
            INSERT INTO agent_operating_modes
            (mode_id, agent_id, game_id, generation, operating_mode, mode_reason,
             mutation_multiplier, action_diversity, novelty_seeking)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mode_id, agent_id, game_id, generation, mode, reason,
            params['mutation_multiplier'],
            params['action_diversity'],
            params['novelty_seeking']
        ))
    
    def update_mode_effectiveness(self, agent_id: str, generation: int,
                                 score: float, win: bool, actions: int):
        """Update how effective this mode was for this agent"""
        # Calculate effectiveness: score + win bonus + efficiency
        efficiency = score / max(actions, 1)
        effectiveness = (score * 0.5) + (10.0 if win else 0.0) + (efficiency * 0.5)
        
        self.db.execute_query("""
            UPDATE agent_operating_modes
            SET actions_taken = ?,
                score_achieved = ?,
                win_achieved = ?,
                mode_effectiveness = ?
            WHERE agent_id = ? AND generation = ?
        """, (actions, score, win, effectiveness, agent_id, generation))
    
    def get_population_mode_distribution(self, generation: int) -> Dict[str, int]:
        """Get current distribution of modes in population"""
        results = self.db.execute_query("""
            SELECT operating_mode, COUNT(*) as count
            FROM agent_operating_modes
            WHERE generation = ?
            GROUP BY operating_mode
        """, (generation,))
        
        distribution = {'pioneer': 0, 'optimizer': 0, 'generalist': 0, 'exploiter': 0}
        for row in results:
            distribution[row['operating_mode']] = row['count']
        
        return distribution
