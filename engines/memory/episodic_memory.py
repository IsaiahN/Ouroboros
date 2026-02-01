"""
Episodic Memory System

Enables agents to query their own experience history (wA) vs network wisdom (wB).
Implements the Two-Streams insight that private memory (wA) should be queryable
and comparable against network recommendations (wB).

DELEGATION: wA/wB state management is delegated to IThread.
This class focuses on:
- Pre-game autobiography synthesis
- Personal history queries
- Session state tracking
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from database_interface import DatabaseInterface
    from engines.consciousness.i_thread import IThread

logger = logging.getLogger(__name__)

# Role default weights for wA/wB initialization
ROLE_DEFAULT_WEIGHTS: Dict[str, Tuple[float, float]] = {
    'pioneer': (0.7, 0.3),      # High self-trust for exploration
    'optimizer': (0.3, 0.7),   # High network-trust for refinement
    'generalist': (0.5, 0.5),  # Balanced
    'exploiter': (0.6, 0.4),   # Slightly self-trusting
}


class EpisodicMemorySystem:
    """
    Enables agents to query their own experience history (wA) vs network wisdom (wB).

    Philosophy: "Episodic memory" is not a separate storage - it's the ability
    to query one's own action history and form intuitions from personal experience.

    This implements the Two-Streams insight that private memory (wA) should be
    queryable and comparable against network recommendations (wB).

    DELEGATION: wA/wB state management is now delegated to IThread.
    This class focuses on:
    - Pre-game autobiography synthesis
    - Personal history queries
    - Session state tracking
    """

    def __init__(self, db: "DatabaseInterface", i_thread: Optional["IThread"] = None):
        """
        Initialize episodic memory system.

        Args:
            db: Database interface for queries
            i_thread: Optional IThread for wA/wB state management delegation
        """
        self.db = db
        self._i_thread = i_thread

    def query_personal_history(
        self,
        agent_id: str,
        game_type: str,
        query_type: str = 'recent_actions'
    ) -> Dict[str, Any]:
        """
        Query agent's personal experience history.

        This is the CORE of Stream A (private knowledge) - what has this
        specific agent done and learned?

        Args:
            agent_id: Agent to query
            game_type: Game context
            query_type: Type of query
                - 'recent_actions': Last N actions taken
                - 'successful_patterns': What has worked before
                - 'failure_patterns': What to avoid
                - 'all': Full history summary

        Returns:
            Query results
        """
        if query_type == 'recent_actions':
            return self._query_recent_actions(agent_id, game_type)
        elif query_type == 'successful_patterns':
            return self._query_successful_patterns(agent_id, game_type)
        elif query_type == 'failure_patterns':
            return self._query_failure_patterns(agent_id, game_type)
        elif query_type == 'all':
            return {
                'recent': self._query_recent_actions(agent_id, game_type),
                'successes': self._query_successful_patterns(agent_id, game_type),
                'failures': self._query_failure_patterns(agent_id, game_type)
            }
        else:
            logger.warning(f"Unknown query_type: {query_type}")
            return {}

    def _query_recent_actions(
        self,
        agent_id: str,
        game_type: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Query agent's recent action history."""
        result = self.db.execute_query("""
            SELECT action, score_delta, level_number, created_at
            FROM game_action_history
            WHERE agent_id = ? AND game_type = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (agent_id, game_type, limit))

        if not result:
            return {'actions': [], 'summary': 'No recent history'}

        # Compute summary stats
        positive_count = sum(1 for r in result if (r.get('score_delta') or 0) > 0)
        negative_count = sum(1 for r in result if (r.get('score_delta') or 0) < 0)
        neutral_count = len(result) - positive_count - negative_count

        return {
            'actions': result,
            'count': len(result),
            'positive_outcomes': positive_count,
            'negative_outcomes': negative_count,
            'neutral_outcomes': neutral_count,
            'summary': f"{len(result)} actions: {positive_count} positive, {negative_count} negative"
        }

    def _query_successful_patterns(
        self,
        agent_id: str,
        game_type: str
    ) -> Dict[str, Any]:
        """Query patterns that have worked for this agent."""
        # Look for winning sequences from this agent
        result = self.db.execute_query("""
            SELECT sequence_data, action_count, level, created_at
            FROM winning_sequences
            WHERE game_type = ? AND winning_agent_id = ?
            ORDER BY created_at DESC
            LIMIT 5
        """, (game_type, agent_id))

        if not result:
            return {'patterns': [], 'summary': 'No successful patterns recorded'}

        return {
            'patterns': result,
            'count': len(result),
            'summary': f"Found {len(result)} winning sequences"
        }

    def _query_failure_patterns(
        self,
        agent_id: str,
        game_type: str
    ) -> Dict[str, Any]:
        """Query what this agent has learned to avoid."""
        # Look for eliminated actions
        result = self.db.execute_query("""
            SELECT eliminated_action, reason, test_count
            FROM metacognitive_eliminations
            WHERE agent_id = ? AND game_type = ?
            ORDER BY test_count DESC
            LIMIT 10
        """, (agent_id, game_type))

        if not result:
            return {'patterns': [], 'summary': 'No failure patterns recorded'}

        return {
            'patterns': result,
            'count': len(result),
            'summary': f"Learned to avoid {len(result)} actions"
        }

    def compare_streams(
        self,
        agent_id: str,
        game_type: str,
        proposed_action: str
    ) -> Dict[str, Any]:
        """
        Compare personal experience (wA) vs network wisdom (wB) for an action.

        This is the key function that enables Two-Streams reasoning.

        Args:
            agent_id: Agent considering the action
            game_type: Current game
            proposed_action: Action being considered

        Returns:
            Comparison with wA and wB perspectives
        """
        # Stream A: Personal experience with this action
        personal = self._get_personal_action_experience(agent_id, game_type, proposed_action)

        # Stream B: Network wisdom about this action
        network = self._get_network_action_wisdom(game_type, proposed_action)

        # Compare
        agreement = (personal['recommendation'] == network['recommendation'])

        if agreement:
            confidence = max(personal['confidence'], network['confidence'])
            reasoning = f"Both streams agree: {personal['recommendation']}"
        else:
            # Conflict - need to weigh
            if personal['confidence'] > network['confidence']:
                confidence = personal['confidence'] - network['confidence'] * 0.3
                reasoning = f"Personal experience ({personal['recommendation']}) overrides uncertain network ({network['recommendation']})"
            else:
                confidence = network['confidence'] - personal['confidence'] * 0.3
                reasoning = f"Network wisdom ({network['recommendation']}) overrides uncertain personal experience ({personal['recommendation']})"

        return {
            'stream_a': personal,
            'stream_b': network,
            'agreement': agreement,
            'confidence': confidence,
            'reasoning': reasoning,
            'recommendation': personal['recommendation'] if personal['confidence'] > network['confidence'] else network['recommendation']
        }

    def _get_personal_action_experience(
        self,
        agent_id: str,
        game_type: str,
        action: str
    ) -> Dict[str, Any]:
        """Get this agent's personal experience with an action."""
        result = self.db.execute_query("""
            SELECT
                COUNT(*) as total_uses,
                SUM(CASE WHEN score_delta > 0 THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN score_delta < 0 THEN 1 ELSE 0 END) as negative
            FROM game_action_history
            WHERE agent_id = ? AND game_type = ? AND action = ?
        """, (agent_id, game_type, action))

        if not result or not result[0].get('total_uses'):
            return {
                'recommendation': 'unknown',
                'confidence': 0.0,
                'reasoning': 'No personal experience with this action'
            }

        row = result[0]
        total = row['total_uses'] or 0
        positive = row['positive'] or 0
        negative = row['negative'] or 0

        if total == 0:
            return {
                'recommendation': 'unknown',
                'confidence': 0.0,
                'reasoning': 'No personal experience with this action'
            }

        success_rate = positive / total

        if success_rate > 0.6:
            recommendation = 'use'
            confidence = min(0.9, success_rate)
        elif success_rate < 0.3:
            recommendation = 'avoid'
            confidence = min(0.9, 1 - success_rate)
        else:
            recommendation = 'neutral'
            confidence = 0.4

        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reasoning': f"Personal: {positive}/{total} positive outcomes ({success_rate:.0%})",
            'total_uses': total,
            'positive': positive,
            'negative': negative
        }

    def _get_network_action_wisdom(
        self,
        game_type: str,
        action: str
    ) -> Dict[str, Any]:
        """Get network-wide wisdom about an action."""
        # Check if action is in winning sequences
        result = self.db.execute_query("""
            SELECT COUNT(*) as win_count
            FROM winning_sequences
            WHERE game_type = ? AND sequence_data LIKE ?
        """, (game_type, f'%{action}%'))

        win_count = result[0]['win_count'] if result else 0

        # Check elimination patterns
        elim_result = self.db.execute_query("""
            SELECT COUNT(*) as elim_count
            FROM metacognitive_eliminations
            WHERE game_type = ? AND eliminated_action = ?
        """, (game_type, action))

        elim_count = elim_result[0]['elim_count'] if elim_result else 0

        if win_count > elim_count * 2:
            recommendation = 'use'
            confidence = min(0.85, 0.3 + win_count * 0.1)
        elif elim_count > win_count * 2:
            recommendation = 'avoid'
            confidence = min(0.85, 0.3 + elim_count * 0.1)
        else:
            recommendation = 'neutral'
            confidence = 0.4

        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reasoning': f"Network: {win_count} wins, {elim_count} eliminations",
            'win_count': win_count,
            'elim_count': elim_count
        }

    def get_narrative_summary(
        self,
        agent_id: str,
        game_type: str,
        _recent_count: int = 10
    ) -> str:
        """
        Generate a narrative summary of agent's experience.

        This is for debugging/logging - helps understand what the agent "knows".
        """
        history = self.query_personal_history(agent_id, game_type, 'all')

        recent = history.get('recent', {})
        successes = history.get('successes', {})
        failures = history.get('failures', {})

        parts = []

        # Recent activity
        recent_summary = recent.get('summary', 'No recent history')
        parts.append(f"Recent: {recent_summary}")

        # Successes
        success_count = successes.get('count', 0)
        if success_count > 0:
            parts.append(f"Found {success_count} winning patterns")

        # Failures
        failure_count = failures.get('count', 0)
        if failure_count > 0:
            parts.append(f"Learned to avoid {failure_count} actions")

        return " | ".join(parts)

    def synthesize_pregame_autobiography(
        self,
        agent_id: Optional[str],
        agent_role: Optional[str],
        game_type: str
    ) -> Dict[str, Any]:
        """
        Synthesize a pre-game autobiography for context.

        DELEGATION: If IThread is available, initial wA/wB weights come from there.
        Otherwise fall back to role-based defaults.

        This combines:
        1. Agent's historical performance data
        2. Role-based initial wA/wB bias
        3. Network context for this game type

        Returns:
            Autobiography dictionary with:
            - game_history: Summary of past performance
            - action_patterns: Common action preferences
            - knowledge_base: What agent has learned
            - network_context: What the network knows
            - recommended_strategy: Initial approach
            - key_uncertainties: What to investigate
            - autobiography_narrative: Human-readable summary
            - session_state: Runtime tracking dict (initialized)
        """
        autobiography: Dict[str, Any] = {
            'agent_id': agent_id,
            'agent_role': agent_role,
            'game_type': game_type,
            'created_at': datetime.now().isoformat()
        }

        # Populate sections
        self._populate_game_history(autobiography, agent_id, game_type)
        self._populate_action_patterns(autobiography, agent_id, game_type)
        self._populate_knowledge_base(autobiography, agent_id, game_type)
        self._populate_network_context(autobiography, game_type)

        # Compute recommendations
        strategy = self._compute_recommended_strategy(autobiography)
        autobiography['recommended_strategy'] = strategy

        uncertainties = self._identify_key_uncertainties(autobiography)
        autobiography['key_uncertainties'] = uncertainties

        # Generate narrative
        narrative = self._generate_autobiography_narrative(autobiography)
        autobiography['autobiography_narrative'] = narrative

        # Initialize wA/wB weights - DELEGATE to IThread if available
        initial_wA, initial_wB, bias_source = self._initialize_stream_weights(
            agent_id, agent_role
        )

        return self._build_session_state(
            autobiography, agent_id, agent_role, strategy,
            initial_wA, initial_wB, bias_source
        )

    def _initialize_stream_weights(
        self,
        agent_id: Optional[str],
        agent_role: Optional[str]
    ) -> Tuple[float, float, str]:
        """
        Initialize wA/wB stream weights.

        DELEGATION: Uses IThread when available for persisted/role-based weights.
        Fallback: Role-based defaults from ROLE_DEFAULT_WEIGHTS.

        Returns:
            Tuple of (wA, wB, source_description)
        """
        # DELEGATE to IThread if available
        if self._i_thread is not None and agent_id:
            try:
                # Get or create state via IThread
                role = agent_role or 'generalist'
                state = self._i_thread.get_state(agent_id)

                if state is None:
                    # Initialize via IThread
                    state = self._i_thread.initialize_for_role(agent_id, role, persist=False)

                return state.w_a, state.w_b, f"i_thread ({state.bias_source})"
            except Exception as e:
                logger.debug(f"IThread delegation failed, using fallback: {e}")

        # FALLBACK: Role-based defaults
        role_key = (agent_role or 'generalist').lower()
        default_wA, default_wB = ROLE_DEFAULT_WEIGHTS.get(role_key, (0.5, 0.5))

        return default_wA, default_wB, f"role_default:{role_key}"

    def _populate_game_history(
        self,
        autobiography: Dict[str, Any],
        agent_id: Optional[str],
        game_type: str
    ) -> None:
        """Populate game history section."""
        if not agent_id:
            autobiography['game_history'] = {
                'total_games': 0,
                'wins': 0,
                'best_score': 0,
                'avg_score': 0.0,
                'summary': 'New agent with no history'
            }
            return

        result = self.db.execute_query("""
            SELECT
                COUNT(*) as total_games,
                SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as wins,
                MAX(final_score) as best_score,
                AVG(final_score) as avg_score
            FROM game_results
            WHERE agent_id = ? AND game_type = ?
        """, (agent_id, game_type))

        if result and result[0].get('total_games'):
            row = result[0]
            autobiography['game_history'] = {
                'total_games': row['total_games'],
                'wins': row['wins'] or 0,
                'best_score': row['best_score'] or 0,
                'avg_score': row['avg_score'] or 0.0,
                'summary': f"{row['wins'] or 0} wins in {row['total_games']} games"
            }
        else:
            autobiography['game_history'] = {
                'total_games': 0,
                'wins': 0,
                'best_score': 0,
                'avg_score': 0.0,
                'summary': 'No prior experience with this game type'
            }

    def _populate_action_patterns(
        self,
        autobiography: Dict[str, Any],
        agent_id: Optional[str],
        game_type: str
    ) -> None:
        """Populate action pattern preferences."""
        if not agent_id:
            autobiography['action_patterns'] = {
                'preferred_actions': [],
                'avoided_actions': [],
                'summary': 'No action patterns yet'
            }
            return

        # Get most successful actions
        result = self.db.execute_query("""
            SELECT action, COUNT(*) as uses,
                   SUM(CASE WHEN score_delta > 0 THEN 1 ELSE 0 END) as successes
            FROM game_action_history
            WHERE agent_id = ? AND game_type = ?
            GROUP BY action
            ORDER BY successes DESC
            LIMIT 5
        """, (agent_id, game_type))

        preferred = []
        if result:
            for r in result:
                if (r.get('successes') or 0) > (r.get('uses') or 1) * 0.3:
                    preferred.append(r['action'])

        # Get eliminated actions
        elim_result = self.db.execute_query("""
            SELECT eliminated_action
            FROM metacognitive_eliminations
            WHERE agent_id = ? AND game_type = ?
        """, (agent_id, game_type))

        avoided = [r['eliminated_action'] for r in (elim_result or [])]

        autobiography['action_patterns'] = {
            'preferred_actions': preferred[:3],
            'avoided_actions': avoided[:3],
            'summary': f"Prefer: {preferred[:3]}, Avoid: {avoided[:3]}"
        }

    def _populate_knowledge_base(
        self,
        autobiography: Dict[str, Any],
        agent_id: Optional[str],
        game_type: str
    ) -> None:
        """Populate learned knowledge."""
        if not agent_id:
            autobiography['knowledge_base'] = {
                'insights': [],
                'disproven_assumptions': [],
                'summary': 'No learned knowledge yet'
            }
            return

        # Get insights
        insights_result = self.db.execute_query("""
            SELECT key_insight, winning_strategy
            FROM metacognitive_insights
            WHERE (agent_id = ? OR is_transferable = TRUE) AND game_type = ?
            ORDER BY created_at DESC
            LIMIT 5
        """, (agent_id, game_type))

        insights = [r['key_insight'] for r in (insights_result or [])]

        # Get disproven assumptions
        disproven_result = self.db.execute_query("""
            SELECT assumption_text
            FROM metacognitive_assumptions
            WHERE agent_id = ? AND game_type = ? AND is_valid = FALSE
            LIMIT 5
        """, (agent_id, game_type))

        disproven = [r['assumption_text'] for r in (disproven_result or [])]

        autobiography['knowledge_base'] = {
            'insights': insights,
            'disproven_assumptions': disproven,
            'summary': f"{len(insights)} insights, {len(disproven)} disproven assumptions"
        }

    def _populate_network_context(
        self,
        autobiography: Dict[str, Any],
        game_type: str
    ) -> None:
        """Populate network-level context."""
        # Get network stats for this game
        result = self.db.execute_query("""
            SELECT
                COUNT(DISTINCT winning_agent_id) as agents_beat,
                COUNT(*) as total_wins,
                MIN(action_count) as best_sequence_length
            FROM winning_sequences
            WHERE game_type = ? AND is_active = TRUE
        """, (game_type,))

        if result and result[0].get('total_wins'):
            row = result[0]
            autobiography['network_context'] = {
                'agents_have_beaten': row['agents_beat'] or 0,
                'total_winning_sequences': row['total_wins'] or 0,
                'best_sequence_length': row['best_sequence_length'],
                'summary': f"{row['agents_beat'] or 0} agents have beaten this game"
            }
        else:
            autobiography['network_context'] = {
                'agents_have_beaten': 0,
                'total_winning_sequences': 0,
                'best_sequence_length': None,
                'summary': 'No agents have beaten this game yet'
            }

    def _compute_recommended_strategy(
        self,
        autobiography: Dict[str, Any]
    ) -> str:
        """Compute initial recommended strategy based on autobiography."""
        game_history = autobiography.get('game_history', {})
        network_context = autobiography.get('network_context', {})

        # If network has solutions, leverage them
        if network_context.get('total_winning_sequences', 0) > 0:
            return 'follow_network_sequence'

        # If agent has won before, try similar approach
        if game_history.get('wins', 0) > 0:
            return 'repeat_successful_pattern'

        # If agent has played but not won, analyze failures
        if game_history.get('total_games', 0) > 3:
            return 'analyze_past_failures'

        # Otherwise, explore
        return 'systematic_exploration'

    def _identify_key_uncertainties(
        self,
        autobiography: Dict[str, Any]
    ) -> List[str]:
        """Identify key uncertainties to investigate."""
        uncertainties: List[str] = []

        game_history = autobiography.get('game_history', {})
        network_context = autobiography.get('network_context', {})
        knowledge_base = autobiography.get('knowledge_base', {})

        if game_history.get('total_games', 0) == 0:
            uncertainties.append("What object do I control?")
            uncertainties.append("What is the goal?")

        if network_context.get('agents_have_beaten', 0) == 0:
            uncertainties.append("Has anyone solved this game?")

        if not knowledge_base.get('insights'):
            uncertainties.append("What patterns work here?")

        return uncertainties[:3]

    def _generate_autobiography_narrative(
        self,
        autobiography: Dict[str, Any]
    ) -> str:
        """Generate human-readable autobiography narrative."""
        parts: List[str] = []

        # Identity
        role = autobiography.get('agent_role', 'agent')
        game = autobiography.get('game_type', 'unknown')
        parts.append(f"I am a {role} preparing to play {game}.")

        # History
        history = autobiography.get('game_history', {})
        wins = history.get('wins', 0)
        total = history.get('total_games', 0)
        if total > 0:
            parts.append(f"I have played {total} times with {wins} wins.")
        else:
            parts.append("This is my first time playing this game.")

        # Network context
        network = autobiography.get('network_context', {})
        agents_beat = network.get('agents_have_beaten', 0)
        if agents_beat > 0:
            parts.append(f"Other agents have beaten this {agents_beat} times.")
        else:
            parts.append("No one has beaten this game yet.")

        # Strategy
        strategy = autobiography.get('recommended_strategy', 'explore')
        strategy_text = {
            'follow_network_sequence': "I will follow proven network strategies.",
            'repeat_successful_pattern': "I will repeat what worked before.",
            'analyze_past_failures': "I will learn from past failures.",
            'systematic_exploration': "I will systematically explore."
        }
        parts.append(strategy_text.get(strategy, "I will explore carefully."))

        return " ".join(parts)

    def initialize_session_state(
        self,
        autobiography: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Initialize runtime session state from autobiography.

        The session_state tracks runtime changes to wA/wB weights
        and other session-specific data.
        """
        if 'session_state' in autobiography:
            return autobiography  # Already initialized

        # Get initial weights (might come from autobiography or re-derive)
        agent_id = autobiography.get('agent_id')
        agent_role = autobiography.get('agent_role')
        initial_wA, initial_wB, bias_source = self._initialize_stream_weights(
            agent_id, agent_role
        )

        return self._build_session_state(
            autobiography, agent_id, agent_role,
            autobiography.get('recommended_strategy', 'explore'),
            initial_wA, initial_wB, bias_source
        )

    def _build_session_state(
        self,
        autobiography: Dict[str, Any],
        agent_id: Optional[str],
        agent_role: Optional[str],
        strategy: str,
        initial_wA: float,
        initial_wB: float,
        bias_source: str
    ) -> Dict[str, Any]:
        """Build the session_state structure for autobiography."""
        autobiography['session_state'] = {
            'actions_taken_this_game': 0,
            'actions_taken_this_level': 0,
            'current_level': 1,
            'discoveries_this_game': [],
            'confirmations_this_game': [],
            'contradictions_this_game': [],
            'wA': initial_wA,
            'wB': initial_wB,
            'initial_wA': initial_wA,
            'initial_wB': initial_wB,
            'bias_source': bias_source,
            'agent_role': agent_role,
            'stream_trust_history': [],
            'level_transitions': [],
            'last_action_source': None,
            'last_action_outcome': None,
        }

        autobiography['session_narrative'] = (
            f"Starting game as {agent_role or 'unknown'} with strategy '{strategy}' "
            f"(wA={initial_wA:.2f}, wB={initial_wB:.2f}, source={bias_source})."
        )

        return autobiography

    def reset_wA_wB_for_role_change(
        self,
        agent_id: str,
        new_role: str
    ) -> Tuple[float, float]:
        """
        Reset agent's wA/wB bias when they change roles.

        DELEGATION: Uses IThread.initialize_for_role() when available.

        Per AGI theory: When agents switch roles, their stream weighting
        should reset to the new role's default, not carry over old habits.

        Args:
            agent_id: Agent ID
            new_role: New role being assigned

        Returns:
            Tuple of (new_wA, new_wB)
        """
        # DELEGATE to IThread if available
        if self._i_thread is not None:
            try:
                state = self._i_thread.initialize_for_role(agent_id, new_role, persist=True)
                logger.info(
                    f"[ROLE CHANGE] Reset wA/wB via IThread for {agent_id[:8]} -> {new_role}: "
                    f"wA={state.w_a:.2f}, wB={state.w_b:.2f}"
                )
                return state.w_a, state.w_b
            except Exception as e:
                logger.debug(f"IThread delegation failed, using fallback: {e}")

        # FALLBACK: Local implementation
        new_wA, new_wB = ROLE_DEFAULT_WEIGHTS.get(new_role.lower(), (0.5, 0.5))

        # Update database with new bias
        try:
            self.db.execute_query(
                "UPDATE agents SET self_network_bias = ? WHERE agent_id = ?",
                (new_wB, agent_id)  # self_network_bias is wB
            )
            logger.info(
                f"[ROLE CHANGE] Reset wA/wB for {agent_id[:8]} -> {new_role}: "
                f"wA={new_wA:.2f}, wB={new_wB:.2f}"
            )
        except Exception as e:
            logger.warning(f"Failed to reset wA/wB in DB: {e}")

        return new_wA, new_wB

    def update_autobiography_after_action(
        self,
        autobiography: Dict[str, Any],
        action: str,
        action_source: str,  # 'wA' (personal), 'wB' (network), 'explore'
        outcome: str,  # 'positive' (score up), 'negative' (stuck/died), 'neutral'
        discovery: Optional[Dict[str, Any]] = None,
        confirmation: Optional[Dict[str, Any]] = None,
        contradiction: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update autobiography based on action outcome.

        This is the core runtime learning - adjusting wA/wB weights
        based on which stream is providing better guidance.
        """
        if 'session_state' not in autobiography:
            autobiography = self.initialize_session_state(autobiography)

        session = autobiography['session_state']
        session['actions_taken_this_game'] += 1
        session['actions_taken_this_level'] += 1

        # Record what happened
        session['last_action_source'] = action_source
        session['last_action_outcome'] = outcome

        # Track stream trust history
        session['stream_trust_history'].append({
            'action_num': session['actions_taken_this_game'],
            'source': action_source,
            'outcome': outcome,
            'action': action
        })
        # Full game memory - safety cap at 20000 for pathological cases
        if len(session['stream_trust_history']) > 20000:
            session['stream_trust_history'] = session['stream_trust_history'][-20000:]

        # ================================================================
        # DYNAMIC wA/wB ADJUSTMENT
        # ================================================================
        wA, wB = session['wA'], session['wB']

        if action_source == 'wA':  # Personal strategy
            if outcome == 'positive':
                wA = min(0.9, wA + 0.03)  # Reinforce personal trust
                wB = max(0.1, wB - 0.02)
            elif outcome == 'negative':
                wA = max(0.1, wA - 0.02)  # Reduce personal trust
                wB = min(0.9, wB + 0.02)
        elif action_source == 'wB':  # Network strategy
            if outcome == 'positive':
                wB = min(0.9, wB + 0.03)  # Reinforce network trust
                wA = max(0.1, wA - 0.02)
            elif outcome == 'negative':
                wB = max(0.1, wB - 0.02)  # Reduce network trust
                wA = min(0.9, wA + 0.02)
        # Exploration doesn't shift weights

        # Normalize to sum = 1.0
        total = wA + wB
        session['wA'] = wA / total
        session['wB'] = wB / total

        # ================================================================
        # TRACK DISCOVERIES
        # ================================================================
        if discovery:
            discovery['when'] = f"action {session['actions_taken_this_game']}"
            discovery['level'] = session['current_level']
            session['discoveries_this_game'].append(discovery)

        if confirmation:
            confirmation['when'] = f"action {session['actions_taken_this_game']}"
            session['confirmations_this_game'].append(confirmation)

        if contradiction:
            contradiction['when'] = f"action {session['actions_taken_this_game']}"
            session['contradictions_this_game'].append(contradiction)

        return autobiography

    def update_autobiography_on_level_change(
        self,
        autobiography: Dict[str, Any],
        old_level: int,
        new_level: int,
        actions_to_complete: int
    ) -> Dict[str, Any]:
        """
        Update autobiography when level changes.

        This records level completion and resets per-level counters.
        """
        if 'session_state' not in autobiography:
            autobiography = self.initialize_session_state(autobiography)

        session = autobiography['session_state']

        # Record transition
        session['level_transitions'].append({
            'from_level': old_level,
            'to_level': new_level,
            'actions_taken': actions_to_complete,
            'wA_at_transition': session['wA'],
            'wB_at_transition': session['wB']
        })

        session['current_level'] = new_level
        session['actions_taken_this_level'] = 0

        # Update narrative
        autobiography['session_narrative'] += (
            f" Completed level {old_level} in {actions_to_complete} actions."
            f" Now on level {new_level} (wA={session['wA']:.2f}, wB={session['wB']:.2f})."
        )

        return autobiography

    def get_current_wA_wB(
        self,
        autobiography: Dict[str, Any]
    ) -> Tuple[float, float]:
        """
        Get current wA/wB weighting for action selection.

        Returns:
            Tuple of (wA, wB) where wA + wB = 1.0
        """
        if 'session_state' not in autobiography:
            return (0.5, 0.5)
        return (
            autobiography['session_state']['wA'],
            autobiography['session_state']['wB']
        )

    def get_action_source_recommendation(
        self,
        autobiography: Dict[str, Any],
        personal_action: Optional[str] = None,
        network_action: Optional[str] = None
    ) -> Tuple[Optional[str], str, str]:
        """
        Decide which action source to use based on current wA/wB.

        This is the core decision function - should the agent follow
        their personal experience (wA) or network wisdom (wB)?

        Returns:
            Tuple of (action, source, reasoning)
        """
        if 'session_state' not in autobiography:
            return ('explore', 'explore', 'No session state - exploring')

        session = autobiography['session_state']
        wA, wB = session['wA'], session['wB']

        # If only one option available
        if personal_action and not network_action:
            return (personal_action, 'wA', f"Using personal strategy (wA={wA:.2f}, no network option)")
        if network_action and not personal_action:
            return (network_action, 'wB', f"Following network (wB={wB:.2f}, no personal option)")
        if not personal_action and not network_action:
            return ('explore', 'explore', "No suggestions from either stream - exploring")

        # Both options available - use weighted probabilistic selection
        import random

        if personal_action == network_action:
            return (personal_action, 'blend', f"Both streams agree (wA={wA:.2f}, wB={wB:.2f})")

        # Probabilistic selection based on weights
        if random.random() < wA:
            reasoning = (
                f"Choosing personal strategy (wA={wA:.2f} > random). "
                f"Recent outcomes: {self._summarize_recent_outcomes(session, 'wA')}"
            )
            return (personal_action, 'wA', reasoning)
        else:
            reasoning = (
                f"Following network (wB={wB:.2f} > random). "
                f"Recent outcomes: {self._summarize_recent_outcomes(session, 'wB')}"
            )
            return (network_action, 'wB', reasoning)

    def _summarize_recent_outcomes(
        self,
        session: Dict[str, Any],
        source: str
    ) -> str:
        """Summarize recent outcomes for a given source."""
        history = session.get('stream_trust_history', [])
        recent = [h for h in history[-20:] if h['source'] == source]
        if not recent:
            return "no recent data"

        positive = sum(1 for h in recent if h['outcome'] == 'positive')
        negative = sum(1 for h in recent if h['outcome'] == 'negative')
        total = len(recent)

        return f"{positive}/{total} positive, {negative}/{total} negative"

    def generate_runtime_narrative(
        self,
        autobiography: Dict[str, Any]
    ) -> str:
        """
        Generate current narrative reflecting runtime state.

        This combines the static autobiography with dynamic session state.
        """
        base = autobiography.get('autobiography_narrative', '')
        session = autobiography.get('session_state', {})

        if not session:
            return base

        parts = [base]

        # Current session status
        actions = session.get('actions_taken_this_game', 0)
        level = session.get('current_level', 1)
        wA, wB = session.get('wA', 0.5), session.get('wB', 0.5)

        parts.append(
            f"Currently on level {level} after {actions} actions "
            f"(wA={wA:.2f}, wB={wB:.2f})."
        )

        # Discoveries this session
        discoveries = session.get('discoveries_this_game', [])
        if discoveries:
            parts.append(f"This session I discovered: {len(discoveries)} new control(s).")

        # Confirmations/contradictions
        confirmations = session.get('confirmations_this_game', [])
        contradictions = session.get('contradictions_this_game', [])

        if confirmations:
            parts.append(f"Network wisdom confirmed {len(confirmations)} time(s).")
        if contradictions:
            parts.append(f"My experience contradicted network {len(contradictions)} time(s).")

        # Trust trend
        history = session.get('stream_trust_history', [])
        if len(history) >= 10:
            recent_wA = sum(1 for h in history[-10:] if h['source'] == 'wA' and h['outcome'] == 'positive')
            recent_wB = sum(1 for h in history[-10:] if h['source'] == 'wB' and h['outcome'] == 'positive')
            if recent_wA > recent_wB:
                parts.append("Personal strategies are working better recently.")
            elif recent_wB > recent_wA:
                parts.append("Network wisdom is proving more reliable recently.")

        return " ".join(parts)

    def persist_wA_wB_at_game_end(
        self,
        agent_id: str,
        autobiography: Dict[str, Any],
        game_outcome: str  # 'win', 'loss', 'timeout'
    ) -> bool:
        """
        Persist learned wA/wB bias to database at game end.

        The agent's wA/wB shifts during gameplay based on outcomes.
        At game end, we blend this session's learned bias with their
        historical bias, weighted by outcome quality.

        Philosophy: Wins teach more than losses.
        """
        if not agent_id or 'session_state' not in autobiography:
            return False

        session = autobiography['session_state']
        session_wB = session.get('wB', 0.5)
        initial_wB = session.get('initial_wB', 0.5)

        # How much did wB shift this game?
        shift = session_wB - initial_wB

        # Only persist if there was meaningful shift (> 0.05)
        if abs(shift) < 0.05:
            logger.debug(
                f"[wA/wB] Agent {agent_id[:8]} wB shift too small ({shift:.3f}), not persisting"
            )
            return False

        # Outcome-weighted learning rate
        if game_outcome == 'win':
            session_weight = 0.4
        elif game_outcome == 'timeout':
            session_weight = 0.3
        else:  # loss
            session_weight = 0.2

        try:
            # Get current persisted bias
            result = self.db.execute_query(
                "SELECT self_network_bias FROM agents WHERE agent_id = ?",
                (agent_id,)
            )

            if result and result[0].get('self_network_bias') is not None:
                historical_wB = result[0]['self_network_bias']
            else:
                historical_wB = initial_wB

            # Blend session learning with historical
            new_wB = (session_weight * session_wB) + ((1 - session_weight) * historical_wB)

            # Clamp to valid range
            new_wB = max(0.1, min(0.9, new_wB))

            # Update database
            self.db.execute_query(
                "UPDATE agents SET self_network_bias = ? WHERE agent_id = ?",
                (new_wB, agent_id)
            )

            logger.info(
                f"[wA/wB] Agent {agent_id[:8]} persisted bias: "
                f"{historical_wB:.2f} -> {new_wB:.2f} "
                f"(session learned {session_wB:.2f}, outcome={game_outcome})"
            )
            return True

        except Exception as e:
            logger.warning(f"Failed to persist wA/wB for {agent_id[:8]}: {e}")
            return False

    def _temporal_weight(
        self,
        created_at_str: str,
        half_life_days: float = 7.0
    ) -> float:
        """
        Calculate temporal weight with exponential decay.

        Recent data is weighted more heavily than old data.

        Args:
            created_at_str: ISO timestamp string
            half_life_days: Days until weight is halved

        Returns:
            Weight between 0.0 and 1.0
        """
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            age_days = (datetime.now() - created_at.replace(tzinfo=None)).days

            # Exponential decay
            decay_rate = math.log(2) / half_life_days
            weight = math.exp(-decay_rate * age_days)

            return max(0.01, min(1.0, weight))
        except Exception:
            return 0.5  # Default weight on parse error
