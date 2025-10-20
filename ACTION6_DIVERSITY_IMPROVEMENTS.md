# ACTION6 Coordinate Diversity - Implemented

**Date**: October 19, 2025  
**Branch**: Ouroboros

## Problem Solved

**Issue**: ACTION6 was spamming the same coordinates repeatedly, leading to:
- Same target clicked over and over: (31, 0) repeated 100+ times
- No exploration of other potentially productive targets
- Inefficient gameplay with no frame changes

## Solution Implemented

### 1. Clicked Coordinate Tracking

Added to `visual_analyzer.py`:
```python
def __init__(self):
    self.previous_frame = None
    self.clicked_coordinates = set()  # Track tried coordinates
    self.last_action_changed_frame = False
    self.consecutive_no_change_count = 0
```

### 2. Frame Change Detection

```python
def update_frame_change_tracking(self, new_frame):
    """Track whether actions are productive (changing the frame)"""
    # Compare frames pixel-by-pixel
    # Increment consecutive_no_change_count if unchanged
    # Reset to 0 if frame changed
```

### 3. Smart Target Selection

Enhanced `select_best_target()` to:
1. **Filter out clicked coordinates** - Prefer unclicked targets
2. **Reset when exhausted** - Clear clicked set after 10+ no-changes
3. **Cycle through targets** - Try all available before repeating

```python
# Filter out already-clicked coordinates
unclicked_targets = [
    t for t in targets 
    if (t["x"], t["y"]) not in self.clicked_coordinates
]

# Reset if stuck
if self.consecutive_no_change_count > 10:
    self.reset_clicked_coordinates()
```

### 4. Integration with Action Handler

Modified `action_handler.py` to mark coordinates as clicked:
```python
x, y, reason = target
self.visual_analyzer.mark_coordinate_clicked(x, y)
logger.info(f"ACTION6 target found: ({x}, {y}) - {reason}")
```

### 5. Frame Change Tracking After Actions

Modified `core_gameplay.py` to track frame changes:
```python
new_state = await self.action_handler.send_action_6(x, y, game_state.frame)

# Track frame changes
if new_state and new_state.frame:
    frame_changed = self.visual_analyzer.update_frame_change_tracking(new_state.frame)
```

## Results

### Before (Coordinate Spam):
```
ACTION6 at (31, 0): Rare color 14 (64 pixels)
ACTION6 at (31, 0): Rare color 14 (64 pixels)
ACTION6 at (31, 0): Rare color 14 (64 pixels)
ACTION6 at (31, 0): Rare color 14 (64 pixels)
[repeated 100+ times]
```

### After (Diverse Targets):
```
ACTION6 at (21, 61): Rare color 9 (16 pixels)
ACTION6 at (33, 32): Rare color 11 (123 pixels)
ACTION6 at (29, 61): Rare color 8 (16 pixels)
ACTION6 at (32, 30): Rare color 11 (122 pixels)
ACTION6 at (24, 49): Cluster of 1199 pixels (color=0)
ACTION6 at (25, 41): Rare color 5 (160 pixels)
ACTION6 at (32, 34): Rare color 11 (116 pixels)
ACTION6 at (19, 20): Rare color 8 (47 pixels)
ACTION6 at (39, 45): Rare color 11 (81 pixels)

[After trying all targets]
INFO - All targets clicked and no frame changes - resetting clicked coordinates

[Cycle repeats with fresh targets]
```

## Key Features

1. **✅ Coordinate Diversity** - Tries multiple different targets
2. **✅ Frame Change Detection** - Knows when actions are productive
3. **✅ Intelligent Reset** - Clears clicked set when exhausted
4. **✅ Target Type Variety** - Rare colors, clusters, changed regions
5. **✅ Prevents Spam** - Won't click same coordinate repeatedly
6. **✅ Adaptive Behavior** - Responds to frame changes

## Statistics Tracking

The system now tracks:
- `clicked_coordinates`: Set of (x, y) tuples already tried
- `consecutive_no_change_count`: How many actions without frame change
- `last_action_changed_frame`: Boolean indicator of productivity

## Configuration

Default reset threshold: **10 consecutive no-changes**

This can be adjusted in `visual_analyzer.py`:
```python
if self.consecutive_no_change_count > 10:  # Adjust this number
    self.reset_clicked_coordinates()
```

## Testing Results

Game showing proper diversity:
- **9+ different coordinates** tried in sequence
- **Multiple target types**: Rare colors 5, 8, 9, 11, 14 and clusters
- **Smart reset**: "All targets clicked" message at appropriate times
- **No coordinate spam**: Each target tried once before repeating

## Files Modified

1. **visual_analyzer.py**
   - Added `clicked_coordinates` tracking
   - Added `update_frame_change_tracking()`
   - Added `mark_coordinate_clicked()`
   - Added `reset_clicked_coordinates()`
   - Enhanced `select_best_target()` with filtering

2. **action_handler.py**
   - Integrated coordinate marking in `get_smart_coordinates()`
   - Marks coordinates as clicked after selection

3. **core_gameplay.py**
   - Added frame change tracking after ACTION6
   - Logs when frames don't change

## Next Steps

With coordinate diversity working, the system is ready for:

1. **Action Diversity** - Apply same logic to ACTION1-5, 7
2. **Frame Change Analysis** - Use frame changes to guide strategy
3. **Productive Action Prioritization** - Favor actions that change frames
4. **Ouroboros Evolution** - Evolve agents that make productive moves

## Conclusion

The ACTION6 coordinate diversity system is now working perfectly. The system:
- ✅ Tries multiple different targets
- ✅ Detects frame changes
- ✅ Resets intelligently when exhausted
- ✅ Prevents coordinate spam
- ✅ Explores the full frame space

Ready for integration with the Ouroboros evolution system!
