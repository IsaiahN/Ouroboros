"""
v46b: force action_num=6 during cursor scan when cursor_mode=True and ACTION6 available
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

OLD = (
    '            action_data = CURSOR_SCAN_POSITIONS[_cursor_scan_idx]\n'
    '            _cursor_scan_idx += 1\n'
    '            if _cursor_scan_idx >= len(CURSOR_SCAN_POSITIONS):\n'
    '                _cursor_scan_done = True\n'
)
NEW = (
    '            action_data = CURSOR_SCAN_POSITIONS[_cursor_scan_idx]\n'
    '            _cursor_scan_idx += 1\n'
    '            if _cursor_scan_idx >= len(CURSOR_SCAN_POSITIONS):\n'
    '                _cursor_scan_done = True\n'
    '            # v46b: cursor scan always clicks (ACTION6) when available\n'
    '            if 6 in current_available:\n'
    '                action_num = 6\n'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if OLD in src and "v46b" not in src:
        src = src.replace(OLD, NEW, 1)
        cell["source"] = [src]
        print(f"  Cell {i}: applied v46b force-click during scan")
    elif "v46b" in src:
        print(f"  Cell {i}: v46b already applied")

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
