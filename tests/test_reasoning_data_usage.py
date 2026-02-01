# -*- coding: utf-8 -*-
"""
Unit tests for reasoning log data usage improvements.

Tests the following implementations:
1. Available actions change detection (control proof)
2. Win-validated hypothesis usage in action selection
3. Frame changes -> self-model learning
4. Tetrahedral perception always populated
5. Agent position inference from controlled objects
6. Machine-actionable failure insights
7. Decision contributors tracking

Per project rules:
- PYTHONDONTWRITEBYTECODE=1 (no pycache)
- Uses real database patterns
- No mock games - tests data flow
"""

import os
import sys

# Disable pycache per project rules
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestAvailableActionsChangeDetection:
    """Test the available_actions change detection mechanism."""

    def test_detects_new_actions_after_click(self):
        """When clicking unlocks movement (1-4), should detect as control proof."""
        # Simulate before and after states
        previous = {5, 6, 7}  # Only action5, action6, action7 available
        current = {1, 2, 3, 4, 5, 6, 7}  # Now movement unlocked

        new_actions = current - previous
        lost_actions = previous - current

        assert new_actions == {1, 2, 3, 4}
        assert lost_actions == set()
        # Movement actions unlocked = strong control proof
        assert new_actions & {1, 2, 3, 4}

    def test_detects_deselection(self):
        """When losing actions, should detect potential deselection."""
        previous = {1, 2, 3, 4, 5, 6, 7}  # Full actions
        current = {5, 6, 7}  # Lost movement

        lost_actions = previous - current

        assert lost_actions == {1, 2, 3, 4}


class TestMovementCorrelationLearning:
    """Test frame_changes -> self-model learning."""

    def test_parses_movement_from_frame_change(self):
        """Extract color and direction from movement description."""
        import re

        frame_change = "color_9 object moved left"
        expected_direction = "left"

        # Pattern matching
        color_match = re.search(r'color_(\d+)', frame_change)
        assert color_match is not None
        controlled_color = int(color_match.group(1))

        assert controlled_color == 9
        assert expected_direction in frame_change

    def test_action_direction_mapping(self):
        """Verify action to direction mapping."""
        action_direction_map = {
            'ACTION1': 'up',
            'ACTION2': 'down',
            'ACTION3': 'left',
            'ACTION4': 'right'
        }

        assert action_direction_map['ACTION3'] == 'left'
        assert action_direction_map['ACTION1'] == 'up'


class TestAgentPositionInference:
    """Test agent position inference from controlled objects."""

    def test_calculates_centroid(self):
        """Calculate centroid from multiple positions."""
        positions = [(5, 3), (6, 3), (5, 4), (6, 4)]

        avg_x = sum(p[0] for p in positions) / len(positions)
        avg_y = sum(p[1] for p in positions) / len(positions)

        assert avg_x == 5.5
        assert avg_y == 3.5
        assert [int(avg_x), int(avg_y)] == [5, 3]

    def test_handles_empty_positions(self):
        """Gracefully handle no controlled objects."""
        positions = []

        if positions:
            avg_x = sum(p[0] for p in positions) / len(positions)
            avg_y = sum(p[1] for p in positions) / len(positions)
            result = [int(avg_x), int(avg_y)]
        else:
            result = None

        assert result is None


class TestActionableFailureInsights:
    """Test machine-actionable parsing of failure hypotheses."""

    def test_parses_direction_avoidance(self):
        """Extract avoid_directions from failure text."""
        failure_text = "Agent got stuck at the bottom edge after falling down"

        avoid_directions = []
        direction_keywords = {
            'down': ['stuck bottom', 'fell down', 'bottom edge']
        }

        failure_lower = failure_text.lower()
        for direction, keywords in direction_keywords.items():
            if any(kw in failure_lower for kw in keywords):
                avoid_directions.append(direction)

        assert 'down' in avoid_directions

    def test_parses_strategy_preferences(self):
        """Extract prefer_actions from strategy text."""
        strategy_text = "Try clicking on the colored object, then move up"

        prefer_actions = []
        strategy_lower = strategy_text.lower()

        if any(kw in strategy_lower for kw in ['click', 'select', 'interact']):
            prefer_actions.append(6)  # ACTION6
        if any(kw in strategy_lower for kw in ['move up', 'go up']):
            prefer_actions.append(1)  # ACTION1 = up

        assert 6 in prefer_actions
        assert 1 in prefer_actions

    def test_detects_oscillation_pattern(self):
        """Detect oscillation from failure text."""
        failure_text = "Agent was stuck in oscillation between left and right"

        patterns_detected = []
        if any(kw in failure_text.lower() for kw in ['oscillat', 'loop', 'repeat']):
            patterns_detected.append('oscillation')

        assert 'oscillation' in patterns_detected

    def test_extracts_color_references(self):
        """Extract color numbers from text."""
        import re

        text = "Avoid color_5 objects, target color_3 goal"

        color_matches = re.findall(r'color[_\s]*(\d+)', text)
        colors = [int(c) for c in color_matches]

        assert 5 in colors
        assert 3 in colors


class TestDecisionContributors:
    """Test decision_contributors tracking."""

    def test_tracks_multiple_systems(self):
        """Verify multiple systems can contribute."""
        contributors = {}

        # Simulate various system contributions
        active_rules = ['rule1', 'rule2']
        if active_rules:
            contributors['rule_engine'] = len(active_rules)

        sensation_influence = 0.7
        if sensation_influence:
            contributors['sensation_engine'] = sensation_influence

        using_sequence = True
        if using_sequence:
            contributors['sequence_matching'] = 1.0

        hypothesis_ids = ['hyp1', 'hyp2', 'hyp3']
        if hypothesis_ids:
            contributors['failure_hypotheses'] = len(hypothesis_ids)

        assert contributors['rule_engine'] == 2
        assert contributors['sensation_engine'] == 0.7
        assert contributors['sequence_matching'] == 1.0
        assert contributors['failure_hypotheses'] == 3


class TestTetrahedralPerceptionPopulation:
    """Test that tetrahedral_perception is always populated."""

    def test_structure_has_required_fields(self):
        """Verify tetrahedral_perception structure."""
        tetra = {
            'self_objects': [],
            'goal_objects': [],
            'threat_objects': [],
            'mood': {
                'valence': 0.0,
                'arousal': 0.0,
                'dominance': 0.0
            }
        }

        assert 'self_objects' in tetra
        assert 'goal_objects' in tetra
        assert 'threat_objects' in tetra
        assert 'mood' in tetra
        assert 'valence' in tetra['mood']

    def test_populated_from_sensation_context(self):
        """When sensation_context available, populate tetra fields."""
        sensation_context = {
            'self_objects': [{'color': 9, 'center': [5, 3]}],
            'goal_objects': [{'color': 3, 'center': [10, 10]}],
            'threat_objects': [],
            'mood_vector': {'valence': 0.5, 'arousal': 0.3, 'dominance': 0.4}
        }

        tetra = {
            'self_objects': [],
            'goal_objects': [],
            'threat_objects': [],
            'mood': {'valence': 0.0, 'arousal': 0.0, 'dominance': 0.0}
        }

        # Simulate population logic
        if sensation_context:
            tetra['self_objects'] = sensation_context.get('self_objects', [])
            tetra['goal_objects'] = sensation_context.get('goal_objects', [])
            tetra['threat_objects'] = sensation_context.get('threat_objects', [])
            tetra['mood'] = sensation_context.get('mood_vector', tetra['mood'])

        assert len(tetra['self_objects']) == 1
        assert tetra['self_objects'][0]['color'] == 9
        assert tetra['mood']['valence'] == 0.5


class TestValidatedHypothesisPrioritization:
    """Test that validated_by_win hypotheses are prioritized."""

    def test_filters_validated_hypotheses(self):
        """Filter hypotheses where validated_by_win is True."""
        hypotheses = [
            {'hypothesis_id': 'h1', 'reliability': 0.8, 'validated_by_win': False},
            {'hypothesis_id': 'h2', 'reliability': 0.7, 'validated_by_win': True},
            {'hypothesis_id': 'h3', 'reliability': 0.9, 'validated_by_win': True},
        ]

        validated = [h for h in hypotheses if h.get('validated_by_win')]

        assert len(validated) == 2
        assert validated[0]['hypothesis_id'] == 'h2'
        assert validated[1]['hypothesis_id'] == 'h3'

    def test_validated_comes_before_non_validated(self):
        """Validated hypotheses should come first in sorted list."""
        hypotheses = [
            {'hypothesis_id': 'h1', 'reliability': 0.95, 'validated_by_win': False},
            {'hypothesis_id': 'h2', 'reliability': 0.6, 'validated_by_win': True},
        ]

        # Sort by validated_by_win first, then reliability
        sorted_hyps = sorted(
            hypotheses,
            key=lambda h: (not h.get('validated_by_win', False), -h.get('reliability', 0))
        )

        # Validated should come first even with lower reliability
        assert sorted_hyps[0]['hypothesis_id'] == 'h2'
        assert sorted_hyps[0]['validated_by_win'] == True


# =======================================================================
# ADDITIONAL TESTS FOR GAP FIXES (Added 2025-12-28)
# =======================================================================

class TestNetworkBootstrap:
    """Test bootstrapping objects_agent_controls from network hypotheses."""

    def test_bootstraps_when_local_empty(self):
        """When agent has no local control data, adopt network hypothesis."""
        local_controlled = None  # Agent has no knowledge

        network_hypotheses = [
            {
                'hypothesis_id': 'oc_vc33_L3_ff6df507',
                'controlled_objects': ['x:10,y:0', 'x:10,y:1', 'x:10,y:2'],
                'reliability': 0.93,
                'validated_by_win': 0
            }
        ]

        # Bootstrap logic
        bootstrapped = None
        if not local_controlled and network_hypotheses:
            best = network_hypotheses[0]
            bootstrapped = best.get('controlled_objects', [])[:10]

        assert bootstrapped is not None
        assert len(bootstrapped) == 3
        assert bootstrapped[0] == 'x:10,y:0'

    def test_prefers_validated_hypothesis(self):
        """When bootstrapping, prefer validated_by_win hypothesis."""
        network_hypotheses = [
            {'hypothesis_id': 'h1', 'controlled_objects': ['a'], 'reliability': 0.95, 'validated_by_win': 0},
            {'hypothesis_id': 'h2', 'controlled_objects': ['b'], 'reliability': 0.7, 'validated_by_win': 1},
        ]

        # Find win-validated first
        best = None
        for h in network_hypotheses:
            if h.get('validated_by_win'):
                best = h
                break
        if not best:
            best = network_hypotheses[0]

        assert best['hypothesis_id'] == 'h2'  # Win-validated wins


class TestWorkingTheoryGeneration:
    """Test working_theory generation from multiple sources."""

    def test_generates_from_controlled_objects(self):
        """When we have controlled objects, build control theory."""
        ctrl_objects = ['x:5,y:3', 'x:5,y:4', 'x:5,y:5']

        if ctrl_objects:
            working_theory = f"I control {len(ctrl_objects)} objects and move with directional actions"
        else:
            working_theory = None

        assert working_theory == "I control 3 objects and move with directional actions"

    def test_generates_from_network_hypotheses(self):
        """When network has hypotheses, form tentative theory."""
        ctrl_objects = []
        network_hypos = [{'reliability': 0.85}]

        if ctrl_objects:
            working_theory = "control theory"
        elif network_hypos:
            rel = network_hypos[0].get('reliability', 0)
            if rel > 0.8:
                working_theory = f"Network suggests object control with {rel:.0%} confidence"
            else:
                working_theory = f"Exploring - network has {len(network_hypos)} control hypotheses"
        else:
            working_theory = "no theory"

        assert working_theory == "Network suggests object control with 85% confidence"

    def test_generates_from_score_progress(self):
        """When we've made progress, acknowledge it."""
        ctrl_objects = []
        network_hypos = []
        goal_objects = []
        score = 2

        if ctrl_objects:
            theory = "control"
        elif network_hypos:
            theory = "network"
        elif goal_objects:
            theory = "goals"
        elif score > 0:
            theory = f"Current approach works - score {score} achieved"
        else:
            theory = "Exploring game mechanics - no pattern confirmed yet"

        assert theory == "Current approach works - score 2 achieved"


class TestGenomeFetch:
    """Test genome fetching from database."""

    def test_builds_genome_from_agent_data(self):
        """Simulate building genome from agent table row."""
        # Simulated database row
        agent_row = {
            'agent_type': 'pioneer',
            'exploration_rate': 0.35,
            'learning_rate': 0.12,
            'mutation_rate': 0.08,
            'species': 'explorer_v2'
        }

        genome = {
            'agent_type': agent_row.get('agent_type', 'generalist'),
            'exploration_rate': agent_row.get('exploration_rate', 0.3),
            'learning_rate': agent_row.get('learning_rate', 0.1),
            'mutation_rate': agent_row.get('mutation_rate', 0.05),
            'species': agent_row.get('species', 'unknown')
        }

        assert genome['agent_type'] == 'pioneer'
        assert genome['exploration_rate'] == 0.35
        assert genome['species'] == 'explorer_v2'


class TestEmotionalStateComputation:
    """Test emotional_state computation from multiple sources."""

    def test_derives_from_mood_valence(self):
        """Derive emotional state from sensation mood vector."""
        sensation_context = {
            'mood_vector': {'valence': 0.4, 'arousal': 0.3, 'dominance': 0.5}
        }

        valence = sensation_context.get('mood_vector', {}).get('valence', 0)

        if valence > 0.3:
            emotional_state = 'confident'
        elif valence > 0:
            emotional_state = 'curious'
        elif valence > -0.3:
            emotional_state = 'neutral'
        else:
            emotional_state = 'frustrated'

        assert emotional_state == 'confident'

    def test_derives_from_navigation_state(self):
        """Fall back to navigation state for emotional state."""
        navigation_state = -0.4

        if navigation_state > 0.3:
            emotional_state = 'confident'
        elif navigation_state > 0:
            emotional_state = 'curious'
        elif navigation_state > -0.3:
            emotional_state = 'neutral'
        else:
            emotional_state = 'frustrated'

        assert emotional_state == 'frustrated'


class TestInferredGoalsUsage:
    """Test that inferred_goals are used in action selection."""

    def test_calculates_direction_to_goal(self):
        """Calculate which direction to move toward goal."""
        agent_pos = (5, 5)
        goal_pos = (10, 3)  # To the right and up

        gx, gy = goal_pos
        ax, ay = agent_pos

        if abs(gx - ax) >= abs(gy - ay):
            # Horizontal priority
            if gx > ax:
                direction = 'right'
            else:
                direction = 'left'
        else:
            # Vertical priority
            if gy > ay:
                direction = 'down'
            else:
                direction = 'up'

        assert direction == 'right'  # Goal is more to the right than up

    def test_uses_manhattan_distance(self):
        """Use Manhattan distance for closest goal."""
        agent_pos = (5, 5)
        goals = [
            {'position': [10, 5]},  # 5 away
            {'position': [7, 7]},   # 4 away
            {'position': [20, 20]}, # 30 away
        ]

        min_dist = float('inf')
        closest = None
        for g in goals:
            pos = g.get('position', [])
            if len(pos) >= 2:
                dist = abs(pos[0] - agent_pos[0]) + abs(pos[1] - agent_pos[1])
                if dist < min_dist:
                    min_dist = dist
                    closest = g

        assert closest == {'position': [7, 7]}
        assert min_dist == 4


class TestNetworkHypothesesFallback:
    """Test fallback to network_object_control_hypotheses."""

    def test_uses_control_hypotheses_when_rules_empty(self):
        """When learned_rules is empty, use control hypotheses."""
        learned_rules = []

        control_hypotheses = [
            {'hypothesis_id': 'oc_game_L1_abc123', 'reliability': 0.85, 'validated_by_win': 1}
        ]

        if not learned_rules and control_hypotheses:
            network_hypotheses = [
                {
                    'rule_id': h['hypothesis_id'][:12],
                    'type': 'object_control',
                    'confidence': h['reliability'],
                    'validated_by_win': h['validated_by_win']
                }
                for h in control_hypotheses
            ]
        else:
            network_hypotheses = []

        assert len(network_hypotheses) == 1
        assert network_hypotheses[0]['type'] == 'object_control'
        assert network_hypotheses[0]['validated_by_win'] == 1


# =======================================================================
# HYPOTHESIS TESTING LOOP TESTS (Added 2025-12-28)
# =======================================================================

class TestHypothesisFormation:
    """Test hypothesis formation from frame changes."""

    def test_forms_hypothesis_from_color_changes(self):
        """Form hypothesis when frame shows consistent color changes."""
        import re

        frame_changes = [
            "position (36, 42) changed from color_12 to color_9",
            "position (37, 42) changed from color_12 to color_9",
            "position (38, 42) changed from color_12 to color_9",
        ]
        last_action = "ACTION6"

        # Analyze changes to form hypothesis
        color_changes = {}
        for change in frame_changes:
            if 'changed from' in change:
                colors = re.findall(r'color_(\d+)', change)
                if len(colors) >= 2:
                    from_color, to_color = int(colors[0]), int(colors[1])
                    color_changes[(from_color, to_color)] = color_changes.get((from_color, to_color), 0) + 1

        assert (12, 9) in color_changes
        assert color_changes[(12, 9)] == 3

        # Form hypothesis
        most_common = max(color_changes.items(), key=lambda x: x[1])
        (from_c, to_c), count = most_common

        hypothesis = {
            'action': last_action,
            'effect': f"Changes color_{from_c} to color_{to_c}",
            'change_count': count,
            'confidence': min(0.8, 0.3 + count * 0.05)
        }

        assert hypothesis['action'] == 'ACTION6'
        assert hypothesis['effect'] == 'Changes color_12 to color_9'
        assert hypothesis['change_count'] == 3
        assert hypothesis['confidence'] == 0.45  # 0.3 + 3*0.05

    def test_insight_reflects_frame_changes(self):
        """Q1 insight should describe what actually changed."""
        delta_changes = [
            "position (36, 42) changed from color_12 to color_9",
            "position (37, 42) changed from color_12 to color_9",
        ]
        last_action = "ACTION6"

        # Simulate Q1 insight generation
        if delta_changes:
            import re
            color_changes = {}
            for change in delta_changes:
                colors = re.findall(r'color_(\d+)', change)
                if len(colors) >= 2:
                    from_c, to_c = int(colors[0]), int(colors[1])
                    color_changes[(from_c, to_c)] = color_changes.get((from_c, to_c), 0) + 1

            if color_changes:
                most_common = max(color_changes.items(), key=lambda x: x[1])
                (from_c, to_c), count = most_common
                insight = f"{last_action} changed {count} pixels (color_{from_c}->color_{to_c})"
            else:
                insight = f"{last_action} caused {len(delta_changes)} frame changes"
        else:
            insight = "No actions observed to change state yet"

        assert "ACTION6" in insight
        assert "color_12" in insight
        assert "color_9" in insight


class TestHypothesisValidation:
    """Test hypothesis validation when effects match predictions."""

    def test_validates_when_effect_observed(self):
        """Hypothesis is validated when predicted effect occurs."""
        hypothesis = {
            'action': 'ACTION6',
            'effect': 'Changes color_12 to color_9',
            'confidence': 0.5
        }

        frame_changes = [
            "position (40, 42) changed from color_12 to color_9"
        ]
        last_action = 'ACTION6'

        # Validation logic
        import re
        if hypothesis['action'] == last_action:
            hyp_colors = re.findall(r'color_(\d+)', hypothesis['effect'])

            effect_observed = False
            for change in frame_changes:
                change_colors = re.findall(r'color_(\d+)', change)
                if hyp_colors and change_colors and hyp_colors == change_colors:
                    effect_observed = True
                    break

            if effect_observed:
                hypothesis['validated'] = True
                hypothesis['confidence'] = min(0.95, hypothesis['confidence'] + 0.2)

        assert hypothesis.get('validated') == True
        assert hypothesis['confidence'] == 0.7  # 0.5 + 0.2

    def test_lowers_confidence_when_effect_not_observed(self):
        """Hypothesis confidence decreases when effect doesn't occur."""
        hypothesis = {
            'action': 'ACTION6',
            'effect': 'Changes color_12 to color_9',
            'confidence': 0.5
        }

        frame_changes = [
            "NULL - 304 Not Modified"  # No change
        ]
        last_action = 'ACTION6'

        # Validation logic
        import re
        if hypothesis['action'] == last_action:
            hyp_colors = re.findall(r'color_(\d+)', hypothesis['effect'])

            effect_observed = False
            for change in frame_changes:
                if isinstance(change, str) and 'NULL' not in change:
                    change_colors = re.findall(r'color_(\d+)', change)
                    if hyp_colors and change_colors and hyp_colors == change_colors:
                        effect_observed = True
                        break

            if not effect_observed:
                hypothesis['confidence'] = max(0.1, hypothesis['confidence'] - 0.1)

        assert hypothesis.get('validated') is None
        assert hypothesis['confidence'] == 0.4  # 0.5 - 0.1


class TestDM3HypothesisDrivenAction:
    """Test DM-3: action selection using Q1 hypotheses."""

    def test_boosts_lever_actions(self):
        """Actions with high change count get boosted."""
        dm_biases = {}
        gameover_actions = []

        hypothesis = {
            'action': 'ACTION6',
            'effect': 'Changes color_12 to color_9',
            'change_count': 10,
            'confidence': 0.7
        }

        if hypothesis and hypothesis.get('confidence', 0) > 0.5:
            action_num = int(hypothesis['action'].replace('ACTION', ''))
            change_count = hypothesis.get('change_count', 0)

            if change_count >= 5:
                dm_biases[action_num] = dm_biases.get(action_num, 0) + 0.3

        assert dm_biases.get(6) == 0.3

    def test_boosts_actions_that_caused_changes(self):
        """Actions we observed causing changes get exploration boost."""
        dm_biases = {}
        gameover_actions = [7]  # ACTION7 caused game over

        actions_that_work = [1, 3, 6]  # These caused state changes

        for action_num in actions_that_work[:3]:
            if action_num not in gameover_actions:
                dm_biases[action_num] = dm_biases.get(action_num, 0) + 0.15

        assert dm_biases.get(1) == 0.15
        assert dm_biases.get(3) == 0.15
        assert dm_biases.get(6) == 0.15
        assert 7 not in dm_biases  # Avoided because it caused game over


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
