"""Check Arcade API and game flow."""
import sys


def log(msg):
    print(msg, flush=True)

log("Starting...")
from arc_agi import Arcade, OperationMode
from arcengine import GameAction, GameState

log("Imports done")

arcade = Arcade(operation_mode=OperationMode.OFFLINE)
log("Arcade created")

# Check available games
log("=== Available Games ===")
games = arcade.get_environments()
log(f"Games: {games}")

# Create an environment
print("\n=== Testing ls20 ===")
env = arcade.make("ls20")
print(f"Env type: {type(env)}")
print(f"Env methods: {[m for m in dir(env) if not m.startswith('_')]}")

# Check observation_space
print(f"\nObservation space type: {type(env.observation_space)}")
print(f"Observation space: {env.observation_space}")
print(f"Action space: {env.action_space}")

# Initial state - look at frame
log("\n=== Look at Frame Structure ===")
obs = env.step(GameAction.ACTION1)
log(f"Frame type: {type(obs.frame)}")
if obs.frame:
    log(f"Frame length: {len(obs.frame)}")
    if len(obs.frame) > 0:
        log(f"First row type: {type(obs.frame[0])}")
        log(f"First row length: {len(obs.frame[0]) if hasattr(obs.frame[0], '__len__') else 'N/A'}")
        log(f"First few rows: {obs.frame[:3]}")

# Try playing a bunch more actions to see if we can complete a level
log("\n=== Extended Gameplay ===")
level_0_count = 0
for i in range(200):
    # Simple exploration strategy - try each direction
    action_cycle = [GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4]
    action = action_cycle[i % 4]
    obs = env.step(action)

    if obs.levels_completed > 0:
        log(f"  Level completed at step {i+1}! Levels: {obs.levels_completed}")
        level_0_count = 0
        break

    if i % 50 == 0:
        log(f"  Step {i}: still on level 0")

    if obs.state in (GameState.WIN, GameState.GAME_OVER):
        log(f"  Game ended at step {i+1}: {obs.state}")
        break

log(f"Final state: levels={obs.levels_completed}, state={obs.state}")
