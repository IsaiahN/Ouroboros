EXPLORATION MODE: when an agent is freely exploring a frame. 
EXAMPLE 1:
Frame 323
{
  "action": "ACTION6",
  "reasoning": "Standard balanced strategy",
  "level": 3,
  "score": 1,
  "timestamp": "2025-12-08T21:08:25.108159",
  "agent_id": "offspring_8c4c7e12",
  "agent_mode": "optimizer",
  "generation": 283,
  "exploration_mode": "self_directed",
  "exploration_context": {
    "reason": "Broke out of stuck state, now exploring independently",
    "trust_self": true,
    "network_sequences_invalid": true,
    "start_action": 384
  },
  "self_model": {
    "objects_agent_controls": [],
    "aggregated_controlled": [],
    "control_confidence": 0,
    "object_dependencies": [],
    "network_control_hypotheses": [],
    "tetrahedral_perception": {
      "self_objects": [],
      "goal_objects": [],
      "threat_objects": [],
      "mood": {
        "valence": 0,
        "arousal": 0,
        "dominance": 0
      }
    }
  },
  "world_model": {
    "obstacles": [
      {
        "position": [
          31,
          0
        ],
        "color": 14
      },
      {
        "position": [
          6,
          32
        ],
        "color": 3
      },
      {
        "position": [
          31,
          32
        ],
        "color": 4
      },
      {
        "position": [
          32,
          4
        ],
        "color": 8
      },
      {
        "position": [
          32,
          58
        ],
        "color": 14
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "level": 2,
        "failure": "Game state frozen on level 2. Possibly reached dead end or unwinnable state.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false
      },
      {
        "level": 3,
        "failure": "Game state frozen on level 3. Possibly reached dead end or unwinnable state.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 3.",
        "confidence": 0.5,
        "validated": false
      },
      {
        "level": 2,
        "failure": "Game state frozen on level 2. Possibly reached dead end or unwinnable state.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false
      }
    ]
  },
  "emergent_reasoning": {
    "q1_change_vs_fixed": {
      "actions_that_changed_state": [],
      "actions_with_no_effect": [
        6
      ],
      "invariant_positions": 4096,
      "variable_positions": 0,
      "confidence": 0.8999999999999999,
      "insight": "No actions observed to change state yet"
    },
    "q2_reward_punishment": {
      "dangerous_objects": [],
      "rewarding_objects": [],
      "neutral_objects": [],
      "emotional_state": "neutral",
      "navigation_state": 0,
      "confidence": 0.3,
      "insight": "No strong impressions yet. Feeling neutral."
    },
    "q3_salient_target": {
      "most_salient": "rare_color_11",
      "salience_score": 0.92,
      "salience_reason": "Rare color (only 0.4% of frame)",
      "planned_interaction": "Consider ACTION6 at position (29, 31)",
      "ranked_targets": [
        {
          "type": "rare_color_11",
          "salience": 0.92
        },
        {
          "type": "rare_color_15",
          "salience": 0.86
        },
        {
          "type": "rare_color_8",
          "salience": 0.85
        }
      ],
      "confidence": 0.9,
      "insight": "Most salient: rare_color_11 (Rare color (only 0.4% of frame))"
    },
    "q4_working_theory": {
      "working_hypothesis": "Exploring level 2 to discover patterns",
      "hypothesis_source": "default_exploration",
      "evidence_for": 0,
      "evidence_against": 0,
      "transferable": false,
      "action_recommendations": {},
      "confidence": 0.3,
      "insight": "Exploring: Exploring level 2 to discover patterns"
    },
    "q7_familiarity": {
      "current_level": 2,
      "network_max_level": 1,
      "is_frontier": true,
      "familiarity": "frontier",
      "insight": "Level 2 is FRONTIER (novel)"
    },
    "q5_goal_variables": {
      "actions_with_score_increase": [],
      "actions_causing_game_over": [],
      "score_increasing_patterns": [],
      "terminal_patterns": [],
      "goal_insight": "No recent score changes or game-overs detected",
      "confidence": 0.3
    }
  },
  "strategy": "balanced",
  "learning_mode": "smart_exploration",
  "coordinate": {
    "x": 29,
    "y": 46
  },
  "visual_reason": "Pseudo-button pathfinding: Combination point between oscillating targets"
}

SEQUENCE REPLAY MODE:
When an agent is just playing back the working pattern the network already found:
I still want to see the "knowledge it gains from watching replays shown to me" so i understand how it sees the world/self.
that way i can align it with my own knowledge of the game (RLVR)
Frame 48
{
  "action": "ACTION6",
  "reasoning": "OPTIMIZER replaying proven sequence seq_a1d4 (target: L1)",
  "agent_role": "optimizer",
  "optimizer_target_level": 1,
  "sequence_id": "seq_a1d4e4ba8a3d4c37",
  "replay_step": 48,
  "total_steps": 53,
  "coordinate": {
    "x": 17,
    "y": 4
  },
  "checkpoint_validation": true,
  "role_compliance": "optimizer following sequence script"
}