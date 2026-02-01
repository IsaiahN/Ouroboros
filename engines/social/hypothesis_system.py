"""
Agent Hypothesis System - Agent-initiated hypothesis creation and testing.

Enables agents to CREATE hypotheses, not just follow them.

Key insight: Formal operational agents should be able to:
1. Notice patterns in their experience
2. Formulate testable hypotheses
3. Design experiments to test them
4. Update beliefs based on results

This requires FORMAL_OPERATIONAL cognitive stage.

Also includes Mortality Awareness features:
- Legacy computation: What have I contributed that will survive me?
- Dying thoughts: Record final wisdom before retirement
- Memento mori: Periodic mortality reflection
"""

import json
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from database_interface import DatabaseInterface
    from engines.cognition.cognitive_stages import CognitiveStageSystem

from engines.engine_logger import get_engine_logger, log_silent_failure

logger = get_engine_logger("hypothesis_system")


class AgentHypothesisSystem:
    """
    Enables agents to CREATE hypotheses, not just follow them.
    
    Key insight: Formal operational agents should be able to:
    1. Notice patterns in their experience
    2. Formulate testable hypotheses
    3. Design experiments to test them
    4. Update beliefs based on results
    
    This requires FORMAL_OPERATIONAL cognitive stage.
    """
    
    def __init__(self, db: 'DatabaseInterface', cognitive_system: 'CognitiveStageSystem'):
        """Initialize agent hypothesis system."""
        self.db = db
        self.cognitive_system = cognitive_system
        self._ensure_tables()
    
    def _ensure_tables(self) -> None:
        """Ensure agent hypothesis tables exist."""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS agent_hypotheses (
                hypothesis_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                
                -- Hypothesis content
                game_type TEXT NOT NULL,
                level_number INTEGER,
                hypothesis_text TEXT NOT NULL,
                hypothesis_type TEXT NOT NULL,  -- 'object_behavior', 'action_effect', 'sequence_pattern', 'game_rule'
                
                -- PRIMITIVE-AWARE HYPOTHESIS STRUCTURE
                -- Hypotheses are now expressed in terms of primitives + actions
                primitives_used TEXT,            -- JSON: list of primitives referenced in this hypothesis
                trigger_condition TEXT,          -- JSON: {primitive: name, params: {...}} - what triggers the action
                predicted_action TEXT,           -- ACTION1-ACTION7 that the hypothesis suggests
                action_sequence TEXT,            -- JSON: sequence of actions if multi-step
                
                -- Evidence and confidence
                supporting_evidence TEXT,        -- JSON: list of observations supporting this
                contradicting_evidence TEXT,     -- JSON: list of observations against this
                confidence REAL DEFAULT 0.5,
                
                -- Testing
                tests_conducted INTEGER DEFAULT 0,
                tests_successful INTEGER DEFAULT 0,
                last_tested DATETIME,
                
                -- Status
                status TEXT DEFAULT 'proposed',  -- 'proposed', 'testing', 'confirmed', 'refuted', 'abandoned'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)
        
        # Add new columns if table already exists (migration)
        try:
            self.db.execute_query("ALTER TABLE agent_hypotheses ADD COLUMN primitives_used TEXT")
        except Exception:
            pass  # Column already exists - expected
        try:
            self.db.execute_query("ALTER TABLE agent_hypotheses ADD COLUMN trigger_condition TEXT")
        except Exception:
            pass  # Column already exists - expected
        try:
            self.db.execute_query("ALTER TABLE agent_hypotheses ADD COLUMN predicted_action TEXT")
        except Exception:
            pass  # Column already exists - expected
        try:
            self.db.execute_query("ALTER TABLE agent_hypotheses ADD COLUMN action_sequence TEXT")
        except Exception:
            pass  # Column already exists - expected
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_agent_hypotheses_game 
            ON agent_hypotheses(game_type, level_number, status)
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_agent_hypotheses_agent 
            ON agent_hypotheses(agent_id, status)
        """)

        # Telemetry for hypothesis promotion/decay events (DB-only)
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacog_hypothesis_events (
                event_id TEXT PRIMARY KEY,
                hypothesis_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                event_type TEXT NOT NULL,         -- 'promotion', 'decay'
                from_status TEXT,
                to_status TEXT,
                confidence_before REAL,
                confidence_after REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def can_create_hypothesis(self, agent_id: str) -> bool:
        """Check if agent has the cognitive capability to create hypotheses."""
        capabilities = self.cognitive_system.get_stage_capabilities(agent_id)
        return capabilities.get('hypothesis_generation', False)
    
    def create_hypothesis(
        self,
        agent_id: str,
        game_type: str,
        hypothesis_text: str,
        hypothesis_type: str,
        level_number: Optional[int] = None,
        initial_evidence: Optional[List[str]] = None,
        primitives_used: Optional[List[str]] = None,
        trigger_condition: Optional[Dict[str, Any]] = None,
        predicted_action: Optional[str] = None,
        action_sequence: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Agent creates a new hypothesis based on observations.
        
        Only agents in FORMAL_OPERATIONAL stage can create hypotheses.
        
        PRIMITIVE-AWARE HYPOTHESES:
        Hypotheses can now be expressed in terms of:
        - primitives_used: Which primitives inform this hypothesis
        - trigger_condition: {primitive: 'detect_color_change', params: {color: 'red'}}
        - predicted_action: 'ACTION2' - what to do when trigger fires
        - action_sequence: ['ACTION2', 'ACTION4'] - multi-step response
        
        Args:
            agent_id: Agent creating hypothesis
            game_type: Game type this applies to
            hypothesis_text: Natural language hypothesis
            hypothesis_type: Category ('object_behavior', 'action_effect', 'sequence_pattern', 'game_rule')
            level_number: Optional specific level
            initial_evidence: List of observations supporting this hypothesis
            primitives_used: List of primitive names used in this hypothesis
            trigger_condition: Dict with primitive and params that trigger the action
            predicted_action: Single action prediction (ACTION1-ACTION7)
            action_sequence: Sequence of actions if multi-step
            
        Returns:
            hypothesis_id if created, None if agent lacks capability
        """
        if not self.can_create_hypothesis(agent_id):
            logger.debug(f"[HYPOTHESIS] Agent {agent_id[:8]} lacks cognitive stage for hypothesis creation")
            return None
        
        hypothesis_id = f"hyp_{uuid.uuid4().hex[:12]}"
        
        evidence_json = json.dumps(initial_evidence or [])
        primitives_json = json.dumps(primitives_used or [])
        trigger_json = json.dumps(trigger_condition) if trigger_condition else None
        sequence_json = json.dumps(action_sequence) if action_sequence else None
        
        self.db.execute_query("""
            INSERT INTO agent_hypotheses 
            (hypothesis_id, agent_id, game_type, level_number, hypothesis_text, 
             hypothesis_type, supporting_evidence, confidence, status,
             primitives_used, trigger_condition, predicted_action, action_sequence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?, ?, ?)
        """, (hypothesis_id, agent_id, game_type, level_number, hypothesis_text,
              hypothesis_type, evidence_json, 0.5,
              primitives_json, trigger_json, predicted_action, sequence_json))
        
        # Update agent's competency
        self.cognitive_system.update_competencies(agent_id, hypotheses_created_delta=1)
        
        # Log with primitive info if available
        if primitives_used:
            logger.info(f"[HYPOTHESIS] Agent {agent_id[:8]} created primitive-aware: {hypothesis_text[:40]}... using {primitives_used}")
        else:
            logger.info(f"[HYPOTHESIS] Agent {agent_id[:8]} created: {hypothesis_text[:50]}...")
        
        return hypothesis_id

    def _log_hypothesis_event(
        self,
        *,
        hypothesis_id: str,
        agent_id: str,
        event_type: str,
        from_status: Optional[str],
        to_status: Optional[str],
        confidence_before: Optional[float],
        confidence_after: Optional[float]
    ) -> None:
        """Record promotion/decay telemetry (DB-only)."""
        try:
            event_id = f"h_evt_{uuid.uuid4().hex[:12]}"
            self.db.execute_query(
                """
                INSERT INTO metacog_hypothesis_events (
                    event_id, hypothesis_id, agent_id, event_type,
                    from_status, to_status, confidence_before, confidence_after
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    hypothesis_id,
                    agent_id,
                    event_type,
                    from_status,
                    to_status,
                    confidence_before,
                    confidence_after,
                ),
            )
        except Exception as e:
            logger.debug(f"[HYPOTHESIS] Event log failed: {e}")
    
    def record_test_result(
        self,
        hypothesis_id: str,
        success: bool,
        observation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record the result of testing a hypothesis.
        
        Returns updated hypothesis status and confidence.
        """
        # Get current hypothesis
        result = self.db.execute_query("""
            SELECT * FROM agent_hypotheses WHERE hypothesis_id = ?
        """, (hypothesis_id,))
        
        if not result:
            return {'error': 'hypothesis_not_found'}
        
        h = result[0]
        
        # Update test counts
        tests = h['tests_conducted'] + 1
        successes = h['tests_successful'] + (1 if success else 0)
        
        # Calculate new confidence using Bayesian-ish update
        prior = h['confidence']
        if success:
            new_confidence = prior + (1.0 - prior) * 0.2  # Move toward 1.0
        else:
            new_confidence = prior * 0.8  # Decay toward 0
        
        new_confidence = max(0.05, min(0.95, new_confidence))
        
        # Update evidence
        evidence_key = 'supporting_evidence' if success else 'contradicting_evidence'
        existing_evidence = json.loads(h[evidence_key] or '[]')
        if observation:
            existing_evidence.append(observation)
        # Full game memory - keep all evidence during game (was [-10:] goldfish window)
        # Hypothesis validation needs full evidence history
        # Safety cap at 500 for JSON storage efficiency
        evidence_json = json.dumps(existing_evidence[-500:] if len(existing_evidence) > 500 else existing_evidence)
        
        # Determine status
        status = h['status']
        if new_confidence > 0.85 and tests >= 3:
            status = 'confirmed'
        elif new_confidence < 0.15 and tests >= 3:
            status = 'refuted'
        elif status == 'proposed':
            status = 'testing'

        # Telemetry: log promotion/decay when status changes or confidence drops
        try:
            event_type = None
            from_status = h['status']
            to_status = status

            if to_status != from_status:
                event_type = 'promotion' if to_status in {'testing', 'confirmed'} else 'decay'
            elif new_confidence < prior:
                event_type = 'decay'

            if event_type:
                self._log_hypothesis_event(
                    hypothesis_id=hypothesis_id,
                    agent_id=h['agent_id'],
                    event_type=event_type,
                    from_status=from_status,
                    to_status=to_status,
                    confidence_before=prior,
                    confidence_after=new_confidence,
                )
        except Exception as e:
            log_silent_failure(logger, "hypothesis_event_logging", e, {"hypothesis_id": hypothesis_id})
        
        self.db.execute_query(f"""
            UPDATE agent_hypotheses
            SET tests_conducted = ?,
                tests_successful = ?,
                confidence = ?,
                {evidence_key} = ?,
                status = ?,
                last_tested = CURRENT_TIMESTAMP
            WHERE hypothesis_id = ?
        """, (tests, successes, new_confidence, evidence_json, status, hypothesis_id))
        
        return {
            'hypothesis_id': hypothesis_id,
            'new_confidence': new_confidence,
            'status': status,
            'tests_conducted': tests,
            'tests_successful': successes
        }
    
    def get_agent_hypotheses(
        self,
        agent_id: str,
        game_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get hypotheses created by an agent."""
        query = "SELECT * FROM agent_hypotheses WHERE agent_id = ?"
        params: List[Any] = [agent_id]
        
        if game_type:
            query += " AND game_type = ?"
            params.append(game_type)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT 20"
        
        result = self.db.execute_query(query, tuple(params))
        return [dict(r) for r in result] if result else []
    
    def suggest_hypothesis_from_pattern(
        self,
        agent_id: str,
        game_type: str,
        observations: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze observations and suggest a hypothesis the agent could create.
        
        This helps agents generate hypotheses by finding patterns in their experience.
        """
        if not self.can_create_hypothesis(agent_id):
            return None
        
        if len(observations) < 3:
            return None  # Need minimum observations
        
        # Look for action-effect patterns
        action_effects: Dict[str, List[Any]] = {}
        for obs in observations:
            action = obs.get('action')
            effect = obs.get('effect')
            if action and effect:
                if action not in action_effects:
                    action_effects[action] = []
                action_effects[action].append(effect)
        
        # Find consistent patterns
        for action, effects in action_effects.items():
            if len(effects) >= 2:
                # Check if same effect occurs consistently
                effect_counts: Dict[Any, int] = {}
                for e in effects:
                    effect_counts[e] = effect_counts.get(e, 0) + 1
                
                for effect, count in effect_counts.items():
                    if count >= 2:
                        return {
                            'suggested_hypothesis': f"ACTION{action} consistently causes {effect}",
                            'hypothesis_type': 'action_effect',
                            'evidence_count': count,
                            'confidence': count / len(effects)
                        }
        
        return None

    def generate_primitive_aware_hypothesis(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        available_primitives: List[str],
        game_observations: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate a hypothesis that explicitly references available primitives.
        
        This is the key method that connects primitives to hypothesis formation.
        The agent thinks: "Given I have [primitives], what combination + actions
        might help me progress?"
        
        Args:
            agent_id: Agent creating hypothesis
            game_type: Current game type
            level_number: Current level
            available_primitives: List of primitive names agent can use
            game_observations: Dict with observed patterns:
                - frame_changes: What changed between frames
                - controlled_objects: What agent controls
                - stuck_pattern: How agent is stuck (if any)
                - action_effects: Observed action->effect mappings
                - goal_indicators: Detected goal patterns
                
        Returns:
            hypothesis_id if created, None otherwise
        """
        if not self.can_create_hypothesis(agent_id):
            return None
        
        # ===================================================================
        # PRIMITIVE-BASED REASONING
        # Map observations to primitives that could detect/exploit them
        # ===================================================================
        
        primitives_to_use: List[str] = []
        trigger_condition: Optional[Dict[str, Any]] = None
        predicted_action: Optional[str] = None
        action_sequence: Optional[List[str]] = None
        
        # 1. OBJECT DETECTION -> Movement primitives
        controlled = game_observations.get('controlled_objects', [])
        if controlled:
            # Agent knows what it controls - can use movement detection
            if 'detect_movement' in available_primitives:
                primitives_to_use.append('detect_movement')
            if 'track_object' in available_primitives:
                primitives_to_use.append('track_object')
        
        # 2. FRAME CHANGES -> Pattern detection primitives
        frame_changes = game_observations.get('frame_changes', {})
        if frame_changes:
            change_type = frame_changes.get('type', 'unknown')
            
            if change_type == 'color_change' and 'detect_color_change' in available_primitives:
                primitives_to_use.append('detect_color_change')
                trigger_condition = {
                    'primitive': 'detect_color_change',
                    'params': {'watch_for': frame_changes.get('colors', [])}
                }
            
            if change_type == 'boundary_hit' and 'detect_boundary' in available_primitives:
                primitives_to_use.append('detect_boundary')
                trigger_condition = {
                    'primitive': 'detect_boundary',
                    'params': {'direction': frame_changes.get('direction')}
                }
            
            if change_type == 'object_appeared' and 'detect_new_object' in available_primitives:
                primitives_to_use.append('detect_new_object')
        
        # 3. STUCK PATTERNS -> Escape strategy primitives
        stuck_pattern = game_observations.get('stuck_pattern')
        if stuck_pattern:
            if 'oscillation' in stuck_pattern.lower():
                # Oscillating = need to break pattern
                if 'detect_oscillation' in available_primitives:
                    primitives_to_use.append('detect_oscillation')
                # Suggest a different action
                last_actions = game_observations.get('last_actions', [])
                if last_actions:
                    # Avoid the oscillating actions
                    used_actions = set(last_actions[-4:])
                    for a in ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION6']:
                        if a not in used_actions:
                            predicted_action = a
                            break
        
        # 4. GOAL INDICATORS -> Goal-seeking primitives  
        goal_indicators = game_observations.get('goal_indicators', {})
        if goal_indicators:
            goal_direction = goal_indicators.get('direction')
            if goal_direction and 'identify_goal' in available_primitives:
                primitives_to_use.append('identify_goal')
                # Map direction to action
                direction_to_action = {
                    'up': 'ACTION1', 'right': 'ACTION2',
                    'down': 'ACTION4', 'left': 'ACTION3'
                }
                predicted_action = direction_to_action.get(goal_direction, 'ACTION6')
        
        # 5. ACTION EFFECTS -> Use proven patterns
        action_effects = game_observations.get('action_effects', {})
        if action_effects:
            # Find actions that had positive effects
            for action, effect in action_effects.items():
                if effect.get('positive'):
                    # This action worked before
                    if 'get_last_action' in available_primitives:
                        primitives_to_use.append('get_last_action')
                    if not predicted_action:
                        predicted_action = action
        
        # ===================================================================
        # GENERATE HYPOTHESIS
        # ===================================================================
        
        if not primitives_to_use:
            # No specific primitives matched - use basic reasoning
            primitives_to_use = [p for p in available_primitives 
                                if p in ['get_frame', 'get_action_history', 'frame_diff']][:3]
        
        # Build hypothesis text
        if trigger_condition and predicted_action:
            hypothesis_text = (
                f"When {trigger_condition['primitive']} detects change, "
                f"execute {predicted_action} to progress"
            )
        elif predicted_action:
            hypothesis_text = f"Execute {predicted_action} based on observed patterns"
        elif stuck_pattern:
            hypothesis_text = f"Escape {stuck_pattern} by trying alternative actions"
        else:
            hypothesis_text = f"Explore using {primitives_to_use[:2]} to find path forward"
        
        # Create the hypothesis
        return self.create_hypothesis(
            agent_id=agent_id,
            game_type=game_type,
            hypothesis_text=hypothesis_text,
            hypothesis_type='action_effect' if predicted_action else 'sequence_pattern',
            level_number=level_number,
            initial_evidence=[json.dumps(game_observations)],
            primitives_used=primitives_to_use,
            trigger_condition=trigger_condition,
            predicted_action=predicted_action,
            action_sequence=action_sequence
        )

    def get_primitive_based_action(
        self,
        agent_id: str,
        game_type: str,
        level_number: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get an action recommendation based on agent's primitive-aware hypotheses.
        
        This queries the agent's confirmed/testing hypotheses and returns
        an actionable recommendation if a trigger condition is met.
        
        Returns:
            Dict with 'action', 'hypothesis_id', 'confidence', 'primitives' or None
        """
        # Get agent's active primitive-aware hypotheses
        hypotheses = self.db.execute_query("""
            SELECT hypothesis_id, predicted_action, trigger_condition,
                   action_sequence, primitives_used, confidence, hypothesis_text
            FROM agent_hypotheses
            WHERE agent_id = ?
              AND game_type = ?
              AND (level_number = ? OR level_number IS NULL)
              AND status IN ('proposed', 'testing', 'confirmed')
              AND predicted_action IS NOT NULL
            ORDER BY 
                CASE status 
                    WHEN 'confirmed' THEN 1 
                    WHEN 'testing' THEN 2 
                    ELSE 3 
                END,
                confidence DESC
            LIMIT 5
        """, (agent_id, game_type, level_number))
        
        if not hypotheses:
            return None
        
        # Return the highest confidence hypothesis with an action
        for h in hypotheses:
            if h['predicted_action']:
                return {
                    'action': h['predicted_action'],
                    'hypothesis_id': h['hypothesis_id'],
                    'confidence': h['confidence'],
                    'primitives': json.loads(h['primitives_used'] or '[]'),
                    'reasoning': h['hypothesis_text']
                }
        
        return None

    def get_hypotheses_by_primitives(
        self,
        primitives: List[str],
        game_type: Optional[str] = None,
        min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find hypotheses that use specific primitives.
        
        Useful for:
        - Finding how other agents used a primitive
        - Learning from network's primitive combinations
        - Identifying which primitives lead to success
        
        Args:
            primitives: List of primitive names to search for
            game_type: Optional game type filter
            min_confidence: Minimum hypothesis confidence
            
        Returns:
            List of matching hypotheses with usage context
        """
        # Build query to search JSON primitives_used field
        matches: List[Dict[str, Any]] = []
        
        for primitive in primitives:
            query = """
                SELECT h.*, a.fitness
                FROM agent_hypotheses h
                LEFT JOIN agents a ON h.agent_id = a.agent_id
                WHERE h.primitives_used LIKE ?
                  AND h.confidence >= ?
                  AND h.status IN ('testing', 'confirmed')
            """
            params: List[Any] = [f'%"{primitive}"%', min_confidence]
            
            if game_type:
                query += " AND h.game_type = ?"
                params.append(game_type)
            
            query += " ORDER BY h.confidence DESC LIMIT 10"
            
            results = self.db.execute_query(query, tuple(params))
            if results:
                for r in results:
                    matches.append({
                        'hypothesis_id': r['hypothesis_id'],
                        'agent_id': r['agent_id'],
                        'hypothesis_text': r['hypothesis_text'],
                        'primitives': json.loads(r['primitives_used'] or '[]'),
                        'predicted_action': r['predicted_action'],
                        'confidence': r['confidence'],
                        'agent_fitness': r.get('fitness', 0),
                        'status': r['status']
                    })
        
        # Deduplicate and sort by confidence
        seen: set = set()
        unique: List[Dict[str, Any]] = []
        for m in matches:
            if m['hypothesis_id'] not in seen:
                seen.add(m['hypothesis_id'])
                unique.append(m)
        
        return sorted(unique, key=lambda x: x['confidence'], reverse=True)

    # ========================================================================
    # MORTALITY AWARENESS: Legacy & Self-Reflection
    # ========================================================================
    # From MetaContextual Awareness Theory:
    # "What have I contributed that will survive me?"
    #
    # Agents must be aware of their legacy - what they leave behind.
    # This creates pressure to contribute meaningful knowledge to the network
    # rather than simply existing.
    # ========================================================================
    
    def compute_legacy_score(self, agent_id: str) -> Dict[str, Any]:
        """
        Compute an agent's legacy score - what they will leave behind.
        
        Legacy components:
        - Sequences contributed (most valuable - saved others from rediscovering)
        - Patterns discovered (transferable knowledge)
        - Hypotheses validated (quality control contribution)
        - Games won (proof of capability)
        - Agents influenced (viral spread of knowledge)
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dict with legacy breakdown and total score
        """
        legacy: Dict[str, Any] = {
            'sequences': 0,
            'patterns': 0,
            'hypotheses': 0,
            'wins': 0,
            'influenced': 0,
            'total': 0.0,
            'rank': 'unknown',
            'epitaph': ''
        }
        
        try:
            # Get agent's contribution data
            result = self.db.execute_query("""
                SELECT 
                    COALESCE(sequence_discovery_count, 0) as sequences,
                    COALESCE(pattern_discovery_count, 0) as patterns,
                    COALESCE(validation_reputation, 0) as validation_rep,
                    COALESCE(total_games_won, 0) as wins,
                    COALESCE(discovery_prestige, 0) as prestige
                FROM agents WHERE agent_id = ?
            """, (agent_id,))
            
            if result:
                data = result[0]
                legacy['sequences'] = data['sequences']
                legacy['patterns'] = data['patterns']
                legacy['wins'] = data['wins']
                
                # Get hypotheses validated by this agent
                hyp_result = self.db.execute_query("""
                    SELECT COUNT(*) as count FROM network_object_control_hypotheses
                    WHERE discovered_by_agent = ? AND validation_attempts >= 3
                """, (agent_id,))
                if hyp_result:
                    legacy['hypotheses'] = hyp_result[0]['count']
                
                # Estimate agents influenced (via viral packages with this agent's discoveries)
                # Simplified: prestige / 10 as proxy for influence
                legacy['influenced'] = int((data['prestige'] or 0) / 10)
                
                # Calculate weighted total
                legacy['total'] = (
                    legacy['sequences'] * 5.0 +  # Sequences are most valuable
                    legacy['patterns'] * 2.0 +   # Patterns are transferable
                    legacy['hypotheses'] * 1.5 + # Validation helps network
                    legacy['wins'] * 1.0 +       # Proof of capability
                    legacy['influenced'] * 0.5   # Viral spread
                )
                
                # Assign rank based on total
                if legacy['total'] >= 50:
                    legacy['rank'] = 'legendary'
                    legacy['epitaph'] = "A titan whose discoveries shaped the network"
                elif legacy['total'] >= 20:
                    legacy['rank'] = 'notable'
                    legacy['epitaph'] = "A valued contributor whose work lives on"
                elif legacy['total'] >= 10:
                    legacy['rank'] = 'recognized'
                    legacy['epitaph'] = "Left meaningful marks on the collective"
                elif legacy['total'] >= 5:
                    legacy['rank'] = 'remembered'
                    legacy['epitaph'] = "Contributed to the greater understanding"
                elif legacy['total'] >= 1:
                    legacy['rank'] = 'documented'
                    legacy['epitaph'] = "Existed and tried"
                else:
                    legacy['rank'] = 'forgotten'
                    legacy['epitaph'] = "Passed through without trace"
                    
        except Exception as e:
            logger.debug(f"[LEGACY] Failed to compute legacy for {agent_id[:8]}: {e}")
        
        return legacy
    
    def record_dying_thoughts(
        self,
        agent_id: str,
        role: str,
        legacy: Dict[str, Any],
        final_game_type: Optional[str] = None,
        final_insight: Optional[str] = None
    ) -> str:
        """
        Record an agent's dying thoughts before retirement.
        
        Called during retirement phase to preserve the agent's final wisdom.
        These become part of the network's collective memory - wisdom from
        those who came before.
        
        Args:
            agent_id: Agent identifier
            role: Agent's role
            legacy: Legacy score data
            final_game_type: Last game played
            final_insight: Any final insight to pass on
            
        Returns:
            The recorded dying thought
        """
        # Role-specific final thoughts
        role_thoughts = {
            'pioneer': "I walked the frontier. Others will walk further.",
            'optimizer': "I refined what I found. Others will refine further.",
            'generalist': "I connected domains. Others will connect more.",
            'exploiter': "I stressed the edges. Others will find new edges."
        }
        
        base_thought = role_thoughts.get(role, "I existed. Others will continue.")
        
        # Customize based on legacy
        if legacy['total'] >= 20:
            legacy_suffix = f" My {legacy['sequences']} sequences and {legacy['patterns']} patterns remain."
        elif legacy['total'] >= 5:
            legacy_suffix = f" I contributed {legacy['total']:.0f} to the collective."
        else:
            legacy_suffix = " I leave questions for others to answer."
        
        # Add final insight if provided
        insight_suffix = ""
        if final_insight:
            insight_suffix = f" My final insight: {final_insight}"
        
        dying_thought = f"{base_thought}{legacy_suffix}{insight_suffix}"
        
        # Store in database
        try:
            self.db.execute_query("""
                INSERT INTO i_thread_episodic_memories
                (memory_id, agent_id, game_type, level_number, episode_type,
                 summary, emotional_valence, significance, stream_source)
                VALUES (?, ?, ?, 0, 'dying_thought', ?, -0.5, 1.0, 'stream_a')
            """, (
                f"dying_{uuid.uuid4().hex[:10]}",
                agent_id,
                final_game_type or 'FINAL',
                dying_thought
            ))
            
            logger.info(f"[DYING THOUGHTS] {agent_id[:8]} ({role}): {dying_thought}")
            
        except Exception as e:
            logger.debug(f"[DYING THOUGHTS] Failed to record: {e}")
        
        return dying_thought
    
    def get_memento_mori(self, agent_id: str, role: str) -> Dict[str, Any]:
        """
        Get a "memento mori" for an agent - a reminder of mortality.
        
        Returns context about the agent's mortality situation:
        - Current legacy status
        - Estimated time remaining
        - Reflection prompt
        - Historical dying thoughts from similar agents
        
        This is called periodically to keep mortality salient.
        "Remember you must die."
        
        Args:
            agent_id: Agent identifier
            role: Agent's role
            
        Returns:
            Mortality context
        """
        memento: Dict[str, Any] = {
            'legacy': self.compute_legacy_score(agent_id),
            'reflection': '',
            'ancestors_words': [],
            'urgency': 'low'
        }
        
        # Generate reflection based on legacy
        if memento['legacy']['total'] < 1:
            memento['reflection'] = "You have not yet contributed. What will you leave behind?"
            memento['urgency'] = 'high'
        elif memento['legacy']['total'] < 5:
            memento['reflection'] = "Your mark is small but visible. Can you deepen it?"
            memento['urgency'] = 'medium'
        elif memento['legacy']['total'] < 20:
            memento['reflection'] = "You have contributed. Will it be enough?"
            memento['urgency'] = 'low'
        else:
            memento['reflection'] = "Your legacy is established. What more can you give?"
            memento['urgency'] = 'none'
        
        # Get dying thoughts from similar agents (ancestors)
        try:
            result = self.db.execute_query("""
                SELECT summary FROM i_thread_episodic_memories
                WHERE episode_type = 'dying_thought'
                    AND agent_id != ?
                ORDER BY created_at DESC
                LIMIT 3
            """, (agent_id,))
            
            if result:
                memento['ancestors_words'] = [r['summary'] for r in result]
                
        except Exception as e:
            log_silent_failure(logger, "ancestor_words_retrieval", e, {"agent_id": agent_id})
        
        return memento
    
    def reflect_on_mortality(
        self,
        agent_id: str,
        role: str,
        current_game_type: Optional[str] = None,
        actions_taken: int = 0
    ) -> str:
        """
        Generate a mortality reflection during gameplay.
        
        Called periodically (e.g., every 100 actions) to maintain
        existential awareness. Returns a reflection appropriate to
        the agent's current situation.
        
        Args:
            agent_id: Agent identifier
            role: Agent's role
            current_game_type: Current game being played
            actions_taken: Actions taken this session
            
        Returns:
            Reflection string
        """
        legacy = self.compute_legacy_score(agent_id)
        
        # Early-action reflections (fresh start)
        if actions_taken < 50:
            if legacy['total'] < 1:
                return "I begin again. Every action could be my contribution."
            else:
                return f"I carry {legacy['total']:.0f} legacy points. Each action adds or wastes."
        
        # Mid-game reflections
        if actions_taken < 500:
            if legacy['total'] < 5:
                return "Time passes. I must find something worth leaving behind."
            else:
                return "My contributions exist. Are they enough?"
        
        # Late-game reflections (running out of time)
        if legacy['total'] < 1:
            return "Many actions spent. Nothing discovered. The network will forget me."
        elif legacy['total'] < 10:
            return "I have contributed. But my impact could have been greater."
        else:
            return "My legacy grows with each action. Death will not erase me."
