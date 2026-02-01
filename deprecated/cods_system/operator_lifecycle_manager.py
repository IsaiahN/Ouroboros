import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Operator Lifecycle Manager - Survival & Competition System
==========================================================

Extracted from cods_engine.py (Jan 2026 refactor).

Operators must fight to survive like viral packages and pariahs.
Good operators get promoted, bad operators die.

Rule 1: Disable pycache
Rule 2: All data in database
Rule 10: Leverage existing systems
"""

import logging
from typing import Dict, List, Any, Optional

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class OperatorLifecycleManager:
    """
    Manages the lifecycle of composed operators.
    
    Operators go through stages:
    1. Created (new, untested)
    2. Tested (has some test results)
    3. Canonical (high-performing, protected)
    4. Pruned (underperforming, inactive)
    5. Killed (deleted permanently)
    """
    
    def __init__(self, db: DatabaseInterface):
        """
        Initialize the Operator Lifecycle Manager.
        
        Args:
            db: Database interface for persistence
        """
        self.db = db
    
    def evolve_operators(
        self,
        generations: int = 5,
        population_size: int = 20,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.3
    ) -> List[Any]:
        """
        Evolve operator population through genetic operators.
        
        Args:
            generations: Number of evolution generations
            population_size: Target population size
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
            
        Returns:
            List of evolved operators
        """
        from engines.social.operator_composer import ComposedOperator
        
        evolved = []
        
        # Get current population of tested operators
        population_rows = self.db.execute_query("""
            SELECT operator_id, name, composition_tree, success_rate, times_tested
            FROM composed_operators
            WHERE status IN ('tested', 'canonical')
            AND times_tested >= 3
            ORDER BY success_rate DESC
            LIMIT ?
        """, (population_size * 2,))
        
        population = []
        for row in (population_rows or []):
            try:
                import json
                tree = json.loads(row['composition_tree']) if row['composition_tree'] else {}
                op = ComposedOperator(
                    operator_id=row['operator_id'],
                    name=row['name'],
                    primitives=[],  # Not needed for evolution
                    composition_tree=tree,
                    success_rate=row['success_rate'],
                    times_tested=row['times_tested']
                )
                population.append(op)
            except Exception:
                continue
        
        if len(population) < 2:
            logger.debug("[CODS] Not enough operators for evolution")
            return evolved
        
        # Evolution loop
        import random
        for gen in range(generations):
            new_population = []
            
            for _ in range(population_size // 2):
                # Tournament selection
                parent1 = max(
                    random.sample(population, min(3, len(population))),
                    key=lambda x: x.success_rate
                )
                parent2 = max(
                    random.sample(population, min(3, len(population))),
                    key=lambda x: x.success_rate
                )
                
                # TODO: Implement crossover and mutation when composition_tree 
                # structure is finalized
                
            # Keep best operators
            population = sorted(
                population,
                key=lambda x: x.success_rate,
                reverse=True
            )[:population_size]
            
            evolved.extend(new_population)
            
            logger.debug(f"[CODS] Evolution gen {gen+1}: {len(new_population)} new variants")
        
        return evolved
    
    def prune_operators(
        self,
        min_success_rate: float = 0.3,
        min_tests: int = 10
    ) -> int:
        """
        Prune poorly performing operators.
        
        Args:
            min_success_rate: Minimum success rate to keep
            min_tests: Minimum tests required before pruning
            
        Returns:
            Number of operators pruned
        """
        self.db.execute_query("""
            UPDATE composed_operators
            SET status = 'pruned'
            WHERE times_tested >= ?
            AND success_rate < ?
            AND status NOT IN ('canonical', 'solid')
        """, (min_tests, min_success_rate))
        
        count = self.db.execute_query("""
            SELECT COUNT(*) as cnt FROM composed_operators WHERE status = 'pruned'
        """)
        
        pruned_count = count[0]['cnt'] if count else 0
        logger.info(f"[CODS] Pruned {pruned_count} underperforming operators")
        
        return pruned_count
    
    def run_operator_lifecycle(self) -> Dict[str, Any]:
        """
        Run the full operator lifecycle: promote, demote, and kill operators.
        
        Called periodically (e.g., every generation) to apply evolutionary pressure.
        
        Returns:
            Summary of lifecycle actions taken
        """
        results = {
            'promoted': 0,
            'demoted': 0,
            'killed': 0,
            'spared': 0
        }
        
        try:
            # 1. Promote strong operators to canonical
            results['promoted'] = self._promote_strong_operators()
            
            # 2. Kill weak operators (not just prune - actually delete)
            results['killed'] = self._kill_weak_operators()
            
            # 3. Track competition stats
            self._update_competition_rankings()
            
            logger.info(f"[CODS] Operator lifecycle: {results['promoted']} promoted, "
                       f"{results['killed']} killed")
            
        except Exception as e:
            logger.error(f"[CODS] Operator lifecycle error: {e}")
        
        return results
    
    def _promote_strong_operators(
        self,
        min_success_rate: float = 0.9,
        min_tests: int = 10,
        min_games: int = 2
    ) -> int:
        """
        Promote operators that consistently succeed to 'canonical' status.
        
        Canonical operators are:
        - Protected from pruning/killing
        - Prioritized in operator selection
        - Shared network-wide as validated solutions
        """
        try:
            # Find operators that deserve promotion
            candidates = self.db.execute_query("""
                SELECT operator_id, name, success_rate, times_tested, games_tested_on
                FROM composed_operators
                WHERE status = 'tested'
                  AND success_rate >= ?
                  AND times_tested >= ?
            """, (min_success_rate, min_tests))
            
            promoted = 0
            for op in (candidates or []):
                # Check game diversity (tested on multiple games)
                games = op['games_tested_on'] or ''
                unique_games = len(set(g for g in games.split(',') if g.strip('"')))
                
                if unique_games >= min_games:
                    self.db.execute_query("""
                        UPDATE composed_operators
                        SET status = 'canonical'
                        WHERE operator_id = ?
                    """, (op['operator_id'],))
                    promoted += 1
                    logger.info(f"[CODS] Promoted operator to canonical: {op['name']} "
                               f"(rate={op['success_rate']:.2f}, tests={op['times_tested']})")
            
            return promoted
            
        except Exception as e:
            logger.error(f"[CODS] Error promoting operators: {e}")
            return 0
    
    def _kill_weak_operators(
        self,
        max_failure_rate: float = 0.9,
        min_tests: int = 5,
        kill_old_unused: bool = True,
        unused_days: int = 14
    ) -> int:
        """
        Permanently DELETE operators that consistently fail.
        
        Unlike pruning (status change), this removes them from the database.
        Dead operators free up space for new experiments.
        
        Note: Thresholds are aggressive - operators must prove value quickly
        or be replaced by better alternatives.
        """
        killed = 0
        
        try:
            # Temporarily disable foreign keys for batch deletion
            self.db.execute_query("PRAGMA foreign_keys=OFF")
            
            # Kill high-failure operators (success_rate < 10% after 5+ tests)
            failures = self.db.execute_query("""
                SELECT operator_id, name, success_rate, times_tested
                FROM composed_operators
                WHERE status NOT IN ('canonical', 'solid')
                  AND times_tested >= ?
                  AND success_rate < ?
            """, (min_tests, 1 - max_failure_rate))
            
            for op in (failures or []):
                op_id = op['operator_id']
                op_name = op['name']
                
                # Delete from ALL referencing tables FIRST (foreign key order)
                self.db.execute_query("""
                    DELETE FROM operator_test_results WHERE operator_id = ?
                """, (op_id,))
                self.db.execute_query("""
                    DELETE FROM concept_operator_map WHERE operator_id = ?
                """, (op_id,))
                self.db.execute_query("""
                    DELETE FROM gametype_primitive_theory WHERE primitive_or_operator = ?
                """, (op_name,))
                # Now delete the operator itself
                self.db.execute_query("""
                    DELETE FROM composed_operators WHERE operator_id = ?
                """, (op_id,))
                killed += 1
                logger.debug(f"[CODS] Killed failing operator: {op_name} "
                           f"(rate={op['success_rate']:.2f})")
            
            # Kill old unused operators (stale ideas that never caught on)
            if kill_old_unused:
                old_unused = self.db.execute_query("""
                    SELECT operator_id, name, times_tested
                    FROM composed_operators
                    WHERE status NOT IN ('canonical', 'solid')
                      AND times_tested < 3
                      AND created_at < datetime('now', ? || ' days')
                """, (f"-{unused_days}",))
                
                for op in (old_unused or []):
                    op_id = op['operator_id']
                    op_name = op['name']
                    
                    # Delete from ALL referencing tables FIRST
                    self.db.execute_query("""
                        DELETE FROM operator_test_results WHERE operator_id = ?
                    """, (op_id,))
                    self.db.execute_query("""
                        DELETE FROM concept_operator_map WHERE operator_id = ?
                    """, (op_id,))
                    self.db.execute_query("""
                        DELETE FROM gametype_primitive_theory WHERE primitive_or_operator = ?
                    """, (op_name,))
                    self.db.execute_query("""
                        DELETE FROM composed_operators WHERE operator_id = ?
                    """, (op_id,))
                    killed += 1
                    logger.debug(f"[CODS] Killed unused operator: {op_name}")
            
            # Re-enable foreign keys
            self.db.execute_query("PRAGMA foreign_keys=ON")
            return killed
            
        except Exception as e:
            # Re-enable foreign keys even on error
            try:
                self.db.execute_query("PRAGMA foreign_keys=ON")
            except Exception:
                logger.warning("Failed to re-enable foreign keys")
            logger.error(f"[CODS] Error killing operators: {e}")
            return killed
    
    def _update_competition_rankings(self) -> None:
        """
        Update competition stats between operators targeting similar goals.
        
        Operators that solve the same problem compete for survival.
        The winner gets used more, the loser eventually dies.
        
        CRITICAL: Uses weighted_competition_score, NOT raw success_rate!
        This ensures frontier performance matters more than replay grinding.
        """
        try:
            # Group operators by their composition type and find competitors
            # Use weighted_competition_score for ranking (frontier-weighted)
            operators = self.db.execute_query("""
                SELECT operator_id, name, composition_type, 
                       success_rate, times_tested,
                       COALESCE(weighted_competition_score, success_rate) as competition_score,
                       COALESCE(frontier_tests, 0) as frontier_tests
                FROM composed_operators
                WHERE status NOT IN ('pruned')
                  AND times_tested >= 5
                ORDER BY composition_type, competition_score DESC
            """)
            
            if not operators:
                return
            
            # Group by composition type
            by_type: Dict[str, List[Dict]] = {}
            for op in operators:
                comp_type = op['composition_type'] or 'unknown'
                if comp_type not in by_type:
                    by_type[comp_type] = []
                by_type[comp_type].append(op)
            
            # Within each type, mark competition
            for comp_type, ops in by_type.items():
                if len(ops) < 2:
                    continue
                
                # Best performer vs rest (based on weighted_competition_score)
                best = ops[0]
                for competitor in ops[1:]:
                    best_score = best.get('competition_score', 0) or 0
                    comp_score = competitor.get('competition_score', 0) or 0
                    
                    # Require meaningful difference (10% gap)
                    if best_score > comp_score + 0.1:
                        # Best wins - but weight by frontier experience
                        # Operators with frontier experience earn more decisive wins
                        frontier_bonus = 1 + min(best.get('frontier_tests', 0) or 0, 10) * 0.1
                        
                        self.db.execute_query("""
                            UPDATE composed_operators
                            SET wins_vs_primitive = wins_vs_primitive + ?
                            WHERE operator_id = ?
                        """, (int(frontier_bonus), best['operator_id']))
                        self.db.execute_query("""
                            UPDATE composed_operators
                            SET losses_vs_primitive = losses_vs_primitive + 1
                            WHERE operator_id = ?
                        """, (competitor['operator_id'],))
            
        except Exception as e:
            logger.error(f"[CODS] Error updating competition rankings: {e}")
    
    def get_operator_survival_stats(self) -> Dict[str, Any]:
        """Get statistics on operator population and survival."""
        try:
            stats = {}
            
            # Population by status
            status_counts = self.db.execute_query("""
                SELECT status, COUNT(*) as count
                FROM composed_operators
                GROUP BY status
            """)
            
            stats['by_status'] = {
                row['status']: row['count'] 
                for row in (status_counts or [])
            }
            
            # Total population
            stats['total'] = sum(stats['by_status'].values())
            
            # Average success rate
            avg_result = self.db.execute_query("""
                SELECT AVG(success_rate) as avg_rate, 
                       AVG(times_tested) as avg_tests
                FROM composed_operators
                WHERE status NOT IN ('pruned')
            """)
            
            if avg_result and avg_result[0]:
                stats['avg_success_rate'] = round(avg_result[0]['avg_rate'] or 0, 3)
                stats['avg_times_tested'] = round(avg_result[0]['avg_tests'] or 0, 1)
            
            # Top performers
            top_ops = self.db.execute_query("""
                SELECT name, success_rate, times_tested
                FROM composed_operators
                WHERE status = 'canonical'
                ORDER BY success_rate DESC
                LIMIT 5
            """)
            
            stats['top_canonical'] = [
                {
                    'name': op['name'],
                    'success_rate': round(op['success_rate'], 3),
                    'tests': op['times_tested']
                }
                for op in (top_ops or [])
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"[CODS] Error getting survival stats: {e}")
            return {'error': str(e)}
