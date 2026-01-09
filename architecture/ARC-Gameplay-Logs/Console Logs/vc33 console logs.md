ACTION6 to API with coordinates (31, 32)
2026-01-09 07:16:12,555 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:12,559 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (52,12)
2026-01-09 07:16:12,571 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:12,572 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 143x consecutively. Will try alternative prediction types.
2026-01-09 07:16:12,624 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:12,691 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:12,695 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:12,731 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:12,737 - core_gameplay - WARNING - [THEORY] CHANGED: Previous 'I control 10 objects and move with directional actions' vs merged evidence: {'moveable': 10.0, 'toggleable': 0.0} (raw current: {'moveable': 10, 'toggleable': 0}, network: {'moveable': 0, 'toggleable': 0}, weights: self=0.5, network=0.5)
2026-01-09 07:16:12,837 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=20)
2026-01-09 07:16:12,849 - action_handler - INFO - ACTION6 target found: (60, 12) - Grid exploration (60,12) - systematic search
2026-01-09 07:16:12,850 - core_gameplay - INFO - ACTION6 at (60, 12): micro rollout: probe salience | Visual: Grid exploration (60,12) - systematic search
2026-01-09 07:16:12,851 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (60, 12)
2026-01-09 07:16:12,854 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:12,861 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (27,61)
2026-01-09 07:16:12,875 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:12,876 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 80x consecutively. Will try alternative prediction types.2026-01-09 07:16:12,936 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:13,008 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:13,011 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:13,052 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-09 07:16:13,182 - visual_analyzer - INFO - [GRID] Generated 3 grid exploration targets (index=385)
2026-01-09 07:16:13,199 - action_handler - WARNING - [WARN] Coordinate oscillation detected: {(2, 31)}
2026-01-09 07:16:13,200 - action_handler - WARNING - [SYNC] Coordinate oscillation detected (unproductive) - trying pseudo-button pathfinding
2026-01-09 07:16:13,201 - action_handler - INFO - [TARGET] Pathfinding target: (37, 61)
2026-01-09 07:16:13,202 - action_handler - INFO - ACTION6 target found: (37, 61) - Pseudo-button pathfinding: Combination point between oscillating targets
2026-01-09 07:16:13,204 - core_gameplay - INFO - ACTION6 at (37, 61): micro rollout: probe salience | Visual: Pseudo-button pathfinding: Combination point between oscillating targets
2026-01-09 07:16:13,206 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (37, 61)
2026-01-09 07:16:13,209 - arc_api_client - INFO - ACTION4 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:13,292 - agent_self_model - INFO - [DISCOVERY] Found control: obj_9 responds to ACTION4
2026-01-09 07:16:13,293 - core_gameplay - INFO - [DISCOVERY] ACTION4 controls obj_9 (shared to network for ls20 L2)
2026-01-09 07:16:13,438 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:13,454 - agent_self_model - INFO - [METACOG] PREDICTION CORRECT: Theory 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_3 control with ACTION4... -> forced exploration' confirmed!
2026-01-09 07:16:13,482 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=ls20-fa137e247ce6
2026-01-09 07:16:13,505 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION1 - Testing obj_5 control with ACTION1
2026-01-09 07:16:13,506 - core_gameplay - INFO - [QUESTIONING] ACTION1 blocked by ['Q9'], substituting ACTION6
2026-01-09 07:16:13,508 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_5 control with ACTION1... -> forced exploration' then 1 should cause 'object_control'
2026-01-09 07:16:13,557 - agent_self_model - INFO - [NETWORK-INVENTORY] ls20 L2: 2 toggleable, 25 moveable, 0 interactable positions
2026-01-09 07:16:13,569 - core_gameplay - INFO - [FRAME->SELF] ACTION4 caused color_9 
to move right
2026-01-09 07:16:13,660 - arc_api_client - INFO - Sending ACTION1 to API
2026-01-09 07:16:13,675 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:13,802 - arc_api_client - INFO - Sending ACTION4 to API
2026-01-09 07:16:13,805 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:13,810 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (60,12)
2026-01-09 07:16:13,873 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:13,874 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 90x consecutively. Will try alternative prediction types.2026-01-09 07:16:13,890 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:13,979 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:13,984 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:14,024 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:14,136 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=25)
2026-01-09 07:16:14,149 - action_handler - INFO - ACTION6 target found: (52, 20) - Grid exploration (52,20) - systematic search
2026-01-09 07:16:14,150 - core_gameplay - INFO - ACTION6 at (52, 20): micro rollout: probe salience | Visual: Grid exploration (52,20) - systematic search
2026-01-09 07:16:14,151 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (52, 20)
2026-01-09 07:16:14,156 - arc_api_client - INFO - ACTION2 API response - State: NOT_FINISHED, Score: 2
2026-01-09 07:16:14,323 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:14,326 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:14,344 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: [DISCOVERY] Testing obj_2 control with ACTION2' -> 'REVISED: Action from explore: [DISCOVERY] Testing obj_2 control with ACTION2 [failed: object_control]'    
2026-01-09 07:16:14,423 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=vc33-6ae7bf49eea5
2026-01-09 07:16:14,438 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION3 - Testing obj_2 control with ACTION3
2026-01-09 07:16:14,441 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: [DISCOVERY] Testing obj_2 control with ACTION3' then ACTION3 should cause 'object_control'
2026-01-09 07:16:14,560 - arc_api_client - INFO - Sending ACTION3 to API
2026-01-09 07:16:14,577 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:14,582 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (60,12)
2026-01-09 07:16:14,593 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:14,594 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 144x consecutively. Will try alternative prediction types.
2026-01-09 07:16:14,614 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:14,670 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:14,725 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:14,775 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:14,784 - core_gameplay - WARNING - [THEORY] CHANGED: Previous 'I control 10 objects and move with directional actions' vs merged evidence: {'moveable': 10.0, 'toggleable': 0.0} (raw current: {'moveable': 10, 'toggleable': 0}, network: {'moveable': 0, 'toggleable': 0}, weights: self=0.5, network=0.5)
2026-01-09 07:16:14,853 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=25)
2026-01-09 07:16:14,855 - action_handler - INFO - ACTION6 target found: (52, 20) - Grid exploration (52,20) - systematic search
2026-01-09 07:16:14,856 - core_gameplay - INFO - ACTION6 at (52, 20): micro rollout: probe salience | Visual: Grid exploration (52,20) - systematic search
2026-01-09 07:16:14,856 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (52, 20)
2026-01-09 07:16:14,860 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:14,902 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (37,61)
2026-01-09 07:16:14,926 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:14,928 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 81x consecutively. Will try alternative prediction types.2026-01-09 07:16:14,950 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:15,239 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:15,271 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:15,360 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-09 07:16:15,522 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=390)
2026-01-09 07:16:15,534 - action_handler - WARNING - [WARN] Coordinate oscillation detected: {(2, 31)}
2026-01-09 07:16:15,535 - action_handler - WARNING - [SYNC] Coordinate oscillation detected (unproductive) - trying pseudo-button pathfinding
2026-01-09 07:16:15,535 - action_handler - INFO - [TARGET] Pathfinding target: (32, 61)
2026-01-09 07:16:15,536 - action_handler - INFO - ACTION6 target found: (32, 61) - Pseudo-button pathfinding: Combination point between oscillating targets
2026-01-09 07:16:15,537 - core_gameplay - INFO - ACTION6 at (32, 61): micro rollout: probe salience | Visual: Pseudo-button pathfinding: Combination point between oscillating targets
2026-01-09 07:16:15,538 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (32, 61)
2026-01-09 07:16:15,542 - arc_api_client - INFO - ACTION1 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:15,722 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:15,739 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:15,757 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_5 control with ACTION1... -> 
forced exploration' -> 'REVISED: Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_5 control with ACTION1... -> forced exploration [failed: object_control]'  
2026-01-09 07:16:15,812 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=ls20-fa137e247ce6
2026-01-09 07:16:15,841 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION2 - Testing obj_5 control with ACTION2
2026-01-09 07:16:15,842 - core_gameplay - INFO - [QUESTIONING] ACTION2 blocked by ['Q9'], substituting ACTION6
2026-01-09 07:16:15,844 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_5 control with ACTION2... -> forced exploration' then 3 should cause 'object_control'
2026-01-09 07:16:15,886 - agent_self_model - INFO - [NETWORK-INVENTORY] ls20 L2: 2 toggleable, 25 moveable, 0 interactable positions
2026-01-09 07:16:15,972 - arc_api_client - INFO - Sending ACTION3 to API
2026-01-09 07:16:15,987 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-09 07:16:16,011 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (45, 37)
2026-01-09 07:16:16,016 - arc_api_client - INFO - ACTION4 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:16,237 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:16,364 - arc_api_client - INFO - Sending ACTION1 to API
2026-01-09 07:16:16,383 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:16,388 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (52,20)
2026-01-09 07:16:16,397 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:16,398 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 91x consecutively. Will try alternative prediction types.2026-01-09 07:16:16,426 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:16,514 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:16,562 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:16,596 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:16,689 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=30)
2026-01-09 07:16:16,701 - visual_analyzer - INFO - All targets clicked and no frame changes - forcing exploration expansion
2026-01-09 07:16:16,701 - action_handler - INFO - ACTION6 target found: (30, 0) - Rare color 5 (29 pixels)
2026-01-09 07:16:16,702 - core_gameplay - INFO - ACTION6 at (30, 0): micro rollout: probe salience | Visual: Rare color 5 (29 pixels)
2026-01-09 07:16:16,703 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (30, 0)
2026-01-09 07:16:16,706 - arc_api_client - INFO - ACTION3 API response - State: NOT_FINISHED, Score: 2
2026-01-09 07:16:16,831 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:16,834 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:16,835 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 5x consecutively. Will try alternative prediction types.
2026-01-09 07:16:16,885 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: [DISCOVERY] Testing obj_2 control with ACTION3' -> 'REVISED: Action from explore: [DISCOVERY] Testing obj_2 control with ACTION3 [failed: object_control]'    
2026-01-09 07:16:16,923 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=vc33-6ae7bf49eea5
2026-01-09 07:16:16,925 - visual_analyzer - INFO - Stagnation detected - expanding exploration radius: 9 -> 13 (+4)
2026-01-09 07:16:16,939 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION4 - Testing obj_2 control with ACTION4
2026-01-09 07:16:16,942 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: [DISCOVERY] Testing obj_2 control with ACTION4' then ACTION4 should cause 'frame_change'
2026-01-09 07:16:17,055 - arc_api_client - INFO - Sending ACTION4 to API
2026-01-09 07:16:17,071 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:17,075 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (52,20)
2026-01-09 07:16:17,086 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:17,087 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 145x consecutively. Will try alternative prediction types.
2026-01-09 07:16:17,102 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:17,167 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:17,222 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:17,266 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:17,272 - core_gameplay - WARNING - [THEORY] CHANGED: Previous 'I control 10 objects and move with directional actions' vs merged evidence: {'moveable': 10.0, 'toggleable': 0.0} (raw current: {'moveable': 10, 'toggleable': 0}, network: {'moveable': 0, 'toggleable': 0}, weights: self=0.5, network=0.5)
2026-01-09 07:16:17,381 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=30)
2026-01-09 07:16:17,394 - visual_analyzer - INFO - All targets clicked and no frame changes - forcing exploration expansion
2026-01-09 07:16:17,395 - action_handler - INFO - ACTION6 target found: (30, 0) - Rare color 5 (29 pixels)
2026-01-09 07:16:17,396 - core_gameplay - INFO - ACTION6 at (30, 0): micro rollout: probe salience | Visual: Rare color 5 (29 pixels)
2026-01-09 07:16:17,397 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (30, 0)
2026-01-09 07:16:17,399 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:17,404 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (32,61)
2026-01-09 07:16:17,413 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:17,414 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 82x consecutively. Will try alternative prediction types.2026-01-09 07:16:17,467 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:17,528 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:17,533 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:17,570 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-09 07:16:17,692 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=395)
2026-01-09 07:16:17,704 - action_handler - WARNING - [WARN] Coordinate oscillation detected: {(2, 31)}
2026-01-09 07:16:17,705 - action_handler - WARNING - [SYNC] Coordinate oscillation detected (unproductive) - trying pseudo-button pathfinding
2026-01-09 07:16:17,706 - action_handler - INFO - [TARGET] Pathfinding target: (34, 61)
2026-01-09 07:16:17,707 - action_handler - INFO - ACTION6 target found: (34, 61) - Pseudo-button pathfinding: Combination point between oscillating targets
2026-01-09 07:16:17,707 - core_gameplay - INFO - ACTION6 at (34, 61): micro rollout: probe salience | Visual: Pseudo-button pathfinding: Combination point between oscillating targets
2026-01-09 07:16:17,708 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (34, 61)
2026-01-09 07:16:17,713 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-09 07:16:17,737 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (31, 2)
2026-01-09 07:16:17,740 - arc_api_client - INFO - ACTION3 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:17,898 - agent_self_model - INFO - [DISCOVERY] Found control: obj_9 responds to ACTION3
2026-01-09 07:16:17,900 - core_gameplay - INFO - [DISCOVERY] ACTION3 controls obj_9 (shared to network for ls20 L2)
2026-01-09 07:16:18,014 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:18,019 - agent_self_model - INFO - [METACOG] PREDICTION CORRECT: Theory 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_5 control with ACTION2... -> forced exploration' confirmed!
2026-01-09 07:16:18,079 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=ls20-fa137e247ce6
2026-01-09 07:16:18,105 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION3 - Testing obj_5 control with ACTION3
2026-01-09 07:16:18,106 - core_gameplay - INFO - [QUESTIONING] ACTION3 blocked by ['Q9'], substituting ACTION6
2026-01-09 07:16:18,109 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_5 control with ACTION3... -> forced exploration' then 2 should cause 'object_control'
2026-01-09 07:16:18,144 - agent_self_model - INFO - [NETWORK-INVENTORY] ls20 L2: 2 toggleable, 25 moveable, 0 interactable positions
2026-01-09 07:16:18,152 - core_gameplay - INFO - [FRAME->SELF] ACTION3 caused color_9 
to move left
2026-01-09 07:16:18,230 - arc_api_client - INFO - Sending ACTION2 to API
2026-01-09 07:16:18,248 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:18,252 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (30,0)
2026-01-09 07:16:18,263 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:18,264 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 92x consecutively. Will try alternative prediction types.2026-01-09 07:16:18,280 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:18,348 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:18,403 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:18,439 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:18,541 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=5)
2026-01-09 07:16:18,553 - action_handler - INFO - ACTION6 target found: (14, 29) - Rare color 14 (97 pixels)
2026-01-09 07:16:18,553 - core_gameplay - INFO - ACTION6 at (14, 29): micro rollout: probe salience | Visual: Rare color 14 (97 pixels)
2026-01-09 07:16:18,555 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (14, 29)
2026-01-09 07:16:18,557 - arc_api_client - INFO - ACTION4 API response - State: NOT_FINISHED, Score: 2
2026-01-09 07:16:18,643 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:18,648 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:18,650 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 7x consecutively. Will try alternative prediction types. 
2026-01-09 07:16:18,677 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: [DISCOVERY] Testing obj_2 control with ACTION4' -> 'REVISED: Action from explore: [DISCOVERY] Testing obj_2 control with ACTION4 [failed: frame_change]'      
2026-01-09 07:16:18,751 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=vc33-6ae7bf49eea5
2026-01-09 07:16:18,770 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION1 - Testing obj_11 control with ACTION1
2026-01-09 07:16:18,774 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: [DISCOVERY] Testing obj_11 control with ACTION1' then ACTION1 should cause 'discover_pattern'
2026-01-09 07:16:18,894 - arc_api_client - INFO - Sending ACTION1 to API
2026-01-09 07:16:18,911 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:18,916 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (30,0)
2026-01-09 07:16:18,929 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:18,929 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 146x consecutively. Will try alternative prediction types.
2026-01-09 07:16:18,946 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:18,999 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:19,044 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:19,088 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:19,096 - core_gameplay - WARNING - [THEORY] CHANGED: Previous 'I control 10 objects and move with directional actions' vs merged evidence: {'moveable': 10.0, 'toggleable': 0.0} (raw current: {'moveable': 10, 'toggleable': 0}, network: {'moveable': 0, 'toggleable': 0}, weights: self=0.5, network=0.5)
2026-01-09 07:16:19,205 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=5)
2026-01-09 07:16:19,216 - action_handler - INFO - ACTION6 target found: (14, 29) - Rare color 14 (97 pixels)
2026-01-09 07:16:19,217 - core_gameplay - INFO - ACTION6 at (14, 29): micro rollout: probe salience | Visual: Rare color 14 (97 pixels)
2026-01-09 07:16:19,218 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (14, 29)
2026-01-09 07:16:19,221 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-09 07:16:19,243 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (29, 31)
2026-01-09 07:16:19,247 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:19,289 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (34,61)
2026-01-09 07:16:19,313 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:19,314 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 83x consecutively. Will try alternative prediction types.2026-01-09 07:16:19,330 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:19,408 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:19,413 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:19,452 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-09 07:16:19,583 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=400)
2026-01-09 07:16:19,595 - action_handler - WARNING - [WARN] Coordinate oscillation detected: {(2, 31)}
2026-01-09 07:16:19,596 - action_handler - WARNING - [SYNC] Coordinate oscillation detected (unproductive) - trying pseudo-button pathfinding
2026-01-09 07:16:19,597 - action_handler - INFO - [TARGET] Pathfinding target: (33, 61)
2026-01-09 07:16:19,598 - action_handler - INFO - ACTION6 target found: (33, 61) - Pseudo-button pathfinding: Combination point between oscillating targets
2026-01-09 07:16:19,598 - core_gameplay - INFO - ACTION6 at (33, 61): micro rollout: probe salience | Visual: Pseudo-button pathfinding: Combination point between oscillating targets
2026-01-09 07:16:19,600 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (33, 61)
2026-01-09 07:16:19,611 - arc_api_client - INFO - ACTION1 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:19,733 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:19,811 - arc_api_client - INFO - Sending ACTION2 to API
2026-01-09 07:16:19,813 - arc_api_client - INFO - ACTION2 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:19,961 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:19,965 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:19,981 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_5 control with ACTION3... -> 
forced exploration' -> 'REVISED: Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_5 control with ACTION3... -> forced exploration [failed: object_control]'  
2026-01-09 07:16:20,034 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=ls20-fa137e247ce6
2026-01-09 07:16:20,048 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION4 - Testing obj_5 control with ACTION4
^A2026-01-09 07:16:20,049 - core_gameplay - INFO - [QUESTIONING] ACTION4 blocked by ['Q9'], substituting ACTION6
2026-01-09 07:16:20,051 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_5 control with ACTION4... -> forced exploration' then 4 should cause 'object_control'
2026-01-09 07:16:20,091 - agent_self_model - INFO - [NETWORK-INVENTORY] ls20 L2: 2 toggleable, 25 moveable, 0 interactable positions
2026-01-09 07:16:20,188 - arc_api_client - INFO - Sending ACTION4 to API
2026-01-09 07:16:20,200 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:20,204 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 4 at (14,29)
2026-01-09 07:16:20,221 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:20,222 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 93x consecutively. Will try alternative prediction types.2026-01-09 07:16:20,482 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:20,557 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:20,559 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:20,592 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:20,692 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=10)
2026-01-09 07:16:20,696 - action_handler - INFO - ACTION6 target found: (34, 32) - Rare color 2 (32 pixels)
2026-01-09 07:16:20,697 - core_gameplay - INFO - ACTION6 at (34, 32): micro rollout: probe salience | Visual: Rare color 2 (32 pixels)
2026-01-09 07:16:20,698 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (34, 32)
2026-01-09 07:16:20,702 - arc_api_client - INFO - ACTION1 API response - State: NOT_FINISHED, Score: 2
2026-01-09 07:16:20,817 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:20,821 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:20,821 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 6x consecutively. Will try alternative prediction types.
2026-01-09 07:16:20,853 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: [DISCOVERY] Testing obj_11 control with ACTION1' -> 'REVISED: Action from explore: [DISCOVERY] Testing obj_11 control with ACTION1 [failed: discover_pattern]'2026-01-09 07:16:20,873 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=vc33-6ae7bf49eea5
2026-01-09 07:16:20,886 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION2 - Testing obj_11 control with ACTION2
2026-01-09 07:16:20,889 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: [DISCOVERY] Testing obj_11 control with ACTION2' then ACTION2 should cause 'object_control'
2026-01-09 07:16:21,012 - arc_api_client - INFO - Sending ACTION2 to API
2026-01-09 07:16:21,020 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:21,028 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 4 at (14,29)
2026-01-09 07:16:21,048 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:21,050 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 147x consecutively. Will try alternative prediction types.
2026-01-09 07:16:21,071 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:21,130 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:21,144 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
^A2026-01-09 07:16:21,186 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:21,192 - core_gameplay - WARNING - [THEORY] CHANGED: Previous 'I control 10 objects and move with directional actions' vs merged evidence: {'moveable': 10.0, 'toggleable': 0.0} (raw current: {'moveable': 10, 'toggleable': 0}, network: {'moveable': 0, 'toggleable': 0}, weights: self=0.5, network=0.5)
2026-01-09 07:16:21,265 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=10)
2026-01-09 07:16:21,267 - action_handler - INFO - ACTION6 target found: (34, 32) - Rare color 2 (32 pixels)
2026-01-09 07:16:21,268 - core_gameplay - INFO - ACTION6 at (34, 32): micro rollout: probe salience | Visual: Rare color 2 (32 pixels)
2026-01-09 07:16:21,269 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (34, 32)
2026-01-09 07:16:21,274 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-09 07:16:21,304 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (29, 31)
2026-01-09 07:16:21,307 - arc_api_client - INFO - ACTION4 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:21,338 - agent_self_model - INFO - [DISCOVERY] Found control: obj_9 responds to ACTION4
2026-01-09 07:16:21,340 - core_gameplay - INFO - [DISCOVERY] ACTION4 controls obj_9 (shared to network for ls20 L2)
2026-01-09 07:16:21,481 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:21,487 - agent_self_model - INFO - [METACOG] PREDICTION CORRECT: Theory 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_5 control with ACTION4... -> forced exploration' confirmed!
2026-01-09 07:16:21,509 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=ls20-fa137e247ce6
2026-01-09 07:16:21,559 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION1 - Testing obj_14 control with ACTION1
2026-01-09 07:16:21,560 - core_gameplay - INFO - [QUESTIONING] ACTION1 blocked by ['Q9'], substituting ACTION6
2026-01-09 07:16:21,564 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_14 control with ACTION1... -> 
forced exploration' then 3 should cause 'object_control'
2026-01-09 07:16:21,604 - agent_self_model - INFO - [NETWORK-INVENTORY] ls20 L2: 2 toggleable, 25 moveable, 0 interactable positions
2026-01-09 07:16:21,616 - core_gameplay - INFO - [FRAME->SELF] ACTION4 caused color_9 
to move right
2026-01-09 07:16:21,671 - arc_api_client - INFO - Sending ACTION3 to API
2026-01-09 07:16:21,675 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:21,681 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (33,61)
2026-01-09 07:16:21,693 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:21,694 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 84x consecutively. Will try alternative prediction types.2026-01-09 07:16:21,719 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:21,804 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:21,806 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:21,842 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-09 07:16:21,925 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=405)
2026-01-09 07:16:21,927 - action_handler - WARNING - [WARN] Coordinate oscillation detected: {(2, 31)}
2026-01-09 07:16:21,928 - action_handler - WARNING - [SYNC] Coordinate oscillation detected (unproductive) - trying pseudo-button pathfinding
2026-01-09 07:16:21,929 - action_handler - INFO - [TARGET] Pathfinding target: (53, 61)
2026-01-09 07:16:21,931 - action_handler - INFO - ACTION6 target found: (53, 61) - Pseudo-button pathfinding: Exploration around oscillation pattern (offset=20,0)
2026-01-09 07:16:21,932 - core_gameplay - INFO - ACTION6 at (53, 61): micro rollout: probe salience | Visual: Pseudo-button pathfinding: Exploration around oscillation pattern (offset=20,0)
2026-01-09 07:16:21,933 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (53, 61)
2026-01-09 07:16:21,936 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:21,951 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 4 at (34,32)
2026-01-09 07:16:21,960 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:21,962 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 94x consecutively. Will try alternative prediction types.2026-01-09 07:16:21,978 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:22,039 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:22,042 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:22,086 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:22,182 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=15)
2026-01-09 07:16:22,185 - action_handler - INFO - ACTION6 target found: (52, 12) - Grid exploration (52,12) - systematic search
2026-01-09 07:16:22,185 - core_gameplay - INFO - ACTION6 at (52, 12): micro rollout: probe salience | Visual: Grid exploration (52,12) - systematic search
2026-01-09 07:16:22,187 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (52, 12)
2026-01-09 07:16:22,191 - arc_api_client - INFO - ACTION2 API response - State: NOT_FINISHED, Score: 2
2026-01-09 07:16:22,329 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:22,333 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:22,335 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 6x consecutively. Will try alternative prediction types.
2026-01-09 07:16:22,367 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: [DISCOVERY] Testing obj_11 control with ACTION2' -> 'REVISED: Action from explore: [DISCOVERY] Testing obj_11 control with ACTION2 [failed: object_control]'  
2026-01-09 07:16:22,400 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=vc33-6ae7bf49eea5
2026-01-09 07:16:22,415 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION3 - Testing obj_11 control with ACTION3
2026-01-09 07:16:22,418 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: [DISCOVERY] Testing obj_11 control with ACTION3' then ACTION3 should cause 'frame_change'
2026-01-09 07:16:22,510 - arc_api_client - INFO - Sending ACTION3 to API
2026-01-09 07:16:22,519 - arc_api_client - INFO - ACTION2 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:22,585 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:22,673 - arc_api_client - INFO - Sending ACTION1 to API
2026-01-09 07:16:22,676 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:22,680 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 9 at (7,53)
2026-01-09 07:16:22,686 - agent_self_model - INFO - [DISCOVERY] Toggle detected: obj_9 color 9 -> 12
2026-01-09 07:16:22,688 - agent_self_model - INFO - [TOGGLE-DISCOVERY] Recorded toggle at (7,53): color 9 <-> 12
2026-01-09 07:16:22,689 - agent_self_model - INFO - [DISCOVERY] Click effect: color_9 
-> color_12 at (7,53) type=toggle
2026-01-09 07:16:22,690 - agent_self_model - WARNING - Network click effect sharing failed: table network_object_control_hypotheses has no column named controlled_color    
2026-01-09 07:16:22,713 - agent_self_model - INFO - [METACOG] PREDICTION CORRECT: Theory 'Action from explore: Network hypotheses (3 insights, 0 validated) | ACTION6 salience target' confirmed!
2026-01-09 07:16:22,785 - agent_self_model - INFO - Stored control map for offspring_eabafe34 on ft09-b8377d4b7815 L2: 1 objects (confidence: 1.00)
2026-01-09 07:16:22,810 - agent_self_model - INFO - [NETWORK] Agent offsprin shared 'I am object' hypothesis: oc_ft09_L2_99ed9846 for ft09 L2 (1 objects)
2026-01-09 07:16:22,914 - core_gameplay - INFO - [HYPOTHESIS] Level 2: 3 hypotheses (0 validated)
2026-01-09 07:16:22,919 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: Preoperational exploration: Random ACTION2' then ACTION2 should cause 'frame_change'
2026-01-09 07:16:22,969 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-09 07:16:23,006 - arc_api_client - INFO - Sending ACTION2 to API
2026-01-09 07:16:23,009 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-09 07:16:23,068 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (29, 31)
2026-01-09 07:16:23,071 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:23,087 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 4 at (34,32)
2026-01-09 07:16:23,097 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:23,098 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 148x consecutively. Will try alternative prediction types.
2026-01-09 07:16:23,118 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:23,230 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:23,233 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:23,291 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:23,301 - core_gameplay - WARNING - [THEORY] CHANGED: Previous 'I control 10 objects and move with directional actions' vs merged evidence: {'moveable': 10.0, 'toggleable': 0.0} (raw current: {'moveable': 10, 'toggleable': 0}, network: {'moveable': 0, 'toggleable': 0}, weights: self=0.5, network=0.5)
2026-01-09 07:16:23,389 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=15)
2026-01-09 07:16:23,396 - action_handler - INFO - ACTION6 target found: (52, 12) - Grid exploration (52,12) - systematic search
2026-01-09 07:16:23,397 - core_gameplay - INFO - ACTION6 at (52, 12): micro rollout: probe salience | Visual: Grid exploration (52,12) - systematic search
2026-01-09 07:16:23,398 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (52, 12)
2026-01-09 07:16:23,404 - arc_api_client - INFO - ACTION3 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:23,449 - agent_self_model - INFO - [DISCOVERY] Found control: obj_9 responds to ACTION3
2026-01-09 07:16:23,450 - core_gameplay - INFO - [DISCOVERY] ACTION3 controls obj_9 (shared to network for ls20 L2)
2026-01-09 07:16:23,585 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:23,603 - agent_self_model - INFO - [METACOG] PREDICTION CORRECT: Theory 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_14 control with ACTION1... -> forced exploration' confirmed!
2026-01-09 07:16:23,620 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=ls20-fa137e247ce6
2026-01-09 07:16:23,642 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION2 - Testing obj_14 control with ACTION2
2026-01-09 07:16:23,644 - core_gameplay - INFO - [QUESTIONING] ACTION2 blocked by ['Q9'], substituting ACTION6
2026-01-09 07:16:23,668 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_14 control with ACTION2... -> 
forced exploration' then 2 should cause 'object_control'
2026-01-09 07:16:23,708 - agent_self_model - INFO - [NETWORK-INVENTORY] ls20 L2: 2 toggleable, 25 moveable, 0 interactable positions
2026-01-09 07:16:23,717 - core_gameplay - INFO - [FRAME->SELF] ACTION3 caused color_9 
to move left
2026-01-09 07:16:23,765 - arc_api_client - INFO - Sending ACTION2 to API
2026-01-09 07:16:23,771 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:23,776 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (53,61)
2026-01-09 07:16:23,794 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:23,795 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 85x consecutively. Will try alternative prediction types.2026-01-09 07:16:23,839 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:23,928 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:23,931 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:23,968 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-09 07:16:24,062 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=410)
2026-01-09 07:16:24,064 - action_handler - WARNING - [WARN] Coordinate oscillation detected: {(2, 31)}
2026-01-09 07:16:24,065 - action_handler - WARNING - [SYNC] Coordinate oscillation detected (unproductive) - trying pseudo-button pathfinding
2026-01-09 07:16:24,066 - action_handler - INFO - [TARGET] Pathfinding target: (43, 61)
2026-01-09 07:16:24,067 - action_handler - INFO - ACTION6 target found: (43, 61) - Pseudo-button pathfinding: Combination point between oscillating targets
2026-01-09 07:16:24,068 - core_gameplay - INFO - ACTION6 at (43, 61): micro rollout: probe salience | Visual: Pseudo-button pathfinding: Combination point between oscillating targets
2026-01-09 07:16:24,068 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (43, 61)
2026-01-09 07:16:24,072 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:24,076 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (52,12)
2026-01-09 07:16:24,109 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:24,109 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 95x consecutively. Will try alternative prediction types.2026-01-09 07:16:24,126 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:24,178 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:24,180 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:24,213 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:24,286 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=20)
2026-01-09 07:16:24,289 - action_handler - INFO - ACTION6 target found: (60, 12) - Grid exploration (60,12) - systematic search
2026-01-09 07:16:24,289 - core_gameplay - INFO - ACTION6 at (60, 12): micro rollout: probe salience | Visual: Grid exploration (60,12) - systematic search
2026-01-09 07:16:24,290 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (60, 12)
2026-01-09 07:16:24,295 - arc_api_client - INFO - ACTION3 API response - State: NOT_FINISHED, Score: 2
2026-01-09 07:16:24,396 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:24,400 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:24,400 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 8x consecutively. Will try alternative prediction types. 
2026-01-09 07:16:24,431 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: [DISCOVERY] Testing obj_11 control with ACTION3' -> 'REVISED: Action from explore: [DISCOVERY] Testing obj_11 control with ACTION3 [failed: frame_change]'    
2026-01-09 07:16:24,474 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=vc33-6ae7bf49eea5
2026-01-09 07:16:24,492 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION4 - Testing obj_11 control with ACTION4
2026-01-09 07:16:24,495 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: [DISCOVERY] Testing obj_11 control with ACTION4' then ACTION4 should cause 'discover_pattern'
2026-01-09 07:16:24,600 - arc_api_client - INFO - Sending ACTION4 to API
2026-01-09 07:16:24,605 - arc_api_client - INFO - ACTION2 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:24,773 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:24,777 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:24,817 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: Preoperational exploration: Random ACTION2' -> 'REVISED: Action from explore: Preoperational exploration: Random ACTION2 [failed: frame_change]'
2026-01-09 07:16:24,891 - agent_self_model - INFO - Stored control map for offspring_eabafe34 on ft09-b8377d4b7815 L2: 1 objects (confidence: 1.00)
2026-01-09 07:16:25,002 - core_gameplay - INFO - [HYPOTHESIS] Level 2: 3 hypotheses (0 validated)
2026-01-09 07:16:25,005 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: Preoperational exploration: Random ACTION2' then ACTION2 should cause 'frame_change'
2026-01-09 07:16:25,044 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-09 07:16:25,117 - arc_api_client - INFO - Sending ACTION2 to API
2026-01-09 07:16:25,122 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-09 07:16:25,142 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (21, 58)
2026-01-09 07:16:25,146 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:25,151 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (52,12)
2026-01-09 07:16:25,160 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:25,161 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 149x consecutively. Will try alternative prediction types.
2026-01-09 07:16:25,194 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:25,251 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:25,255 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:25,332 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:25,350 - core_gameplay - WARNING - [THEORY] CHANGED: Previous 'I control 10 objects and move with directional actions' vs merged evidence: {'moveable': 10.0, 'toggleable': 0.0} (raw current: {'moveable': 10, 'toggleable': 0}, network: {'moveable': 0, 'toggleable': 0}, weights: self=0.5, network=0.5)
2026-01-09 07:16:25,473 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=20)
2026-01-09 07:16:25,478 - action_handler - INFO - ACTION6 target found: (60, 12) - Grid exploration (60,12) - systematic search
[DatabaseLogHandler] Auto-cleanup: 5,999 → 5,000 logs
2026-01-09 07:16:25,479 - core_gameplay - INFO - ACTION6 at (60, 12): micro rollout: probe salience | Visual: Grid exploration (60,12) - systematic search
2026-01-09 07:16:25,714 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (60, 12)
2026-01-09 07:16:25,788 - arc_api_client - INFO - ACTION2 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:26,306 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:26,314 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:26,348 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_14 control with ACTION2... -> forced exploration' -> 'REVISED: Action from explore: BLOCKED by ['Q9']: [DISCOVERY] 
Testing obj_14 control with ACTION2... -> forced exploration [failed: object_control]'2026-01-09 07:16:26,376 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=ls20-fa137e247ce6
2026-01-09 07:16:26,415 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION3 - Testing obj_14 control with ACTION3
2026-01-09 07:16:26,418 - core_gameplay - INFO - [QUESTIONING] ACTION3 blocked by ['Q9'], substituting ACTION6
2026-01-09 07:16:26,423 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: BLOCKED by ['Q9']: [DISCOVERY] Testing obj_14 control with ACTION3... -> 
forced exploration' then 3 should cause 'object_control'
2026-01-09 07:16:26,491 - agent_self_model - INFO - [NETWORK-INVENTORY] ls20 L2: 2 toggleable, 25 moveable, 0 interactable positions
2026-01-09 07:16:26,570 - arc_api_client - INFO - Sending ACTION3 to API
2026-01-09 07:16:26,584 - arc_api_client - INFO - ACTION1 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:26,669 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:26,768 - arc_api_client - INFO - Sending ACTION2 to API
2026-01-09 07:16:26,771 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:26,779 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (43,61)
2026-01-09 07:16:26,801 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:26,802 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 86x consecutively. Will try alternative prediction types.2026-01-09 07:16:26,838 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:26,902 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:26,927 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:26,963 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-09 07:16:27,056 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=415)
2026-01-09 07:16:27,058 - action_handler - WARNING - [WARN] Coordinate oscillation detected: {(2, 31)}
2026-01-09 07:16:27,059 - action_handler - WARNING - [SYNC] Coordinate oscillation detected (unproductive) - trying pseudo-button pathfinding
2026-01-09 07:16:27,060 - action_handler - INFO - [TARGET] Pathfinding target: (28, 61)
2026-01-09 07:16:27,061 - action_handler - INFO - ACTION6 target found: (28, 61) - Pseudo-button pathfinding: Exploration around oscillation pattern (offset=-20,0)
2026-01-09 07:16:27,063 - core_gameplay - INFO - ACTION6 at (28, 61): micro rollout: probe salience | Visual: Pseudo-button pathfinding: Exploration around oscillation pattern (offset=-20,0)
2026-01-09 07:16:27,065 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (28, 61)
2026-01-09 07:16:27,069 - arc_api_client - INFO - ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:27,076 - core_gameplay - INFO - [SELECTION] ACTION6 clicked on object color 3 at (60,12)
2026-01-09 07:16:27,102 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:27,103 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 96x consecutively. Will try alternative prediction types.2026-01-09 07:16:27,119 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-09 07:16:27,173 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-09 07:16:27,176 - agent_self_model - INFO - [METACOG] PREDICTION (suppressed type 'frame_change'): Skipping - failed too many times
2026-01-09 07:16:27,211 - agent_self_model - INFO - [NETWORK-INVENTORY] lp85 L2: 0 toggleable, 33 moveable, 0 interactable positions
2026-01-09 07:16:27,285 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=25)
2026-01-09 07:16:27,288 - action_handler - INFO - ACTION6 target found: (52, 20) - Grid exploration (52,20) - systematic search
2026-01-09 07:16:27,289 - core_gameplay - INFO - ACTION6 at (52, 20): micro rollout: probe salience | Visual: Grid exploration (52,20) - systematic search
2026-01-09 07:16:27,289 - arc_api_client - INFO - Sending ACTION6 to API with coordinates (52, 20)
2026-01-09 07:16:27,294 - arc_api_client - INFO - ACTION4 API response - State: NOT_FINISHED, Score: 2
2026-01-09 07:16:27,424 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:27,428 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:27,429 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 7x consecutively. Will try alternative prediction types.
2026-01-09 07:16:27,442 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: [DISCOVERY] Testing obj_11 control with ACTION4' -> 'REVISED: Action from explore: [DISCOVERY] Testing obj_11 control with ACTION4 [failed: discover_pattern]'2026-01-09 07:16:27,482 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=vc33-6ae7bf49eea5
2026-01-09 07:16:27,494 - core_gameplay - INFO - [DISCOVERY PHASE] ACTION1 - Testing obj_5 control with ACTION1
2026-01-09 07:16:27,496 - agent_self_model - INFO - [METACOG] PREDICTION: If 'Action from explore: [DISCOVERY] Testing obj_5 control with ACTION1' then ACTION1 should cause 'object_control'
2026-01-09 07:16:27,592 - arc_api_client - INFO - Sending ACTION1 to API
2026-01-09 07:16:27,598 - arc_api_client - INFO - ACTION2 API response - State: NOT_FINISHED, Score: 1
2026-01-09 07:16:27,722 - core_gameplay - INFO - [PRIMITIVE] Stuck pattern detected by primitives
2026-01-09 07:16:27,726 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'
2026-01-09 07:16:27,771 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action 
from explore: Preoperational exploration: Random ACTION2' -> 'REVISED: Action from explore: Preoperational exploration: Random ACTION2 [failed: frame_change]'
2026-01-09 07:16:27,820 - agent_self_model - INFO - Stored control map for offspring_eabafe34 on ft09-b8377d4b7815 L2: 1 objects (confidence: 1.00)
2026-01-09 07:16:27,911 - core_gameplay - INFO - [HYPOTHESIS] Level 2: 3 hypotheses (0 validated)
