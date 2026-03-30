"""v87 patch: Private-eval performance overhaul.

4 systemic changes + 2 new concepts:

1. Stagnation 30 -> 10  (cycle 5 concepts in a 50-step budget instead of 2)
2. Bootstrap probe       (first len(avail)+1 steps: try every action once, record
                          frame-delta per action, reclassify, raise stagnation if
                          movement-productive)
3. UCB bandit over concepts  (signal_concept_failed picks next concept via UCB1
                              instead of blind graph rotation)
4. Count-based curiosity     (track (action, coarse_frame_hash)->count; update
                              per-action Q-values each step for ucb_explore)

New concepts:
  ucb_explore  - UCB1 over single actions using observed Q-values (cheap MCTS leaf)
  vmcts        - Virtual MCTS: builds action-sequence tree from actual gameplay;
                 selection via UCB, backprop reward after every step.
                 No forward model needed -- the game IS the simulator.
"""
import json
import re

NOTEBOOK = 'bittertruth_ai_upload/competition_notebook_v2.ipynb'

# ===========================================================================
# 1. Stagnation 30 -> 10
# ===========================================================================
OLD_STAG = "        self._stagnation_limit      = 30"
NEW_STAG = "        self._stagnation_limit      = 10"

# ===========================================================================
# 2. New state variables in __init__
# ===========================================================================
OLD_INIT_END = (
    "        # Pipeline context: shared state across concept rotations within one game.\n"
    "        # Persists through signal_concept_failed() ??? only cleared on level gain.\n"
    "        # Stores: cell_states (read_grid), _sat_targets (constraint_sat),\n"
    "        #         _bfs_path (bfs_path), _hc_scores (hill_climb), etc.\n"
    "        self._pipeline_context      = {}"
)
NEW_INIT_END = (
    "        # Pipeline context: shared state across concept rotations within one game.\n"
    "        # Persists through signal_concept_failed() ??? only cleared on level gain.\n"
    "        # Stores: cell_states (read_grid), _sat_targets (constraint_sat),\n"
    "        #         _bfs_path (bfs_path), _hc_scores (hill_climb), etc.\n"
    "        self._pipeline_context      = {}\n"
    "\n"
    "        # v87: UCB bandit over concepts\n"
    "        self._concept_ucb        = {}  # concept -> {'n': int, 'r': float}\n"
    "        self._ucb_concept_total  = 0\n"
    "        # v87: per-action Q-values and visit counts (count-based curiosity)\n"
    "        self._action_Q           = {}  # action_id -> ewma reward\n"
    "        self._action_visit_counts= {}  # (action_id, frame_hash_coarse) -> n\n"
    "        self._action_Q_total     = 0\n"
    "        # v87: bootstrap probe state\n"
    "        self._bootstrap_done     = False\n"
    "        self._bootstrap_seq      = []\n"
    "        self._bootstrap_prev_frame = None\n"
    "        self._bootstrap_frame_deltas = {}\n"
    "        self._bootstrap_last_act = None"
)

# ===========================================================================
# 3. Bootstrap probe at start of decide()
#    Insert right before: # Classify concept on first call
# ===========================================================================
OLD_CLASSIFY_COMMENT = "        # Classify concept on first call\n        if self._current_concept is None:"
NEW_CLASSIFY_COMMENT = """\
        # ── v87 Bootstrap probe: try every available action once before committing ──
        if not self._bootstrap_done:
            if not self._bootstrap_seq:
                self._bootstrap_seq = list(sorted(set(avail)))
            _bsf = context.get('frame') if context else None
            if self._bootstrap_last_act is not None and _bsf is not None:
                _bprev = self._bootstrap_prev_frame
                if _bprev is not None:
                    try:
                        import numpy as _np
                        _ff = _np.array(_bsf,   dtype=float); _ff = _ff[0] if _ff.ndim == 3 else _ff
                        _pp = _np.array(_bprev, dtype=float); _pp = _pp[0] if _pp.ndim == 3 else _pp
                        _bd = float(_np.mean(_np.abs(_ff - _pp))) / 255.0
                        self._bootstrap_frame_deltas[self._bootstrap_last_act] = _bd
                    except Exception:
                        pass
            self._bootstrap_prev_frame = _bsf
            if self._bootstrap_seq:
                _bs_act = self._bootstrap_seq.pop(0)
                self._bootstrap_last_act = _bs_act
                if not self._bootstrap_seq:
                    self._bootstrap_done = True
                    _productive = [a for a, d in self._bootstrap_frame_deltas.items()
                                   if d > 0.015]
                    _move_prod  = [a for a in _productive if a in {1, 2, 3, 4}]
                    _click_prod = [a for a in _productive if a == 6]
                    if _move_prod:
                        self._stagnation_limit = max(self._stagnation_limit, 20)
                    if self.verbose:
                        print(f"  [bridge:{self.game_id}] BOOTSTRAP "
                              f"deltas={self._bootstrap_frame_deltas} "
                              f"productive={_productive}")
                return _bs_act, None, f'bootstrap:probe A{_bs_act}'

        # Classify concept on first call
        if self._current_concept is None:\
"""

# ===========================================================================
# 4. After action is returned, update action Q-values + visit counts
#    Anchor: the line after action_num/action_data/reason are set
# ===========================================================================
OLD_ACTION_SELECTED = (
    "        action_num, action_data, reason = self._get_action_for_concept(\n"
    "            self._current_concept, context)\n"
    "        self._concept_steps += 1\n"
    "        self._concept_step_counts[self._current_concept] = (\n"
    "            self._concept_step_counts.get(self._current_concept, 0) + 1)"
)
NEW_ACTION_SELECTED = (
    "        action_num, action_data, reason = self._get_action_for_concept(\n"
    "            self._current_concept, context)\n"
    "        self._concept_steps += 1\n"
    "        self._concept_step_counts[self._current_concept] = (\n"
    "            self._concept_step_counts.get(self._current_concept, 0) + 1)\n"
    "        # v87: count-based curiosity — update action Q and visit count\n"
    "        _fhash = hash(str(context.get('frame', ''))[:150]) % 2000 if context else 0\n"
    "        _av_key = (action_num, _fhash)\n"
    "        self._action_visit_counts[_av_key] = (\n"
    "            self._action_visit_counts.get(_av_key, 0) + 1)\n"
    "        _sc_now = float(context.get('score_delta', 0) or 0)\n"
    "        self._action_Q[action_num] = (\n"
    "            0.88 * self._action_Q.get(action_num, 0.0) + 0.12 * _sc_now)\n"
    "        self._action_Q_total += 1"
)

# ===========================================================================
# 5. UCB concept selection in signal_concept_failed()
#    Replace the simple chosen = (applicable or nxt or [None])[0] line
# ===========================================================================
OLD_UCB_SELECT = "            chosen = (applicable or nxt or [None])[0]"
NEW_UCB_SELECT = """\
            # v87: UCB1 concept selection — prefer unvisited or high-reward concepts
            import math as _ucbm
            self._ucb_concept_total = getattr(self, '_ucb_concept_total', 0) + 1
            _ucb_d = getattr(self, '_concept_ucb', {})
            _ucb_s = _ucb_d.setdefault(prev, {'n': 0, 'r': 0.0})
            _ucb_s['n'] += 1  # record this failure (r unchanged = 0 for now)
            _N_ucb = max(1, self._ucb_concept_total)
            def _ucb1(c):
                s = _ucb_d.get(c, {'n': 0, 'r': 0.0})
                if s['n'] == 0:
                    return float('inf')
                return s['r'] / s['n'] + 1.4 * _ucbm.sqrt(_ucbm.log(_N_ucb) / s['n'])
            if applicable:
                chosen = max(applicable, key=_ucb1)
            else:
                chosen = (nxt or [None])[0]
            self._concept_ucb = _ucb_d\
"""

# ===========================================================================
# 6. UCB reward update on level gain (in the level-gain block)
#    After: self.ledger.record(self._current_concept, True, ...)
# ===========================================================================
OLD_LEVEL_GAIN_LEDGER = (
    "            self.ledger.record(self._current_concept, True,\n"
    "                               f'levels={cur_levels}')"
)
NEW_LEVEL_GAIN_LEDGER = (
    "            self.ledger.record(self._current_concept, True,\n"
    "                               f'levels={cur_levels}')\n"
    "            # v87: positive UCB reward for concept that gained a level\n"
    "            _ucb_win = getattr(self, '_concept_ucb', {})\n"
    "            _ucb_win.setdefault(self._current_concept, {'n': 0, 'r': 0.0})\n"
    "            _ucb_win[self._current_concept]['r'] += 1.0\n"
    "            _ucb_win[self._current_concept]['n'] = max(\n"
    "                1, _ucb_win[self._current_concept]['n'])\n"
    "            self._concept_ucb = _ucb_win"
)

# ===========================================================================
# 7. New concepts: ucb_explore + vmcts
#    Insert before the navigation marker
# ===========================================================================
NEW_CONCEPTS = r"""
        elif concept == 'ucb_explore':
            # Lightweight MCTS leaf: UCB1 over single actions.
            # Uses per-action Q-values (ewma of score_delta) + exploration bonus.
            # Prefer actions that are both high-value and under-tried.
            import math as _um
            _aq  = getattr(self, '_action_Q', {})
            _avc = getattr(self, '_action_visit_counts', {})
            _aqt = max(1, getattr(self, '_action_Q_total', 1))
            def _ucb_act(a):
                q = _aq.get(a, 0.0)
                n = sum(v for (aa, _fh), v in _avc.items() if aa == a)
                if n == 0:
                    return float('inf')
                import math as _m2
                return q + 1.2 * _m2.sqrt(_m2.log(_aqt + 1) / n)
            _ue_act = max(avail, key=_ucb_act)
            # Occasionally inject click probe if available
            _ue_click = 6 if 6 in avail else (5 if 5 in avail else None)
            if _ue_click and self._concept_steps % 9 == 0:
                _ue_act = _ue_click
            return _ue_act, None, (
                f'ucb_explore:A{_ue_act} Q={_aq.get(_ue_act, 0):.3f} '
                f'step={self._concept_steps}')

        elif concept == 'vmcts':
            # Virtual MCTS: builds action-sequence tree from actual gameplay.
            # No forward model -- the live game IS the simulator.
            # Selection: UCB1 over (last_action, current_action) pairs.
            # Backprop: accumulate reward into all ancestor nodes after each step.
            import math as _vm
            if '_vmcts_tree' not in self._pipeline_context:
                self._pipeline_context['_vmcts_tree']    = {}  # seq_tuple->{n,v}
                self._pipeline_context['_vmcts_history'] = []
                self._pipeline_context['_vmcts_depth']   = 2   # sequence context len
            _tree    = self._pipeline_context['_vmcts_tree']
            _history = self._pipeline_context['_vmcts_history']
            _depth   = self._pipeline_context['_vmcts_depth']
            # Compute reward from previous step
            _vm_score = float(context.get('score_delta', 0) or 0)
            _vm_frame = context.get('frame')
            _vm_fhash = hash(str(_vm_frame)[:150]) % 5000 if _vm_frame else 0
            # Backpropagate reward into parent nodes in tree
            if _history:
                for _d in range(1, min(_depth + 1, len(_history) + 1)):
                    _seq = tuple(_history[-_d:])
                    _node = _tree.setdefault(_seq, {'n': 0, 'v': 0.0})
                    _node['n'] += 1
                    _node['v'] += _vm_score + 0.3 * (_vm_fhash % 100) / 100.0
            # Selection: UCB1 over (context, action) pairs
            _ctx = tuple(_history[-_depth:]) if len(_history) >= _depth else tuple(_history)
            _N_vm = max(1, sum(_tree.get(_ctx + (a,), {}).get('n', 0) for a in avail))
            def _vm_ucb(a):
                _node = _tree.get(_ctx + (a,), {'n': 0, 'v': 0.0})
                if _node['n'] == 0:
                    return float('inf')
                return _node['v'] / _node['n'] + 1.4 * _vm.sqrt(_vm.log(_N_vm) / _node['n'])
            _vm_act = max(avail, key=_vm_ucb)
            _history.append(_vm_act)
            if len(_history) > 20:
                _history = _history[-20:]
            self._pipeline_context['_vmcts_history'] = _history
            return _vm_act, None, (
                f'vmcts:A{_vm_act} N={_N_vm} '
                f'tree_size={len(_tree)} step={self._concept_steps}')

"""

TARGET = "        # navigation / coverage / traversal_ordering / mixed_movement"
INSERTION = NEW_CONCEPTS + "        # navigation / coverage / traversal_ordering / mixed_movement"

# ===========================================================================
# 8. Add ucb_explore + vmcts to LONG_PATH_CONCEPTS and classifiers
# ===========================================================================
OLD_LONG = (
    "                # v86 gamelist gap concepts\n"
    "                'frame_punish', 'objective_chase', 'risk_assess',\n"
    "            }"
)
NEW_LONG = (
    "                # v86 gamelist gap concepts\n"
    "                'frame_punish', 'objective_chase', 'risk_assess',\n"
    "                # v87 MCTS / bandit concepts\n"
    "                'ucb_explore', 'vmcts',\n"
    "            }"
)

# Add vmcts + ucb_explore to the maze prio list
OLD_MAZE = (
    "                          'recurrent_avoid', 'conv_scan',\n"
    "                          'objective_chase', 'risk_assess']"
)
NEW_MAZE = (
    "                          'recurrent_avoid', 'conv_scan',\n"
    "                          'objective_chase', 'risk_assess',\n"
    "                          'ucb_explore', 'vmcts']"
)

# Add vmcts to interact cands (games with movement + commit benefit from vmcts)
OLD_INTERACT = (
    "                     'attention_seek', 'frame_punish'] + cands"
)
NEW_INTERACT = (
    "                     'attention_seek', 'frame_punish',\n"
    "                     'vmcts', 'ucb_explore'] + cands"
)

# ===========================================================================
# Apply all patches
# ===========================================================================
nb  = json.load(open(NOTEBOOK))
cell = nb['cells'][11]
src  = ''.join(cell['source'])

checks = [
    (OLD_STAG,              'OLD_STAG'),
    (OLD_INIT_END,          'OLD_INIT_END'),
    (OLD_CLASSIFY_COMMENT,  'OLD_CLASSIFY_COMMENT'),
    (OLD_ACTION_SELECTED,   'OLD_ACTION_SELECTED'),
    (OLD_UCB_SELECT,        'OLD_UCB_SELECT'),
    (OLD_LEVEL_GAIN_LEDGER, 'OLD_LEVEL_GAIN_LEDGER'),
    (TARGET,                'TARGET'),
    (OLD_LONG,              'OLD_LONG'),
    (OLD_MAZE,              'OLD_MAZE'),
    (OLD_INTERACT,          'OLD_INTERACT'),
]
for old, name in checks:
    assert old in src, f'ANCHOR NOT FOUND: {name}'

src = src.replace(OLD_STAG,              NEW_STAG,              1)
src = src.replace(OLD_INIT_END,          NEW_INIT_END,          1)
src = src.replace(OLD_CLASSIFY_COMMENT,  NEW_CLASSIFY_COMMENT,  1)
src = src.replace(OLD_ACTION_SELECTED,   NEW_ACTION_SELECTED,   1)
src = src.replace(OLD_UCB_SELECT,        NEW_UCB_SELECT,        1)
src = src.replace(OLD_LEVEL_GAIN_LEDGER, NEW_LEVEL_GAIN_LEDGER, 1)
src = src.replace(TARGET,                INSERTION,             1)
src = src.replace(OLD_LONG,              NEW_LONG,              1)
src = src.replace(OLD_MAZE,              NEW_MAZE,              1)
src = src.replace(OLD_INTERACT,          NEW_INTERACT,          1)

# Version bump
src = src.replace('# -- v86: ConceptRungBridge', '# -- v87: ConceptRungBridge', 1)

# Verify
concepts = re.findall(r"elif concept == '(\w+)'", src)
print(f"Total concepts: {len(concepts)}")
print("New:", [c for c in concepts if c in ['ucb_explore', 'vmcts']])
print("Stagnation 10:", '= 10' in src[src.find('_stagnation_limit'):src.find('_stagnation_limit')+30])
print("Bootstrap in decide:", '_bootstrap_done' in src[src.find('def decide'):src.find('def decide')+500])
print("UCB in signal_concept_failed:", '_ucb1' in src[src.find('def signal_concept_failed'):src.find('def signal_concept_failed')+1000])
print("Action Q update:", '_action_Q_total += 1' in src)

nb['cells'][11]['source'] = src
json.dump(nb, open(NOTEBOOK, 'w'), indent=1)
print("Patch v87 applied.")
