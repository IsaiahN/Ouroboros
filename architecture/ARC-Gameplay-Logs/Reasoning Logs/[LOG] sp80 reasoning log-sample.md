
ARC-AGI-3
Preview
Games
Overview
Docs
Leaderboard
Scorecards
Ouroboros
Ouroboros
Sp80-0605ab9e5b2a
Session: 8fe2817b-acb6-4400-a339-2c2a4f1d3d16
Level: 1
251 / 251





1×
Reasoning Log
Frame 250
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T19:00:30.957402",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 75
    }
  }
}
Show less
Frame 224
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_14 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T19:00:20.951711",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 72
    }
  }
}
Show less
Frame 223
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_14 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T19:00:10.784440",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 69
    }
  },
  "coordinate": {
    "x": 26,
    "y": 38
  },
  "visual_reason": "Rare color 8 (112 pixels)"
}
Show less
Frame 222
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_14 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T19:00:00.443525",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 66
    }
  }
}
Show less
Frame 221
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_14 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:59:50.712177",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 63
    }
  },
  "coordinate": {
    "x": 38,
    "y": 0
  },
  "visual_reason": "Rare color 0 (51 pixels)"
}
Show less
Frame 220
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_14 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:59:40.651423",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 60
    }
  },
  "coordinate": {
    "x": 6,
    "y": 0
  },
  "visual_reason": "Rare color 14 (13 pixels)"
}
Show less
Frame 219
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_14 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:59:30.877548",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 57
    }
  }
}
Show less
Frame 218
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "ACTION2 caused 20 frame changes",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_14 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.4
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:59:21.341957",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 54
    }
  }
}
Show less
Frame 217
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "color_14 object disappeared from (13, 0)",
      "color_14 object disappeared from (14, 0)",
      "color_14 object disappeared from (15, 0)",
      "color_14 object disappeared from (16, 0)",
      "color_14 object disappeared from (17, 0)",
      "color_14 object disappeared from (18, 0)",
      "color_14 object disappeared from (19, 0)",
      "color_14 object disappeared from (20, 0)",
      "color_14 object disappeared from (21, 0)",
      "color_14 object disappeared from (22, 0)",
      "color_14 object disappeared from (23, 0)",
      "color_14 object disappeared from (24, 0)",
      "color_14 object disappeared from (25, 0)",
      "position (12, 8) changed from color_6 to color_12",
      "position (13, 8) changed from color_6 to color_12",
      "position (14, 8) changed from color_6 to color_12",
      "position (15, 8) changed from color_6 to color_12",
      "position (44, 8) changed from color_6 to color_12",
      "position (45, 8) changed from color_6 to color_12",
      "position (46, 8) changed from color_6 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_14 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:59:11.740280",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 51
    }
  }
}
Show less
Frame 216
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:59:01.989714",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 48
    }
  }
}
Show less
Frame 215
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "ACTION4 caused 1 frame changes",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.4
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:58:52.142525",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 45
    }
  }
}
Show less
Frame 214
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "ACTION1 caused 1 frame changes",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.4
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:58:42.122583",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 42
    }
  }
}
Show less
Frame 213
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "ACTION5 caused 20 frame changes",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.4
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:58:32.156593",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 39
    }
  }
}
Show less
Frame 187
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "color_14 object disappeared from (26, 0)",
      "color_14 object disappeared from (27, 0)",
      "color_14 object disappeared from (28, 0)",
      "color_14 object disappeared from (29, 0)",
      "color_14 object disappeared from (30, 0)",
      "color_14 object disappeared from (31, 0)",
      "color_14 object disappeared from (32, 0)",
      "color_14 object disappeared from (33, 0)",
      "color_14 object disappeared from (34, 0)",
      "color_14 object disappeared from (35, 0)",
      "color_14 object disappeared from (36, 0)",
      "color_14 object disappeared from (37, 0)",
      "position (12, 8) changed from color_6 to color_12",
      "position (13, 8) changed from color_6 to color_12",
      "position (14, 8) changed from color_6 to color_12",
      "position (15, 8) changed from color_6 to color_12",
      "position (44, 8) changed from color_6 to color_12",
      "position (45, 8) changed from color_6 to color_12",
      "position (46, 8) changed from color_6 to color_12",
      "position (47, 8) changed from color_6 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:58:22.258633",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 36
    }
  }
}
Show less
Frame 186
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "ACTION6 caused 1 frame changes",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.4
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:58:12.768678",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 33
    }
  }
}
Show less
Frame 185
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "ACTION2 caused 1 frame changes",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.4
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:58:02.426056",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 30
    }
  },
  "coordinate": {
    "x": 55,
    "y": 42
  },
  "visual_reason": "Rare color 0 (106 pixels)"
}
Show less
Frame 184
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "ACTION5 caused 1 frame changes",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.4
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:57:51.948866",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 27
    }
  }
}
Show less
Frame 158
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "ACTION5 caused 1 frame changes",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.4
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:57:41.727765",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 24
    }
  }
}
Show less
Frame 157
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:57:31.604459",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 21
    }
  }
}
Show less
Frame 131
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:57:21.772690",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 18
    }
  }
}
Show less
Frame 130
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:57:12.228744",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 15
    }
  }
}
Show less
Frame 129
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:57:02.061654",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 12
    }
  }
}
Show less
Frame 128
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:52.315773",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 9
    }
  }
}
Show less
Frame 127
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "No actions observed to change state yet",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.6% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:42.326707",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 6
    }
  }
}
Show less
Frame 126
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:31.375243",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "[DISCOVERY] Testing obj_10 control with ACTION4",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 125
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:30.545699",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "[DISCOVERY] Testing obj_10 control with ACTION3",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 124
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:29.818859",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "[DISCOVERY] Testing obj_10 control with ACTION2",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 123
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:29.030613",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "[DISCOVERY] Testing obj_10 control with ACTION1",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 122
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "color_14 object disappeared from (51, 0)",
      "color_14 object disappeared from (52, 0)",
      "color_14 object disappeared from (53, 0)",
      "color_14 object disappeared from (54, 0)",
      "color_14 object disappeared from (55, 0)",
      "color_14 object disappeared from (56, 0)",
      "color_14 object disappeared from (57, 0)",
      "color_14 object disappeared from (58, 0)",
      "color_14 object disappeared from (59, 0)",
      "color_14 object disappeared from (60, 0)",
      "color_14 object disappeared from (61, 0)",
      "color_14 object disappeared from (62, 0)",
      "color_14 object disappeared from (63, 0)",
      "position (12, 8) changed from color_6 to color_12",
      "position (13, 8) changed from color_6 to color_12",
      "position (14, 8) changed from color_6 to color_12",
      "position (15, 8) changed from color_6 to color_12",
      "position (44, 8) changed from color_6 to color_12",
      "position (45, 8) changed from color_6 to color_12",
      "position (46, 8) changed from color_6 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:28.082412",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 33
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "[DISCOVERY] Click on obj_10 to see if selectable",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  },
  "coordinate": {
    "x": 25,
    "y": 0
  },
  "visual_reason": "Rare color 14 (51 pixels)"
}
Show less
Frame 121
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:27.044367",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "ESCAPE MODE: Trying ACTION5 to break out of frozen state",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 120
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:18.730060",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "[DISCOVERY] Testing obj_11 control with ACTION4",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 119
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:17.725682",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "[DISCOVERY] Testing obj_11 control with ACTION3",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 118
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:16.763451",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "[DISCOVERY] Testing obj_11 control with ACTION2",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 117
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:15.737684",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "[DISCOVERY] Testing obj_11 control with ACTION1",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 116
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:14.757132",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "[DISCOVERY] Click on obj_11 to see if selectable",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  },
  "coordinate": {
    "x": 29,
    "y": 2
  },
  "visual_reason": "Rare color 4 (24 pixels)"
}
Show less
Frame 115
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:13.735783",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "[DISCOVERY] Testing obj_8 control with ACTION4",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 114
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:12.979199",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "[DISCOVERY] Testing obj_8 control with ACTION3",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 113
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:12.030280",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "[DISCOVERY] Testing obj_8 control with ACTION2",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 112
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:11.015182",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "[DISCOVERY] Testing obj_8 control with ACTION1",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 111
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:10.055295",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "[DISCOVERY] Click on obj_8 to see if selectable",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  },
  "coordinate": {
    "x": 26,
    "y": 38
  },
  "visual_reason": "Rare color 8 (112 pixels)"
}
Show less
Frame 110
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:09.262909",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "[DISCOVERY] Testing obj_6 control with ACTION4",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 109
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:08.041042",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "[DISCOVERY] Testing obj_6 control with ACTION3",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 108
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:07.085789",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "[DISCOVERY] Testing obj_6 control with ACTION2",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 107
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:06.033378",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "[DISCOVERY] Testing obj_6 control with ACTION1",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 106
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:04.869652",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "[DISCOVERY] Click on obj_6 to see if selectable",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  },
  "coordinate": {
    "x": 29,
    "y": 2
  },
  "visual_reason": "Rare color 4 (24 pixels)"
}
Show less
Frame 105
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:03.859159",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "self_directed",
    "self_directed_context": {
      "reason": "Broke out of stuck state, exploring independently",
      "trust_self": true,
      "network_invalid": true,
      "start_action": 16
    }
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "[DISCOVERY] Testing obj_4 control with ACTION4",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 79
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:56:02.457956",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "ESCAPE MODE: Trying ACTION5 to break out of frozen state",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 78
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:53.794342",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "[DISCOVERY] Testing obj_4 control with ACTION3",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 77
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:52.821663",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "[DISCOVERY] Testing obj_4 control with ACTION2",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 76
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:52.061908",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "[DISCOVERY] Testing obj_4 control with ACTION1",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 75
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:51.240573",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "[DISCOVERY] Click on obj_4 to see if selectable",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  },
  "coordinate": {
    "x": 31,
    "y": 0
  },
  "visual_reason": "Rare color 14 (64 pixels)"
}
Show less
Frame 74
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:50.474787",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "[DISCOVERY] Testing obj_12 control with ACTION4",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 73
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:49.434119",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "[DISCOVERY] Testing obj_12 control with ACTION3",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 72
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:48.430938",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "[DISCOVERY] Testing obj_12 control with ACTION2",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 71
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:47.679951",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "[DISCOVERY] Testing obj_12 control with ACTION1",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 70
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:46.585129",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "[DISCOVERY] Click on obj_12 to see if selectable",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  },
  "coordinate": {
    "x": 29,
    "y": 5
  },
  "visual_reason": "Rare color 6 (32 pixels)"
}
Show less
Frame 69
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:45.598856",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "[DISCOVERY] Testing obj_14 control with ACTION4",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 68
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:44.854681",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "[DISCOVERY] Testing obj_14 control with ACTION3",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 67
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:43.901199",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "[DISCOVERY] Testing obj_14 control with ACTION2",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 66
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:42.974276",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "[DISCOVERY] Testing obj_14 control with ACTION1",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  }
}
Show less
Frame 65
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION6",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:41.980547",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "[DISCOVERY] Click on obj_14 to see if selectable",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  },
  "coordinate": {
    "x": 31,
    "y": 0
  },
  "visual_reason": "Rare color 14 (64 pixels)"
}
Show less
Frame 64
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 10 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:0,y:0",
        "x:0,y:1",
        "x:0,y:10",
        "x:0,y:11",
        "x:0,y:12",
        "x:0,y:13",
        "x:0,y:14",
        "x:0,y:15",
        "x:0,y:16",
        "x:0,y:17"
      ],
      "aggregated_controlled": [],
      "control_confidence": 1,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L2_534d9326",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_356bf247",
          "controlled": [
            "x:0,y:0",
            "x:0,y:1",
            "x:0,y:10",
            "x:0,y:11",
            "x:0,y:12"
          ],
          "reliability": 1,
          "validated_by_win": 0
        },
        {
          "id": "oc_sp80_L2_1a742fda",
          "controlled": [
            "x:32,y:48",
            "x:33,y:48",
            "x:34,y:48"
          ],
          "reliability": 0.75,
          "validated_by_win": 0
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "Grid size changed"
    ],
    "score_change": 1,
    "level_change": true,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Observed 0 actions that change state",
    "Q2_how_does_this_feel": "No strong impressions yet. Feeling neutral.",
    "Q3_what_worked_before": "Most salient: rare_color_4 (Rare color (only 0.3% of frame))",
    "Q4_what_should_i_try": "Exploring to discover rules",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 450 Network Sensation Isolated",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 2,
    "score": 1,
    "timestamp": "2025-12-28T18:55:40.891514",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": true,
    "frontier_status": "NULL - 451 Frontier Level",
    "exploration_mode": "frontier_exploration"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": [],
    "failure_insights": [
      {
        "hypothesis_id": "b3def090-296e-4265-8c45-41f9aaeb1434",
        "level": 2,
        "failure": "Attempted 38 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2. May need to find the correct starting move or object to interact with.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [
            6
          ],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "1a43f188-d8fb-4b24-89e8-72b06a6cc71d",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      },
      {
        "hypothesis_id": "e668160e-df50-4391-8789-adee7e93f88b",
        "level": 2,
        "failure": "Attempted 0 actions on level 2 without score increase. Early exploration attempt.",
        "strategy": "Levels 1-1 are solvable. Focus exploration on level 2.",
        "confidence": 0.5,
        "validated": false,
        "actionable": {
          "avoid_actions": [],
          "prefer_actions": [],
          "avoid_directions": [],
          "prefer_directions": [],
          "avoid_colors": [],
          "target_colors": [],
          "patterns_detected": []
        }
      }
    ]
  },
  "7_action": {
    "action_code": "ACTION6",
    "reasoning": "Network hypotheses (3 insights, 0 validated)",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {
      "failure_hypotheses": 3
    }
  },
  "coordinate": {
    "x": 0,
    "y": 9
  },
  "visual_reason": "Rare color (14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) (19 pixels)"
}
Show less
Frame 44
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "color_9 object moved up",
      "position (24, 12) changed from color_12 to color_9",
      "position (25, 12) changed from color_12 to color_9",
      "position (26, 12) changed from color_12 to color_9",
      "position (27, 12) changed from color_12 to color_9",
      "position (28, 12) changed from color_12 to color_9",
      "position (29, 12) changed from color_12 to color_9",
      "position (30, 12) changed from color_12 to color_9",
      "position (31, 12) changed from color_12 to color_9",
      "position (32, 12) changed from color_12 to color_9",
      "position (33, 12) changed from color_12 to color_9",
      "position (34, 12) changed from color_12 to color_9",
      "position (35, 12) changed from color_12 to color_9",
      "position (36, 12) changed from color_12 to color_9",
      "position (37, 12) changed from color_12 to color_9",
      "position (38, 12) changed from color_12 to color_9",
      "position (39, 12) changed from color_12 to color_9",
      "position (40, 12) changed from color_12 to color_9",
      "position (41, 12) changed from color_12 to color_9",
      "position (42, 12) changed from color_12 to color_9",
      "position (43, 12) changed from color_12 to color_9"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:23.043295",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 43
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "color_9 object moved right",
      "position (20, 16) changed from color_9 to color_12",
      "position (21, 16) changed from color_9 to color_12",
      "position (22, 16) changed from color_9 to color_12",
      "position (23, 16) changed from color_9 to color_12",
      "position (40, 16) changed from color_12 to color_9",
      "position (41, 16) changed from color_12 to color_9",
      "position (42, 16) changed from color_12 to color_9",
      "position (43, 16) changed from color_12 to color_9",
      "position (20, 17) changed from color_9 to color_12",
      "position (21, 17) changed from color_9 to color_12",
      "position (22, 17) changed from color_9 to color_12",
      "position (23, 17) changed from color_9 to color_12",
      "position (40, 17) changed from color_12 to color_9",
      "position (41, 17) changed from color_12 to color_9",
      "position (42, 17) changed from color_12 to color_9",
      "position (43, 17) changed from color_12 to color_9",
      "position (20, 18) changed from color_9 to color_12",
      "position (21, 18) changed from color_9 to color_12",
      "position (22, 18) changed from color_9 to color_12",
      "position (23, 18) changed from color_9 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:22.206992",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 42
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "color_9 object moved right",
      "position (16, 16) changed from color_9 to color_12",
      "position (17, 16) changed from color_9 to color_12",
      "position (18, 16) changed from color_9 to color_12",
      "position (19, 16) changed from color_9 to color_12",
      "position (36, 16) changed from color_12 to color_9",
      "position (37, 16) changed from color_12 to color_9",
      "position (38, 16) changed from color_12 to color_9",
      "position (39, 16) changed from color_12 to color_9",
      "position (16, 17) changed from color_9 to color_12",
      "position (17, 17) changed from color_9 to color_12",
      "position (18, 17) changed from color_9 to color_12",
      "position (19, 17) changed from color_9 to color_12",
      "position (36, 17) changed from color_12 to color_9",
      "position (37, 17) changed from color_12 to color_9",
      "position (38, 17) changed from color_12 to color_9",
      "position (39, 17) changed from color_12 to color_9",
      "position (16, 18) changed from color_9 to color_12",
      "position (17, 18) changed from color_9 to color_12",
      "position (18, 18) changed from color_9 to color_12",
      "position (19, 18) changed from color_9 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:21.194085",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 41
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "color_9 object moved right",
      "position (12, 16) changed from color_9 to color_12",
      "position (13, 16) changed from color_9 to color_12",
      "position (14, 16) changed from color_9 to color_12",
      "position (15, 16) changed from color_9 to color_12",
      "position (32, 16) changed from color_12 to color_9",
      "position (33, 16) changed from color_12 to color_9",
      "position (34, 16) changed from color_12 to color_9",
      "position (35, 16) changed from color_12 to color_9",
      "position (12, 17) changed from color_9 to color_12",
      "position (13, 17) changed from color_9 to color_12",
      "position (14, 17) changed from color_9 to color_12",
      "position (15, 17) changed from color_9 to color_12",
      "position (32, 17) changed from color_12 to color_9",
      "position (33, 17) changed from color_12 to color_9",
      "position (34, 17) changed from color_12 to color_9",
      "position (35, 17) changed from color_12 to color_9",
      "position (12, 18) changed from color_9 to color_12",
      "position (13, 18) changed from color_9 to color_12",
      "position (14, 18) changed from color_9 to color_12",
      "position (15, 18) changed from color_9 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:20.552036",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 40
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "color_9 object moved up",
      "position (12, 16) changed from color_12 to color_9",
      "position (13, 16) changed from color_12 to color_9",
      "position (14, 16) changed from color_12 to color_9",
      "position (15, 16) changed from color_12 to color_9",
      "position (16, 16) changed from color_12 to color_9",
      "position (17, 16) changed from color_12 to color_9",
      "position (18, 16) changed from color_12 to color_9",
      "position (19, 16) changed from color_12 to color_9",
      "position (20, 16) changed from color_12 to color_9",
      "position (21, 16) changed from color_12 to color_9",
      "position (22, 16) changed from color_12 to color_9",
      "position (23, 16) changed from color_12 to color_9",
      "position (24, 16) changed from color_12 to color_9",
      "position (25, 16) changed from color_12 to color_9",
      "position (26, 16) changed from color_12 to color_9",
      "position (27, 16) changed from color_12 to color_9",
      "position (28, 16) changed from color_12 to color_9",
      "position (29, 16) changed from color_12 to color_9",
      "position (30, 16) changed from color_12 to color_9",
      "position (31, 16) changed from color_12 to color_9"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:19.662398",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 39
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "color_9 object moved left",
      "position (12, 20) changed from color_12 to color_9",
      "position (13, 20) changed from color_12 to color_9",
      "position (14, 20) changed from color_12 to color_9",
      "position (15, 20) changed from color_12 to color_9",
      "position (32, 20) changed from color_9 to color_12",
      "position (33, 20) changed from color_9 to color_12",
      "position (34, 20) changed from color_9 to color_12",
      "position (35, 20) changed from color_9 to color_12",
      "position (12, 21) changed from color_12 to color_9",
      "position (13, 21) changed from color_12 to color_9",
      "position (14, 21) changed from color_12 to color_9",
      "position (15, 21) changed from color_12 to color_9",
      "position (32, 21) changed from color_9 to color_12",
      "position (33, 21) changed from color_9 to color_12",
      "position (34, 21) changed from color_9 to color_12",
      "position (35, 21) changed from color_9 to color_12",
      "position (12, 22) changed from color_12 to color_9",
      "position (13, 22) changed from color_12 to color_9",
      "position (14, 22) changed from color_12 to color_9",
      "position (15, 22) changed from color_12 to color_9"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:18.807782",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 38
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "color_9 object moved down",
      "position (16, 16) changed from color_9 to color_12",
      "position (17, 16) changed from color_9 to color_12",
      "position (18, 16) changed from color_9 to color_12",
      "position (19, 16) changed from color_9 to color_12",
      "position (20, 16) changed from color_9 to color_12",
      "position (21, 16) changed from color_9 to color_12",
      "position (22, 16) changed from color_9 to color_12",
      "position (23, 16) changed from color_9 to color_12",
      "position (24, 16) changed from color_9 to color_12",
      "position (25, 16) changed from color_9 to color_12",
      "position (26, 16) changed from color_9 to color_12",
      "position (27, 16) changed from color_9 to color_12",
      "position (28, 16) changed from color_9 to color_12",
      "position (29, 16) changed from color_9 to color_12",
      "position (30, 16) changed from color_9 to color_12",
      "position (31, 16) changed from color_9 to color_12",
      "position (32, 16) changed from color_9 to color_12",
      "position (33, 16) changed from color_9 to color_12",
      "position (34, 16) changed from color_9 to color_12",
      "position (35, 16) changed from color_9 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:17.951364",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 37
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "color_9 object moved left",
      "position (16, 16) changed from color_12 to color_9",
      "position (17, 16) changed from color_12 to color_9",
      "position (18, 16) changed from color_12 to color_9",
      "position (19, 16) changed from color_12 to color_9",
      "position (36, 16) changed from color_9 to color_12",
      "position (37, 16) changed from color_9 to color_12",
      "position (38, 16) changed from color_9 to color_12",
      "position (39, 16) changed from color_9 to color_12",
      "position (16, 17) changed from color_12 to color_9",
      "position (17, 17) changed from color_12 to color_9",
      "position (18, 17) changed from color_12 to color_9",
      "position (19, 17) changed from color_12 to color_9",
      "position (36, 17) changed from color_9 to color_12",
      "position (37, 17) changed from color_9 to color_12",
      "position (38, 17) changed from color_9 to color_12",
      "position (39, 17) changed from color_9 to color_12",
      "position (16, 18) changed from color_12 to color_9",
      "position (17, 18) changed from color_12 to color_9",
      "position (18, 18) changed from color_12 to color_9",
      "position (19, 18) changed from color_12 to color_9"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:17.299480",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 36
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "color_9 object moved right",
      "position (16, 16) changed from color_9 to color_12",
      "position (17, 16) changed from color_9 to color_12",
      "position (18, 16) changed from color_9 to color_12",
      "position (19, 16) changed from color_9 to color_12",
      "position (36, 16) changed from color_12 to color_9",
      "position (37, 16) changed from color_12 to color_9",
      "position (38, 16) changed from color_12 to color_9",
      "position (39, 16) changed from color_12 to color_9",
      "position (16, 17) changed from color_9 to color_12",
      "position (17, 17) changed from color_9 to color_12",
      "position (18, 17) changed from color_9 to color_12",
      "position (19, 17) changed from color_9 to color_12",
      "position (36, 17) changed from color_12 to color_9",
      "position (37, 17) changed from color_12 to color_9",
      "position (38, 17) changed from color_12 to color_9",
      "position (39, 17) changed from color_12 to color_9",
      "position (16, 18) changed from color_9 to color_12",
      "position (17, 18) changed from color_9 to color_12",
      "position (18, 18) changed from color_9 to color_12",
      "position (19, 18) changed from color_9 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:16.455088",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 35
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "color_14 object disappeared from (51, 0)",
      "color_14 object disappeared from (52, 0)",
      "color_14 object disappeared from (53, 0)",
      "color_14 object disappeared from (54, 0)",
      "color_14 object disappeared from (55, 0)",
      "color_14 object disappeared from (56, 0)",
      "color_14 object disappeared from (57, 0)",
      "color_14 object disappeared from (58, 0)",
      "color_14 object disappeared from (59, 0)",
      "color_14 object disappeared from (60, 0)",
      "color_14 object disappeared from (61, 0)",
      "color_14 object disappeared from (62, 0)",
      "color_14 object disappeared from (63, 0)",
      "position (36, 8) changed from color_6 to color_12",
      "position (37, 8) changed from color_6 to color_12",
      "position (38, 8) changed from color_6 to color_12",
      "position (39, 8) changed from color_6 to color_12",
      "position (36, 9) changed from color_6 to color_12",
      "position (37, 9) changed from color_6 to color_12",
      "position (38, 9) changed from color_6 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:15.584625",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 34
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:14.748267",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 33
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION1",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:13.912121",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 32
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION2",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:13.192401",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION1",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 31
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:12.362146",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION2",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 30
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:11.732874",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 29
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION5",
    "frame_changes": [
      "position (36, 8) changed from color_12 to color_6",
      "position (37, 8) changed from color_12 to color_6",
      "position (38, 8) changed from color_12 to color_6",
      "position (39, 8) changed from color_12 to color_6",
      "position (36, 9) changed from color_12 to color_6",
      "position (37, 9) changed from color_12 to color_6",
      "position (38, 9) changed from color_12 to color_6",
      "position (39, 9) changed from color_12 to color_6",
      "position (36, 10) changed from color_12 to color_6",
      "position (37, 10) changed from color_12 to color_6",
      "position (38, 10) changed from color_12 to color_6",
      "position (39, 10) changed from color_12 to color_6",
      "position (36, 11) changed from color_12 to color_6",
      "position (37, 11) changed from color_12 to color_6",
      "position (38, 11) changed from color_12 to color_6",
      "position (39, 11) changed from color_12 to color_6",
      "position (36, 12) changed from color_12 to color_6",
      "position (37, 12) changed from color_12 to color_6",
      "position (38, 12) changed from color_12 to color_6",
      "position (39, 12) changed from color_12 to color_6"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:10.831219",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 28
{
  "action": "ACTION6",
  "reasoning": "PIONEER replaying proven sequence seq_732f (target: LNone)",
  "agent_role": "pioneer",
  "optimizer_target_level": null,
  "sequence_id": "seq_732f3fabe1e340be",
  "replay_step": 7,
  "total_steps": 23,
  "coordinate": {
    "x": 29,
    "y": 13
  },
  "checkpoint_validation": true,
  "role_compliance": "pioneer following sequence script"
}
Show less
Frame 6
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION3",
    "frame_changes": [
      "color_9 object moved left",
      "position (16, 16) changed from color_12 to color_9",
      "position (17, 16) changed from color_12 to color_9",
      "position (18, 16) changed from color_12 to color_9",
      "position (19, 16) changed from color_12 to color_9",
      "position (36, 16) changed from color_9 to color_12",
      "position (37, 16) changed from color_9 to color_12",
      "position (38, 16) changed from color_9 to color_12",
      "position (39, 16) changed from color_9 to color_12",
      "position (16, 17) changed from color_12 to color_9",
      "position (17, 17) changed from color_12 to color_9",
      "position (18, 17) changed from color_12 to color_9",
      "position (19, 17) changed from color_12 to color_9",
      "position (36, 17) changed from color_9 to color_12",
      "position (37, 17) changed from color_9 to color_12",
      "position (38, 17) changed from color_9 to color_12",
      "position (39, 17) changed from color_9 to color_12",
      "position (16, 18) changed from color_12 to color_9",
      "position (17, 18) changed from color_12 to color_9",
      "position (18, 18) changed from color_12 to color_9",
      "position (19, 18) changed from color_12 to color_9"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:09.236348",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION5",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 5
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "color_9 object moved right",
      "position (16, 16) changed from color_9 to color_12",
      "position (17, 16) changed from color_9 to color_12",
      "position (18, 16) changed from color_9 to color_12",
      "position (19, 16) changed from color_9 to color_12",
      "position (36, 16) changed from color_12 to color_9",
      "position (37, 16) changed from color_12 to color_9",
      "position (38, 16) changed from color_12 to color_9",
      "position (39, 16) changed from color_12 to color_9",
      "position (16, 17) changed from color_9 to color_12",
      "position (17, 17) changed from color_9 to color_12",
      "position (18, 17) changed from color_9 to color_12",
      "position (19, 17) changed from color_9 to color_12",
      "position (36, 17) changed from color_12 to color_9",
      "position (37, 17) changed from color_12 to color_9",
      "position (38, 17) changed from color_12 to color_9",
      "position (39, 17) changed from color_12 to color_9",
      "position (16, 18) changed from color_9 to color_12",
      "position (17, 18) changed from color_9 to color_12",
      "position (18, 18) changed from color_9 to color_12",
      "position (19, 18) changed from color_9 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:08.335528",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION3",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 4
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "color_9 object moved right",
      "position (12, 16) changed from color_9 to color_12",
      "position (13, 16) changed from color_9 to color_12",
      "position (14, 16) changed from color_9 to color_12",
      "position (15, 16) changed from color_9 to color_12",
      "position (32, 16) changed from color_12 to color_9",
      "position (33, 16) changed from color_12 to color_9",
      "position (34, 16) changed from color_12 to color_9",
      "position (35, 16) changed from color_12 to color_9",
      "position (12, 17) changed from color_9 to color_12",
      "position (13, 17) changed from color_9 to color_12",
      "position (14, 17) changed from color_9 to color_12",
      "position (15, 17) changed from color_9 to color_12",
      "position (32, 17) changed from color_12 to color_9",
      "position (33, 17) changed from color_12 to color_9",
      "position (34, 17) changed from color_12 to color_9",
      "position (35, 17) changed from color_12 to color_9",
      "position (12, 18) changed from color_9 to color_12",
      "position (13, 18) changed from color_9 to color_12",
      "position (14, 18) changed from color_9 to color_12",
      "position (15, 18) changed from color_9 to color_12"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "Learned: control color_9",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:07.508662",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 3
{
  "action": "ACTION6",
  "reasoning": "PIONEER replaying proven sequence seq_732f (target: LNone)",
  "agent_role": "pioneer",
  "optimizer_target_level": null,
  "sequence_id": "seq_732f3fabe1e340be",
  "replay_step": 3,
  "total_steps": 23,
  "coordinate": {
    "x": 37,
    "y": 2
  },
  "checkpoint_validation": true,
  "role_compliance": "pioneer following sequence script"
}
Show less
Frame 2
{
  "1_identity": {
    "agent_id": "offspring_3b8d9805",
    "role": "pioneer",
    "generation": 295,
    "working_theory": "I control 3 objects and move with directional actions",
    "self_model": {
      "objects_agent_controls": [
        "x:32,y:24",
        "x:33,y:24",
        "x:34,y:24"
      ],
      "aggregated_controlled": [],
      "control_confidence": 0.75,
      "object_dependencies": [],
      "network_control_hypotheses": [
        {
          "id": "oc_sp80_L1_357fb97d",
          "controlled": [
            "x:32,y:24",
            "x:33,y:24",
            "x:34,y:24"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_e1c4b007",
          "controlled": [
            "x:32,y:28",
            "x:33,y:28",
            "x:34,y:28"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        },
        {
          "id": "oc_sp80_L1_a1a84ca6",
          "controlled": [
            "x:32,y:32",
            "x:33,y:32",
            "x:34,y:32"
          ],
          "reliability": 0.75,
          "validated_by_win": 1
        }
      ],
      "tetrahedral_perception": {
        "self_objects": [],
        "goal_objects": [],
        "threat_objects": [],
        "mood": {
          "valence": 0,
          "arousal": 0,
          "dominance": 0
        }
      },
      "control_source": "network_bootstrap"
    },
    "genome": {
      "status": "NULL - 404 Not Found"
    }
  },
  "2_delta": {
    "last_action": "ACTION4",
    "frame_changes": [
      "NULL - 304 Not Modified"
    ],
    "score_change": 0,
    "level_change": false,
    "self_model_update": "NULL - 425 Too Early",
    "world_model_update": "NULL - 425 Too Early",
    "theory_validation": "NULL - 425 Too Early"
  },
  "3_understanding": {
    "Q1_what_is_happening": "Starting game sp80-0605ab9e5b2a, observing initial state",
    "Q2_how_does_this_feel": "Neutral - no actions taken yet",
    "Q3_what_worked_before": "No history yet - will observe what works",
    "Q4_what_should_i_try": "Explore to understand game mechanics",
    "Q5_how_confident": 0.3
  },
  "4_network_wisdom": {
    "private_memory": "NULL - 425 Too Early",
    "network_strength": "NULL - 425 Too Early",
    "self_trust_bias": "NULL - 425 Too Early",
    "decision_weight": "NULL - 425 Too Early",
    "conflict_detected": false,
    "two_streams_narrative": "NULL - 425 Too Early"
  },
  "4.5_resonance": {
    "queried": false,
    "status": "NULL - 102 Computation pending",
    "reason": "Query gate: pioneer at 0.00 novelty"
  },
  "5_context": {
    "game_id": "sp80-0605ab9e5b2a",
    "level": 1,
    "score": 0,
    "timestamp": "2025-12-28T18:55:06.349551",
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "is_frontier": false,
    "frontier_status": "explored",
    "exploration_mode": "network_guided"
  },
  "6_environment": {
    "obstacles": [
      {
        "position": [
          0,
          31
        ],
        "color": 14
      },
      {
        "position": [
          29,
          31
        ],
        "color": 12
      },
      {
        "position": [
          17,
          21
        ],
        "color": 9
      },
      {
        "position": [
          55,
          21
        ],
        "color": 11
      },
      {
        "position": [
          55,
          45
        ],
        "color": 11
      }
    ],
    "goals": [],
    "inferred_goals": [],
    "agent_position": null,
    "network_hypotheses": []
  },
  "7_action": {
    "action_code": "ACTION4",
    "reasoning": "PIONEER mode | Score: 0.0",
    "emotional_state": "neutral"
  },
  "8_primitives": {
    "cods_operators_used": [],
    "features_activated": [
      "PATTERN_LEARNING",
      "SENSATION_NAVIGATION",
      "VISUAL_ANALYSIS"
    ],
    "decision_contributors": {}
  }
}
Show less
Frame 1
{
  "action": "ACTION6",
  "reasoning": "PIONEER replaying proven sequence seq_732f (target: LNone)",
  "agent_role": "pioneer",
  "optimizer_target_level": null,
  "sequence_id": "seq_732f3fabe1e340be",
  "replay_step": 1,
  "total_steps": 23,
  "coordinate": {
    "x": 31,
    "y": 0
  },
  "checkpoint_validation": true,
  "role_compliance": "pioneer following sequence script"
}
Show less
© 2025 ARC Prize Foundation.ARC-AGI-3 Preview Replay: sp80-0605ab9e5b2a - 8fe2817b-acb6-4400-a339-2c2a4f1d3d16