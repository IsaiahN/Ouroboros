"""v78 patch: 3 new concepts + classifier fixes for re86/ar25/dc22/bp35 navigation routing.

New concepts:
  - greedy_productive: tracks per-action frame-change productivity; always chooses best direction
  - oscillation_escape: detects frame-repeat cycles, forces random escape direction
  - click_navigate: move + click at center every 5 steps (dc22/bp35 interact-on-overlap)

Classifier fix:
  - Maze routing fires for ANY movement game with no commit and no CausalMap data,
    regardless of whether A6 is in available_actions (re86/ar25 had has_click=True
    but click is useless -- was blocked from maze routing).
"""

import json

# ---------------------------------------------------------------------------
# New concept handlers (inserted before marker)
# ---------------------------------------------------------------------------
NEW_CONCEPTS = (
    "\n"
    "        elif concept == 'greedy_productive':\n"
    "            # Track per-action frame-change productivity over last _GP_WINDOW steps.\n"
    "            # Always choose the action with the highest recent productivity score.\n"
    "            # Re-probe all actions every _GP_RESET steps to stay adaptive.\n"
    "            # Good for: navigation games (re86/ar25/dc22) where more movement = progress.\n"
    "            _GP_WINDOW = 10   # rolling window steps scored per action\n"
    "            _GP_RESET  = 40   # full re-probe cycle after this many steps\n"
    "            acts_gp = (move_actions or list(avail))\n"
    "            if not acts_gp:\n"
    "                return _rb_random.choice(list(avail)), None, 'gp:no_acts'\n"
    "            if '_gp_scores' not in self._pipeline_context:\n"
    "                self._pipeline_context['_gp_scores'] = {a: 0.0 for a in acts_gp}\n"
    "                self._pipeline_context['_gp_counts'] = {a: 0   for a in acts_gp}\n"
    "                self._pipeline_context['_gp_cur']    = acts_gp[0]\n"
    "                self._pipeline_context['_gp_step']   = 0\n"
    "                self._pipeline_context['_gp_probe_idx'] = 0\n"
    "                self._pipeline_context['_gp_phase']  = 'probe'\n"
    "            _gp_scores  = self._pipeline_context['_gp_scores']\n"
    "            _gp_counts  = self._pipeline_context['_gp_counts']\n"
    "            _gp_cur     = self._pipeline_context['_gp_cur']\n"
    "            _gp_step    = self._pipeline_context['_gp_step']\n"
    "            _gp_pidx    = self._pipeline_context['_gp_probe_idx']\n"
    "            _gp_phase   = self._pipeline_context['_gp_phase']\n"
    "            _gp_prod    = context.get('last_was_productive', True)\n"
    "            # Score the last action\n"
    "            if _gp_cur in _gp_scores:\n"
    "                _gp_scores[_gp_cur] = (_gp_scores[_gp_cur] * _gp_counts.get(_gp_cur, 0)\n"
    "                                       + (1.0 if _gp_prod else 0.0))\n"
    "                _gp_counts[_gp_cur] = _gp_counts.get(_gp_cur, 0) + 1\n"
    "                if _gp_counts[_gp_cur] > 0:\n"
    "                    _gp_scores[_gp_cur] /= _gp_counts[_gp_cur]\n"
    "            _gp_step += 1\n"
    "            # Probe phase: cycle through each action _GP_WINDOW times\n"
    "            if _gp_phase == 'probe':\n"
    "                _probe_act = acts_gp[_gp_pidx % len(acts_gp)]\n"
    "                if _gp_step % _GP_WINDOW == 0:\n"
    "                    _gp_pidx += 1\n"
    "                    if _gp_pidx >= len(acts_gp):\n"
    "                        _gp_phase = 'exploit'\n"
    "                        _gp_step  = 0\n"
    "                        _gp_pidx  = 0\n"
    "                _gp_cur = _probe_act\n"
    "            else:  # exploit phase: pick best\n"
    "                if _gp_step >= _GP_RESET:\n"
    "                    # Reset scores and re-probe\n"
    "                    _gp_scores  = {a: 0.0 for a in acts_gp}\n"
    "                    _gp_counts  = {a: 0   for a in acts_gp}\n"
    "                    _gp_phase   = 'probe'\n"
    "                    _gp_step    = 0\n"
    "                    _gp_pidx    = 0\n"
    "                _gp_cur = max(acts_gp, key=lambda a: _gp_scores.get(a, 0.0))\n"
    "            self._pipeline_context.update({\n"
    "                '_gp_scores': _gp_scores, '_gp_counts': _gp_counts,\n"
    "                '_gp_cur': _gp_cur, '_gp_step': _gp_step,\n"
    "                '_gp_probe_idx': _gp_pidx, '_gp_phase': _gp_phase,\n"
    "            })\n"
    "            return _gp_cur, None, (\n"
    "                f'greedy_prod:A{_gp_cur} phase={_gp_phase} '\n"
    "                f'sc={_gp_scores.get(_gp_cur,0):.2f}')\n"
    "\n"
    "        elif concept == 'oscillation_escape':\n"
    "            # Maintain rolling window of recent frame hashes.\n"
    "            # If current frame was seen in last _OE_WINDOW steps, we are in a cycle:\n"
    "            # force a random direction change for _OE_ESCAPE steps.\n"
    "            # Good for: any game where player bounces between 2-3 states forever.\n"
    "            _OE_WINDOW = 12   # look-back steps for repeated frame detection\n"
    "            _OE_ESCAPE = 8    # steps to move in random escape direction\n"
    "            if '_oe_hashes' not in self._pipeline_context:\n"
    "                self._pipeline_context['_oe_hashes']   = []\n"
    "                self._pipeline_context['_oe_escape_n'] = 0\n"
    "                self._pipeline_context['_oe_dir']      = None\n"
    "            _oe_hashes   = self._pipeline_context['_oe_hashes']\n"
    "            _oe_escape_n = self._pipeline_context['_oe_escape_n']\n"
    "            _oe_dir      = self._pipeline_context['_oe_dir']\n"
    "            # Hash current frame\n"
    "            _oe_frame = context.get('frame')\n"
    "            _oe_h = None\n"
    "            if _oe_frame is not None:\n"
    "                try:\n"
    "                    import numpy as _np\n"
    "                    _arr = _np.array(_oe_frame).flatten()\n"
    "                    _oe_h = int(_arr[::max(1, len(_arr)//32)].sum()) & 0xFFFF\n"
    "                except Exception:\n"
    "                    pass\n"
    "            # Check for cycle\n"
    "            _oe_repeat = (_oe_h is not None and _oe_h in _oe_hashes)\n"
    "            if _oe_h is not None:\n"
    "                _oe_hashes.append(_oe_h)\n"
    "                if len(_oe_hashes) > _OE_WINDOW:\n"
    "                    _oe_hashes.pop(0)\n"
    "            acts_oe = move_actions or list(avail)\n"
    "            if not acts_oe:\n"
    "                return _rb_random.choice(list(avail)), None, 'oe:no_acts'\n"
    "            if _oe_repeat or _oe_escape_n > 0:\n"
    "                if _oe_dir is None or _oe_escape_n == 0:\n"
    "                    # Choose a random direction different from recent pattern\n"
    "                    _oe_dir = _rb_random.choice(acts_oe)\n"
    "                    _oe_escape_n = _OE_ESCAPE\n"
    "                    _oe_hashes.clear()\n"
    "                _oe_escape_n -= 1\n"
    "                self._pipeline_context.update({\n"
    "                    '_oe_hashes': _oe_hashes, '_oe_escape_n': _oe_escape_n, '_oe_dir': _oe_dir,\n"
    "                })\n"
    "                return _oe_dir, None, f'osc_escape:A{_oe_dir} n={_oe_escape_n}'\n"
    "            else:\n"
    "                # Normal navigation: use directional_sweep logic as base\n"
    "                _oe_dst = self._pipeline_context.get('_oe_dst', 0)\n"
    "                _oe_stall = self._pipeline_context.get('_oe_stall', 0)\n"
    "                _oe_prod = context.get('last_was_productive', True)\n"
    "                if not _oe_prod:\n"
    "                    _oe_stall += 1\n"
    "                else:\n"
    "                    _oe_stall = 0\n"
    "                if _oe_stall >= 2:\n"
    "                    _oe_dst = (_oe_dst + 1) % len(acts_oe)\n"
    "                    _oe_stall = 0\n"
    "                _oe_act = acts_oe[_oe_dst % len(acts_oe)]\n"
    "                self._pipeline_context.update({\n"
    "                    '_oe_hashes': _oe_hashes, '_oe_escape_n': _oe_escape_n,\n"
    "                    '_oe_dir': _oe_dir, '_oe_dst': _oe_dst, '_oe_stall': _oe_stall,\n"
    "                })\n"
    "                return _oe_act, None, f'osc_escape:sweep A{_oe_act} stall={_oe_stall}'\n"
    "\n"
    "        elif concept == 'click_navigate':\n"
    "            # Navigate using movement, but click ACTION6 at player center every 5 steps.\n"
    "            # Good for: dc22/bp35-style games where interact-on-overlap requires A6 click\n"
    "            # at the exact player position (pick-up, door-open, NPC-interact mechanics).\n"
    "            _CN_CLICK_FREQ = 5\n"
    "            if '_cn_steps' not in self._pipeline_context:\n"
    "                self._pipeline_context['_cn_steps']  = 0\n"
    "                self._pipeline_context['_cn_dir']    = (move_actions or [1])[0]\n"
    "                self._pipeline_context['_cn_stall']  = 0\n"
    "            _cn_steps = self._pipeline_context['_cn_steps'] + 1\n"
    "            self._pipeline_context['_cn_steps'] = _cn_steps\n"
    "            # Periodic click at estimated player center\n"
    "            if 6 in avail and _cn_steps % _CN_CLICK_FREQ == 0:\n"
    "                return 6, {'x': 32, 'y': 32}, f'click_nav:click at step={_cn_steps}'\n"
    "            # Navigation: directional_sweep logic\n"
    "            acts_cn = move_actions if move_actions else [a for a in avail if a != 6]\n"
    "            if not acts_cn:\n"
    "                return 6, {'x': 32, 'y': 32}, 'click_nav:click-only fallback'\n"
    "            _cn_dir   = self._pipeline_context['_cn_dir']\n"
    "            _cn_stall = self._pipeline_context['_cn_stall']\n"
    "            _cn_prod  = context.get('last_was_productive', True)\n"
    "            if not _cn_prod:\n"
    "                _cn_stall += 1\n"
    "            else:\n"
    "                _cn_stall = 0\n"
    "            if _cn_dir not in acts_cn or _cn_stall >= 2:\n"
    "                _cn_idx = acts_cn.index(_cn_dir) if _cn_dir in acts_cn else 0\n"
    "                _cn_dir = acts_cn[(_cn_idx + 1) % len(acts_cn)]\n"
    "                _cn_stall = 0\n"
    "            self._pipeline_context['_cn_dir']   = _cn_dir\n"
    "            self._pipeline_context['_cn_stall'] = _cn_stall\n"
    "            return _cn_dir, None, (\n"
    "                f'click_nav:A{_cn_dir} stall={_cn_stall} step={_cn_steps}')\n"
    "\n"
)

TARGET = "        # navigation / coverage / traversal_ordering / mixed_movement"

# ---------------------------------------------------------------------------
# Classifier fix: maze routing for re86/ar25/dc22/bp35 (has_click but useless)
# ---------------------------------------------------------------------------
OLD_MAZE_COND = (
    "        if (has_movement and not has_click and commit_cands\n"
    "                and n_eff_now == 0 and n_rul_now == 0):\n"
    "            # Blind movement + unconfirmed commit: lead with maze-traversal, keep\n"
    "            # sequence_commit as fallback so g50t/su15 still work.\n"
    "            _maze_prio = ['directional_sweep', 'wall_follower', 'momentum_probe']\n"
    "            _maze_prio = [c for c in _maze_prio if c not in cands]\n"
    "            cands = _maze_prio + cands"
)

NEW_MAZE_COND = (
    "        if (has_movement and n_eff_now == 0 and n_rul_now == 0\n"
    "                and not (behavioral.get('has_toggle') or behavioral.get('has_self_toggle'))):\n"
    "            # Broad maze/navigation routing: any movement game with no learned CausalMap\n"
    "            # data yet (n_eff=0, n_rul=0) and no confirmed toggle mechanics.\n"
    "            # Covers: re86/ar25/dc22/bp35 (has_click=True but A6 useless),\n"
    "            #         wa30/g50t (has commit action), and other novel nav games.\n"
    "            # greedy_productive tracks per-direction productivity -- great timer games.\n"
    "            # oscillation_escape prevents cycle-locking in any maze.\n"
    "            _maze_prio = ['greedy_productive', 'directional_sweep',\n"
    "                          'wall_follower', 'momentum_probe', 'oscillation_escape']\n"
    "            if commit_cands:\n"
    "                # Keep sequence_commit in cands as fallback for g50t/su15 style games\n"
    "                pass\n"
    "            _maze_prio = [c for c in _maze_prio if c not in cands]\n"
    "            cands = _maze_prio + cands"
)

# Also: add click_navigate for dc22/bp35 (movement + click, no commit, no toggle)
OLD_INTERACT = (
    "        if (has_movement and not has_click and commit_cands\n"
    "                and n_eff_now > 0 and 'interact_seek' not in cands):\n"
    "            _is_commit_avail = commit_cands[0]\n"
    "            # Only add interact_seek if we haven't already covered it\n"
    "            cands = ['interact_seek'] + cands"
)

NEW_INTERACT = (
    "        if (has_movement and commit_cands\n"
    "                and n_eff_now > 0 and 'interact_seek' not in cands):\n"
    "            # Movement + confirmed commit: interact_seek (navigate + press commit action).\n"
    "            _is_commit_avail = commit_cands[0]\n"
    "            cands = ['interact_seek'] + cands\n"
    "\n"
    "        # click_navigate: movement + A6 click, no commit action, no toggle mechanics.\n"
    "        # Good for dc22/bp35 where pick-up/interact triggers on A6 at player position.\n"
    "        if (has_movement and has_click and not commit_cands\n"
    "                and not behavioral.get('has_toggle') and not behavioral.get('has_self_toggle')\n"
    "                and n_coord <= 10\n"
    "                and 'click_navigate' not in cands):\n"
    "            cands = cands + ['click_navigate']"
)

# Also add greedy_productive and oscillation_escape to _LONG_PATH_CONCEPTS
OLD_LONG_PATH = (
    "            _LONG_PATH_CONCEPTS = {\n"
    "                'navigation', 'bfs_path',\n"
    "                # v71-v75 maze-traversal concepts: long-path games need 100-500 steps\n"
    "                'directional_sweep', 'wall_follower', 'momentum_probe',\n"
    "                'color_seek', 'score_directed_probe', 'action_repeat',\n"
    "     "
)
NEW_LONG_PATH = (
    "            _LONG_PATH_CONCEPTS = {\n"
    "                'navigation', 'bfs_path',\n"
    "                # v71-v78 maze-traversal concepts: long-path games need 100-500 steps\n"
    "                'directional_sweep', 'wall_follower', 'momentum_probe',\n"
    "                'color_seek', 'score_directed_probe', 'action_repeat',\n"
    "                'greedy_productive', 'oscillation_escape', 'click_navigate',\n"
    "     "
)

with open('bittertruth_ai_upload/competition_notebook_v2.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

cell = nb['cells'][11]
src = ''.join(cell.get('source', []))

# Apply all patches
assert TARGET in src, 'TARGET not found!'
assert OLD_MAZE_COND in src, f'OLD_MAZE_COND not found!'
assert OLD_INTERACT in src, f'OLD_INTERACT not found!'
assert OLD_LONG_PATH in src, f'OLD_LONG_PATH not found!'

src2 = src.replace(TARGET, NEW_CONCEPTS + TARGET, 1)
src2 = src2.replace(OLD_MAZE_COND, NEW_MAZE_COND, 1)
src2 = src2.replace(OLD_INTERACT, NEW_INTERACT, 1)
src2 = src2.replace(OLD_LONG_PATH, NEW_LONG_PATH, 1)

assert src2 != src, 'No changes made!'
print(f'Added {len(src2) - len(src)} chars')

nb['cells'][11]['source'] = [src2]
with open('bittertruth_ai_upload/competition_notebook_v2.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f)
print('Done')
