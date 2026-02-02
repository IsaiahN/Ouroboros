"""Test online mode with API key."""
from dotenv import load_dotenv

load_dotenv()

import os

print(f"API Key from env: {os.environ.get('ARC_API_KEY', 'NOT SET')[:20]}...")

from arc_agi import Arcade, OperationMode
from arcengine import GameAction

# Create online arcade
arcade = Arcade(operation_mode=OperationMode.ONLINE)
print(f"Arcade API Key: {arcade.arc_api_key[:20] if arcade.arc_api_key else 'NONE'}...")
print(f"Arcade Base URL: {arcade.arc_base_url}")
print(f"Operation Mode: {arcade.operation_mode}")

# Make environment
print("\nCreating ls20 environment...")
env = arcade.make("ls20")
print(f"Environment type: {type(env).__name__}")
print(f"Scorecard ID: {env.scorecard_id}")

# Take a few actions
print("\nTaking actions...")
for i in range(5):
    obs = env.step(GameAction.ACTION1)
    print(f"  Step {i+1}: state={obs.state}, levels={obs.levels_completed}")

print(f"\nFinal scorecard ID: {env.scorecard_id}")
print("Check https://three.arcprize.org to see if this scorecard appears!")
