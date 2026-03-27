"""
v52: handle KAGGLE_IS_COMPETITION_RERUN correctly.

In competition rerun mode (KAGGLE_IS_COMPETITION_RERUN=1):
- Kaggle's gateway is already running at http://gateway:8001
- Connect to IT (OperationMode.ONLINE) instead of starting our own Flask server
- Let the gateway write submission.parquet via close_scorecard()
- Also call close_scorecard() in standard mode so scores are finalized

In standard mode (no env var, or local):
- Keep starting our own local server (existing v34 behavior)
- Still write parquet manually as before
"""

import json

NB = "competition_notebook.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

OLD = (
    '# -- Competition mode: start local game server (v34) --------\n'
    'import threading as _threading\n'
    'COMPETITION_MODE = True  # always run in competition mode (v34b)\n'
    'if COMPETITION_MODE:\n'
    '    print(\'COMPETITION MODE: starting local game server on port 8001...\')\n'
    '    _srv_arcade = Arcade(\n'
    '        operation_mode=OperationMode.OFFLINE,\n'
    '        arc_api_key=\'\',\n'
    '        environments_dir=ENVS_DIR,\n'
    '    )\n'
    '    _srv_thread = _threading.Thread(\n'
    '        target=lambda: _srv_arcade.listen_and_serve(competition_mode=True),\n'
    '        daemon=True,\n'
    '    )\n'
    '    _srv_thread.start()\n'
    '    time.sleep(3)  # wait for Flask to initialise\n'
    '    os.environ[\'ARC_BASE_URL\'] = \'http://localhost:8001\'\n'
    '    arcade = Arcade(\n'
    '        operation_mode=OperationMode.COMPETITION,\n'
    '        arc_api_key=\'local\',  # non-empty skips anonymous key fetch (v34c)\n'
    '        environments_dir=ENVS_DIR,\n'
    '    )\n'
    '    games = arcade.get_environments()\n'
    '    print(f\'Server started. {len(games)} competition games available.\')\n'
)

NEW = (
    '# -- Competition mode setup (v52) ----------------------------------\n'
    '# In competition rerun (KAGGLE_IS_COMPETITION_RERUN=1): connect to\n'
    '# Kaggle\'s official gateway at http://gateway:8001 (ONLINE mode).\n'
    '# In standard/local mode: start our own local Flask server (v34).\n'
    'import threading as _threading\n'
    'COMPETITION_MODE = True\n'
    '_IS_COMP_RERUN = bool(os.getenv(\'KAGGLE_IS_COMPETITION_RERUN\'))\n'
    'if _IS_COMP_RERUN:\n'
    '    # Official competition rerun: use Kaggle\'s gateway\n'
    '    print(\'COMPETITION RERUN: connecting to Kaggle gateway at gateway:8001...\')\n'
    '    # Wait for gateway to be ready (up to 2 min)\n'
    '    import urllib.request as _ur\n'
    '    for _attempt in range(24):\n'
    '        try:\n'
    '            _ur.urlopen(\'http://gateway:8001/api/games\', timeout=5)\n'
    '            break\n'
    '        except Exception:\n'
    '            time.sleep(5)\n'
    '    os.environ[\'ARC_BASE_URL\'] = \'http://gateway:8001\'\n'
    '    _arc_api_key = os.getenv(\'ARC_API_KEY\', \'test-key-123\')\n'
    '    arcade = Arcade(\n'
    '        operation_mode=OperationMode.ONLINE,\n'
    '        arc_api_key=_arc_api_key,\n'
    '        environments_dir=ENVS_DIR,\n'
    '    )\n'
    '    games = arcade.get_environments()\n'
    '    print(f\'Gateway ready. {len(games)} competition games available.\')\n'
    'else:\n'
    '    # Standard/local mode: start our own local server (v34)\n'
    '    print(\'COMPETITION MODE: starting local game server on port 8001...\')\n'
    '    _srv_arcade = Arcade(\n'
    '        operation_mode=OperationMode.OFFLINE,\n'
    '        arc_api_key=\'\',\n'
    '        environments_dir=ENVS_DIR,\n'
    '    )\n'
    '    _srv_thread = _threading.Thread(\n'
    '        target=lambda: _srv_arcade.listen_and_serve(competition_mode=True),\n'
    '        daemon=True,\n'
    '    )\n'
    '    _srv_thread.start()\n'
    '    time.sleep(3)  # wait for Flask to initialise\n'
    '    os.environ[\'ARC_BASE_URL\'] = \'http://localhost:8001\'\n'
    '    arcade = Arcade(\n'
    '        operation_mode=OperationMode.COMPETITION,\n'
    '        arc_api_key=\'local\',\n'
    '        environments_dir=ENVS_DIR,\n'
    '    )\n'
    '    games = arcade.get_environments()\n'
    '    print(f\'Server started. {len(games)} competition games available.\')\n'
)

# Find and replace the close_scorecard call location
OLD_END = (
    '# -- Write submission.parquet (required by Kaggle as submission artifact) --\n'
    '# Build rows for ALL games; unplayed games get score=0.\n'
    'try:\n'
    '    import pandas as _pd\n'
    '    _results_map = {r[\'game_id\']: r[\'score\'] for r in all_results}\n'
    '    _rows = []\n'
    '    for _i, _g in enumerate(games):\n'
    '        _score = float(_results_map.get(_g.game_id, 0.0))\n'
    '        _rows.append({\'row_id\': f\'{_i}_0\', \'game_id\': _g.game_id,\n'
    '                       \'end_of_game\': True, \'score\': _score})\n'
    '    _sub_df = _pd.DataFrame(_rows)\n'
    '    _sub_path = \'/kaggle/working/submission.parquet\' if KAGGLE else \'submission.parquet\'\n'
    '    _sub_df.to_parquet(_sub_path, index=False)\n'
    '    print(f\'submission.parquet written: {len(_sub_df)} rows, \'\n'
    '          f\'avg_score={_sub_df["score"].mean():.4f}\')\n'
    'except Exception as _e:\n'
    '    print(f\'WARNING: failed to write submission.parquet: {_e}\')'
)

NEW_END = (
    '# -- Finalize scorecard + write submission.parquet (v52) -------\n'
    '# In competition rerun: close_scorecard() tells the Kaggle gateway\n'
    '# to finalize scores; the gateway writes the official parquet.\n'
    '# In standard mode: write parquet manually from our tracked results.\n'
    'try:\n'
    '    _final_scorecard = arcade.close_scorecard(scorecard_id)\n'
    '    if _final_scorecard:\n'
    '        print(f\'Scorecard closed. Official score: {_final_scorecard.score:.4f}\')\n'
    'except Exception as _sce:\n'
    '    print(f\'close_scorecard warning: {_sce}\')\n'
    '\n'
    '# Always write parquet from our tracking (gateway may also write it)\n'
    'try:\n'
    '    import pandas as _pd\n'
    '    _results_map = {r[\'game_id\']: r[\'score\'] for r in all_results}\n'
    '    _rows = []\n'
    '    for _i, _g in enumerate(games):\n'
    '        _score = float(_results_map.get(_g.game_id, 0.0))\n'
    '        _rows.append({\'row_id\': f\'{_i}_0\', \'game_id\': _g.game_id,\n'
    '                       \'end_of_game\': True, \'score\': _score})\n'
    '    _sub_df = _pd.DataFrame(_rows)\n'
    '    _sub_path = \'/kaggle/working/submission.parquet\' if KAGGLE else \'submission.parquet\'\n'
    '    _sub_df.to_parquet(_sub_path, index=False)\n'
    '    print(f\'submission.parquet written: {len(_sub_df)} rows, \'\n'
    '          f\'avg_score={_sub_df["score"].mean():.4f}\')\n'
    'except Exception as _e:\n'
    '    print(f\'WARNING: failed to write submission.parquet: {_e}\')'
)

for i, cell in enumerate(cells):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if "v52" in src:
        print(f"  Cell {i}: v52 already applied")
        continue
    changed = False
    if OLD in src:
        src = src.replace(OLD, NEW, 1)
        print(f"  Cell {i}: applied v52 competition-rerun gateway handling")
        changed = True
    if OLD_END in src:
        src = src.replace(OLD_END, NEW_END, 1)
        print(f"  Cell {i}: applied v52 close_scorecard + parquet finalization")
        changed = True
    if changed:
        cell["source"] = [src]
    elif "listen_and_serve" in src and "COMPETITION_MODE" in src:
        print(f"  Cell {i}: WARNING — competition setup found but patch didn't match")

with open(NB, "w", encoding="ascii") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("Done.")
