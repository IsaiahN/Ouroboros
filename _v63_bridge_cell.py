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
#   "experiment" signal + N steps -> signal_concept_failed()
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

    def __init__(self, game_id: str, available_actions: list):
        self.game_id           = game_id
        self.available_actions = list(available_actions)
        self.ledger            = EphemeralLedger(game_id)
        self.graph             = ConceptGraph()

        self._current_concept    = None
        self._concept_candidates = []
        self._concept_steps      = 0
        self._step               = 0
        self._last_score         = 0.0
        self._concept_cycle_idx  = 0  # for cycling within concept strategies

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

    # -- Interface stubs (duck-type compatibility) ----------------------------

    @property
    def _cognitive_router(self):
        """CognitiveLoop reads this to wire router into think() phase."""
        return self._router

    def report_outcome(self, *a, **kw):
        pass

    def notify_action_complete(self, *a, **kw):
        pass

    # -- Internal helpers ----------------------------------------------------

    def _classify_from_context(self, context: dict) -> list:
        """Map context signals -> ordered concept candidates (game-agnostic)."""
        behavioral = {}
        probe      = {}

        avail        = context.get('available_actions', self.available_actions)
        has_movement = bool(set(avail) & {1, 2, 3, 4})
        has_click    = 6 in avail

        # Behavioral signals from CausalMap (H47/H49 effects)
        cm = context.get('causal_map')
        if cm:
            effects = getattr(cm, '_effects', {}) or {}
            rules   = getattr(cm, '_rules',   []) or []
            for r in rules:
                desc = getattr(r, 'description', '') or ''
                if any(kw in desc.lower() for kw in ('commit', 'ghost', 'phase', 'record')):
                    behavioral['commit_action'] = 5
                    break
            n_coord = sum(1 for k in effects
                          if isinstance(k, tuple) and len(k) == 2
                          and all(isinstance(v, (int, float)) for v in k))
            if n_coord > 4:
                behavioral['has_toggle'] = not has_movement

        # Percept (visual structure signals)
        percept = context.get('percept')
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
        return ConceptGraph.classify(probe, behavioral, _FakeGame())

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
            if self._concept_steps >= 3 and commit_cands:
                return commit_cands[0], None, f'seq_commit:commit(step={self._concept_steps})'
            if move_actions:
                act = move_actions[step % len(move_actions)]
                return act, None, f'seq_commit:pre_commit A{act}'
            if commit_cands:
                return commit_cands[0], None, 'seq_commit:commit_only'

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

        # navigation / coverage / push_force / traversal_ordering / mixed_movement
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
        """Record failure and follow graph edge to next concept (cyclic traversal)."""
        if self._current_concept:
            self.ledger.record(
                self._current_concept, False,
                f'rotate at step={self._concept_steps}')
            nxt = self.graph.next_concepts(self._current_concept, self.ledger)
            if nxt:
                self._current_concept   = nxt[0]
                self._concept_steps     = 0
                self._concept_cycle_idx = 0

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
          classify -> try concept -> if experiment+steps -> signal_failed()
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

        # Score improvement -> record success, stay on concept
        cur_score = float(context.get('score', 0.0) or 0.0)
        if cur_score > self._last_score:
            self.signal_score(cur_score)

        # "experiment" strategy signals current approach is failing
        # After enough steps -> rotate concept along graph edge
        strategy = context.get('strategy', 'exploit')
        if strategy == 'experiment' and self._concept_steps >= 6:
            self.signal_concept_failed()

        # Get action from current concept strategy
        action_num, action_data, reason = self._get_action_for_concept(
            self._current_concept, context)
        self._concept_steps += 1

        # Safety: ensure action is in available set
        if action_num not in avail:
            action_num  = _rb_random.choice(list(avail))
            action_data = None
            reason      = f'bridge:avail_fix from {self._current_concept}'

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
