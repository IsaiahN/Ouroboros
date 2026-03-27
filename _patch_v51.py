"""
v51: denser cursor scan — step 8 (64 positions) instead of step 10 (36).
Also: multi-action cursor scan — for games with ACTION7, alternate 6/7.

Step 10: range(5,62,10) -> 6x6 = 36 positions (~14% grid coverage)
Step 8:  range(4,61,8)  -> 8x8 = 64 positions (~25% grid coverage)
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

OLD = (
    'CURSOR_SCAN_POSITIONS = [{"x": x, "y": y} for y in range(5, 62, 10) for x in range(5, 62, 10)]\n'
)

NEW = (
    '# v51: denser scan — step 8 -> 8x8 = 64 positions (was step 10 -> 36)\n'
    'CURSOR_SCAN_POSITIONS = [{"x": x, "y": y} for y in range(4, 61, 8) for x in range(4, 61, 8)]\n'
)

OLD_ACTION6 = (
    '            # v46b: cursor scan always clicks (ACTION6) when available\n'
    '            if 6 in current_available:\n'
    '                action_num = 6\n'
)

NEW_ACTION6 = (
    '            # v46b/v51: cursor scan clicks ACTION6 or ACTION7 if available\n'
    '            # Alternate between ACTION6 and ACTION7 to cover both click types\n'
    '            _scan_action = 6 if (_cursor_scan_idx % 2 == 0) else 7\n'
    '            if _scan_action in current_available:\n'
    '                action_num = _scan_action\n'
    '            elif 6 in current_available:\n'
    '                action_num = 6\n'
    '            elif 7 in current_available:\n'
    '                action_num = 7\n'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if "v51" in src:
        print(f"  Cell {i}: v51 already applied")
        continue
    replaced = False
    if OLD in src:
        src = src.replace(OLD, NEW, 1)
        print(f"  Cell {i}: applied v51 denser scan")
        replaced = True
    if OLD_ACTION6 in src:
        src = src.replace(OLD_ACTION6, NEW_ACTION6, 1)
        print(f"  Cell {i}: applied v51 multi-action scan")
        replaced = True
    if replaced:
        cell["source"] = [src]

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
