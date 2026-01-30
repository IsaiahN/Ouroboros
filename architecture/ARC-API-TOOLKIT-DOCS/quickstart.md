> ## Documentation Index
> Fetch the complete documentation index at: https://docs.arcprize.org/llms.txt
> Use this file to discover all available pages before exploring further.

# ARC-AGI Toolkit Quickstart

> Getting started with the ARC-AGI Toolkit

The ARC-AGI Toolkit is an open-source Python SDK for ARC-AGI-3 environments, geared towards researchers looking to make progress on ARC-AGI-3.

The Toolkit enables:

* **Local development** — Run your agents locally without needing the API, built on top of the [ARC-AGI-3 game engine](https://github.com/arcprize/ARCEngine)
* **Customization** — Edit existing games and create new ones
* **Flexibility** — Interact with environments locally or via API

## QuickStart

### 1. Install the Toolkit

```bash  theme={null}
uv add arc-agi
# or
pip install arc-agi
```

### 2. Set your API key (optional)

```bash  theme={null}
export ARC_API_KEY="your-api-key-here"
```

If no key is provided, an anonymous key will be used. See [API Keys](/api-keys) for more details.

### 3. Play a game

```python  theme={null}
import arc_agi
from arcengine import GameAction

arc = arc_agi.Arcade()
env = arc.make("ls20", render_mode="terminal")

# See available actions
print(env.action_space)

# Take an action
obs = env.step(GameAction.ACTION1)

# Check your scorecard
print(arc.get_scorecard())
```

## Next Steps

* [Minimal Example](./minimal) — A complete script example
* [List Games](./list-games) — Discover available games
* [Local vs Online](/local-vs-online) — Choose how to run games
