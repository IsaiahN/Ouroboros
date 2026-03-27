"""
v54b: Fix the broken indentation from v54.

v54 only re-indented the first and last lines of the try block,
leaving the middle body at the wrong level. Replace entire block.
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

OLD = (
    '# In competition rerun the gateway writes parquet via close_scorecard().\n'
    '# Only write manually in standard/local mode (v54).\n'
    'if not _IS_COMP_RERUN:\n'
    '    try:\n'
    '        import pandas as _pd\n'
    '    _results_map = {r[\'game_id\']: r[\'score\'] for r in all_results}\n'
    '    _rows = []\n'
    '    for _i, _g in enumerate(games):\n'
    '        _score = float(_results_map.get(_g.game_id, 0.0))\n'
    '        _rows.append({\'row_id\': f\'{_i}_0\', \'game_id\': _g.game_id,\n'
    '                       \'end_of_game\': True, \'score\': _score})\n'
    '    _sub_df = _pd.DataFrame(_rows)\n'
    '    _sub_path = \'/kaggle/working/submission.parquet\' if KAGGLE else \'submission.parquet\'\n'
    '    _sub_df.to_parquet(_sub_path, index=False)\n'
    '        print(f\'submission.parquet written: {len(_sub_df)} rows, \'\n'
    '              f\'avg_score={_sub_df["score"].mean():.4f}\')\n'
    '    except Exception as _e:\n'
    '        print(f\'WARNING: failed to write submission.parquet: {_e}\')'
)

NEW = (
    '# In competition rerun the gateway writes parquet via close_scorecard().\n'
    '# Only write manually in standard/local mode (v54b).\n'
    'if not _IS_COMP_RERUN:\n'
    '    try:\n'
    '        import pandas as _pd\n'
    '        _results_map = {r[\'game_id\']: r[\'score\'] for r in all_results}\n'
    '        _rows = []\n'
    '        for _i, _g in enumerate(games):\n'
    '            _score = float(_results_map.get(_g.game_id, 0.0))\n'
    '            _rows.append({\'row_id\': f\'{_i}_0\', \'game_id\': _g.game_id,\n'
    '                           \'end_of_game\': True, \'score\': _score})\n'
    '        _sub_df = _pd.DataFrame(_rows)\n'
    '        _sub_path = \'/kaggle/working/submission.parquet\' if KAGGLE else \'submission.parquet\'\n'
    '        _sub_df.to_parquet(_sub_path, index=False)\n'
    '        print(f\'submission.parquet written: {len(_sub_df)} rows, \'\n'
    '              f\'avg_score={_sub_df["score"].mean():.4f}\')\n'
    '    except Exception as _e:\n'
    '        print(f\'WARNING: failed to write submission.parquet: {_e}\')'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if OLD in src:
        src = src.replace(OLD, NEW, 1)
        cell["source"] = [src]
        print(f"  Cell {i}: applied v54b indentation fix")
        break
else:
    print("  WARNING: broken block not found")

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
