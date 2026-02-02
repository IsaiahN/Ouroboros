# ACTION6 Reference Guide

## What ACTION6 Is

ACTION6 is a **parameterized coordinate-based action**. Unlike ACTION1-5 (simple directional commands), ACTION6 requires explicit x,y coordinates.

**Think of the grid as a touchscreen.** `ACTION6(x, y)` means "touch/select the pixel at (x, y)".

---

## API Format

```python
import requests

url = "https://three.arcprize.org/api/cmd/ACTION6"

payload = {
    "game_id": "CURRENT_GAME_ID",
    "guid": "CURRENT_GUID",
    "x": X_COORDINATE,  # Integer 0-63
    "y": Y_COORDINATE   # Integer 0-63
}
headers = {
    "X-API-Key": "YOUR_API_KEY",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
```

**Response includes:**
```json
{
  "action_input": {
    "id": 6,
    "data": {
      "x": 12,
      "y": 34
    }
  }
}
```

---

## Coordinate System

```
(0,0) ─────────────────── (63,0)
  │                          │
  │      64x64 GRID          │
  │                          │
  │     Y increases ↓        │
  │     X increases →        │
  │                          │
(0,63) ─────────────────── (63,63)
```

- **Top-left**: (0, 0)
- **Top-right**: (63, 0)
- **Bottom-left**: (0, 63)
- **Bottom-right**: (63, 63)
- **Moving down** = Y increases
- **Moving right** = X increases

---

## Key Rules

1. **Always include coordinates** - Never send ACTION6 without x,y
2. **Bounds: 0-63** - Any value outside this range will fail
3. **Check availability** - Only use when `6` is in `available_actions`
4. **Prefer simpler actions first** - Use ACTION1-5 when available

---

## ACTION6 is NOT Just Movement

**Critical insight**: ACTION6 is a **universal targeting/interaction system**, not just "move to (x,y)".

The effect depends entirely on what is at that location:
- Click a button → triggers something
- Click an object → selects/interacts with it
- Click empty space → may move there (game-dependent)
- Click a portal → teleports you

---

## Decision Logic

```python
# Pseudocode for ACTION6 usage

# 1. PREFER simpler actions when available
if 6 not in available_actions:
    return  # Don't use ACTION6

if any(a in available_actions for a in [1, 2, 3, 4, 5, 7]):
    # Try these first - more predictable
    use_simple_action()
    return

# 2. If ACTION6 is best/only option, ANALYZE the frame
targets = find_interesting_regions(frame)

if targets:
    # Click on something meaningful
    x, y = select_best_target(targets)
    execute_action6(x, y)
else:
    # Exploratory tap - try nearby area
    x = clamp(current_x + random(-5, 5), 0, 63)
    y = clamp(current_y + random(-5, 5), 0, 63)
    execute_action6(x, y)
```

---

## What to Target

Look for in the frame:
1. **Unique colors** - Objects that stand out from background
2. **High contrast regions** - Bright/dark spots
3. **Geometric shapes** - Buttons, portals, interactive elements
4. **Things that changed** - Compare to previous frame

---

## Boundary Handling

```python
def safe_coordinate(value):
    return max(0, min(63, value))

# Before sending ACTION6:
x = safe_coordinate(target_x)
y = safe_coordinate(target_y)
```

---

## Summary

| Aspect | Details |
|--------|---------|
| Format | `ACTION6` with `x` and `y` in payload |
| Range | 0-63 for both coordinates |
| Purpose | Target/interact with specific grid location |
| Priority | Use after trying ACTION1-5 first |
| Strategy | Analyze frame visually, click meaningful targets |
