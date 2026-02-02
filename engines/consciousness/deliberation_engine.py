import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Deliberation Engine - True Reasoning vs Gut Instinct
=====================================================

Extracted from i_thread.py (Jan 2026 refactor).

Implements System 1 (gut) and System 2 (deliberation) thinking.
Decides when to use each, manages deliberation budgets, and
logs the complete reasoning process.

From "True Reasoning vs Gut Instinct" Theory:
"The harder the problem, or the higher the stakes, the more rumination and
deliberation - the more reasoning, the more thinking about thinking about
what action to take next is required."

System 1 (Gut Instinct): Fast, automatic, often right, often wrong
System 2 (Deliberation): Slow, effortful, careful, but accurate

Rule 1: Disable pycache
Rule 2: All data in database
Rule 10: Leverage existing systems
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface
from engines.consciousness.i_thread_types import (
    DeliberationResult,
    GutInstinctResult,
    ReasoningLog,
)

# WorldModel used in type hints below but imported directly where needed

logger = logging.getLogger(__name__)


# =============================================================================
# DELIBERATION CONFIGURATION
# =============================================================================

DELIBERATION_CONFIG = {
    # Base budgets by context (seconds)
    'frontier_unknown': 30.0,    # Hard unknown territory - think hard
    'frontier_partial': 15.0,    # Frontier but some network knowledge
    'known_territory': 5.0,      # Known territory - less deliberation needed
    'following_sequence': 1.0,   # Just executing - minimal thought

    # Multipliers
    'performance_mult_range': (0.5, 1.5),  # Based on agent performance

    # Tension modifiers
    'tension_multipliers': {
        'panic': 0.2,       # Gut instinct dominates under extreme stress
        'stressed': 0.6,    # Reduced deliberation capacity
        'optimal': 1.0,     # Full deliberation capacity
        'relaxed': 0.9,     # Slightly reduced (not urgent enough)
        'complacent': 0.7,  # Reduced motivation to think deeply
    },

    # Action budget modifiers
    'action_budget_thresholds': {
        'critical': (0.0, 0.1, 0.3),   # <10% actions left
        'low': (0.1, 0.25, 0.6),       # 10-25% actions left
        'normal': (0.25, 1.0, 1.0),    # >25% actions - full deliberation
    },

    # Hard caps
    'min_deliberation': 0.5,     # Always at least half a second
    'max_deliberation': 60.0,    # Never more than 1 minute per action

    # When to skip deliberation entirely (use pure gut)
    'skip_deliberation_when': [
        'following_validated_sequence',
        'panic_state',
        'actions_critical',  # <10% actions remaining
    ]
}


def _get_resonance_detector():
    """Lazy import to avoid circular dependency."""
    try:
        from database_interface import DatabaseInterface
        from engines.social.resonance_detector import ResonanceDetector
        return ResonanceDetector(DatabaseInterface())
    except ImportError:
        return None


def _get_sequence_abstraction():
    """Lazy import to avoid circular dependency."""
    try:
        from engines.planning.sequence_abstraction import SequenceAbstraction
        return SequenceAbstraction()
    except ImportError:
        return None


class DeliberationEngine:
    """
    Engine for True Reasoning vs Gut Instinct.

    Implements System 1 (gut) and System 2 (deliberation) thinking.
    Decides when to use each, manages deliberation budgets, and
    logs the complete reasoning process.

    Integration with Consciousness Theory:
    - Uses Stream A/B weights from IThread
    - Uses tension state from MortalityState
    - Consults episodic memory for past attempts
    - Queries network hypotheses (Stream B)
    - Signals missing primitives to CODS

    Usage:
        engine = DeliberationEngine(db)
        result = engine.decide_action(
            agent_id='agent_123',
            game_context={...},
            available_actions=['ACTION1', 'ACTION2', ...],
            i_thread_state=state,
            mortality_state=mortality
        )
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Create reasoning log tables if they don't exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS action_reasoning_logs (
                    log_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    action_number INTEGER NOT NULL,

                    -- Context
                    is_frontier INTEGER DEFAULT 0,
                    network_traction REAL DEFAULT 0.0,
                    actions_remaining INTEGER,
                    actions_budget INTEGER,
                    tension_state TEXT,

                    -- Budget
                    deliberation_budget_seconds REAL,
                    budget_reason TEXT,

                    -- Gut instinct (JSON)
                    gut_action TEXT,
                    gut_confidence REAL,
                    gut_basis TEXT,
                    gut_response_time_ms REAL,
                    gut_stream_a_influence REAL,
                    gut_stream_b_influence REAL,
                    gut_pattern_matched TEXT,

                    -- Deliberation (JSON for complex fields)
                    deliberation_performed INTEGER DEFAULT 0,
                    deliberation_action TEXT,
                    deliberation_confidence REAL,
                    deliberation_time_seconds REAL,
                    deliberation_reasoning_steps TEXT,  -- JSON array
                    deliberation_changed_from_gut INTEGER DEFAULT 0,
                    deliberation_change_reason TEXT,
                    deliberation_skipped_reason TEXT,

                    -- Stream analysis
                    stream_conflict_detected INTEGER DEFAULT 0,
                    stream_conflict_resolution TEXT,

                    -- Missing primitive signal
                    missing_primitive_signal TEXT,

                    -- Final decision
                    final_action TEXT NOT NULL,
                    final_confidence REAL,
                    decision_source TEXT,
                    total_decision_time_ms REAL,

                    -- Outcome (updated after action)
                    outcome TEXT,
                    score_change REAL DEFAULT 0.0,

                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index for efficient queries
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_reasoning_logs_agent
                ON action_reasoning_logs(agent_id, game_type, created_at DESC)
            """)
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_reasoning_logs_game
                ON action_reasoning_logs(game_id, level, action_number)
            """)

        except Exception as e:
            logger.warning(f"Failed to create reasoning log tables: {e}")

    def compute_deliberation_budget(
        self,
        is_frontier: bool,
        network_traction: float,
        agent_performance: float,
        tension_state: str,
        actions_remaining_pct: float,
        following_sequence: bool = False
    ) -> Tuple[float, str]:
        """
        Compute deliberation time budget for this action.

        Args:
            is_frontier: Is this a frontier level (no winning sequences)?
            network_traction: How much network knows (0-1)
            agent_performance: Agent's performance percentile (0-1)
            tension_state: Current tension state
            actions_remaining_pct: Fraction of action budget remaining
            following_sequence: Are we following a validated sequence?

        Returns:
            Tuple of (budget_seconds, reason_string)
        """
        config = DELIBERATION_CONFIG

        # Check for skip conditions
        if following_sequence:
            return config['following_sequence'], "following validated sequence"

        if tension_state == 'panic':
            return config['min_deliberation'], "panic state - gut only"

        if actions_remaining_pct < 0.1:
            return config['min_deliberation'], "critical action budget - decide fast"

        # Base budget by context
        if is_frontier and network_traction < 0.2:
            base = config['frontier_unknown']
            reason = "frontier + no network knowledge"
        elif is_frontier:
            base = config['frontier_partial']
            reason = f"frontier + partial network ({network_traction:.0%})"
        else:
            base = config['known_territory']
            reason = "known territory"

        # Performance multiplier
        min_mult, max_mult = config['performance_mult_range']
        perf_mult = min_mult + (agent_performance * (max_mult - min_mult))

        # Tension modifier
        tension_mult = config['tension_multipliers'].get(tension_state, 1.0)

        # Action budget modifier
        action_mult = 1.0
        for threshold_name, (low, high, mult) in config['action_budget_thresholds'].items():
            if low <= actions_remaining_pct < high:
                action_mult = mult
                break

        # Compute final budget
        budget = base * perf_mult * tension_mult * action_mult

        # Hard caps
        budget = max(config['min_deliberation'], min(config['max_deliberation'], budget))

        # Extend reason
        reason += f" | perf={agent_performance:.0%} | tension={tension_state} | actions={actions_remaining_pct:.0%}"

        return budget, reason

    def capture_gut_instinct(
        self,
        available_actions: List[str],
        recent_actions: List[str],
        recent_outcomes: List[str],
        w_a: float,
        w_b: float,
        network_recommendation: Optional[str] = None,
        private_preference: Optional[str] = None
    ) -> GutInstinctResult:
        """
        Capture the immediate gut response before deliberation.

        This is System 1 - fast, automatic pattern matching.

        Args:
            available_actions: List of valid actions
            recent_actions: Last N actions taken
            recent_outcomes: Outcomes of last N actions
            w_a: Stream A weight
            w_b: Stream B weight
            network_recommendation: What Stream B suggests
            private_preference: What Stream A suggests

        Returns:
            GutInstinctResult with the automatic response
        """
        import random

        start_time = time.time()

        action = None
        basis = "random"
        pattern_matched = None
        habit_strength = 0.0

        # Stream influences
        stream_a_influence = w_a / (w_a + w_b) if (w_a + w_b) > 0 else 0.5
        stream_b_influence = w_b / (w_a + w_b) if (w_a + w_b) > 0 else 0.5

        # Pattern 1: Recent success momentum
        if len(recent_actions) >= 2 and len(recent_outcomes) >= 2:
            if recent_outcomes[-1] == 'positive' and recent_outcomes[-2] == 'positive':
                # Keep doing what worked
                if recent_actions[-1] in available_actions:
                    action = recent_actions[-1]
                    basis = "success momentum - repeating last successful action"
                    pattern_matched = "consecutive_success"
                    habit_strength = 0.7

        # Pattern 2: Network recommendation (if trusted)
        if action is None and network_recommendation and w_b > 0.5:
            if network_recommendation in available_actions:
                action = network_recommendation
                basis = f"network recommendation (trust={w_b:.2f})"
                pattern_matched = "network_trust"
                habit_strength = w_b

        # Pattern 3: Private preference (if trusted)
        if action is None and private_preference and w_a > 0.5:
            if private_preference in available_actions:
                action = private_preference
                basis = f"private experience preference (trust={w_a:.2f})"
                pattern_matched = "self_trust"
                habit_strength = w_a

        # Pattern 4: Avoid recent failures
        if action is None and recent_actions and recent_outcomes:
            failed_actions = [
                a for a, o in zip(recent_actions[-5:], recent_outcomes[-5:])
                if o == 'negative' and a in available_actions
            ]
            safe_actions = [a for a in available_actions if a not in failed_actions]
            if safe_actions:
                action = random.choice(safe_actions)
                basis = "avoiding recent failures"
                pattern_matched = "failure_avoidance"
                habit_strength = 0.3

        # Fallback: Random
        if action is None:
            action = random.choice(available_actions) if available_actions else "ACTION1"
            basis = "no pattern - random selection"
            habit_strength = 0.0

        # Compute confidence based on pattern strength
        confidence = 0.3 + (habit_strength * 0.5)  # 0.3 to 0.8 range

        response_time_ms = (time.time() - start_time) * 1000

        return GutInstinctResult(
            action=action,
            confidence=confidence,
            basis=basis,
            response_time_ms=response_time_ms,
            stream_a_influence=stream_a_influence,
            stream_b_influence=stream_b_influence,
            pattern_matched=pattern_matched,
            habit_strength=habit_strength
        )

    def conduct_deliberation(
        self,
        gut_result: GutInstinctResult,
        available_actions: List[str],
        budget_seconds: float,
        game_context: Dict[str, Any],
        agent_id: str,
        w_a: float,
        w_b: float,
        world_model: Optional[Any] = None,  # WorldModel for counterfactual simulation
        _current_frame: Optional[List[List[int]]] = None  # Reserved for pattern matching
    ) -> DeliberationResult:
        """
        Conduct careful, effortful deliberation (System 2).

        This examines evidence, consults streams, tests theories,
        and produces a reasoned decision. NOW WITH WORLD MODEL SIMULATION.

        TRUE DELIBERATION: Uses WorldModel.predict_state() to mentally
        simulate each candidate action BEFORE choosing. This is counterfactual
        reasoning - "what would happen if I did X?"

        Args:
            gut_result: The initial gut response
            available_actions: Valid actions
            budget_seconds: Time budget for deliberation
            game_context: Context including game_type, level, frame, etc.
            agent_id: Agent performing deliberation
            w_a, w_b: Stream weights
            world_model: WorldModel instance for counterfactual simulation
            _current_frame: Reserved for future pattern matching (unused)

        Returns:
            DeliberationResult with reasoned decision
        """
        start_time = time.time()
        reasoning_steps = []

        game_type = game_context.get('game_type', 'unknown')
        level = game_context.get('level', 1)

        # Initialize tracking
        examined_past = 0
        examined_hypotheses = 0
        examined_primitives = 0
        examined_memories = 0
        stream_a_consulted = False
        stream_b_consulted = False
        stream_conflict = False
        conflict_resolution = None
        theory_tested = None
        theory_result = None
        missing_primitive = None

        # Cognitive experience tracking
        resonance_felt = None
        deja_vu_strength = 0.0
        insight_felt = None
        understanding_confidence = 0.0
        analytical_proposal = None

        # Step 1: Acknowledge gut response
        reasoning_steps.append(f"Gut suggests {gut_result.action} ({gut_result.basis})")

        # Step 1.5: Examine episodic memories
        try:
            memories = self._query_episodic_memories(agent_id, game_type)
            examined_memories = len(memories)

            if memories:
                for memory in memories[:5]:
                    if memory.get('episode_type') == 'breakthrough':
                        reasoning_steps.append(
                            f"Memory (breakthrough): \"{memory.get('summary', '')[:60]}...\""
                        )
                    elif memory.get('episode_type') == 'frustration':
                        reasoning_steps.append(
                            f"Memory (frustration): \"{memory.get('summary', '')[:60]}...\""
                        )

                    if memory.get('belief_formed'):
                        reasoning_steps.append(
                            f"Belief from memory: \"{memory.get('belief_formed')}\""
                        )
        except Exception:
            pass

        # Step 2: Consult Stream A (private experience)
        stream_a_consulted = True
        best_action = None
        best_ratio = 0.0
        try:
            past_attempts = self._query_past_attempts(agent_id, game_type, level)
            examined_past = len(past_attempts)

            if past_attempts:
                action_outcomes = {}
                for attempt in past_attempts[:20]:
                    act = attempt.get('action', '')
                    outcome = attempt.get('outcome', 'neutral')
                    if act not in action_outcomes:
                        action_outcomes[act] = {'positive': 0, 'negative': 0, 'neutral': 0}
                    action_outcomes[act][outcome] = action_outcomes[act].get(outcome, 0) + 1

                worst_action = None
                worst_ratio = 1.0

                for act, outcomes in action_outcomes.items():
                    total = sum(outcomes.values())
                    if total >= 2:
                        pos_ratio = outcomes['positive'] / total
                        if pos_ratio > best_ratio and act in available_actions:
                            best_ratio = pos_ratio
                            best_action = act
                        if pos_ratio < worst_ratio and act in available_actions:
                            worst_ratio = pos_ratio
                            worst_action = act

                if best_action:
                    reasoning_steps.append(f"Stream A: {best_action} has {best_ratio:.0%} success rate from {examined_past} attempts")
                if worst_action and worst_action != best_action:
                    reasoning_steps.append(f"Stream A: Avoid {worst_action} ({worst_ratio:.0%} success rate)")

        except Exception as e:
            reasoning_steps.append(f"Stream A query failed: {str(e)[:50]}")

        # Step 3: Consult Stream B (network wisdom)
        stream_b_consulted = True
        network_recommendation = None
        try:
            hypotheses = self._query_network_hypotheses(game_type, level)
            examined_hypotheses = len(hypotheses)

            if hypotheses:
                best_hyp = max(hypotheses, key=lambda h: h.get('reliability', 0))
                if best_hyp.get('recommended_action') in available_actions:
                    network_recommendation = best_hyp.get('recommended_action')
                    reasoning_steps.append(
                        f"Stream B: Network recommends {network_recommendation} "
                        f"(reliability={best_hyp.get('reliability', 0):.2f})"
                    )
            else:
                reasoning_steps.append("Stream B: No network data for this level")

        except Exception as e:
            reasoning_steps.append(f"Stream B query failed: {str(e)[:50]}")

        # Phase 2: Resonance as Recognition (Deja Vu)
        try:
            resonance_detector = _get_resonance_detector()
            if resonance_detector:
                resonant_patterns = resonance_detector.detect_resonance()
                relevant_resonances = [
                    p for p in resonant_patterns
                    if game_type in p.get('game_types', [])
                ]

                if relevant_resonances:
                    strongest = max(relevant_resonances, key=lambda p: p.get('resonance_score', 0))
                    deja_vu_strength = min(1.0, strongest.get('resonance_score', 0) / 5.0)

                    if deja_vu_strength > 0.3:
                        resonance_felt = {
                            'source': 'collective_memory',
                            'pattern_hash': strongest.get('pattern_hash'),
                            'agents_who_know': strongest.get('independent_discoverers', 0),
                            'roles_agreed': strongest.get('roles_found', []),
                            'feeling': 'recognition'
                        }
                        reasoning_steps.append(
                            f"[FEELING: RECOGNITION] Deja vu (strength={deja_vu_strength:.2f}): "
                            f"Pattern known by {resonance_felt['agents_who_know']} agents"
                        )
        except Exception:
            pass

        # Phase 3: Abstraction as Understanding (Insight)
        try:
            abstraction_engine = _get_sequence_abstraction()
            if abstraction_engine:
                relations = abstraction_engine.get_few_shot_relations(game_type, level)

                if relations and relations.get('confidence', 0) > 0.5:
                    understanding_confidence = relations.get('confidence', 0)
                    invariants = relations.get('invariants', [])

                    if invariants:
                        insight_felt = {
                            'source': 'pattern_memory',
                            'invariant_positions': len(invariants),
                            'variant_regions': len(relations.get('variant_regions', [])),
                            'template_confidence': understanding_confidence,
                            'feeling': 'understanding'
                        }

                        for inv in invariants:
                            action_type = inv.get('action')
                            if action_type:
                                proposed = f"ACTION{action_type}"
                                if proposed in available_actions:
                                    analytical_proposal = {
                                        'persona': 'analytical',
                                        'action': proposed,
                                        'confidence': understanding_confidence,
                                        'reasoning': f"Pattern invariant at position {inv.get('position')}: ACTION{action_type}",
                                        'feeling': 'understanding'
                                    }
                                    break

                        reasoning_steps.append(
                            f"[FEELING: UNDERSTANDING] Insight (confidence={understanding_confidence:.2f}): "
                            f"Pattern has {len(invariants)} invariants"
                        )

                        if analytical_proposal:
                            reasoning_steps.append(
                                f"[ANALYTICAL PERSONA] Based on pattern: {analytical_proposal['action']}"
                            )
        except Exception:
            pass

        # Step 4: Detect stream conflict
        private_recommendation = best_action if best_action else gut_result.action

        if network_recommendation and private_recommendation:
            if network_recommendation != private_recommendation:
                stream_conflict = True
                reasoning_steps.append(
                    f"STREAM CONFLICT: Stream A says {private_recommendation}, "
                    f"Stream B says {network_recommendation}"
                )

                if w_a > w_b:
                    conflict_resolution = f"Trusting Stream A (w_a={w_a:.2f} > w_b={w_b:.2f})"
                elif w_b > w_a:
                    conflict_resolution = f"Trusting Stream B (w_b={w_b:.2f} > w_a={w_a:.2f})"
                else:
                    conflict_resolution = "Weights equal - using gut as tiebreaker"
                reasoning_steps.append(f"Resolution: {conflict_resolution}")

        # Step 5: Examine available primitives
        try:
            primitives = self._get_available_primitives(agent_id)
            examined_primitives = len(primitives)

            if examined_past > 10 and best_ratio < 0.3:
                missing_primitive = f"Pattern recognition failing on {game_type} level {level}"
                reasoning_steps.append(f"Signal to CODS: May need new primitive - {missing_primitive}")

        except Exception:
            pass

        # Step 5.5: World Model Simulation
        simulations_run = 0
        best_simulated_action = None
        best_simulated_score = -999.0
        simulation_used = False
        simulation_predictions = {}

        if world_model is not None:
            try:
                reasoning_steps.append("[SIMULATION] Running counterfactual predictions...")

                for action_str in available_actions:
                    try:
                        action_int = int(action_str.replace('ACTION', ''))
                    except ValueError:
                        continue

                    try:
                        predicted_state = world_model.predict_state([action_int])
                        simulations_run += 1

                        current_score = world_model.state.score if world_model.state else 0
                        predicted_score = predicted_state.score if predicted_state else current_score
                        score_change = predicted_score - current_score

                        predicted_agent = predicted_state.get_agent() if predicted_state else None
                        predicted_pos = predicted_agent.position if predicted_agent else None

                        surprise_risk = 0.0
                        if hasattr(world_model, 'beliefs') and world_model.beliefs:
                            for belief in world_model.beliefs.values():
                                content = belief.content if hasattr(belief, 'content') else {}
                                if content.get('trigger_action') == action_int:
                                    surprise_risk = max(surprise_risk, 1.0 - belief.confidence)

                        simulation_predictions[action_str] = {
                            'score_change': score_change,
                            'predicted_position': predicted_pos,
                            'surprise_risk': surprise_risk,
                            'is_positive': score_change > 0
                        }

                        effective_score = score_change - (surprise_risk * 0.5)
                        if effective_score > best_simulated_score:
                            best_simulated_score = effective_score
                            best_simulated_action = action_str

                    except Exception as pred_err:
                        reasoning_steps.append(f"[SIM] {action_str} prediction failed: {str(pred_err)[:30]}")
                        continue

                if simulations_run > 0:
                    positive_actions = [a for a, p in simulation_predictions.items() if p.get('is_positive')]

                    if positive_actions:
                        reasoning_steps.append(
                            f"[SIMULATION] Positive outcomes predicted for: {', '.join(positive_actions)}"
                        )

                    if best_simulated_action:
                        pred = simulation_predictions.get(best_simulated_action, {})
                        reasoning_steps.append(
                            f"[SIMULATION] Best: {best_simulated_action} "
                            f"(+{pred.get('score_change', 0):.1f} score, "
                            f"{pred.get('surprise_risk', 0):.1%} risk)"
                        )
                else:
                    reasoning_steps.append("[SIMULATION] No valid predictions generated")

            except Exception as sim_err:
                reasoning_steps.append(f"[SIMULATION] Failed: {str(sim_err)[:50]}")
        else:
            reasoning_steps.append("[SIMULATION] No world model available - using statistical reasoning only")

        # Step 6: Form theory and test prediction
        if examined_past >= 5:
            theory_tested = f"Theory: Consistent action selection improves outcomes on {game_type}"
            theory_result = "pending_verification"
            reasoning_steps.append(f"Testing: {theory_tested}")

        # Step 7: Make final decision with TRM-INSPIRED ITERATIVE REFINEMENT
        time_spent = time.time() - start_time
        time_remaining = budget_seconds - time_spent

        action_scores: Dict[str, float] = {a: 0.0 for a in available_actions}
        action_sources: Dict[str, List[str]] = {a: [] for a in available_actions}

        # Seed with gut instinct
        if gut_result.action in action_scores:
            action_scores[gut_result.action] += gut_result.confidence * 0.3
            action_sources[gut_result.action].append(f"gut:{gut_result.confidence:.2f}")

        # Adaptive refinement passes
        if time_remaining > 10.0:
            max_refinement_passes = 4
        elif time_remaining > 3.0:
            max_refinement_passes = 3
        elif time_remaining > 1.0:
            max_refinement_passes = 2
        else:
            max_refinement_passes = 1

        convergence_threshold = 0.05
        previous_best_score = -1.0
        refinement_passes_used = 0
        convergence_achieved = False

        for refinement_pass in range(max_refinement_passes):
            refinement_passes_used += 1

            if refinement_pass == 0:
                # Source 1: Stream A
                if best_action and best_action in action_scores:
                    score_boost = best_ratio * 0.4
                    action_scores[best_action] += score_boost
                    action_sources[best_action].append(f"stream_a:{score_boost:.2f}")

                # Source 2: Stream B
                if network_recommendation and network_recommendation in action_scores:
                    score_boost = w_b * 0.4
                    action_scores[network_recommendation] += score_boost
                    action_sources[network_recommendation].append(f"stream_b:{score_boost:.2f}")

                # Source 3: Simulation predictions
                for action_str, pred in simulation_predictions.items():
                    if action_str in action_scores:
                        score_change = pred.get('score_change', 0)
                        risk = pred.get('surprise_risk', 0.5)
                        sim_score = (score_change * 0.1) - (risk * 0.2)
                        action_scores[action_str] += sim_score
                        if abs(sim_score) > 0.01:
                            action_sources[action_str].append(f"sim:{sim_score:.2f}")

                # Source 4: Analytical persona
                if analytical_proposal and analytical_proposal.get('action') in action_scores:
                    conf = analytical_proposal.get('confidence', 0.5)
                    action_scores[analytical_proposal['action']] += conf * 0.3
                    action_sources[analytical_proposal['action']].append(f"pattern:{conf:.2f}")

                # Source 5: Resonance/deja vu
                if deja_vu_strength > 0.3 and resonance_felt:
                    roles = resonance_felt.get('roles_agreed', [])
                    for action_str in action_scores:
                        action_num = action_str.replace('ACTION', '')
                        if action_num in str(roles):
                            action_scores[action_str] += deja_vu_strength * 0.2
                            action_sources[action_str].append(f"resonance:{deja_vu_strength:.2f}")

            # Consensus boost each pass
            for action_str in action_scores:
                source_count = len(action_sources.get(action_str, []))
                if source_count >= 2:
                    consensus_boost = (source_count - 1) * 0.02
                    action_scores[action_str] += consensus_boost

            # Check convergence
            current_best = max(action_scores.values()) if action_scores else 0
            if refinement_pass > 0 and abs(current_best - previous_best_score) < convergence_threshold:
                reasoning_steps.append(f"[REFINEMENT] Converged at pass {refinement_pass + 1}")
                convergence_achieved = True
                break
            previous_best_score = current_best

        consensus_actions_list = [
            action_str for action_str, sources in action_sources.items()
            if len(sources) >= 2
        ]

        if refinement_passes_used > 1:
            top_3 = dict(sorted(action_scores.items(), key=lambda x: -x[1])[:3])
            reasoning_steps.append(f"[REFINEMENT] {refinement_passes_used} passes, top: {top_3}")

        final_action = max(action_scores, key=action_scores.get) if action_scores else gut_result.action
        change_reason = None
        changed_from_gut = False

        # Refinement confidence
        sorted_scores = sorted(action_scores.values(), reverse=True)
        refinement_confidence = 0.0
        if len(sorted_scores) >= 2 and sorted_scores[0] > 0:
            refinement_confidence = (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0]

        # Simulation override
        if best_simulated_action and best_simulated_score > 0:
            pred = simulation_predictions.get(best_simulated_action, {})
            if pred.get('surprise_risk', 1.0) < 0.3 and refinement_confidence < 0.3:
                final_action = best_simulated_action
                change_reason = f"Simulation override: +{pred.get('score_change', 0):.1f} predicted"
                simulation_used = True
                reasoning_steps.append(f"[DECISION] Simulation overrides uncertain refinement: {final_action}")

        # Defensive check
        if not simulation_used and gut_result.action == final_action and gut_result.action in simulation_predictions:
            gut_pred = simulation_predictions[gut_result.action]
            if gut_pred.get('score_change', 0) < -1 or gut_pred.get('surprise_risk', 0) > 0.8:
                sorted_actions = sorted(action_scores.items(), key=lambda x: -x[1])
                for alt_action, alt_score in sorted_actions:
                    if alt_action != gut_result.action:
                        alt_pred = simulation_predictions.get(alt_action, {})
                        if alt_pred.get('surprise_risk', 0.5) < 0.6:
                            final_action = alt_action
                            change_reason = f"Defensive: avoiding gut ({gut_result.action}) due to high risk"
                            simulation_used = True
                            reasoning_steps.append(f"[DECISION] Defensive switch to: {final_action}")
                            break

        if final_action != gut_result.action:
            changed_from_gut = True
            if not change_reason:
                sources = action_sources.get(final_action, [])
                if sources:
                    change_reason = f"Iterative refinement ({', '.join(sources[:2])})"
                else:
                    change_reason = "Deliberation found better option"

        # Compute confidence
        base_confidence = 0.5 + refinement_confidence * 0.3

        if best_ratio > 0:
            base_confidence = max(base_confidence, best_ratio * 0.8)
        if examined_hypotheses > 0:
            base_confidence += 0.1
        if not stream_conflict:
            base_confidence += 0.1
        if examined_memories > 0:
            base_confidence += 0.05
        if simulation_used and simulations_run > 0:
            base_confidence += 0.15
            reasoning_steps.append("[CONFIDENCE] +15% boost from world model simulation")
        if deja_vu_strength > 0.5:
            base_confidence += 0.05
            reasoning_steps.append("[CONFIDENCE] +5% boost from strong recognition")
        if understanding_confidence > 0.6:
            base_confidence += 0.08
            reasoning_steps.append("[CONFIDENCE] +8% boost from pattern understanding")

        final_confidence = min(0.95, base_confidence)

        # Current feeling
        current_feeling = 'neutral'
        if simulation_used and simulations_run > 0:
            current_feeling = 'expectation'
        if deja_vu_strength > 0.5:
            current_feeling = 'recognition'
        if understanding_confidence > 0.6:
            current_feeling = 'understanding'

        # Build predictions_felt
        predictions_felt = []
        for action_str, pred in simulation_predictions.items():
            predictions_felt.append({
                'action': action_str,
                'expected_outcome': pred.get('score_change', 0),
                'confidence': 1.0 - pred.get('surprise_risk', 0.5),
                'feeling': 'expectation'
            })

        time_spent = time.time() - start_time
        reasoning_steps.append(f"Final decision: {final_action} (confidence={final_confidence:.2f})")

        return DeliberationResult(
            action=final_action,
            confidence=final_confidence,
            time_spent_seconds=time_spent,
            budget_used_seconds=min(time_spent, budget_seconds),
            budget_available_seconds=budget_seconds,
            examined_past_attempts=examined_past,
            examined_network_hypotheses=examined_hypotheses,
            examined_primitives=examined_primitives,
            examined_episodic_memories=examined_memories,
            stream_a_consulted=stream_a_consulted,
            stream_b_consulted=stream_b_consulted,
            reasoning_steps=reasoning_steps,
            stream_conflict_detected=stream_conflict,
            stream_conflict_resolution=conflict_resolution,
            theory_tested=theory_tested,
            theory_result=theory_result,
            missing_primitive_signal=missing_primitive,
            changed_from_gut=changed_from_gut,
            gut_action=gut_result.action if changed_from_gut else None,
            change_reason=change_reason,
            simulations_run=simulations_run,
            best_simulated_action=best_simulated_action,
            best_simulated_score=best_simulated_score,
            simulation_used=simulation_used,
            refinement_passes=refinement_passes_used,
            refinement_confidence=refinement_confidence,
            consensus_actions=consensus_actions_list,
            convergence_achieved=convergence_achieved,
            predictions_felt=predictions_felt,
            expectation_match=None,
            surprise_felt=0.0,
            resonance_felt=resonance_felt,
            deja_vu_strength=deja_vu_strength,
            insight_felt=insight_felt,
            understanding_confidence=understanding_confidence,
            current_feeling=current_feeling
        )

    def _query_episodic_memories(
        self,
        agent_id: str,
        game_type: str
    ) -> List[Dict[str, Any]]:
        """Query episodic memories (thoughts from previous games)."""
        try:
            results = self.db.execute_query("""
                SELECT memory_id, episode_type, summary, belief_formed,
                       rule_discovered, emotional_valence, significance
                FROM i_thread_episodic_memories
                WHERE agent_id = ? AND game_type = ?
                ORDER BY significance DESC, created_at DESC
                LIMIT 10
            """, (agent_id, game_type))
            return [dict(r) for r in results] if results else []
        except Exception:
            return []

    def _query_past_attempts(
        self,
        agent_id: str,
        game_type: str,
        level: int
    ) -> List[Dict[str, Any]]:
        """Query past action outcomes for this agent on this game/level."""
        try:
            results = self.db.execute_query("""
                SELECT action_taken as action,
                       CASE WHEN score_delta > 0 THEN 'positive'
                            WHEN score_delta < 0 THEN 'negative'
                            ELSE 'neutral' END as outcome,
                       score_delta
                FROM action_traces
                WHERE agent_id = ? AND game_type = ? AND level_number = ?
                ORDER BY created_at DESC
                LIMIT 50
            """, (agent_id, game_type, level))
            return [dict(r) for r in results] if results else []
        except Exception:
            return []

    def _query_network_hypotheses(
        self,
        game_type: str,
        level: int
    ) -> List[Dict[str, Any]]:
        """Query network hypotheses for this game/level."""
        try:
            results = self.db.execute_query("""
                SELECT hypothesis_id,
                       controlled_object as recommended_action,
                       reliability_score as reliability,
                       validation_attempts
                FROM network_object_control_hypotheses
                WHERE game_type = ?
                  AND level_number = ?
                  AND is_active = 1
                  AND (validation_attempts >= 3 OR validated_by_win = 1)
                ORDER BY reliability_score DESC
                LIMIT 10
            """, (game_type, level))
            return [dict(r) for r in results] if results else []
        except Exception:
            return []

    def _get_available_primitives(self, agent_id: str) -> List[str]:
        """Get list of primitives available to this agent."""
        return [
            'detect_novelty', 'detect_motion', 'object_permanence',
            'pattern_matching', 'spatial_reasoning', 'temporal_tracking'
        ]

    def decide_action(
        self,
        agent_id: str,
        game_context: Dict[str, Any],
        available_actions: List[str],
        i_thread_state: Optional[Any] = None,
        mortality_state: Optional['MortalityState'] = None,
        recent_actions: Optional[List[str]] = None,
        recent_outcomes: Optional[List[str]] = None,
        network_recommendation: Optional[str] = None,
        private_preference: Optional[str] = None,
        following_sequence: bool = False,
        world_model: Optional['WorldModel'] = None
    ) -> ReasoningLog:
        """
        Main entry point: Decide which action to take.

        Captures gut instinct, optionally performs deliberation,
        and returns complete reasoning log.

        Args:
            agent_id: Agent making decision
            game_context: Dict with game_id, game_type, level, frame, etc.
            available_actions: Valid actions
            i_thread_state: Current IThread state (for stream weights)
            mortality_state: Current mortality state (for tension)
            recent_actions: Last N actions taken
            recent_outcomes: Outcomes of those actions
            network_recommendation: Stream B suggestion
            private_preference: Stream A suggestion
            following_sequence: Are we executing a known sequence?
            world_model: WorldModel for counterfactual simulation

        Returns:
            ReasoningLog with complete decision record
        """
        decision_start = datetime.now()
        start_time = time.time()

        # Extract context
        game_id = game_context.get('game_id', 'unknown')
        game_type = game_context.get('game_type', 'unknown')
        level = game_context.get('level', 1)
        action_number = game_context.get('action_number', 0)
        actions_remaining = game_context.get('actions_remaining', 400)
        actions_budget = game_context.get('actions_budget', 400)
        is_frontier = game_context.get('is_frontier', True)
        network_traction = game_context.get('network_traction', 0.0)

        # Get stream weights
        w_a = i_thread_state.w_a if i_thread_state else 0.5
        w_b = i_thread_state.w_b if i_thread_state else 0.5

        # Get tension state
        tension_state = 'optimal'
        if mortality_state:
            pressure = mortality_state.compute_existential_pressure()
            tension_result = mortality_state.compute_tension_state(pressure)
            tension_state = tension_result.get('state', 'optimal')

        # Compute agent performance
        agent_performance = 0.5
        try:
            perf_result = self.db.execute_query("""
                SELECT AVG(CASE WHEN final_score > 0 THEN 1.0 ELSE 0.0 END) as win_rate
                FROM game_results
                WHERE agent_id = ? AND created_at > datetime('now', '-7 days')
            """, (agent_id,))
            if perf_result and perf_result[0]['win_rate']:
                agent_performance = float(perf_result[0]['win_rate'])
        except Exception:
            pass

        # Compute deliberation budget
        actions_remaining_pct = actions_remaining / actions_budget if actions_budget > 0 else 1.0
        budget_seconds, budget_reason = self.compute_deliberation_budget(
            is_frontier=is_frontier,
            network_traction=network_traction,
            agent_performance=agent_performance,
            tension_state=tension_state,
            actions_remaining_pct=actions_remaining_pct,
            following_sequence=following_sequence
        )

        # Step 1: Always capture gut instinct
        gut_result = self.capture_gut_instinct(
            available_actions=available_actions,
            recent_actions=recent_actions or [],
            recent_outcomes=recent_outcomes or [],
            w_a=w_a,
            w_b=w_b,
            network_recommendation=network_recommendation,
            private_preference=private_preference
        )

        # Step 2: Decide whether to deliberate
        deliberation_result = None
        skip_reason = None

        should_skip = (
            following_sequence or
            tension_state == 'panic' or
            actions_remaining_pct < 0.1 or
            budget_seconds <= DELIBERATION_CONFIG['min_deliberation']
        )

        if should_skip:
            if following_sequence:
                skip_reason = "Following validated sequence"
            elif tension_state == 'panic':
                skip_reason = "Panic state - relying on instinct"
            elif actions_remaining_pct < 0.1:
                skip_reason = "Critical action budget - no time to think"
            else:
                skip_reason = "Minimal budget allocated"
        else:
            # Conduct deliberation
            deliberation_result = self.conduct_deliberation(
                gut_result=gut_result,
                available_actions=available_actions,
                budget_seconds=budget_seconds,
                game_context=game_context,
                agent_id=agent_id,
                w_a=w_a,
                w_b=w_b,
                world_model=world_model
            )

        # Determine final action
        if deliberation_result:
            final_action = deliberation_result.action
            final_confidence = deliberation_result.confidence
            decision_source = 'deliberation' if deliberation_result.changed_from_gut else 'gut_confirmed'
        else:
            final_action = gut_result.action
            final_confidence = gut_result.confidence
            decision_source = 'gut'

        # Calculate total time
        total_time_ms = (time.time() - start_time) * 1000

        # Create reasoning log
        log_id = f"rl_{agent_id}_{game_id}_{level}_{action_number}_{int(time.time()*1000)}"

        reasoning_log = ReasoningLog(
            log_id=log_id,
            agent_id=agent_id,
            game_id=game_id,
            game_type=game_type,
            level=level,
            action_number=action_number,
            is_frontier=is_frontier,
            network_traction=network_traction,
            actions_remaining=actions_remaining,
            actions_budget=actions_budget,
            tension_state=tension_state,
            deliberation_budget_seconds=budget_seconds,
            budget_reason=budget_reason,
            gut=gut_result,
            deliberation=deliberation_result,
            deliberation_skipped_reason=skip_reason,
            final_action=final_action,
            final_confidence=final_confidence,
            decision_source=decision_source,
            decision_started_at=decision_start,
            decision_completed_at=datetime.now(),
            total_decision_time_ms=total_time_ms
        )

        # Store in database
        self._store_reasoning_log(reasoning_log)

        return reasoning_log

    def _store_reasoning_log(self, log: ReasoningLog) -> None:
        """Store reasoning log in database."""
        import json

        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO action_reasoning_logs (
                    log_id, agent_id, game_id, game_type, level, action_number,
                    is_frontier, network_traction, actions_remaining, actions_budget,
                    tension_state, deliberation_budget_seconds, budget_reason,
                    gut_action, gut_confidence, gut_basis, gut_response_time_ms,
                    gut_stream_a_influence, gut_stream_b_influence, gut_pattern_matched,
                    deliberation_performed, deliberation_action, deliberation_confidence,
                    deliberation_time_seconds, deliberation_reasoning_steps,
                    deliberation_changed_from_gut, deliberation_change_reason,
                    deliberation_skipped_reason,
                    stream_conflict_detected, stream_conflict_resolution,
                    missing_primitive_signal,
                    final_action, final_confidence, decision_source, total_decision_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.log_id, log.agent_id, log.game_id, log.game_type, log.level,
                log.action_number, 1 if log.is_frontier else 0, log.network_traction,
                log.actions_remaining, log.actions_budget, log.tension_state,
                log.deliberation_budget_seconds, log.budget_reason,
                log.gut.action, log.gut.confidence, log.gut.basis,
                log.gut.response_time_ms, log.gut.stream_a_influence,
                log.gut.stream_b_influence, log.gut.pattern_matched,
                1 if log.deliberation else 0,
                log.deliberation.action if log.deliberation else None,
                log.deliberation.confidence if log.deliberation else None,
                log.deliberation.time_spent_seconds if log.deliberation else None,
                json.dumps(log.deliberation.reasoning_steps) if log.deliberation else None,
                1 if log.deliberation and log.deliberation.changed_from_gut else 0,
                log.deliberation.change_reason if log.deliberation else None,
                log.deliberation_skipped_reason,
                1 if log.deliberation and log.deliberation.stream_conflict_detected else 0,
                log.deliberation.stream_conflict_resolution if log.deliberation else None,
                log.deliberation.missing_primitive_signal if log.deliberation else None,
                log.final_action, log.final_confidence, log.decision_source,
                log.total_decision_time_ms
            ))
        except Exception as e:
            logger.warning(f"Failed to store reasoning log: {e}")
