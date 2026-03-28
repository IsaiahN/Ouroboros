# -- v63: ConceptRungBridge -----------------------------------------------
# Wires the mainline CognitiveRouter (SPEED 2) into the concept graph.
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


# Patch ConceptGraph to add probe_all node (runs after cell 10 defines ConceptGraph).
# probe_all: systematically tries every action, reads last_was_productive from context
# (pixel-diff based — works even when CausalMap is fully blind), then promotes to the
# best matching concept based on which action types responded.
def _patch_concept_graph():
    try:
        ConceptGraph.EDGES['probe_all'] = [
            'navigation', 'toggle_puzzle', 'sequence_commit', 'coverage']
        # wire existing nodes to fall back to probe_all when all else fails
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
        cm      = context.get('causal_map')
        n_coord = 0
        n_goals = 0
        if cm:
            effects = getattr(cm, '_effects', {}) or {}
            rules   = getattr(cm, '_rules',   []) or []
            n_goals = len(getattr(cm, '_goal_cells', {}) or {})
            for r in rules:
                desc = getattr(r, 'description', '') or ''
                if any(kw in desc.lower() for kw in ('commit', 'ghost', 'phase', 'record')):
                    behavioral['commit_action'] = behavioral.get('commit_action', 5)
                    break
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
                    # Movement AND click with coord effects → push_force
                    behavioral['has_push'] = True
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

        # Filter out concepts that are structurally impossible given available actions.
        # Avoids wasting 30 steps on toggle/extension when the game has no click action.
        click_concepts = {'toggle_puzzle', 'extension', 'pattern_input',
                          'merge_elimination', 'push_force'}
        if not has_click:
            cands = [c for c in cands if c not in click_concepts] or cands

        # Store signals for logging
        self._last_classify_signals = {
            'n_coord': n_coord, 'n_objs': n_objs, 'n_goals': n_goals,
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
                # Explore for 8 moves, then try commit, then explore again.
                # Pattern: 8 moves → commit → 8 moves → commit → ...
                phase = self._concept_steps % 9
                if phase == 8:
                    return commit_cands[0], None, f'seq_commit:commit(step={self._concept_steps})'
                if move_actions:
                    act = move_actions[(self._concept_steps // 9 * 4 + phase) % len(move_actions)]
                    return act, None, f'seq_commit:explore A{act} phase={phase}'
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
                elif click_prod and move_prod:
                    promoted = 'push_force'
                elif move_prod:
                    promoted = 'navigation'
                else:
                    promoted = 'navigation'   # nothing productive — best guess

                success = bool(productive)
                self.ledger.record('probe_all', success,
                                   f'productive={productive} -> {promoted}')
                if self.verbose:
                    print(f"  [bridge:{self.game_id}] PROBE done "
                          f"productive={productive} -> {promoted} "
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

        # navigation / coverage / traversal_ordering / mixed_movement
        if move_actions:
            if cm and hasattr(cm, '_explored'):
                explored  = set(getattr(cm, '_explored', set()))
                agent_pos = getattr(cm, '_agent_pos', None)
                if agent_pos is None and hasattr(cm, '_all_positions'):
                    pos_set = getattr(cm, '_all_positions', set())
                    if pos_set:
                        agent_pos = next(iter(pos_set))
                if agent_pos:
                    dirs = {1:(0,-5), 2:(0,5), 3:(-5,0), 4:(5,0)}
                    for a in move_actions:
                        if a not in dirs:
                            continue
                        dx, dy = dirs[a]
                        npos = (agent_pos[0]+dx, agent_pos[1]+dy)
                        if npos not in explored:
                            return a, None, f'{concept}:unexplored({npos[0]},{npos[1]})'
            act = move_actions[step % len(move_actions)]
            return act, None, f'{concept}:cycle A{act}'

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
            if n_effects == 0 and self._current_concept != 'probe_all':
                if self.verbose:
                    print(f"  [bridge:{self.game_id}] BLIND at step={self._step} "
                          f"(effects=0) -> probe_all")
                self._current_concept   = 'probe_all'
                self._concept_steps     = 0
                self._concept_cycle_idx = 0
                self._probe_results     = {}
            else:
                new_cands = self._classify_from_context(context)
                if new_cands and new_cands[0] != self._current_concept:
                    old_concept = self._current_concept
                    self._current_concept    = new_cands[0]
                    self._concept_candidates = new_cands
                    self._concept_steps      = 0
                    self._concept_cycle_idx  = 0
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
        else:
            self._steps_without_gain = getattr(self, '_steps_without_gain', 0) + 1

        # Rotate concept after 30 non-productive actions (graph traversal)
        if self._steps_without_gain >= 30:
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


print("v63 ConceptRungBridge loaded")
print(f"  CognitiveRouter available: {_CognitiveRouter is not None}")
print(f"  Concept graph nodes: {list(ConceptGraph.EDGES.keys())}")
