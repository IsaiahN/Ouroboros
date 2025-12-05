# Payload Quality Improvement Plan

**Date**: December 4, 2025  
**Target File**: `core_gameplay.py`  
**Purpose**: Fix broken feedback loops in emergent reasoning and self/world models

---

## Implementation Status: COMPLETED (December 4, 2025)

All tasks have been implemented. See changes in `core_gameplay.py`:

| Task | Status | Lines Changed |
|------|--------|---------------|
| Q5 Goal Variables | [OK] Already implemented in game loop (~line 1658-1669) | - |
| Q2 Reward/Punishment | [OK] Already implemented via `form_semantic_impression` calls | - |
| Self-Model Aggregation | [OK] Added `_aggregate_controlled_objects()` (~line 3976-4040) | ~65 lines |
| World Model Goals | [OK] Added `_infer_goals_from_frame()` (~line 4041-4090) | ~50 lines |
| Self-Reflection Fix | [OK] Updated `_build_self_reflection_context()` (~line 4960-5070) | ~80 lines |
| DM-1 to DM-6 Integration | [OK] Added decision integrations in `_select_action()` (~line 2655-2770) | ~115 lines |

**Total Added**: ~310 lines of new functionality

---

## Executive Summary

The API payload contains rich data structures for reasoning, but critical feedback loops are broken:
- **Q2 Reward/Punishment**: Never populates danger/reward associations
- **Q5 Goal Variables**: Never tracks score-causing actions
- **Self-Model**: Shows raw coordinates instead of meaningful objects
- **Self-Reflection Networks**: Stuck at default values (0.5, 0.3)

This plan fixes these issues in priority order, with each task scoped for implementation.

---

## Priority 1: Fix Q5 Goal Variables (ROI: 9/10)

### Problem
`actions_with_score_increase` and `actions_causing_game_over` are always empty arrays.

### Root Cause
`_recent_action_traces` is not tracking `score_change` and `outcome_type` fields.

### Implementation - ALREADY DONE

Found at line 1658-1669 in game loop - already tracking score_change and outcome_type.

**Location**: `core_gameplay.py` - Game loop where actions are executed (~line 1700-1800)

**Step 1**: Enhance `_recent_action_traces` structure

```python
# When tracking action in game loop, add score tracking:
trace = {
    'action_type': action,
    'frame_before': previous_frame,
    'frame_after': new_frame,
    'score_before': previous_score,      # NEW
    'score_after': game_state.score,     # NEW
    'score_change': game_state.score - previous_score,  # NEW
    'outcome_type': self._determine_outcome_type(previous_score, game_state)  # NEW
}
```

**Step 2**: Add helper method `_determine_outcome_type()`

```python
def _determine_outcome_type(self, previous_score: float, game_state: GameState) -> str:
    """Classify action outcome for Q5 goal variable analysis."""
    if game_state.state == 'GAME_OVER':
        return 'game_over'
    elif game_state.score > previous_score:
        return 'score_increase'
    elif game_state.state == 'WIN':
        return 'win'
    else:
        return 'neutral'
```

**Step 3**: Verify `_analyze_goal_variables()` reads these fields (already implemented, just needs data)

### Files to Modify
- `core_gameplay.py`: Lines ~1700-1800 (game loop action tracking)

### Verification
- Run a game where agent completes a level
- Check payload: `q5_goal_variables.actions_with_score_increase` should contain the level-completing action

---

## Priority 2: Fix Q2 Reward/Punishment (ROI: 8/10)

### Problem
`dangerous_objects` and `rewarding_objects` are always empty despite `sensation_engine` existing.

### Root Cause
`form_semantic_impression()` is not being called after level completions and game-overs.

### Implementation

**Location 1**: `_handle_level_completion()` (~line 580-700)

```python
# After level completion, form GOAL associations for objects present
if agent_id and hasattr(self, 'sensation_engine'):
    perceived_objects = getattr(self, '_last_perceived_objects', [])
    for obj_type in perceived_objects[:5]:  # Limit to top 5
        try:
            self.sensation_engine.form_semantic_impression(
                agent_id=agent_id,
                object_type=obj_type,
                association='goal',
                strength=0.6,  # Medium-strong association
                context={'level': current_level, 'event': 'level_completion'}
            )
        except Exception:
            pass
```

**Location 2**: `_finalize_game()` on GAME_OVER (~line 700-900)

```python
# On game over (not win), form DANGER associations
if not results['win'] and agent_id and hasattr(self, 'sensation_engine'):
    perceived_objects = getattr(self, '_last_perceived_objects', [])
    for obj_type in perceived_objects[:3]:  # Top 3 most recent
        try:
            self.sensation_engine.form_semantic_impression(
                agent_id=agent_id,
                object_type=obj_type,
                association='danger',
                strength=0.5,
                context={'level': current_level, 'event': 'game_over'}
            )
        except Exception:
            pass
```

**Location 3**: Ensure `_last_perceived_objects` is being set in `_select_action()`

Already exists at line ~2470:
```python
self._last_perceived_objects = sensation_context.get('perceived_objects', [])
```

But need to verify `_analyze_sensation_context()` is returning meaningful object types.

### Files to Modify
- `core_gameplay.py`: `_handle_level_completion()`, `_finalize_game()`

### Verification
- Complete a level, check `q2_reward_punishment.rewarding_objects` has entries
- Fail a game, check `q2_reward_punishment.dangerous_objects` has entries

---

## Priority 3: Improve Self-Model Object Identification (ROI: 8/10)

### Problem
`objects_agent_controls` shows `["x:0,y:0", "x:1,y:0", ...]` (first row pixels) instead of meaningful objects.

### Root Cause
`identify_controlled_objects()` returns raw coordinates without aggregation.

### Implementation

**Location**: `_build_self_model_context()` (~line 3920-3975)

**Step 1**: Aggregate coordinates into object identifiers

```python
def _build_self_model_context(self, agent_id: Optional[str], game_id: str, level: int) -> Dict[str, Any]:
    context = {
        'objects_agent_controls': [],
        'control_confidence': 0.0,
        'object_dependencies': [],
        'network_control_hypotheses': []
    }
    
    if not agent_id:
        return context
    
    try:
        # Get controlled coordinates from agent_self_model
        controlled_coords = self.agent_self_model.get_controlled_objects(agent_id, game_id, level)
        
        if controlled_coords:
            # NEW: Aggregate coordinates into meaningful object identifiers
            aggregated = self._aggregate_controlled_objects(controlled_coords)
            context['objects_agent_controls'] = aggregated[:10]
            
            # Get confidence from DB
            result = self.db.execute_query("""
                SELECT confidence FROM agent_object_control
                WHERE agent_id = ? AND game_id = ? AND level_number = ?
            """, (agent_id, game_id, level))
            if result:
                context['control_confidence'] = result[0]['confidence']
        
        # ... rest of method unchanged ...
```

**Step 2**: Add helper method `_aggregate_controlled_objects()`

```python
def _aggregate_controlled_objects(self, coordinates: List[str]) -> List[str]:
    """
    Convert raw coordinates to meaningful object identifiers.
    
    E.g., ["x:0,y:0", "x:1,y:0", "x:2,y:0"] -> ["horizontal_line_y0_len3"]
    """
    if not coordinates:
        return []
    
    # Parse coordinates
    parsed = []
    for coord in coordinates:
        try:
            parts = coord.replace('x:', '').replace('y:', '').split(',')
            x, y = int(parts[0]), int(parts[1])
            parsed.append((x, y))
        except:
            continue
    
    if not parsed:
        return coordinates[:10]  # Fallback to raw
    
    # Group by row (same y)
    by_row = {}
    for x, y in parsed:
        if y not in by_row:
            by_row[y] = []
        by_row[y].append(x)
    
    # Group by column (same x)
    by_col = {}
    for x, y in parsed:
        if x not in by_col:
            by_col[x] = []
        by_col[x].append(y)
    
    aggregated = []
    
    # Identify horizontal lines (3+ pixels in a row)
    for y, x_list in by_row.items():
        if len(x_list) >= 3:
            x_list.sort()
            # Check if consecutive
            if x_list[-1] - x_list[0] == len(x_list) - 1:
                aggregated.append(f"h_line_y{y}_x{x_list[0]}-{x_list[-1]}")
    
    # Identify vertical lines
    for x, y_list in by_col.items():
        if len(y_list) >= 3:
            y_list.sort()
            if y_list[-1] - y_list[0] == len(y_list) - 1:
                aggregated.append(f"v_line_x{x}_y{y_list[0]}-{y_list[-1]}")
    
    # Identify clusters (adjacent pixels)
    if not aggregated:
        # Just report bounding box
        min_x = min(p[0] for p in parsed)
        max_x = max(p[0] for p in parsed)
        min_y = min(p[1] for p in parsed)
        max_y = max(p[1] for p in parsed)
        aggregated.append(f"region_x{min_x}-{max_x}_y{min_y}-{max_y}_size{len(parsed)}")
    
    return aggregated if aggregated else [f"pixels_{len(parsed)}"]
```

### Files to Modify
- `core_gameplay.py`: `_build_self_model_context()`, add `_aggregate_controlled_objects()`

### Verification
- Check payload: `self_model.objects_agent_controls` shows `["h_line_y0_x0-9"]` instead of raw coords

---

## Priority 4: Populate World Model Goals (ROI: 6/10)

### Problem
`world_model.goals` is always empty despite being a core concept.

### Root Cause
`SymbolicReasoningEngine.world_model.state.get_goals()` returns empty, and no fallback exists.

### Implementation

**Location**: `_build_world_model_context()` (~line 3977-4056)

```python
def _build_world_model_context(self, game_id: str, level: int, frame: Optional[List]) -> Dict[str, Any]:
    context = {
        'obstacles': [],
        'goals': [],
        'agent_position': None,
        'network_hypotheses': []
    }
    
    # ... existing symbolic engine code ...
    
    # NEW: If goals empty, infer from rare colors (same as Q3 salience)
    if not context['goals'] and frame:
        try:
            inferred_goals = self._infer_goals_from_frame(frame)
            context['goals'] = inferred_goals[:3]  # Top 3
        except Exception:
            pass
    
    # ... rest unchanged ...
```

**Add helper method**:

```python
def _infer_goals_from_frame(self, frame: List) -> List[Dict]:
    """Infer goal positions from rare colors in frame."""
    if not frame:
        return []
    
    try:
        import numpy as np
        frame_arr = np.array(frame)
        
        # Find rare colors (< 1% of frame)
        unique, counts = np.unique(frame_arr, return_counts=True)
        total = frame_arr.size
        
        goals = []
        for color, count in zip(unique, counts):
            if color == 0:  # Skip background
                continue
            percentage = count / total
            if percentage < 0.01:  # Less than 1%
                # Find position of this rare color
                positions = np.argwhere(frame_arr == color)
                if len(positions) > 0:
                    # Use centroid
                    centroid = positions.mean(axis=0).astype(int)
                    goals.append({
                        'position': [int(centroid[1]), int(centroid[0])],  # x, y
                        'color': int(color),
                        'inferred': True,
                        'reason': f'rare_color_{percentage*100:.1f}%'
                    })
        
        # Sort by rarity (most rare first)
        goals.sort(key=lambda g: float(g['reason'].split('_')[-1].replace('%', '')))
        return goals
        
    except Exception:
        return []
```

### Files to Modify
- `core_gameplay.py`: `_build_world_model_context()`, add `_infer_goals_from_frame()`

### Verification
- Check payload: `world_model.goals` contains inferred goal positions with rare colors

---

## Priority 5: Fix Self-Reflection Network Calculations (ROI: 5/10)

### Problem
`emotional_network` and `semantic_network` are stuck at 0.5 (default).

### Root Cause
`_build_self_reflection_context()` calculates these from agent data, but input data may be missing/stale.

### Implementation

**Location**: `_build_self_reflection_context()` (~line 4804-4928)

**Step 1**: Add fallback calculations when agent data is missing

```python
def _build_self_reflection_context(
    self,
    agent_id: Optional[str],
    agent_mode: Optional[str],
    action: str,
    game_state: GameState
) -> Optional[Dict[str, Any]]:
    if not agent_id:
        return None
    
    try:
        agent_data = self.db.execute_query("""
            SELECT self_network_bias, navigation_state, role_confidence, 
                   sensation_profile
            FROM agents WHERE agent_id = ?
        """, (agent_id,))
        
        if not agent_data:
            return None
        
        a = agent_data[0]
        self_network_bias = a.get('self_network_bias', 0.5) or 0.5
        navigation_state = a.get('navigation_state', 0.0) or 0.0
        role_confidence = a.get('role_confidence', 0.5) or 0.5
        
        # Parse sensation profile
        sensation_profile = {}
        try:
            sp = a.get('sensation_profile')
            if sp:
                sensation_profile = json.loads(sp) if isinstance(sp, str) else sp
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Calculate emotional input from CURRENT navigation state (not just DB)
        # NEW: Also factor in recent action success
        current_nav = getattr(self, '_current_navigation_state', navigation_state)
        emotional_input = (current_nav + 1.0) / 2.0  # Map -1..1 to 0..1
        
        # NEW: Factor in recent success/failure from game state
        if game_state.score > 0:
            emotional_input = min(1.0, emotional_input + 0.1 * game_state.score)
        
        # Semantic input from sensation profile
        object_sensations = sensation_profile.get('object_sensations', {})
        if object_sensations:
            top_sensations = sorted(object_sensations.values(), reverse=True)[:3]
            semantic_input = (sum(top_sensations) / len(top_sensations) + 1.0) / 2.0
        else:
            # NEW: Fallback - use perceived objects count as proxy
            perceived_count = len(getattr(self, '_last_perceived_objects', []))
            semantic_input = min(1.0, 0.3 + perceived_count * 0.05)
        
        # ... rest of method ...
```

### Files to Modify
- `core_gameplay.py`: `_build_self_reflection_context()`

### Verification
- Check payload: `self_reflection.emotional_network` varies based on game progress
- Check payload: `self_reflection.semantic_network` varies based on perceived objects

---

## Priority 6: Add Conflict Detection Action (ROI: 5/10)

### Problem
`self_reflection.conflict` is always `false` despite being calculated.

### Root Cause
Conflict is detected but never acted upon.

### Implementation

**Location**: `_select_action()` (~line 2334-2907)

After building self-reflection context, check for conflict:

```python
# After emergent reasoning section, before final action selection:

# Two-Streams: Handle conflict between private memory and network wisdom
if agent_id:
    try:
        self_reflection = self._build_self_reflection_context(agent_id, agent_mode, base_action, game_state)
        if self_reflection and self_reflection.get('conflict'):
            # Conflict detected - use self_trust_bias to decide
            bias = self_reflection.get('self_trust_bias', 0.5)
            private_strength = self_reflection.get('private_memory', 0.3)
            network_strength = self_reflection.get('network_wisdom', 0.3)
            
            if bias > 0.6 and private_strength > network_strength:
                # Trust self - try a different action
                logger.info(f"[CONFLICT] Stream conflict detected. Self-trusting (bias={bias:.2f}), trying alternative.")
                # Prefer exploration action
                base_action = "ACTION6" if random.random() > 0.3 else f"ACTION{random.randint(1,7)}"
                conflict_reasoning = f"CONFLICT RESOLVED: Trusting self over network (bias={bias:.2f})"
                reasoning_parts.append(conflict_reasoning)
            elif bias < 0.4 and network_strength > private_strength:
                # Trust network - keep current action but log it
                logger.info(f"[CONFLICT] Stream conflict detected. Following network (bias={bias:.2f}).")
            else:
                # Balanced - add some randomness
                if random.random() < 0.3:
                    base_action = f"ACTION{random.randint(1,7)}"
                    reasoning_parts.append(f"CONFLICT: Balanced exploration (bias={bias:.2f})")
    except Exception:
        pass
```

### Files to Modify
- `core_gameplay.py`: `_select_action()`

### Verification
- When `conflict=true` in payload, agent takes different action than it would have

---

## Priority 7: Consolidate network_hypotheses and failure_insights (ROI: 3/10)

### Problem
`world_model.network_hypotheses` is always empty while `failure_insights` has data.

### Implementation

**Option A**: Populate `network_hypotheses` from `learned_rules`

**Location**: `_build_world_model_context()` - Already has code for this, just not working

```python
# Existing code that should work:
try:
    game_type = game_id[:4] if game_id else ""
    rules = self.db.execute_query("""
        SELECT rule_id, confidence, success_count, failure_count
        FROM learned_rules
        WHERE (applicable_games LIKE ? OR source_game_id LIKE ?)
          AND confidence > 0.5
        ORDER BY confidence DESC, success_count DESC
        LIMIT 3
    """, (f'%{game_type}%', f'{game_type}%'))
    
    if rules:
        context['network_hypotheses'] = [...]
```

**Debug Step**: Add logging to see if `learned_rules` table has data

```python
# Temporary debug
rule_count = self.db.execute_query("SELECT COUNT(*) as c FROM learned_rules")
logger.debug(f"[DEBUG] learned_rules table has {rule_count[0]['c']} rows")
```

**Option B**: Rename/merge fields for clarity

If `learned_rules` is intentionally empty, just remove `network_hypotheses` and keep `failure_insights`.

### Verification
- Either `network_hypotheses` has data, or remove the field

---

## Implementation Order

| Order | Task | Estimated Lines | Risk |
|-------|------|-----------------|------|
| 1 | Q5 Goal Variables (score tracking) | ~30 lines | Low |
| 2 | Q2 Reward/Punishment (form_semantic_impression calls) | ~40 lines | Low |
| 3 | Self-Model Object Aggregation | ~60 lines | Medium |
| 4 | World Model Goals Inference | ~40 lines | Low |
| 5 | Self-Reflection Network Fix | ~20 lines | Low |
| 6 | Conflict Detection Action | ~30 lines | Low |
| 7 | Network Hypotheses Debug/Fix | ~10 lines | Low |

**Total Estimated**: ~230 lines of changes

---

## Testing Strategy

### Unit Test Checklist

1. **Q5**: Create mock action trace with score change, verify `_analyze_goal_variables()` returns non-empty
2. **Q2**: Call `form_semantic_impression()` manually, verify `query_personal_impression()` returns it
3. **Self-Model**: Pass coordinate list to `_aggregate_controlled_objects()`, verify output is aggregated
4. **Goals**: Pass frame with rare color, verify `_infer_goals_from_frame()` returns goal position

### Integration Test

1. Run a single game with logging enabled
2. Capture payload at:
   - Level completion (verify Q2 rewarding_objects populated)
   - Score increase (verify Q5 actions_with_score_increase populated)
   - Game end (verify all fields have meaningful data)

---

## Success Metrics

After implementation, the following should be true in API payloads:

| Field | Before | After |
|-------|--------|-------|
| `q5_goal_variables.actions_with_score_increase` | Always `[]` | Contains action that caused score increase |
| `q2_reward_punishment.rewarding_objects` | Always `[]` | Contains objects associated with wins |
| `q2_reward_punishment.dangerous_objects` | Always `[]` | Contains objects associated with failures |
| `self_model.objects_agent_controls` | Raw coordinates | Aggregated identifiers |
| `world_model.goals` | Always `[]` | Inferred goal positions |
| `self_reflection.emotional_network` | Always `0.5` | Varies 0.3-0.8 based on game state |
| `self_reflection.conflict` | Always `false` | Sometimes `true` when streams disagree |

---

---

## Decision-Making Integration

Once the payload data is fixed, it must be **actively used** in `_select_action()` to influence decisions. This section details how each improved data field should modify agent behavior.

---

### DM-1: Use Q5 Goal Variables in Action Selection

**Current State**: Q5 data is built but never used in decision-making.

**Implementation Location**: `_select_action()` (~line 2630, after emergent reasoning is built)

```python
# After _build_emergent_reasoning_context() call:
if emergent_reasoning:
    q5_data = emergent_reasoning.get('q5_goal_variables', {})
    
    # BOOST: Actions that previously caused score increases
    score_actions = q5_data.get('actions_with_score_increase', [])
    for action_num in score_actions:
        if action_num in hypothesis_biases:
            hypothesis_biases[action_num] += 0.4  # Strong positive boost
        else:
            hypothesis_biases[action_num] = 0.4
        logger.debug(f"[Q5] Boosting ACTION{action_num} (caused score increase)")
    
    # PENALIZE: Actions that caused game-over
    game_over_actions = q5_data.get('actions_causing_game_over', [])
    for action_num in game_over_actions:
        if action_num in hypothesis_biases:
            hypothesis_biases[action_num] -= 0.5  # Strong negative
        else:
            hypothesis_biases[action_num] = -0.5
        logger.debug(f"[Q5] Penalizing ACTION{action_num} (caused game-over)")
```

**Decision Impact**:
- Actions that previously increased score get +0.4 bias boost
- Actions that caused game-over get -0.5 penalty
- This creates immediate feedback loop: agent learns from its own session

---

### DM-2: Use Q2 Reward/Punishment for Object Avoidance

**Current State**: Q2 data is built but never influences action choice.

**Implementation Location**: `_select_action()` (~line 2500, in sensation biases section)

```python
# After sensation_biases are calculated:
if emergent_reasoning:
    q2_data = emergent_reasoning.get('q2_reward_punishment', {})
    
    dangerous_objects = q2_data.get('dangerous_objects', [])
    rewarding_objects = q2_data.get('rewarding_objects', [])
    
    # If we have strong danger associations, increase caution
    if dangerous_objects:
        danger_strength = sum(d.get('strength', 0.5) for d in dangerous_objects) / len(dangerous_objects)
        if danger_strength > 0.5:
            # Penalize ACTION6 (click) when dangerous objects present
            # Agent should be cautious about interacting
            sensation_biases[6] = sensation_biases.get(6, 0) - 0.3 * danger_strength
            logger.debug(f"[Q2] Danger detected ({len(dangerous_objects)} objects) - reducing ACTION6 bias")
    
    # If we have reward associations, boost exploration toward them
    if rewarding_objects:
        # Boost ACTION6 to interact with rewarding objects
        reward_strength = sum(r.get('strength', 0.5) for r in rewarding_objects) / len(rewarding_objects)
        sensation_biases[6] = sensation_biases.get(6, 0) + 0.2 * reward_strength
        logger.debug(f"[Q2] Rewards detected ({len(rewarding_objects)} objects) - boosting ACTION6")
```

**Decision Impact**:
- High danger → agent avoids clicking (more cautious movement)
- High reward → agent more willing to click/interact
- Creates learned object associations that transfer across sessions

---

### DM-3: Use Aggregated Self-Model for Identity-Based Decisions

**Current State**: Self-model is built but not used for "I am this object" reasoning.

**Implementation Location**: `_select_action()` (~line 2400, new section after self-model context)

```python
# Query self-model context for identity-based decisions
self_model_context = self._build_self_model_context(agent_id, game_id, current_level)
controlled_objects = self_model_context.get('objects_agent_controls', [])

if controlled_objects:
    # Parse the aggregated object type
    for obj in controlled_objects[:1]:  # Primary controlled object
        if 'h_line' in obj:
            # Horizontal line - movement should be horizontal
            # Boost left/right actions
            hypothesis_biases[3] = hypothesis_biases.get(3, 0) + 0.15  # Left
            hypothesis_biases[4] = hypothesis_biases.get(4, 0) + 0.15  # Right
            logger.debug(f"[SELF] Controlling horizontal object - boosting lateral movement")
        
        elif 'v_line' in obj:
            # Vertical line - movement should be vertical
            hypothesis_biases[1] = hypothesis_biases.get(1, 0) + 0.15  # Up
            hypothesis_biases[2] = hypothesis_biases.get(2, 0) + 0.15  # Down
            logger.debug(f"[SELF] Controlling vertical object - boosting vertical movement")
        
        elif 'region' in obj:
            # Complex region - try clicking for transformation
            hypothesis_biases[6] = hypothesis_biases.get(6, 0) + 0.1
            logger.debug(f"[SELF] Controlling region - boosting click for transformation")
```

**Decision Impact**:
- Agent understands its "body shape" and moves accordingly
- Horizontal objects → prefer horizontal movement
- Vertical objects → prefer vertical movement
- Complex regions → prefer clicking for transformation

---

### DM-4: Use Inferred Goals for Directed Exploration

**Current State**: World model goals would be inferred but not used for navigation.

**Implementation Location**: `_select_action()` (~line 2700, after network wisdom section)

```python
# Use inferred goals for directed exploration
world_model_context = self._build_world_model_context(game_id, current_level, game_state.frame)
goals = world_model_context.get('goals', [])

if goals and game_state.frame:
    primary_goal = goals[0]
    goal_pos = primary_goal.get('position', [])
    
    if len(goal_pos) == 2:
        goal_x, goal_y = goal_pos
        
        # Get current agent position (if known)
        agent_pos = world_model_context.get('agent_position')
        if agent_pos and len(agent_pos) == 2:
            agent_x, agent_y = agent_pos
            
            # Calculate direction to goal
            dx = goal_x - agent_x
            dy = goal_y - agent_y
            
            # Bias actions toward goal
            if abs(dx) > abs(dy):
                # Prioritize horizontal movement
                if dx > 0:
                    hypothesis_biases[4] = hypothesis_biases.get(4, 0) + 0.2  # Right
                else:
                    hypothesis_biases[3] = hypothesis_biases.get(3, 0) + 0.2  # Left
            else:
                # Prioritize vertical movement
                if dy > 0:
                    hypothesis_biases[2] = hypothesis_biases.get(2, 0) + 0.2  # Down
                else:
                    hypothesis_biases[1] = hypothesis_biases.get(1, 0) + 0.2  # Up
            
            logger.debug(f"[GOAL] Moving toward inferred goal at ({goal_x}, {goal_y}) from ({agent_x}, {agent_y})")
        
        else:
            # No agent position - try clicking on goal directly
            hypothesis_biases[6] = hypothesis_biases.get(6, 0) + 0.25
            # Store goal coordinates for ACTION6
            self._goal_click_target = (goal_x, goal_y)
            logger.debug(f"[GOAL] No agent position - targeting goal at ({goal_x}, {goal_y}) for click")
```

**Decision Impact**:
- Agent navigates TOWARD inferred goals (rare colors)
- If agent position unknown, tries clicking on goal directly
- Creates directed exploration instead of random wandering

---

### DM-5: Use Dynamic Self-Reflection for Stream Arbitration

**Current State**: Self-reflection networks are calculated but static values don't influence decisions.

**Implementation Location**: `_select_action()` (~line 2850, before final action assembly)

```python
# Two-Streams Arbitration: Dynamic bias adjustment based on emotional state
if agent_id:
    self_reflection = self._build_self_reflection_context(agent_id, agent_mode, base_action, game_state)
    
    if self_reflection:
        emotional_network = self_reflection.get('emotional_network', 0.5)
        semantic_network = self_reflection.get('semantic_network', 0.5)
        identity_network = self_reflection.get('identity_network', 0.5)
        
        # Frustrated state (low emotional) -> increase exploration variance
        if emotional_network < 0.3:
            # Agent is frustrated - try something different
            random_boost = random.choice([1, 2, 3, 4, 5, 6, 7])
            hypothesis_biases[random_boost] = hypothesis_biases.get(random_boost, 0) + 0.3
            logger.info(f"[STREAM] Frustrated (emotional={emotional_network:.2f}) - adding variance to ACTION{random_boost}")
        
        # High semantic awareness -> trust object associations more
        if semantic_network > 0.7:
            # Strong semantic context - amplify sensation biases
            for action, bias in sensation_biases.items():
                sensation_biases[action] = bias * 1.5
            logger.debug(f"[STREAM] High semantic awareness ({semantic_network:.2f}) - amplifying sensation biases")
        
        # Low identity confidence -> explore role alternatives
        if identity_network < 0.3:
            # Not confident in role - try actions outside normal role behavior
            if agent_mode == 'pioneer':
                # Pioneer with low identity might try optimizer behavior (sequence replay)
                hypothesis_biases[5] = hypothesis_biases.get(5, 0) + 0.2  # Wait/observe
            elif agent_mode == 'optimizer':
                # Optimizer with low identity might try pioneer behavior (exploration)
                hypothesis_biases[6] = hypothesis_biases.get(6, 0) + 0.2  # Explore
            logger.debug(f"[STREAM] Low identity ({identity_network:.2f}) - trying cross-role behavior")
```

**Decision Impact**:
- Frustrated agents add randomness to break out of loops
- High semantic awareness amplifies learned object associations
- Low identity confidence causes role-crossing behavior (pioneers optimize, optimizers explore)

---

### DM-6: Conflict Resolution with Action Override

**Current State**: Conflict detected but never acted upon.

**Implementation Location**: `_select_action()` (~line 2880, new section)

```python
# Stream Conflict Resolution
if self_reflection and self_reflection.get('conflict'):
    bias = self_reflection.get('self_trust_bias', 0.5)
    private_strength = self_reflection.get('private_memory', 0.3)
    network_strength = self_reflection.get('network_wisdom', 0.3)
    
    logger.info(f"[CONFLICT] Stream conflict! Self={private_strength:.2f}, Network={network_strength:.2f}, Bias={bias:.2f}")
    
    if bias > 0.6:
        # High self-trust: Ignore network recommendation, explore on own
        if private_strength > 0.5:
            # Strong private memory + high bias = trust yourself completely
            # Override any network-suggested action
            self._self_directed_mode = True
            logger.info(f"[CONFLICT] Resolved: Trusting self (strong private memory)")
        else:
            # High bias but weak memory = random exploration
            base_action = f"ACTION{random.choice([1, 2, 3, 4, 5, 6, 7])}"
            reasoning_parts.append(f"CONFLICT: Self-trust override (bias={bias:.2f})")
            logger.info(f"[CONFLICT] Resolved: Random exploration (weak memory but high bias)")
    
    elif bias < 0.4:
        # Low self-trust: Follow network even if it feels wrong
        # Don't change action, but log for debugging
        logger.info(f"[CONFLICT] Resolved: Following network (low self-trust)")
        reasoning_parts.append(f"CONFLICT: Network override (bias={bias:.2f})")
    
    else:
        # Balanced bias: Use coin flip weighted by relative strengths
        follow_network = random.random() < (network_strength / (private_strength + network_strength + 0.01))
        if not follow_network:
            base_action = f"ACTION{random.choice([1, 2, 3, 4, 5, 6, 7])}"
            reasoning_parts.append(f"CONFLICT: Balanced coin-flip chose self")
        logger.info(f"[CONFLICT] Resolved: Coin flip -> {'network' if follow_network else 'self'}")
```

**Decision Impact**:
- High self-trust agents override network recommendations during conflict
- Low self-trust agents follow network even when uncomfortable
- Balanced agents use weighted random choice
- Conflict resolution is logged for debugging

---

## Decision-Making Summary Table

| Data Field | Decision Impact | Bias Type | Magnitude |
|------------|----------------|-----------|-----------|
| Q5: score_increase actions | Boost those actions | `hypothesis_biases` | +0.4 |
| Q5: game_over actions | Penalize those actions | `hypothesis_biases` | -0.5 |
| Q2: dangerous_objects | Reduce clicking | `sensation_biases[6]` | -0.3 × strength |
| Q2: rewarding_objects | Boost clicking | `sensation_biases[6]` | +0.2 × strength |
| Self-Model: h_line | Boost lateral movement | `hypothesis_biases[3,4]` | +0.15 |
| Self-Model: v_line | Boost vertical movement | `hypothesis_biases[1,2]` | +0.15 |
| Goals: inferred position | Navigate toward goal | `hypothesis_biases` | +0.2 |
| Self-Reflection: frustrated | Add random variance | `hypothesis_biases[random]` | +0.3 |
| Self-Reflection: high semantic | Amplify sensation biases | multiplier | ×1.5 |
| Self-Reflection: conflict | Override or random | action override | varies |

---

## Implementation Order (Updated)

| Order | Task | Includes DM? | Total Lines |
|-------|------|--------------|-------------|
| 1 | Q5 Goal Variables + DM-1 | Yes | ~50 |
| 2 | Q2 Reward/Punishment + DM-2 | Yes | ~60 |
| 3 | Self-Model Aggregation + DM-3 | Yes | ~80 |
| 4 | World Model Goals + DM-4 | Yes | ~70 |
| 5 | Self-Reflection Networks + DM-5 | Yes | ~50 |
| 6 | Conflict Detection + DM-6 | Yes | ~50 |
| 7 | Network Hypotheses Debug | No | ~10 |

**Total Estimated**: ~370 lines of changes

---

## Dependencies

None - all changes are internal to `core_gameplay.py` and use existing infrastructure.

## Rollback Plan

Each change is independent. If any causes issues:
1. Revert that specific function
2. Other improvements continue working
3. No database schema changes required
