"""Update the notebook's opening markdown cell with clean room engineering description."""
import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

NEW_README = (
    "# BitterTruth-AI -- ARC-AGI-3 Competition Submission\n"
    "\n"
    "**Architecture**: Solver-free cognitive pipeline --"
    " OBSERVE > CLASSIFY > EXTRACT_GOAL > MAP_EFFECTS > PLAN > EXECUTE > VERIFY\n"
    "\n"
    "**Key innovations**:\n"
    "- H53: Win-state goal templates (learn goals from prior sessions)\n"
    "- H55: Self-toggle rule extrapolation (plan without visiting every cell)\n"
    "- H56: Rule-based strategy unlock (escape explore-forever deadlock)\n"
    "- H51: Autonomous spatial navigation + dead reckoning for movement games\n"
    "- H47: Score-correlated goal discovery\n"
    "\n"
    "**No solver data required** -- the system discovers mechanics autonomously.\n"
    "\n"
    "---\n"
    "\n"
    "## Development Methodology: Clean Room Engineering\n"
    "\n"
    "This system was built using a clean room engineering process applied to game cognition.\n"
    "\n"
    "**Phase 1 -- Intelligence Gathering**: Each of the 25 public competition games is"
    " observed and played to understand its mechanics at the pixel/reward level."
    " Win conditions, productive actions, and progress signals are documented purely"
    " observationally -- no game documentation consulted.\n"
    "\n"
    "**Phase 2 -- Solver Development**: For each game, a minimal solver is built by any"
    " means necessary (constraint satisfaction, BFS, brute force, computer vision) to"
    " reliably produce winning sequences. The solver is permitted to use game-specific"
    " knowledge at this stage.\n"
    "\n"
    "**Phase 3 -- Principle Extraction (the clean room step)**: Each solver is"
    " deconstructed into an abstract cognitive principle. The game-specific knowledge is"
    " discarded; only the principle survives. Example: a lights-out solver becomes"
    " *identify toggleable regions; find minimum action set that drives collective state"
    " to target configuration*. A rail-switch solver becomes *detect that actions cause"
    " local state change; learn which action affects which region; chain changes to reach"
    " target layout*.\n"
    "\n"
    "**Phase 4 -- Cognitive Primitive Synthesis**: Each abstract principle is implemented"
    " as a game-agnostic module. Modules activate on observation signals (pixel change"
    " patterns, score deltas, action effect maps) -- never on game ID or hardcoded"
    " mechanics. The expected primitive set: change detection, state cycling, goal"
    " detection, spatial navigation, object identity, causal attribution, constraint"
    " propagation, sequence memory.\n"
    "\n"
    "**Phase 5 -- Integration**: The unified system plays all games through the same code"
    " path. It never branches on game identity. The same cognitive pipeline that solves a"
    " lights-out puzzle solves a rail-switching puzzle and a maze challenge -- because the"
    " underlying operations (detect state change, find causal action, plan to goal) are"
    " universal.\n"
    "\n"
    "The result is a system that can be dropped into any unknown game and reason about it"
    " the way a human would on first play: observe, hypothesize, test, learn, plan."
)

assert nb["cells"][0]["cell_type"] == "markdown", "Cell 0 is not markdown"
nb["cells"][0]["source"] = [NEW_README]

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
