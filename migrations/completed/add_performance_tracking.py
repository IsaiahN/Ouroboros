"""
Add agent performance tracking to core_gameplay.py.
This script inserts performance tracking logic after game completion.
"""

import re

FILE_PATH = "core_gameplay.py"

# Read the file
with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Find the location after game results are calculated in play_single_game
# We want to add tracking right after the results dict is created
# Pattern: after results dict creation and before diversity tracking

pattern = r"(results = \{[^}]+\})\s+# Diversity Mode: Track game diversity"

# Replacement: add performance tracking before diversity tracking
replacement = r"""\1

            # TASK #6: Agent Self-Model - Track performance metrics
            if agent_id:
                self._track_agent_performance(
                    agent_id=agent_id,
                    game_id=game_id,
                    final_score=game_state.score,
                    actions_taken=action_count,
                    level_completions=level_completions,
                    win=(game_state.state == "WIN"),
                    duration_seconds=duration
                )

            # Diversity Mode: Track game diversity"""

# Apply the replacement
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content == content:
    print("ERROR: Pattern not found. Searching for alternative location...")
    # Try alternative pattern
    pattern2 = r"(# Diversity Mode: Track game diversity \(Rule 10: integrated, Rule 2: database-only\))"
    replacement2 = r"""# TASK #6: Agent Self-Model - Track performance metrics
            if agent_id:
                self._track_agent_performance(
                    agent_id=agent_id,
                    game_id=game_id,
                    final_score=game_state.score,
                    actions_taken=action_count,
                    level_completions=level_completions,
                    win=(game_state.state == "WIN"),
                    duration_seconds=duration
                )

            \1"""

    new_content = re.sub(pattern2, replacement2, content)

    if new_content == content:
        print("ERROR: Could not find insertion point for performance tracking")
        exit(1)

# Write the modified content
with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(new_content)

print("[OK] Successfully added performance tracking call to play_single_game")
