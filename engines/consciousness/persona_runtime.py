import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be FIRST before other imports

import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from database_interface import DatabaseInterface

# =============================================================================
# PERSONA BUDGET MANAGER CONSTANTS (from agent_consciousness_synthesis.md)
# =============================================================================
# Hard limits to prevent persona explosion while maintaining diversity.
# These are non-negotiable caps that apply globally.
# =============================================================================
MAX_ACTIVE_PERSONAS = 12          # Absolute maximum personas per agent
MAX_TEMPORARY_PERSONAS = 5        # Investigators, adapters, etc.
MAX_OBJECT_FOCUSED_PERSONAS = 3   # Even if controlling 10 objects


@dataclass
class PersonaDecision:
    persona_id: str
    proposal_id: str
    problem_signature: Optional[str]
    world_model: Optional[str]
    step_idx: Optional[int]
    level_number: Optional[int]
    game_id: Optional[str]
    action: Optional[str]


class PersonaManager:
    """Lightweight persona runtime for proposal/outcome logging and reliability updates.

    Includes PersonaBudgetManager functionality from agent_consciousness_synthesis.md:
    - Hard limits on total personas (MAX_ACTIVE_PERSONAS = 12)
    - Hard limits on temporary personas (MAX_TEMPORARY_PERSONAS = 5)
    - Budget-aware spawning via can_spawn_persona()
    """

    def __init__(self, db: DatabaseInterface, agent_id: Optional[str] = None):
        self.db = db
        self.agent_id = agent_id
        self._persona_cache: Dict[str, Dict[str, Any]] = {}
        self._persona_allowance: Optional[int] = None
        self._imagination_remaining: float = 1.0

    def set_agent(self, agent_id: Optional[str]) -> None:
        self.agent_id = agent_id

    def set_imagination_budget(self, allowance: Optional[int] = None, imagination_remaining: Optional[float] = None) -> None:
        """Update persona spawn limits based on imagination budget signals."""
        if allowance is not None:
            self._persona_allowance = max(1, min(int(allowance), MAX_ACTIVE_PERSONAS))
        if imagination_remaining is not None:
            try:
                self._imagination_remaining = float(imagination_remaining)
            except Exception:
                self._imagination_remaining = 1.0

    def can_spawn_persona(self, persona_type: str = 'experimental', imagination_remaining: Optional[float] = None) -> tuple[bool, str]:
        """
        Check if spawning a new persona is allowed within budget.

        Part of PersonaBudgetManager functionality.

        Args:
            persona_type: Type of persona ('core', 'experimental', 'temporary')
            imagination_remaining: Remaining imagination budget (0.0-1.0)

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        if not self.agent_id:
            return False, 'no_agent_id'

        # Query current persona count
        try:
            rows = self.db.execute_query(
                "SELECT persona_id, persistence_class, persona_type FROM persona_profiles WHERE agent_id=?",
                (self.agent_id,),
            )
            personas = rows or []
        except Exception:
            return True, 'db_error_allowing'

        current_count = len(personas)
        temp_count = sum(1 for p in personas if (p.get('persistence_class') or '').lower() == 'temporary')

        # Apply dynamic allowance if provided
        allowance_cap = self._persona_allowance or MAX_ACTIVE_PERSONAS
        if current_count >= allowance_cap:
            return False, 'allowance_limit'

        # Check against hard limits
        if current_count >= MAX_ACTIVE_PERSONAS:
            return False, 'at_hard_limit'

        if persona_type.lower() == 'temporary' and temp_count >= MAX_TEMPORARY_PERSONAS:
            return False, 'temporary_limit'

        # Check imagination budget
        effective_imagination = self._imagination_remaining if imagination_remaining is None else imagination_remaining
        if effective_imagination is None:
            effective_imagination = 1.0
        if effective_imagination < 0.1:
            return False, 'imagination_exhausted'

        return True, 'allowed'

    def spawn_temporary_persona(self, spec: Dict[str, Any]) -> Optional[str]:
        """
        Spawn a temporary investigating persona if budget allows.

        Used by QuestioningEngineWithTeeth to spawn investigators.

        Args:
            spec: Persona specification with type, investigating, query, etc.

        Returns:
            Persona ID if spawned, None if blocked by budget
        """
        allowed, reason = self.can_spawn_persona('temporary')
        if not allowed:
            return None

        persona_id = f"persona_tmp_{spec.get('investigating', 'unknown')}_{uuid.uuid4().hex[:6]}"

        try:
            self.ensure_persona(
                persona_id,
                persona_type=spec.get('type', 'investigator'),
                persistence_class='temporary',
                role=spec.get('investigating'),
            )
            return persona_id
        except Exception:
            return None

    # =========================================================================
    # PERSONA-THEORY BINDING (from agent_consciousness_synthesis.md)
    # Personas bound to theories die when theories are contradicted
    # =========================================================================

    def bind_persona_to_theory(self, persona_id: str, theory: Dict[str, Any]) -> bool:
        """
        Bind a persona to a specific theory.

        When the theory is contradicted, the persona dies with it.
        This prevents zombie personas advocating for dead theories.

        Args:
            persona_id: The persona to bind
            theory: The theory dict with at least 'theory_id' and 'formed_at_action'

        Returns:
            True if binding succeeded
        """
        if not persona_id or not theory:
            return False

        theory_id = theory.get('theory_id') or theory.get('hypothesis')
        formed_at = theory.get('formed_at_action') or theory.get('formed_at', 0)

        # Store binding in database
        try:
            self.db.execute_query(
                """INSERT OR REPLACE INTO persona_theory_bindings
                   (persona_id, theory_id, bound_at_action, agent_id, created_at)
                   VALUES (?, ?, ?, ?, datetime('now'))""",
                (persona_id, str(theory_id), formed_at, self.agent_id)
            )
            return True
        except Exception:
            # Table might not exist - that's okay, binding is optional
            return False

    def unbind_personas_for_theory(self, theory_id: str) -> int:
        """
        When a theory is contradicted, unbind and optionally prune its personas.

        Returns count of personas unbound.
        """
        if not theory_id:
            return 0

        try:
            rows = self.db.execute_query(
                "SELECT persona_id FROM persona_theory_bindings WHERE theory_id=? AND agent_id=?",
                (str(theory_id), self.agent_id)
            )
            if not rows:
                return 0

            count = 0
            for row in rows:
                pid = row.get('persona_id')
                if pid:
                    # Mark persona as unbound (could also delete it)
                    self.db.execute_query(
                        "DELETE FROM persona_theory_bindings WHERE persona_id=? AND agent_id=?",
                        (pid, self.agent_id)
                    )
                    count += 1

            return count
        except Exception:
            return 0

    def prune_theory_orphans(self, working_theory: Optional[Dict[str, Any]] = None) -> int:
        """
        Aggressive pruning of personas not bound to current theory.

        Called when theory changes significantly.

        Args:
            working_theory: Current active theory (personas not bound to this die)

        Returns:
            Number of personas pruned
        """
        if not self.agent_id:
            return 0

        pruned = 0
        current_theory_id = None
        if working_theory:
            current_theory_id = str(working_theory.get('theory_id') or working_theory.get('hypothesis', ''))

        try:
            # Get all bound personas
            rows = self.db.execute_query(
                "SELECT persona_id, theory_id FROM persona_theory_bindings WHERE agent_id=?",
                (self.agent_id,)
            )

            if rows:
                for row in rows:
                    bound_theory = row.get('theory_id')
                    pid = row.get('persona_id')

                    # If bound to a different theory and not core, consider pruning
                    if bound_theory and bound_theory != current_theory_id and pid:
                        # Check if persona is temporary
                        persona_rows = self.db.execute_query(
                            "SELECT persistence_class FROM persona_profiles WHERE persona_id=?",
                            (pid,)
                        )
                        if persona_rows:
                            cls = (persona_rows[0].get('persistence_class') or '').lower()
                            if cls in ('temporary', 'experimental'):
                                # Delete the persona
                                self.db.execute_query(
                                    "DELETE FROM persona_profiles WHERE persona_id=?",
                                    (pid,)
                                )
                                self.db.execute_query(
                                    "DELETE FROM persona_theory_bindings WHERE persona_id=?",
                                    (pid,)
                                )
                                pruned += 1

            return pruned
        except Exception:
            return 0

    def generate_proposals(
        self,
        game_state: Any,
        available_actions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate diverse action proposals from multiple personas.

        Each persona has a different bias/personality that influences
        its action preference:
        - Explorer: prefers novel actions, high risk tolerance
        - Cautious: prefers safe actions, avoids known dangers
        - Optimizer: prefers efficient actions, follows proven paths
        - Pioneer: prefers unknown territory, discovery-oriented

        This is the key function for Consciousness Theory CON-002.

        Returns:
            List of proposals, each with:
            - action: proposed action (ACTION1-7)
            - confidence: 0.0-1.0
            - persona_id: which persona proposed
            - reasoning: why this action
        """
        # FIX: Don't require agent_id - use default personas if not available
        # The agent_id check was causing ALL proposals to return empty

        proposals = []
        available = available_actions or ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4',
                                          'ACTION5', 'ACTION6', 'ACTION7']

        # Get active personas for this agent (if agent_id available)
        personas = []
        if self.agent_id:
            try:
                rows = self.db.execute_query(
                    """SELECT persona_id, persona_type, bias_risk, novelty_bias, reliability_global
                       FROM persona_profiles WHERE agent_id=? ORDER BY reliability_global DESC LIMIT 5""",
                    (self.agent_id,)
                )
                personas = list(rows) if rows else []
            except Exception:
                personas = []

        # If no personas from DB, create default ensemble
        # This ensures we ALWAYS have proposals for deliberation
        if not personas:
            personas = [
                {'persona_id': 'explorer', 'persona_type': 'explorer', 'bias_risk': 0.7, 'novelty_bias': 0.8, 'reliability_global': 0.5},
                {'persona_id': 'cautious', 'persona_type': 'cautious', 'bias_risk': 0.2, 'novelty_bias': 0.3, 'reliability_global': 0.5},
                {'persona_id': 'optimizer', 'persona_type': 'optimizer', 'bias_risk': 0.5, 'novelty_bias': 0.1, 'reliability_global': 0.5},
            ]

        # Context for decision-making
        ctx = context or {}
        recent_actions = ctx.get('recent_actions', [])
        failed_actions = ctx.get('failed_actions', [])
        network_suggested = ctx.get('network_suggested', [])

        for persona in personas:
            pid = persona.get('persona_id', 'unknown')
            ptype = (persona.get('persona_type') or 'explorer').lower()
            risk_bias = persona.get('bias_risk', 0.5) or 0.5
            novelty_bias = persona.get('novelty_bias', 0.5) or 0.5
            reliability = persona.get('reliability_global', 0.5) or 0.5

            # Each persona type has different action preferences
            if ptype in ('explorer', 'pioneer', 'discovery'):
                # Prefers novel actions, avoids recently tried
                action_scores = {}
                for action in available:
                    score = 0.5
                    if action not in recent_actions:
                        score += 0.3 * novelty_bias  # Novel = good
                    if action in failed_actions:
                        score -= 0.2 * (1 - risk_bias)  # Less penalty if risk-tolerant
                    action_scores[action] = score
                best = max(action_scores, key=action_scores.get)
                proposals.append({
                    'action': best,
                    'confidence': min(1.0, action_scores[best] * reliability),
                    'persona_id': pid,
                    'persona_type': ptype,
                    'reasoning': f"Explorer persona prefers novel action {best}"
                })

            elif ptype in ('cautious', 'validator'):
                # Prefers safe actions, follows network
                action_scores = {}
                for action in available:
                    score = 0.3
                    if action in network_suggested:
                        score += 0.4  # Network validated = safe
                    if action in failed_actions:
                        score -= 0.4 * (1 - risk_bias)  # Heavy penalty
                    action_scores[action] = score
                best = max(action_scores, key=action_scores.get)
                proposals.append({
                    'action': best,
                    'confidence': min(1.0, action_scores[best] * reliability),
                    'persona_id': pid,
                    'persona_type': ptype,
                    'reasoning': f"Cautious persona prefers safe action {best}"
                })

            elif ptype in ('optimizer', 'network'):
                # Follows network suggestions closely
                action_scores = {}
                for action in available:
                    score = 0.2
                    if action in network_suggested:
                        score += 0.6  # Strongly prefer network
                    if action in recent_actions[-3:] if len(recent_actions) >= 3 else recent_actions:
                        score -= 0.1  # Slight penalty for repetition
                    action_scores[action] = score
                best = max(action_scores, key=action_scores.get)
                proposals.append({
                    'action': best,
                    'confidence': min(1.0, action_scores[best] * reliability),
                    'persona_id': pid,
                    'persona_type': ptype,
                    'reasoning': f"Optimizer persona follows network with {best}"
                })

            else:
                # Default: random selection with slight exploration bias
                import random
                action = random.choice(available)
                proposals.append({
                    'action': action,
                    'confidence': 0.3 * reliability,
                    'persona_id': pid,
                    'persona_type': ptype,
                    'reasoning': f"Default persona proposes {action}"
                })

        return proposals

    def allocate_attention(self) -> Dict[str, float]:
        """
        Allocate attention budget across active personas.

        More personas = less attention each.
        This prevents cognitive explosion.

        Returns:
            Dict mapping persona_id to attention weight (0.0-1.0)
        """
        if not self.agent_id:
            return {}

        try:
            rows = self.db.execute_query(
                """SELECT persona_id, persistence_class, reliability_global
                   FROM persona_profiles WHERE agent_id=?""",
                (self.agent_id,)
            )
            if not rows:
                return {}

            personas = list(rows)
            total_count = len(personas)

            if total_count == 0:
                return {}

            # Base attention per persona (inversely proportional to count)
            base_attention = 1.0 / total_count

            # Weight by persistence class and reliability
            attention = {}
            total_weight = 0.0

            for p in personas:
                pid = p.get('persona_id')
                cls = (p.get('persistence_class') or 'experimental').lower()
                rel = p.get('reliability_global') or 0.5

                # Core personas get more attention
                class_weight = 1.5 if cls == 'core' else (0.7 if cls == 'temporary' else 1.0)

                # Reliable personas get more attention
                rel_weight = 0.5 + rel

                weight = class_weight * rel_weight
                attention[pid] = weight
                total_weight += weight

            # Normalize to sum to 1.0
            if total_weight > 0:
                for pid in attention:
                    attention[pid] /= total_weight

            return attention

        except Exception:
            return {}

    def ensure_persona(
        self,
        persona_id: str,
        *,
        persona_type: Optional[str] = None,
        role: Optional[str] = None,
        stage: Optional[int] = None,
        world_model: Optional[str] = None,
        bias_vector: Optional[Dict[str, Any]] = None,
        bias_risk: Optional[float] = None,
        bias_abstraction: Optional[float] = None,
        bias_symbolic: Optional[float] = None,
        novelty_bias: Optional[float] = None,
        persistence_class: Optional[str] = None,
        lifetime_exposures: Optional[int] = None,
        stream_type: Optional[str] = None,  # FIX #9: 'A', 'B', or 'neutral'
    ) -> None:
        if persona_id in self._persona_cache:
            return

        # FIX #9: Derive stream_type from persona_type if not provided
        # Action Proposers = Stream A (private experience)
        # Observers/Evaluators = Stream B (network wisdom)
        if stream_type is None:
            pt_lower = (persona_type or '').lower()
            if pt_lower in ('proposer', 'explorer', 'pioneer', 'investigator', 'discovery'):
                stream_type = 'A'  # Private experience stream
            elif pt_lower in ('observer', 'evaluator', 'validator', 'optimizer', 'network'):
                stream_type = 'B'  # Network wisdom stream
            elif pt_lower in ('counterfactual', 'scorer', 'classifier'):
                stream_type = 'neutral'  # Both streams equally
            else:
                stream_type = 'neutral'  # Default

        bias_str = json.dumps(bias_vector) if bias_vector is not None else None
        self.db.upsert_persona_profile(
            persona_id=persona_id,
            agent_id=self.agent_id,
            persona_type=persona_type,
            role=role,
            stage=stage,
            world_model=world_model,
            bias_vector=bias_str,
            bias_risk=bias_risk,
            bias_abstraction=bias_abstraction,
            bias_symbolic=bias_symbolic,
            novelty_bias=novelty_bias,
            persistence_class=persistence_class,
            lifetime_exposures=lifetime_exposures,
            stream_type=stream_type,  # FIX #9
        )
        self._persona_cache[persona_id] = {
            'persona_type': persona_type,
            'role': role,
            'stage': stage,
            'world_model': world_model,
            'bias_vector': bias_vector,
            'bias_risk': bias_risk,
            'bias_abstraction': bias_abstraction,
            'bias_symbolic': bias_symbolic,
            'novelty_bias': novelty_bias,
            'persistence_class': persistence_class,
            'lifetime_exposures': lifetime_exposures,
            'stream_type': stream_type,  # FIX #9
        }

    def _default_persona_id(self, rung: str) -> str:
        return f"persona_{rung}"

    def get_reliability(self, persona_id: str, problem_signature: Optional[str] = None) -> Dict[str, Any]:
        """Fetch reliability signals (global + context) for scoring.

        Returns:
            Dict with reliability_global (float) and reliability_context (float or None)
        """
        rel_global = None
        rel_context = None
        try:
            row = self.db.execute_query(
                "SELECT reliability_global FROM persona_profiles WHERE persona_id=?",
                (persona_id,),
            )
            if row:
                rel_global = row[0].get('reliability_global')
        except Exception:
            rel_global = None
        if problem_signature:
            try:
                crow = self.db.execute_query(
                    "SELECT reliability_score FROM persona_context_reliability WHERE persona_id=? AND problem_signature=?",
                    (persona_id, problem_signature),
                )
                if crow:
                    rel_context = crow[0].get('reliability_score')
            except Exception:
                rel_context = None
        return {
            'reliability_global': rel_global,
            'reliability_context': rel_context,
        }

    def build_problem_signature(
        self,
        *,
        game_id: Optional[str],
        level_number: Optional[int],
        frame: Optional[Any],
        world_model: Optional[str],
    ) -> str:
        game_prefix = (game_id.split('-')[0] if game_id else 'unknown').lower()
        level_tag = f"L{level_number}" if level_number is not None else "L?"
        shape_tag = "grid_?"
        unique_colors = 0
        object_cells = 0
        component_count = None
        largest_component = 0
        symmetry_tag = "sym_unknown"
        pattern_tag = "pattern_unknown"
        control_ratio = None
        try:
            if frame and isinstance(frame, list) and frame and isinstance(frame[0], list):
                rows = len(frame)
                cols = len(frame[0])
                shape_tag = f"grid_{rows}x{cols}"
                # Simple stats: unique colors and non-zero cells as object proxy
                colors = set()
                non_zero_colors = set()
                component_count = 0
                visited = set()
                def _neighbors(r: int, c: int) -> List[tuple[int, int]]:
                    return [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
                def _flood(r: int, c: int, color: Any) -> int:
                    stack = [(r, c)]
                    size = 0
                    while stack:
                        cr, cc = stack.pop()
                        if (cr, cc) in visited:
                            continue
                        if cr < 0 or cc < 0 or cr >= rows or cc >= cols:
                            continue
                        if frame[cr][cc] != color:
                            continue
                        visited.add((cr, cc))
                        size += 1
                        for nr, nc in _neighbors(cr, cc):
                            if (nr, nc) not in visited:
                                stack.append((nr, nc))
                    return size
                # Simple symmetry heuristic: horizontal mirror check on small grids
                try:
                    if rows and cols and rows == len(frame):
                        if all(frame[r] == list(reversed(frame[r])) for r in range(rows)):
                            symmetry_tag = "sym_horizontal"
                        elif all(frame[r] == frame[rows - r - 1] for r in range(rows // 2)):
                            symmetry_tag = "sym_vertical"
                except Exception:
                    symmetry_tag = "sym_unknown"
                for r in frame:
                    for c in r:
                        colors.add(c)
                        if c != 0:
                            non_zero_colors.add(c)
                        if c != 0:
                            object_cells += 1
                # Component count and largest component size (quick flood fill)
                try:
                    for ri in range(rows):
                        for ci in range(cols):
                            cell_color = frame[ri][ci]
                            if cell_color == 0 or (ri, ci) in visited:
                                continue
                            comp_size = _flood(ri, ci, cell_color)
                            if comp_size > 0:
                                component_count = (component_count or 0) + 1
                                largest_component = max(largest_component, comp_size)
                except Exception:
                    component_count = component_count or None
                # Simple pattern heuristics: stripes or checkerboard-like
                try:
                    if rows and cols:
                        row_patterns = len({tuple(row) for row in frame})
                        col_patterns = len({tuple(col) for col in zip(*frame)}) if cols else 0
                        if row_patterns == 1:
                            pattern_tag = "pattern_horizontal_stripe"
                        elif col_patterns == 1:
                            pattern_tag = "pattern_vertical_stripe"
                        elif row_patterns <= 3 and col_patterns <= 3:
                            pattern_tag = "pattern_repeated"
                        elif symmetry_tag != "sym_unknown":
                            pattern_tag = "pattern_symmetric"
                except Exception:
                    pattern_tag = "pattern_unknown"
                unique_colors = len(colors)
                unique_non_zero = len(non_zero_colors)
                total_cells = rows * cols if rows and cols else 0
                if total_cells:
                    control_ratio = round(object_cells / float(total_cells), 3)
        except Exception:
            pass
        wm_tag = world_model or "world_unknown"
        color_tag = f"colors_{unique_colors}" if unique_colors else "colors_?"
        color_nz_tag = f"colorsnz_{unique_non_zero}" if locals().get('unique_non_zero') else "colorsnz_?"
        obj_tag = f"objcells_{object_cells}" if object_cells else "objcells_?"
        comp_tag = f"comp_{component_count}" if component_count is not None else "comp_?"
        largest_tag = f"largest_{largest_component}" if largest_component else "largest_?"
        ctrl_tag = f"ctrl_{control_ratio}" if control_ratio is not None else "ctrl_?"
        sym_tag = symmetry_tag or "sym_unknown"
        pattern_tag = pattern_tag or "pattern_unknown"
        return f"{game_prefix}:{level_tag}:{shape_tag}:{color_tag}:{color_nz_tag}:{obj_tag}:{comp_tag}:{largest_tag}:{ctrl_tag}:{sym_tag}:{pattern_tag}:{wm_tag}"

    def _log_proposals(
        self,
        proposals: List[Dict[str, Any]],
        *,
        game_id: Optional[str],
        level_number: Optional[int],
        step_idx: Optional[int],
        world_model: Optional[str],
        problem_signature: Optional[str],
        self_identity_snapshot: Optional[Dict[str, Any]],
    ) -> Optional[PersonaDecision]:
        chosen: Optional[PersonaDecision] = None
        sis_json = json.dumps(self_identity_snapshot) if self_identity_snapshot is not None else None
        for proposal in proposals:
            persona_id = proposal.get('persona_id') or self._default_persona_id(proposal.get('rung', 'unknown'))
            self.ensure_persona(
                persona_id,
                world_model=world_model,
                persona_type=proposal.get('persona_type'),
                bias_vector=proposal.get('bias_vector'),
                bias_risk=proposal.get('bias_risk'),
                bias_abstraction=proposal.get('bias_abstraction'),
                bias_symbolic=proposal.get('bias_symbolic'),
                novelty_bias=proposal.get('novelty_bias'),
            )
            payload = {
                'proposal_id': proposal.get('proposal_id') or f"pp_{uuid.uuid4().hex[:12]}",
                'persona_id': persona_id,
                'agent_id': self.agent_id,
                'persona_type': proposal.get('persona_type'),
                'game_id': game_id,
                'session_id': proposal.get('session_id'),
                'level_number': level_number,
                'step_idx': step_idx,
                'problem_signature': problem_signature,
                'world_model': world_model,
                'self_identity_snapshot': sis_json,
                'action': proposal.get('action'),
                'rationale_embedding': proposal.get('rationale_embedding'),
                'confidence': proposal.get('confidence', 0.5),
                'safety_flag': proposal.get('safety_flag', False),
                'novelty_flag': proposal.get('novelty_flag', False),
                'surprise_score': proposal.get('surprise_score'),
                'observer_flags': json.dumps(proposal.get('observer_flags')) if isinstance(proposal.get('observer_flags'), dict) else proposal.get('observer_flags'),
                'synthesis_source': proposal.get('synthesis_source'),
                'scorer_score': proposal.get('scorer_score'),
                'chosen': bool(proposal.get('chosen')),
            }
            proposal_id = self.db.log_persona_proposal(payload)
            proposal['proposal_id'] = proposal_id
            if proposal.get('persona_type') == 'observer':
                try:
                    self.record_observer_output(
                        proposal_id=proposal_id,
                        persona_id=persona_id,
                        problem_signature=problem_signature,
                        observer_flags=proposal.get('observer_flags') or {},
                    )
                except Exception:
                    pass
            if payload.get('chosen'):
                chosen = PersonaDecision(
                    persona_id=persona_id,
                    proposal_id=proposal_id,
                    problem_signature=problem_signature,
                    world_model=world_model,
                    step_idx=step_idx,
                    level_number=level_number,
                    game_id=game_id,
                    action=proposal.get('action'),
                )
        return chosen

    def record_from_ladder(
        self,
        ladder_trace: Dict[str, Dict[str, Any]],
        *,
        chosen_action: str,
        _chosen_reason: str,
        chosen_rung: str,
        game_id: Optional[str],
        level_number: Optional[int],
        step_idx: Optional[int],
        world_model: Optional[str],
        problem_signature: Optional[str],
        self_identity_snapshot: Optional[Dict[str, Any]],
        enable_synthesis: bool = True,
        max_proposals: Optional[int] = None,
    ) -> Dict[str, Any]:
        proposals: List[Dict[str, Any]] = []
        # Represent each rung as a persona proposal; mark the chosen rung
        for rung, info in ladder_trace.items():
            rung_status = (info or {}).get('status')
            rung_reason = (info or {}).get('reason')
            is_chosen = rung == chosen_rung
            persona_type = (info or {}).get('persona_type') or ('action' if rung != 'observer' else 'observer')
            observer_flags = (info or {}).get('observer_flags')
            proposals.append({
                'persona_id': self._default_persona_id(rung),
                'persona_type': persona_type,
                'rung': rung,
                'action': chosen_action if is_chosen else None,
                'confidence': 0.65 if is_chosen else 0.25,
                'safety_flag': False,
                'novelty_flag': rung == 'heuristic',
                'observer_flags': observer_flags or {'ladder_reason': rung_reason, 'ladder_status': rung_status},
                'scorer_score': info.get('score') if isinstance(info, dict) else None,
                'chosen': is_chosen,
            })

        # Simple interpolation synthesis: aggregate top two scores if multiple rungs present
        if enable_synthesis and len(proposals) >= 2:
            sorted_props = sorted(proposals, key=lambda p: p.get('scorer_score') or 0, reverse=True)
            top = sorted_props[0]
            second = sorted_props[1]
            synth_action = top.get('action') or chosen_action
            synth_conf = ((top.get('confidence') or 0.5) + (second.get('confidence') or 0.25)) / 2
            synth_mode = 'interpolation'
            try:
                if top.get('action') and second.get('action') and top.get('action') != second.get('action'):
                    synth_mode = 'dialectical'
                if len(sorted_props) >= 3:
                    synth_mode = 'compositional'
            except Exception:
                synth_mode = 'interpolation'
            proposals.append({
                'persona_id': 'persona_synthesis',
                'persona_type': 'synthesis',
                'rung': 'synthesis',
                'action': synth_action,
                'confidence': synth_conf,
                'safety_flag': bool(top.get('safety_flag')) or bool(second.get('safety_flag')),
                'novelty_flag': bool(top.get('novelty_flag')) or bool(second.get('novelty_flag')),
                'observer_flags': {'sources': [top.get('rung'), second.get('rung')], 'synthesis_mode': synth_mode},
                'synthesis_source': f"{top.get('persona_id')},{second.get('persona_id')}",
                'synthesis_mode': synth_mode,
                'scorer_score': max(top.get('scorer_score') or 0, second.get('scorer_score') or 0),
                'chosen': False,
            })

        # Optional budget-aware trimming: keep chosen rung and top-scoring others
        if max_proposals is not None and max_proposals > 0 and len(proposals) > max_proposals:
            chosen_list = [p for p in proposals if p.get('chosen')]
            others = [p for p in proposals if not p.get('chosen')]
            others_sorted = sorted(others, key=lambda p: p.get('scorer_score') or 0, reverse=True)
            trimmed: List[Dict[str, Any]] = []
            if chosen_list:
                trimmed.append(chosen_list[0])
            for p in others_sorted:
                if len(trimmed) >= max_proposals:
                    break
                trimmed.append(p)
            proposals = trimmed[:max_proposals]

        decision = self._log_proposals(
            proposals,
            game_id=game_id,
            level_number=level_number,
            step_idx=step_idx,
            world_model=world_model,
            problem_signature=problem_signature,
            self_identity_snapshot=self_identity_snapshot,
        )
        logged = []
        if proposals:
            for p in proposals:
                if 'persona_id' in p:
                    logged.append({'persona_id': p['persona_id'], 'chosen': p.get('chosen', False), 'proposal_id': p.get('proposal_id')})
        return {'decision': decision, 'logged': logged, 'proposal_count': len(proposals)}

    def record_outcome(
        self,
        decision: PersonaDecision,
        *,
        delta_score: Optional[float],
        delta_actions: Optional[int],
        outcome_score: Optional[float],
        safety_incident: bool,
        surprise_score: Optional[float],
        stuck_flag: bool,
        observer_flags: Optional[Dict[str, Any]] = None,
    ) -> None:
        obs = observer_flags or {}
        payload = {
            'proposal_id': decision.proposal_id,
            'persona_id': decision.persona_id,
            'agent_id': self.agent_id,
            'game_id': decision.game_id,
            'level_number': decision.level_number,
            'delta_score': delta_score,
            'delta_actions': delta_actions,
            'outcome_score': outcome_score,
            'safety_incident': safety_incident,
            'surprise_score': surprise_score,
            'stuck_flag': stuck_flag,
            'observer_flags': json.dumps(observer_flags) if isinstance(observer_flags, dict) else observer_flags,
            'observer_stuckness': obs.get('stuckness'),
            'observer_control_loss': obs.get('control_loss'),
            'observer_confidence_trend': obs.get('confidence_trend'),
            'observer_pattern_tag': obs.get('pattern_tag'),
            'observer_suggested_approach': obs.get('suggested_approach'),
            'observer_veto_unsafe': obs.get('veto_unsafe'),
        }
        self.db.log_persona_outcome(payload)
        # Update global reliability and exposures
        try:
            reliability_delta = 0.0
            if delta_score is not None:
                if delta_score > 0:
                    reliability_delta += 0.05
                elif delta_score < 0:
                    reliability_delta -= 0.05
            if safety_incident:
                reliability_delta -= 0.1
            # Surprise-driven attribution for chosen persona
            if surprise_score is not None:
                try:
                    s = float(surprise_score)
                    if s >= 0.8 and delta_score and delta_score > 0:
                        reliability_delta += 0.03
                    elif s >= 0.8 and delta_score and delta_score < 0:
                        reliability_delta -= 0.03
                except Exception:
                    pass
            current_rel = None
            try:
                row = self.db.execute_query(
                    "SELECT reliability_global, lifetime_exposures FROM persona_profiles WHERE persona_id=?",
                    (decision.persona_id,),
                )
                if row:
                    current_rel = row[0].get('reliability_global')
                    exposures = row[0].get('lifetime_exposures') or 0
                else:
                    exposures = 0
            except Exception:
                exposures = 0
            new_rel = max(0.0, min(1.0, (current_rel if current_rel is not None else 0.5) + reliability_delta))
            self.db.upsert_persona_profile(
                persona_id=decision.persona_id,
                agent_id=self.agent_id,
                reliability_global=new_rel,
                lifetime_exposures=(exposures + 1),
            )
            self._update_persistence_class(decision.persona_id)
            # Observer calibration: if observer persona, align reliability with stuckness/control flags
            if decision.persona_id.startswith('persona_observer'):
                try:
                    predicted_stuck = obs.get('stuckness') or 0.0
                    actual_stuck = 1.0 if stuck_flag else 0.0
                    delta = actual_stuck - predicted_stuck
                    cal_adj = -0.03 if abs(delta) > 0.5 else 0.02
                    adj_rel = max(0.0, min(1.0, new_rel + cal_adj))
                    self.db.upsert_persona_profile(
                        persona_id=decision.persona_id,
                        agent_id=self.agent_id,
                        reliability_global=adj_rel,
                        lifetime_exposures=(exposures + 1),
                    )
                except Exception:
                    pass
        except Exception:
            pass
        if decision.problem_signature:
            self.db.update_persona_context_reliability(
                persona_id=decision.persona_id,
                problem_signature=decision.problem_signature,
                delta_score=delta_score,
                safety_incident=safety_incident,
            )

    def record_hindsight_outcomes(
        self,
        logged_entries: List[Dict[str, Any]],
        *,
        problem_signature: Optional[str],
        delta_score: Optional[float],
        safety_incident: bool,
        surprise_score: Optional[float] = None,
        max_entries: int = 5,
    ) -> None:
        if not logged_entries or not problem_signature:
            return
        # Budget guard: only a small sample per step
        for entry in logged_entries[:max_entries]:
            persona_id = entry.get('persona_id')
            if not persona_id:
                continue
            # Smaller adjustment for unchosen personas
            bonus = 0.3
            if surprise_score is not None:
                try:
                    if float(surprise_score) >= 0.8:
                        bonus = 0.45
                    elif float(surprise_score) >= 0.5:
                        bonus = 0.35
                except Exception:
                    bonus = 0.3
            self.db.update_persona_context_reliability(
                persona_id=persona_id,
                problem_signature=problem_signature,
                delta_score=(delta_score or 0) * bonus,
                safety_incident=safety_incident,
            )
            # Light-touch global reliability adjustment for hindsight (reduced rate)
            try:
                row = self.db.execute_query(
                    "SELECT reliability_global, lifetime_exposures FROM persona_profiles WHERE persona_id=?",
                    (persona_id,),
                )
                if row:
                    rel_g = row[0].get('reliability_global')
                    exposures = row[0].get('lifetime_exposures') or 0
                    adj = 0.02 if (delta_score or 0) > 0 else (-0.02 if (delta_score or 0) < 0 else 0.0)
                    new_rel = max(0.0, min(1.0, (rel_g if rel_g is not None else 0.5) + adj))
                    self.db.upsert_persona_profile(
                        persona_id=persona_id,
                        agent_id=self.agent_id,
                        reliability_global=new_rel,
                        lifetime_exposures=exposures + 1,
                    )
            except Exception:
                pass
            try:
                self.db.log_persona_hindsight(
                    {
                        'original_proposal_id': entry.get('proposal_id'),
                        'alternative_persona_id': persona_id,
                        'agent_id': self.agent_id,
                        'problem_signature': problem_signature,
                        'estimated_outcome': delta_score,
                        'retrospective_credit': (delta_score or 0) * bonus,
                        'surprise_score': surprise_score,
                        'observer_flags': None,
                    }
                )
            except Exception:
                pass

    def record_observer_output(
        self,
        *,
        proposal_id: Optional[str],
        persona_id: Optional[str],
        problem_signature: Optional[str],
        observer_flags: Dict[str, Any],
    ) -> None:
        try:
            self.db.log_observer_output(
                {
                    'proposal_id': proposal_id,
                    'persona_id': persona_id,
                    'agent_id': self.agent_id,
                    'problem_signature': problem_signature,
                    'stuckness_level': observer_flags.get('stuckness'),
                    'control_loss': observer_flags.get('control_loss'),
                    'confidence_trend': observer_flags.get('confidence_trend'),
                    'pattern_tag': observer_flags.get('pattern_tag'),
                    'suggested_approach': observer_flags.get('suggested_approach'),
                    'veto_unsafe': observer_flags.get('veto_unsafe'),
                }
            )
        except Exception:
            pass

    def record_hindsight_credit(
        self,
        *,
        original_proposal_id: str,
        alternative_persona_id: Optional[str],
        problem_signature: Optional[str],
        estimated_outcome: Optional[float],
        retrospective_credit: Optional[float],
        surprise_score: Optional[float],
        observer_flags: Optional[Dict[str, Any]] = None,
        max_entries: int = 5,
    ) -> None:
        try:
            self.db.log_persona_hindsight(
                {
                    'original_proposal_id': original_proposal_id,
                    'alternative_persona_id': alternative_persona_id,
                    'agent_id': self.agent_id,
                    'problem_signature': problem_signature,
                    'estimated_outcome': estimated_outcome,
                    'retrospective_credit': retrospective_credit,
                    'surprise_score': surprise_score,
                    'observer_flags': json.dumps(observer_flags) if isinstance(observer_flags, dict) else observer_flags,
                }
            )
        except Exception:
            pass

    def record_metrics(
        self,
        *,
        problem_signature: Optional[str],
        synthesis_used: bool,
        observer_veto: bool,
        micro_cf_used: bool,
        hindsight_updates: int,
    ) -> None:
        """Record lightweight monitoring metrics to DB."""
        try:
            core_ratio = None
            diversity_count = None
            try:
                rows = self.db.execute_query(
                    "SELECT persistence_class FROM persona_profiles WHERE agent_id=?",
                    (self.agent_id,),
                )
                if rows:
                    total = len(rows)
                    core = sum(1 for r in rows if (r.get('persistence_class') or '').lower() == 'core')
                    diversity_count = len(set((r.get('persistence_class') or 'unknown') for r in rows))
                    if total:
                        core_ratio = round(core / float(total), 3)
            except Exception:
                core_ratio = None
            self.db.log_persona_metrics(
                {
                    'agent_id': self.agent_id,
                    'problem_signature': problem_signature,
                    'synthesis_used': synthesis_used,
                    'observer_veto': observer_veto,
                    'micro_cf_used': micro_cf_used,
                    'hindsight_updates': hindsight_updates,
                    'core_ratio': core_ratio,
                    'diversity_count': diversity_count,
                }
            )
        except Exception:
            pass

    def _update_persistence_class(self, persona_id: str) -> None:
        """Promote/demote based on reliability and exposures."""
        try:
            row = self.db.execute_query(
                "SELECT reliability_global, lifetime_exposures, persistence_class, novelty_bias FROM persona_profiles WHERE persona_id=?",
                (persona_id,),
            )
            if not row:
                return
            rel = row[0].get('reliability_global') or 0.5
            exposures = row[0].get('lifetime_exposures') or 0
            current = row[0].get('persistence_class') or 'tactical'
            novelty = row[0].get('novelty_bias') or 0.0
            new_class = current
            # Promotion: strong reliability with experience
            if rel >= 0.7 and exposures >= 10:
                new_class = 'core'
            # Diversity guard: keep at least one high-novelty core
            if novelty >= 0.6 and rel >= 0.5 and exposures >= 8:
                new_class = 'core'
            # Demotion: weak reliability with sufficient trials
            if rel <= 0.25 and exposures >= 6:
                new_class = 'experimental'
            if new_class != current:
                self.db.upsert_persona_profile(
                    persona_id=persona_id,
                    agent_id=self.agent_id,
                    persistence_class=new_class,
                )
        except Exception:
            pass

    def enforce_lifecycle(
        self,
        *,
        min_personas: int = 3,
        max_experimental: int = 6,
        stalled: bool = False,
        stage: Optional[int] = None,
    ) -> None:
        """Lightweight lifecycle maintenance: prune weak, enforce minimum ensemble, spawn on stall.

        Includes PersonaBudgetManager hard limits from agent_consciousness_synthesis.md:
        - MAX_ACTIVE_PERSONAS = 12 (absolute cap)
        - MAX_TEMPORARY_PERSONAS = 5
        - Aggressive pruning if over limit

        Stage gating: no-op below stage 3 unless stalled.
        """
        if not self.agent_id:
            return
        if (stage or 0) < 3 and not stalled:
            return
        try:
            rows = self.db.execute_query(
                "SELECT persona_id, persistence_class, reliability_global, lifetime_exposures, novelty_bias, persona_type FROM persona_profiles WHERE agent_id=?",
                (self.agent_id,),
            )
        except Exception:
            return
        personas = rows or []

        # ===================================================================
        # HARD LIMIT ENFORCEMENT: Prune if over MAX_ACTIVE_PERSONAS
        # ===================================================================
        if len(personas) > MAX_ACTIVE_PERSONAS:
            # Sort by reliability, prune lowest-reliability non-core personas
            sorted_by_rel = sorted(personas, key=lambda p: (
                0 if (p.get('persistence_class') or '').lower() == 'core' else 1,  # Core last
                p.get('reliability_global') or 0.0  # Low reliability first
            ))

            pruned_count = 0
            for p in sorted_by_rel:
                if len(personas) - pruned_count <= MAX_ACTIVE_PERSONAS:
                    break
                if (p.get('persistence_class') or '').lower() == 'core':
                    continue  # Never prune core
                try:
                    self.db.execute_query(
                        "DELETE FROM persona_profiles WHERE persona_id=? AND agent_id=?",
                        (p.get('persona_id'), self.agent_id),
                    )
                    pruned_count += 1
                except Exception:
                    pass

        # ===================================================================
        # TEMPORARY LIMIT ENFORCEMENT: Prune temporary if over limit
        # ===================================================================
        temp_personas = [p for p in personas if (p.get('persistence_class') or '').lower() == 'temporary']
        if len(temp_personas) > MAX_TEMPORARY_PERSONAS:
            # Prune oldest temporary personas
            sorted_temp = sorted(temp_personas, key=lambda p: p.get('lifetime_exposures') or 0, reverse=True)
            for p in sorted_temp[MAX_TEMPORARY_PERSONAS:]:
                try:
                    self.db.execute_query(
                        "DELETE FROM persona_profiles WHERE persona_id=? AND agent_id=?",
                        (p.get('persona_id'), self.agent_id),
                    )
                except Exception:
                    pass

        # Prune weak experimental personas with sufficient exposure
        try:
            for row in list(personas):
                cls = (row.get('persistence_class') or 'experimental').lower()
                rel = row.get('reliability_global') or 0.0
                exposures = row.get('lifetime_exposures') or 0
                if cls == 'experimental' and exposures >= 6 and rel <= 0.25:
                    try:
                        self.db.execute_query(
                            "DELETE FROM persona_profiles WHERE persona_id=? AND agent_id=?",
                            (row.get('persona_id'), self.agent_id),
                        )
                    except Exception:
                        pass
        except Exception:
            pass

        # Refresh list after pruning
        try:
            rows = self.db.execute_query(
                "SELECT persona_id, persistence_class, reliability_global, lifetime_exposures, novelty_bias, persona_type FROM persona_profiles WHERE agent_id=?",
                (self.agent_id,),
            )
            personas = rows or []
        except Exception:
            pass

        # Ensure minimum ensemble size (respecting hard limits)
        try:
            while len(personas) < min_personas and len(personas) < MAX_ACTIVE_PERSONAS:
                allowed, reason = self.can_spawn_persona('experimental')
                if not allowed:
                    break
                pid = f"persona_auto_{uuid.uuid4().hex[:8]}"
                novelty_bias = 0.5 + 0.1 * (len(personas) % 2)
                bias_risk = 0.3 + 0.1 * (len(personas) % 3)
                self.ensure_persona(
                    pid,
                    persona_type='action',
                    persistence_class='experimental',
                    novelty_bias=novelty_bias,
                    bias_risk=bias_risk,
                )
                personas.append({'persona_id': pid, 'persistence_class': 'experimental', 'reliability_global': 0.5, 'lifetime_exposures': 0, 'novelty_bias': novelty_bias})
        except Exception:
            pass

        # Spawn extra experimental when stalled and below cap (respecting hard limits)
        try:
            if stalled and (stage or 0) >= 3:
                exp_count = sum(1 for p in personas if (p.get('persistence_class') or 'experimental').lower() == 'experimental')
                allowed, reason = self.can_spawn_persona('experimental')
                if exp_count < max_experimental and allowed and len(personas) < MAX_ACTIVE_PERSONAS:
                    pid = f"persona_auto_{uuid.uuid4().hex[:8]}"
                    self.ensure_persona(
                        pid,
                        persona_type='action',
                        persistence_class='experimental',
                        novelty_bias=0.7,
                        bias_risk=0.4,
                    )
                    personas.append({'persona_id': pid, 'persistence_class': 'experimental', 'reliability_global': 0.5, 'lifetime_exposures': 0, 'novelty_bias': 0.7})
        except Exception:
            pass

        # Promote a reliable persona to core if none exist
        try:
            has_core = any((p.get('persistence_class') or '').lower() == 'core' for p in personas)
            if not has_core:
                candidates = sorted(personas, key=lambda p: p.get('reliability_global') or 0.0, reverse=True)
                for cand in candidates:
                    persona_id = cand.get('persona_id')
                    if not persona_id:
                        continue
                    rel = cand.get('reliability_global') or 0.0
                    exposures = cand.get('lifetime_exposures') or 0
                    if rel >= 0.6 and exposures >= 6:
                        self.db.upsert_persona_profile(
                            persona_id=persona_id,
                            agent_id=self.agent_id,
                            persistence_class='core',
                        )
                        break
        except Exception:
            pass

        # Diversity guard: ensure at least one high-novelty core
        try:
            core_novel = any((p.get('persistence_class') or '').lower() == 'core' and (p.get('novelty_bias') or 0.0) >= 0.6 for p in personas)
            if not core_novel:
                high_novel = sorted(personas, key=lambda p: p.get('novelty_bias') or 0.0, reverse=True)
                for cand in high_novel:
                    persona_id = cand.get('persona_id')
                    if not persona_id:
                        continue
                    if (cand.get('novelty_bias') or 0.0) >= 0.6:
                        self.db.upsert_persona_profile(
                            persona_id=persona_id,
                            agent_id=self.agent_id,
                            persistence_class='core',
                        )
                        break
        except Exception:
            pass
