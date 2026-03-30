"""v86 patch: 3 targeted concepts from gamelist gap analysis.

frame_punish   (Fighting) - Stores known button sequences; fires combo at
                            opponent recovery windows. Handles SF4/MK/Bayonetta.
objective_chase(Open-World)- Detects HUD directional change; moves toward highest-
                            delta edge of frame (quest-arrow / minimap following).
risk_assess    (Roguelike) - Tracks score-delta variance as a danger proxy; backs
                            off and waits when variance spikes (Spelunky/Returnal).
"""
import json
import re

NOTEBOOK = 'bittertruth_ai_upload/competition_notebook_v2.ipynb'

NEW_CONCEPTS = r"""
        elif concept == 'frame_punish':
            # Fighting-game inspired: build a combo dictionary from short
            # exploratory sequences, then replay the best-scoring one.
            # Detects opponent "recovery window" via sudden score_delta spike,
            # then fires the stored combo immediately.
            _FP_EXPLORE_LEN = 4   # length of random combo to try
            _FP_COMBO_CAP   = 8   # store top N combos
            _FP_BURST_STEPS = 6   # steps to execute stored combo before re-eval
            if '_fp_combos' not in self._pipeline_context:
                self._pipeline_context['_fp_combos']    = {}   # seq_tuple -> best_score
                self._pipeline_context['_fp_current']   = []   # current attempt seq
                self._pipeline_context['_fp_burst']     = []   # executing this combo
                self._pipeline_context['_fp_seq_score'] = 0.0
                self._pipeline_context['_fp_steps']     = 0
            _fp_combos    = self._pipeline_context['_fp_combos']
            _fp_current   = list(self._pipeline_context['_fp_current'])
            _fp_burst     = list(self._pipeline_context['_fp_burst'])
            _fp_seq_score = self._pipeline_context['_fp_seq_score']
            _fp_steps     = self._pipeline_context['_fp_steps'] + 1
            _fp_score     = float(context.get('score_delta', 0) or 0)
            _fp_seq_score += _fp_score
            # If we have a combo bursting, execute it
            if _fp_burst:
                _fp_act = _fp_burst.pop(0)
                self._pipeline_context.update({
                    '_fp_burst': _fp_burst, '_fp_steps': _fp_steps,
                    '_fp_seq_score': _fp_seq_score})
                return _fp_act, None, f'frame_punish:burst A{_fp_act} left={len(_fp_burst)}'
            # Record current sequence result
            if _fp_current and len(_fp_current) >= _FP_EXPLORE_LEN:
                _fp_key = tuple(_fp_current)
                _old = _fp_combos.get(_fp_key, -999)
                if _fp_seq_score > _old:
                    _fp_combos[_fp_key] = _fp_seq_score
                # Prune to top N
                if len(_fp_combos) > _FP_COMBO_CAP:
                    _fp_combos = dict(sorted(
                        _fp_combos.items(), key=lambda x: -x[1])[:_FP_COMBO_CAP])
                _fp_current   = []
                _fp_seq_score = 0.0
            # Spike detected: fire best known combo
            if _fp_score > 0.05 and _fp_combos:
                _best = max(_fp_combos, key=lambda k: _fp_combos[k])
                _fp_burst = list(_best)
                self._pipeline_context.update({
                    '_fp_combos': _fp_combos, '_fp_burst': _fp_burst,
                    '_fp_current': [], '_fp_seq_score': 0.0, '_fp_steps': _fp_steps})
                _fp_act = _fp_burst.pop(0)
                return _fp_act, None, f'frame_punish:best_combo A{_fp_act}'
            # Explore: build random combo
            import random as _rnd
            _fp_act = _rnd.choice(avail)
            _fp_current.append(_fp_act)
            self._pipeline_context.update({
                '_fp_combos': _fp_combos, '_fp_current': _fp_current,
                '_fp_seq_score': _fp_seq_score, '_fp_steps': _fp_steps})
            return _fp_act, None, f'frame_punish:explore A{_fp_act} seq_len={len(_fp_current)}'

        elif concept == 'objective_chase':
            # Open-world / quest-following inspired: detect HUD directional cues.
            # Measures pixel-change along each edge strip of the frame — the edge
            # with highest cumulative change indicates the quest arrow / minimap
            # direction.  Moves toward that edge.
            _OC_EDGE_W    = 8    # edge strip width in pixels
            _OC_DECAY     = 0.80
            _OC_COMMIT    = 5    # steps to commit to a direction before re-eval
            if '_oc_edge_Q' not in self._pipeline_context:
                self._pipeline_context['_oc_edge_Q']   = [0.0]*4  # top,bot,left,right
                self._pipeline_context['_oc_prev']     = None
                self._pipeline_context['_oc_dir']      = 0
                self._pipeline_context['_oc_commit_n'] = 0
                self._pipeline_context['_oc_steps']    = 0
            _oc_Q       = list(self._pipeline_context['_oc_edge_Q'])
            _oc_prev    = self._pipeline_context['_oc_prev']
            _oc_dir     = self._pipeline_context['_oc_dir']
            _oc_commit  = self._pipeline_context['_oc_commit_n']
            _oc_steps   = self._pipeline_context['_oc_steps'] + 1
            _oc_frame   = context.get('frame') if context else None
            if _oc_frame is not None:
                import numpy as _np
                _f = _np.array(_oc_frame, dtype=float)
                if _f.ndim == 3: _f = _f[0]
                H, W = _f.shape
                W8, H8 = min(_OC_EDGE_W, W//4), min(_OC_EDGE_W, H//4)
                if _oc_prev is not None:
                    _d = _np.abs(_f - _oc_prev)
                    _oc_Q[0] = _OC_DECAY * _oc_Q[0] + float(_np.mean(_d[:H8, :]))    # top
                    _oc_Q[1] = _OC_DECAY * _oc_Q[1] + float(_np.mean(_d[-H8:, :]))   # bot
                    _oc_Q[2] = _OC_DECAY * _oc_Q[2] + float(_np.mean(_d[:, :W8]))    # left
                    _oc_Q[3] = _OC_DECAY * _oc_Q[3] + float(_np.mean(_d[:, -W8:]))   # right
                self._pipeline_context['_oc_prev'] = _f.copy()
            # Map edge to action: top=A1, bot=A2, left=A3, right=A4
            _oc_edge_acts = [1, 2, 3, 4]
            _oc_commit += 1
            if _oc_commit >= _OC_COMMIT:
                import numpy as _np2
                _oc_dir    = int(_np2.argmax(_oc_Q)) if sum(_oc_Q) > 0 else (_oc_steps % 4)
                _oc_commit = 0
            _oc_act = _oc_edge_acts[_oc_dir]
            if _oc_act not in avail:
                _oc_act = (move_actions or avail)[0]
            # Occasionally fire click at the active edge region
            _oc_click = 6 if 6 in avail else (5 if 5 in avail else None)
            if _oc_click and _oc_steps % 7 == 0:
                _oc_act = _oc_click
            self._pipeline_context.update({
                '_oc_edge_Q': _oc_Q, '_oc_dir': _oc_dir,
                '_oc_commit_n': _oc_commit, '_oc_steps': _oc_steps})
            return _oc_act, None, (
                f'objective_chase:dir={_oc_dir} Q={[f"{q:.1f}" for q in _oc_Q]}')

        elif concept == 'risk_assess':
            # Roguelike-inspired: use score-delta variance as a danger proxy.
            # When variance spikes (erratic reward signal = combat / hazard),
            # switches to defensive mode: back off, wait, then cautiously re-probe.
            _RA2_WIN      = 12   # variance window
            _RA2_THRESH   = 0.03 # variance threshold for danger
            _RA2_SAFE_WIN = 6    # consecutive safe steps before re-engage
            if '_ra2_hist' not in self._pipeline_context:
                self._pipeline_context['_ra2_hist']    = []
                self._pipeline_context['_ra2_mode']    = 'explore'
                self._pipeline_context['_ra2_safe_n']  = 0
                self._pipeline_context['_ra2_retreat'] = 0
                self._pipeline_context['_ra2_last_dir']= 0
            _ra2_hist    = list(self._pipeline_context['_ra2_hist'])
            _ra2_mode    = self._pipeline_context['_ra2_mode']
            _ra2_safe_n  = self._pipeline_context['_ra2_safe_n']
            _ra2_retreat = self._pipeline_context['_ra2_retreat']
            _ra2_last_dir= self._pipeline_context['_ra2_last_dir']
            _ra2_score   = float(context.get('score_delta', 0) or 0)
            _ra2_hist.append(_ra2_score)
            if len(_ra2_hist) > _RA2_WIN:
                _ra2_hist = _ra2_hist[-_RA2_WIN:]
            # Compute variance
            _ra2_n    = len(_ra2_hist)
            _ra2_mean = sum(_ra2_hist) / max(1, _ra2_n)
            _ra2_var  = sum((s - _ra2_mean)**2 for s in _ra2_hist) / max(1, _ra2_n)
            _ra2_dirs = move_actions or [1, 2, 3, 4]
            _ra2_click = 6 if 6 in avail else (5 if 5 in avail else None)
            # Reverse direction map for retreat
            _ra2_rev = {1: 2, 2: 1, 3: 4, 4: 3}
            if _ra2_mode == 'danger':
                # Back off: move in reverse of last direction
                _ra2_safe_n = _ra2_safe_n + 1 if _ra2_var < _RA2_THRESH else 0
                if _ra2_safe_n >= _RA2_SAFE_WIN:
                    _ra2_mode   = 'explore'
                    _ra2_safe_n = 0
                _ra2_retreat += 1
                _ra2_act = _ra2_rev.get(_ra2_last_dir, _ra2_dirs[0])
                if _ra2_act not in avail:
                    _ra2_act = _ra2_dirs[0]
                self._pipeline_context.update({
                    '_ra2_hist': _ra2_hist, '_ra2_mode': _ra2_mode,
                    '_ra2_safe_n': _ra2_safe_n, '_ra2_retreat': _ra2_retreat,
                    '_ra2_last_dir': _ra2_act})
                return _ra2_act, None, (
                    f'risk_assess:danger var={_ra2_var:.4f} safe={_ra2_safe_n}')
            else:
                # Explore: normal BFS-style movement
                if _ra2_var >= _RA2_THRESH and _ra2_n >= 4:
                    _ra2_mode   = 'danger'
                    _ra2_safe_n = 0
                _ra2_step = sum(1 for _ in _ra2_hist)
                _ra2_act = _ra2_dirs[_ra2_step % len(_ra2_dirs)]
                if _ra2_click and _ra2_step % 6 == 0:
                    _ra2_act = _ra2_click
                self._pipeline_context.update({
                    '_ra2_hist': _ra2_hist, '_ra2_mode': _ra2_mode,
                    '_ra2_safe_n': _ra2_safe_n, '_ra2_last_dir': _ra2_act})
                return _ra2_act, None, (
                    f'risk_assess:explore var={_ra2_var:.4f} mode={_ra2_mode}')

"""

# ---------------------------------------------------------------------------
# Classifier updates
# ---------------------------------------------------------------------------

# interact cands: add frame_punish (combo games have commits + movement)
OLD_INTERACT = (
    "cands = ['interact_seek', 'shoot_and_move', 'position_commit',\n"
    "                     'momentum_build', 'dodge_reactive', 'terrain_modify',\n"
    "                     'multi_target_sequence', 'spike_react',\n"
    "                     'attention_seek'] + cands"
)
NEW_INTERACT = (
    "cands = ['interact_seek', 'shoot_and_move', 'position_commit',\n"
    "                     'momentum_build', 'dodge_reactive', 'terrain_modify',\n"
    "                     'multi_target_sequence', 'spike_react',\n"
    "                     'attention_seek', 'frame_punish'] + cands"
)

# maze prio: add risk_assess + objective_chase (open-world nav + danger-aware)
OLD_MAZE = (
    "'gravity_platformer', 'racing_steer', 'physics_probe',\n"
    "                          'stealth_patrol_wait', 'phase_transition_detect',\n"
    "                          'recurrent_avoid', 'conv_scan']"
)
NEW_MAZE = (
    "'gravity_platformer', 'racing_steer', 'physics_probe',\n"
    "                          'stealth_patrol_wait', 'phase_transition_detect',\n"
    "                          'recurrent_avoid', 'conv_scan',\n"
    "                          'objective_chase', 'risk_assess']"
)

# LONG_PATH: all 3 new concepts need sustained movement budgets
OLD_LONG = (
    "                # v85 neural-arch concepts\n"
    "                'conv_scan', 'spike_react', 'temporal_diff',\n"
    "                'attention_seek', 'recurrent_avoid', 'reservoir_sample',\n"
    "            }"
)
NEW_LONG = (
    "                # v85 neural-arch concepts\n"
    "                'conv_scan', 'spike_react', 'temporal_diff',\n"
    "                'attention_seek', 'recurrent_avoid', 'reservoir_sample',\n"
    "                # v86 gamelist gap concepts\n"
    "                'frame_punish', 'objective_chase', 'risk_assess',\n"
    "            }"
)

TARGET = "        # navigation / coverage / traversal_ordering / mixed_movement"
INSERTION = NEW_CONCEPTS + "        # navigation / coverage / traversal_ordering / mixed_movement"

nb = json.load(open(NOTEBOOK))
cell = nb['cells'][11]
src = ''.join(cell['source'])

assert TARGET in src,        "TARGET marker not found"
assert OLD_INTERACT in src,  "OLD_INTERACT not found"
assert OLD_MAZE in src,      "OLD_MAZE not found"
assert OLD_LONG in src,      "OLD_LONG not found"

src = src.replace(TARGET, INSERTION, 1)
src = src.replace(OLD_INTERACT, NEW_INTERACT, 1)
src = src.replace(OLD_MAZE, NEW_MAZE, 1)
src = src.replace(OLD_LONG, NEW_LONG, 1)

# Version bump
src = src.replace('# -- v85: ConceptRungBridge', '# -- v86: ConceptRungBridge', 1)

import re

concepts = re.findall(r"elif concept == '(\w+)'", src)
print(f"Total concepts: {len(concepts)}")
print("New:", [c for c in concepts if c in [
    'frame_punish', 'objective_chase', 'risk_assess']])

nb['cells'][11]['source'] = src
json.dump(nb, open(NOTEBOOK, 'w'), indent=1)
print("Patch applied.")
