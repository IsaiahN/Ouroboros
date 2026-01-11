
2026-01-10 20:19:05,810 - core_gameplay - INFO -  Recorded validation: seq_93f0ba948e274fe3 by offspring_e922f284 -  Success (63/63 actions)
2026-01-10 20:19:05,811 - core_gameplay - INFO - [OK] Inline replay successful for seq_93f0ba948e274fe3! Reached level 2 (target: 1), Score: 1.0
2026-01-10 20:19:27,064 - core_gameplay - INFO - [3-TRY] SUCCESS on attempt 1: seq_93f0ba94 worked!
2026-01-10 20:19:27,066 - core_gameplay - INFO -  Cumulative replay reached frontier (Level 2, Score 1.0)
2026-01-10 20:19:27,067 - core_gameplay - INFO -  GENERALIST: At frontier (Level 2), exploring until action budget exhausted
2026-01-10 20:19:27,068 - core_gameplay - INFO - [INIT] Starting game loop with 1 levels already completed (score=1.0)
2026-01-10 20:19:27,159 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:19:27,165 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:19:27,334 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:19:27,401 - action_handler - WARNING - [WARN] FRAME DIMENSION CHANGE: (64, 64) → (2, 64) at get_smart_coordinates entry
2026-01-10 20:19:27,403 - action_handler - WARNING - 🔍 NON-STANDARD FRAME SIZE: 2x64 (expected 64x64) at get_smart_coordinates entry
2026-01-10 20:19:27,404 - action_handler - ERROR - [FAIL] FRAME CORRUPTION: Frame too small (2x64), likely API error - aborting game at get_smart_coordinates entry
2026-01-10 20:19:27,405 - action_handler - ERROR - [FAIL] Frame validation failed, falling back to safe coordinates
2026-01-10 20:19:27,406 - core_gameplay - INFO - ACTION6 at (32, 32): micro rollout: probe salience | Visual: Fallback center (frame validation failed)   
2026-01-10 20:19:27,409 - action_handler - WARNING - [WARN] FRAME DIMENSION CHANGE: (64, 64) → (2, 64) in gameplay loop ACTION6
2026-01-10 20:19:27,410 - action_handler - WARNING - 🔍 NON-STANDARD FRAME SIZE: 2x64 (expected 64x64) in gameplay loop ACTION6
2026-01-10 20:19:27,414 - action_handler - ERROR - [FAIL] FRAME CORRUPTION: Frame too small (2x64), likely API error - aborting game in gameplay loop ACTION6
2026-01-10 20:19:27,416 - action_handler - INFO - [SYNC] FRAME RECOVERY [1/20]: Sending ACTION5 to flush corrupt frame
2026-01-10 20:19:27,417 - arc_api_client - INFO - [ft09] Sending ACTION5 to API
2026-01-10 20:19:27,774 - arc_api_client - INFO - [ft09] ACTION5 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:19:27,775 - action_handler - INFO - [OK] FRAME RECOVERY SUCCESS after 1 attempts! Frame: 64x64
2026-01-10 20:19:27,777 - core_gameplay - INFO - [RECOVER] Frame recovered for ACTION6; continuing exploration
2026-01-10 20:19:27,778 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (32, 32)
2026-01-10 20:19:28,082 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:19:28,107 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 4 at (32,32)
2026-01-10 20:19:28,146 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:19:28,201 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:19:28,232 - cods_engine - INFO - [CODS] Testing triggered by score increase: +1.0
2026-01-10 20:19:28,233 - cods_engine - INFO - [CODS] Testing operators: reason=score_increase, game=ft09-b8377d4b7815
2026-01-10 20:19:28,254 - visual_analyzer - INFO - Improvement detected - contracting exploration radius: 5 -> 4
2026-01-10 20:19:28,279 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:19:28,282 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:19:28,336 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:19:28,397 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:19:28,400 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 18)
2026-01-10 20:19:28,514 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:19:28,535 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,18)
2026-01-10 20:19:28,560 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:19:28,671 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:19:28,761 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:19:28,768 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:19:28,819 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:19:28,878 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:19:28,879 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 14)
2026-01-10 20:19:29,191 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:19:29,198 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,14)
2026-01-10 20:19:29,230 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:19:29,276 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:19:29,337 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:19:29,344 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:19:29,407 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:19:29,530 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:19:29,531 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 14)
2026-01-10 20:19:29,849 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:19:29,859 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,14)
2026-01-10 20:19:29,880 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:19:29,934 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:19:29,996 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:19:30,000 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:19:30,045 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:19:30,126 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:19:30,128 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 20)
2026-01-10 20:19:30,499 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:19:30,504 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,20)
2026-01-10 20:19:30,518 - visual_analyzer - INFO - Stagnation detected - expanding exploration radius: 4 -> 6 (+2)
2026-01-10 20:19:30,543 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:19:30,545 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 5x consecutively. Will try alternative prediction types.
2026-01-10 20:19:30,588 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
Database logging error: database is locked
Original message: [GAP] Recorded comprehension gap 'no_delta' for ft09-b8377d4b7815 L2
2026-01-10 20:19:30,650 - core_gameplay - INFO - [GAP] Recorded comprehension gap 'no_delta' for ft09-b8377d4b7815 L2
2026-01-10 20:20:03,438 - core_gameplay - INFO - [FIX5-RECOVERY] Entering recovery mode: stuck_conf=0.75, primitive_stuck=False
2026-01-10 20:20:03,440 - core_gameplay - INFO - [FIX7-IMAGINATION] Spent 0.020 budget on 1 counterfactuals -> ACTIONACTION6
2026-01-10 20:20:03,441 - core_gameplay - INFO - [FIX5+7] [RECOVERY MODE] Breaking stuck pattern (conf=0.75, imagination-guided). Trying ACTIONACTION6    
2026-01-10 20:20:03,444 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: [RECOVERY MODE] Breaking stuck pattern (conf=0.75, imagination-guided). Trying ACTIONACTION6' then ACTIONACTION6 should cause 'frame_change'
2026-01-10 20:20:03,494 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:20:03,573 - core_gameplay - ERROR - ACTION6 reached generic handler - this should not happen. Falling back to visual target.
2026-01-10 20:20:03,596 - action_handler - INFO - ACTION6 target found: (2, 31) - Rare color 14 (12 pixels)
2026-01-10 20:20:03,599 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (2, 31)
2026-01-10 20:20:04,043 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:20:04,052 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:20:04,127 - agent_self_model - INFO - [METACOG-FIX4] Marked ACTION6 as contradicted: frame_change
2026-01-10 20:20:04,128 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: [RECOVERY MODE] Breaking stuck pattern (conf=0.75, imagination-guided). Trying ACTIONACTION6' -> 'REVISED: Action from micro_cf: [RECOVERY MODE] Breaking stuck pattern (conf=0.75, imagination-guided). Trying ACTIONACTION6 [failed: frame_change]'
2026-01-10 20:20:04,173 - cods_engine - INFO - [CODS] Testing triggered by reasoning mention: 'pattern'
2026-01-10 20:20:04,174 - cods_engine - INFO - [CODS] Testing operators: reason=reasoning_mentions_pattern, game=ft09-b8377d4b7815
2026-01-10 20:20:04,205 - core_gameplay - INFO - [SELF-MODEL] ACTION6 target 
from controlled objects: (58,19) - Controlled color 9
2026-01-10 20:20:04,206 - core_gameplay - INFO - [CLOSURE-PROBE] Using ACTION6 at (58,19)
2026-01-10 20:20:04,212 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: Self-model: Controlled color 9' then ACTION6 should cause 'frame_change'
2026-01-10 20:20:04,260 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:20:04,343 - core_gameplay - INFO - ACTION6 at (58, 19): Self-model: Controlled color 9 | Self-model: Controlled color 9
2026-01-10 20:20:04,344 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 19)
2026-01-10 20:20:04,668 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:20:04,726 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,19)
2026-01-10 20:20:04,749 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:20:04,831 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: Self-model: Controlled color 9' -> 'REVISED: Action from micro_cf: Self-model: Controlled color 9 [failed: frame_change]'
2026-01-10 20:20:04,870 - cods_engine - INFO - [CODS] Testing triggered by reasoning mention: 'color'
2026-01-10 20:20:04,872 - cods_engine - INFO - [CODS] Testing operators: reason=reasoning_mentions_color, game=ft09-b8377d4b7815
2026-01-10 20:20:04,911 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:20:04,915 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:20:04,980 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:20:05,096 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:20:05,097 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 20)
2026-01-10 20:20:05,417 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:20:05,429 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,20)
2026-01-10 20:20:05,465 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:20:05,560 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:20:05,668 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:20:05,675 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:20:05,768 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:20:05,846 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:20:05,848 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 21)
2026-01-10 20:20:06,165 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:20:06,176 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,21)
2026-01-10 20:20:06,213 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:20:06,268 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:20:06,433 - visual_analyzer - INFO - Stagnation detected - expanding exploration radius: 6 -> 9 (+3)
2026-01-10 20:20:06,487 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:20:06,517 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:20:06,774 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:20:07,008 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:20:07,052 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 14)
2026-01-10 20:20:07,405 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:20:07,424 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,14)
2026-01-10 20:20:07,454 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:20:07,463 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 5x consecutively. Will try alternative 
prediction types.
2026-01-10 20:20:07,590 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:20:07,830 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:20:07,838 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:20:07,917 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:20:08,048 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:20:08,059 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 14)
2026-01-10 20:20:08,383 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:20:08,394 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,14)
2026-01-10 20:20:08,416 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:20:08,498 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'



2026-01-10 20:21:07,872 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:07,945 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:07,946 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 19)
2026-01-10 20:21:08,262 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:08,284 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,19)
2026-01-10 20:21:08,319 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:08,324 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 16x consecutively. Will try alternative prediction types.
2026-01-10 20:21:08,363 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:08,489 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:08,498 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:08,585 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:08,661 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:08,665 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 18)
2026-01-10 20:21:08,970 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:08,987 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,18)
2026-01-10 20:21:09,006 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:09,008 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 17x consecutively. Will try alternative prediction types.
2026-01-10 20:21:09,067 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:09,210 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:09,220 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:09,270 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:09,322 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:09,323 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 20)
2026-01-10 20:21:09,665 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:09,681 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,20)
2026-01-10 20:21:09,707 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:09,710 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 17x consecutively. Will try alternative prediction types.
2026-01-10 20:21:09,760 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:09,848 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:09,854 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:09,907 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:09,970 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:09,974 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 16)
2026-01-10 20:21:10,322 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:10,332 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,16)
2026-01-10 20:21:10,349 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:10,350 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 17x consecutively. Will try alternative prediction types.
2026-01-10 20:21:10,420 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:10,513 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:10,518 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:10,588 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:10,680 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:10,692 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 19)
2026-01-10 20:21:11,022 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:11,074 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,19)
2026-01-10 20:21:11,098 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:11,099 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 18x consecutively. Will try alternative prediction types.
2026-01-10 20:21:11,154 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:11,271 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:11,274 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:11,329 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:11,419 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:11,422 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 14)
2026-01-10 20:21:11,730 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:11,739 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,14)
2026-01-10 20:21:11,782 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:11,790 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 18x consecutively. Will try alternative prediction types.
2026-01-10 20:21:11,873 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:12,011 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:12,014 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:12,075 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:12,168 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:12,170 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 21)
2026-01-10 20:21:12,491 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:12,498 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,21)
2026-01-10 20:21:12,525 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:12,526 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 18x consecutively. Will try alternative prediction types.
2026-01-10 20:21:12,565 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:12,684 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:12,715 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:12,764 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:12,825 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:12,829 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 17)
2026-01-10 20:21:13,149 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:13,160 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,17)
2026-01-10 20:21:13,170 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:13,171 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 19x consecutively. Will try alternative prediction types.
2026-01-10 20:21:13,222 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:13,317 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:13,322 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:13,360 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:13,412 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:13,415 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 19)
2026-01-10 20:21:13,739 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:13,745 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,19)
2026-01-10 20:21:13,758 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:13,760 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 19x consecutively. Will try alternative prediction types.
2026-01-10 20:21:13,813 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:13,918 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:13,937 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:14,154 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:14,397 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:14,510 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 19)
2026-01-10 20:21:14,988 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:15,053 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,19)
2026-01-10 20:21:15,147 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:15,148 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 19x consecutively. Will try alternative prediction types.
2026-01-10 20:21:15,216 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:15,392 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:15,413 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:15,480 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:15,549 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:15,552 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 20)
2026-01-10 20:21:16,022 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:16,158 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,20)
2026-01-10 20:21:16,202 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:16,226 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 20x consecutively. Will try alternative prediction types.
2026-01-10 20:21:16,437 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:16,741 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:16,750 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:16,835 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:16,950 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:16,955 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 18)
2026-01-10 20:21:17,063 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:17,086 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,18)
2026-01-10 20:21:17,107 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:17,108 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 20x consecutively. Will try alternative prediction types.
2026-01-10 20:21:17,156 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:17,325 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:17,341 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:17,399 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:17,480 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:17,486 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 14)
2026-01-10 20:21:17,595 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:17,600 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,14)
2026-01-10 20:21:17,617 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:17,618 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 20x consecutively. Will try alternative prediction types.
2026-01-10 20:21:17,675 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:17,752 - cods_engine - INFO - [CODS] Testing operators: reason=periodic_20, game=ft09-b8377d4b7815
2026-01-10 20:21:17,795 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:17,799 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:17,987 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:18,094 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:18,096 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 19)
2026-01-10 20:21:18,207 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:18,218 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,19)
2026-01-10 20:21:18,245 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:18,246 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 21x consecutively. Will try alternative prediction types.
2026-01-10 20:21:18,296 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:18,396 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:18,401 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:18,466 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:18,563 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:18,568 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 19)
2026-01-10 20:21:18,975 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:18,994 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,19)
2026-01-10 20:21:19,012 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:19,013 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 21x consecutively. Will try alternative prediction types.
2026-01-10 20:21:19,065 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:19,226 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:19,236 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:19,298 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:19,381 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:19,382 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 19)
2026-01-10 20:21:19,485 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:19,497 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,19)
2026-01-10 20:21:19,521 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:19,523 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 21x consecutively. Will try alternative prediction types.
2026-01-10 20:21:19,637 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:19,772 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:19,776 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:19,820 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:19,878 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:19,879 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 15)
2026-01-10 20:21:20,210 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:20,245 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,15)
2026-01-10 20:21:20,263 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:20,264 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 22x consecutively. Will try alternative prediction types.
2026-01-10 20:21:20,326 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:20,435 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:20,439 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:20,496 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:20,579 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:20,581 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 18)
2026-01-10 20:21:20,895 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
[DatabaseLogHandler] Auto-cleanup: 5,662 → 5,000 logs
2026-01-10 20:21:20,910 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,18)
2026-01-10 20:21:20,960 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:20,961 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 22x consecutively. Will try alternative prediction types.
2026-01-10 20:21:21,022 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:21,136 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:21,140 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:21,203 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:21,293 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:21,296 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 20)
2026-01-10 20:21:21,644 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:21,656 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,20)
2026-01-10 20:21:21,681 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:21,684 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 22x consecutively. Will try alternative prediction types.
2026-01-10 20:21:21,745 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:21,912 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:21,943 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:22,064 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:22,296 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:22,320 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 19)
2026-01-10 20:21:22,669 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:22,675 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,19)
2026-01-10 20:21:22,699 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:22,701 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 23x consecutively. Will try alternative prediction types.
2026-01-10 20:21:22,773 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:22,910 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:22,915 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:22,986 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:23,077 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:23,079 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 19)
2026-01-10 20:21:23,394 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:23,414 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,19)
2026-01-10 20:21:23,430 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:23,432 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 23x consecutively. Will try alternative prediction types.
2026-01-10 20:21:23,493 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:23,617 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:23,624 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:23,680 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:23,753 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:23,755 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 14)
2026-01-10 20:21:24,103 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:24,116 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,14)
2026-01-10 20:21:24,145 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:24,147 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 23x consecutively. Will try alternative prediction types.
2026-01-10 20:21:24,221 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:24,409 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:24,415 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:24,487 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:24,614 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:24,616 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 18)
2026-01-10 20:21:24,720 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:24,734 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,18)
2026-01-10 20:21:24,764 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:24,765 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 24x consecutively. Will try alternative prediction types.
2026-01-10 20:21:24,831 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:25,018 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:25,027 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:25,106 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:25,228 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:25,230 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 18)
2026-01-10 20:21:25,559 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:25,565 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,18)
2026-01-10 20:21:25,578 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:25,580 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 24x consecutively. Will try alternative prediction types.
2026-01-10 20:21:25,634 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:25,728 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:25,732 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:25,784 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:25,873 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:25,875 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 18)
2026-01-10 20:21:25,978 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:25,988 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,18)
2026-01-10 20:21:26,001 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:26,002 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 24x consecutively. Will try alternative prediction types.
2026-01-10 20:21:26,053 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:26,129 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:26,133 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:26,181 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:26,246 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:26,248 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 14)
2026-01-10 20:21:26,561 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:26,569 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,14)
2026-01-10 20:21:26,589 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:26,591 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 25x consecutively. Will try alternative prediction types.
2026-01-10 20:21:26,641 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:26,757 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:26,762 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:26,820 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:26,907 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:26,909 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 14)
2026-01-10 20:21:27,013 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:27,027 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,14)
2026-01-10 20:21:27,048 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:27,052 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 25x consecutively. Will try alternative prediction types.
2026-01-10 20:21:27,109 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:27,289 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:27,295 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:27,363 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:27,488 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:27,491 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 19)
2026-01-10 20:21:27,890 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:27,896 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,19)
2026-01-10 20:21:27,916 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:27,917 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 25x consecutively. Will try alternative prediction types.
2026-01-10 20:21:27,975 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:28,101 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:28,109 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:28,180 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:28,266 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:28,269 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 17)
2026-01-10 20:21:28,373 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:28,383 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,17)
2026-01-10 20:21:28,402 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:28,404 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 26x consecutively. Will try alternative prediction types.
2026-01-10 20:21:28,466 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:28,583 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:28,589 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:28,649 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:28,719 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:28,721 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 20)
2026-01-10 20:21:29,025 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:29,036 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,20)
2026-01-10 20:21:29,058 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:29,063 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 26x consecutively. Will try alternative prediction types.
2026-01-10 20:21:29,122 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:29,278 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:29,288 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:29,354 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:29,434 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:29,437 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 20)
2026-01-10 20:21:29,540 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:29,550 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,20)
2026-01-10 20:21:29,575 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:29,576 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 26x consecutively. Will try alternative prediction types.
2026-01-10 20:21:29,645 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:29,805 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:29,811 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:29,881 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:29,963 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:29,965 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 15)
2026-01-10 20:21:30,453 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:30,461 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,15)
2026-01-10 20:21:30,484 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:30,485 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 27x consecutively. Will try alternative prediction types.
2026-01-10 20:21:30,547 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:30,670 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:30,676 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:30,736 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:30,832 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:30,833 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 16)
2026-01-10 20:21:31,170 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:31,179 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,16)
2026-01-10 20:21:31,201 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:31,203 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 27x consecutively. Will try alternative prediction types.
2026-01-10 20:21:31,264 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:31,362 - cods_engine - INFO - [CODS] Testing operators: reason=periodic_20, game=ft09-b8377d4b7815
2026-01-10 20:21:31,402 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:31,409 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:31,497 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:31,602 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:31,604 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 16)
2026-01-10 20:21:31,916 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:31,927 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,16)
2026-01-10 20:21:31,951 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:31,958 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 27x consecutively. Will try alternative prediction types.
2026-01-10 20:21:32,027 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:32,173 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:32,179 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:32,253 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:32,349 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:32,351 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 18)
2026-01-10 20:21:32,704 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:32,709 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,18)
2026-01-10 20:21:32,723 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:32,724 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 28x consecutively. Will try alternative prediction types.
2026-01-10 20:21:32,773 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:32,877 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:32,881 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:32,928 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:32,977 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:32,978 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 20)
2026-01-10 20:21:33,318 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:33,325 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,20)
2026-01-10 20:21:33,347 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:33,353 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 28x consecutively. Will try alternative prediction types.
2026-01-10 20:21:33,422 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:33,542 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:33,547 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:33,600 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:33,673 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:33,675 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 16)
2026-01-10 20:21:33,985 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:33,993 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,16)
2026-01-10 20:21:34,013 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:34,017 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 28x consecutively. Will try alternative prediction types.
2026-01-10 20:21:34,074 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:34,174 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:34,179 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:34,237 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:34,305 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:34,307 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 21)
2026-01-10 20:21:34,410 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:34,417 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,21)
2026-01-10 20:21:34,436 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:34,439 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 29x consecutively. Will try alternative prediction types.
2026-01-10 20:21:34,519 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:34,641 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:34,645 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:34,693 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:34,752 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:34,753 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 19)
2026-01-10 20:21:35,076 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:35,085 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,19)
2026-01-10 20:21:35,097 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:35,099 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 29x consecutively. Will try alternative prediction types.
2026-01-10 20:21:35,152 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:35,235 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:35,239 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:35,293 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:35,359 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:35,361 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 21)
2026-01-10 20:21:35,685 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:35,693 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,21)
2026-01-10 20:21:35,710 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:35,713 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 29x consecutively. Will try alternative prediction types.
2026-01-10 20:21:35,773 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:35,853 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:35,857 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:35,908 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions


2026-01-10 20:21:52,329 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:52,330 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 37x consecutively. Will try alternative prediction types.
2026-01-10 20:21:52,396 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:52,569 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:52,581 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:52,655 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:52,777 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:52,778 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 19)
2026-01-10 20:21:52,880 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:52,919 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,19)
2026-01-10 20:21:52,946 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:52,947 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 37x consecutively. Will try alternative prediction types.
2026-01-10 20:21:53,050 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:53,178 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:53,202 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:53,276 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:53,401 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:53,418 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 16)
2026-01-10 20:21:53,521 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:53,575 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,16)
2026-01-10 20:21:53,635 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:53,636 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 38x consecutively. Will try alternative prediction types.
2026-01-10 20:21:53,691 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:53,823 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:53,826 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:53,889 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:53,994 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:53,995 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 19)
2026-01-10 20:21:54,310 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:54,935 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,19)
2026-01-10 20:21:54,944 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:54,945 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 38x consecutively. Will try alternative prediction types.
2026-01-10 20:21:55,020 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:55,150 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:55,172 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:55,257 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:55,376 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:55,379 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 16)
2026-01-10 20:21:55,497 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:55,532 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,16)
2026-01-10 20:21:55,578 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:55,584 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 38x consecutively. Will try alternative prediction types.
2026-01-10 20:21:55,693 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:55,838 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:55,865 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:55,924 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:56,022 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:56,036 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 20)
2026-01-10 20:21:56,358 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:56,373 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,20)
2026-01-10 20:21:56,417 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:56,420 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 39x consecutively. Will try alternative prediction types.
2026-01-10 20:21:56,490 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:56,587 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:56,616 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:56,680 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:56,804 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:56,806 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 14)
2026-01-10 20:21:57,179 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:57,207 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,14)
2026-01-10 20:21:57,268 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:57,273 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 39x consecutively. Will try alternative prediction types.
2026-01-10 20:21:57,381 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:57,554 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:57,647 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:21:57,796 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:57,945 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:57,967 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 21)
2026-01-10 20:21:58,303 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:58,313 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,21)
2026-01-10 20:21:58,381 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:21:58,384 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 39x consecutively. Will try alternative prediction types.
2026-01-10 20:21:58,441 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:21:58,573 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:58,619 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:21:58,670 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:58,810 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:58,822 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 15)
2026-01-10 20:21:58,923 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:58,945 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,15)
2026-01-10 20:21:58,960 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:21:58,961 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 40x consecutively. Will try alternative prediction types.
2026-01-10 20:21:59,040 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:21:59,152 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:59,250 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:21:59,371 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:21:59,567 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:21:59,572 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 16)
2026-01-10 20:21:59,688 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:21:59,715 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,16)
2026-01-10 20:21:59,732 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:21:59,733 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 40x consecutively. Will try alternative prediction types.
2026-01-10 20:21:59,802 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:21:59,917 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:21:59,945 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:00,016 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:00,312 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:00,324 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 16)
2026-01-10 20:22:00,642 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:00,726 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,16)
2026-01-10 20:22:00,763 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:00,766 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 40x consecutively. Will try alternative prediction types.
2026-01-10 20:22:00,840 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:00,922 - cods_engine - INFO - [CODS] Testing operators: reason=periodic_20, game=ft09-b8377d4b7815
2026-01-10 20:22:01,013 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:01,022 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:01,084 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:01,253 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:01,255 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 15)
2026-01-10 20:22:01,579 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:01,622 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,15)
2026-01-10 20:22:01,773 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:01,774 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 41x consecutively. Will try alternative prediction types.
2026-01-10 20:22:01,855 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:01,981 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:02,025 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:02,080 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:02,205 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:02,237 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 20)
2026-01-10 20:22:02,605 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:02,629 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,20)
2026-01-10 20:22:02,679 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:02,680 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 41x consecutively. Will try alternative prediction types.
2026-01-10 20:22:02,772 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:02,991 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:03,052 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:03,122 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:03,220 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:03,230 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 18)
2026-01-10 20:22:03,589 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:03,608 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,18)
2026-01-10 20:22:03,651 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:03,657 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 41x consecutively. Will try alternative prediction types.
2026-01-10 20:22:03,709 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:03,872 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:03,915 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:03,976 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:04,152 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:04,168 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 15)
2026-01-10 20:22:04,553 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:04,651 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,15)
2026-01-10 20:22:04,706 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:04,707 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 42x consecutively. Will try alternative prediction types.
2026-01-10 20:22:04,823 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:04,970 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:04,973 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:05,028 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:05,105 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:05,135 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 20)
2026-01-10 20:22:05,471 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:05,487 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,20)
2026-01-10 20:22:05,540 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:05,541 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 42x consecutively. Will try alternative prediction types.
2026-01-10 20:22:05,596 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:05,716 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:05,742 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:05,828 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:05,983 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:05,999 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 15)
2026-01-10 20:22:06,188 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:06,244 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,15)
2026-01-10 20:22:06,270 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:06,274 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 42x consecutively. Will try alternative prediction types.
2026-01-10 20:22:06,388 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:06,586 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:06,625 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:06,696 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:06,812 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:06,813 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 15)
2026-01-10 20:22:07,129 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:07,139 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,15)
2026-01-10 20:22:07,318 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:07,338 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 43x consecutively. Will try alternative prediction types.
2026-01-10 20:22:07,417 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:07,540 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:07,552 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:07,610 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:07,721 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:07,722 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 18)
2026-01-10 20:22:08,034 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:08,043 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,18)
2026-01-10 20:22:08,072 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:08,075 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 43x consecutively. Will try alternative prediction types.
2026-01-10 20:22:08,133 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:08,217 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:08,223 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:08,272 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:08,342 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:08,343 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 21)
2026-01-10 20:22:08,542 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:08,549 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,21)
2026-01-10 20:22:08,563 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:08,564 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 43x consecutively. Will try alternative prediction types.
2026-01-10 20:22:08,611 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:08,749 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:08,760 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:08,845 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:08,935 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:08,936 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 18)
2026-01-10 20:22:09,037 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:09,042 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,18)
2026-01-10 20:22:09,059 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:09,060 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 44x consecutively. Will try alternative prediction types.
2026-01-10 20:22:09,107 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:09,231 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:09,235 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:09,285 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:09,359 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:09,360 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 17)
2026-01-10 20:22:09,672 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:09,690 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,17)
2026-01-10 20:22:09,719 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:09,722 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 44x consecutively. Will try alternative prediction types.
2026-01-10 20:22:09,813 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:09,944 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:09,949 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:10,002 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:10,078 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:10,079 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 15)
2026-01-10 20:22:10,392 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:10,399 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,15)
2026-01-10 20:22:10,410 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:10,410 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 44x consecutively. Will try alternative prediction types.
2026-01-10 20:22:10,458 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:10,572 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:10,576 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:10,627 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:10,686 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:10,688 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 20)
2026-01-10 20:22:11,002 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:11,009 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,20)
2026-01-10 20:22:11,027 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:11,030 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 45x consecutively. Will try alternative prediction types.
2026-01-10 20:22:11,102 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:11,238 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:11,242 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:11,289 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:11,373 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:11,374 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 19)
2026-01-10 20:22:11,479 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:11,488 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,19)
2026-01-10 20:22:11,497 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:11,499 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 45x consecutively. Will try alternative prediction types.
2026-01-10 20:22:11,541 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:11,640 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:11,643 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:11,699 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:11,753 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:11,754 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 17)
2026-01-10 20:22:11,857 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:11,866 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,17)
2026-01-10 20:22:11,882 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:11,883 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 45x consecutively. Will try alternative prediction types.
2026-01-10 20:22:11,928 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:12,017 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:12,022 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:12,080 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:12,154 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:12,156 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 15)
2026-01-10 20:22:12,537 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:12,542 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,15)
2026-01-10 20:22:12,560 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:12,562 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 46x consecutively. Will try alternative prediction types.
2026-01-10 20:22:12,610 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:12,731 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:12,737 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:12,793 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:12,852 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:12,855 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 14)
2026-01-10 20:22:13,169 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:13,179 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,14)
2026-01-10 20:22:13,201 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:13,202 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 46x consecutively. Will try alternative prediction types.
2026-01-10 20:22:13,250 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:13,389 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:13,403 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:13,475 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:13,563 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:13,565 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 14)
2026-01-10 20:22:13,669 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:13,677 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,14)
2026-01-10 20:22:13,688 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:13,689 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 46x consecutively. Will try alternative prediction types.
2026-01-10 20:22:13,736 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:13,850 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:13,854 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:13,902 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:13,957 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:13,959 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 19)
2026-01-10 20:22:14,280 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:14,298 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,19)
2026-01-10 20:22:14,354 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:14,487 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 47x consecutively. Will try alternative prediction types.
2026-01-10 20:22:14,711 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:15,008 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:15,043 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:15,107 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:15,213 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:15,216 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 16)
2026-01-10 20:22:15,327 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:15,336 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,16)
2026-01-10 20:22:15,353 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:15,355 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 47x consecutively. Will try alternative prediction types.
2026-01-10 20:22:15,401 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:15,502 - cods_engine - INFO - [CODS] Testing operators: reason=periodic_20, game=ft09-b8377d4b7815
2026-01-10 20:22:15,540 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:15,550 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:15,619 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:15,727 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:15,769 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 15)
2026-01-10 20:22:16,121 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:16,158 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,15)
2026-01-10 20:22:16,267 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:16,325 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 47x consecutively. Will try alternative prediction types.
2026-01-10 20:22:16,458 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:16,660 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:16,667 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:16,738 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:16,829 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:16,830 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 15)
2026-01-10 20:22:17,139 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:17,144 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,15)
2026-01-10 20:22:17,154 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:17,155 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 48x consecutively. Will try alternative prediction types.
2026-01-10 20:22:17,196 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:17,301 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:17,305 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:17,366 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:17,450 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:17,451 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 15)
2026-01-10 20:22:17,912 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:17,942 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,15)
2026-01-10 20:22:17,966 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:17,969 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 48x consecutively. Will try alternative prediction types.
2026-01-10 20:22:18,036 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:18,145 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:18,150 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:18,217 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:18,295 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:18,296 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 15)
2026-01-10 20:22:18,608 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:18,614 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,15)
2026-01-10 20:22:18,632 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:18,633 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 48x consecutively. Will try alternative prediction types.
2026-01-10 20:22:18,692 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:18,830 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:18,835 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:18,898 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:18,973 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:18,974 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 17)
2026-01-10 20:22:19,076 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:19,083 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,17)
2026-01-10 20:22:19,094 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:19,095 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 49x consecutively. Will try alternative prediction types.
2026-01-10 20:22:19,144 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:19,257 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:19,261 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:19,310 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:19,385 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:19,387 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 19)
2026-01-10 20:22:19,704 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:19,715 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,19)
2026-01-10 20:22:19,737 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:19,742 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 49x consecutively. Will try alternative prediction types.
2026-01-10 20:22:19,795 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:19,900 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:19,907 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:19,982 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:20,061 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:20,063 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 21)
2026-01-10 20:22:20,376 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:20,383 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,21)
2026-01-10 20:22:20,400 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:20,402 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 49x consecutively. Will try alternative prediction types.
2026-01-10 20:22:20,475 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:20,587 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:20,591 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:20,638 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:20,696 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:20,699 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 21)
2026-01-10 20:22:20,802 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:20,809 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,21)
2026-01-10 20:22:20,827 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:20,829 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 50x consecutively. Will try alternative prediction types.
2026-01-10 20:22:20,876 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:21,001 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:21,007 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:21,109 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:21,212 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:21,214 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 19)
2026-01-10 20:22:21,549 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:21,554 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,19)
2026-01-10 20:22:21,572 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:21,574 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 50x consecutively. Will try alternative prediction types.
2026-01-10 20:22:21,625 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:21,759 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:21,763 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:21,826 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:21,893 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:21,894 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 21)
2026-01-10 20:22:21,999 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:22,009 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,21)
2026-01-10 20:22:22,027 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:22,029 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 50x consecutively. Will try alternative prediction types.
2026-01-10 20:22:22,088 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:22,181 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:22,185 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:22,240 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:22,327 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:22,329 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 14)
2026-01-10 20:22:22,737 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:22,745 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,14)
2026-01-10 20:22:22,765 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:22,766 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 51x consecutively. Will try alternative prediction types.
2026-01-10 20:22:22,829 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:22,952 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:22,956 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:23,004 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:23,073 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:23,075 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 21)
2026-01-10 20:22:23,517 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:23,525 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,21)

re_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,14)
2026-01-10 20:22:26,183 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:26,185 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 52x consecutively. Will try alternative prediction types.
2026-01-10 20:22:26,242 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:26,348 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:26,353 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:26,418 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:26,491 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:26,492 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 20)
2026-01-10 20:22:26,976 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:26,985 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,20)
2026-01-10 20:22:27,008 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:27,010 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 53x consecutively. Will try alternative prediction types.
2026-01-10 20:22:27,065 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:27,201 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:27,206 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:27,270 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:27,362 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:27,365 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 15)
2026-01-10 20:22:27,678 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:27,685 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,15)
2026-01-10 20:22:27,704 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:27,705 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 53x consecutively. Will try alternative prediction types.
2026-01-10 20:22:27,762 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:27,890 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:27,895 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:27,960 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:28,078 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:28,080 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 19)
2026-01-10 20:22:28,410 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:28,420 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,19)
2026-01-10 20:22:28,444 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:28,446 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 53x consecutively. Will try alternative prediction types.
2026-01-10 20:22:28,518 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:28,698 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:28,703 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:28,773 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:28,850 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:28,851 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 20)
2026-01-10 20:22:29,231 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:29,240 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,20)
2026-01-10 20:22:29,264 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:29,266 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 54x consecutively. Will try alternative prediction types.
2026-01-10 20:22:29,325 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:29,407 - cods_engine - INFO - [CODS] Testing operators: reason=periodic_20, game=ft09-b8377d4b7815
2026-01-10 20:22:29,433 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:29,438 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:29,492 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:29,570 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:29,571 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 16)
2026-01-10 20:22:29,901 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:29,908 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,16)
2026-01-10 20:22:29,930 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:29,932 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 54x consecutively. Will try alternative prediction types.
2026-01-10 20:22:29,978 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:30,078 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:30,083 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:30,127 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:30,260 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:30,345 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 21)
2026-01-10 20:22:30,533 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:30,625 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,21)
2026-01-10 20:22:30,767 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:30,854 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 54x consecutively. Will try alternative prediction types.
2026-01-10 20:22:31,003 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:31,299 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:31,307 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:31,382 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:31,483 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:31,485 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 20)
2026-01-10 20:22:31,589 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:31,601 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,20)
2026-01-10 20:22:31,619 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:31,620 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 55x consecutively. Will try alternative prediction types.
2026-01-10 20:22:31,676 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:31,950 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:32,018 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:32,172 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:32,402 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:32,552 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 21)
2026-01-10 20:22:33,022 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:33,029 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,21)
2026-01-10 20:22:33,048 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:33,049 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 55x consecutively. Will try alternative prediction types.
2026-01-10 20:22:33,101 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:33,222 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
[DatabaseLogHandler] Auto-cleanup: 6,041 → 5,000 logs
2026-01-10 20:22:33,229 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:33,365 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:33,457 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:33,458 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 18)
2026-01-10 20:22:33,836 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:33,844 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,18)
2026-01-10 20:22:33,861 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:33,862 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 55x consecutively. Will try alternative prediction types.
2026-01-10 20:22:33,919 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:33,993 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:33,997 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:34,049 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:34,109 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:34,110 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 19)
2026-01-10 20:22:34,456 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:34,464 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,19)
2026-01-10 20:22:34,483 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:34,487 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 56x consecutively. Will try alternative prediction types.
2026-01-10 20:22:34,539 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:34,690 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:34,693 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:34,759 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:34,837 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:34,840 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 15)
2026-01-10 20:22:34,940 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:34,948 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,15)
2026-01-10 20:22:34,966 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:34,967 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 56x consecutively. Will try alternative prediction types.
2026-01-10 20:22:35,033 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:35,144 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:35,151 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:35,206 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:35,273 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:35,274 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 15)
2026-01-10 20:22:35,680 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:35,692 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,15)
2026-01-10 20:22:35,727 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:35,733 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 56x consecutively. Will try alternative prediction types.
2026-01-10 20:22:35,806 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:35,940 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:35,943 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:36,009 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:36,075 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:36,076 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 17)
2026-01-10 20:22:36,499 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:36,506 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,17)
2026-01-10 20:22:36,556 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:36,557 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 57x consecutively. Will try alternative prediction types.
2026-01-10 20:22:36,601 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:36,760 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:36,775 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:36,898 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:36,991 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:36,993 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 18)
2026-01-10 20:22:37,422 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:37,434 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,18)
2026-01-10 20:22:37,464 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:37,482 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 57x consecutively. Will try alternative prediction types.
2026-01-10 20:22:37,573 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:37,733 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:37,812 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:37,884 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:38,034 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:38,051 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 18)
2026-01-10 20:22:38,157 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:38,164 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,18)
2026-01-10 20:22:38,188 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:38,191 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 57x consecutively. Will try alternative prediction types.
2026-01-10 20:22:38,233 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:38,332 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:38,339 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:38,397 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:38,501 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:38,505 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 17)
2026-01-10 20:22:38,619 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:38,638 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,17)
2026-01-10 20:22:38,665 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:38,666 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 58x consecutively. Will try alternative prediction types.
2026-01-10 20:22:38,711 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:38,886 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:38,892 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:38,953 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:39,004 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:39,005 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 19)
2026-01-10 20:22:39,106 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:39,123 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,19)
2026-01-10 20:22:39,196 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:39,200 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 58x consecutively. Will try alternative prediction types.
2026-01-10 20:22:39,278 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:39,409 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:39,417 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:39,473 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:39,603 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:39,608 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 16)
2026-01-10 20:22:39,721 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:39,735 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,16)
2026-01-10 20:22:39,754 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:39,755 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 58x consecutively. Will try alternative prediction types.
2026-01-10 20:22:39,801 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:39,913 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:39,965 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:40,046 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:40,185 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:40,199 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 17)
2026-01-10 20:22:40,512 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:40,567 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,17)
2026-01-10 20:22:40,576 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:40,577 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 59x consecutively. Will try alternative prediction types.
2026-01-10 20:22:40,617 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:40,717 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:40,733 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:40,773 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:40,849 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:40,866 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 14)
2026-01-10 20:22:41,170 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:41,187 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,14)
2026-01-10 20:22:41,197 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:41,199 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 59x consecutively. Will try alternative prediction types.
2026-01-10 20:22:41,263 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:41,362 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:41,422 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:41,489 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:41,634 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:41,635 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 20)
2026-01-10 20:22:41,952 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:41,957 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,20)
2026-01-10 20:22:41,972 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:41,973 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 59x consecutively. Will try alternative prediction types.
2026-01-10 20:22:42,019 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:42,169 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:42,174 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:42,223 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:42,395 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:42,410 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 20)
2026-01-10 20:22:42,717 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:42,724 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,20)
2026-01-10 20:22:42,736 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:42,738 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 60x consecutively. Will try alternative prediction types.
2026-01-10 20:22:42,789 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:42,902 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:42,967 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:43,059 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:43,251 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:43,267 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 18)
2026-01-10 20:22:43,578 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:43,639 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,18)
2026-01-10 20:22:43,675 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:43,684 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 60x consecutively. Will try alternative prediction types.
2026-01-10 20:22:43,742 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:43,851 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:43,854 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:43,898 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:43,969 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:43,970 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 16)
2026-01-10 20:22:44,189 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:44,302 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,16)
2026-01-10 20:22:44,348 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:44,350 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 60x consecutively. Will try alternative prediction types.
2026-01-10 20:22:44,391 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:44,459 - cods_engine - INFO - [CODS] Testing operators: reason=periodic_20, game=ft09-b8377d4b7815
2026-01-10 20:22:44,494 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:44,498 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:44,545 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:44,642 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:44,643 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 19)
2026-01-10 20:22:45,004 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:45,016 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,19)
2026-01-10 20:22:45,027 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:45,028 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 61x consecutively. Will try alternative prediction types.
2026-01-10 20:22:45,134 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:45,234 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:45,239 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:45,285 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:45,411 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:45,425 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 20)
2026-01-10 20:22:45,539 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:45,567 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,20)
2026-01-10 20:22:45,590 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:45,591 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 61x consecutively. Will try alternative prediction types.
2026-01-10 20:22:45,655 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:45,815 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:45,818 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:45,874 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:45,927 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:45,928 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 20)
2026-01-10 20:22:46,241 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:46,263 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,20)
2026-01-10 20:22:46,283 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:46,287 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 61x consecutively. Will try alternative prediction types.
2026-01-10 20:22:46,360 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:46,460 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:46,464 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:46,507 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:46,603 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:46,604 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 20)
2026-01-10 20:22:46,926 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:46,934 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,20)
2026-01-10 20:22:46,944 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:46,945 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 62x consecutively. Will try alternative prediction types.
2026-01-10 20:22:47,018 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:47,168 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:47,218 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:47,299 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:47,443 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:47,482 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 15)
2026-01-10 20:22:47,811 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:47,826 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,15)
2026-01-10 20:22:47,922 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:47,925 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 62x consecutively. Will try alternative prediction types.
2026-01-10 20:22:48,033 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:48,142 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:48,145 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:48,189 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:48,382 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:48,384 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 17)
2026-01-10 20:22:48,691 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:48,705 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,17)
2026-01-10 20:22:48,733 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:48,736 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 62x consecutively. Will try alternative prediction types.
2026-01-10 20:22:48,825 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:49,008 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:49,011 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:49,061 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:49,192 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:49,206 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 15)
2026-01-10 20:22:49,526 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:49,537 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,15)
2026-01-10 20:22:49,562 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:49,567 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 63x consecutively. Will try alternative prediction types.
2026-01-10 20:22:49,687 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:49,820 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:49,826 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:49,894 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:49,966 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:49,967 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 18)
2026-01-10 20:22:50,326 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:50,357 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,18)
2026-01-10 20:22:50,383 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:50,387 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 63x consecutively. Will try alternative prediction types.
2026-01-10 20:22:50,468 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:50,594 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:50,600 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:50,648 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:50,756 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:50,759 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 18)
2026-01-10 20:22:50,863 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:50,998 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,18)
2026-01-10 20:22:51,040 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:51,040 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 63x consecutively. Will try alternative prediction types.
2026-01-10 20:22:51,077 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:51,208 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:51,268 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:51,315 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:51,401 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:51,402 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 20)
2026-01-10 20:22:51,710 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:51,720 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,20)
2026-01-10 20:22:51,744 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:51,747 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 64x consecutively. Will try alternative prediction types.
2026-01-10 20:22:51,863 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:52,032 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:52,036 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:52,094 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:52,161 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:52,163 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 18)
2026-01-10 20:22:52,268 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:52,273 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,18)
2026-01-10 20:22:52,288 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:52,289 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 64x consecutively. Will try alternative prediction types.
2026-01-10 20:22:52,336 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:52,427 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:52,434 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:52,503 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:52,575 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:52,576 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 14)
2026-01-10 20:22:52,693 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:52,701 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,14)
2026-01-10 20:22:52,717 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:52,718 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 64x consecutively. Will try alternative prediction types.
2026-01-10 20:22:52,766 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:52,895 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:52,902 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:52,957 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:53,059 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:53,061 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 21)
2026-01-10 20:22:53,396 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:53,408 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,21)
2026-01-10 20:22:53,432 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:53,435 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 65x consecutively. Will try alternative prediction types.
2026-01-10 20:22:53,504 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:53,651 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:53,655 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:53,702 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:53,768 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:53,769 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 21)
2026-01-10 20:22:54,076 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:54,086 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,21)
2026-01-10 20:22:54,109 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:54,110 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 65x consecutively. Will try alternative prediction types.
2026-01-10 20:22:54,168 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:54,303 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:54,308 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:54,388 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:54,458 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:54,459 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 15)
2026-01-10 20:22:54,563 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:54,571 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,15)
2026-01-10 20:22:54,585 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:54,586 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 65x consecutively. Will try alternative prediction types.
2026-01-10 20:22:54,639 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:54,739 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:54,742 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:54,793 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:54,858 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:54,861 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 18)
2026-01-10 20:22:55,180 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:55,187 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,18)
2026-01-10 20:22:55,200 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:55,201 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 66x consecutively. Will try alternative prediction types.
2026-01-10 20:22:55,248 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:55,358 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:55,363 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:55,432 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:55,500 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:55,502 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 18)
2026-01-10 20:22:55,854 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:55,864 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,18)
2026-01-10 20:22:55,884 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:55,885 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 66x consecutively. Will try alternative prediction types.
2026-01-10 20:22:55,923 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:56,020 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:56,023 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:22:56,069 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:56,153 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:56,155 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 15)
2026-01-10 20:22:56,468 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:56,475 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,15)
2026-01-10 20:22:56,494 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:22:56,499 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 66x consecutively. Will try alternative prediction types.
2026-01-10 20:22:56,563 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:22:56,720 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:56,724 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:22:56,771 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:56,841 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:56,842 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 16)
2026-01-10 20:22:56,948 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:56,957 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,16)
2026-01-10 20:22:56,971 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:22:56,972 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 67x consecutively. Will try alternative prediction types.
2026-01-10 20:22:57,011 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:22:57,116 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:22:57,120 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:22:57,177 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:22:57,252 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:22:57,253 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 18)
2026-01-10 20:22:57,357 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:22:57,364 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,18)
2026-01-10 20:22:57,374 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:22:57,375 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 67x consecutively. Will try alternative prediction types.
2026-01-10 20:22:57,434 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:22:57,522 - cods_engine - INFO - [CODS] Testing operators: reason=periodic_20, game=ft09-b8377d4b7815
2026-01-10 20:22:57,525 - core_gameplay - WARNING - [ESCAPE] STUCK STATE detected (frontier): 200 consecutive actions with no frame change. Agent mode: generalist. Entering escape mode - will try 21 different actions.
2026-01-10 20:22:57,526 - core_gameplay - INFO -    Current score: 1.0, Actions taken: 200, Level 2 actions: 200
2026-01-10 20:22:57,527 - core_gameplay - INFO - [ESCAPE] API only reports ACTION6 - expanding to ALL actions for escape

2026-01-10 20:23:22,640 - core_gameplay - INFO - [ESCAPE] INTELLIGENT ESCAPE 
#1: ACTION5 (score=-0.55) [Available: [1, 2, 3, 4, 5, 6]; Avoiding recent: [6, 6, 6]; METACOG eliminated: [2, 3, 4, 1, 5, 2, 5, 4, 1, 3]; Theory contradicted ACTION6 (1x); Hypotheses: 5; DidNothing: [6]; SelfModel: 4 objects; Try A5 (special); Theory:speculating]
2026-01-10 20:23:54,402 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=5)
2026-01-10 20:23:54,449 - core_gameplay - INFO - [ESCAPE] ACTION6 available: 
4 untried targets remain (tried 0, METACOG eliminated 145, 2 grid, total 7)  
2026-01-10 20:23:54,458 - core_gameplay - INFO - [ESCAPE] Attempt 1/21: INTELLIGENT ESCAPE #1: ACTION5 (score=-0.55) [Available: [1, 2, 3, 4, 5, 6]; Avoiding recent: [6, 6, 6]; METACOG eliminated: [2, 3, 4, 1, 5, 2, 5, 4, 1, 3]; Theory contradicted ACTION6 (1x); Hypotheses: 5; DidNothing: [6]; SelfModel: 4 
objects; Try A5 (special); Theory:speculating]
2026-01-10 20:23:54,462 - core_gameplay - INFO - [SELF-DIRECTED] Boosted self-trust: 0.50 -> 0.75
2026-01-10 20:23:54,503 - core_gameplay - INFO - [ESCAPE] ESCAPE MODE: Trying ACTION5 to break out of frozen state
2026-01-10 20:23:54,522 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: ESCAPE MODE: Trying ACTION5 to break out of frozen state' then ACTION5 should cause 'object_control'
2026-01-10 20:23:54,629 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:23:54,699 - arc_api_client - INFO - [ft09] Sending ACTION5 to API
2026-01-10 20:23:54,964 - arc_api_client - INFO - [ft09] ACTION5 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:23:55,077 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:23:55,078 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 67x consecutively. Will try alternative prediction types.
2026-01-10 20:23:55,121 - agent_self_model - INFO - [METACOG-FIX4] Marked ACTION5 as contradicted: object_control
2026-01-10 20:23:55,122 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: ESCAPE MODE: Trying ACTION5 to break out of frozen state' -> 'REVISED: Action from micro_cf: ESCAPE MODE: Trying ACTION5 to break 
out of frozen state [failed: object_control]'
2026-01-10 20:23:55,215 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=ft09-b8377d4b7815
2026-01-10 20:23:55,237 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:23:55,241 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:23:55,304 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:23:55,413 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:23:55,415 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 14)
2026-01-10 20:23:55,480 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:23:55,494 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,14)
2026-01-10 20:23:55,504 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:23:55,505 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 68x consecutively. Will try alternative prediction types.
2026-01-10 20:23:55,565 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:23:55,669 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:23:55,673 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:23:55,729 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:23:55,810 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:23:55,811 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 16)
2026-01-10 20:23:55,983 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:23:56,016 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,16)
2026-01-10 20:23:56,026 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:23:56,028 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 68x consecutively. Will try alternative prediction types.
2026-01-10 20:23:56,064 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:23:56,127 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:23:56,130 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:23:56,170 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:23:56,270 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:23:56,288 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 21)
2026-01-10 20:23:56,472 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:23:56,481 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,21)
2026-01-10 20:23:56,518 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:23:56,520 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 68x consecutively. Will try alternative prediction types.
2026-01-10 20:23:56,570 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:23:56,685 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:23:56,691 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:23:56,747 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:23:56,808 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:23:56,813 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 17)
2026-01-10 20:23:56,894 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:23:56,908 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,17)
2026-01-10 20:23:56,935 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:23:56,936 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 69x consecutively. Will try alternative prediction types.
2026-01-10 20:23:56,996 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:23:57,117 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:23:57,122 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:23:57,172 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:23:57,260 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:23:57,262 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 14)
2026-01-10 20:23:57,437 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:23:57,443 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,14)
2026-01-10 20:23:57,474 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:23:57,478 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 69x consecutively. Will try alternative prediction types.
2026-01-10 20:23:57,579 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:23:57,656 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:23:57,660 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:23:57,699 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:23:57,748 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:23:57,749 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 15)
2026-01-10 20:23:57,812 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:23:57,821 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,15)
2026-01-10 20:23:57,844 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:23:57,847 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 69x consecutively. Will try alternative prediction types.
2026-01-10 20:24:30,969 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:24:31,151 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:24:31,171 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:24:31,245 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:24:31,318 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:24:31,319 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 17)
2026-01-10 20:24:31,406 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:24:31,442 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,17)
2026-01-10 20:24:31,455 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:24:31,456 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 70x consecutively. Will try alternative prediction types.
2026-01-10 20:24:31,532 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:24:31,743 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:24:31,790 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:24:31,852 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:24:31,990 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:24:31,995 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 16)
2026-01-10 20:24:32,065 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:24:32,084 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,16)
2026-01-10 20:24:32,110 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:24:32,116 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 70x consecutively. Will try alternative prediction types.
2026-01-10 20:24:32,173 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:24:32,316 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:24:32,345 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:24:32,406 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:24:32,463 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:24:32,464 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 18)
2026-01-10 20:24:32,638 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:24:32,648 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,18)
2026-01-10 20:24:32,671 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:24:32,675 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 70x consecutively. Will try alternative prediction types.
2026-01-10 20:24:32,725 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:24:32,823 - core_gameplay - INFO - [ESCAPE] API only reports ACTION6 - expanding to ALL actions for escape


2026-01-10 20:24:59,367 - core_gameplay - INFO - [ESCAPE] INTELLIGENT ESCAPE 
#2: ACTION4 (score=-0.85) [Available: [1, 2, 3, 4, 5, 6]; Avoiding recent: [5, 6, 6]; METACOG eliminated: [2, 3, 4, 1, 5, 2, 5, 4, 1, 3]; Theory contradicted ACTION6 (1x); Theory contradicted ACTION5 (1x); Hypotheses: 5; DidNothing: [5, 6]; SelfModel: 4 objects; Self-directed (bias=0.75); Theory:speculating]
2026-01-10 20:24:59,491 - visual_analyzer - INFO - [GRID] Generated 5 grid exploration targets (index=10)
2026-01-10 20:24:59,532 - core_gameplay - INFO - [ESCAPE] ACTION6 available: 
2 untried targets remain (tried 0, METACOG eliminated 145, 1 grid, total 5)  
2026-01-10 20:24:59,534 - core_gameplay - INFO - [ESCAPE] Attempt 2/21: INTELLIGENT ESCAPE #2: ACTION4 (score=-0.85) [Available: [1, 2, 3, 4, 5, 6]; Avoiding recent: [5, 6, 6]; METACOG eliminated: [2, 3, 4, 1, 5, 2, 5, 4, 1, 3]; Theory contradicted ACTION6 (1x); Theory contradicted ACTION5 (1x); Hypotheses: 5; DidNothing: [5, 6]; SelfModel: 4 objects; Self-directed (bias=0.75); Theory:speculating]
2026-01-10 20:24:59,547 - core_gameplay - INFO - [SELF-DIRECTED] Boosted self-trust: 0.75 -> 1.00
2026-01-10 20:24:59,583 - core_gameplay - INFO - [ESCAPE] ESCAPE MODE: Trying ACTION4 to break out of frozen state
2026-01-10 20:24:59,590 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: ESCAPE MODE: Trying ACTION4 to break out of frozen state' then ACTION4 should cause 'frame_change'
2026-01-10 20:24:59,650 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:24:59,715 - arc_api_client - INFO - [ft09] Sending ACTION4 to API
2026-01-10 20:24:59,913 - arc_api_client - INFO - [ft09] ACTION4 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:00,562 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:25:00,564 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 71x consecutively. Will try alternative prediction types.
2026-01-10 20:25:00,666 - agent_self_model - INFO - [METACOG-FIX4] Marked ACTION4 as contradicted: frame_change
2026-01-10 20:25:00,683 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: ESCAPE MODE: Trying ACTION4 to break out of frozen state' -> 'REVISED: Action from micro_cf: ESCAPE MODE: Trying ACTION4 to break 
out of frozen state [failed: frame_change]'
2026-01-10 20:25:00,833 - cods_engine - INFO - [CODS] Testing operators: reason=discovery_mode, game=ft09-b8377d4b7815
2026-01-10 20:25:00,875 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:00,887 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:25:00,943 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:01,092 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:01,094 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 17)
2026-01-10 20:25:01,291 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:01,319 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,17)
2026-01-10 20:25:01,342 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:25:01,343 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 71x consecutively. Will try alternative prediction types.
2026-01-10 20:25:01,414 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:25:01,517 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:01,524 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:25:01,598 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:01,652 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:01,653 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 17)
2026-01-10 20:25:01,777 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:01,823 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,17)
2026-01-10 20:25:01,856 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:25:01,858 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 71x consecutively. Will try alternative prediction types.
2026-01-10 20:25:01,921 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:25:02,104 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:02,110 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:25:02,184 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:02,277 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:02,278 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 16)
2026-01-10 20:25:02,523 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:02,558 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,16)
2026-01-10 20:25:02,590 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:25:02,592 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 72x consecutively. Will try alternative prediction types.
2026-01-10 20:25:02,654 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:25:02,853 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:02,871 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:25:02,988 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:03,173 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:03,180 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 18)
2026-01-10 20:25:03,375 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:03,385 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,18)
2026-01-10 20:25:03,410 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:25:03,411 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 72x consecutively. Will try alternative prediction types.
2026-01-10 20:25:03,469 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:25:03,599 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:03,609 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:25:03,667 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:03,766 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:03,769 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 19)
2026-01-10 20:25:04,061 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:04,068 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,19)
2026-01-10 20:25:04,100 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:25:04,102 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 72x consecutively. Will try alternative prediction types.
2026-01-10 20:25:04,168 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:25:04,316 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:04,320 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:25:04,381 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:04,480 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:04,482 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 16)
2026-01-10 20:25:04,544 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:04,580 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,16)
2026-01-10 20:25:04,590 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:25:04,593 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 73x consecutively. Will try alternative prediction types.
2026-01-10 20:25:04,638 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:25:04,764 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:04,767 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:25:04,825 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:04,911 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:04,912 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 18)
2026-01-10 20:25:04,976 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:04,989 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,18)
2026-01-10 20:25:05,015 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:25:05,017 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 73x consecutively. Will try alternative prediction types.
2026-01-10 20:25:05,069 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:25:05,213 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:05,219 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:25:05,270 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:05,388 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:05,399 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 16)
2026-01-10 20:25:05,469 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:05,478 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,16)
2026-01-10 20:25:05,515 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:25:05,517 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 73x consecutively. Will try alternative prediction types.
2026-01-10 20:25:05,567 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:25:05,729 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:05,742 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:25:05,823 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:05,909 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:05,911 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 20)
2026-01-10 20:25:05,974 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:05,986 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,20)
2026-01-10 20:25:06,009 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:25:06,012 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 74x consecutively. Will try alternative prediction types.
2026-01-10 20:25:06,105 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:25:06,225 - cods_engine - INFO - [CODS] Testing operators: reason=periodic_20, game=ft09-b8377d4b7815
2026-01-10 20:25:06,230 - core_gameplay - INFO - [ESCAPE] API only reports ACTION6 - expanding to ALL actions for escape
[MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:54,216 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:25:54,263 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:54,324 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:54,325 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 21)
2026-01-10 20:25:54,547 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:54,557 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,21)
2026-01-10 20:25:54,573 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:25:54,578 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 85x consecutively. Will try alternative prediction types.
2026-01-10 20:25:54,632 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:25:54,744 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:54,749 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:25:54,860 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:54,919 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:54,923 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 14)
2026-01-10 20:25:54,984 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:54,994 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,14)
2026-01-10 20:25:55,017 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:25:55,018 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 85x consecutively. Will try alternative prediction types.
2026-01-10 20:25:55,067 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:25:55,161 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:55,167 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:25:55,219 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:55,272 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:55,274 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 19)
2026-01-10 20:25:55,338 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:55,346 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,19)
2026-01-10 20:25:55,369 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:25:55,380 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 86x consecutively. Will try alternative prediction types.
2026-01-10 20:25:55,521 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:25:55,653 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:55,660 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:25:55,724 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:55,779 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:55,781 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 14)
2026-01-10 20:25:55,847 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:55,859 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,14)
2026-01-10 20:25:55,880 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:25:55,892 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 86x consecutively. Will try alternative prediction types.
2026-01-10 20:25:55,961 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:25:56,083 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:56,089 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:25:56,151 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:56,256 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:56,259 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 16)
2026-01-10 20:25:56,329 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:56,366 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,16)
2026-01-10 20:25:56,394 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:25:56,396 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 86x consecutively. Will try alternative prediction types.
2026-01-10 20:25:56,458 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:25:56,578 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:56,582 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:25:56,641 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:56,695 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:56,696 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 18)
2026-01-10 20:25:56,871 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:56,896 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,18)
2026-01-10 20:25:56,914 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:25:56,915 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 87x consecutively. Will try alternative prediction types.
2026-01-10 20:25:56,978 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:25:57,093 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:57,097 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:25:57,161 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:57,274 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:57,276 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 17)
2026-01-10 20:25:57,349 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:57,365 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,17)
2026-01-10 20:25:57,383 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:25:57,385 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 87x consecutively. Will try alternative prediction types.
2026-01-10 20:25:57,474 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:25:57,575 - cods_engine - INFO - [CODS] Testing operators: reason=periodic_20, game=ft09-b8377d4b7815
2026-01-10 20:25:57,597 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:57,602 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:25:57,665 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:57,763 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:57,764 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 15)
2026-01-10 20:25:57,827 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:57,843 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,15)
2026-01-10 20:25:57,861 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:25:57,862 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 87x consecutively. Will try alternative prediction types.
2026-01-10 20:25:57,968 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:25:58,093 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:58,098 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:25:58,177 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:58,293 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 18): micro rollout: probe salience | Self-model: Controlled color 9
[DatabaseLogHandler] Auto-cleanup: 5,598 → 5,000 logs
2026-01-10 20:25:58,311 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 18)
2026-01-10 20:25:58,415 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:58,441 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,18)
2026-01-10 20:25:58,468 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:25:58,469 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 88x consecutively. Will try alternative prediction types.
2026-01-10 20:25:58,546 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:25:58,667 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:58,672 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:25:58,726 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:58,791 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:58,792 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 18)
2026-01-10 20:25:58,863 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:58,896 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,18)
2026-01-10 20:25:58,908 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:25:58,909 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 88x consecutively. Will try alternative prediction types.
2026-01-10 20:25:58,944 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:25:59,036 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:59,041 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:25:59,101 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:59,207 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:59,209 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 16)
2026-01-10 20:25:59,272 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:59,281 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,16)
2026-01-10 20:25:59,304 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:25:59,311 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 88x consecutively. Will try alternative prediction types.
2026-01-10 20:25:59,365 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:25:59,472 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:59,475 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:25:59,518 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:25:59,584 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:25:59,586 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 17)
2026-01-10 20:25:59,765 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:25:59,772 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,17)
2026-01-10 20:25:59,800 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:25:59,804 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 89x consecutively. Will try alternative prediction types.
2026-01-10 20:25:59,875 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:25:59,993 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:25:59,999 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:00,169 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:00,375 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:00,377 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 18)
2026-01-10 20:26:00,439 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:00,452 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,18)
2026-01-10 20:26:00,473 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:00,477 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 89x consecutively. Will try alternative prediction types.
2026-01-10 20:26:00,530 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:00,660 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:00,663 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:00,712 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:00,763 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:00,764 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 19)
2026-01-10 20:26:00,853 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:00,871 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,19)
2026-01-10 20:26:00,895 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:00,897 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 89x consecutively. Will try alternative prediction types.
2026-01-10 20:26:00,957 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:01,113 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:01,118 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:26:01,306 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:01,536 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:01,620 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 21)
2026-01-10 20:26:01,824 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:01,848 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,21)
2026-01-10 20:26:01,872 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:26:01,878 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 90x consecutively. Will try alternative prediction types.
2026-01-10 20:26:01,939 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:26:02,066 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:02,073 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:02,131 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:02,198 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:02,202 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 14)
2026-01-10 20:26:02,281 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:02,291 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,14)
2026-01-10 20:26:02,304 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:02,304 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 90x consecutively. Will try alternative prediction types.
2026-01-10 20:26:02,373 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:02,458 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:02,468 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:02,567 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:02,643 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:02,645 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 17)
2026-01-10 20:26:02,710 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:02,717 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,17)
2026-01-10 20:26:02,769 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:02,773 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 90x consecutively. Will try alternative prediction types.
2026-01-10 20:26:02,831 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:02,938 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:02,959 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:26:03,051 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:03,127 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:03,129 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 20)
2026-01-10 20:26:03,193 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:03,204 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,20)
2026-01-10 20:26:03,227 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:26:03,228 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 91x consecutively. Will try alternative prediction types.
2026-01-10 20:26:03,283 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:26:03,388 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:03,395 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:03,459 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:03,534 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:03,549 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 21)
2026-01-10 20:26:03,761 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:03,773 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,21)
2026-01-10 20:26:03,803 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:03,811 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 91x consecutively. Will try alternative prediction types.
2026-01-10 20:26:03,858 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:03,984 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:03,998 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:04,056 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:04,188 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:04,191 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 20)
2026-01-10 20:26:04,366 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:04,407 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,20)
2026-01-10 20:26:04,418 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:04,419 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 91x consecutively. Will try alternative prediction types.
2026-01-10 20:26:04,481 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:04,627 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:04,635 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:26:04,712 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:04,802 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:04,804 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 18)
2026-01-10 20:26:04,978 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:04,988 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,18)
2026-01-10 20:26:04,998 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:26:04,999 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 92x consecutively. Will try alternative prediction types.
2026-01-10 20:26:05,068 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:26:05,217 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:05,230 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:05,307 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:05,371 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:05,372 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 20)
2026-01-10 20:26:05,543 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:05,560 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,20)
2026-01-10 20:26:05,582 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:05,584 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 92x consecutively. Will try alternative prediction types.
2026-01-10 20:26:05,631 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:05,740 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:05,743 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:05,813 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:05,893 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:05,893 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 19)
2026-01-10 20:26:06,068 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:06,079 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,19)
2026-01-10 20:26:06,098 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:06,100 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 92x consecutively. Will try alternative prediction types.
2026-01-10 20:26:06,156 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:06,309 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:06,313 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:26:06,376 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:06,448 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:06,450 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 15)
2026-01-10 20:26:06,648 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:06,656 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,15)
2026-01-10 20:26:06,671 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:26:06,672 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 93x consecutively. Will try alternative prediction types.
2026-01-10 20:26:06,715 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:26:06,823 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:06,827 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:06,894 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:06,965 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:06,968 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 20)
2026-01-10 20:26:07,046 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:07,071 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,20)
2026-01-10 20:26:07,125 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:07,130 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 93x consecutively. Will try alternative prediction types.
2026-01-10 20:26:07,239 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:07,337 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:07,355 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:07,429 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:07,517 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:07,518 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 21)
2026-01-10 20:26:07,592 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:07,612 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,21)
2026-01-10 20:26:07,648 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:07,652 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 93x consecutively. Will try alternative prediction types.
2026-01-10 20:26:07,728 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:07,846 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:07,860 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:26:07,912 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:07,998 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:08,000 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 18)
2026-01-10 20:26:08,065 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:08,076 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,18)
2026-01-10 20:26:08,092 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:26:08,093 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 94x consecutively. Will try alternative prediction types.
2026-01-10 20:26:08,159 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:26:08,254 - cods_engine - INFO - [CODS] Testing operators: reason=periodic_20, game=ft09-b8377d4b7815
2026-01-10 20:26:08,276 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:08,280 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:08,336 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:08,465 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:08,466 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 14)
2026-01-10 20:26:08,641 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:08,657 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,14)
2026-01-10 20:26:08,674 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:08,677 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 94x consecutively. Will try alternative prediction types.
2026-01-10 20:26:08,734 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:08,828 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:08,832 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:08,887 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:08,959 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:08,961 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 21)
2026-01-10 20:26:09,132 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:09,143 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,21)
2026-01-10 20:26:09,158 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:09,162 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 94x consecutively. Will try alternative prediction types.
2026-01-10 20:26:09,227 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:09,338 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:09,345 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:26:09,399 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:09,492 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:09,493 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 19)
2026-01-10 20:26:09,558 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:09,568 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,19)
2026-01-10 20:26:09,590 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:26:09,594 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 95x consecutively. Will try alternative prediction types.
2026-01-10 20:26:09,711 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:26:09,819 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:09,827 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:09,905 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:09,977 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:09,982 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 16)
2026-01-10 20:26:10,058 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:10,078 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,16)
2026-01-10 20:26:10,103 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:10,105 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 95x consecutively. Will try alternative prediction types.
2026-01-10 20:26:10,164 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:10,291 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:10,297 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:10,362 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:10,458 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 16): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:10,459 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 16)
2026-01-10 20:26:10,630 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:10,640 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,16)
2026-01-10 20:26:10,667 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:10,668 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 95x consecutively. Will try alternative prediction types.
2026-01-10 20:26:10,711 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:10,822 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:10,828 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:26:10,896 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:10,974 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 21): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:10,976 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 21)
2026-01-10 20:26:11,147 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:11,160 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,21)
2026-01-10 20:26:11,180 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:26:11,183 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 96x consecutively. Will try alternative prediction types.
2026-01-10 20:26:11,247 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:26:11,392 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:11,404 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:11,466 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:11,588 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:11,591 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 14)
2026-01-10 20:26:11,661 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:11,706 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,14)
2026-01-10 20:26:11,726 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:11,728 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 96x consecutively. Will try alternative prediction types.
2026-01-10 20:26:11,907 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:12,185 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:12,210 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:12,367 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:12,533 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (57, 17): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:12,565 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (57, 17)
2026-01-10 20:26:12,644 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:12,689 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (57,17)
2026-01-10 20:26:12,725 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:12,731 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 96x consecutively. Will try alternative prediction types.
2026-01-10 20:26:12,860 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:12,990 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:12,994 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:26:13,062 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:13,259 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 19): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:13,263 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 19)
2026-01-10 20:26:13,329 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:13,354 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,19)
2026-01-10 20:26:13,377 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:26:13,380 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 97x consecutively. Will try alternative prediction types.
2026-01-10 20:26:13,456 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:26:13,632 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:13,654 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:13,724 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:13,782 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 20): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:13,783 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 20)
2026-01-10 20:26:13,846 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:13,862 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,20)
2026-01-10 20:26:13,883 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:13,884 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 97x consecutively. Will try alternative prediction types.
2026-01-10 20:26:13,949 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:14,080 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:14,084 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:14,180 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:14,360 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (62, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:14,418 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (62, 15)
2026-01-10 20:26:14,670 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:14,727 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (62,15)
2026-01-10 20:26:14,755 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:14,772 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 97x consecutively. Will try alternative prediction types.
2026-01-10 20:26:15,013 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:15,357 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:15,374 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:26:15,445 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:15,559 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (56, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:15,561 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (56, 14)
2026-01-10 20:26:15,745 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:15,760 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (56,14)
2026-01-10 20:26:15,782 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:26:15,784 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 98x consecutively. Will try alternative prediction types.
2026-01-10 20:26:15,855 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:26:16,041 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:16,046 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:16,328 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:16,579 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (58, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:16,626 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (58, 15)
2026-01-10 20:26:16,866 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:16,875 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (58,15)
2026-01-10 20:26:16,891 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:16,892 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 98x consecutively. Will try alternative prediction types.
2026-01-10 20:26:16,945 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:17,056 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:17,061 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:17,152 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:17,261 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:17,358 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 18)
2026-01-10 20:26:17,426 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:17,438 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,18)
2026-01-10 20:26:17,455 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:17,459 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 98x consecutively. Will try alternative prediction types.
2026-01-10 20:26:17,510 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:17,688 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:17,694 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'frame_change'
2026-01-10 20:26:17,767 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:17,835 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (60, 18): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:17,838 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (60, 18)
2026-01-10 20:26:18,011 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:18,018 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (60,18)
2026-01-10 20:26:18,036 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'frame_change', got 'score_delta=0.0, frame_changed=False'       
2026-01-10 20:26:18,037 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'frame_change' failed 99x consecutively. Will try alternative prediction types.
2026-01-10 20:26:18,081 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: frame_change]'
2026-01-10 20:26:18,240 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:18,273 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'discover_pattern'
2026-01-10 20:26:18,327 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:18,381 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (59, 15): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:18,382 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (59, 15)
2026-01-10 20:26:18,448 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:18,458 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (59,15)
2026-01-10 20:26:18,477 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'discover_pattern', got 'score_delta=0.0, frame_changed=False'   
2026-01-10 20:26:18,478 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'discover_pattern' failed 99x consecutively. Will try alternative prediction types.
2026-01-10 20:26:18,518 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: discover_pattern]'       
2026-01-10 20:26:18,654 - core_gameplay - INFO - [MICRO-CF] micro rollout: probe salience
2026-01-10 20:26:18,660 - agent_self_model - INFO - [METACOG] PREDICTION: If 
'Action from micro_cf: micro rollout: probe salience' then ACTION6 should cause 'object_control'
2026-01-10 20:26:18,729 - agent_self_model - INFO - [NETWORK-INVENTORY] ft09 
L2: 2 toggleable, 20 moveable, 29 interactable positions
2026-01-10 20:26:18,793 - core_gameplay - INFO - [SELF-MODEL] ACTION6 at (61, 14): micro rollout: probe salience | Self-model: Controlled color 9
2026-01-10 20:26:18,794 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (61, 14)
2026-01-10 20:26:18,856 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 1
2026-01-10 20:26:18,866 - core_gameplay - INFO - [SELECTION] ACTION6 clicked 
on object color 9 at (61,14)
2026-01-10 20:26:18,889 - agent_self_model - INFO - [METACOG] PREDICTION WRONG: Expected 'object_control', got 'score_delta=0.0, frame_changed=False'     
2026-01-10 20:26:18,890 - agent_self_model - WARNING - [METACOG] PREDICTION TYPE SUPPRESSED: 'object_control' failed 99x consecutively. Will try alternative prediction types.
2026-01-10 20:26:18,947 - agent_self_model - INFO - [METACOG] THEORY REVISED: 'Action from micro_cf: micro rollout: probe salience' -> 'REVISED: Action from micro_cf: micro rollout: probe salience [failed: object_control]'
2026-01-10 20:26:19,032 - core_gameplay - WARNING - [TIME] Reached max actions (297) for level 2
2026-01-10 20:26:19,034 - core_gameplay - INFO - [TIME] No score progress on 
level 2. Agent stuck - ending game.

2026-01-10 20:26:38,916 - game_session_manager - INFO - Finished game ft09-b8377d4b7815: NOT_FINISHED, Score: 1.0
2026-01-10 20:26:39,426 - core_gameplay - INFO - [PKG] LEVEL-SPECIFIC CAPTURE: 63 actions for level 1
2026-01-10 20:26:39,432 - core_gameplay - INFO -  Captured partial progress sequence (score 1.0): seq_e96094eebe55434a
2026-01-10 20:26:39,434 - core_gameplay - INFO -    → Future agents can replay this to guarantee 1 level(s) minimum

2026-01-10 20:27:05,284 - core_gameplay - INFO - [HYPOTHESIS] Generated failure hypothesis 5951f5a8-74a for level 2
2026-01-10 20:27:05,290 - agent_operating_mode_system - INFO - 🔍 EXPLORATION PHASE: No games fully beaten yet
2026-01-10 20:27:05,291 - agent_operating_mode_system - INFO -    Distribution: 60% PIONEER, 15% OPTIMIZER, 20% GENERALIST, 5% EXPLOITER
2026-01-10 20:27:05,356 - agent_operating_mode_system - INFO - [OK] agent_operating_modes table initialized
2026-01-10 20:27:05,357 - agent_operating_mode_system - INFO - [✓] Agent Operating Mode System initialized
2026-01-10 20:27:05,358 - agent_operating_mode_system - INFO -    Target distribution: 60% pioneers, 15% optimizers, 20% generalists, 5% exploiters
2026-01-10 20:27:05,535 - core_gameplay - INFO - Game ft09-b8377d4b7815 completed: NOT_FINISHED, Score: 1.0, Actions: 297, Levels Completed: 1/2
2026-01-10 20:27:17,842 - counterfactual_analyzer - INFO - Generated 68 counterfactual scenarios from 8501 decision points
2026-01-10 20:27:18,011 - cods_engine - INFO - [CODS] Processed 68 counterfactual 
scenarios
2026-01-10 20:27:18,040 - cods_engine - INFO - [CODS] Game outcome: FAIL L2 - 0 primitive gaps detected


[OK] Released ft09-b8377d4b7815 (played for 555.0s by offspring_e922f284)
2026-01-10 20:27:34,323 - counterfactual_analyzer - INFO - Counterfactual analysis schema initialized
2026-01-10 20:27:34,350 - core_gameplay - INFO - Rule induction engine initialized2026-01-10 20:27:34,417 - core_gameplay - INFO - Abstraction engine initialized
2026-01-10 20:27:34,477 - primitive_unlock_manager - INFO - [CODS] Grandfathered 'detect_symmetry' -> visual_reasoning_engine.py:detect_symmetry()
2026-01-10 20:27:34,478 - primitive_unlock_manager - INFO - [CODS] Grandfathered 'flood_fill' -> object_detector.py:_flood_fill()
2026-01-10 20:27:34,479 - primitive_unlock_manager - INFO - [CODS] Grandfathered 'detect_shapes' -> visual_reasoning_engine.py:detect_shapes()
2026-01-10 20:27:34,480 - primitive_unlock_manager - INFO - [CODS] Grandfathered 'find_repeating_patterns' -> visual_reasoning_engine.py:find_repeating_patterns()  
2026-01-10 20:27:34,481 - primitive_unlock_manager - INFO - [CODS] Grandfathered 'analyze_color_distribution' -> visual_reasoning_engine.py:analyze_color_distribution()
2026-01-10 20:27:34,484 - primitive_unlock_manager - INFO - [CODS] Grandfathered 'analyze_spatial_relations' -> visual_reasoning_engine.py:analyze_spatial_relations()
2026-01-10 20:27:34,486 - primitive_unlock_manager - INFO - [CODS] Grandfathered 'detect_objects_in_frame' -> object_detector.py:detect_objects_in_frame()
2026-01-10 20:27:34,496 - primitive_unlock_manager - INFO - [CODS] Grandfathered 'parse_scene' -> symbolic_reasoning_engine.py:parse_scene()
2026-01-10 20:27:34,498 - primitive_unlock_manager - INFO - [CODS] Grandfathered '_pattern_similarity' -> sequence_abstraction.py:_pattern_similarity()
2026-01-10 20:27:34,500 - primitive_unlock_manager - INFO - [CODS] Grandfathered 9 existing primitives
2026-01-10 20:27:34,501 - cods_engine - INFO - [CODS] Concept discovery engine initialized (Tier 4)
2026-01-10 20:27:34,503 - cods_engine - INFO - [CODS] Engine initialized with 122 
seed primitives
2026-01-10 20:27:34,504 - core_gameplay - INFO - CODS engine initialized (earn-to-learn primitives)
2026-01-10 20:27:34,504 - core_gameplay - INFO - Baby primitives initialized (seed_primitives integration)
2026-01-10 20:27:34,506 - core_gameplay - INFO - Terminal pattern detector initialized (game_over foresight)
2026-01-10 20:27:34,507 - core_gameplay - INFO - Scientific method engine initialized (autonomous theory formation)
2026-01-10 20:27:34,512 - core_gameplay - INFO - Questioning engine initialized (critical question blocking)
2026-01-10 20:27:34,513 - core_gameplay - INFO - Network knowledge synthesis initialized (agent knowledge tool)
2026-01-10 20:27:34,515 - core_gameplay - INFO - Agent network contributor initialized (decentralized viral exchange)
2026-01-10 20:27:34,520 - core_gameplay - INFO - Games-as-Teachers engine initialized (lesson extraction)
2026-01-10 20:27:34,521 - core_gameplay - INFO - Imagination budget manager initialized (adaptive cognitive limits)
2026-01-10 20:27:34,523 - subgoal_planner - INFO - Subgoal planning schema initialized
2026-01-10 20:27:34,523 - subgoal_planning_activator - INFO - [SubgoalActivator] Subgoal planner injected successfully
2026-01-10 20:27:34,525 - core_gameplay - INFO - Subgoal planner injected into activator
2026-01-10 20:27:34,526 - core_gameplay - INFO - Updated game config: {'strategy': 'balanced', 'max_actions_per_level': 300, 'max_total_actions': 2000, 'enable_random_exploration': True, 'enable_pattern_learning': True, 'diversity_mode': False, 'enforce_game_diversity': False, 'max_repeats_per_game': 999, 'specialist_mode': False, 'agent_operating_mode': 'generalist', 'optimizer_target_level': None, 'current_generation': 302}
2026-01-10 20:27:34,529 - core_gameplay - INFO - Starting game: ft09-b8377d4b7815 
(agent: offspring_2f12a9b4)
2026-01-10 20:27:34,564 - database_interface - INFO - Created session: session_f535196d_1768098454
2026-01-10 20:27:34,568 - arc_api_client - INFO - Initialized ARC client with base URL: https://three.arcprize.org
2026-01-10 20:27:34,569 - game_session_manager - INFO - Started session: session_f535196d_1768098454
2026-01-10 20:27:34,595 - core_gameplay - INFO -  Agent mode set to: GENERALIST
2026-01-10 20:27:34,991 - arc_api_client - INFO - Opened scorecard: 37ac4ca1-6f68-4c23-8ac7-a300345d2f8f
2026-01-10 20:27:35,201 - arc_api_client - INFO - Created game ft09-b8377d4b7815 with scorecard 37ac4ca1-6f68-4c23-8ac7-a300345d2f8f
2026-01-10 20:27:35,204 - game_session_manager - INFO - [GAME-RESULT] Saved start 
for game ft09-b8377d4b7815 session session_f535196d_1768098454 scorecard 37ac4ca1-6f68-4c23-8ac7-a300345d2f8f
2026-01-10 20:27:35,205 - game_session_manager - INFO - Created game: ft09-b8377d4b7815 with actions: [6]
2026-01-10 20:27:35,314 - core_gameplay - INFO - [WORLD-MODEL] Symbolic engine initialized for ft09
2026-01-10 20:27:35,340 - core_gameplay - INFO - [AUTOBIOGRAPHY] offsprin: First time on ft09
2026-01-10 20:27:35,341 - subgoal_planning_activator - INFO - [SubgoalActivator] Level start trigger for ft09-b8377d4b7815_L1
2026-01-10 20:27:35,343 - subgoal_planning_activator - INFO - [SubgoalActivator] Generated 3 subgoals for ft09-b8377d4b7815_L1
2026-01-10 20:27:35,345 - subgoal_planner - INFO - Created plan plan_4c5ef75a5924: Complete all levels and win with 3 subgoals
2026-01-10 20:27:35,347 - subgoal_planning_activator - INFO - [SubgoalActivator] Stored plan plan_4c5ef75a5924 to database
2026-01-10 20:27:35,348 - core_gameplay - INFO - [SUBGOAL] Generated 3 subgoals for ft09-b8377d4b7815 L1
2026-01-10 20:27:35,389 - core_gameplay - INFO - [SEQUENCE REPLAY DEBUG] Checking 
for sequences for game ft09-b8377d4b7815, agent_mode=generalist
2026-01-10 20:27:35,391 - core_gameplay - INFO - [RANKED SEQ] Found 1 candidate sequences for ft09
2026-01-10 20:27:35,392 - core_gameplay - INFO - [3-TRY SYSTEM] Found 1 candidate 
sequences for ft09-b8377d4b7815
2026-01-10 20:27:35,393 - core_gameplay - INFO -  GENERALIST mode: Found 63-action sequence (completes 1 levels), will replay exactly
2026-01-10 20:27:35,394 - core_gameplay - INFO - [3-TRY] Attempt 1/3: Trying sequence seq_93f0ba94 (score 1.0, 63 actions)
2026-01-10 20:27:35,397 - core_gameplay - INFO -   [PROVEN] 100.0% success rate   
2026-01-10 20:27:35,398 - core_gameplay - INFO -  Replaying sequence seq_93f0ba948e274fe3 inline (level 1)
2026-01-10 20:27:35,413 - core_gameplay - INFO - [SEQUENCE REPLAY DEBUG] Incrementing times_referenced for sequence seq_93f0ba948e274fe3
2026-01-10 20:27:35,416 - core_gameplay - INFO - [SEQUENCE REPLAY DEBUG] Successfully incremented times_referenced for sequence seq_93f0ba948e274fe3
2026-01-10 20:27:35,418 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (7, 58)
2026-01-10 20:27:35,613 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-10 20:27:35,675 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (31, 32)
2026-01-10 20:27:35,937 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-10 20:27:35,971 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (45, 37)
2026-01-10 20:27:36,122 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-10 20:27:36,156 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (31, 2)
2026-01-10 20:27:36,327 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-10 20:27:36,357 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (29, 31)
2026-01-10 20:27:36,552 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-10 20:27:36,580 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (29, 31)
2026-01-10 20:27:36,740 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 0
2026-01-10 20:27:36,834 - arc_api_client - INFO - [ft09] Sending ACTION6 to API with coordinates (29, 31)
2026-01-10 20:27:36,991 - arc_api_client - INFO - [ft09] ACTION6 API response - State: NOT_FINISHED, Score: 0