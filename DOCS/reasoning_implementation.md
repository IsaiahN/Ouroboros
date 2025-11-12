# Reasoning Implementation for ARC API

## Overview
Implemented comprehensive reasoning generation and propagation system to send decision rationale with every action to the ARC AGI 3 API. This enables replay analysis showing WHY agents chose each action.

## Implementation Date
2025-01-XX (Gen 162→182)

## Changes Made

### 1. Modified `_select_action()` Return Type
**File**: `core_gameplay.py`
**Change**: Return type changed from `str` to `tuple[str, str]`
```python
async def _select_action(self, game_state: GameState) -> tuple[str, str]:
    """Returns: Tuple of (action, reasoning)"""
```

### 2. Reasoning Generation by Decision Source

#### Subgoal Planning
```python
reasoning = f"Following hierarchical subgoal plan (plan_id: {plan_id[:8]})"
```

#### Meta-Learning Patterns
```python
reasoning = f"Meta-learned {pattern_result['pattern_type']} pattern (confidence: {pattern_result['confidence']:.2f})"
reasoning = f"Continuing meta-learned pattern: {next_action['reason']}"
```

#### Sensation-Based Navigation (Emotional Intelligence)
```python
# Positive bias reinforcement
reasoning = f"{emotion.capitalize()} state (nav: {navigation_state:.2f}) - positive sensation bias (bias: {current_bias:.2f})"

# Negative bias avoidance
reasoning = f"{emotion.capitalize()} state (nav: {navigation_state:.2f}) - switched from negative bias to positive alternative (bias: {best_bias:.2f})"
```

#### Viral Package Influence
```python
# Pariah avoidance with alternative suggestion
reasoning = f"Viral package suggested ACTION{best_alt} (net influence: {alt_influence:.2f}) - avoiding pariah penalty on {base_action} (penalty: {penalty:.2f})"

# Viral reinforcement
viral_reasoning = f"Viral package reinforcement (weight: {weight:.2f})"
```

#### Default Strategy
```python
# Combines multiple factors
reasoning_parts = []
if is_unbeaten_game:
    reasoning_parts.append("Unbeaten game - full exploration")
if sensation_reasoning:
    reasoning_parts.append(sensation_reasoning)
if viral_reasoning:
    reasoning_parts.append(viral_reasoning)
if not reasoning_parts:
    reasoning_parts.append(f"Standard {strategy} strategy")

final_reasoning = " | ".join(reasoning_parts)
```

### 3. Modified `_execute_action()` Signature
**File**: `core_gameplay.py`
**Change**: Added reasoning parameter and propagation logic
```python
async def _execute_action(self, action: str, game_state: GameState, reasoning: str = "") -> GameState:
```

**Default Reasoning Generation** (if not provided):
```python
agent_mode = self._get_agent_operating_mode(self.game_config.get('agent_id'))
score = game_state.score

reasoning_parts = []
if agent_mode:
    reasoning_parts.append(f"{agent_mode.upper()} mode")
reasoning_parts.append(f"Score: {score}")
reasoning = " | ".join(reasoning_parts)
```

**ACTION6 Reasoning Enhancement**:
```python
# Combines base reasoning with coordinate selection reasoning
full_reasoning = f"{reasoning} | Visual: {reason}"
# or
full_reasoning = f"{reasoning} | Meta-pattern: {reason}"
```

### 4. Updated Action Handler Call
**File**: `core_gameplay.py`
**Change**: Pass reasoning to all action methods
```python
# ACTION1-5,7
return await method(reasoning=reasoning)

# ACTION6
new_state = await self.action_handler.send_action_6(x, y, game_state.frame, reasoning=full_reasoning)
```

### 5. Enhanced `send_action_6()` Signature
**File**: `action_handler.py`
**Change**: Added optional reasoning parameter
```python
async def send_action_6(self, x: int, y: int, frame: Optional[List[List[int]]] = None, reasoning: Optional[str] = None) -> GameState:
    if reasoning:
        return await self._send_action_with_context("ACTION6", x=x, y=y, coordinates=[x, y], reasoning=reasoning)
    else:
        return await self._send_action_with_context("ACTION6", x=x, y=y, coordinates=[x, y])
```

### 6. Updated Call Site in Game Loop
**File**: `core_gameplay.py`
**Change**: Unpack tuple from `_select_action()`
```python
# Old
action = await self._select_action(game_state)
game_state = await self._execute_action(action, game_state)

# New
action, reasoning = await self._select_action(game_state)
game_state = await self._execute_action(action, game_state, reasoning)
```

## Reasoning Flow Chain

```
_select_action() 
  ↓ (action, reasoning)
_execute_action()
  ↓ enhances reasoning with coordinate context for ACTION6
action_handler.send_action_X(reasoning=...)
  ↓ 
_send_action_with_context(..., reasoning=reasoning)
  ↓ **kwargs
game_session_manager.send_action(**kwargs)
  ↓ **kwargs
arc_api_client.send_action(..., **kwargs)
  ↓ payload['reasoning'] = kwargs.get('reasoning', '')
ARC API
```

## Example Reasoning Strings

### Specialist Mode (OPTIMIZER)
```
"OPTIMIZER mode | Score: 12 | Following hierarchical subgoal plan (plan_id: abc12345)"
"OPTIMIZER mode | Score: 8 | Curious state (nav: 0.65) - positive sensation bias (bias: 0.45) | Visual: Central cluster @ (5,6)"
"OPTIMIZER mode | Score: 15 | Viral package reinforcement (weight: 0.82)"
```

### Pioneer Mode (Frontier Exploration)
```
"PIONEER mode | Score: 0 | Unbeaten game - full exploration | Visual: Edge feature @ (2,9)"
"PIONEER mode | Score: 5 | Meta-learned symmetry pattern (confidence: 0.87) | Visual: Symmetric point @ (7,7)"
```

### Generalist Mode (Stable Baseline)
```
"GENERALIST mode | Score: 10 | Standard balanced strategy"
"GENERALIST mode | Score: 3 | Viral package suggested ACTION4 (net influence: 0.67) - avoiding pariah penalty on ACTION1 (penalty: 0.88)"
```

## Benefits

1. **Replay Analysis**: ARC scorecards show WHY each action was chosen
2. **Mode Validation**: Can verify OPTIMIZER actually optimizes, PIONEER actually explores
3. **System Debugging**: Identify if subgoal planning, sensation navigation, or viral packages are effective
4. **Research Value**: Understand what strategies lead to wins vs losses
5. **Evolutionary Insights**: Track which reasoning patterns correlate with high performance

## ARC API Visibility

All reasoning is visible in:
- ARC scorecard replays on https://three.arcprize.org
- Reasoning log section showing decision rationale for each action
- Searchable/filterable by reasoning content

## Testing Verification

To verify reasoning is being sent:
```python
# Check database for recent actions with reasoning
from database_interface import DatabaseInterface
db = DatabaseInterface()

actions = db.execute_query("""
    SELECT action_type, action_number, coordinate_x, coordinate_y, 
           reasoning, action_timestamp
    FROM arc_action_tracking 
    WHERE action_timestamp > datetime('now', '-1 hour')
      AND reasoning IS NOT NULL
    ORDER BY action_timestamp DESC
    LIMIT 20
""")
```

## Bug Fixes (Pre-existing)

While implementing reasoning, also fixed two pre-existing type errors:

**1. Session Manager Client Null Check** (line 316)
- **Issue**: `self.session_manager.client.reset_game()` could fail if client is None
- **Fix**: Added null check before accessing client
```python
if not self.session_manager.client:
    raise ValueError("Session manager client not initialized")
```

**2. Max Games Null Check** (line 1088)
- **Issue**: `_select_diverse_games(game_ids, max_games)` called when `max_games` could be None
- **Fix**: Added null check to condition
```python
if self.game_config.get('diversity_mode') and self.game_config.get('enforce_game_diversity') and max_games:
    game_ids = self._select_diverse_games(game_ids, max_games)
```

## Notes

- All pre-existing action_handler methods already supported reasoning parameter (ACTION1-5,7)
- ACTION6 required signature enhancement to accept reasoning
- get_smart_coordinates() already returns reasoning tuple `(x, y, reason)`
- Full chain from selection to API was already in place, just needed activation
- No breaking changes - reasoning defaults to empty string if not provided
- All type errors now resolved

## Related Files

- `core_gameplay.py` - Action selection and execution (lines 645-932)
- `action_handler.py` - Action wrapper methods (lines 319-405)
- `game_session_manager.py` - Session management (lines 300-380)
- `arc_api_client.py` - API interface (lines 431-503)
- `agent_operating_mode_system.py` - Mode definitions (OPTIMIZER/PIONEER/GENERALIST)
