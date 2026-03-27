"""
v48: fix toggle-classification for keyboard games without ACTION6.
g50t has actions=[1,2,3,4,5] — all fire in probe → falls into toggle branch
because ACTION5 is excluded from the movement check (range(1,5) = [1,2,3,4]).
Add guard: toggle requires ACTION6 (click) to be present. Otherwise → movement.
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

OLD = (
    '            elif _hit_acts and len(_hit_acts) == len(_eff_avail):\n'
    '                # All actions change frames equally\n'
    '                if "keyboard_click" in _game_tags:\n'
)
NEW = (
    '            elif _hit_acts and len(_hit_acts) == len(_eff_avail):\n'
    '                # All actions change frames equally\n'
    '                # v48: toggle requires ACTION6 (click) — keyboard-only games\n'
    '                # with all actions firing are movement games, not toggle.\n'
    '                if 6 not in _hit_acts and "keyboard_click" not in _game_tags:\n'
    '                    # No click action: must be movement (e.g. g50t ACTION1-5 all fire)\n'
    '                    _game_type_hint = "movement"\n'
    '                    if verbose:\n'
    '                        print(f"    [{game_id}] probe-classify: all-fire no-click -> MOVEMENT (v48)")\n'
    '                elif "keyboard_click" in _game_tags:\n'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if "v48" in src:
        print(f"  Cell {i}: v48 already applied")
        continue
    if OLD in src:
        src = src.replace(OLD, NEW, 1)
        cell["source"] = [src]
        print(f"  Cell {i}: applied v48 toggle guard")

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
