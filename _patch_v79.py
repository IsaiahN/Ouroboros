"""v79 patch: 3 new concepts (aligned_scan, random_action, scatter_probe)
+ classifier updates.

aligned_scan: range(0,64,8) raster click — catches s5i5 cells at multiples of 8
              that systematic_click (range(4,64,8)) misses.
random_action: uniform random over all available actions — general exploration fallback,
               breaks out of all concept dead-ends.
scatter_probe: click at random positions across the frame, record productive ones,
               then focus repeat-clicking on those — for very sparse interactive surfaces.
"""

import json

NEW_CONCEPTS = (
    "\n"
    "        elif concept == 'aligned_scan':\n"
    "            # Raster click at aligned 8-pixel grid (0,8,16,...,56) in both axes.\n"
    "            # Complements systematic_click which starts at (4,4) and misses\n"
    "            # cells aligned to multiples of 8 (e.g. s5i5 cells at 40,24).\n"
    "            # Second pass revisits productive positions.\n"
    "            _AS_GRID = list(range(0, 64, 8))\n"
    "            if '_as_positions' not in self._pipeline_context:\n"
    "                self._pipeline_context['_as_positions'] = [\n"
    "                    (x, y) for y in _AS_GRID for x in _AS_GRID]\n"
    "                self._pipeline_context['_as_changed']  = []\n"
    "                self._pipeline_context['_as_idx']      = 0\n"
    "                self._pipeline_context['_as_pass']     = 1\n"
    "            _as_pos  = self._pipeline_context['_as_positions']\n"
    "            _as_idx  = self._pipeline_context['_as_idx']\n"
    "            _as_pass = self._pipeline_context['_as_pass']\n"
    "            _as_prod = context.get('last_was_productive', False)\n"
    "            if _as_prod and _as_idx > 0:\n"
    "                self._pipeline_context['_as_changed'].append(\n"
    "                    _as_pos[(_as_idx - 1) % len(_as_pos)])\n"
    "            if _as_idx >= len(_as_pos):\n"
    "                _as_changed = self._pipeline_context['_as_changed']\n"
    "                if _as_changed and _as_pass == 1:\n"
    "                    self._pipeline_context['_as_positions'] = _as_changed\n"
    "                    self._pipeline_context['_as_changed']   = []\n"
    "                    self._pipeline_context['_as_pass']      = 2\n"
    "                else:\n"
    "                    self._pipeline_context['_as_positions'] = [\n"
    "                        (x, y) for y in _AS_GRID for x in _AS_GRID]\n"
    "                    self._pipeline_context['_as_changed']   = []\n"
    "                    self._pipeline_context['_as_pass']      = 1\n"
    "                _as_idx = 0\n"
    "            x_as, y_as = _as_pos[_as_idx % len(_as_pos)]\n"
    "            self._pipeline_context['_as_idx'] = _as_idx + 1\n"
    "            return 6, {'x': x_as, 'y': y_as}, (\n"
    "                f'aligned_scan:({x_as},{y_as}) pass={_as_pass} idx={_as_idx}')\n"
    "\n"
    "        elif concept == 'random_action':\n"
    "            # Uniform random selection from all available actions each step.\n"
    "            # General exploration fallback -- breaks out of any concept dead-end.\n"
    "            # Biases toward movement when available to avoid wasting click budget.\n"
    "            _ra_acts = list(avail)\n"
    "            if not _ra_acts:\n"
    "                return 1, None, 'random_action:empty_avail'\n"
    "            # Weight movement actions 3x vs click/commit to explore space faster\n"
    "            _ra_weighted = []\n"
    "            for _a in _ra_acts:\n"
    "                if _a in {1, 2, 3, 4}:\n"
    "                    _ra_weighted += [_a, _a, _a]\n"
    "                else:\n"
    "                    _ra_weighted.append(_a)\n"
    "            if move_actions:\n"
    "                _ra_act = _rb_random.choice(_ra_weighted)\n"
    "            else:\n"
    "                _ra_act = _rb_random.choice(_ra_acts)\n"
    "            if _ra_act == 6:\n"
    "                _ra_x = _rb_random.randint(4, 60)\n"
    "                _ra_y = _rb_random.randint(4, 60)\n"
    "                return 6, {'x': _ra_x, 'y': _ra_y}, (\n"
    "                    f'random_action:click({_ra_x},{_ra_y})')\n"
    "            return _ra_act, None, f'random_action:A{_ra_act}'\n"
    "\n"
    "        elif concept == 'scatter_probe':\n"
    "            # Click at random positions across the frame (_SP_BUDGET positions).\n"
    "            # Track which positions produce frame changes; then cycle those\n"
    "            # productive positions repeatedly.\n"
    "            # Good for: games with very sparse interactive surfaces where raster\n"
    "            # scanning is too slow (e.g. single-pixel triggers, hidden buttons).\n"
    "            _SP_BUDGET  = 64   # random positions to try in probe phase\n"
    "            _SP_REPEAT  = 20   # times to repeat each productive position\n"
    "            if '_sp_phase' not in self._pipeline_context:\n"
    "                self._pipeline_context['_sp_phase']    = 'probe'\n"
    "                self._pipeline_context['_sp_tried']    = 0\n"
    "                self._pipeline_context['_sp_hits']     = []\n"
    "                self._pipeline_context['_sp_hit_idx']  = 0\n"
    "                self._pipeline_context['_sp_rep_cnt']  = 0\n"
    "                self._pipeline_context['_sp_last_pos'] = None\n"
    "            _sp_phase   = self._pipeline_context['_sp_phase']\n"
    "            _sp_tried   = self._pipeline_context['_sp_tried']\n"
    "            _sp_hits    = self._pipeline_context['_sp_hits']\n"
    "            _sp_hidx    = self._pipeline_context['_sp_hit_idx']\n"
    "            _sp_rep     = self._pipeline_context['_sp_rep_cnt']\n"
    "            _sp_last    = self._pipeline_context['_sp_last_pos']\n"
    "            _sp_prod    = context.get('last_was_productive', False)\n"
    "            if _sp_phase == 'probe':\n"
    "                if _sp_prod and _sp_last is not None and _sp_last not in _sp_hits:\n"
    "                    _sp_hits.append(_sp_last)\n"
    "                _sp_tried += 1\n"
    "                if _sp_tried >= _SP_BUDGET:\n"
    "                    if _sp_hits:\n"
    "                        _sp_phase  = 'exploit'\n"
    "                        _sp_hidx   = 0\n"
    "                        _sp_rep    = 0\n"
    "                    else:\n"
    "                        _sp_tried  = 0  # reset probe\n"
    "                # Random position\n"
    "                _sp_x = _rb_random.randint(2, 62)\n"
    "                _sp_y = _rb_random.randint(2, 62)\n"
    "                _sp_last = (_sp_x, _sp_y)\n"
    "                self._pipeline_context.update({\n"
    "                    '_sp_phase': _sp_phase, '_sp_tried': _sp_tried,\n"
    "                    '_sp_hits': _sp_hits, '_sp_hit_idx': _sp_hidx,\n"
    "                    '_sp_rep_cnt': _sp_rep, '_sp_last_pos': _sp_last,\n"
    "                })\n"
    "                return 6, {'x': _sp_x, 'y': _sp_y}, (\n"
    "                    f'scatter_probe:probe ({_sp_x},{_sp_y}) hits={len(_sp_hits)}')\n"
    "            else:  # exploit: cycle productive positions\n"
    "                if not _sp_hits:\n"
    "                    _sp_phase = 'probe'\n"
    "                    _sp_tried = 0\n"
    "                    self._pipeline_context.update({\n"
    "                        '_sp_phase': _sp_phase, '_sp_tried': _sp_tried,\n"
    "                    })\n"
    "                    return 6, {'x': 32, 'y': 32}, 'scatter_probe:no_hits_reset'\n"
    "                _sp_rep += 1\n"
    "                if _sp_rep >= _SP_REPEAT:\n"
    "                    _sp_hidx = (_sp_hidx + 1) % len(_sp_hits)\n"
    "                    _sp_rep  = 0\n"
    "                _hx, _hy = _sp_hits[_sp_hidx % len(_sp_hits)]\n"
    "                self._pipeline_context.update({\n"
    "                    '_sp_hit_idx': _sp_hidx, '_sp_rep_cnt': _sp_rep,\n"
    "                })\n"
    "                return 6, {'x': _hx, 'y': _hy}, (\n"
    "                    f'scatter_probe:exploit ({_hx},{_hy}) n={_sp_rep}')\n"
    "\n"
)

TARGET = "        # navigation / coverage / traversal_ordering / mixed_movement"

# Classifier: add aligned_scan alongside systematic_click for click-only games,
# and add random_action as final fallback for all game types.
OLD_FINE = (
    "        # Fine-grid click: add alongside systematic_click for click-only toggle games.\n"
    "        # r11l/dc22 have cells at non-8px positions that systematic_click misses.\n"
    "        if (has_click and not has_movement\n"
    "                and 'fine_grid_click' not in cands):\n"
    "            # Add as a fallback after the standard read_grid path\n"
    "            if 'systematic_click' not in _prio:\n"
    "                _prio.append('fine_grid_click')"
)
NEW_FINE = (
    "        # Fine-grid / aligned click: add alongside systematic_click for click-only games.\n"
    "        # systematic_click: range(4,64,8) -- misses multiples of 8 (s5i5 cells at 40,24)\n"
    "        # aligned_scan:     range(0,64,8) -- hits multiples of 8, misses +4 offsets\n"
    "        # fine_grid_click:  range(2,64,4) -- 4px grid, good for non-standard alignment\n"
    "        # Together they cover all likely cell positions.\n"
    "        if (has_click and not has_movement\n"
    "                and 'fine_grid_click' not in cands):\n"
    "            _click_extras = []\n"
    "            if 'systematic_click' not in _prio:\n"
    "                _click_extras.append('systematic_click')\n"
    "            if 'aligned_scan' not in cands and 'aligned_scan' not in _prio:\n"
    "                _click_extras.append('aligned_scan')\n"
    "            _click_extras.append('fine_grid_click')\n"
    "            _click_extras.append('scatter_probe')\n"
    "            _prio += _click_extras"
)

# Also add random_action and aligned_scan to _LONG_PATH_CONCEPTS isn't right,
# but add them to the big maze priority block comment update:
OLD_LONG_PATH2 = (
    "                'greedy_productive', 'oscillation_escape', 'click_navigate',\n"
    "     "
)
NEW_LONG_PATH2 = (
    "                'greedy_productive', 'oscillation_escape', 'click_navigate',\n"
    "                'random_action',\n"
    "     "
)

with open('bittertruth_ai_upload/competition_notebook_v2.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

cell = nb['cells'][11]
src = ''.join(cell.get('source', []))

assert TARGET in src, 'TARGET not found!'
assert OLD_FINE in src, f'OLD_FINE not found!'
assert OLD_LONG_PATH2 in src, f'OLD_LONG_PATH2 not found!'

src2 = src.replace(TARGET, NEW_CONCEPTS + TARGET, 1)
src2 = src2.replace(OLD_FINE, NEW_FINE, 1)
src2 = src2.replace(OLD_LONG_PATH2, NEW_LONG_PATH2, 1)

assert src2 != src
print(f'Added {len(src2) - len(src)} chars')

nb['cells'][11]['source'] = [src2]

# Update version in cell 10
src10 = ''.join(nb['cells'][10].get('source', []))
src10_new = src10.replace("_SOLVER_VERSION = 'v78.0'", "_SOLVER_VERSION = 'v79.0'")
assert src10_new != src10, 'version not updated'
nb['cells'][10]['source'] = [src10_new]

with open('bittertruth_ai_upload/competition_notebook_v2.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f)
print('Done v79')
