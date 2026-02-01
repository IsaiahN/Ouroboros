import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Bayesian Hypothesis Engine - Evidence-Driven Operator Synthesis
================================================================

Extracted from cods_engine.py (Jan 2026 refactor).

The core of operator evolution:
1. Create hypotheses from failure patterns
2. Accumulate evidence from game outcomes
3. When posterior > threshold -> trigger synthesis
4. Validate synthesized operators over generations

Rule 1: Disable pycache
Rule 2: All data in database
Rule 10: Leverage existing systems
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from database_interface import DatabaseInterface
from engines.social.cods_types import BayesianHypothesis
from primitive_unlock_manager import PrimitiveUnlockManager, PrimitiveStatus

logger = logging.getLogger(__name__)


class BayesianHypothesisEngine:
    """
    Bayesian Hypothesis System for evidence-driven operator synthesis.
    
    This system:
    - Creates hypotheses from failure patterns
    - Accumulates evidence from game outcomes
    - Uses Bayesian updates to track confidence
    - Triggers synthesis when evidence is strong enough
    """
    
    def __init__(
        self,
        db: DatabaseInterface,
        unlock_manager: Optional[PrimitiveUnlockManager] = None
    ):
        """
        Initialize the Bayesian Hypothesis Engine.
        
        Args:
            db: Database interface for persistence
            unlock_manager: Optional primitive unlock manager for synthesis
        """
        self.db = db
        self.unlock_manager = unlock_manager
        
    def _bayesian_update(self, prior: float, evidence_for: int, evidence_against: int) -> float:
        """
        Calculate posterior probability using Bayesian update.
        
        Uses Beta-Binomial conjugate prior for clean updates.
        
        Args:
            prior: Prior probability P(H)
            evidence_for: Count of supporting observations
            evidence_against: Count of contradicting observations
            
        Returns:
            Posterior probability P(H|E)
        """
        # Convert prior to pseudo-counts (Beta distribution parameters)
        # Prior of 0.5 = 2 pseudo-observations each way (weak prior)
        alpha_prior = 2 * prior
        beta_prior = 2 * (1 - prior)
        
        # Update with evidence
        alpha_post = alpha_prior + evidence_for
        beta_post = beta_prior + evidence_against
        
        # Posterior mean of Beta distribution
        posterior = alpha_post / (alpha_post + beta_post)
        
        return posterior
    
    def _wilson_confidence_interval(
        self, 
        successes: int, 
        total: int, 
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate Wilson score confidence interval.
        
        Better than normal approximation for small samples.
        
        Args:
            successes: Number of positive outcomes
            total: Total observations
            confidence: Confidence level (default 0.95)
            
        Returns:
            (lower_bound, upper_bound) tuple
        """
        import math
        
        if total == 0:
            return (0.0, 1.0)
        
        # Z-score for confidence level
        z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
        
        p_hat = successes / total
        n = total
        
        # Wilson score interval
        denominator = 1 + z**2 / n
        center = (p_hat + z**2 / (2*n)) / denominator
        spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4*n)) / n) / denominator
        
        lower = max(0.0, center - spread)
        upper = min(1.0, center + spread)
        
        return (lower, upper)
    
    def create_hypothesis(
        self,
        hypothesis_type: str,
        game_type: str,
        description: str,
        level_number: Optional[int] = None,
        target_primitive: Optional[str] = None,
        suggested_composition: Optional[List[str]] = None,
        source_type: Optional[str] = None,
        prior: float = 0.5
    ) -> Optional[str]:
        """
        Create a new Bayesian hypothesis for potential operator synthesis.
        
        Args:
            hypothesis_type: 'PRIMITIVE_NEED', 'OPERATOR_SYNTHESIS', 'PATTERN_DISCOVERY'
            game_type: Game type this hypothesis applies to (e.g., 'sp80')
            description: Human-readable description
            level_number: Specific level (optional)
            target_primitive: Primitive to unlock if confirmed
            suggested_composition: List of primitives to compose if confirmed
            source_type: How hypothesis was generated ('failure_analysis', 'counterfactual', etc.)
            prior: Initial probability (default 0.5 = maximum uncertainty)
            
        Returns:
            hypothesis_id if created, None on failure
        """
        try:
            # Check for existing similar hypothesis
            existing_rows = self.db.execute_query("""
                SELECT hypothesis_id, evidence_for, evidence_against, posterior_probability
                FROM cods_bayesian_hypotheses
                WHERE game_type = ? AND description = ? AND status = 'active'
            """, (game_type, description))
            existing = existing_rows[0] if existing_rows else None
            
            if existing:
                # Hypothesis already exists - just return its ID
                h_id = existing['hypothesis_id']
                logger.debug(f"[BAYES] Hypothesis already exists: {h_id[:12]}")
                return h_id
            
            hypothesis_id = str(uuid.uuid4())
            
            self.db.execute_query("""
                INSERT INTO cods_bayesian_hypotheses
                (hypothesis_id, hypothesis_type, game_type, level_number, description,
                 target_primitive, suggested_composition, prior_probability, 
                 posterior_probability, source_type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                hypothesis_id,
                hypothesis_type,
                game_type,
                level_number,
                description,
                target_primitive,
                json.dumps(suggested_composition) if suggested_composition else None,
                prior,
                prior,  # Initially posterior = prior
                source_type
            ))
            
            logger.info(f"[BAYES] Created hypothesis: {description[:50]} (P={prior:.2f})")
            return hypothesis_id
            
        except Exception as e:
            logger.error(f"[BAYES] Failed to create hypothesis: {e}")
            return None
    
    def record_evidence(
        self,
        hypothesis_id: str,
        supports: bool,
        weight: float = 1.0,
        source_game: Optional[str] = None
    ) -> Optional[float]:
        """
        Record evidence for/against a hypothesis and update posterior.
        
        Args:
            hypothesis_id: ID of hypothesis to update
            supports: True if evidence supports hypothesis, False if contradicts
            weight: Evidence weight (default 1.0, can be higher for strong evidence)
            source_game: Game ID that provided this evidence
            
        Returns:
            Updated posterior probability, or None on failure
        """
        try:
            # Fetch current state
            current_rows = self.db.execute_query("""
                SELECT prior_probability, evidence_for, evidence_against, source_games
                FROM cods_bayesian_hypotheses
                WHERE hypothesis_id = ? AND status = 'active'
            """, (hypothesis_id,))
            current = current_rows[0] if current_rows else None
            
            if not current:
                logger.warning(f"[BAYES] Hypothesis not found or inactive: {hypothesis_id[:12]}")
                return None
            
            prior = current['prior_probability']
            evidence_for = current['evidence_for']
            evidence_against = current['evidence_against']
            source_games_json = current['source_games']
            
            # Update evidence counts
            evidence_weight = int(weight)  # Round to integer for counts
            if supports:
                evidence_for += evidence_weight
            else:
                evidence_against += evidence_weight
            
            # Calculate new posterior
            posterior = self._bayesian_update(prior, evidence_for, evidence_against)
            
            # Calculate confidence interval
            total_evidence = evidence_for + evidence_against
            conf_low, conf_high = self._wilson_confidence_interval(evidence_for, total_evidence)
            
            # Update source games
            source_games = json.loads(source_games_json) if source_games_json else []
            if source_game and source_game not in source_games:
                source_games.append(source_game)
                source_games = source_games[-50:]  # Keep last 50
            
            # Update database
            self.db.execute_query("""
                UPDATE cods_bayesian_hypotheses
                SET evidence_for = ?,
                    evidence_against = ?,
                    posterior_probability = ?,
                    confidence_low = ?,
                    confidence_high = ?,
                    source_games = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE hypothesis_id = ?
            """, (
                evidence_for,
                evidence_against,
                posterior,
                conf_low,
                conf_high,
                json.dumps(source_games),
                hypothesis_id
            ))
            
            logger.debug(
                f"[BAYES] Updated: +{evidence_weight if supports else 0}/-{evidence_weight if not supports else 0} "
                f"-> P={posterior:.3f} (n={total_evidence})"
            )
            
            return posterior
            
        except Exception as e:
            logger.error(f"[BAYES] Failed to record evidence: {e}")
            return None
    
    def observe_failure_pattern(
        self,
        game_type: str,
        level_number: int,
        failure_pattern: str,
        suggested_primitive: Optional[str] = None,
        suggested_composition: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Record a failure pattern and create/update hypothesis.
        
        This is the main entry point for failure-driven learning.
        Called when agents fail at a level with a specific pattern.
        
        Args:
            game_type: Game type (e.g., 'sp80')
            level_number: Level where failure occurred
            failure_pattern: Description of what went wrong (e.g., 'boundary_overflow')
            suggested_primitive: Oracle's suggestion for what primitive might help
            suggested_composition: Oracle's suggestion for operator composition
            
        Returns:
            hypothesis_id (new or existing)
        """
        # Create descriptive hypothesis
        description = f"{failure_pattern} at {game_type} L{level_number}"
        
        hypothesis_type = 'OPERATOR_SYNTHESIS' if suggested_composition else 'PRIMITIVE_NEED'
        
        # Create or get existing hypothesis
        hypothesis_id = self.create_hypothesis(
            hypothesis_type=hypothesis_type,
            game_type=game_type,
            description=description,
            level_number=level_number,
            target_primitive=suggested_primitive,
            suggested_composition=suggested_composition,
            source_type='failure_analysis'
        )
        
        if hypothesis_id:
            # Record this as supporting evidence (failure happened again)
            self.record_evidence(
                hypothesis_id=hypothesis_id,
                supports=True,  # Failure pattern recurring = evidence we need this capability
                weight=1.0,
                source_game=f"{game_type}-failure-L{level_number}"
            )
        
        return hypothesis_id
    
    def observe_success_pattern(
        self,
        game_type: str,
        level_number: int,
        hypothesis_id: Optional[str] = None
    ):
        """
        Record when a level is successfully completed.
        
        This provides counter-evidence against "we need X to pass this level".
        
        Args:
            game_type: Game type
            level_number: Level completed
            hypothesis_id: Specific hypothesis to update (optional)
        """
        try:
            if hypothesis_id:
                # Direct update
                self.record_evidence(
                    hypothesis_id=hypothesis_id,
                    supports=False,  # Success without the capability = counter-evidence
                    weight=1.0,
                    source_game=f"{game_type}-success-L{level_number}"
                )
            else:
                # Update all active hypotheses for this game/level
                hypotheses = self.db.execute_query("""
                    SELECT hypothesis_id
                    FROM cods_bayesian_hypotheses
                    WHERE game_type = ? 
                    AND (level_number = ? OR level_number IS NULL)
                    AND status = 'active'
                """, (game_type, level_number))
                
                for h in (hypotheses or []):
                    h_id = h['hypothesis_id'] if isinstance(h, dict) else h[0]
                    self.record_evidence(
                        hypothesis_id=h_id,
                        supports=False,
                        weight=0.5,  # Weaker counter-evidence for indirect match
                        source_game=f"{game_type}-success-L{level_number}"
                    )
                    
        except Exception as e:
            logger.error(f"[BAYES] Failed to record success: {e}")
    
    def get_confirmed_hypotheses(self, min_posterior: float = 0.85) -> List[BayesianHypothesis]:
        """
        Get hypotheses that have accumulated enough evidence to act on.
        
        Args:
            min_posterior: Minimum posterior probability (default 0.85)
            
        Returns:
            List of BayesianHypothesis objects ready for synthesis
        """
        try:
            rows = self.db.execute_query("""
                SELECT hypothesis_id, hypothesis_type, game_type, level_number,
                       description, target_primitive, suggested_composition,
                       prior_probability, evidence_for, evidence_against,
                       posterior_probability, confidence_low, confidence_high,
                       confirmation_threshold, refutation_threshold, status, source_type
                FROM cods_bayesian_hypotheses
                WHERE status = 'active'
                AND posterior_probability >= ?
                AND (evidence_for + evidence_against) >= 5
                ORDER BY posterior_probability DESC
            """, (min_posterior,))
            
            hypotheses = []
            for row in (rows or []):
                h = BayesianHypothesis(
                    hypothesis_id=row['hypothesis_id'],
                    hypothesis_type=row['hypothesis_type'],
                    game_type=row['game_type'],
                    level_number=row['level_number'],
                    description=row['description'],
                    target_primitive=row['target_primitive'],
                    suggested_composition=json.loads(row['suggested_composition']) if row['suggested_composition'] else None,
                    prior=row['prior_probability'],
                    evidence_for=row['evidence_for'],
                    evidence_against=row['evidence_against'],
                    posterior=row['posterior_probability'],
                    confidence_low=row['confidence_low'],
                    confidence_high=row['confidence_high'],
                    confirmation_threshold=row['confirmation_threshold'],
                    refutation_threshold=row['refutation_threshold'],
                    status=row['status'],
                    source_type=row['source_type']
                )
                hypotheses.append(h)
            
            return hypotheses
            
        except Exception as e:
            logger.error(f"[BAYES] Failed to get confirmed hypotheses: {e}")
            return []
    
    def synthesize_from_hypothesis(
        self,
        hypothesis: BayesianHypothesis,
        generation: int = 0,
        context: Optional[Any] = None,
        composer: Optional[Any] = None
    ) -> Optional[str]:
        """
        Synthesize a new operator from a confirmed hypothesis.
        
        This is where evolution happens: accumulated evidence
        triggers the creation of new cognitive capabilities.
        
        Args:
            hypothesis: Confirmed hypothesis to synthesize from
            generation: Current generation number
            context: Optional CODS context for agent_id
            composer: Optional OperatorComposer for creating composed operators
            
        Returns:
            operator_id if synthesis successful, None otherwise
        """
        try:
            if not hypothesis.is_confirmed():
                logger.warning(f"[SYNTH] Hypothesis not confirmed: P={hypothesis.posterior:.2f}")
                return None
            
            operator_id = None
            
            if hypothesis.suggested_composition and composer is not None:
                # Compose new operator from suggested primitives
                operator_name = f"synth_{hypothesis.game_type}_L{hypothesis.level_number or 'X'}_{uuid.uuid4().hex[:6]}"
                
                # Check that primitives are available
                available_primitives = []
                for prim_name in hypothesis.suggested_composition:
                    if self.unlock_manager:
                        status = self.unlock_manager.get_status(prim_name)
                        if status in [PrimitiveStatus.UNLOCKED, PrimitiveStatus.GRANDFATHERED]:
                            available_primitives.append(prim_name)
                            continue
                    # Fallback: assume available if no unlock manager
                    available_primitives.append(prim_name)
                
                if len(available_primitives) < 2:
                    logger.warning(f"[SYNTH] Not enough primitives for composition: {available_primitives}")
                    return None
                
                # Create the composed operator
                try:
                    composed_op = composer.compose_operator(
                        primitives=available_primitives,
                        name=operator_name
                    )
                    if composed_op:
                        operator_id = composed_op.operator_id
                        logger.info(
                            f"[SYNTH] Created operator: {operator_name} "
                            f"from {available_primitives}"
                        )
                        
                        # Distribute via viral package system
                        self._distribute_via_viral(
                            operator_id, operator_name, available_primitives,
                            generation, hypothesis, context
                        )
                            
                except Exception as e:
                    logger.error(f"[SYNTH] Composition failed: {e}")
                    return None
                    
            elif hypothesis.target_primitive and self.unlock_manager:
                # Unlock the suggested primitive
                sample_size = hypothesis.sample_size()
                success_rate = max(0.0, min(1.0, hypothesis.posterior))
                cross_game_rate = max(0.0, min(1.0, sample_size / 5.0))

                success = self.unlock_manager.attempt_unlock(
                    primitive_name=hypothesis.target_primitive,
                    pattern={
                        'source': 'bayesian_hypothesis',
                        'posterior': hypothesis.posterior,
                        'evidence_for': hypothesis.evidence_for,
                        'evidence_against': hypothesis.evidence_against,
                        'suggested_composition': hypothesis.suggested_composition,
                        'description': hypothesis.description
                    },
                    success_rate=success_rate,
                    cross_game_success_rate=cross_game_rate,
                    unlock_reason=f"Bayesian confirmation: {hypothesis.description}",
                    agent_id=context.agent_id if context else None,
                    generation=generation
                )
                if success:
                    operator_id = hypothesis.target_primitive
                    logger.info(f"[SYNTH] Unlocked primitive: {hypothesis.target_primitive}")
            
            if operator_id:
                # Mark hypothesis as synthesized
                self.db.execute_query("""
                    UPDATE cods_bayesian_hypotheses
                    SET status = 'synthesized',
                        synthesized_operator_id = ?,
                        synthesis_generation = ?,
                        synthesized_at = CURRENT_TIMESTAMP
                    WHERE hypothesis_id = ?
                """, (operator_id, generation, hypothesis.hypothesis_id))
                
                logger.info(
                    f"[SYNTH] Hypothesis synthesized: {hypothesis.description[:40]} "
                    f"-> {operator_id}"
                )
            
            return operator_id
            
        except Exception as e:
            logger.error(f"[SYNTH] Synthesis failed: {e}")
            return None
    
    def _distribute_via_viral(
        self,
        operator_id: str,
        operator_name: str,
        primitives: List[str],
        generation: int,
        hypothesis: BayesianHypothesis,
        context: Optional[Any]
    ):
        """Distribute synthesized operator via viral package system."""
        try:
            from engines.social.viral_package_engine import ViralPackageEngine
            viral_engine = ViralPackageEngine(self.db)
            
            # Get agent_id from context if available
            agent_id = context.agent_id if context else "system"
            
            package_id = viral_engine.create_viral_package_from_operator(
                operator_id=operator_id,
                operator_name=operator_name,
                primitives=primitives,
                agent_id=agent_id or 'unknown',
                generation=generation,
                game_type=hypothesis.game_type,
                level_number=hypothesis.level_number
            )
            if package_id:
                logger.info(f"[SYNTH->VIRAL] Operator distributed as package: {package_id}")
        except Exception as ve:
            logger.warning(f"[SYNTH->VIRAL] Failed to distribute operator: {ve}")
    
    def check_and_synthesize(
        self, 
        generation: int = 0,
        context: Optional[Any] = None,
        composer: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Check for confirmed hypotheses and synthesize operators.
        
        Call this at the end of each generation.
        
        Args:
            generation: Current generation number
            context: Optional CODS context
            composer: Optional OperatorComposer
            
        Returns:
            Summary of synthesis actions taken
        """
        results = {
            'hypotheses_checked': 0,
            'syntheses_triggered': 0,
            'operators_created': [],
            'primitives_unlocked': []
        }
        
        try:
            confirmed = self.get_confirmed_hypotheses()
            results['hypotheses_checked'] = len(confirmed)
            
            for hypothesis in confirmed:
                operator_id = self.synthesize_from_hypothesis(
                    hypothesis, generation, context, composer
                )
                
                if operator_id:
                    results['syntheses_triggered'] += 1
                    if hypothesis.suggested_composition:
                        results['operators_created'].append(operator_id)
                    else:
                        results['primitives_unlocked'].append(operator_id)
            
            if results['syntheses_triggered'] > 0:
                logger.info(
                    f"[SYNTH] Generation {generation}: "
                    f"{results['syntheses_triggered']} syntheses from "
                    f"{results['hypotheses_checked']} confirmed hypotheses"
                )
                
        except Exception as e:
            logger.error(f"[SYNTH] Check and synthesize failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_hypothesis_summary(self) -> Dict[str, Any]:
        """Get summary of current hypothesis state for logging."""
        try:
            stats_rows = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed,
                    SUM(CASE WHEN status = 'synthesized' THEN 1 ELSE 0 END) as synthesized,
                    SUM(CASE WHEN status = 'refuted' THEN 1 ELSE 0 END) as refuted,
                    AVG(posterior_probability) as avg_posterior,
                    MAX(posterior_probability) as max_posterior,
                    SUM(evidence_for + evidence_against) as total_evidence
                FROM cods_bayesian_hypotheses
            """)
            stats = stats_rows[0] if stats_rows else None
            
            if stats:
                return {
                    'total': stats['total'] or 0,
                    'active': stats['active'] or 0,
                    'confirmed': stats['confirmed'] or 0,
                    'synthesized': stats['synthesized'] or 0,
                    'refuted': stats['refuted'] or 0,
                    'avg_posterior': round(stats['avg_posterior'] or 0, 3),
                    'max_posterior': round(stats['max_posterior'] or 0, 3),
                    'total_evidence': stats['total_evidence'] or 0
                }
            return {}
            
        except Exception as e:
            logger.error(f"[BAYES] Failed to get summary: {e}")
            return {'error': str(e)}
    
    def prune_refuted_hypotheses(self, max_age_days: int = 30) -> int:
        """
        Clean up hypotheses that have been refuted or are too old.
        
        Args:
            max_age_days: Max age for inactive hypotheses
            
        Returns:
            Number of hypotheses removed
        """
        try:
            # Mark low-posterior hypotheses as refuted
            self.db.execute_query("""
                UPDATE cods_bayesian_hypotheses
                SET status = 'refuted'
                WHERE status = 'active'
                AND posterior_probability < refutation_threshold
                AND (evidence_for + evidence_against) >= 10
            """)
            
            # Delete old refuted hypotheses
            result = self.db.execute_query(f"""
                DELETE FROM cods_bayesian_hypotheses
                WHERE status = 'refuted'
                AND last_updated < datetime('now', '-{max_age_days} days')
            """)
            
            deleted = len(result) if isinstance(result, list) else (result.rowcount if hasattr(result, 'rowcount') else 0)
            
            if deleted > 0:
                logger.info(f"[BAYES] Pruned {deleted} refuted hypotheses")
            
            return deleted
            
        except Exception as e:
            logger.error(f"[BAYES] Prune failed: {e}")
            return 0
