"""
v46 patch: fix cursor scan condition for keyboard_click games
- After v45 probe-classify switches keyboard_click to cursor_mode, effects from
  navigation probes block the scan. Remove the len(effects)==0 gate when cursor_mode=True.
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

# Fix the cursor scan condition to run when cursor_mode=True regardless of effects
OLD = (
    '        # Cursor scan override (v20): systematic grid scan while no effects known\n'
    '        if (not _cursor_scan_done and\n'
    '                _cursor_scan_idx < len(CURSOR_SCAN_POSITIONS) and\n'
    '                len(getattr(getattr(loop, "_causal_map", None), "_effects", {})) == 0):\n'
)
NEW = (
    '        # Cursor scan override (v20/v46): grid scan while cursor_mode active\n'
    '        # v46: run scan if cursor_mode=True regardless of effects (keyboard_click games\n'
    '        # may have navigation effects from probe phase but still need click scan)\n'
    '        _cm_effects = len(getattr(getattr(loop, "_causal_map", None), "_effects", {}))\n'
    '        if (not _cursor_scan_done and\n'
    '                _cursor_scan_idx < len(CURSOR_SCAN_POSITIONS) and\n'
    '                (_cm_effects == 0 or getattr(loop, "_cursor_mode", False))):\n'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if OLD in src:
        src = src.replace(OLD, NEW, 1)
        cell["source"] = [src]
        print(f"  Cell {i}: applied v46 cursor scan fix")
    elif "_cm_effects" in src:
        print(f"  Cell {i}: v46 already applied, skipping")

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
