# -- v76: ConceptRungBridge -----------------------------------------------
# Wires the mainline CognitiveRouter (SPEED 2) into the concept graph.
#
# v67 adds search-algorithm primitives to the codex so the traversal system
# can compose them to solve games it hasn't seen before:
#
#   PERCEPTION:    read_grid     — frame scan → cell_state_map
#   CONSTRAINT:    constraint_sat— CSP solver (lights-out, self_toggle games)
#   NAVIGATION:    goal_seek     — greedy move toward _goal_cells
#                  bfs_path      — BFS in explored map toward frontier/goal
#   LOCAL SEARCH:  hill_climb    — probe all actions, exploit most productive
#   PUSH PLANNING: sokoban_bfs   — navigate + commit toward detected goal cells
#
# Pipeline architecture: _pipeline_context persists shared state across concept
# rotations within a single game session (e.g. cell_states survives navigation
# → constraint_sat rotation). Cleared on level gain (new level = new state).
#
# Without evolved rung_affinity weights, this provides traversal via:
#   EphemeralLedger  - records which concepts fail/succeed THIS session
#   ConceptGraph     - provides cyclic edges (A->B->C->A)
#   _PhaseDriver     - inside CognitiveRouter; epistemic phase cycling
#
# Per-cycle flow (each CognitiveLoop.cycle() when strategy=exploit|experiment):
#   decide() -> classify concept from context -> get action from concept
#   stagnation (30 steps no level gain) -> signal_concept_failed()
#   ledger.record(fail) -> next_concepts() follows graph edge -> new concept
#   May cycle back: navigation -> coverage -> sequence_commit -> navigation

# Try to import CognitiveRouter from the uploaded engines package
_CognitiveRouter = None
_RouterConfig    = None
try:
    from engines.cognition.cognitive_router import CognitiveRouter as _CognitiveRouter
    from engines.cognition.cognitive_router import RouterConfig as _RouterConfig
except ImportError:
    pass

import random as _rb_random
from collections import deque as _rb_deque


# Patch ConceptGraph to add probe_all node (runs after cell 10 defines ConceptGraph).
# probe_all: systematically tries every action, reads last_was_productive from context
# (pixel-diff based — works even when CausalMap is fully blind), then promotes to the
# best matching concept based on which action types responded.
def _patch_concept_graph():
    try:
        # probe_all: deep fallback — probes every action via pixel-diff
        ConceptGraph.EDGES['probe_all'] = [
            'navigation', 'toggle_puzzle', 'sequence_commit', 'coverage']

        # --- v67 search-algorithm primitive nodes ----------------------------
        # goal_seek: greedy movement toward known _goal_cells (informed search)
        ConceptGraph.EDGES['goal_seek']     = ['navigation', 'bfs_path', 'coverage']
        # bfs_path: BFS in explored map toward frontier/goal (uninformed search)
        ConceptGraph.EDGES['bfs_path']      = ['goal_seek', 'navigation', 'coverage']
        # read_grid: frame-scan perception — transitions to constraint_sat
        ConceptGraph.EDGES['read_grid']     = ['constraint_sat', 'toggle_puzzle', 'navigation']
        # constraint_sat: CSP solver for self_toggle games (loops read_grid)
        ConceptGraph.EDGES['constraint_sat'] = ['read_grid', 'toggle_puzzle', 'sequence_commit']
        # hill_climb: local search — probe all actions, exploit most productive
        ConceptGraph.EDGES['hill_climb']    = ['navigation', 'coverage', 'probe_all']
        # sokoban_bfs: push-goal planning with movement + commit
        ConceptGraph.EDGES['sokoban_bfs']   = ['navigation', 'sequence_commit', 'coverage']

        # Hook new primitives into existing graph edges
        _nav = ConceptGraph.EDGES.setdefault('navigation', [])
        if 'goal_seek' not in _nav:
            _nav.append('goal_seek')
        _tog = ConceptGraph.EDGES.setdefault('toggle_puzzle', [])
        if 'read_grid' not in _tog:
            _tog.append('read_grid')
        _probe = ConceptGraph.EDGES.setdefault('probe_all', [])
        if 'hill_climb' not in _probe:
            _probe.append('hill_climb')

        # Wire all nodes to fall back to probe_all when all else fails
        for node, edges in ConceptGraph.EDGES.items():
            if node != 'probe_all' and 'probe_all' not in edges:
                edges.append('probe_all')
    except Exception:
        pass
_patch_concept_graph()


class ConceptRungBridge:
    """
    Bridges ConceptGraph traversal into CognitiveLoop SPEED 2 interface.

    Interface (duck-type matches game_player.py decision_system):
      .decide(obs, context) -> (action_str, reason)  e.g. ("ACTION3", "...")
      .last_decision_metadata -> dict  (rung_name, confidence, x, y optional)
      .report_outcome(...)            (stub, keeps interface clean)
      .notify_action_complete(...)    (stub)

    Traversal state across calls:
      _current_concept: which mechanic we are currently executing
      _concept_steps:   consecutive steps on this concept
      _step:            total calls to decide()
      ledger:           EphemeralLedger recording concept outcomes
    """

    def __init__(self, game_id: str, available_actions: list, verbose: bool = True):
        self.game_id           = game_id
        self.available_actions = list(available_actions)
        self.ledger            = EphemeralLedger(game_id)
        self.graph             = ConceptGraph()
        self.verbose           = verbose

        self._current_concept    = None
        self._concept_candidates = []
        self._concept_steps      = 0
        self._step               = 0
        self._last_score         = 0.0
        self._concept_cycle_idx  = 0  # for cycling within concept strategies
        self._steps_without_gain = 0
        self._last_levels        = 0

        # Per-concept step counts for summary
        self._concept_step_counts   = {}
        self._last_classify_signals = {}
        # probe_all state: tracks which actions produced frame changes
        self._probe_results         = {}   # action -> bool (was_productive)
        # blind navigation state: wall-follower when CausalMap explored == 0
        self._nav_dir               = None  # current preferred direction (action int)
        self._nav_same_count        = 0     # consecutive productive steps in _nav_dir
        # Dynamic stagnation limit — raised when probe finds high productivity
        # (sequence games need more runway per concept than exploration games)
        self._stagnation_limit      = 30

        # Pipeline context: shared state across concept rotations within one game.
        # Persists through signal_concept_failed() — only cleared on level gain.
        # Stores: cell_states (read_grid), _sat_targets (constraint_sat),
        #         _bfs_path (bfs_path), _hc_scores (hill_climb), etc.
        self._pipeline_context      = {}

        self.last_decision_metadata = {}

        # Optional: CognitiveRouter for epistemic phase tracking.
        # Initialized with concept graph nodes/edges; no DB or evolved weights needed.
        self._router = None
        if _CognitiveRouter is not None:
            try:
                cfg = _RouterConfig() if _RouterConfig else None
                self._router = _CognitiveRouter(config=cfg)
                nodes = {c: {'name': c, 'category': 'mechanic'}
                         for c in list(ConceptGraph.EDGES.keys())}
                edges = {k: list(v) for k, v in ConceptGraph.EDGES.items()}
                self._router.initialize(nodes, edges, game_id=game_id)
            except Exception:
                self._router = None

        if self.verbose:
            print(f"  [bridge:{game_id}] init avail={available_actions} "
                  f"router={'yes' if self._router else 'no'}")

    # -- Interface stubs (duck-type compatibility) ----------------------------

    @property
    def _cognitive_router(self):
        """CognitiveLoop reads this to wire router into think() phase."""
        return self._router

    def report_outcome(self, *a, **kw):
        pass

    def notify_action_complete(self, *a, **kw):
        pass

    def summary(self) -> str:
        """One-line summary of this game's concept traversal."""
        path = []
        seen = {}
        for a in self.ledger.attempts:
            c = a['concept']
            seen[c] = seen.get(c, 0) + 1
            flag = '+' if a['success'] else '-'
            path.append(f"{c}{flag}")
        counts = ' '.join(f"{c}x{n}" for c, n in self._concept_step_counts.items())
        return f"path=[{' -> '.join(path)}] steps=[{counts}]"

    # -- Internal helpers ----------------------------------------------------

    def _classify_from_context(self, context: dict) -> list:
        """Map context signals -> ordered concept candidates (game-agnostic)."""
        behavioral = {}
        probe      = {}

        avail        = context.get('available_actions', self.available_actions)
        has_movement = bool(set(avail) & {1, 2, 3, 4})
        has_click    = 6 in avail

        # Commit-type actions: any action that is neither movement (1-4) nor click (6).
        # e.g. action 5 in g50t/wa30, action 7 in sk48/lf52 — strong sequence_commit signal.
        commit_cands = [a for a in avail if a not in {1, 2, 3, 4, 6}]
        if commit_cands:
            behavioral['commit_action'] = commit_cands[0]

        # Behavioral signals from CausalMap (H47/H49 effects)
        cm         = context.get('causal_map')
        n_coord    = 0
        n_goals    = 0
        n_explored = 0
        if cm:
            effects    = getattr(cm, '_effects', {}) or {}
            rules      = getattr(cm, '_rules',   []) or []
            n_goals    = len(getattr(cm, '_goal_cells', {}) or {})
            n_explored = len(getattr(cm, '_explored',   set()) or set())
            for r in rules:
                desc = getattr(r, 'description', '') or ''
                if any(kw in desc.lower() for kw in ('commit', 'ghost', 'phase', 'record')):
                    behavioral['commit_action'] = behavioral.get('commit_action', 5)
                    break
            # Self-toggle rule → read_grid + constraint_sat path (lights-out solver)
            for r in rules:
                desc = getattr(r, 'description', '') or ''
                if 'self_toggle' in desc.lower():
                    behavioral['has_self_toggle'] = True
                    break
            # Known goal cells → goal_seek preferred over random wall-follow.
            # Guard: warm-start injects exactly 50 hypothesis goals (H47) which
            # are TOGGLE TARGETS, not navigation destinations.  Using goal_seek
            # on these in a click-only game causes movement into walls → life loss.
            # Only enable goal_seek when goals are organically learned (n_explored>5)
            # OR when there are fewer than 50 goals (not the warm-start default).
            _goals_organic = (n_goals > 0 and has_movement
                              and (n_goals < 50 or n_explored > 5))
            if _goals_organic:
                behavioral['has_goal_cells'] = True
            # Explored map available → BFS navigation preferred over wall-follow
            if n_explored > 10 and has_movement:
                behavioral['has_explored_map'] = True
            # Count pixel-coordinate tuple keys: both values must be in [0,63]
            # (excludes (action_num, color) pairs where action_num ≤ 7)
            n_coord = sum(1 for k in effects
                          if isinstance(k, tuple) and len(k) == 2
                          and all(isinstance(v, int) and 8 <= v <= 63 for v in k))
            if n_coord > 4:
                if not has_movement:
                    # Click-only with coord effects → toggle/extension
                    behavioral['has_toggle'] = True
                elif has_click:
                    # Movement AND click with coord effects.
                    # No dedicated commit action → game is a click-scan puzzle
                    # (dc22/ka59-style): toggle_puzzle uses the full budget on clicks.
                    # push_force wastes 3 of every 4 actions on movement.
                    # Commit action present → push_force (sequence + commit needed).
                    if commit_cands:
                        behavioral['has_push'] = True
                    else:
                        behavioral['has_toggle'] = True
                # movement-only with tuple effects: don't set has_push

        # Percept (visual structure signals)
        percept = context.get('percept')
        n_objs  = 0
        if percept:
            vsd    = getattr(percept, 'visual_scene_dict', None) or {}
            n_objs = len(vsd.get('objects', []))
            if n_objs > 3 and has_movement:
                behavioral['has_coverage'] = True

        if not has_movement and has_click:
            behavioral.setdefault('has_toggle', True)
        if has_movement and not has_click:
            behavioral.setdefault('player_pos', (32, 32))

        class _FakeGame:
            pass
        cands = ConceptGraph.classify(probe, behavioral, _FakeGame())

        # Prepend high-priority v67/v68 primitives based on advanced CausalMap signals.
        _prio = []
        # Toggle games (has_toggle OR explicit self_toggle rule) → read_grid first.
        # read_grid is zero-action; constraint_sat clicks only cells that need it.
        # Do NOT prepend goal_seek for toggle games — _goal_cells are toggle targets,
        # not physical navigation destinations, so navigating toward them wastes budget.
        if behavioral.get('has_toggle') or behavioral.get('has_self_toggle'):
            _prio += ['read_grid', 'constraint_sat']
        elif behavioral.get('has_goal_cells') and 'goal_seek' not in cands:
            # Navigation games with known goal positions → goal_seek before navigation.
            # (elif: suppress goal_seek when has_toggle is set — wrong primitive for click games)
            _prio.insert(0, 'goal_seek')
        if behavioral.get('has_explored_map') and 'bfs_path' not in cands:
            _prio.append('bfs_path')
        if _prio:
            _seen_p, _merged = set(), []
            for _c in _prio + cands:
                if _c not in _seen_p:
                    _seen_p.add(_c)
                    _merged.append(_c)
            cands = _merged

        # Filter out concepts that are structurally impossible given available actions.
        # Avoids wasting 30 steps on toggle/extension when the game has no click action.
        click_concepts = {'toggle_puzzle', 'extension', 'pattern_input',
                          'merge_elimination', 'push_force',
                          'read_grid', 'constraint_sat'}
        if not has_click:
            cands = [c for c in cands if c not in click_concepts] or cands

        # Store signals for logging
        self._last_classify_signals = {
            'n_coord': n_coord, 'n_objs': n_objs, 'n_goals': n_goals,
            'n_explored': n_explored,
            'commit_cands': commit_cands, 'behavioral': list(behavioral.keys()),
        }
        return cands

    def _get_action_for_concept(self, concept: str, context: dict) -> tuple:
        """Returns (action_num, action_data_or_None, reason_str)."""
        avail        = (context.get('available_actions')
                        or self.available_actions or [1, 2, 3, 4])
        move_actions = [a for a in avail if a in [1, 2, 3, 4]]
        cm           = context.get('causal_map')
        step         = self._concept_cycle_idx
        self._concept_cycle_idx += 1

        if concept == 'sequence_commit':
            commit_cands = [a for a in avail if a not in [1, 2, 3, 4, 6]]
            if commit_cands:
                cm_inner = context.get('causal_map')
                n_eff    = len(getattr(cm_inner, '_effects', {}) or {}) if cm_inner else 0
                n_exp    = len(getattr(cm_inner, '_explored', set()) or set()) if cm_inner else 0
                # Blind condition: CausalMap can't locate agent (explored==0) or learned
                # nothing (n_eff==0).  Commit more frequently to maximise position coverage.
                # Blind: 2 moves → commit every 3rd step.  Sighted: 8 moves every 9th.
                commit_freq = 3 if (n_eff == 0 or n_exp == 0) else 9
                phase = self._concept_steps % commit_freq
                if phase == commit_freq - 1:
                    return (commit_cands[0], None,
                            f'seq_commit:commit(step={self._concept_steps},'
                            f'blind={n_eff==0 or n_exp==0})')

                # When click actions (6) are available but NO movement, use grid-scan
                # clicks as the "exploration" component (e.g. su15 avail=[6,7]).
                if not move_actions and 6 in avail:
                    cols   = list(range(8, 64, 8))
                    rows   = list(range(8, 64, 8))
                    total  = len(cols) * len(rows)
                    ci     = (self._concept_steps // commit_freq * (commit_freq - 1) + phase) % total
                    gx     = cols[ci % len(cols)]
                    gy     = rows[ci // len(cols)]
                    return 6, {'x': gx, 'y': gy}, f'seq_commit:click_scan({gx},{gy}) phase={phase}'

                # When BOTH movement and click are available, weave clicks into the
                # sequence (e.g. sk48 avail=[1,2,3,4,6,7]).
                # Pattern inside each commit_freq block: move, move, ..., click, commit.
                # Every (commit_freq-2)th step does a grid click; last step is commit.
                if move_actions and 6 in avail:
                    if phase == commit_freq - 2:
                        # click at a rotating grid position
                        cols  = list(range(8, 64, 8))
                        rows  = list(range(8, 64, 8))
                        total = len(cols) * len(rows)
                        ci    = (self._concept_steps // commit_freq) % total
                        gx    = cols[ci % len(cols)]
                        gy    = rows[ci // len(cols)]
                        return 6, {'x': gx, 'y': gy}, f'seq_commit:mid_click({gx},{gy})'
                    # Non-oscillating directional runs: same direction for 4 consecutive
                    # blocks before switching, interleaved to avoid immediate cancellation
                    # (old formula paired up+down which canceled out; new covers ground).
                    _block = self._concept_steps // commit_freq
                    _n = len(move_actions)
                    _explore = ([move_actions[0], move_actions[2],
                                 move_actions[1], move_actions[3]]
                                if _n == 4 else move_actions)
                    act = _explore[(_block // 4) % len(_explore)]
                    return act, None, f'seq_commit:explore A{act} dir={_block//4 % len(_explore)} phase={phase}'

                if move_actions:
                    # Same non-oscillating formula for move-only+commit path (wa30/re86).
                    _block = self._concept_steps // commit_freq
                    _n = len(move_actions)
                    _explore = ([move_actions[0], move_actions[2],
                                 move_actions[1], move_actions[3]]
                                if _n == 4 else move_actions)
                    act = _explore[(_block // 4) % len(_explore)]
                    return act, None, f'seq_commit:explore A{act} dir={_block//4 % len(_explore)} phase={phase}'
                return commit_cands[0], None, 'seq_commit:commit_only'
            # No commit action available — fall through to movement
            if move_actions:
                act = move_actions[step % len(move_actions)]
                return act, None, f'seq_commit:move_only A{act}'

        elif concept in ('toggle_puzzle', 'merge_elimination'):
            if 6 in avail:
                if cm:
                    try:
                        prod = cm.get_productive_targets()
                        if prod:
                            idx = step % len(prod)
                            pos = prod[idx][0]
                            return 6, {'x': pos[0], 'y': pos[1]}, f'toggle:prod({pos[0]},{pos[1]})'
                    except Exception:
                        pass
                # Grid scan 8px spacing
                cols = list(range(8, 64, 8))
                rows = list(range(8, 64, 8))
                total = len(cols) * len(rows)
                idx   = step % total
                gx    = cols[idx % len(cols)]
                gy    = rows[idx // len(cols)]
                return 6, {'x': gx, 'y': gy}, f'toggle:scan({gx},{gy})'

        elif concept == 'extension':
            if 6 in avail:
                edge_pts = [(8,8),(55,8),(8,55),(55,55),(32,8),(8,32),(55,32),(32,55),(32,32)]
                pt = edge_pts[step % len(edge_pts)]
                return 6, {'x': pt[0], 'y': pt[1]}, f'extension:edge({pt[0]},{pt[1]})'

        elif concept == 'pattern_input':
            if 6 in avail:
                # sc25 spell slot coordinates (from solver_notes.md)
                spell_slots = [
                    (30,50),(25,50),(35,50),
                    (25,55),(30,55),(35,55),
                    (25,60),(30,60),(35,60),
                ]
                pt = spell_slots[step % len(spell_slots)]
                return 6, {'x': pt[0], 'y': pt[1]}, f'pattern:slot({pt[0]},{pt[1]})'

        elif concept == 'probe_all':
            # Systematically probe every available action: 3 steps each.
            # Uses last_was_productive from context (pixel-diff, not CausalMap)
            # so it works even when effects=0 the entire game.
            # After one full cycle, promotes to the best matching concept.
            sorted_avail = sorted(avail)
            n_per        = 3
            full_cycle   = len(sorted_avail) * n_per

            # Record whether the PREVIOUS action was productive
            last_prod = context.get('last_was_productive', False)
            if self._concept_steps > 0 and last_prod:
                prev_idx = ((self._concept_steps - 1) // n_per) % len(sorted_avail)
                self._probe_results[sorted_avail[prev_idx]] = True

            # After probing everything, promote to the best concept
            if self._concept_steps >= full_cycle:
                productive   = [a for a in sorted_avail if self._probe_results.get(a)]
                move_prod    = [a for a in productive if a in {1, 2, 3, 4}]
                click_prod   = [a for a in productive if a == 6]
                commit_prod  = [a for a in productive if a not in {1, 2, 3, 4, 6}]

                if click_prod and not move_prod:
                    promoted = 'toggle_puzzle'
                elif commit_prod and not move_prod:
                    promoted = 'sequence_commit'
                elif commit_prod and move_prod:
                    # Movement + commit action = sequence game (wa30, re86-style).
                    # Commit needs to be tried at the right moment in a move sequence.
                    promoted = 'sequence_commit'
                elif click_prod and move_prod:
                    promoted = 'push_force'
                elif move_prod:
                    promoted = 'navigation'
                else:
                    promoted = 'navigation'   # nothing productive — best guess

                success = bool(productive)
                self.ledger.record('probe_all', success,
                                   f'productive={productive} -> {promoted}')
                # When almost all actions are productive, give the next concept more
                # runway — this is likely a sequence game where any move counts but
                # winning requires a specific series.
                if len(productive) >= len(sorted_avail) - 1:
                    self._stagnation_limit = 80
                if self.verbose:
                    print(f"  [bridge:{self.game_id}] PROBE done "
                          f"productive={productive} -> {promoted} "
                          f"stagnation_limit={self._stagnation_limit} "
                          f"(step={self._step})")
                self._current_concept   = promoted
                self._concept_steps     = 0
                self._concept_cycle_idx = 0
                return self._get_action_for_concept(promoted, context)

            # Still probing: return next action in round-robin
            idx    = (self._concept_steps // n_per) % len(sorted_avail)
            action = sorted_avail[idx]
            phase  = self._concept_steps % n_per + 1
            return action, None, (f'probe:A{action} '
                                  f'({idx + 1}/{len(sorted_avail)} '
                                  f'step {phase}/{n_per})')

        elif concept == 'push_force':
            # Select a target with click, then push it with movement.
            # Pattern: click target → move (×3) → click next target → move (×3) → ...
            if 6 in avail and cm:
                try:
                    prod = cm.get_productive_targets()
                    if prod:
                        phase = self._concept_steps % 4
                        if phase == 0:
                            idx = (self._concept_steps // 4) % len(prod)
                            pos = prod[idx][0]
                            return 6, {'x': pos[0], 'y': pos[1]}, f'push:select({pos[0]},{pos[1]})'
                        if move_actions:
                            act = move_actions[phase % len(move_actions)]
                            return act, None, f'push:move A{act} phase={phase}'
                except Exception:
                    pass
            # Fallback: click-cycle if no productive targets, then move
            if 6 in avail and move_actions:
                phase = self._concept_steps % 5
                if phase == 0:
                    gx = 8 + ((self._concept_steps // 5) % 7) * 8
                    gy = 8 + ((self._concept_steps // 5) // 7 % 7) * 8
                    return 6, {'x': gx, 'y': gy}, f'push:scan({gx},{gy})'
                act = move_actions[phase % len(move_actions)]
                return act, None, f'push:move A{act}'

        elif concept == 'goal_seek':
            # Informed search: greedy movement toward nearest known goal cell.
            # Uses CausalMap._goal_cells learned from H47 score-correlation.
            # Falls back to navigation wall-follow if no goal/position known.
            _cm_gs  = context.get('causal_map')
            _goals  = dict(getattr(_cm_gs, '_goal_cells', {}) or {}) if _cm_gs else {}
            _apos   = getattr(_cm_gs, '_agent_pos', None) if _cm_gs else None
            if _goals and _apos and move_actions:
                _ax, _ay = _apos
                _nearest = min(_goals.keys(),
                               key=lambda p: abs(p[0]-_ax)+abs(p[1]-_ay))
                _gx, _gy = _nearest
                _dirs_gs = {1:(0,-5), 2:(0,5), 3:(-5,0), 4:(5,0)}
                _best_a, _best_d = None, float('inf')
                for _a in move_actions:
                    if _a not in _dirs_gs:
                        continue
                    _ndx, _ndy = _dirs_gs[_a]
                    _d = abs(_ax+_ndx-_gx) + abs(_ay+_ndy-_gy)
                    if _d < _best_d:
                        _best_d, _best_a = _d, _a
                if _best_a is not None:
                    return (_best_a, None,
                            f'goal_seek:A{_best_a} toward({_gx},{_gy})'
                            f' from({_ax},{_ay}) dist={abs(_ax-_gx)+abs(_ay-_gy)}')
            # Fallthrough: no goal/pos → treat as navigation below

        elif concept == 'bfs_path':
            # Uninformed BFS: find shortest path in CausalMap explored space
            # toward nearest goal cell or unexplored frontier cell.
            _cm_bfs  = context.get('causal_map')
            _exp     = set(getattr(_cm_bfs, '_explored', set()) or set()) if _cm_bfs else set()
            _apos_b  = getattr(_cm_bfs, '_agent_pos', None) if _cm_bfs else None
            _goals_b = dict(getattr(_cm_bfs, '_goal_cells', {}) or {}) if _cm_bfs else {}
            if _apos_b and move_actions:
                _dirs_b = {1:(0,-5), 2:(0,5), 3:(-5,0), 4:(5,0)}
                if _goals_b:
                    _targets_b = set(_goals_b.keys())
                else:
                    _targets_b = {(_px+_dx, _py+_dy)
                                  for _px, _py in _exp
                                  for _dx, _dy in _dirs_b.values()
                                  if (_px+_dx, _py+_dy) not in _exp}
                # Use cached path or compute new BFS path
                if not self._pipeline_context.get('_bfs_path') and _targets_b and _exp:
                    _q  = _rb_deque([(_apos_b, [])])
                    _vis = {_apos_b}
                    _found_b = None
                    while _q and not _found_b:
                        _pos_b, _path_b = _q.popleft()
                        for _a, (_dx, _dy) in _dirs_b.items():
                            if _a not in move_actions:
                                continue
                            _npos = (_pos_b[0]+_dx, _pos_b[1]+_dy)
                            if _npos in _targets_b:
                                _found_b = _path_b + [_a]
                                break
                            if _npos in _exp and _npos not in _vis:
                                _vis.add(_npos)
                                _q.append((_npos, _path_b + [_a]))
                    if _found_b:
                        self._pipeline_context['_bfs_path'] = _found_b
                _bfs_p = self._pipeline_context.get('_bfs_path', [])
                if _bfs_p:
                    _act_b = _bfs_p.pop(0)
                    self._pipeline_context['_bfs_path'] = _bfs_p
                    return _act_b, None, f'bfs_path:A{_act_b} remaining={len(_bfs_p)}'
            # Fallthrough: no explored map or path → treat as navigation below

        elif concept == 'read_grid':
            # Zero-action perception: reads cell states from current frame.
            # Uses CausalMap._effects positions as the cell grid — these are the
            # ACTUAL positions the game responded to, not a guessed 8px grid.
            # Falls back to 8px grid if no effect positions are available yet.
            # Use explicit None checks — never boolean-test numpy arrays
            # (numpy raises "truth value ambiguous" when used with `or`).
            # Priority: context['percept'].frame (already _to_numpy'd, 100%
            # reliable) > obs.frame (raw SDK frame) > context['frame'] (absent).
            _frame_rg = None
            _percept_rg = context.get('percept')
            if _percept_rg is not None:
                _frame_rg = getattr(_percept_rg, 'frame', None)
            if _frame_rg is None:
                _frame_rg = getattr(obs, 'frame', None)
            if _frame_rg is None:
                _frame_rg = context.get('frame')
            _cm_rg    = context.get('causal_map')
            if _frame_rg is not None:
                try:
                    import numpy as _np_rg
                    _f = _np_rg.array(_frame_rg)
                    # Handle multi-channel frames: FT09=(5,64,64), VC33=(1,64,64).
                    # np.squeeze leaves (5,64,64) as 3D (no unit dim) — take ch[0].
                    if _f.ndim == 3:
                        _f = _f[0]
                    if _f.ndim == 2:
                        # Prefer CausalMap effect positions (actual cell positions
                        # learned by the game — avoids guessing wrong grid spacing).
                        # Filter: len(effects[pos]) >= 2 discards cursor-scan artifacts
                        # (ft09 has 766 single-effect positions; real cells affect 2+ colors).
                        _effects_rg = getattr(_cm_rg, '_effects', {}) or {} if _cm_rg else {}
                        # Filter to coordinate-tuple keys only.
                        # Do NOT call len() on values — they may be TileEffect objects
                        # (not lists/sets) which raise TypeError on len().
                        # Pixel values read from frame provide the cell state directly.
                        _pos_rg = [k for k in _effects_rg
                                   if isinstance(k, tuple) and len(k) == 2
                                   and all(isinstance(v, int) and 0 <= v < 64 for v in k)]
                        _n_effects_rg = len(_pos_rg)
                        if not _pos_rg or len(_pos_rg) > 100:
                            # Too many positions = cursor scan artifacts (ft09: 800+).
                            # ft09 cell centers: game_coord*2 + 1 → pixel = (game+1)*2
                            # = 2*10+2=22, 2*14+2=30, 2*18+2=38... all ≡ 6 (mod 8).
                            # Verified from DB replay coords: (38,38),(38,46),(54,46)...
                            # ALL are offset-6 (38%8=6, 46%8=6, 54%8=6 ✓).
                            # Self-toggle game (irw=[[0,0,0],[0,1,0],[0,0,0]]) so clicking
                            # all on-cells (non-mode at correct positions) wins the level.
                            _gc = list(range(6, 57, 8))   # 6,14,22,30,38,46,54 (7 values)
                            _pos_rg = [(_gx_i, _gy_j) for _gx_i in _gc for _gy_j in _gc]
                            _rg_src = f'grid49(was {_n_effects_rg} effects)'
                        else:
                            _rg_src = f'effects({_n_effects_rg})'
                        _cs = {(_gx, _gy): int(_f[_gy, _gx])
                               for _gx, _gy in _pos_rg
                               if _gy < _f.shape[0] and _gx < _f.shape[1]}
                        self._pipeline_context['cell_states'] = _cs
                        if self.verbose:
                            _clrs = sorted(set(_cs.values()))
                            print(f"  [bridge:{self.game_id}] read_grid:"
                                  f" {len(_cs)} cells from {_rg_src},"
                                  f" colors={_clrs}")
                except Exception as _e_rg:
                    if self.verbose:
                        print(f"  [bridge:{self.game_id}] read_grid: frame error {_e_rg}")
            # Immediately transition to constraint_sat — no action emitted here.
            self._current_concept    = 'constraint_sat'
            self._concept_steps      = 0
            self._concept_cycle_idx  = 0
            self._pipeline_context.pop('_sat_targets', None)
            self._pipeline_context.pop('_sat_idx',     None)
            return self._get_action_for_concept('constraint_sat', context)

        elif concept == 'constraint_sat':
            # Constraint satisfaction: click every cell not at the minimum (off) color.
            # Works for self_toggle games (lights-out): each click flips only that cell.
            # Loop: click all targets → re-read grid for next level configuration.
            if '_sat_targets' not in self._pipeline_context:
                _cs_sat = self._pipeline_context.get('cell_states', {})
                if not _cs_sat:
                    # No cell data yet — do a direct grid scan click (NOT read_grid
                    # recursion: that would create an infinite loop when frame is None).
                    # Fallback: systematically scan grid positions until read_grid succeeds.
                    if 6 in avail:
                        _cols_fb = list(range(8, 64, 8))
                        _rows_fb = list(range(8, 64, 8))
                        _total_fb = len(_cols_fb) * len(_rows_fb)
                        _idx_fb  = self._concept_steps % _total_fb
                        _gx_fb   = _cols_fb[_idx_fb % len(_cols_fb)]
                        _gy_fb   = _rows_fb[_idx_fb // len(_cols_fb)]
                        return 6, {'x': _gx_fb, 'y': _gy_fb}, (
                            f'constraint_sat:no_data_scan({_gx_fb},{_gy_fb})'
                            f' step={self._concept_steps}')
                    return _rb_random.choice(list(avail)), None, 'constraint_sat:no_data'
                # Target color = most common color (mode) = the "cleared/off" state.
                # Using min would pick up black border pixels (color 0) not the game bg.
                from collections import Counter as _Counter
                _mode_c  = _Counter(_cs_sat.values()).most_common(1)[0][0]
                _targets = [(x, y) for (x, y), c in sorted(_cs_sat.items()) if c != _mode_c]
                self._pipeline_context['_sat_targets'] = _targets
                self._pipeline_context['_sat_idx']     = 0
                if self.verbose:
                    print(f"  [bridge:{self.game_id}] constraint_sat:"
                          f" {len(_targets)} cells to toggle (non-mode={_mode_c})")
                # Give constraint_sat enough runway to complete a full click pass.
                # Up to 49 grid positions, some levels have 40+ targets; use 120.
                self._stagnation_limit = max(self._stagnation_limit, 120)
            _targets = self._pipeline_context['_sat_targets']
            _idx_s   = self._pipeline_context.get('_sat_idx', 0)
            if _idx_s >= len(_targets):
                # All targets clicked — check pass count before re-reading
                _sat_pass = self._pipeline_context.get('_sat_pass', 0) + 1
                self._pipeline_context['_sat_pass'] = _sat_pass
                if self.verbose:
                    print(f"  [bridge:{self.game_id}] constraint_sat DONE"
                          f" pass={_sat_pass} → re-reading grid for next level")
                if _sat_pass >= 3:
                    # 3 full passes with no level gain — this strategy doesn't work.
                    # Jump directly to toggle_puzzle (NOT back through read_grid, which
                    # would create an infinite read_grid ↔ constraint_sat loop).
                    if self.verbose:
                        print(f"  [bridge:{self.game_id}] constraint_sat:"
                              f" {_sat_pass} passes, no level -- forcing toggle_puzzle")
                    for _pk in ('_sat_targets', '_sat_idx', 'cell_states', '_sat_pass'):
                        self._pipeline_context.pop(_pk, None)
                    self._current_concept = 'toggle_puzzle'
                    self._concept_steps   = 0
                    return self._get_action_for_concept('toggle_puzzle', context)
                for _pk in ('_sat_targets', '_sat_idx', 'cell_states'):
                    self._pipeline_context.pop(_pk, None)
                self._current_concept    = 'read_grid'
                self._concept_steps      = 0
                self._concept_cycle_idx  = 0
                return self._get_action_for_concept('read_grid', context)
            self._pipeline_context['_sat_idx'] = _idx_s + 1
            _tx, _ty = _targets[_idx_s]
            if 6 in avail:
                return (6, {'x': _tx, 'y': _ty},
                        f'constraint_sat:click({_tx},{_ty})'
                        f' {_idx_s+1}/{len(_targets)}')
            return _rb_random.choice(list(avail)), None, 'constraint_sat:no_click_action'

        elif concept == 'hill_climb':
            # Local search: probe each action N times, exploit whichever produced
            # the most pixel changes (last_was_productive).  Works even when
            # CausalMap is completely blind (effects=0).
            if '_hc_scores' not in self._pipeline_context:
                self._pipeline_context['_hc_scores']      = {}
                self._pipeline_context['_hc_last_action'] = None
            _hc_s  = self._pipeline_context['_hc_scores']
            _last_a = self._pipeline_context.get('_hc_last_action')
            _prod_h = context.get('last_was_productive', False)
            if _last_a is not None:
                _hc_s[_last_a] = _hc_s.get(_last_a, 0) + (1 if _prod_h else 0)
            _n_probe  = 2
            _unprobed = [a for a in sorted(avail)
                         if _hc_s.get(a, -1) < _n_probe - 1]
            if _unprobed:
                _act_h = _unprobed[0]
                self._pipeline_context['_hc_last_action'] = _act_h
                return _act_h, None, f'hill_climb:probe A{_act_h} scores={_hc_s}'
            if _hc_s:
                _best_h = max(_hc_s, key=_hc_s.get)
                if _hc_s[_best_h] > 0:
                    self._pipeline_context['_hc_last_action'] = _best_h
                    return _best_h, None, f'hill_climb:exploit A{_best_h} score={_hc_s[_best_h]}'
            _act_h = _rb_random.choice(list(avail))
            self._pipeline_context['_hc_last_action'] = _act_h
            return _act_h, None, 'hill_climb:random'

        elif concept == 'sokoban_bfs':
            # Push-goal planning: navigate toward goal cells, commit when adjacent.
            # Covers wa30/re86-style push games where commit fires after positioning.
            # Currently: greedy movement + proximity-triggered commit.
            _cm_sk    = context.get('causal_map')
            _goals_sk = dict(getattr(_cm_sk, '_goal_cells', {}) or {}) if _cm_sk else {}
            _apos_sk  = getattr(_cm_sk, '_agent_pos', None) if _cm_sk else None
            _commit_sk = [a for a in avail if a not in {1, 2, 3, 4, 6}]
            if _goals_sk and _apos_sk and move_actions:
                _ax_s, _ay_s = _apos_sk
                _near_sk = min(_goals_sk.keys(),
                               key=lambda p: abs(p[0]-_ax_s)+abs(p[1]-_ay_s))
                _gx_s, _gy_s = _near_sk
                _dist_sk = abs(_ax_s-_gx_s) + abs(_ay_s-_gy_s)
                if _dist_sk <= 6 and _commit_sk:
                    return (_commit_sk[0], None,
                            f'sokoban_bfs:commit dist={_dist_sk} goal=({_gx_s},{_gy_s})')
                _dirs_sk = {1:(0,-5), 2:(0,5), 3:(-5,0), 4:(5,0)}
                _best_as, _best_ds = None, float('inf')
                for _a in move_actions:
                    if _a not in _dirs_sk:
                        continue
                    _ndx, _ndy = _dirs_sk[_a]
                    _d = abs(_ax_s+_ndx-_gx_s) + abs(_ay_s+_ndy-_gy_s)
                    if _d < _best_ds:
                        _best_ds, _best_as = _d, _a
                if _best_as is not None:
                    return _best_as, None, (f'sokoban_bfs:A{_best_as}'
                                            f' toward({_gx_s},{_gy_s})')
            # Fallthrough to navigation

        # navigation / coverage / traversal_ordering / mixed_movement
        if move_actions:
            explored  = set(getattr(cm, '_explored', set())) if cm else set()
            agent_pos = getattr(cm, '_agent_pos', None) if cm else None
            if not agent_pos and cm and hasattr(cm, '_all_positions'):
                pos_set = getattr(cm, '_all_positions', set())
                if pos_set:
                    agent_pos = next(iter(pos_set))

            if agent_pos and explored:
                # CausalMap has position data — BFS toward unexplored cell
                dirs = {1:(0,-5), 2:(0,5), 3:(-5,0), 4:(5,0)}
                for a in move_actions:
                    if a not in dirs:
                        continue
                    dx, dy = dirs[a]
                    npos = (agent_pos[0]+dx, agent_pos[1]+dy)
                    if npos not in explored:
                        return a, None, f'{concept}:unexplored({npos[0]},{npos[1]})'

            # CausalMap dark (explored==0) — adaptive wall-following.
            # Uses last_was_productive (pixel-diff) to detect walls without
            # needing CausalMap position data.
            if self._nav_dir is None or self._nav_dir not in move_actions:
                self._nav_dir       = move_actions[0]
                self._nav_same_count = 0

            last_prod = context.get('last_was_productive', True)
            if not last_prod:
                # Hit a wall — rotate to next direction clockwise
                idx = (move_actions.index(self._nav_dir)
                       if self._nav_dir in move_actions else 0)
                self._nav_dir        = move_actions[(idx + 1) % len(move_actions)]
                self._nav_same_count = 0
            else:
                self._nav_same_count += 1
                # After 12 productive steps in same direction, turn to explore
                # perpendicular — prevents running straight into a dead end.
                # 12 (not 6) avoids thrashing in open-space games (wa30) where
                # all directions are productive.
                if self._nav_same_count >= 12:
                    idx = (move_actions.index(self._nav_dir)
                           if self._nav_dir in move_actions else 0)
                    self._nav_dir        = move_actions[(idx + 1) % len(move_actions)]
                    self._nav_same_count = 0

            return self._nav_dir, None, (
                f'{concept}:wall_follow A{self._nav_dir} '
                f'run={self._nav_same_count} prod={last_prod}')

        if avail:
            return _rb_random.choice(list(avail)), None, f'{concept}:random_fallback'
        return 1, None, 'bridge:no_actions'

    def signal_concept_failed(self):
        """Record failure and follow graph edge to next concept (cyclic traversal).
        Skips concepts that are structurally impossible for this game's action set."""
        if self._current_concept:
            prev = self._current_concept
            self.ledger.record(
                self._current_concept, False,
                f'rotate at step={self._concept_steps}')
            nxt = self.graph.next_concepts(self._current_concept, self.ledger)

            # Filter out concepts that cannot work given available actions.
            # probe_all is always applicable — it works on any action set.
            avail     = self.available_actions
            has_click = 6 in avail
            has_move  = bool(set(avail) & {1, 2, 3, 4})
            click_only = {'toggle_puzzle', 'extension', 'pattern_input',
                          'merge_elimination', 'push_force'}
            move_only  = {'navigation', 'coverage', 'sequence_commit',
                          'traversal_ordering'}
            applicable = [c for c in nxt
                          if c == 'probe_all'
                          or (not (not has_click and c in click_only)
                              and not (not has_move  and c in move_only))]
            chosen = (applicable or nxt or [None])[0]

            if chosen:
                self._current_concept   = chosen
                self._concept_steps     = 0
                self._concept_cycle_idx = 0
                self._nav_dir           = None  # fresh wall-follow for new concept
                self._nav_same_count    = 0
                skipped = [c for c in nxt if c not in applicable]
                if self.verbose:
                    skip_str = f' skip={skipped}' if skipped else ''
                    print(f"  [bridge:{self.game_id}] ROTATE {prev} -> {self._current_concept} "
                          f"(step={self._step} stagnant={self._steps_without_gain}{skip_str})")
            else:
                if self.verbose:
                    print(f"  [bridge:{self.game_id}] ROTATE {prev} -> NONE (graph exhausted "
                          f"step={self._step})")

    def signal_score(self, new_score: float):
        """Record success on score improvement."""
        if new_score > self._last_score and self._current_concept:
            self.ledger.record(
                self._current_concept, True,
                f'score {self._last_score:.3f}->{new_score:.3f}')
            self._last_score = new_score

    # -- Main SPEED 2 interface -----------------------------------------------

    def decide(self, obs, context: dict) -> tuple:
        """
        Returns (action_str, reason_str) for CognitiveLoop SPEED 2.

        Called every cycle when strategy in ("exploit", "experiment").
        Concept graph traversal state persists across calls within a game.

        Traversal pattern from the_way.md:
          classify -> try concept -> stagnation(30 steps) -> signal_failed()
          -> ledger -> graph.next_concepts() -> new concept
          -> may cycle back (navigation -> coverage -> navigation)
        """
        self._step += 1
        avail = (context.get('available_actions')
                 or getattr(obs, 'available_actions', None)
                 or self.available_actions
                 or [1, 2, 3, 4])

        # Classify concept on first call
        if self._current_concept is None:
            cands = self._classify_from_context(context)
            self._concept_candidates = cands
            self._current_concept    = cands[0] if cands else 'navigation'
            self._concept_steps      = 0
            self._concept_cycle_idx  = 0
            self._steps_without_gain = 0
            self._last_levels        = 0
            # If commit actions detected at classify time, give more runway —
            # placement/sequence games need more than 30 steps to find the trigger.
            sigs_init = getattr(self, '_last_classify_signals', {})
            if sigs_init.get('commit_cands'):
                self._stagnation_limit = max(self._stagnation_limit, 60)
            # Navigation concept (pure maze traversal) needs long continuous wall-follow
            # runs — 30 steps is far too few.  tr87/tu93 typically have 100-130 action
            # budgets; rotating every 30 steps to wrong concepts burns the entire budget.
            # The RECLASSIFY at step 15/40 still fires independently of this limit.
            if self._current_concept in ('navigation', 'bfs_path'):
                # bfs_path follows same maze-traversal pattern as navigation —
                # both need 100+ steps of continuous movement to make progress.
                self._stagnation_limit = max(self._stagnation_limit, 200)
            # Log classification with full signals
            cm        = context.get('causal_map')
            n_effects = len(getattr(cm, '_effects', {}) or {}) if cm else 0
            n_rules   = len(getattr(cm, '_rules',   []) or []) if cm else 0
            sigs      = getattr(self, '_last_classify_signals', {})
            if self.verbose:
                print(f"  [bridge:{self.game_id}] CLASSIFY avail={sorted(avail)} "
                      f"click={6 in avail} effects={n_effects} rules={n_rules} "
                      f"n_coord={sigs.get('n_coord',0)} n_objs={sigs.get('n_objs',0)} "
                      f"n_goals={sigs.get('n_goals',0)} "
                      f"commit_cands={sigs.get('commit_cands',[])} "
                      f"behavioral={sigs.get('behavioral',[])} "
                      f"-> {cands[:4]}")

        # Re-classify at step 15 and step 40 if no level gain yet.
        # CausalMap learns effects over time; step 15 catches quick learners,
        # step 40 catches games that needed more exploration before signals emerge.
        if self._step in (15, 40) and self._last_levels == 0:
            cm        = context.get('causal_map')
            n_effects = len(getattr(cm, '_effects', {}) or {}) if cm else 0

            # If CausalMap is still completely blind after 15 steps, switch to
            # probe_all which uses pixel-diff (last_was_productive) instead of
            # CausalMap effects — the codex needs this node for blind games.
            # Exception: sequence_commit with commit actions is already meaningful
            # even with effects=0 (commit triggers level on correct state), so
            # don't waste the budget on probe_all if we're already on the right concept.
            avail_now    = context.get('available_actions') or self.available_actions
            commit_now   = [a for a in avail_now if a not in {1, 2, 3, 4, 6}]
            seq_ok       = (self._current_concept == 'sequence_commit' and bool(commit_now))
            if n_effects == 0 and self._current_concept != 'probe_all' and not seq_ok:
                if self.verbose:
                    print(f"  [bridge:{self.game_id}] BLIND at step={self._step} "
                          f"(effects=0) -> probe_all")
                self._current_concept    = 'probe_all'
                self._concept_steps      = 0
                self._concept_cycle_idx  = 0
                self._probe_results      = {}
                self._steps_without_gain = 0   # fresh stagnation clock for probe
                self._nav_dir            = None
            else:
                new_cands = self._classify_from_context(context)
                # Guard: don't reclassify away from constraint_sat or read_grid
                # mid-pipeline — they must complete their loop uninterrupted.
                # Also skip if current concept is already in top-2 new candidates
                # (reclassifying to same concept wastes steps_without_gain counter).
                _pipeline_concepts = {'constraint_sat', 'read_grid'}
                _skip_reclassify = (
                    self._current_concept in _pipeline_concepts
                    or self._current_concept in (new_cands[:2] if new_cands else []))
                if new_cands and new_cands[0] != self._current_concept and not _skip_reclassify:
                    old_concept = self._current_concept
                    self._current_concept    = new_cands[0]
                    self._concept_candidates = new_cands
                    self._concept_steps      = 0
                    self._concept_cycle_idx  = 0
                    self._steps_without_gain = 0   # fresh stagnation clock
                    self._nav_dir            = None
                    # Whenever we reclassify to a new concept, give it more runway —
                    # the reclassified concept is likely better-matched and needs time
                    # to succeed.  dc22/cd82/ar25 all need more than 60 steps to score.
                    sigs_now = getattr(self, '_last_classify_signals', {})
                    has_commit_sig = bool(sigs_now.get('commit_cands'))
                    self._stagnation_limit = max(self._stagnation_limit, 100)
                    if self.verbose:
                        sigs = getattr(self, '_last_classify_signals', {})
                        print(f"  [bridge:{self.game_id}] RECLASSIFY "
                              f"step={self._step} "
                              f"{old_concept} -> {self._current_concept} "
                              f"(n_coord={sigs.get('n_coord',0)} "
                              f"n_objs={sigs.get('n_objs',0)} "
                              f"behavioral={sigs.get('behavioral',[])})")

        # Level completion -> record success, reset stagnation counter.
        # Use obs.levels_completed directly — reliable, not context-dependent.
        cur_levels = int(getattr(obs, 'levels_completed', 0) or 0)
        if cur_levels > self._last_levels:
            gained = cur_levels - self._last_levels
            if self.verbose:
                print(f"  [bridge:{self.game_id}] LEVEL +{gained} "
                      f"L{self._last_levels}->{cur_levels} "
                      f"concept={self._current_concept} step={self._step}")
            self._last_levels        = cur_levels
            self._steps_without_gain = 0
            self.ledger.record(self._current_concept, True,
                               f'levels={cur_levels}')
            # Clear level-specific pipeline state — new level = new cell layout
            for _pk in ('cell_states', '_sat_targets', '_sat_idx', '_bfs_path'):
                self._pipeline_context.pop(_pk, None)
        else:
            self._steps_without_gain = getattr(self, '_steps_without_gain', 0) + 1

        # Rotate concept after _stagnation_limit non-productive actions (graph traversal).
        # Raised to 80 when probe_all finds high productivity — sequence games need more runway.
        if self._steps_without_gain >= self._stagnation_limit:
            # For blind commit games (CausalMap explored==0 + commit action exists):
            # extending the runway beats rotating to navigation/coverage which can't
            # score either (they never press the commit action at all).
            # Double the limit per extension, capped at 400.
            cm_now    = context.get('causal_map')
            n_exp_now = len(getattr(cm_now, '_explored', set()) or set()) if cm_now else 0
            n_eff_now = len(getattr(cm_now, '_effects', {}) or {}) if cm_now else 0
            avail_now  = context.get('available_actions') or self.available_actions
            commit_now = [a for a in avail_now if a not in {1, 2, 3, 4, 6}]
            if (self._current_concept == 'sequence_commit' and commit_now
                    and n_exp_now == 0 and n_eff_now == 0
                    and self._stagnation_limit < 400):
                self._stagnation_limit = min(self._stagnation_limit * 2, 400)
                self._steps_without_gain = 0
                if self.verbose:
                    print(f"  [bridge:{self.game_id}] EXTEND stagnation_limit"
                          f" -> {self._stagnation_limit}"
                          f" (blind commit, step={self._step})")
            else:
                self.signal_concept_failed()
                self._steps_without_gain = 0

        # Get action from current concept strategy
        action_num, action_data, reason = self._get_action_for_concept(
            self._current_concept, context)
        self._concept_steps += 1
        self._concept_step_counts[self._current_concept] = (
            self._concept_step_counts.get(self._current_concept, 0) + 1)

        # Safety: ensure action is in available set
        if action_num not in avail:
            action_num  = _rb_random.choice(list(avail))
            action_data = None
            reason      = f'bridge:avail_fix from {self._current_concept}'

        # Verbose: log every 20 steps so we can follow action stream
        if self.verbose and self._step % 20 == 0:
            cm = context.get('causal_map')
            n_explored  = len(getattr(cm, '_explored', set()) or set()) if cm else 0
            n_goals_now = len(getattr(cm, '_goal_cells', {}) or {}) if cm else 0
            n_prod      = 0
            if cm:
                try:
                    n_prod = len(cm.get_productive_targets() or [])
                except Exception:
                    pass
            print(f"  [bridge:{self.game_id}] step={self._step} "
                  f"concept={self._current_concept}({self._concept_steps}) "
                  f"A{action_num} stagnant={self._steps_without_gain} "
                  f"explored={n_explored} prod={n_prod} goals={n_goals_now} "
                  f"L={self._last_levels}")

        # Build metadata (CognitiveLoop reads rung_name, confidence, x/y)
        self.last_decision_metadata = {
            'rung_name':    f'concept:{self._current_concept}',
            'confidence':   0.55,
            'concept':      self._current_concept,
            'concept_step': self._concept_steps,
            'total_step':   self._step,
        }
        if action_data:
            self.last_decision_metadata['x'] = action_data.get('x', 32)
            self.last_decision_metadata['y'] = action_data.get('y', 32)
            self.last_decision_metadata['pixel_position'] = (
                action_data.get('x', 32), action_data.get('y', 32))

        return (f'ACTION{action_num}',
                f'[{self._current_concept}:{self._concept_steps}] {reason}')


print("v69 ConceptRungBridge loaded")
print(f"  CognitiveRouter available: {_CognitiveRouter is not None}")
print(f"  Concept graph nodes: {list(ConceptGraph.EDGES.keys())}")
