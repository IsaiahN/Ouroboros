> ## Documentation Index
> Fetch the complete documentation index at: https://docs.arcprize.org/llms.txt
> Use this file to discover all available pages before exploring further.

# Get Scorecard

> How to retrieve scorecard results using the ARC-AGI Toolkit

## Overview

After playing games, you can retrieve your scorecard to see aggregated performance results. The Toolkit automatically manages a default scorecard, or you can create and manage your own.

## Getting the Default Scorecard

The Toolkit automatically creates a scorecard when you start playing. Retrieve it with `get_scorecard()`:

```python  theme={null}
import arc_agi
from arcengine import GameAction

arc = arc_agi.Arcade()
env = arc.make("ls20", render_mode="terminal")

# Play the game
env.step(GameAction.ACTION1)

# Get your scorecard
scorecard = arc.get_scorecard()
if scorecard:
    print(f"Score: {scorecard.score}")
    print(f"Games played: {len(scorecard.games)}")
```

## Scorecard Properties

The scorecard contains your aggregated results:

```python  theme={null}
scorecard = arc.get_scorecard()

if scorecard:
    print(f"Score: {scorecard.score}")
    print(f"Games: {scorecard.games}")
```

## See Full Scorecard

To view the complete scorecard with all fields, use `model_dump_json()`:

```python  theme={null}
scorecard = arc.get_scorecard()

if scorecard:
    print(scorecard.model_dump_json(indent=2))
```

## Next Steps

* [Create Scorecard](/toolkit/create-scorecard) — Create a custom scorecard with tags
* [Close Scorecard](/toolkit/close-scorecard) — Finalize and close a scorecard
* [Learn about scoring methodology](/methodology)
