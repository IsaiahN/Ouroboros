"""v81 patch: 2 new concepts (position_commit, momentum_build)
+ classifier updates.

position_commit: Systematic grid navigation to every cell + fire commit
  action at each position. Direct solution for collect-items games (wa30)
  where player must reach each item location and press A5 to collect.
  Covers entire 8x8 grid of positions systematically.

momentum_build: Press same direction until frame stops changing (wall hit),
  then rotate direction. For large-displacement physics games (sp80 where
  A1/A2 move 162px per step) — keeps momentum going in one direction until
  blocked, then tries next.
"""

import json

NEW_CONCEPTS = (
    "\n"
    "        elif concept == 'position_commit':\n"
    "            # Systematic grid coverage + fire commit action at each position.\n"
    "            # Navigates to each 8-pixel grid position and presses commit (A5/A7/etc).\n"
    "            # Direct solution for collect-items games (wa30: navigate to item + A5).\n"
    "            # Also works for interact-on-arrival games (stand on trigger + commit).\n"
    "            _PC_STEP  = 8    # pixels per movement step (assumed)\n"
    "            _PC_GRID  = list(range(0, 64, _PC_STEP))  # [0,8,16,24,32,40,48,56]\n"
    "            _PC_POS   = [(x, y) for y in _PC_GRID for x in _PC_GRID]\n"
    "            _pc_commit_acts = [a for a in avail if a not in {1, 2, 3, 4, 6}]\n"
    "            if not _pc_commit_acts:\n"
    "                # No commit action: fall back to navigation concept\n"
    "                concept = 'navigation'\n"
    "            else:\n"
    "                _pc_commit = _pc_commit_acts[0]\n"
    "                if '_pc_phase' not in self._pipeline_context:\n"
    "                    self._pipeline_context['_pc_phase']      = 'seek'\n"
    "                    self._pipeline_context['_pc_target_idx'] = 0\n"
    "                    self._pipeline_context['_pc_nav_steps']  = 0\n"
    "                    self._pipeline_context['_pc_committed']  = False\n"
    "                _pc_phase  = self._pipeline_context['_pc_phase']\n"
    "                _pc_tidx   = self._pipeline_context['_pc_target_idx']\n"
    "                _pc_navs   = self._pipeline_context['_pc_nav_steps']\n"
    "                _pc_done   = self._pipeline_context['_pc_committed']\n"
    "                _pc_prod   = context.get('last_was_productive', False)\n"
    "                # If we just committed and it was productive: move to next target\n"
    "                if _pc_done:\n"
    "                    _pc_tidx = (_pc_tidx + 1) % len(_PC_POS)\n"
    "                    _pc_phase = 'seek'\n"
    "                    _pc_navs  = 0\n"
    "                    _pc_done  = False\n"
    "                if _pc_phase == 'commit':\n"
    "                    # Fire commit action\n"
    "                    _pc_done = True\n"
    "                    _pc_phase = 'seek'\n"
    "                    self._pipeline_context.update({\n"
    "                        '_pc_phase': _pc_phase, '_pc_target_idx': _pc_tidx,\n"
    "                        '_pc_nav_steps': 0, '_pc_committed': _pc_done,\n"
    "                    })\n"
    "                    return _pc_commit, None, (\n"
    "                        f'pos_commit:A{_pc_commit} at target={_pc_tidx}')\n"
    "                # Seek phase: navigate toward target using directional actions\n"
    "                _pc_tx, _pc_ty = _PC_POS[_pc_tidx % len(_PC_POS)]\n"
    "                _pc_navs += 1\n"
    "                # After max nav steps, commit anyway (might be at target)\n"
    "                if _pc_navs >= 12:\n"
    "                    _pc_phase = 'commit'\n"
    "                    _pc_navs  = 0\n"
    "                # Choose direction toward target (rough: use up/down/left/right)\n"
    "                # We don't know exact player pos, so cycle directions systematically\n"
    "                _pc_dir_cycle = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4, 4]\n"
    "                _pc_step_dir  = _pc_dir_cycle[(_pc_navs - 1) % len(_pc_dir_cycle)]\n"
    "                if move_actions and _pc_step_dir not in move_actions:\n"
    "                    _pc_step_dir = move_actions[0]\n"
    "                self._pipeline_context.update({\n"
    "                    '_pc_phase': _pc_phase, '_pc_target_idx': _pc_tidx,\n"
    "                    '_pc_nav_steps': _pc_navs, '_pc_committed': _pc_done,\n"
    "                })\n"
    "                return _pc_step_dir, None, (\n"
    "                    f'pos_commit:nav A{_pc_step_dir} -> ({_pc_tx},{_pc_ty}) navs={_pc_navs}')\n"
    "\n"
    "        elif concept == 'momentum_build':\n"
    "            # Keep pressing same direction until no frame change (wall hit),\n"
    "            # then rotate 90 degrees. Efficient for large-step physics games\n"
    "            # where a single action moves the player many pixels (sp80: 162px/step).\n"
    "            # Also periodically fires commit actions to collect/interact.\n"
    "            _MB_STUCK_THRESH = 2   # non-productive steps before changing direction\n"
    "            _MB_COMMIT_FREQ  = 8   # fire commit every N steps if commit action exists\n"
    "            if '_mb_dir_idx' not in self._pipeline_context:\n"
    "                self._pipeline_context['_mb_dir_idx']   = 0\n"
    "                self._pipeline_context['_mb_stuck']     = 0\n"
    "                self._pipeline_context['_mb_steps']     = 0\n"
    "            _mb_dirs  = move_actions or [1, 2, 3, 4]\n"
    "            _mb_didx  = self._pipeline_context['_mb_dir_idx']\n"
    "            _mb_stuck = self._pipeline_context['_mb_stuck']\n"
    "            _mb_steps = self._pipeline_context['_mb_steps']\n"
    "            _mb_prod  = context.get('last_was_productive', False)\n"
    "            _mb_commit_acts = [a for a in avail if a not in {1, 2, 3, 4, 6}]\n"
    "            _mb_steps += 1\n"
    "            # Periodically try commit action if available\n"
    "            if _mb_commit_acts and _mb_steps % _MB_COMMIT_FREQ == 0:\n"
    "                self._pipeline_context['_mb_steps'] = _mb_steps\n"
    "                return _mb_commit_acts[0], None, (\n"
    "                    f'momentum:commit A{_mb_commit_acts[0]} at step={_mb_steps}')\n"
    "            if not _mb_prod:\n"
    "                _mb_stuck += 1\n"
    "            else:\n"
    "                _mb_stuck = 0\n"
    "            if _mb_stuck >= _MB_STUCK_THRESH:\n"
    "                _mb_didx  = (_mb_didx + 1) % len(_mb_dirs)\n"
    "                _mb_stuck = 0\n"
    "            _mb_act = _mb_dirs[_mb_didx % len(_mb_dirs)]\n"
    "            self._pipeline_context.update({\n"
    "                '_mb_dir_idx': _mb_didx, '_mb_stuck': _mb_stuck,\n"
    "                '_mb_steps': _mb_steps,\n"
    "            })\n"
    "            return _mb_act, None, (\n"
    "                f'momentum_build:A{_mb_act} stuck={_mb_stuck} dir={_mb_didx}')\n"
    "\n"
)

TARGET = "        # navigation / coverage / traversal_ordering / mixed_movement"

# Add position_commit to interact_seek routing: when movement+commit, also include position_commit
OLD_INTERACT_ROUTE = (
    "        if (has_movement and commit_cands\n"
    "                and n_eff_now > 0 and 'interact_seek' not in cands):\n"
    "            # Movement + confirmed commit: interact_seek (navigate + press commit action).\n"
    "            _is_commit_avail = commit_cands[0]\n"
    "            cands = ['interact_seek'] + cands"
)
NEW_INTERACT_ROUTE = (
    "        if (has_movement and commit_cands\n"
    "                and n_eff_now > 0 and 'interact_seek' not in cands):\n"
    "            # Movement + confirmed commit: interact_seek (navigate + press commit action).\n"
    "            # Also add position_commit (systematic grid nav + commit at each cell) and\n"
    "            # momentum_build (keep direction until stuck + commit) as fallbacks.\n"
    "            _is_commit_avail = commit_cands[0]\n"
    "            cands = ['interact_seek', 'position_commit', 'momentum_build'] + cands"
)

# Add momentum_build and position_commit to LONG_PATH_CONCEPTS
OLD_LONG = (
    "                'greedy_productive', 'oscillation_escape', 'click_navigate',\n"
    "                'random_action',\n"
    "     "
)
NEW_LONG = (
    "                'greedy_productive', 'oscillation_escape', 'click_navigate',\n"
    "                'random_action', 'interact_seek', 'position_commit', 'momentum_build',\n"
    "     "
)

with open('bittertruth_ai_upload/competition_notebook_v2.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

cell = nb['cells'][11]
src = ''.join(cell.get('source', []))

assert TARGET in src, 'TARGET not found!'
assert OLD_INTERACT_ROUTE in src, f'OLD_INTERACT_ROUTE not found!'
assert OLD_LONG in src, f'OLD_LONG not found!'

src2 = src.replace(TARGET, NEW_CONCEPTS + TARGET, 1)
src2 = src2.replace(OLD_INTERACT_ROUTE, NEW_INTERACT_ROUTE, 1)
src2 = src2.replace(OLD_LONG, NEW_LONG, 1)

assert src2 != src
print(f'Added {len(src2) - len(src)} chars')

nb['cells'][11]['source'] = [src2]

src10 = ''.join(nb['cells'][10].get('source', []))
src10_new = src10.replace("_SOLVER_VERSION = 'v80.0'", "_SOLVER_VERSION = 'v81.0'")
assert src10_new != src10
nb['cells'][10]['source'] = [src10_new]

with open('bittertruth_ai_upload/competition_notebook_v2.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f)
print('Done v81')
