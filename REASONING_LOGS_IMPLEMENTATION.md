# Reasoning Logs Implementation

## Summary

Added comprehensive reasoning metadata to all ARC API action calls. Every action (ACTION1-ACTION7) now sends structured JSON reasoning (≤16 KB) with agent context, genome config, and decision factors.

## Changes Made

### 1. arc_api_client.py (Lines 500-520)
**Before:**
- Reasoning only added for non-ACTION6 actions
- Inconsistent reasoning support

**After:**
```python
# Add reasoning for ALL actions (optional JSON blob ≤16 KB)
if "reasoning" in kwargs and kwargs["reasoning"]:
    payload["reasoning"] = kwargs["reasoning"]
```
- Reasoning now added to ALL actions uniformly
- Supports both ACTION6 and ACTION1-5,7

### 2. core_gameplay.py

#### Added _format_reasoning_for_api() method (Lines 1481-1540)
Converts human-readable reasoning text into structured JSON metadata:

```python
reasoning_obj = {
    'action': action,
    'reasoning': reasoning_text,
    'level': current_level,
    'score': game_state.score,
    'timestamp': datetime.now().isoformat(),
    'agent_id': agent_id,
    'agent_mode': agent_mode,
    'genome': {
        'agent_type': genome.get('agent_type'),
        'exploration_rate': genome.get('exploration_rate'),
        'learning_rate': genome.get('learning_rate')
    },
    'strategy': self.game_config.get('strategy', 'balanced'),
    'learning_mode': self.game_config.get('learning_mode', 'smart_exploration')
}
```

**Size Enforcement:**
- Automatically truncates reasoning text if JSON exceeds 16 KB
- Ensures compliance with ARC API limits

#### Updated _execute_action() method (Lines 1096-1180)
**Before:**
- Reasoning passed as plain string
- No structured metadata

**After:**
```python
# Format reasoning as JSON object (≤16 KB) for ARC API
reasoning_json = self._format_reasoning_for_api(
    action=action,
    reasoning_text=reasoning,
    game_state=game_state,
    current_level=current_level
)

# Pass reasoning_json to all actions
await method(reasoning=reasoning_json, level_number=current_level)
```

#### Updated sequence replay methods (Lines 2130-2290)
Added reasoning to all sequence replay operations:
```python
replay_reasoning = {
    'action': 'ACTION6',
    'reasoning': f'Replaying known winning sequence {sequence_id[:8]}',
    'sequence_id': sequence_id,
    'replay_step': action_count + 1,
    'total_steps': len(actions),
    'coordinate': {'x': x, 'y': y}
}
```

#### Updated exploration_strategy() (Lines 3587-3610)
Added reasoning to exploration:
```python
exploration_reasoning = {
    'action': 'ACTION6',
    'reasoning': 'Random exploration strategy',
    'coordinate': {'x': x, 'y': y},
    'strategy': 'exploration'
}
```

### 3. action_handler.py

#### Updated all send_action methods (Lines 344-445)
**Before:**
```python
async def send_action_1(self, reasoning: str = "Action 1", level_number: int = 1)
```

**After:**
```python
async def send_action_1(self, reasoning: Optional[Dict[str, Any]] = None, level_number: int = 1)
```

Changes applied to:
- `send_action_1()` through `send_action_7()`
- Updated type hints from `str` to `Optional[Dict[str, Any]]`
- Updated docstrings to specify "reasoning dict/JSON (≤16 KB)"

#### Updated random action selection (Lines 680-705)
Added reasoning to random actions:
```python
random_reasoning = {
    'action': action,
    'reasoning': 'Random action selection'
}
return await method(reasoning=random_reasoning)
```

### 4. start_game.py (Lines 98-104)
Updated test game to include reasoning:
```python
test_reasoning = {
    'action': 'ACTION1',
    'reasoning': 'Test game action',
    'test_mode': True
}
game_state = await action_handler_instance.send_action_1(reasoning=test_reasoning)
```

## Reasoning Data Structure

### Typical Reasoning Object
```json
{
  "action": "ACTION6",
  "reasoning": "Visual analyzer detected high-value target | Viral package reinforcement (weight: 0.8)",
  "level": 2,
  "score": 15.5,
  "timestamp": "2024-01-15T10:30:45.123456",
  "agent_id": "agent_abc123",
  "agent_mode": "optimizer",
  "genome": {
    "agent_type": "pattern_specialist",
    "exploration_rate": 0.3,
    "learning_rate": 0.05
  },
  "strategy": "balanced",
  "learning_mode": "smart_exploration",
  "coordinate": {
    "x": 15,
    "y": 23
  },
  "visual_reason": "Brightest pixel cluster detected"
}
```

### Sequence Replay Reasoning
```json
{
  "action": "ACTION6",
  "reasoning": "Replaying known winning sequence a1b2c3d4",
  "sequence_id": "seq_a1b2c3d4e5f6",
  "replay_step": 5,
  "total_steps": 12,
  "coordinate": {
    "x": 10,
    "y": 15
  }
}
```

### Random Exploration Reasoning
```json
{
  "action": "ACTION3",
  "reasoning": "Random action selection",
  "strategy": "exploration"
}
```

## Flow Diagram

```
core_gameplay.py
  ↓
  _select_action()
    → Returns: (action_str, reasoning_text)
  ↓
  _execute_action(action, game_state, reasoning_text, current_level)
    ↓
    _format_reasoning_for_api()  [NEW]
      → Converts reasoning_text to JSON object
      → Adds agent context, genome, timestamp
      → Ensures ≤16 KB size
    ↓
    action_handler.send_action_N(reasoning=reasoning_json, level_number=current_level)
      ↓
      _send_action_with_context(action, **kwargs)
        ↓
        session_manager.send_action(action, **kwargs)
          ↓
          arc_api_client.send_action(action, **kwargs)
            ↓
            payload = {
              "game_id": game_id,
              "card_id": card_id,
              "guid": guid,
              "reasoning": kwargs["reasoning"]  [ADDED TO ALL ACTIONS]
            }
            ↓
            POST to ARC API with reasoning metadata
```

## Benefits

1. **Complete Traceability**: Every action sent to ARC API includes full context
2. **Post-hoc Analysis**: Can analyze agent decision-making from API logs
3. **Debugging**: Reasoning metadata helps identify why actions were taken
4. **Agent Tracking**: Links actions to specific agents, genomes, and strategies
5. **Temporal Context**: Timestamps allow correlation with other events
6. **Size Safety**: Automatic truncation prevents API errors

## Testing Verification

### Test 1: Compile Check
✅ All files compile without errors:
- core_gameplay.py
- action_handler.py
- arc_api_client.py
- start_game.py

### Test 2: Type Safety
✅ Type hints updated correctly:
- `reasoning: Optional[Dict[str, Any]]` for all send_action methods
- Backward compatible (None default values)

### Test 3: Integration Points
✅ All action call sites updated:
- Main game loop in `_execute_action()`
- Sequence replay (2 locations)
- Exploration strategy
- Random action selection
- Test game (start_game.py)

## Compliance with Requirements

User requested: **"every action should send a reasoning log with each action sent to api"**

✅ **COMPLETE**:
- All ACTION1-ACTION7 send reasoning to API
- Reasoning format: JSON object (dict) ≤16 KB
- Includes agent context, genome, strategy, timestamp
- Structured metadata enables post-hoc analysis
- Example payload provided matches user's specification

## Example API Payload

```json
{
  "game_id": "sp80-lv1",
  "card_id": "card_abc123",
  "guid": "guid_xyz789",
  "x": 15,
  "y": 23,
  "reasoning": {
    "action": "ACTION6",
    "reasoning": "Visual analyzer: brightest cluster | Viral boost (0.8)",
    "level": 1,
    "score": 0.0,
    "timestamp": "2024-01-15T10:30:45.123456",
    "agent_id": "agent_pioneer_001",
    "agent_mode": "pioneer",
    "genome": {
      "agent_type": "pattern_specialist",
      "exploration_rate": 0.3,
      "learning_rate": 0.05
    },
    "strategy": "balanced",
    "learning_mode": "smart_exploration",
    "coordinate": {
      "x": 15,
      "y": 23
    },
    "visual_reason": "Brightest pixel cluster (value: 255)"
  }
}
```

## Future Enhancements

Potential additions (not implemented):
- Action effectiveness metrics in reasoning
- Historical action context (last N actions)
- Frame change predictions
- Confidence scores for action selection
- Multi-agent coordination metadata

---

**Implementation Date**: 2024-01-15
**Status**: ✅ COMPLETE
**Files Modified**: 4
**Lines Changed**: ~150
**Test Status**: ✅ All syntax checks passed
