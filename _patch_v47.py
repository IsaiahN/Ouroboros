"""
v47: fix v45 pure-click check — only force cursor_mode when no movement actions available.
lf52 is tagged 'click' but has ACTION1-4 movement (physics sim). Don't force cursor_mode.
s5i5, r11l have only ACTION6 — correctly get cursor_mode=True.
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

OLD = (
    '    _game_tags = list((knowledge or {}).get("_tags", []))\n'
    '    if "click" in _game_tags and "keyboard" not in _game_tags:\n'
    '        # Pure click game \u2014 cursor scan only, no navigation\n'
    '        _game_type_hint = "cursor"\n'
    '        loop._cursor_mode = True\n'
    '        if verbose:\n'
    '            print(f"    [{game_id}] tags={_game_tags}: pure-click -> cursor_mode=True (v45)")\n'
)

NEW = (
    '    _game_tags = list((knowledge or {}).get("_tags", []))\n'
    '    # v47: only force cursor_mode if no movement actions (1-5) available.\n'
    '    # lf52 has click tag but also has ACTION1-4 (physics sim) -- do NOT force cursor.\n'
    '    _has_movement = bool(set(available_actions) & {1, 2, 3, 4, 5})\n'
    '    if "click" in _game_tags and "keyboard" not in _game_tags and not _has_movement:\n'
    '        # Pure click game (no movement keys) \u2014 cursor scan only\n'
    '        _game_type_hint = "cursor"\n'
    '        loop._cursor_mode = True\n'
    '        if verbose:\n'
    '            print(f"    [{game_id}] tags={_game_tags}: pure-click (no movement) -> cursor_mode=True (v45/v47)")\n'
)

# Also need to handle the ASCII-only version (em dash -> unicode escape)
OLD_ASCII = (
    '    _game_tags = list((knowledge or {}).get("_tags", []))\n'
    '    if "click" in _game_tags and "keyboard" not in _game_tags:\n'
    '        # Pure click game \u2014 cursor scan only, no navigation\n'
    '        _game_type_hint = "cursor"\n'
    '        loop._cursor_mode = True\n'
    '        if verbose:\n'
    '            print(f"    [{game_id}] tags={_game_tags}: pure-click -> cursor_mode=True (v45)")\n'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if "v47" in src:
        print(f"  Cell {i}: v47 already applied")
        continue
    replaced = False
    for old_str in [OLD, OLD_ASCII]:
        if old_str in src:
            src = src.replace(old_str, NEW, 1)
            replaced = True
            break
    # Also try JSON-escaped em dash version
    if not replaced:
        OLD_JSON = OLD.replace("\u2014", "\\u2014")
        if OLD_JSON in src:
            src = src.replace(OLD_JSON, NEW, 1)
            replaced = True
    if replaced:
        cell["source"] = [src]
        print(f"  Cell {i}: applied v47")
    else:
        # Try string search without the em dash
        if '_game_tags = list((knowledge or {}).get("_tags", []))' in src and "_has_movement" not in src:
            print(f"  Cell {i}: WARNING - v45 block found but could not patch (encoding?)")

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
