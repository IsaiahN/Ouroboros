import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Oracle Stuck Game Diagnostics - Network Learning Health Monitor
================================================================

DIAGNOSTIC ONLY - No interventions imposed on agents.

This module detects when games are stuck and diagnoses WHY by checking
which tier of the 6-tier thought process is broken. It reports findings
to logs for human/Copilot review but does NOT tell agents what to do.

Philosophy: If games stay stuck, a TIER is broken. Fix the SYSTEM,
not the agents. Let network intelligence emerge naturally.

The 6-Tier Architecture:
  Tier 1-3: Agents observe, share, validate
  Tier 4: Agents USE validated knowledge
  Tier 5: Network SELECTS successful strategies
  Tier 6: Network SYNTHESIZES new operators

If all 6 tiers work, stuck games resolve naturally through evolution.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class StuckGameDiagnosis:
    """Diagnostic report for a stuck game."""
    game_type: str
    generation: int

    # Detection metrics
    failure_rate: float = 0.0
    agents_on_game: int = 0
    best_level_reached: int = 0

    # Tier health checks
    tier_1_3_healthy: Optional[bool] = None  # Observation/Sharing/Validation
    tier_4_healthy: Optional[bool] = None     # Usage
    tier_5_healthy: Optional[bool] = None     # Selection
    tier_6_healthy: Optional[bool] = None     # Synthesis

    # Diagnosis
    broken_tier: Optional[str] = None
    diagnosis: str = ""
    details: str = ""
    suggested_fix: str = ""

    # Knowledge inventory
    hypotheses_count: int = 0
    validated_hypotheses: int = 0
    hypothesis_usage_count: int = 0
    operators_synthesized: int = 0
    death_zones_count: int = 0


class OracleStuckGameDiagnostics:
    """
    DIAGNOSTIC ONLY - Monitors network learning health.

    Detects stuck games and diagnoses WHICH TIER is broken.
    Reports findings to logs for human/Copilot review.
    Does NOT tell agents what to do - that's designer intelligence.
    """

    def __init__(self, db):
        """Initialize the diagnostics system."""
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Thresholds
        self.stuck_threshold = 0.70  # 70% failure rate = potentially stuck
        self.min_attempts_for_diagnosis = 10  # Need enough data to diagnose
        self.generations_to_check = 10  # Look at recent history

    def check_stuck_games(self, generation: int) -> List[str]:
        """
        METRIC: Identify games where network is not learning.

        Returns list of stuck game_types for logging.
        This is detection only - no intervention.
        """
        stuck_games = []

        try:
            # Find games with high failure rates in recent generations
            game_stats = self.db.execute_query("""
                SELECT
                    SUBSTR(game_id, 1, 4) as game_type,
                    COUNT(*) as attempts,
                    SUM(CASE WHEN final_score < 2 THEN 1 ELSE 0 END) as failures,
                    MAX(final_score) as best_score,
                    AVG(final_score) as avg_score
                FROM game_results
                WHERE generation BETWEEN ? AND ?
                GROUP BY game_type
                HAVING attempts >= ?
            """, (generation - self.generations_to_check, generation,
                  self.min_attempts_for_diagnosis))

            if not game_stats:
                return []

            for stat in game_stats:
                failure_rate = stat['failures'] / stat['attempts'] if stat['attempts'] > 0 else 0

                if failure_rate >= self.stuck_threshold:
                    stuck_games.append(stat['game_type'])
                    self.logger.warning(
                        f"[ORACLE-METRIC] Game {stat['game_type']} may be stuck: "
                        f"{failure_rate*100:.0f}% failure rate, best_score={stat['best_score']}"
                    )

            return stuck_games

        except Exception as e:
            self.logger.debug(f"Error checking stuck games: {e}")
            return []

    def diagnose_stuck_game(self, game_type: str, generation: int) -> StuckGameDiagnosis:
        """
        DIAGNOSTIC: Identify WHICH TIER is broken.

        Checks each tier of the 6-tier thought process to find
        where the network learning is failing.

        Returns diagnosis with suggested SYSTEM fix (not agent intervention).
        """
        diagnosis = StuckGameDiagnosis(
            game_type=game_type,
            generation=generation
        )

        try:
            # Get basic stats
            stats = self._get_game_stats(game_type, generation)
            diagnosis.failure_rate = stats.get('failure_rate', 0)
            diagnosis.agents_on_game = stats.get('agents', 0)
            diagnosis.best_level_reached = stats.get('best_level', 0)

            # Check Tier 1-3: Are agents sharing observations?
            diagnosis.tier_1_3_healthy = self._check_tier_1_3(game_type, generation, diagnosis)

            if not diagnosis.tier_1_3_healthy:
                return diagnosis  # Can't check later tiers if early tiers broken

            # Check Tier 4: Are agents USING validated knowledge?
            diagnosis.tier_4_healthy = self._check_tier_4(game_type, generation, diagnosis)

            if not diagnosis.tier_4_healthy:
                return diagnosis  # Can't check later tiers if Tier 4 broken

            # Check Tier 5: Is network SELECTING successful strategies?
            diagnosis.tier_5_healthy = self._check_tier_5(game_type, generation, diagnosis)

            if not diagnosis.tier_5_healthy:
                return diagnosis

            # Check Tier 6: Is network SYNTHESIZING operators?
            diagnosis.tier_6_healthy = self._check_tier_6(game_type, generation, diagnosis)

            if not diagnosis.tier_6_healthy:
                return diagnosis

            # All tiers healthy but game still stuck
            diagnosis.diagnosis = "SYSTEM_HEALTHY_GAME_HARD"
            diagnosis.details = (
                f"All 6 tiers working. Network has {diagnosis.hypotheses_count} hypotheses, "
                f"{diagnosis.validated_hypotheses} validated, {diagnosis.operators_synthesized} operators. "
                f"Game may simply be difficult - let evolution continue."
            )
            diagnosis.suggested_fix = "No system fix needed. Trust the network."

            return diagnosis

        except Exception as e:
            self.logger.error(f"Error diagnosing stuck game {game_type}: {e}")
            diagnosis.diagnosis = "DIAGNOSTIC_ERROR"
            diagnosis.details = str(e)
            return diagnosis

    def _get_game_stats(self, game_type: str, generation: int) -> Dict:
        """Get basic game statistics."""
        try:
            stats = self.db.execute_query("""
                SELECT
                    COUNT(*) as attempts,
                    SUM(CASE WHEN final_score < 2 THEN 1 ELSE 0 END) as failures,
                    MAX(final_score) as best_score,
                    COUNT(DISTINCT agent_id) as agents
                FROM game_results
                WHERE game_id LIKE ? || '%'
                  AND generation BETWEEN ? AND ?
            """, (game_type, generation - self.generations_to_check, generation))

            if stats and stats[0]:
                s = stats[0]
                return {
                    'attempts': s['attempts'] or 0,
                    'failure_rate': (s['failures'] or 0) / max(s['attempts'] or 1, 1),
                    'best_level': int(s['best_score'] or 0),
                    'agents': s['agents'] or 0
                }
            return {}

        except:
            return {}

    def _check_tier_1_3(self, game_type: str, generation: int,
                         diagnosis: StuckGameDiagnosis) -> bool:
        """
        Check Tier 1-3: Observation, Sharing, Validation

        Are agents recording and sharing their observations?
        """
        try:
            # Check for network hypotheses (Tier 2: Sharing)
            hypotheses = self.db.execute_query("""
                SELECT COUNT(*) as count FROM network_object_control_hypotheses
                WHERE game_type = ? AND is_active = 1
            """, (game_type,))

            diagnosis.hypotheses_count = hypotheses[0]['count'] if hypotheses else 0

            if diagnosis.hypotheses_count == 0:
                diagnosis.broken_tier = "TIER_1_2"
                diagnosis.diagnosis = "NO_HYPOTHESES_SHARED"
                diagnosis.details = (
                    f"Game {game_type}: 0 hypotheses in network. "
                    "Agents are not sharing their observations."
                )
                diagnosis.suggested_fix = (
                    "Check that learn_from_movement_correlation() is being called "
                    "during discovery phase in core_gameplay.py"
                )
                return False

            # Check for validation (Tier 3)
            validated = self.db.execute_query("""
                SELECT COUNT(*) as count FROM network_object_control_hypotheses
                WHERE game_type = ? AND is_active = 1 AND validation_attempts >= 3
            """, (game_type,))

            diagnosis.validated_hypotheses = validated[0]['count'] if validated else 0

            if diagnosis.validated_hypotheses == 0:
                diagnosis.broken_tier = "TIER_3"
                diagnosis.diagnosis = "NO_VALIDATED_HYPOTHESES"
                diagnosis.details = (
                    f"Game {game_type}: {diagnosis.hypotheses_count} hypotheses but 0 validated. "
                    "Observations are not being repeated for validation."
                )
                diagnosis.suggested_fix = (
                    "Check that discovery phase is testing objects multiple times. "
                    "Agents may need to repeat tests to validate hypotheses."
                )
                return False

            return True

        except Exception as e:
            self.logger.debug(f"Error checking Tier 1-3: {e}")
            return True  # Assume healthy if can't check

    def _check_tier_4(self, game_type: str, generation: int,
                       diagnosis: StuckGameDiagnosis) -> bool:
        """
        Check Tier 4: Usage

        Are agents actually USING the validated hypotheses?
        """
        try:
            # Check if hypotheses are being used in gameplay
            # This is the critical missing tier in many implementations
            usage = self.db.execute_query("""
                SELECT SUM(COALESCE(times_used, 0)) as usage_count
                FROM network_object_control_hypotheses
                WHERE game_type = ? AND is_active = 1
            """, (game_type,))

            diagnosis.hypothesis_usage_count = usage[0]['usage_count'] if usage and usage[0]['usage_count'] else 0

            if diagnosis.hypothesis_usage_count == 0 and diagnosis.validated_hypotheses > 0:
                diagnosis.broken_tier = "TIER_4"
                diagnosis.diagnosis = "HYPOTHESES_NOT_USED"
                diagnosis.details = (
                    f"Game {game_type}: {diagnosis.validated_hypotheses} validated hypotheses "
                    f"but usage_count=0. Agents are not using network knowledge."
                )
                diagnosis.suggested_fix = (
                    "Implement select_action_from_hypothesis() in action selection. "
                    "Agents need to query and USE validated hypotheses, not just store them."
                )
                return False

            return True

        except Exception as e:
            self.logger.debug(f"Error checking Tier 4: {e}")
            return True

    def _check_tier_5(self, game_type: str, generation: int,
                       diagnosis: StuckGameDiagnosis) -> bool:
        """
        Check Tier 5: Selection

        Is the network selecting successful strategies?
        """
        try:
            # Check if hypotheses with high best_score_achieved are rising
            selection = self.db.execute_query("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN best_score_achieved > 0 THEN 1 ELSE 0 END) as with_success
                FROM network_object_control_hypotheses
                WHERE game_type = ? AND is_active = 1
            """, (game_type,))

            if selection and selection[0]:
                total = selection[0]['total']
                with_success = selection[0]['with_success'] or 0

                if total > 10 and with_success == 0:
                    diagnosis.broken_tier = "TIER_5"
                    diagnosis.diagnosis = "NO_SUCCESSFUL_STRATEGIES"
                    diagnosis.details = (
                        f"Game {game_type}: {total} hypotheses but 0 have positive best_score_achieved. "
                        "No strategies are being selected as successful."
                    )
                    diagnosis.suggested_fix = (
                        "Check that hypothesis feedback is being recorded after game results. "
                        "Successful actions should update best_score_achieved on used hypotheses."
                    )
                    return False

            return True

        except Exception as e:
            self.logger.debug(f"Error checking Tier 5: {e}")
            return True

    def _check_tier_6(self, game_type: str, generation: int,
                       diagnosis: StuckGameDiagnosis) -> bool:
        """
        Check Tier 6: Synthesis

        Is the network synthesizing new operators/abstractions?
        """
        try:
            # Check for synthesized operators (CODS output)
            operators = self.db.execute_query("""
                SELECT COUNT(*) as count FROM cods_operators
                WHERE game_type = ? OR game_type = 'universal'
            """, (game_type,))

            diagnosis.operators_synthesized = operators[0]['count'] if operators else 0

            # Also check for composite hypotheses
            composites = self.db.execute_query("""
                SELECT COUNT(*) as count FROM network_object_control_hypotheses
                WHERE game_type = ? AND hypothesis_id LIKE 'composite_%'
            """, (game_type,))

            composite_count = composites[0]['count'] if composites else 0

            # Tier 6 is only "broken" if we have lots of data but no synthesis
            # If network is young, synthesis hasn't had time to happen
            if generation > 50 and diagnosis.validated_hypotheses > 20:
                if diagnosis.operators_synthesized == 0 and composite_count == 0:
                    diagnosis.broken_tier = "TIER_6"
                    diagnosis.diagnosis = "NO_SYNTHESIS"
                    diagnosis.details = (
                        f"Game {game_type}: {diagnosis.validated_hypotheses} validated hypotheses "
                        f"over {generation} generations but 0 operators synthesized. "
                        "Network is not abstracting patterns."
                    )
                    diagnosis.suggested_fix = (
                        "Check CODS Bayesian probability thresholds. "
                        "synthesis_threshold may be too high (try 0.75 instead of 0.85). "
                        "Also check synthesize_composite_hypothesis() is being called."
                    )
                    return False

            return True

        except Exception as e:
            self.logger.debug(f"Error checking Tier 6: {e}")
            return True

    def get_learning_health_summary(self, generation: int) -> Dict[str, Any]:
        """
        METRIC: Overall network learning health summary.

        Returns aggregated health metrics across all games.
        """
        summary = {
            'generation': generation,
            'total_games_tracked': 0,
            'stuck_games': [],
            'tier_health': {
                'tier_1_3': {'healthy': 0, 'broken': 0},
                'tier_4': {'healthy': 0, 'broken': 0},
                'tier_5': {'healthy': 0, 'broken': 0},
                'tier_6': {'healthy': 0, 'broken': 0}
            },
            'overall_health': 'UNKNOWN'
        }

        try:
            stuck_games = self.check_stuck_games(generation)
            summary['stuck_games'] = stuck_games

            for game_type in stuck_games:
                diagnosis = self.diagnose_stuck_game(game_type, generation)
                summary['total_games_tracked'] += 1

                # Track tier health
                if diagnosis.tier_1_3_healthy is not None:
                    key = 'healthy' if diagnosis.tier_1_3_healthy else 'broken'
                    summary['tier_health']['tier_1_3'][key] += 1

                if diagnosis.tier_4_healthy is not None:
                    key = 'healthy' if diagnosis.tier_4_healthy else 'broken'
                    summary['tier_health']['tier_4'][key] += 1

                if diagnosis.tier_5_healthy is not None:
                    key = 'healthy' if diagnosis.tier_5_healthy else 'broken'
                    summary['tier_health']['tier_5'][key] += 1

                if diagnosis.tier_6_healthy is not None:
                    key = 'healthy' if diagnosis.tier_6_healthy else 'broken'
                    summary['tier_health']['tier_6'][key] += 1

            # Overall health
            total_broken = sum(t['broken'] for t in summary['tier_health'].values())
            if total_broken == 0:
                summary['overall_health'] = 'HEALTHY'
            elif total_broken <= 2:
                summary['overall_health'] = 'WARNING'
            else:
                summary['overall_health'] = 'CRITICAL'

        except Exception as e:
            self.logger.error(f"Error getting health summary: {e}")
            summary['overall_health'] = 'ERROR'

        return summary

    def log_full_diagnostics(self, generation: int):
        """
        Log full diagnostic report for all stuck games.

        This is for human/Copilot review - suggests SYSTEM fixes.
        """
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"ORACLE STUCK GAME DIAGNOSTICS - Generation {generation}")
        self.logger.info(f"{'='*60}")

        stuck_games = self.check_stuck_games(generation)

        if not stuck_games:
            self.logger.info("[OK] No stuck games detected - network is learning")
            return

        self.logger.warning(f"[!] {len(stuck_games)} potentially stuck games detected")

        for game_type in stuck_games:
            diagnosis = self.diagnose_stuck_game(game_type, generation)

            self.logger.info(f"\n--- Game: {game_type} ---")
            self.logger.info(f"  Failure rate: {diagnosis.failure_rate*100:.0f}%")
            self.logger.info(f"  Best level: {diagnosis.best_level_reached}")
            self.logger.info(f"  Hypotheses: {diagnosis.hypotheses_count} total, {diagnosis.validated_hypotheses} validated")
            self.logger.info(f"  Hypothesis usage: {diagnosis.hypothesis_usage_count}")
            self.logger.info(f"  Operators: {diagnosis.operators_synthesized}")

            if diagnosis.broken_tier:
                self.logger.error(f"  [BROKEN] {diagnosis.broken_tier}: {diagnosis.diagnosis}")
                self.logger.error(f"  Details: {diagnosis.details}")
                self.logger.error(f"  SUGGESTED FIX: {diagnosis.suggested_fix}")
            else:
                self.logger.info(f"  [OK] All tiers healthy - game may just be difficult")

        self.logger.info(f"\n{'='*60}")
