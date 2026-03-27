"""
v54: In competition rerun mode, skip the manual parquet write.

The gateway writes the official submission.parquet when close_scorecard()
is called. Our manual write was overwriting it with potentially different
data. In standard mode we still write manually (no gateway).
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

OLD = (
    '# Always write parquet from our tracking (gateway may also write it)\n'
    'try:\n'
    '    import pandas as _pd\n'
)

NEW = (
    '# In competition rerun the gateway writes parquet via close_scorecard().\n'
    '# Only write manually in standard/local mode (v54).\n'
    'if not _IS_COMP_RERUN:\n'
    '    try:\n'
    '        import pandas as _pd\n'
)

OLD_END = (
    '    print(f\'submission.parquet written: {len(_sub_df)} rows, \'\n'
    '          f\'avg_score={_sub_df["score"].mean():.4f}\')\n'
    'except Exception as _e:\n'
    '    print(f\'WARNING: failed to write submission.parquet: {_e}\')'
)

NEW_END = (
    '        print(f\'submission.parquet written: {len(_sub_df)} rows, \'\n'
    '              f\'avg_score={_sub_df["score"].mean():.4f}\')\n'
    '    except Exception as _e:\n'
    '        print(f\'WARNING: failed to write submission.parquet: {_e}\')'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if "v54" in src:
        print(f"  Cell {i}: v54 already applied")
        continue
    changed = False
    if OLD in src:
        src = src.replace(OLD, NEW, 1)
        print(f"  Cell {i}: applied v54 guard on manual parquet write")
        changed = True
    if OLD_END in src:
        src = src.replace(OLD_END, NEW_END, 1)
        print(f"  Cell {i}: applied v54 indentation fix on parquet block")
        changed = True
    if changed:
        cell["source"] = [src]
    elif "Always write parquet" in src:
        print(f"  Cell {i}: WARNING — parquet block found but patch didn't match")

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
