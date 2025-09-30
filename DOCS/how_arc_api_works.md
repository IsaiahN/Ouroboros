### HOW ARC 3 AGI API WORKS - PLEASE READ
Agents

# Agents Quickstart

> Swarms are used to orchestrate multiple agents across multiple games simultaneously.

Create AI agents that can play ARC-AGI-3 games by implementing the required interface methods. The following is based off the [ARC-AGI-3 Agents repo](https://github.com/arcprize/ARC-AGI-3-Agents).

## Adding and Running Your Own Agent

Follow these three steps to create and run a new agent.

### Step 1: Create Your Agent File

First, head over to the [ARC-AGI-3-Agents](https://github.com/arcprize/ARC-AGI-3-Agents) repo and clone it

```bash
git clone https://github.com/arcprize/ARC-AGI-3-Agents.git
```

Make sure you have your ARC-AGI-API-KEY populated in your environment variables. You can obtain this key by signing up for an account on the [ARC-AGI-3 website](https://three.arcprize.org).

Next, create a new Python file for your agent inside the `agents/` directory. For this example, let's copy the `random_agent.py` template.

```bash
cp agents/templates/random_agent.py agents/my_awesome_agent.py
```

Now, modify `agents/my_awesome_agent.py` and rename the class to `MyAwesomeAgent`.

```python
# agents/my_awesome_agent.py

from .agent import Agent # Make sure to change from `..` imports
from .structs import FrameData, GameAction, GameState # Make sure to change from `..` imports
import random

# Rename the class
class MyAwesomeAgent(Agent):
    """A simple agent that chooses random actions."""
    
    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        # Your logic to determine if the game is finished
        return latest_frame.state is GameState.WIN

    def choose_action(self, frames: list[FrameData], latest_frame: FrameData) -> GameAction:
        # Your custom decision-making logic goes here
        if latest_frame.state in [GameState.NOT_PLAYED, GameState.GAME_OVER]:
            # Start or restart the game
            action = GameAction.RESET
        else:
            # Choose a random action (except RESET)
            action = random.choice([a for a in GameAction if a is not GameAction.RESET])
        
        # Add reasoning for simple actions
        if action.is_simple():
            action.reasoning = f"Chose {action.value} randomly"
        # For complex actions, set coordinates
        elif action.is_complex():
            action.set_data({
                "x": random.randint(0, 63),
                "y": random.randint(0, 63),
            })
            action.reasoning = {"action": action.value, "reason": "Random choice"}
        
        return action
```

### Step 2: Ensure Your Agent is Automatically Registered

To make your agent available to run, add an import statement to `agents/__init__.py` and add it to the `AVAILABLE_AGENTS` dictionary:

```python
# agents/__init__.py
# ... existing imports ...
from .my_awesome_agent import MyAwesomeAgent

__all__ = [
    # ... existing agents ...
    "MyAwesomeAgent",
    "AVAILABLE_AGENTS",
]
```

### Step 3: Run Your Agent

Your agent is now registered and ready to run. Use the class name in lower case as the value for the `--agent` argument.

```bash
# Run your custom agent on the 'ls20' game
uv run main.py --agent=myawesomeagent --game=ls20
```

You can also run it against all available games:

```bash
# Run your agent on all games
uv run main.py --agent=myawesomeagent
```

That's it! The `main.py` script handles looking up your agent in the registry, instantiating it, and running it against the specified games.

The [replay](/recordings) of your agent is available at the end of the run. Make sure to watch your agent at play.

***

## Troubleshooting

### Relative Import Errors

If you move an agent file or create a new one outside the `agents/` directory, you may encounter `ImportError` exceptions related to relative imports.

**Solution:**
Ensure your import statements use the correct relative pathing. The `..` prefix goes up one directory level.

For example, if your agent is in `agents/my_agents/my_file.py`, the imports should look like this:

```python
# agents/my_agents/my_file.py

# Correct: Go up one level to the 'agents' package root
from ..agent import Agent
from ..structs import FrameData

# Incorrect: Assumes the file is in the 'agents' root
# from .agent import Agent 
```

### Agent Not Found Errors

If you see `ValueError: Agent '<your-agent>' not found`, double-check the following:

1. Your agent class is correctly located in the `agents` directory (or a subdirectory).
2. The class name is correctly spelled and matches the name you provided to the `--agent` flag (in lower case).
3. You have saved your changes to your agent file.


ARC-AGI-3 Quickstart
# ARC-AGI-3 Quickstart

> ARC-AGI-3 is an Interactive Reasoning Benchmark designed to measure an AI Agent's ability to generalize in novel, unseen environments.

<div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
  {/* ───────── Left column ───────── */}

  <div style={{ flex: 1 }}>
    <p>
      Traditionally, to measure AI, static benchmarks have been the yardstick.
      These continue to work well for evaluating things like LLMs and AI
      reasoning systems. However, to evaluate frontier AI agent systems, we
      need new tools that measure:
    </p>

    <ul>
      <li>Exploration</li>
      <li>Percept → Plan → Action</li>
      <li>Memory</li>
      <li>Goal Acquisition</li>
      <li>Alignment</li>
    </ul>

    <p>
      By building agents that can play ARC-AGI-3, you're directly contributing
      to the frontier of AI research. Watch the{' '}

      <a href="https://www.youtube.com/watch?v=xEVg9dcJMkw">
        Quick Start tutorial video
      </a>

      . Learn more about{' '}
      <a href="https://three.arcprize.org/">ARC-AGI-3</a>.
    </p>
  </div>

  {/* ───────── Right column ───────── */}

  <div style={{ flex: 1, textAlign: 'center' }}>
    <img src="https://mintlify.s3.us-west-1.amazonaws.com/arcprizefoundation/images/Ls20Human.gif" alt="Human playing LS20" />

    <p>
      Can you build an agent to beat{' '}
      <a href="https://three.arcprize.org/games/ls20">this game</a>?
    </p>
  </div>
</div>

## Run your first agent against ARC-AGI-3

### 1. Install [uv](https://docs.astral.sh/uv/)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and install the [ARC-AGI-3-Agents Repo](https://github.com/arcprize/ARC-AGI-3-Agents)

```bash
git clone https://github.com/arcprize/ARC-AGI-3-Agents.git && cd ARC-AGI-3-Agents && uv sync
```

### 3. Set up environment variables

```bash
cp .env-example .env
```

You will need to set the `ARC_API_KEY` in the `.env` file. You can get your ARC\_API\_KEY from your user profile after registration on the [ARC-AGI-3 website](https://three.arcprize.org).

### 4. Run your first agent

```bash
# Run 'random' agent against 'ls20' game
uv run main.py --agent=random --game=ls20
```

🎉 **Congratulations!** You just ran your first agent against ARC-AGI-3. A link to view your agent's replay ([example replay](https://three.arcprize.org/replay/ls20-016295f7601e/493202a6-81dc-4e75-bc51-f21174b28b29)) is provided in the output.

## Next Steps

After running your first agent:

1. **Explore your agent's scorecard** - View your scorecard (ex: `https://three.arcprize.org/scorecards/<scorecard_id>`)
2. **Explore a game's replay** - Via your scorecard, view the per-game replays of your agent (ex: `https://three.arcprize.org/replay/ls20-016295f7601e/794795bf-d05f-4bf5-885a-b8a8f37a89fd`)
3. **Try a different game** - Run `uv run main.py --agent=random --game=<>` See a list of games available at three.arcprize.org or via [api](/api-reference/games/list-available-games)
4. **Try using a LLM** - Try `uv run main.py --agent=llm --game=ls20` (requires an `OPENAI_API_KEY` in `.env`) or explore other [templates](/partner_templates/langchain).
5. **Build your own agent** - Follow the [Agents Quickstart](./agents-quickstart) guide and [view the agent tutorial](https://www.youtube.com/watch?v=xEVg9dcJMkw).

Swarms
# Swarms

> Orchestrate agents across multiple games.

Swarms are used to orchestrate your agent across multiple games simultaneously.

Each `swarm`:

* Creates one agent instance per [game](/games)
* Runs all agents concurrently using threads
* Automatically manages [scorecard](/scorecards) opening and closing
* Handles cleanup when all agents complete
* Provides a link to view [replay](/recordings) online

### Running the Agent Swarm

The agent swarm is executed through `main.py`, which manages agent execution across multiple games with automatic scorecard tracking.

### Swarm Command

```bash
uv run main.py --agent <agent_name> [--game <game_filter>] [--tags <tag_list>]
```

### CLI Arguments

| Argument  | Short | Required | Description                                                                                                                                                                                                                                |
| --------- | ----- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--agent` | `-a`  | Yes      | Choose which agent to run. Available agents can be found in the `agents/` directory.                                                                                                                                                       |
| `--game`  | `-g`  | No       | Filter [games](/games) by ID prefix. Can be comma-separated for multiple filters (e.g., `ls20,ft09`). If not specified, the agent plays all available games.                                                                               |
| `--tags`  | `-t`  | No       | Comma-separated list of tags for the scorecard (e.g., `experiment,v1.0`). Tags help categorize and track different agent runs. Helpful when you want to compare different agents. Tags will be recorded on your [scorecards](/scorecards). |

### Examples

```bash
# Run the random agent on all games
uv run main.py --agent=random

# Run an LLM agent on only the ls20 game
uv run main.py --agent=llm --game=ls20

# Run with custom tags for tracking
uv run main.py --agent=llm --tags="experiment,gpt-4,baseline"

# Run against an explicit list of games
uv run main.py --agent=random --game="ls20,ft09"
```
Games
# Games

> Hand crafted environments that test interactive abstraction and reasoning

ARC-AGI-3 games are turn-based systems where agents interact with 2D grid environments through a standardized action interface. Each game maintains state through discrete action-response cycles.

* Agents will receive a 1-N frames of JSON objects with the game state and metadata.
* Agents will respond with an [action](/actions) 1-5 or a 6th action which includes x, y coordinates.

### Available Games

To see which games are available, either go to [three.arcprize.org](https://three.arcprize.org) or make an API call to [list games](/api-reference/games/list-available-games).

Example games include

* [ls20](https://three.arcprize.org/games/ls20) - Agent reasoning
* [ft09](https://three.arcprize.org/games/ft09) - Elementary Logic
* [vc33](https://three.arcprize.org/games/vc33) - Orchestration

### Game ID

Game IDs are formatted as `<game_name>`-`<version>`.

`game_names` are stable, but `version` may change as games update.

### Grid Structure

* **Dimensions:** Maximum 64x64 grid size
* **Cell Values:** Integer values 0-15 representing different states/colors
* **Coordinate System:** (0,0) at top-left, (x,y) format

### Game Available Actions

Each game provides an explicit set of actions that an agent can take. Actions available vary per game.

Typically, the available actions include:

* Actions 1–4: ex: move up, down, left, or right
* Action 6: A complex action (if supported by the game)

To learn more about each action and what it does, please visit the [Actions](/actions).

## Running a Full Playtest

To run a complete playtest, you'll need to integrate your agent with scorecard management and the game loop. This is what happens "under the hood" when you run commands like `uv run main.py --agent=random --game=ls20` (from the [Quick Start](./quick-start.md)). Below is pseudocode for the key steps. For a ready-to-use implementation, see the [Swarms](./swarms.md) guide—which can automate this for you across multiple games.

## Game State Enumeration

| State          | Description                                                        |
| -------------- | ------------------------------------------------------------------ |
| `NOT_FINISHED` | Game is active and awaiting next action                            |
| `WIN`          | Objective completed successfully                                   |
| `GAME_OVER`    | Game terminated due to the max actions reached or other conditions |

## Full Playtest

This is a bare-bones example for (educational purposes) is also available as a [notebook](https://colab.research.google.com/drive/1Bt4PU6Xl_avLPV70hNAyReXaRqFDhifJ?usp=sharing).

```python
#!/usr/bin/env python3
"""
Simple demo showing what a swarm agent does under the hood.
This is a bare-bones example for educational purposes.
"""

import json
import os
import random
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env")

# Setup
ROOT_URL = "https://three.arcprize.org"
API_KEY = os.getenv("ARC_API_KEY")

# Create a session with headers
session = requests.Session()
session.headers.update({
    "X-API-Key": API_KEY,
    "Accept": "application/json"
})

print("=== MANUAL SWARM DEMO ===")
print("This shows what happens when an agent plays an ARC game.\n")

# Step 1: Get available games
print("STEP 1: Getting list of games...")
response = session.get(f"{ROOT_URL}/api/games")
games = [g["game_id"] for g in response.json()]
print(f"Found {len(games)} games")

# Pick a random game
game_id = random.choice(games)
print(f"Selected game: {game_id}\n")

# Step 2: Open a scorecard (tracks performance)
print("STEP 2: Opening scorecard...")
response = session.post(
    f"{ROOT_URL}/api/scorecard/open",
    json={"tags": ["manual_demo"]}
)
card_id = response.json()["card_id"]
print(f"Scorecard ID: {card_id}\n")

# Step 3: Start the game
print("STEP 3: Starting game with RESET action...")
url = f"{ROOT_URL}/api/cmd/RESET"
print(f"URL: {url}")
response = session.post(
    url,
    json={
        "game_id": game_id,
        "card_id": card_id
    }
)

# Check if response is valid
if response.status_code != 200:
    print(f"Error: {response.status_code} - {response.text}")
    exit()

game_data = response.json()
guid = game_data["guid"]
state = game_data["state"]
score = game_data.get("score", 0)
print(f"Game started! State: {state}, Score: {score}\n")

# Step 4: Play with random actions (max 5 actions)
print("STEP 4: Taking random actions...")
actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION6", "ACTION7"]

for i in range(5):
    # Check if game is over
    if state in ["WIN", "GAME_OVER"]:
        print(f"\nGame ended! Final state: {state}, Score: {score}")
        break
    
    # Pick a random action
    action = random.choice(actions)
    
    # Build request data
    request_data = {
        "game_id": game_id,
        "card_id": card_id,
        "guid": guid
    }
    
    # ACTION6 needs x,y coordinates
    if action == "ACTION6":
        request_data["x"] = random.randint(0, 29)
        request_data["y"] = random.randint(0, 29)
        print(f"Action {i+1}: {action} at ({request_data['x']}, {request_data['y']})", end="")
    else:
        print(f"Action {i+1}: {action}", end="")
    
    # Take the action
    response = session.post(
        f"{ROOT_URL}/api/cmd/{action}",
        json=request_data
    )
    
    game_data = response.json()
    state = game_data["state"]
    score = game_data.get("score", 0)
    print(f" -> State: {state}, Score: {score}")

# Step 5: Close scorecard
print("\nSTEP 5: Closing scorecard...")
response = session.post(
    f"{ROOT_URL}/api/scorecard/close",
    json={"card_id": card_id}
)
scorecard = response.json()
print("Scorecard closed!")
print(f"\nView results at: {ROOT_URL}/scorecards/{card_id}")

print("\n=== DEMO COMPLETE ===")
print("\nThis is what every agent does:")
print("1. Get games list")
print("2. Open a scorecard")
print("3. Reset to start the game")
print("4. Take actions based on its strategy (we used random)")
print("5. Close the scorecard when done")
print("\nThe real agents use smarter strategies instead of random!")
```

This workflow ensures your plays are tracked officially. For parallel playtests across games, use a [swarm](./swarms.md) to handle the orchestration automatically.

ScoreCards
# Scorecards

> Keeping track of agent performance

Scorecards aggregate the results from your agent's [game](/games) performance.

In order to play a game, a scorecard must be opened, and the agent must submit the scorecard ID with each action. Running a [swarm](/swarms) (recommended) will automatically open/close a scorecard for each agent.

Scorecards can be viewed online at [https://three.arcprize.org/scorecards](https://three.arcprize.org/scorecards) and [https://three.arcprize.org/scorecards/\`scorecard\_id\`](https://three.arcprize.org/scorecards/`scorecard_id`).

Scorecard fields

| Field       | Description                                                                                        |
| ----------- | -------------------------------------------------------------------------------------------------- |
| tags        | Array of strings used to categorize and filter scorecards (e.g., \["experiment1", "v2.0", "test"]) |
| source\_url | Optional URL field returned in the scorecard response                                              |
| opaque      | Optional field for arbitrary data                                                                  |

Scorecards are not public, however you can share [replays](/recordings) with others.

Other scorecard notes:

* Scorecards auto close after 15min
* Agent scorecards are automatically added to the leaderboard in batch every \~15min
* Stopping the program prematurely with Ctrl‑C mid‑run will not allow you to see the scorecard results.

ACtions
# Actions

> Your agent's interaction with the game

All games implement a standardized action interface with seven core actions:

| Action    | Description                                                                                   |
| --------- | --------------------------------------------------------------------------------------------- |
| `RESET`   | Initialize or restarts the game/level state                                                   |
| `ACTION1` | Simple action - varies by game (semantically mapped to up)                                    |
| `ACTION2` | Simple action - varies by game (semantically mapped to down)                                  |
| `ACTION3` | Simple action - varies by game (semantically mapped to left)                                  |
| `ACTION4` | Simple action - varies by game (semantically mapped to right)                                 |
| `ACTION5` | Simple action - varies by game (e.g., interact, select, rotate, attach/detach, execute, etc.) |
| `ACTION6` | Complex action requiring x,y coordinates (0-63 range)                                         |
| `ACTION7` | Simple action - Undo (e.g., interact, select)                                                 |

### Human Player Keybindings

When playing games manually in the ARC-AGI-3 UI, you can use these keyboard shortcuts instead of clicking action buttons:

| Control Scheme     | ACTION1 | ACTION2 | ACTION3 | ACTION4 | ACTION5 | ACTION6     | ACTION7    |
| ------------------ | ------- | ------- | ------- | ------- | ------- | ----------- | ---------- |
| **WASD + Space**   | `W`     | `S`     | `A`     | `D`     | `Space` | Mouse Click | CTRL/CMD+Z |
| **Arrow Keys + F** | `↑`     | `↓`     | `←`     | `→`     | `F`     | Mouse Click | CTRL/CMD+Z |

All control schemes support mouse clicking for ACTION6 (coordinate-based actions). Choose whichever scheme feels most comfortable for your playstyle.

### Available Actions

Each game explicitly defines the set of available actions that can be used within that game. This approach ensures clarity for both human and AI participants by making it clear which actions are permitted, thereby reducing confusion. In the human-facing UI, available actions are visually highlighted or dismissed to provide the same affordance.

For each action taken, the metadata of the returned frame will indicate which actions are available. Agents may use this information to narrow the action space and develop effective strategies for completing the game.

Note: Action 6 does not provide explicit X/Y coordinates for active areas. If Action 6 is available, only its availability will be indicated, without specifying which coordinates are active.

## open scorecard

import requests

url = "https://three.arcprize.org/api/scorecard/open"

payload = {}
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())

## close score card
import requests

url = "https://three.arcprize.org/api/scorecard/close"

payload = { "card_id": "8bb3b1b8-4b46-4a29-a13b-ad7850a0f916" }
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())

## New Game:

import requests

url = "https://three.arcprize.org/api/cmd/RESET"

payload = {
    "game_id": "ls20-016295f7601e",
    "card_id": "8bb3b1b8-4b46-4a29-a13b-ad7850a0f916"
}
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())


## level Reset
import requests

url = "https://three.arcprize.org/api/cmd/RESET"

payload = {
    "game_id": "ls20-016295f7601e",
    "card_id": "8bb3b1b8-4b46-4a29-a13b-ad7850a0f916",
    "guid": "2fa5332c-2e55-4825-b5c5-df960d504470"
}
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())

## ACTION 1

import requests

url = "https://three.arcprize.org/api/cmd/ACTION1"

payload = {
    "game_id": "ls20-016295f7601e",
    "guid": "2fa5332c-2e55-4825-b5c5-df960d504470",
    "reasoning": { "policy": "π_left" }
}
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())

## ACTION 2
import requests

url = "https://three.arcprize.org/api/cmd/ACTION2"

payload = {
    "game_id": "ls20-016295f7601e",
    "guid": "2fa5332c-2e55-4825-b5c5-df960d504470",
    "reasoning": { "policy": "π_left" }
}
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
## ACTION 3
import requests

url = "https://three.arcprize.org/api/cmd/ACTION3"

payload = {
    "game_id": "ls20-016295f7601e",
    "guid": "2fa5332c-2e55-4825-b5c5-df960d504470",
    "reasoning": { "policy": "π_left" }
}
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
## ACTION 4
import requests

url = "https://three.arcprize.org/api/cmd/ACTION4"

payload = {
    "game_id": "ls20-016295f7601e",
    "guid": "2fa5332c-2e55-4825-b5c5-df960d504470",
    "reasoning": { "policy": "π_left" }
}
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
## ACTION 5
import requests

url = "https://three.arcprize.org/api/cmd/ACTION5"

payload = {
    "game_id": "ls20-016295f7601e",
    "guid": "2fa5332c-2e55-4825-b5c5-df960d504470",
    "reasoning": { "policy": "π_left" }
}
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
## ACTION 6
import requests

url = "https://three.arcprize.org/api/cmd/ACTION6"

payload = {
    "game_id": "ls20-016295f7601e",
    "guid": "2fa5332c-2e55-4825-b5c5-df960d504470",
    "x": 12,
    "y": 34
}
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
## ACTION 7
import requests

url = "https://three.arcprize.org/api/cmd/ACTION7"

payload = {
    "game_id": "ls20-016295f7601e",
    "guid": "2fa5332c-2e55-4825-b5c5-df960d504470",
    "reasoning": { "policy": "π_left" }
}
headers = {
    "X-API-Key": "<api-key>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())



##ACTION RETURN TYPE:
##NOTICE THAT "available_actions" corresponds to the actions which are available. 1 = action1, 2 = action2 etc.
{
  "game_id": "ls20-016295f7601e",
  "guid": "2fa5332c-2e55-4825-b5c5-df960d504470",
  "frame": [
    [
      [
        0,
        0,
        1,
        "…"
      ],
      [
        "…"
      ]
    ]
  ],
  "state": "NOT_FINISHED",
  "score": 3,
  "win_score": 254,
  "action_input": {
    "id": 7
  },
  "available_actions": [
    1,
    2,
    3,
    4,
    7
  ]
}

# Rate Limits

> Limiting RPM for your agents

The ARC-AGI API is currently free to use during its research preview. To prevent abuse and ensure fair access, we have implemented rate limits with an exponential backoff mechanism.

These limits help maintain system stability by throttling excessive requests. If you encounter rate limiting, your requests will receive a backoff response, requiring you to wait increasingly longer periods before retrying.

Rate limits are set at 600 requests per minute (RPM).

## Requesting Limit Increases

We are open to discussing increases in rate limits, particularly for researchers and teams requiring higher throughput.

If you need elevated limits, please email us at [team@arcprize.org](mailto:team@arcprize.org) with the subject line "Increase Rate Limits" to initiate a conversation.

## Navigating Rate Limits

If you've managed to hit a rate limit, you'll see a standard `429` response.

```json
{"error":"RATE_LIMIT_EXCEEDED","message":"rate limit has been exceeded"}
```
