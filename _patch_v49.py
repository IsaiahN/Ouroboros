"""
v49: fix competition mode replay bug.
In competition mode with a replay sequence:
- If replay gets full score (1.0) -> break (correct)
- If replay gets partial score (0 < score < 1.0) -> break and keep partial score
  (can't call make() again in competition)
- If replay fails (score=0) -> fall through to cognitive play in same attempt
  (was: continue to attempt=2 where make() returns None, skipping cognitive play)
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

OLD = (
    '            # First attempt: try replay from known winning sequences\n'
    '            if attempt == 1 and accumulated.get("winning_sequences"):\n'
    '                score, levels, acts = _replay_sequences(\n'
    '                    env, accumulated["winning_sequences"], win_levels, False)\n'
    '                if score > best_score:\n'
    '                    best_score, best_levels, best_actions = score, levels, acts\n'
    '                if verbose:\n'
    '                    print(f"  [{game_id}] A1 Replay: {levels}/{win_levels} score={score:.3f}")\n'
    '                if score >= 1.0:\n'
    '                    break\n'
    '                continue\n'
)
NEW = (
    '            # First attempt: try replay from known winning sequences\n'
    '            if attempt == 1 and accumulated.get("winning_sequences"):\n'
    '                score, levels, acts = _replay_sequences(\n'
    '                    env, accumulated["winning_sequences"], win_levels, False)\n'
    '                if score > best_score:\n'
    '                    best_score, best_levels, best_actions = score, levels, acts\n'
    '                if verbose:\n'
    '                    print(f"  [{game_id}] A1 Replay: {levels}/{win_levels} score={score:.3f}")\n'
    '                if score >= 1.0:\n'
    '                    break\n'
    '                # v49: competition mode — replay partial/fail handling\n'
    '                if competition_mode:\n'
    '                    if score > 0.0:\n'
    '                        # Partial replay success: keep score, stop here\n'
    '                        # (cannot call make() again in competition)\n'
    '                        break\n'
    '                    # score==0: fall through to cognitive play in same attempt\n'
    '                else:\n'
    '                    continue\n'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if "v49" in src:
        print(f"  Cell {i}: v49 already applied")
        continue
    if OLD in src:
        src = src.replace(OLD, NEW, 1)
        cell["source"] = [src]
        print(f"  Cell {i}: applied v49 replay-competition fix")

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
