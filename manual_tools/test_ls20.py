"""Quick test of ls20 game."""
from arc_agi import Arcade, GameAction, OperationMode

arcade = Arcade(operation_mode=OperationMode.OFFLINE)
env = arcade.get_game("ls20")
obs = env.reset()

print("=== LS20 GAME ANALYSIS ===")
print(f"Observation type: {type(obs)}")
print(f"Observation keys: {obs.keys() if hasattr(obs, 'keys') else 'N/A'}")

if hasattr(obs, 'keys'):
    for key in obs.keys():
        val = obs[key]
        if isinstance(val, list):
            print(f"  {key}: list of {len(val)} items")
            if val and isinstance(val[0], list):
                print(f"    First row sample: {val[0][:10]}...")
        else:
            print(f"  {key}: {val}")

print("\n=== TAKE SOME ACTIONS ===")
actions = [GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4]
for i, action in enumerate(actions):
    obs, reward, done, info = env.step(action)
    print(f"Step {i+1} ({action.name}): reward={reward}, done={done}, info keys={info.keys() if hasattr(info, 'keys') else info}")
    if reward > 0:
        print(f"  GOT REWARD!")
    if done:
        print(f"  GAME OVER")
        break

print("\n=== CURRENT STATE ===")
if hasattr(obs, 'keys'):
    if 'score' in obs:
        print(f"Score: {obs['score']}")
    if 'level' in obs:
        print(f"Level: {obs['level']}")
