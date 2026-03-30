"""v85 patch: 6 neural-architecture-inspired concepts.

conv_scan     (CNN)       - Systematic sliding-window grid scan; moves in snake
                            pattern + clicks at each cell. Good for grid-click games.
spike_react   (SNN)       - Event-driven bursts: only act when frame delta crosses
                            threshold, refractory period between bursts.
temporal_diff (TD/RNN)    - Per-action cumulative score tracking; prefer actions
                            with highest historical reward (decaying average).
attention_seek(Attention) - Track pixel-change per quadrant; bias movement toward
                            highest-activity region of the frame.
recurrent_avoid(LSTM)     - Circular action-history buffer; detects repeating loops
                            and forces a break-out action.
reservoir_sample(ESN)     - Echo-state / reservoir: random concept switching based
                            on entropy of recent score signal.
"""
import json
import re
import sys

NOTEBOOK = 'bittertruth_ai_upload/competition_notebook_v2.ipynb'

# ---------------------------------------------------------------------------
# New concept implementations (indented for cell 11 / class body)
# ---------------------------------------------------------------------------

NEW_CONCEPTS = r"""
        elif concept == 'conv_scan':
            # CNN-inspired: systematic sliding-window grid scan.
            # Sweeps the play-area in a snake pattern, clicking A6 at each cell.
            # Useful for grid-click puzzles (BP35 graph nodes, FT09 variants, AR25).
            _CW = 4  # columns per row
            _CH = 4  # rows total -> 16 cells
            if '_cnn_cell' not in self._pipeline_context:
                self._pipeline_context['_cnn_cell']  = 0
                self._pipeline_context['_cnn_phase'] = 'click'
                self._pipeline_context['_cnn_nav']   = []
            _cnn_cell  = self._pipeline_context['_cnn_cell']
            _cnn_phase = self._pipeline_context['_cnn_phase']
            _cnn_nav   = list(self._pipeline_context['_cnn_nav'])
            _cnn_click = 6 if 6 in avail else (5 if 5 in avail else None)
            if _cnn_nav:
                _cnn_act = _cnn_nav.pop(0)
                _cnn_phase = 'click' if not _cnn_nav else 'navigate'
                self._pipeline_context.update({
                    '_cnn_cell': _cnn_cell, '_cnn_phase': _cnn_phase,
                    '_cnn_nav': _cnn_nav})
                return _cnn_act, None, f'conv_scan:nav A{_cnn_act} cell={_cnn_cell}'
            # Click at current cell, then plan navigation to next cell
            _cnn_cell_next = (_cnn_cell + 1) % (_CW * _CH)
            row_cur  = _cnn_cell % _CH
            col_cur  = _cnn_cell % _CW
            row_next = _cnn_cell_next % _CH
            col_next = _cnn_cell_next % _CW
            # Snake: even rows go right, odd rows go left
            if row_cur % 2 == 0:
                _h = [4] if col_next > col_cur else ([3] if col_next < col_cur else [])
            else:
                _h = [3] if col_next < col_cur else ([4] if col_next > col_cur else [])
            _v = [2] if row_next > row_cur else ([1] if row_next < row_cur else [])
            _cnn_nav = _h + _v
            self._pipeline_context.update({
                '_cnn_cell': _cnn_cell_next, '_cnn_phase': 'navigate',
                '_cnn_nav': _cnn_nav})
            if _cnn_click:
                return _cnn_click, None, f'conv_scan:click cell={_cnn_cell}'
            _fb = move_actions[0] if move_actions else avail[0]
            return _fb, None, f'conv_scan:no_click_fb A{_fb}'

        elif concept == 'spike_react':
            # SNN-inspired: event-driven action bursts.
            # Monitors frame pixel-delta; fires a burst when delta > threshold.
            # Refractory period suppresses further bursts for K steps.
            _SR_THRESH    = 0.04   # pixel-change fraction to trigger spike
            _SR_BURST     = 5      # actions per burst
            _SR_REFRACT   = 8      # idle steps after burst
            if '_sr_phase' not in self._pipeline_context:
                self._pipeline_context['_sr_phase']    = 'idle'
                self._pipeline_context['_sr_burst_n']  = 0
                self._pipeline_context['_sr_refract_n']= 0
                self._pipeline_context['_sr_last_dir'] = 0
                self._pipeline_context['_sr_click_n']  = 0
            _sr_phase    = self._pipeline_context['_sr_phase']
            _sr_burst_n  = self._pipeline_context['_sr_burst_n']
            _sr_refract  = self._pipeline_context['_sr_refract_n']
            _sr_last_dir = self._pipeline_context['_sr_last_dir']
            _sr_click_n  = self._pipeline_context['_sr_click_n']
            # Estimate frame delta from context
            _sr_frame = context.get('frame') if context else None
            _sr_delta = 0.0
            if _sr_frame is not None:
                import numpy as _np
                _f = _np.array(_sr_frame, dtype=float)
                if _f.ndim == 3: _f = _f[0]
                _prev = self._pipeline_context.get('_sr_prev_frame')
                if _prev is not None:
                    _sr_delta = float(_np.mean(_np.abs(_f - _prev))) / 255.0
                self._pipeline_context['_sr_prev_frame'] = _f.copy()
            _sr_click = 6 if 6 in avail else (5 if 5 in avail else None)
            _sr_dirs  = move_actions or [1, 2, 3, 4]
            if _sr_phase == 'refractory':
                _sr_refract += 1
                if _sr_refract >= _SR_REFRACT:
                    _sr_phase = 'idle'
                    _sr_refract = 0
                self._pipeline_context.update({
                    '_sr_phase': _sr_phase, '_sr_refract_n': _sr_refract})
                # During refractory: small probe click
                _fb = _sr_click or _sr_dirs[0]
                return _fb, None, f'spike_react:refractory {_sr_refract}/{_SR_REFRACT}'
            if _sr_phase == 'burst':
                _sr_burst_n += 1
                if _sr_burst_n >= _SR_BURST:
                    _sr_phase  = 'refractory'
                    _sr_burst_n = 0
                # Alternate: click then move in triggered direction
                if _sr_burst_n % 2 == 0 and _sr_click:
                    _sr_act = _sr_click
                else:
                    _sr_act = _sr_dirs[_sr_last_dir % len(_sr_dirs)]
                self._pipeline_context.update({
                    '_sr_phase': _sr_phase, '_sr_burst_n': _sr_burst_n})
                return _sr_act, None, f'spike_react:burst {_sr_burst_n}/{_SR_BURST}'
            # idle: check for spike
            if _sr_delta >= _SR_THRESH:
                _sr_phase = 'burst'
                _sr_burst_n = 0
                _sr_last_dir = (_sr_last_dir + 1) % len(_sr_dirs)
                self._pipeline_context.update({
                    '_sr_phase': _sr_phase, '_sr_burst_n': _sr_burst_n,
                    '_sr_last_dir': _sr_last_dir})
                _sr_act = _sr_dirs[_sr_last_dir % len(_sr_dirs)]
                return _sr_act, None, f'spike_react:spike d={_sr_delta:.3f}'
            # No spike: periodic probe click
            _sr_click_n += 1
            self._pipeline_context['_sr_click_n'] = _sr_click_n
            if _sr_click and _sr_click_n % 4 == 0:
                return _sr_click, None, f'spike_react:probe_click d={_sr_delta:.3f}'
            _sr_act = _sr_dirs[_sr_last_dir % len(_sr_dirs)]
            return _sr_act, None, f'spike_react:idle_move A{_sr_act}'

        elif concept == 'temporal_diff':
            # TD/RNN-inspired: per-action cumulative reward tracking.
            # Maintains decaying average score-delta per action.
            # Selects action with highest historical reward.
            _TD_DECAY  = 0.85   # exponential decay per step
            _TD_EXPLORE= 6      # force random explore every N steps
            if '_td_Q' not in self._pipeline_context:
                self._pipeline_context['_td_Q']     = {}  # action -> Q-value
                self._pipeline_context['_td_last']  = None
                self._pipeline_context['_td_steps'] = 0
            _td_Q     = self._pipeline_context['_td_Q']
            _td_last  = self._pipeline_context['_td_last']
            _td_steps = self._pipeline_context['_td_steps'] + 1
            _td_score = float(context.get('score_delta', 0) or 0)
            # Update Q for last action
            if _td_last is not None:
                _old = _td_Q.get(_td_last, 0.0)
                _td_Q[_td_last] = _TD_DECAY * _old + (1 - _TD_DECAY) * _td_score
            # Decay all Q-values
            for _a in list(_td_Q):
                _td_Q[_a] *= _TD_DECAY
            # Select best action (epsilon-greedy: explore every N steps)
            if _td_steps % _TD_EXPLORE == 0 or not _td_Q:
                import random as _rnd
                _td_act = _rnd.choice(avail)
                _cf = f'temporal_diff:explore A{_td_act}'
            else:
                # Best Q among available actions
                _td_act = max(avail, key=lambda a: _td_Q.get(a, 0.0))
                _cf = f'temporal_diff:exploit A{_td_act} Q={_td_Q.get(_td_act,0):.3f}'
            self._pipeline_context.update({
                '_td_Q': _td_Q, '_td_last': _td_act, '_td_steps': _td_steps})
            return _td_act, None, _cf

        elif concept == 'attention_seek':
            # Attention-inspired: track pixel-change per frame quadrant.
            # Bias movement toward the highest-activity (most-changing) quadrant.
            # Useful for games where the interesting region shifts (DC22, re86).
            _AS_HISTORY = 6  # frames to integrate
            if '_as_Q' not in self._pipeline_context:
                self._pipeline_context['_as_Q'] = [0.0, 0.0, 0.0, 0.0]  # TL,TR,BL,BR
                self._pipeline_context['_as_prev'] = None
                self._pipeline_context['_as_steps'] = 0
            _as_Q     = list(self._pipeline_context['_as_Q'])
            _as_prev  = self._pipeline_context['_as_prev']
            _as_steps = self._pipeline_context['_as_steps'] + 1
            _as_frame = context.get('frame') if context else None
            if _as_frame is not None:
                import numpy as _np
                _f = _np.array(_as_frame, dtype=float)
                if _f.ndim == 3: _f = _f[0]
                H, W = _f.shape
                Hh, Wh = H // 2, W // 2
                if _as_prev is not None:
                    _d = _np.abs(_f - _as_prev)
                    _as_Q[0] = 0.85 * _as_Q[0] + float(_np.mean(_d[:Hh, :Wh]))
                    _as_Q[1] = 0.85 * _as_Q[1] + float(_np.mean(_d[:Hh, Wh:]))
                    _as_Q[2] = 0.85 * _as_Q[2] + float(_np.mean(_d[Hh:, :Wh]))
                    _as_Q[3] = 0.85 * _as_Q[3] + float(_np.mean(_d[Hh:, Wh:]))
                self._pipeline_context['_as_prev'] = _f.copy()
            # Map quadrant to action: TL→up+left, TR→up+right, BL→down+left, BR→down+right
            _as_quad_acts = [[1, 3], [1, 4], [2, 3], [2, 4]]
            _as_best_q = int(_np.argmax(_as_Q)) if sum(_as_Q) > 0 else (_as_steps % 4)
            _as_cands  = [a for a in _as_quad_acts[_as_best_q] if a in avail]
            if not _as_cands:
                _as_cands = move_actions or avail
            _as_act = _as_cands[_as_steps % len(_as_cands)]
            # Occasionally click at focus region
            _as_click = 6 if 6 in avail else (5 if 5 in avail else None)
            if _as_click and _as_steps % 5 == 0:
                _as_act = _as_click
            self._pipeline_context.update({
                '_as_Q': _as_Q, '_as_steps': _as_steps})
            return _as_act, None, (
                f'attention_seek:q={_as_best_q} Q={[f"{q:.1f}" for q in _as_Q]}')

        elif concept == 'recurrent_avoid':
            # LSTM-inspired: circular action-history buffer.
            # Detects repeating action loops and breaks out with a novel action.
            # Useful for any game prone to oscillation or deadlock.
            _RA_WINDOW  = 8   # look-back window for loop detection
            _RA_MIN_REP = 3   # minimum repeat length to classify as loop
            if '_ra_hist' not in self._pipeline_context:
                self._pipeline_context['_ra_hist']      = []
                self._pipeline_context['_ra_breakout_n']= 0
            _ra_hist = list(self._pipeline_context['_ra_hist'])
            _ra_bo_n = self._pipeline_context['_ra_breakout_n']
            # Detect loop: does the last _RA_MIN_REP actions repeat?
            _ra_loop = False
            if len(_ra_hist) >= _RA_MIN_REP * 2:
                _tail = _ra_hist[-_RA_MIN_REP:]
                _prev = _ra_hist[-_RA_MIN_REP*2:-_RA_MIN_REP]
                if _tail == _prev:
                    _ra_loop = True
            if _ra_loop:
                _ra_bo_n += 1
                # Break out: pick action NOT in recent tail
                _ra_recent = set(_ra_hist[-_RA_MIN_REP:])
                _ra_novel  = [a for a in avail if a not in _ra_recent]
                if not _ra_novel:
                    _ra_novel = avail
                import random as _rnd
                _ra_act = _rnd.choice(_ra_novel)
                _cf = f'recurrent_avoid:breakout A{_ra_act} bo={_ra_bo_n}'
            else:
                # Normal operation: prefer last-positive-score action else cycle moves
                _ra_last_pos = self._pipeline_context.get('_ra_last_pos_act')
                _ra_score = float(context.get('score_delta', 0) or 0)
                if _ra_score > 0.01:
                    self._pipeline_context['_ra_last_pos_act'] = (
                        _ra_hist[-1] if _ra_hist else avail[0])
                if _ra_last_pos and _ra_last_pos in avail and (
                        len(_ra_hist) % 4 != 0):
                    _ra_act = _ra_last_pos
                else:
                    _ra_act = (move_actions or avail)[len(_ra_hist) % len(
                        move_actions or avail)]
                _cf = f'recurrent_avoid:normal A{_ra_act}'
            _ra_hist.append(_ra_act)
            if len(_ra_hist) > _RA_WINDOW * 4:
                _ra_hist = _ra_hist[-_RA_WINDOW * 2:]
            self._pipeline_context.update({
                '_ra_hist': _ra_hist, '_ra_breakout_n': _ra_bo_n})
            return _ra_act, None, _cf

        elif concept == 'reservoir_sample':
            # Echo-state / reservoir network: random concept-internal switching.
            # Maintains a pool of micro-strategies, samples based on recent entropy
            # of score signal. High entropy -> explore; low entropy -> commit.
            _RS_POOL = ['move_rnd', 'click_all', 'oscillate', 'bfs_hint']
            _RS_WIN  = 10   # scoring window
            _RS_COMMIT_THRESH = 0.8  # high score consistency -> commit
            if '_rs_pool_idx' not in self._pipeline_context:
                self._pipeline_context['_rs_pool_idx']   = 0
                self._pipeline_context['_rs_scores']     = []
                self._pipeline_context['_rs_steps']      = 0
                self._pipeline_context['_rs_commit_act'] = None
            _rs_pi      = self._pipeline_context['_rs_pool_idx']
            _rs_scores  = list(self._pipeline_context['_rs_scores'])
            _rs_steps   = self._pipeline_context['_rs_steps'] + 1
            _rs_commit  = self._pipeline_context['_rs_commit_act']
            _rs_score   = float(context.get('score_delta', 0) or 0)
            _rs_scores.append(_rs_score)
            if len(_rs_scores) > _RS_WIN:
                _rs_scores = _rs_scores[-_RS_WIN:]
            # Entropy of score signal (positive / negative / zero mix)
            _rs_pos = sum(1 for s in _rs_scores if s > 0.01)
            _rs_consistency = _rs_pos / max(1, len(_rs_scores))
            _rs_click = 6 if 6 in avail else (5 if 5 in avail else None)
            _rs_dirs  = move_actions or [1, 2, 3, 4]
            if _rs_consistency >= _RS_COMMIT_THRESH and _rs_commit:
                # Exploit committed action
                _rs_act = _rs_commit if _rs_commit in avail else _rs_dirs[0]
                _cf = f'reservoir:commit A{_rs_act} c={_rs_consistency:.2f}'
            else:
                # Sample from pool
                _rs_strat = _RS_POOL[_rs_pi % len(_RS_POOL)]
                if _rs_strat == 'move_rnd':
                    import random as _rnd
                    _rs_act = _rnd.choice(_rs_dirs)
                elif _rs_strat == 'click_all':
                    _rs_act = _rs_click or _rs_dirs[0]
                elif _rs_strat == 'oscillate':
                    _rs_act = _rs_dirs[_rs_steps % 2]  # back-forth
                else:  # bfs_hint
                    _rs_act = _rs_dirs[_rs_steps % len(_rs_dirs)]
                # Switch pool strategy if no improvement
                if len(_rs_scores) >= _RS_WIN and _rs_consistency < 0.2:
                    _rs_pi = (_rs_pi + 1) % len(_RS_POOL)
                _rs_commit = _rs_act
                _cf = f'reservoir:{_rs_strat} A{_rs_act} c={_rs_consistency:.2f}'
            self._pipeline_context.update({
                '_rs_pool_idx': _rs_pi, '_rs_scores': _rs_scores,
                '_rs_steps': _rs_steps, '_rs_commit_act': _rs_commit})
            return _rs_act, None, _cf

"""

# ---------------------------------------------------------------------------
# Classifier additions (insert into interact cands + maze_prio + LONG_PATH)
# ---------------------------------------------------------------------------

OLD_INTERACT_CANDS = (
    "cands = ['interact_seek', 'shoot_and_move', 'position_commit',\n"
    "                     'momentum_build', 'dodge_reactive', 'terrain_modify',\n"
    "                     'multi_target_sequence'] + cands"
)
NEW_INTERACT_CANDS = (
    "cands = ['interact_seek', 'shoot_and_move', 'position_commit',\n"
    "                     'momentum_build', 'dodge_reactive', 'terrain_modify',\n"
    "                     'multi_target_sequence', 'spike_react',\n"
    "                     'attention_seek'] + cands"
)

OLD_MAZE_PRIO = (
    "'gravity_platformer', 'racing_steer', 'physics_probe',\n"
    "                          'stealth_patrol_wait', 'phase_transition_detect']"
)
NEW_MAZE_PRIO = (
    "'gravity_platformer', 'racing_steer', 'physics_probe',\n"
    "                          'stealth_patrol_wait', 'phase_transition_detect',\n"
    "                          'recurrent_avoid', 'conv_scan']"
)

OLD_LONG_PATH = (
    "'multi_target_sequence', 'stealth_patrol_wait', 'phase_transition_detect',\n"
    "                'gravity_platformer', 'shoot_and_move', 'racing_steer',\n"
    "                'dodge_reactive', 'pursuit_evade', 'stealth_patrol_wait',\n"
    "                'physics_probe',\n"
    "            }"
)
NEW_LONG_PATH = (
    "'multi_target_sequence', 'stealth_patrol_wait', 'phase_transition_detect',\n"
    "                'gravity_platformer', 'shoot_and_move', 'racing_steer',\n"
    "                'dodge_reactive', 'pursuit_evade', 'stealth_patrol_wait',\n"
    "                'physics_probe',\n"
    "                # v85 neural-arch concepts\n"
    "                'conv_scan', 'spike_react', 'temporal_diff',\n"
    "                'attention_seek', 'recurrent_avoid', 'reservoir_sample',\n"
    "            }"
)

TARGET = "        # navigation / coverage / traversal_ordering / mixed_movement"
INSERTION = NEW_CONCEPTS + "        # navigation / coverage / traversal_ordering / mixed_movement"

nb = json.load(open(NOTEBOOK))
cell = nb['cells'][11]
src = ''.join(cell['source'])

assert TARGET in src, "TARGET marker not found!"
assert OLD_INTERACT_CANDS in src, "OLD_INTERACT_CANDS not found!"
assert OLD_MAZE_PRIO in src, "OLD_MAZE_PRIO not found!"
assert OLD_LONG_PATH in src, "OLD_LONG_PATH not found!"

src = src.replace(TARGET, INSERTION, 1)
src = src.replace(OLD_INTERACT_CANDS, NEW_INTERACT_CANDS, 1)
src = src.replace(OLD_MAZE_PRIO, NEW_MAZE_PRIO, 1)
src = src.replace(OLD_LONG_PATH, NEW_LONG_PATH, 1)

# Version bump: first line comment
src = src.replace('# -- v76: ConceptRungBridge', '# -- v85: ConceptRungBridge', 1)

# Verify concept count
concepts = re.findall(r"elif concept == '(\w+)'", src)
print(f"Total concepts after patch: {len(concepts)}")
print("New:", [c for c in concepts if c in [
    'conv_scan', 'spike_react', 'temporal_diff',
    'attention_seek', 'recurrent_avoid', 'reservoir_sample']])

nb['cells'][11]['source'] = src
json.dump(nb, open(NOTEBOOK, 'w'), indent=1)
print("Patch applied.")
