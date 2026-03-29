"""v80 patch: 2 new concepts (repeat_productive, triple_search)
+ minor classifier refinements.

repeat_productive: When last click was productive, re-click same position
  up to _RP_MAX times before advancing. Handles games like lf52 where
  clicking same cell 2-3 times is part of the solution.

triple_search: Extends combo_search to ordered triples (a1, a2, a3).
  Useful for 3-step unlock sequences (commit+interact+confirm style games).
"""

import json

NEW_CONCEPTS = (
    "\n"
    "        elif concept == 'repeat_productive':\n"
    "            # When the last click was productive, re-click the SAME position\n"
    "            # up to _RP_MAX times before moving to the next grid position.\n"
    "            # Handles games where multiple clicks on the same cell are needed\n"
    "            # (e.g. lf52 cells requiring 2-3 clicks, ft09 NTi self-toggle).\n"
    "            # Falls back to systematic 8-pixel raster when no repeat needed.\n"
    "            _RP_MAX  = 4    # max re-clicks before advancing to next position\n"
    "            _RP_GRID = list(range(0, 64, 8)) + list(range(4, 64, 8))  # both grids\n"
    "            _RP_POSITIONS = sorted(set(\n"
    "                (x, y) for y in range(0, 64, 8) for x in range(0, 64, 8)))\n"
    "            if '_rp_idx' not in self._pipeline_context:\n"
    "                self._pipeline_context['_rp_idx']      = 0\n"
    "                self._pipeline_context['_rp_rep']      = 0\n"
    "                self._pipeline_context['_rp_last_pos'] = None\n"
    "                self._pipeline_context['_rp_positions'] = _RP_POSITIONS\n"
    "            _rp_positions = self._pipeline_context['_rp_positions']\n"
    "            _rp_idx  = self._pipeline_context['_rp_idx']\n"
    "            _rp_rep  = self._pipeline_context['_rp_rep']\n"
    "            _rp_last = self._pipeline_context['_rp_last_pos']\n"
    "            _rp_prod = context.get('last_was_productive', False)\n"
    "            if _rp_prod and _rp_rep < _RP_MAX and _rp_last is not None:\n"
    "                # Re-click same position\n"
    "                _rp_rep += 1\n"
    "                _rx, _ry = _rp_last\n"
    "                self._pipeline_context['_rp_rep'] = _rp_rep\n"
    "                return 6, {'x': _rx, 'y': _ry}, (\n"
    "                    f'repeat_prod:re-click ({_rx},{_ry}) rep={_rp_rep}')\n"
    "            else:\n"
    "                # Advance to next position\n"
    "                _rp_rep = 0\n"
    "                if _rp_idx >= len(_rp_positions):\n"
    "                    _rp_idx = 0\n"
    "                _rx, _ry = _rp_positions[_rp_idx % len(_rp_positions)]\n"
    "                _rp_idx += 1\n"
    "                self._pipeline_context.update({\n"
    "                    '_rp_idx': _rp_idx, '_rp_rep': _rp_rep, '_rp_last_pos': (_rx, _ry),\n"
    "                })\n"
    "                return 6, {'x': _rx, 'y': _ry}, (\n"
    "                    f'repeat_prod:scan ({_rx},{_ry}) idx={_rp_idx}')\n"
    "\n"
    "        elif concept == 'triple_search':\n"
    "            # Try all ordered triples (a1, a2, a3) from non-click available actions.\n"
    "            # Extends combo_search for 3-step unlock sequences.\n"
    "            # Good for: games where a 3-action combination is needed\n"
    "            #           (interact-move-confirm, push-push-commit, etc.).\n"
    "            acts_t = move_actions or [a for a in avail if a != 6] or list(avail)\n"
    "            n_t = len(acts_t)\n"
    "            if n_t == 0:\n"
    "                return _rb_random.choice(list(avail)), None, 'triple:no_acts'\n"
    "            _ti = self._pipeline_context.get('_tri_i', 0)\n"
    "            _tj = self._pipeline_context.get('_tri_j', 0)\n"
    "            _tk = self._pipeline_context.get('_tri_k', 0)\n"
    "            _ts = self._pipeline_context.get('_tri_sub', 0)  # 0=a1, 1=a2, 2=a3\n"
    "            a1t = acts_t[_ti % n_t]\n"
    "            a2t = acts_t[_tj % n_t]\n"
    "            a3t = acts_t[_tk % n_t]\n"
    "            if _ts == 0:\n"
    "                act_t = a1t\n"
    "            elif _ts == 1:\n"
    "                act_t = a2t\n"
    "            else:\n"
    "                act_t = a3t\n"
    "                _ts = -1  # will become 0 after += 1\n"
    "                _tk += 1\n"
    "                if _tk >= n_t:\n"
    "                    _tk = 0\n"
    "                    _tj += 1\n"
    "                    if _tj >= n_t:\n"
    "                        _tj = 0\n"
    "                        _ti = (_ti + 1) % n_t\n"
    "            self._pipeline_context['_tri_i']   = _ti\n"
    "            self._pipeline_context['_tri_j']   = _tj\n"
    "            self._pipeline_context['_tri_k']   = _tk\n"
    "            self._pipeline_context['_tri_sub'] = _ts + 1\n"
    "            return act_t, None, (\n"
    "                f'triple_search:A{a1t}+A{a2t}+A{a3t}(sub={_ts})')\n"
    "\n"
)

TARGET = "        # navigation / coverage / traversal_ordering / mixed_movement"

# Add repeat_productive to the click-only game priority along with other scan concepts
OLD_CLICK_EXTRAS = (
    "            _click_extras = []\n"
    "            if 'systematic_click' not in _prio:\n"
    "                _click_extras.append('systematic_click')\n"
    "            if 'aligned_scan' not in cands and 'aligned_scan' not in _prio:\n"
    "                _click_extras.append('aligned_scan')\n"
    "            _click_extras.append('fine_grid_click')\n"
    "            _click_extras.append('scatter_probe')\n"
    "            _prio += _click_extras"
)
NEW_CLICK_EXTRAS = (
    "            _click_extras = []\n"
    "            if 'systematic_click' not in _prio:\n"
    "                _click_extras.append('systematic_click')\n"
    "            if 'aligned_scan' not in cands and 'aligned_scan' not in _prio:\n"
    "                _click_extras.append('aligned_scan')\n"
    "            _click_extras.append('repeat_productive')\n"
    "            _click_extras.append('fine_grid_click')\n"
    "            _click_extras.append('scatter_probe')\n"
    "            _prio += _click_extras"
)

with open('bittertruth_ai_upload/competition_notebook_v2.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

cell = nb['cells'][11]
src = ''.join(cell.get('source', []))

assert TARGET in src, 'TARGET not found!'
assert OLD_CLICK_EXTRAS in src, 'OLD_CLICK_EXTRAS not found!'

src2 = src.replace(TARGET, NEW_CONCEPTS + TARGET, 1)
src2 = src2.replace(OLD_CLICK_EXTRAS, NEW_CLICK_EXTRAS, 1)

assert src2 != src
print(f'Added {len(src2) - len(src)} chars')

nb['cells'][11]['source'] = [src2]

src10 = ''.join(nb['cells'][10].get('source', []))
src10_new = src10.replace("_SOLVER_VERSION = 'v79.0'", "_SOLVER_VERSION = 'v80.0'")
assert src10_new != src10
nb['cells'][10]['source'] = [src10_new]

with open('bittertruth_ai_upload/competition_notebook_v2.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f)
print('Done v80')
