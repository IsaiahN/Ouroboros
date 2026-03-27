"""
v53: Write placeholder submission.parquet immediately at startup.

If anything later crashes (gateway timeout, OOM, Flask failure, etc.)
Kaggle still gets a valid submission file instead of scoring 0.

Inspired by competitor QOR-Lang approach: write dummy parquet first,
overwrite with real scores at the end.
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

OLD = (
    '# -- Install ARC-AGI SDK from competition-provided wheels ----------\n'
    'import subprocess, sys, os, glob\n'
)

NEW = (
    '# -- v53: Write placeholder submission.parquet immediately ---------\n'
    '# If anything later crashes, Kaggle still gets a valid file.\n'
    'import os as _os\n'
    '_kaggle_early = _os.path.exists(\'/kaggle\')\n'
    'if _kaggle_early:\n'
    '    try:\n'
    '        import pandas as _pd_early\n'
    '        _placeholder = _pd_early.DataFrame(\n'
    '            [{"row_id": "0_0", "game_id": "placeholder",\n'
    '              "end_of_game": True, "score": 0.0}]\n'
    '        )\n'
    '        _placeholder.to_parquet(\'/kaggle/working/submission.parquet\', index=False)\n'
    '        print("submission.parquet placeholder written (v53)")\n'
    '    except Exception as _ep:\n'
    '        print(f"WARNING: could not write placeholder parquet: {_ep}")\n'
    '\n'
    '# -- Install ARC-AGI SDK from competition-provided wheels ----------\n'
    'import subprocess, sys, os, glob\n'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if "v53" in src:
        print(f"  Cell {i}: v53 already applied")
        continue
    if OLD in src:
        src = src.replace(OLD, NEW, 1)
        cell["source"] = [src]
        print(f"  Cell {i}: applied v53 placeholder parquet at startup")
        break
else:
    print("  WARNING: OLD pattern not found — patch did not apply")

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
