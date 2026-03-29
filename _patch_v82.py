"""v82 patch: fix _RP_MAX 4→8 + add dense_zero_scan concept.

_RP_MAX fix: s5i5 needs 7 clicks on a single cell. With _RP_MAX=4 we get
  only 1+4=5 total clicks, not enough. Bumping to 8 gives 1+8=9 total,
  covering s5i5's max of 7 clicks per cell.

dense_zero_scan: Raster click at 4px step starting at (0,0).
  fine_grid_click uses range(2,64,4)=[2,6,10,...] which misses 0,4,8,12...
  dense_zero_scan uses range(0,64,4)=[0,4,8,12,16,20,24,28,32,36,40,44,48,52,56,60].
  Together they give complete 2px coverage of the frame.
  Also important for games with cells at multiples of 4 (lf52 cells at 28,40, etc).
"""

import json

NEW_CONCEPTS = (
    "\n"
    "        elif concept == 'dense_zero_scan':\n"
    "            # Raster click at 4px grid starting at (0,0).\n"
    "            # fine_grid_click uses range(2,64,4)=[2,6,10,...] missing 0,4,8,12...\n"
    "            # dense_zero_scan uses range(0,64,4)=[0,4,8,12,16,...] filling that gap.\n"
    "            # Together: complete 2px coverage. Handles lf52 cells at 28/40,\n"
    "            # s5i5 cells at 24/48, and any game with 4px-aligned cell centers.\n"
    "            _DZ_STEP = 4\n"
    "            _DZ_GRID = list(range(0, 64, _DZ_STEP))\n"
    "            if '_dz_positions' not in self._pipeline_context:\n"
    "                self._pipeline_context['_dz_positions'] = [\n"
    "                    (x, y) for y in _DZ_GRID for x in _DZ_GRID]\n"
    "                self._pipeline_context['_dz_changed']   = []\n"
    "                self._pipeline_context['_dz_idx']       = 0\n"
    "                self._pipeline_context['_dz_pass']      = 1\n"
    "            _dz_pos  = self._pipeline_context['_dz_positions']\n"
    "            _dz_idx  = self._pipeline_context['_dz_idx']\n"
    "            _dz_pass = self._pipeline_context['_dz_pass']\n"
    "            _dz_prod = context.get('last_was_productive', False)\n"
    "            if _dz_prod and _dz_idx > 0:\n"
    "                self._pipeline_context['_dz_changed'].append(\n"
    "                    _dz_pos[(_dz_idx - 1) % len(_dz_pos)])\n"
    "            if _dz_idx >= len(_dz_pos):\n"
    "                _dz_changed = self._pipeline_context['_dz_changed']\n"
    "                if _dz_changed and _dz_pass == 1:\n"
    "                    self._pipeline_context['_dz_positions'] = _dz_changed\n"
    "                    self._pipeline_context['_dz_changed']   = []\n"
    "                    self._pipeline_context['_dz_pass']      = 2\n"
    "                else:\n"
    "                    self._pipeline_context['_dz_positions'] = [\n"
    "                        (x, y) for y in _DZ_GRID for x in _DZ_GRID]\n"
    "                    self._pipeline_context['_dz_changed']   = []\n"
    "                    self._pipeline_context['_dz_pass']      = 1\n"
    "                _dz_idx = 0\n"
    "            x_dz, y_dz = _dz_pos[_dz_idx % len(_dz_pos)]\n"
    "            self._pipeline_context['_dz_idx'] = _dz_idx + 1\n"
    "            return 6, {'x': x_dz, 'y': y_dz}, (\n"
    "                f'dense_zero:({x_dz},{y_dz}) pass={_dz_pass} idx={_dz_idx}')\n"
    "\n"
)

TARGET = "        # navigation / coverage / traversal_ordering / mixed_movement"

# Fix _RP_MAX from 4 to 8
OLD_RP_MAX = "            _RP_MAX  = 4    # max re-clicks before advancing to next position"
NEW_RP_MAX = "            _RP_MAX  = 8    # max re-clicks before advancing to next position"

# Add dense_zero_scan to click-only game priority
OLD_CLICK_EXTRAS = (
    "            _click_extras.append('repeat_productive')\n"
    "            _click_extras.append('fine_grid_click')\n"
    "            _click_extras.append('scatter_probe')\n"
    "            _prio += _click_extras"
)
NEW_CLICK_EXTRAS = (
    "            _click_extras.append('repeat_productive')\n"
    "            _click_extras.append('fine_grid_click')\n"
    "            _click_extras.append('dense_zero_scan')\n"
    "            _click_extras.append('scatter_probe')\n"
    "            _prio += _click_extras"
)

with open('bittertruth_ai_upload/competition_notebook_v2.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

cell = nb['cells'][11]
src = ''.join(cell.get('source', []))

assert TARGET in src, 'TARGET not found!'
assert OLD_RP_MAX in src, f'OLD_RP_MAX not found!'
assert OLD_CLICK_EXTRAS in src, f'OLD_CLICK_EXTRAS not found!'

src2 = src.replace(TARGET, NEW_CONCEPTS + TARGET, 1)
src2 = src2.replace(OLD_RP_MAX, NEW_RP_MAX, 1)
src2 = src2.replace(OLD_CLICK_EXTRAS, NEW_CLICK_EXTRAS, 1)

assert src2 != src
print(f'Added {len(src2) - len(src)} chars')

nb['cells'][11]['source'] = [src2]

src10 = ''.join(nb['cells'][10].get('source', []))
src10_new = src10.replace("_SOLVER_VERSION = 'v81.0'", "_SOLVER_VERSION = 'v82.0'")
assert src10_new != src10
nb['cells'][10]['source'] = [src10_new]

with open('bittertruth_ai_upload/competition_notebook_v2.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f)
print('Done v82')
