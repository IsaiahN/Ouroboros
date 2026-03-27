"""
v45 patch: tag-based game-type detection
- Pure click games (tags=['click']): force cursor_mode=True from start
- keyboard_click games that probe as all-fire: cursor_mode instead of CSAT toggle
"""

import json
import sys

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

# ---- Patch 1: After _game_type_hint = _frame_hint["game_type"], add tag-based override ----
OLD1 = '    _game_type_hint = _frame_hint["game_type"]\n'
NEW1 = (
    '    _game_type_hint = _frame_hint["game_type"]\n'
    '\n'
    '    # Tag-based initial mode override (v45): use game metadata tags\n'
    '    _game_tags = list((knowledge or {}).get("_tags", []))\n'
    '    if "click" in _game_tags and "keyboard" not in _game_tags:\n'
    '        # Pure click game — cursor scan only, no navigation\n'
    '        _game_type_hint = "cursor"\n'
    '        loop._cursor_mode = True\n'
    '        if verbose:\n'
    '            print(f"    [{game_id}] tags={_game_tags}: pure-click -> cursor_mode=True (v45)")\n'
)

# ---- Patch 2: cursor_scan_done init — respect tag-based cursor_mode ----
OLD2 = '    _cursor_scan_done = (not _frame_hint["cursor_mode"])  # skip scan for non-cursor games\n'
NEW2 = '    _cursor_scan_done = not getattr(loop, "_cursor_mode", False)  # v45: respects tag-based cursor_mode\n'

# ---- Patch 3: probe-classify toggle branch — check keyboard_click tag ----
OLD3 = (
    '            elif _hit_acts and len(_hit_acts) == len(_eff_avail):\n'
    '                # All actions change frames equally -> toggle/universal\n'
    '                _game_type_hint = "toggle"\n'
    '                if verbose:\n'
    '                    print(f"    [{game_id}] probe-classify: TOGGLE confirmed from evidence")\n'
)
NEW3 = (
    '            elif _hit_acts and len(_hit_acts) == len(_eff_avail):\n'
    '                # All actions change frames equally\n'
    '                if "keyboard_click" in _game_tags:\n'
    '                    # keyboard+click game: use cursor scan instead of CSAT toggle (v45)\n'
    '                    loop._cursor_mode = True\n'
    '                    _game_type_hint = "movement_interact"\n'
    '                    _cursor_scan_done = False\n'
    '                    _cursor_scan_idx = 0\n'
    '                    if verbose:\n'
    '                        print(f"    [{game_id}] probe-classify: keyboard_click all-fire -> cursor_mode=True (v45)")\n'
    '                else:\n'
    '                    _game_type_hint = "toggle"\n'
    '                    if verbose:\n'
    '                        print(f"    [{game_id}] probe-classify: TOGGLE confirmed from evidence")\n'
)

patches = [
    ("Patch1: tag-based initial cursor_mode", OLD1, NEW1),
    ("Patch2: cursor_scan_done respects tag cursor_mode", OLD2, NEW2),
    ("Patch3: probe-classify keyboard_click all-fire -> cursor", OLD3, NEW3),
]

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    changed = False
    for name, old, new in patches:
        if old in src:
            src = src.replace(old, new, 1)
            print(f"  Cell {i}: applied {name}")
            changed = True
        elif new.split("\n")[0] in src:
            print(f"  Cell {i}: {name} already applied, skipping")
    if changed:
        cell["source"] = [src]

with open(NB, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Done.")
