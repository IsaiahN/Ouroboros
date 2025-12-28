import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

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
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import random
import logging
from database_interface import DatabaseInterface

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
        self.PIONEER_MUTATION_MULTIPLIER = 5.0  # 5x exploration
        self.OPTIMIZER_MUTATION_MULTIPLIER = 0.5  # Half mutation
        self.GENERALIST_MUTATION_MULTIPLIER = 1.0  # Normal

        # Mode behavior parameters
        self.MODE_PARAMETERS = {
            "pioneer": {
                "mutation_multiplier": 5.0,
                "action_diversity": 0.95,
                "novelty_seeking": 0.9,
                "risk_tolerance": 0.9,
                "exploit_sequences": False,
                "description": "Breakthrough seeker - maximum exploration",
            },
            "optimizer": {
                "mutation_multiplier": 0.5,
                "action_diversity": 0.3,
                "novelty_seeking": 0.1,
                "risk_tolerance": 0.2,
                "exploit_sequences": True,
                "description": "Efficiency expert - refine known patterns",
            },
            "generalist": {
                "mutation_multiplier": 1.0,
                "action_diversity": 0.6,
                "novelty_seeking": 0.5,
                "risk_tolerance": 0.5,
                "exploit_sequences": False,
                "description": "Balanced agent - maintain baseline capability",
            },
            "exploiter": {
                "mutation_multiplier": 0.1,
                "action_diversity": 0.0,
                "novelty_seeking": 0.0,
                "risk_tolerance": 0.0,
                "exploit_sequences": True,
                "only_use_sequences": True,
                "prefer_uber_sequences": True,
                "description": "Pure exploiter - only replays proven sequences and uber-sequences",
            },
        }

    def _update_population_distribution(self):
        """
        Adaptive population distribution based on game completion status.

        EXPLORATION PHASE (no games fully beaten):
            60% PIONEER - MAXIMUM exploration focus to find first solutions
            15% OPTIMIZER - Refine partial level wins
            20% GENERALIST - Baseline validation
            5% EXPLOITER - Test existing sequences for reliability

        OPTIMIZATION PHASE (at least one game fully beaten):
            10% PIONEER - Maintain some frontier exploration
            50% OPTIMIZER - Focus on efficiency refinement
            25% GENERALIST - Strong baseline for comparison
            15% EXPLOITER - Harvest proven sequences
        """
        try:
            # Check if ANY games have been completely won (win_detected = TRUE)
            full_wins = self.db.execute_query("""
                SELECT COUNT(*) as win_count
                FROM game_results
                WHERE win_detected = TRUE
            """)

            has_full_wins = full_wins and full_wins[0]["win_count"] > 0

            if has_full_wins:
                # OPTIMIZATION PHASE: At least one game fully beaten
                self.TARGET_PIONEER_PCT = 0.10
                self.TARGET_OPTIMIZER_PCT = 0.50
                self.TARGET_GENERALIST_PCT = 0.25
                self.TARGET_EXPLOITER_PCT = 0.15  # Higher in optimization phase
                self.phase = "OPTIMIZATION"
                logger.info(
                    f"[TARGET] OPTIMIZATION PHASE: {full_wins[0]['win_count']} games fully beaten"
                )
                logger.info(
                    f"   Distribution: 10% PIONEER, 50% OPTIMIZER, 25% GENERALIST, 15% EXPLOITER"
                )
            else:
                # EXPLORATION PHASE: No games fully beaten yet - HEAVY PIONEER FOCUS
                self.TARGET_PIONEER_PCT = 0.60
                self.TARGET_OPTIMIZER_PCT = 0.15  # Refine partial level wins
                self.TARGET_GENERALIST_PCT = 0.20
                self.TARGET_EXPLOITER_PCT = 0.05  # Low in exploration (fewer sequences to exploit)
                self.phase = "EXPLORATION"
                logger.info(f"🔍 EXPLORATION PHASE: No games fully beaten yet")
                logger.info(
                    f"   Distribution: 60% PIONEER, 15% OPTIMIZER, 20% GENERALIST, 5% EXPLOITER"
                )

        except Exception as e:
            # Fallback to exploration phase if query fails
            logger.warning(f"Failed to check game completion status: {e}")
            self.TARGET_PIONEER_PCT = 0.60
            self.TARGET_OPTIMIZER_PCT = 0.15
            self.TARGET_GENERALIST_PCT = 0.20
            self.TARGET_EXPLOITER_PCT = (
                0.05  # CRITICAL FIX: Lower for exploration fallback
            )
            self.phase = "EXPLORATION"

        # Create database table if not exists
        self._initialize_database()

        logger.info("[✓] Agent Operating Mode System initialized")
        logger.info(
            f"   Target distribution: {self.TARGET_PIONEER_PCT * 100:.0f}% pioneers, {self.TARGET_OPTIMIZER_PCT * 100:.0f}% optimizers, {self.TARGET_GENERALIST_PCT * 100:.0f}% generalists, {self.TARGET_EXPLOITER_PCT * 100:.0f}% exploiters"
        )

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
        old_phase = getattr(self, "phase", "EXPLORATION")

        # Re-check game completion status
        try:
            full_wins = self.db.execute_query("""
                SELECT COUNT(*) as win_count
                FROM game_results
                WHERE win_detected = TRUE
            """)

            has_full_wins = full_wins and full_wins[0]["win_count"] > 0

            if has_full_wins and old_phase == "EXPLORATION":
                # TRANSITION: First game beaten! Switch to optimization phase
                self.TARGET_PIONEER_PCT = 0.10
                self.TARGET_OPTIMIZER_PCT = 0.60
                self.TARGET_GENERALIST_PCT = 0.30
                self.phase = "OPTIMIZATION"

                logger.info(f"\n{'=' * 80}")
                logger.info(f"[TARGET] PHASE TRANSITION: EXPLORATION → OPTIMIZATION")
                logger.info(f"{'=' * 80}")
                logger.info(f"[OK] {full_wins[0]['win_count']} games fully beaten!")
                logger.info(
                    f"[STATS] Old distribution: 70% PIONEER, 10% OPTIMIZER, 20% GENERALIST"
                )
                logger.info(
                    f"[STATS] New distribution: 10% PIONEER, 60% OPTIMIZER, 30% GENERALIST"
                )
                logger.info(
                    f"   Focus shifting from exploration to efficiency refinement"
                )
                logger.info(f"{'=' * 80}\n")
                return True

            elif not has_full_wins and old_phase == "OPTIMIZATION":
                # Edge case: Somehow lost all wins? Return to exploration
                self.TARGET_PIONEER_PCT = 0.70
                self.TARGET_OPTIMIZER_PCT = 0.10
                self.TARGET_GENERALIST_PCT = 0.20
                self.phase = "EXPLORATION"
                logger.warning(
                    f"[WARN] PHASE REVERT: OPTIMIZATION → EXPLORATION (no wins found)"
                )
                return True

        except Exception as e:
            logger.warning(f"Failed to check phase transition: {e}")

        return False

    def get_best_mode_for_game(self, agent_id: str, game_id: str) -> Optional[str]:
        """
        Get agent's most effective mode for a specific game based on history.

        Returns mode that achieved best score/action efficiency, or None if no history.
        """
        results = self.db.execute_query(
            """
            SELECT operating_mode, 
                   AVG(score_achieved) as avg_score,
                   AVG(score_achieved / NULLIF(actions_taken, 0)) as avg_efficiency,
                   COUNT(*) as attempts
            FROM agent_operating_modes
            WHERE agent_id = ? AND game_id = ?
            GROUP BY operating_mode
            ORDER BY avg_efficiency DESC, avg_score DESC
            LIMIT 1
        """,
            (agent_id, game_id),
        )

        if results and results[0]["attempts"] >= 2:  # Need at least 2 attempts to trust
            best_mode = results[0]["operating_mode"]
            efficiency = results[0].get('avg_efficiency')
            efficiency_str = f"{efficiency:.3f}" if efficiency is not None else "N/A"
            logger.info(
                f"   Agent {agent_id[:8]} best mode for game {game_id}: {best_mode} "
                f"(efficiency={efficiency_str}, {results[0]['attempts']} attempts)"
            )
            return best_mode

        return None

    def assign_population_modes(
        self, generation: int, active_agents: List[str], game_id: Optional[str] = None
    ) -> Dict[str, str]:
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
        target_generalists = (
            total_agents - target_pioneers - target_optimizers - target_exploiters
        )

        logger.info(
            f"\n[MODE ASSIGNMENT] Generation {generation}: {total_agents} agents"
        )
        if game_id:
            logger.info(f"   Game: {game_id} (using persistent mode memory)")
        logger.info(
            f"   Target: {target_pioneers} pioneers, {target_optimizers} optimizers, {target_generalists} generalists, {target_exploiters} exploiters"
        )

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

            logger.info(
                f"   {len(agents_with_memory)} agents have proven modes for this game"
            )
            logger.info(
                f"   {len(agents_needing_assignment)} agents need new mode assignment"
            )
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
            key=lambda aid: agent_stats.get(aid, {}).get("avg_score", 0.0),
            reverse=True,
        )

        # Start with agents who have proven modes
        mode_assignments = dict(agents_with_memory)
        assigned_modes = {
            "pioneer": sum(1 for m in agents_with_memory.values() if m == "pioneer"),
            "optimizer": sum(
                1 for m in agents_with_memory.values() if m == "optimizer"
            ),
            "generalist": sum(
                1 for m in agents_with_memory.values() if m == "generalist"
            ),
            "exploiter": sum(
                1 for m in agents_with_memory.values() if m == "exploiter"
            ),
        }

        for agent_id in agents_by_performance:
            stats = agent_stats.get(agent_id, {})

            # Decision logic: What mode is best for this agent right now?

            # TOP PERFORMERS WITH WINNING SEQUENCES → Exploiters (pure exploitation)
            # But only if we're in optimization phase (has_full_wins) or have local wins
            if (
                assigned_modes["exploiter"] < target_exploiters
                and stats.get("avg_score", 0) > 0.7
                and stats.get("total_wins", 0) > 0
                and (self.phase == "OPTIMIZATION" or stats.get("total_wins", 0) >= 2)
            ):
                mode = "exploiter"
                reason = f"Top performer (avg_score={stats.get('avg_score', 0):.2f}, wins={stats.get('total_wins', 0)}) - exploit proven sequences"

            # HIGH PERFORMERS → Optimizers (refine success)
            # In EXPLORATION phase: only optimize if agent has proven wins (not just score)
            # In OPTIMIZATION phase: any high scorer can optimize
            elif (
                assigned_modes["optimizer"] < target_optimizers
                and stats.get("avg_score", 0) > 0.6
                and (self.phase == "OPTIMIZATION" or stats.get("total_wins", 0) > 0)
            ):
                mode = "optimizer"
                reason = f"High performer (avg_score={stats.get('avg_score', 0):.2f}, wins={stats.get('total_wins', 0)}) - refine winning strategies"

            # LOW PERFORMERS → Pioneers (need breakthrough)
            elif (
                assigned_modes["pioneer"] < target_pioneers
                and stats.get("avg_score", 0) < 0.45
            ):
                mode = "pioneer"
                reason = f"Struggling (avg_score={stats.get('avg_score', 0):.2f}) - needs exploration"

            # MIDDLE PERFORMERS → Generalists (flexible) OR Pioneers (if quota unfilled)
            # In EXPLORATION phase: prioritize pioneer quota over generalist
            elif self.phase == "EXPLORATION" and assigned_modes["pioneer"] < target_pioneers:
                mode = "pioneer"
                reason = f"EXPLORATION phase - filling pioneer quota (avg_score={stats.get('avg_score', 0):.2f})"
            elif assigned_modes["generalist"] < target_generalists:
                mode = "generalist"
                reason = f"Balanced performer (avg_score={stats.get('avg_score', 0):.2f}) - maintain versatility"

            # Fill remaining slots (if targets weren't met)
            else:
                # Prioritize based on phase
                if self.phase == "EXPLORATION":
                    # EXPLORATION: pioneer > generalist > optimizer > exploiter
                    if assigned_modes["pioneer"] < target_pioneers:
                        mode = "pioneer"
                        reason = "Filling pioneer quota (EXPLORATION priority)"
                    elif assigned_modes["generalist"] < target_generalists:
                        mode = "generalist"
                        reason = "Filling generalist quota"
                    elif assigned_modes["optimizer"] < target_optimizers:
                        mode = "optimizer"
                        reason = "Filling optimizer quota"
                    else:
                        mode = "exploiter"
                        reason = "Filling exploiter quota"
                else:
                    # OPTIMIZATION: optimizer > exploiter > generalist > pioneer
                    if assigned_modes["optimizer"] < target_optimizers:
                        mode = "optimizer"
                        reason = "Filling optimizer quota (OPTIMIZATION priority)"
                    elif assigned_modes["exploiter"] < target_exploiters:
                        mode = "exploiter"
                        reason = "Filling exploiter quota"
                    elif assigned_modes["generalist"] < target_generalists:
                        mode = "generalist"
                        reason = "Filling generalist quota"
                    else:
                        mode = "pioneer"
                        reason = "Filling pioneer quota"

            mode_assignments[agent_id] = mode
            assigned_modes[mode] += 1

            # Record assignment in database (with game_id if provided)
            self._record_mode_assignment(agent_id, game_id, generation, mode, reason)

        # Report final distribution
        logger.info(
            f"   Assigned: {assigned_modes['pioneer']} pioneers, "
            f"{assigned_modes['optimizer']} optimizers, "
            f"{assigned_modes['generalist']} generalists, "
            f"{assigned_modes['exploiter']} exploiters"
        )

        return mode_assignments

    def get_mode_parameters(self, agent_id: str, generation: int) -> Dict:
        """
        Get operating mode parameters for agent in this generation.

        Returns mode-specific parameters (mutation multiplier, diversity, etc.)
        """
        # Query most recent mode assignment
        result = self.db.execute_query(
            """
            SELECT operating_mode, mutation_multiplier, action_diversity, novelty_seeking
            FROM agent_operating_modes
            WHERE agent_id = ? AND generation = ?
            ORDER BY assigned_timestamp DESC
            LIMIT 1
        """,
            (agent_id, generation),
        )

        if result:
            mode = result[0]["operating_mode"]
            return {
                "mode": mode,
                "mutation_multiplier": result[0]["mutation_multiplier"],
                "action_diversity": result[0]["action_diversity"],
                "novelty_seeking": result[0]["novelty_seeking"],
                **self.MODE_PARAMETERS[mode],
            }

        # Fallback: default to generalist if no assignment found
        return {"mode": "generalist", **self.MODE_PARAMETERS["generalist"]}

    def _get_agent_performance_stats(self, agent_ids: List[str]) -> Dict[str, Dict]:
        """Get recent performance stats for mode assignment decisions"""
        if not agent_ids:
            return {}

        # Build IN clause for SQL
        placeholders = ",".join(["?" for _ in agent_ids])

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
            stats[row["agent_id"]] = {
                "avg_score": row["avg_score"] or 0.0,
                "games_played": row["games_played"] or 0,
                "wins": row["wins"] or 0,
                "avg_efficiency": row["avg_efficiency"] or 0.0,
            }

        return stats

    def _record_mode_assignment(
        self,
        agent_id: str,
        game_id: Optional[str],
        generation: int,
        mode: str,
        reason: str,
    ):
        """Record mode assignment to database and update social_rule_adherence"""
        import uuid

        mode_id = f"mode_{uuid.uuid4().hex[:12]}"
        params = self.MODE_PARAMETERS[mode]
        
        # FIX: Set social_rule_adherence based on role per Master Ruleset
        # Exploiters get 50/50 split: sociopathic (0.0-0.3) vs social (0.7-1.0)
        # All other roles get moderate social adherence (0.5-0.8)
        if mode == 'exploiter':
            # 50% sociopathic, 50% social per Master Ruleset
            if random.random() < 0.5:
                social_rule_adherence = random.uniform(0.0, 0.3)  # Sociopathic
            else:
                social_rule_adherence = random.uniform(0.7, 1.0)  # Social
        elif mode == 'pioneer':
            # Pioneers: moderate-high (explore but can use network hints)
            social_rule_adherence = random.uniform(0.4, 0.7)
        elif mode == 'optimizer':
            # Optimizers: higher social (rely on proven sequences)
            social_rule_adherence = random.uniform(0.6, 0.9)
        else:  # generalist
            # Generalists: balanced social adherence
            social_rule_adherence = random.uniform(0.5, 0.8)
        
        # Update agent's social_rule_adherence in agents table
        self.db.execute_query(
            "UPDATE agents SET social_rule_adherence = ? WHERE agent_id = ?",
            (social_rule_adherence, agent_id)
        )

        # Role Fairness: Capture initial w_B (self_network_bias) for growth-based evaluation
        # This snapshot records where the agent started when assigned this role
        initial_w_B = 0.5  # Default if not found
        w_B_result = self.db.execute_query(
            "SELECT self_network_bias FROM agents WHERE agent_id = ?",
            (agent_id,)
        )
        if w_B_result and len(w_B_result) > 0 and w_B_result[0].get("self_network_bias") is not None:
            initial_w_B = w_B_result[0]["self_network_bias"]

        self.db.execute_query(
            """
            INSERT INTO agent_operating_modes
            (mode_id, agent_id, game_id, generation, operating_mode, mode_reason,
             mutation_multiplier, action_diversity, novelty_seeking,
             initial_w_B_for_role, current_w_B, progress_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                mode_id,
                agent_id,
                game_id,
                generation,
                mode,
                reason,
                params["mutation_multiplier"],
                params["action_diversity"],
                params["novelty_seeking"],
                initial_w_B,       # Snapshot of w_B when role assigned
                initial_w_B,       # current_w_B starts same as initial
                0.0,               # progress_score starts at 0
            ),
        )

    def update_mode_effectiveness(
        self, agent_id: str, generation: int, score: float, win: bool, actions: int
    ):
        """Update how effective this mode was for this agent"""
        # Calculate effectiveness: score + win bonus + efficiency
        efficiency = score / max(actions, 1)
        effectiveness = (score * 0.5) + (10.0 if win else 0.0) + (efficiency * 0.5)

        self.db.execute_query(
            """
            UPDATE agent_operating_modes
            SET actions_taken = ?,
                score_achieved = ?,
                win_achieved = ?,
                mode_effectiveness = ?
            WHERE agent_id = ? AND generation = ?
        """,
            (actions, score, win, effectiveness, agent_id, generation),
        )

    def update_agent_w_B_progress(self, agent_id: str, generation: int):
        """
        Update agent's current_w_B and progress_score for Role Fairness tracking.
        
        CRITICAL: This updates the agent_operating_modes table with current w_B
        from the agents table, and calculates progress since role assignment.
        
        This should be called after gameplay to track growth-based evaluation.
        
        Args:
            agent_id: Agent to update
            generation: Current generation
        """
        # Get current w_B from agents table
        agent = self.db.execute_query("""
            SELECT self_network_bias FROM agents WHERE agent_id = ?
        """, (agent_id,))
        
        if not agent or len(agent) == 0:
            return
        
        current_w_B = agent[0].get('self_network_bias', 0.5) or 0.5
        
        # Get initial_w_B from the mode assignment
        mode_info = self.db.execute_query("""
            SELECT initial_w_B_for_role FROM agent_operating_modes
            WHERE agent_id = ? AND generation = ?
            ORDER BY created_at DESC LIMIT 1
        """, (agent_id, generation))
        
        if not mode_info or len(mode_info) == 0:
            return
        
        initial_w_B = mode_info[0].get('initial_w_B_for_role', 0.5) or 0.5
        
        # Calculate progress score: growth from initial position
        progress_score = current_w_B - initial_w_B
        
        # Update the agent_operating_modes record
        self.db.execute_query("""
            UPDATE agent_operating_modes
            SET current_w_B = ?,
                progress_score = ?
            WHERE agent_id = ? AND generation = ?
        """, (current_w_B, progress_score, agent_id, generation))
        
        # Log significant progress (positive or negative)
        if abs(progress_score) > 0.1:
            direction = "grew" if progress_score > 0 else "regressed"
            logger.info(f"[W_B PROGRESS] Agent {agent_id[:8]} {direction}: "
                       f"{initial_w_B:.2f} -> {current_w_B:.2f} (delta={progress_score:+.2f})")

    def get_population_mode_distribution(self, generation: int) -> Dict[str, int]:
        """Get current distribution of modes in population"""
        results = self.db.execute_query(
            """
            SELECT operating_mode, COUNT(*) as count
            FROM agent_operating_modes
            WHERE generation = ?
            GROUP BY operating_mode
        """,
            (generation,),
        )

        distribution = {"pioneer": 0, "optimizer": 0, "generalist": 0, "exploiter": 0}
        for row in results:
            distribution[row["operating_mode"]] = row["count"]

        return distribution

    # =========================================================================
    # NEW: Role Permission & Frontier Detection Logic (Immediate Phase Priority)
    # =========================================================================

    def is_frontier_level(self, game_id: str, level_number: int) -> bool:
        """
        Check if a level is a 'frontier' level (unbeaten by the network).

        Args:
            game_id: Game ID
            level_number: Level number (1-based)

        Returns:
            True if level has NEVER been beaten by ANY agent
        """
        # Check if any winning sequence exists for this level
        results = self.db.execute_query(
            """
            SELECT COUNT(*) as count
            FROM winning_sequences
            WHERE game_id = ? AND level_number >= ?
        """,
            (game_id, level_number),
        )

        # If count is 0, no one has beaten this level (or higher) -> It's the frontier
        return results[0]["count"] == 0

    def can_agent_work_on_game(
        self, agent_id: str, game_id: str, level_number: int, mode: str
    ) -> Tuple[bool, str]:
        """
        Check if agent is allowed to work on this game/level based on their role.

        Args:
            agent_id: Agent ID
            game_id: Game ID
            level_number: Current level number
            mode: Agent's operating mode

        Returns:
            (allowed, reason) tuple
        """
        # PIONEER: Should focus on frontier, but allowed to replay to reach it
        if mode == "pioneer":
            # Pioneers are always allowed, but their behavior changes (see get_pioneer_behavior)
            return True, "Pioneers allowed everywhere (behavior adapts)"

        # OPTIMIZER: ONLY work on games that have been beaten (at least partially)
        elif mode == "optimizer":
            # Check if this game has ANY winning sequences
            results = self.db.execute_query(
                """
                SELECT COUNT(*) as count
                FROM winning_sequences
                WHERE game_id = ?
            """,
                (game_id,),
            )

            if results[0]["count"] > 0:
                return True, "Optimizer allowed: Game has known solutions to refine"
            else:
                return False, "Optimizer denied: No known solutions to optimize"

        # EXPLOITER: ONLY work if proven sequence exists for this SPECIFIC level
        elif mode == "exploiter":
            results = self.db.execute_query(
                """
                SELECT COUNT(*) as count
                FROM winning_sequences
                WHERE game_id = ? AND level_number >= ?
            """,
                (game_id, level_number),
            )

            if results[0]["count"] > 0:
                return True, "Exploiter allowed: Proven sequence exists"
            else:
                return False, "Exploiter denied: No proven sequence for this level"

        # GENERALIST: Allowed everywhere
        return True, "Generalist allowed everywhere"

    def get_pioneer_behavior_for_level(self, game_id: str, level_number: int) -> str:
        """
        Determine Pioneer behavior for a specific level.

        Returns:
            'explore': This is the frontier, use high mutation/exploration
            'replay': This is beaten territory, replay efficiently to reach frontier
        """
        if self.is_frontier_level(game_id, level_number):
            return "explore"
        else:
            # User Decision: Option A (Act like Generalist/Replay exactly)
            return "replay"

    # =========================================================================
    # ROLE SELF-DETERMINATION SYSTEM
    # =========================================================================
    # Agents can self-determine their roles based on:
    # 1. Performance history per role (efficiency, win rate)
    # 2. Semantic feedback (frustration, satisfaction from sensation engine)
    # 3. Network contribution (sequences discovered)
    # 
    # Agents start with assigned roles, but can:
    # - Develop a preferred_role based on fit scores
    # - Lock into a role when they find a good fit (role_locked=True)
    # - Request role changes (with cooldown)
    # =========================================================================

    def get_agent_role(self, agent_id: str, generation: int) -> str:
        """
        Get agent's role for this generation - respects self-determination.
        
        Priority:
        1. Locked role (agent found their niche)
        2. Preferred role (agent wants to try this, if capacity allows)
        3. Assigned role (population quota fallback)
        
        Args:
            agent_id: Agent ID
            generation: Current generation
            
        Returns:
            Role string ('pioneer', 'optimizer', 'generalist', 'exploiter')
        """
        # Get agent's self-determination state
        agent = self.db.execute_query("""
            SELECT preferred_role, role_locked, role_confidence, 
                   last_role_switch_gen, role_switch_cooldown
            FROM agents WHERE agent_id = ?
        """, (agent_id,))
        
        if not agent:
            return 'generalist'  # Fallback
        
        agent_data = agent[0]
        
        # 1. Locked agents stay in their role (found their niche)
        if agent_data.get('role_locked') and agent_data.get('preferred_role'):
            logger.debug(f"Agent {agent_id[:8]} locked into {agent_data['preferred_role']}")
            return agent_data['preferred_role']
        
        # 2. Agent has a preference and cooldown is over
        if agent_data.get('preferred_role'):
            cooldown = agent_data.get('role_switch_cooldown', 2)
            last_switch = agent_data.get('last_role_switch_gen', 0)
            
            if generation - last_switch >= cooldown:
                # Check if role has capacity (soft limit)
                if self._role_has_capacity(agent_data['preferred_role'], generation):
                    return agent_data['preferred_role']
                # High-confidence agents can overflow
                elif agent_data.get('role_confidence', 0) > 0.8:
                    logger.info(f"Agent {agent_id[:8]} overflowing into {agent_data['preferred_role']} (high confidence)")
                    return agent_data['preferred_role']
        
        # 3. Fall back to last assigned role or generalist
        last_mode = self.db.execute_query("""
            SELECT operating_mode FROM agent_operating_modes
            WHERE agent_id = ? ORDER BY generation DESC LIMIT 1
        """, (agent_id,))
        
        if last_mode:
            return last_mode[0]['operating_mode']
        
        return 'generalist'

    def _role_has_capacity(self, role: str, generation: int) -> bool:
        """Check if a role has capacity (below target percentage)."""
        # Get current distribution
        distribution = self.get_population_mode_distribution(generation)
        total = sum(distribution.values())
        
        if total == 0:
            return True
        
        current_pct = distribution.get(role, 0) / total
        
        # Get target percentage for this role
        target_pcts = {
            'pioneer': self.TARGET_PIONEER_PCT,
            'optimizer': self.TARGET_OPTIMIZER_PCT,
            'generalist': self.TARGET_GENERALIST_PCT,
            'exploiter': self.TARGET_EXPLOITER_PCT
        }
        
        target = target_pcts.get(role, 0.25)
        
        # Allow 10% overflow above target
        return current_pct < (target * 1.1)

    def get_needed_role_for_new_agent(self, generation: int = 0) -> str:
        """
        Get the role most needed for a new agent based on population distribution.
        Called when creating new agents to ensure balanced role distribution.
        
        Args:
            generation: Current generation (for distribution lookup)
            
        Returns:
            Role string ('pioneer', 'optimizer', 'generalist', 'exploiter')
        """
        # Get current distribution
        distribution = self.get_population_mode_distribution(generation)
        total = sum(distribution.values()) or 1
        
        # Calculate current percentages
        current_pcts = {role: count / total for role, count in distribution.items()}
        
        # Get target percentages
        targets = {
            'pioneer': self.TARGET_PIONEER_PCT,
            'optimizer': self.TARGET_OPTIMIZER_PCT,
            'generalist': self.TARGET_GENERALIST_PCT,
            'exploiter': self.TARGET_EXPLOITER_PCT
        }
        
        # Find role most below target (largest deficit)
        deficits = {role: targets[role] - current_pcts.get(role, 0) 
                    for role in targets}
        
        needed_role = max(deficits, key=deficits.get)
        logger.debug(f"Population needs more {needed_role}s (deficit: {deficits[needed_role]:.2%})")
        
        return needed_role

    def update_role_fit_after_game(self, agent_id: str, role: str, game_result: Dict) -> None:
        """
        Update agent's fit score for their current role after each game.
        Called automatically after every game to track role effectiveness.
        
        Args:
            agent_id: Agent ID
            role: Role played during this game
            game_result: Dict with final_score, win, actions_taken, frustration_level, etc.
        """
        # Get or create role performance record
        perf = self.db.execute_query("""
            SELECT * FROM agent_role_performance WHERE agent_id = ? AND role = ?
        """, (agent_id, role))
        
        if perf:
            perf = dict(perf[0])
        else:
            # Create new record
            perf = {
                'agent_id': agent_id,
                'role': role,
                'games_played': 0,
                'total_score': 0.0,
                'total_wins': 0,
                'total_actions': 0,
                'sequences_discovered': 0,
                'avg_frustration': 0.5,
                'avg_satisfaction': 0.5,
                'role_fit_score': 0.0,
                'consecutive_good_generations': 0
            }
        
        # Update metrics
        perf['games_played'] += 1
        perf['total_score'] += game_result.get('final_score', 0)
        perf['total_wins'] += 1 if game_result.get('win') else 0
        perf['total_actions'] += game_result.get('actions_taken', 0)
        
        # Track sequence discoveries
        if game_result.get('learned_sequence_id'):
            perf['sequences_discovered'] += 1
        
        # Semantic feedback from sensation engine (exponential moving average)
        if 'frustration_level' in game_result:
            perf['avg_frustration'] = (perf['avg_frustration'] * 0.9 + 
                                       game_result['frustration_level'] * 0.1)
        
        if 'satisfaction_level' in game_result:
            perf['avg_satisfaction'] = (perf['avg_satisfaction'] * 0.9 + 
                                        game_result['satisfaction_level'] * 0.1)
        
        # Calculate composite fit score
        games = max(perf['games_played'], 1)
        actions = max(perf['total_actions'], 1)
        
        efficiency = perf['total_score'] / actions  # Score per action
        win_rate = perf['total_wins'] / games
        discovery_rate = perf['sequences_discovered'] / games
        semantic_quality = (1.0 - perf['avg_frustration']) * perf['avg_satisfaction']
        
        # Weighted composite - different roles value different things
        if role == 'pioneer':
            # Pioneers value discovery and exploration
            perf['role_fit_score'] = (
                discovery_rate * 0.4 +      # Pioneers find new things
                semantic_quality * 0.3 +     # Not frustrated by exploration
                efficiency * 0.2 +           # Some efficiency matters
                win_rate * 0.1               # Wins less important for pioneers
            )
        elif role == 'optimizer':
            # Optimizers value efficiency
            perf['role_fit_score'] = (
                efficiency * 0.5 +           # Efficiency is key
                win_rate * 0.3 +             # Should win often
                semantic_quality * 0.15 +    # Satisfaction from refinement
                discovery_rate * 0.05        # Some optimization discoveries
            )
        elif role == 'exploiter':
            # Exploiters value consistent wins with minimal effort
            perf['role_fit_score'] = (
                win_rate * 0.5 +             # Must win consistently
                efficiency * 0.3 +           # Efficient execution
                semantic_quality * 0.2       # Satisfaction from harvesting
            )
        else:  # generalist
            # Generalists are balanced
            perf['role_fit_score'] = (
                efficiency * 0.3 +
                win_rate * 0.3 +
                semantic_quality * 0.2 +
                discovery_rate * 0.2
            )
        
        # Save updated performance
        self.db.execute_query("""
            INSERT OR REPLACE INTO agent_role_performance
            (agent_id, role, games_played, total_score, total_wins, total_actions,
             sequences_discovered, avg_frustration, avg_satisfaction, role_fit_score,
             consecutive_good_generations, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            agent_id, role, perf['games_played'], perf['total_score'],
            perf['total_wins'], perf['total_actions'], perf['sequences_discovered'],
            perf['avg_frustration'], perf['avg_satisfaction'], perf['role_fit_score'],
            perf.get('consecutive_good_generations', 0)
        ))
        
        # Check for role preference update
        self._update_role_preference(agent_id)

    def _update_role_preference(self, agent_id: str) -> None:
        """
        Update agent's preferred role based on fit scores across all roles.
        Called after each game to potentially update preference.
        """
        # Get all role performances for this agent
        performances = self.db.execute_query("""
            SELECT role, role_fit_score, games_played, consecutive_good_generations
            FROM agent_role_performance
            WHERE agent_id = ?
            ORDER BY role_fit_score DESC
        """, (agent_id,))
        
        if not performances or len(performances) == 0:
            return
        
        # Need at least 5 games in a role to consider it
        valid_performances = [p for p in performances if p['games_played'] >= 5]
        
        if not valid_performances:
            return
        
        best = valid_performances[0]
        best_role = best['role']
        best_score = best['role_fit_score']
        
        # Get second best for comparison
        second_best_score = 0.0
        if len(valid_performances) > 1:
            second_best_score = valid_performances[1]['role_fit_score']
        
        # Update preferred role if clearly better (>0.1 difference)
        if best_score > second_best_score + 0.1:
            self.db.execute_query("""
                UPDATE agents SET 
                    preferred_role = ?,
                    role_confidence = ?
                WHERE agent_id = ?
            """, (best_role, best_score, agent_id))
            
            logger.debug(f"Agent {agent_id[:8]} prefers {best_role} (fit={best_score:.2f})")
        
        # Check for role lock (found niche)
        self._check_role_lock(agent_id, best_role, best_score, second_best_score)

    def _check_role_lock(self, agent_id: str, best_role: str, 
                         best_score: float, second_best_score: float) -> None:
        """
        Check if agent should lock into their best role.
        
        Lock criteria:
        - Played at least 15 games in preferred role
        - Fit score > 0.65 
        - Fit score significantly better than second best (>0.15 difference)
        """
        perf = self.db.execute_query("""
            SELECT games_played, consecutive_good_generations
            FROM agent_role_performance
            WHERE agent_id = ? AND role = ?
        """, (agent_id, best_role))
        
        if not perf:
            return
        
        games_in_role = perf[0]['games_played']
        consecutive_good = perf[0].get('consecutive_good_generations', 0)
        
        # Lock conditions
        should_lock = (
            games_in_role >= 15 and
            best_score > 0.65 and
            best_score > second_best_score + 0.15
        )
        
        if should_lock:
            # Get current generation
            gen_result = self.db.execute_query("""
                SELECT MAX(generation) as gen FROM agent_operating_modes WHERE agent_id = ?
            """, (agent_id,))
            current_gen = gen_result[0]['gen'] if gen_result and gen_result[0]['gen'] else 0
            
            self.db.execute_query("""
                UPDATE agents SET 
                    preferred_role = ?,
                    role_locked = TRUE,
                    role_lock_generation = ?,
                    role_confidence = ?
                WHERE agent_id = ?
            """, (best_role, current_gen, best_score, agent_id))
            
            logger.info(f"[ROLE LOCK] Agent {agent_id[:8]} locked into {best_role} "
                       f"(fit={best_score:.2f}, games={games_in_role})")

    def attempt_soft_role_transition(self, agent_id: str, desired_role: str,
                                      generation: int) -> Tuple[bool, str, float]:
        """
        Attempt a SOFT role transition per Role Fairness Protocol.
        
        CRITICAL: This is about ATP (metabolic), NOT prestige (social).
        Agents are always ALLOWED to try transitions (voluntary choice preserved).
        Success is probabilistic based on fit score.
        Failed transitions incur ATP "learning tax" (10% reduction).
        
        Philosophy: "Fair but free, incentivized but not coerced"
        
        Args:
            agent_id: Agent ID
            desired_role: Role agent wants to switch to
            generation: Current generation
            
        Returns:
            (success, reason, atp_cost) tuple
            - success: Whether transition was successful
            - reason: Explanation
            - atp_cost: ATP learning tax (0.0 if success, 0.1 if failure)
        """
        import uuid
        
        # Get agent's current role and w_B
        current_role_info = self.db.execute_query("""
            SELECT operating_mode, initial_w_B_for_role
            FROM agent_operating_modes
            WHERE agent_id = ? AND generation = ?
            ORDER BY created_at DESC LIMIT 1
        """, (agent_id, generation))
        
        current_role = 'generalist'
        if current_role_info and len(current_role_info) > 0:
            current_role = current_role_info[0].get('operating_mode', 'generalist')
        
        # Check if already in desired role
        if current_role == desired_role:
            return True, "Already in requested role", 0.0
        
        # Check if agent is locked (still allow attempt but lower success)
        agent = self.db.execute_query("""
            SELECT role_locked, last_role_switch_gen, role_switch_cooldown, self_network_bias
            FROM agents WHERE agent_id = ?
        """, (agent_id,))
        
        if not agent:
            return False, "Agent not found", 0.0
        
        agent_data = agent[0]
        is_locked = agent_data.get('role_locked', False)
        current_w_B = agent_data.get('self_network_bias', 0.5) or 0.5
        
        # Check cooldown (soft enforcement - reduces success probability)
        cooldown = agent_data.get('role_switch_cooldown', 2)
        last_switch = agent_data.get('last_role_switch_gen', 0) or 0
        cooldown_penalty = 0.0
        if generation - last_switch < cooldown:
            cooldown_penalty = 0.3  # 30% success penalty for cooldown violation
        
        # Get agent's fit score for desired role
        fit_result = self.db.execute_query("""
            SELECT role_fit_score FROM agent_role_performance
            WHERE agent_id = ? AND role = ?
        """, (agent_id, desired_role))
        
        fit_score = fit_result[0]['role_fit_score'] if fit_result else 0.3
        
        # Calculate success probability
        # Base: fit_score (0.0 to 1.0)
        # Minus: cooldown penalty (0.0 or 0.3)
        # Minus: lock penalty (0.0 or 0.4 if locked)
        lock_penalty = 0.4 if is_locked else 0.0
        success_probability = max(0.1, fit_score - cooldown_penalty - lock_penalty)
        
        # Roll for success
        roll = random.random()
        was_successful = roll < success_probability
        
        # Record the transition attempt
        transition_id = f"trans_{uuid.uuid4().hex[:12]}"
        atp_cost = 0.0 if was_successful else 0.1  # 10% ATP learning tax on failure
        
        self.db.execute_query("""
            INSERT INTO role_transition_attempts
            (transition_id, agent_id, from_role, to_role, success_probability,
             was_successful, atp_cost, generation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (transition_id, agent_id, current_role, desired_role,
              success_probability, was_successful, atp_cost, generation))
        
        if was_successful:
            # Apply the transition
            self.db.execute_query("""
                UPDATE agents SET 
                    preferred_role = ?,
                    last_role_switch_gen = ?
                WHERE agent_id = ?
            """, (desired_role, generation, agent_id))
            
            # Record new mode assignment with fresh w_B snapshot
            self._record_mode_assignment(
                agent_id=agent_id,
                game_id='role_transition',  # Special marker
                generation=generation,
                mode=desired_role,
                reason=f"Soft transition from {current_role} (prob={success_probability:.2f})"
            )
            
            logger.info(f"[SOFT TRANSITION] Agent {agent_id[:8]}: {current_role} -> {desired_role} "
                       f"(success, prob={success_probability:.2f})")
            return True, f"Transition successful (prob={success_probability:.2f})", 0.0
        else:
            logger.info(f"[SOFT TRANSITION] Agent {agent_id[:8]}: {current_role} -> {desired_role} "
                       f"(failed, prob={success_probability:.2f}, tax=10%)")
            return False, f"Transition failed (prob={success_probability:.2f}), 10% ATP learning tax", atp_cost

    def request_role_change(self, agent_id: str, desired_role: str, 
                           generation: int) -> Tuple[bool, str]:
        """
        Agent requests to change role. Evaluated based on:
        - Cooldown period (2 generations)
        - Role capacity
        - Agent's fit score for desired role
        
        Args:
            agent_id: Agent ID
            desired_role: Role agent wants to switch to
            generation: Current generation
            
        Returns:
            (approved, reason) tuple
        """
        # Check if agent is locked
        agent = self.db.execute_query("""
            SELECT role_locked, last_role_switch_gen, role_switch_cooldown
            FROM agents WHERE agent_id = ?
        """, (agent_id,))
        
        if not agent:
            return False, "Agent not found"
        
        agent_data = agent[0]
        
        if agent_data.get('role_locked'):
            return False, "Agent is role-locked (found their niche)"
        
        # Check cooldown
        cooldown = agent_data.get('role_switch_cooldown', 2)
        last_switch = agent_data.get('last_role_switch_gen', 0)
        
        if generation - last_switch < cooldown:
            remaining = cooldown - (generation - last_switch)
            return False, f"Cooldown not complete ({remaining} generations remaining)"
        
        # Check capacity (soft limit - high fit agents can overflow)
        has_capacity = self._role_has_capacity(desired_role, generation)
        
        # Get agent's fit score for desired role
        fit_result = self.db.execute_query("""
            SELECT role_fit_score FROM agent_role_performance
            WHERE agent_id = ? AND role = ?
        """, (agent_id, desired_role))
        
        fit_score = fit_result[0]['role_fit_score'] if fit_result else 0.0
        
        if has_capacity or fit_score > 0.7:  # High-fit agents can overflow
            # Approve the change
            self.db.execute_query("""
                UPDATE agents SET 
                    preferred_role = ?,
                    last_role_switch_gen = ?
                WHERE agent_id = ?
            """, (desired_role, generation, agent_id))
            
            logger.info(f"[ROLE CHANGE] Agent {agent_id[:8]} -> {desired_role} (fit={fit_score:.2f})")
            return True, f"Role change approved (fit={fit_score:.2f})"
        
        return False, f"No capacity and fit too low ({fit_score:.2f})"

    def get_role_fit_summary(self, agent_id: str) -> Dict:
        """
        Get summary of agent's fit scores across all roles.
        Useful for debugging and agent introspection.
        """
        performances = self.db.execute_query("""
            SELECT role, role_fit_score, games_played, total_wins, 
                   avg_frustration, avg_satisfaction
            FROM agent_role_performance
            WHERE agent_id = ?
        """, (agent_id,))
        
        agent = self.db.execute_query("""
            SELECT preferred_role, role_locked, role_confidence
            FROM agents WHERE agent_id = ?
        """, (agent_id,))
        
        summary = {
            'agent_id': agent_id,
            'preferred_role': agent[0]['preferred_role'] if agent else None,
            'role_locked': agent[0]['role_locked'] if agent else False,
            'role_confidence': agent[0]['role_confidence'] if agent else 0.0,
            'role_fits': {}
        }
        
        for p in performances:
            summary['role_fits'][p['role']] = {
                'fit_score': p['role_fit_score'],
                'games_played': p['games_played'],
                'win_rate': p['total_wins'] / max(p['games_played'], 1),
                'frustration': p['avg_frustration'],
                'satisfaction': p['avg_satisfaction']
            }
        
        return summary

    def get_locked_agents_count(self) -> Dict[str, int]:
        """Get count of locked agents per role."""
        results = self.db.execute_query("""
            SELECT preferred_role, COUNT(*) as count
            FROM agents
            WHERE role_locked = TRUE AND is_active = TRUE
            GROUP BY preferred_role
        """)
        
        counts = {'pioneer': 0, 'optimizer': 0, 'generalist': 0, 'exploiter': 0}
        for r in results:
            if r['preferred_role']:
                counts[r['preferred_role']] = r['count']
        
        return counts

    # ========================================================================
    # TWO-STREAMS: META-LEARNING (Learn to Trust Self vs Network)
    # ========================================================================
    
    def update_meta_bias(
        self,
        agent_id: str,
        decision_aligned_with: str,
        outcome_success: bool
    ) -> None:
        """
        Update agent's self/network bias based on decision outcome.
        
        Two-Streams Philosophy: Agents should learn WHEN to trust themselves
        vs when to trust the network. This is recursive meta-learning.
        
        Args:
            agent_id: Agent to update
            decision_aligned_with: 'private' (trusted self) or 'network' (trusted network)
            outcome_success: Whether the decision led to success
        """
        # Get current bias and learning rate
        agent = self.db.execute_query("""
            SELECT self_network_bias, bias_learning_rate
            FROM agents WHERE agent_id = ?
        """, (agent_id,))
        
        if not agent:
            return
        
        current_bias = agent[0]['self_network_bias'] or 0.5
        learning_rate = agent[0]['bias_learning_rate'] or 0.1
        
        # Calculate bias adjustment
        # If decision aligned with self and succeeded -> increase self trust
        # If decision aligned with network and succeeded -> decrease self trust
        # Opposite adjustments for failures
        
        if decision_aligned_with == 'private':
            # Trusted self
            if outcome_success:
                adjustment = learning_rate  # Self was right, increase self trust
            else:
                adjustment = -learning_rate  # Self was wrong, decrease self trust
        elif decision_aligned_with == 'network':
            # Trusted network
            if outcome_success:
                adjustment = -learning_rate  # Network was right, decrease self trust
            else:
                adjustment = learning_rate  # Network was wrong, increase self trust
        else:  # 'balanced'
            # No strong adjustment for balanced decisions
            adjustment = 0.0
        
        # Apply adjustment with dampening for extreme values
        # Harder to move away from extremes (avoid oscillation)
        dampening = 1.0 - abs(current_bias - 0.5) * 0.5  # Max dampening at extremes
        adjustment *= dampening
        
        new_bias = current_bias + adjustment
        new_bias = max(0.0, min(1.0, new_bias))  # Clamp to valid range
        
        # Update database
        self.db.execute_query("""
            UPDATE agents SET self_network_bias = ? WHERE agent_id = ?
        """, (new_bias, agent_id))
        
        logger.debug(
            f"[META-BIAS] Agent {agent_id[:8]}: {current_bias:.2f} -> {new_bias:.2f} "
            f"(aligned={decision_aligned_with}, success={outcome_success})"
        )
    
    def record_stream_alignment(
        self,
        agent_id: str,
        game_id: str,
        action_taken: int,
        aligned_with: str,
        reward: float,
        generation: int
    ) -> None:
        """
        Record which stream (private/network) a decision aligned with.
        
        This extends sensation_learning_events to track stream alignment
        for meta-learning analysis.
        
        Args:
            agent_id: Agent who made decision
            game_id: Game context
            action_taken: Action that was taken
            aligned_with: 'private', 'network', or 'balanced'
            reward: Outcome reward signal
            generation: Current generation
        """
        import uuid
        from datetime import datetime
        
        try:
            self.db.execute_query("""
                INSERT INTO sensation_learning_events
                (event_id, agent_id, game_id, generation, action_taken, 
                 reward_received, aligned_with_stream, event_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"stream_{uuid.uuid4().hex[:12]}",
                agent_id, game_id, generation, action_taken,
                reward, aligned_with, datetime.now().isoformat()
            ))
        except Exception as e:
            logger.debug(f"Stream alignment recording failed: {e}")
    
    def get_agent_stream_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get statistics on agent's stream alignment history.
        
        Useful for understanding whether agent should trust self or network more.
        
        Returns:
            Dictionary with success rates for private vs network decisions
        """
        stats = self.db.execute_query("""
            SELECT 
                aligned_with_stream,
                COUNT(*) as total,
                AVG(CASE WHEN reward_received > 0 THEN 1.0 ELSE 0.0 END) as success_rate
            FROM sensation_learning_events
            WHERE agent_id = ? AND aligned_with_stream IS NOT NULL
            GROUP BY aligned_with_stream
        """, (agent_id,))
        
        result = {
            'private_success_rate': 0.5,
            'network_success_rate': 0.5,
            'balanced_success_rate': 0.5,
            'private_count': 0,
            'network_count': 0,
            'balanced_count': 0
        }
        
        for s in (stats or []):
            stream = s['aligned_with_stream']
            if stream == 'private':
                result['private_success_rate'] = s['success_rate'] or 0.5
                result['private_count'] = s['total']
            elif stream == 'network':
                result['network_success_rate'] = s['success_rate'] or 0.5
                result['network_count'] = s['total']
            elif stream == 'balanced':
                result['balanced_success_rate'] = s['success_rate'] or 0.5
                result['balanced_count'] = s['total']
        
        # Calculate recommended bias based on historical performance
        private_weight = result['private_success_rate'] * max(1, result['private_count'])
        network_weight = result['network_success_rate'] * max(1, result['network_count'])
        total_weight = private_weight + network_weight
        
        if total_weight > 0:
            result['recommended_bias'] = private_weight / total_weight
        else:
            result['recommended_bias'] = 0.5
        
        return result


# ============================================================================
# SOCIETAL METRICS SYSTEM - ROLE SATURATION
# Part of autopoiesis monitoring for self-regulation
# ============================================================================

def calculate_role_saturation(db: DatabaseInterface, generation: int) -> Dict[str, float]:
    """
    Calculate saturation level for each role (approaching target limits).
    
    Role Saturation measures how close each role is to its target population.
    Useful for detecting when roles are under/over-filled and need rebalancing.
    
    Formula per role:
        actual_count / target_count
        
    Values:
        < 0.8 = Under-filled (need more agents in this role)
        0.8-1.2 = Healthy range
        > 1.2 = Over-filled (too many agents, wasted resources)
    
    Args:
        db: DatabaseInterface instance
        generation: Current evolution generation
        
    Returns:
        Dict mapping role -> saturation ratio
        
    Part of the Societal Metrics System.
    See DOCS/Societal_Metrics_Implementation_Analysis.md for design rationale.
    """
    try:
        # Default target ratios
        # Adjust based on whether in exploration or optimization phase
        full_wins = db.execute_query("""
            SELECT COUNT(DISTINCT game_id) as count
            FROM winning_sequences
            WHERE is_full_game_win = 1 AND is_valid = 1
        """)
        has_full_wins = (full_wins and full_wins[0]['count'] > 0)
        
        if has_full_wins:
            # OPTIMIZATION PHASE ratios
            target_ratios = {
                'pioneer': 0.10,
                'optimizer': 0.50,
                'generalist': 0.25,
                'exploiter': 0.15
            }
        else:
            # EXPLORATION PHASE ratios
            target_ratios = {
                'pioneer': 0.60,
                'optimizer': 0.10,
                'generalist': 0.20,
                'exploiter': 0.10
            }
        
        # Get actual population counts per role
        population_result = db.execute_query("""
            SELECT 
                LOWER(COALESCE(role, 'generalist')) as role,
                COUNT(*) as count
            FROM agents
            WHERE is_active = TRUE
            GROUP BY role
        """)
        
        if not population_result:
            logger.warning("No active agents for role saturation calculation")
            return {role: 0.0 for role in target_ratios}
        
        total_agents = sum(r['count'] for r in population_result)
        if total_agents == 0:
            return {role: 0.0 for role in target_ratios}
        
        actual_counts = {
            r['role']: r['count'] 
            for r in population_result
        }
        
        # Calculate saturation per role
        saturations = {}
        for role, target_ratio in target_ratios.items():
            target_count = max(total_agents * target_ratio, 1)
            actual_count = actual_counts.get(role, 0)
            saturations[role] = actual_count / target_count
        
        # Store metrics in ecosystem_metrics table
        _store_role_saturation_metrics(db, generation, saturations, has_full_wins)
        
        # Calculate overall saturation health
        mean_saturation = sum(saturations.values()) / len(saturations)
        max_deviation = max(abs(s - 1.0) for s in saturations.values())
        
        logger.info(f"[SATURATION] Generation {generation}: "
                   f"mean={mean_saturation:.2f} max_dev={max_deviation:.2f} "
                   f"phase={'OPTIMIZATION' if has_full_wins else 'EXPLORATION'}")
        
        return saturations
        
    except Exception as e:
        logger.error(f"Error calculating role saturation: {e}")
        return {}


def _store_role_saturation_metrics(db: DatabaseInterface, generation: int,
                                    saturations: Dict[str, float], 
                                    is_optimization_phase: bool):
    """Store role saturation in ecosystem_metrics table for tracking."""
    import json
    
    try:
        # Ensure table exists
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS ecosystem_metrics (
                metric_name TEXT NOT NULL,
                generation INTEGER NOT NULL,
                value REAL NOT NULL,
                measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                PRIMARY KEY (metric_name, generation)
            )
        """)
        
        # Store overall saturation health (mean)
        mean_saturation = sum(saturations.values()) / len(saturations) if saturations else 0.0
        
        metadata = {
            'by_role': saturations,
            'phase': 'optimization' if is_optimization_phase else 'exploration'
        }
        
        db.execute_query("""
            INSERT INTO ecosystem_metrics (metric_name, generation, value, metadata)
            VALUES ('role_saturation', ?, ?, ?)
            ON CONFLICT(metric_name, generation) DO UPDATE SET 
                value = excluded.value,
                metadata = excluded.metadata,
                measured_at = CURRENT_TIMESTAMP
        """, (generation, mean_saturation, json.dumps(metadata)))
        
        # Also store individual role saturations for detailed tracking
        for role, saturation in saturations.items():
            db.execute_query("""
                INSERT INTO ecosystem_metrics (metric_name, generation, value, metadata)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(metric_name, generation) DO UPDATE SET 
                    value = excluded.value,
                    measured_at = CURRENT_TIMESTAMP
            """, (f'role_saturation_{role}', generation, saturation, 
                  json.dumps({'phase': 'optimization' if is_optimization_phase else 'exploration'})))
        
    except Exception as e:
        logger.error(f"Error storing role saturation metrics: {e}")
