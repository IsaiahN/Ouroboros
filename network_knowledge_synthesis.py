import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: MUST be before all other imports

"""Network Knowledge Synthesis - Agent-Accessible Collective Intelligence
=========================================================================

Knowledge synthesis service that agents PULL from when they need help.
NOT a coordinator - agents decide when to query, not the other way around.

Design Philosophy:
- Agents are autonomous - they decide when they're stuck
- This service synthesizes collective network knowledge on demand
- No central control - just a knowledge aggregation tool

What agents can query:
1. DEATH ZONES - Where did other agents die?
2. DANGEROUS OBJECTS - What killed other agents?
3. THEORIES - Why did agents fail?
4. KNOWLEDGE GAPS - What hasn't been tried?

Philosophy: The network gets SMARTER collectively, agents stay autonomous.
"""
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class StuckGameAnalysis:
    """Analysis of why agents are stuck on a specific game."""
    game_id: str
    game_type: str
    bottleneck_level: int
    
    # Knowledge synthesis
    death_zones: List[Dict[str, Any]] = field(default_factory=list)
    dangerous_objects: List[Dict[str, Any]] = field(default_factory=list)
    game_over_theories: List[Dict[str, Any]] = field(default_factory=list)
    scientific_theories: List[Dict[str, Any]] = field(default_factory=list)
    network_hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    
    # Gap analysis
    knowledge_gaps: List[str] = field(default_factory=list)
    untested_experiments: List[str] = field(default_factory=list)
    missing_self_model: bool = False
    
    # Agent status
    agents_stuck: int = 0
    total_agents_on_game: int = 0
    best_score_achieved: float = 0
    collective_actions_taken: int = 0
    
    # Recommended interventions
    recommended_actions: List[Dict[str, Any]] = field(default_factory=list)


class NetworkKnowledgeSynthesis:
    """
    Agent-accessible knowledge synthesis service.
    
    Agents query this when THEY decide they need help - it doesn't push commands.
    Synthesizes death zones, theories, hypotheses, and knowledge gaps from the
    collective network experience.
    
    This is a PULL interface: agents ask for knowledge, not assigned tasks.
    """
    
    def __init__(self, db):
        """Initialize the knowledge synthesis service."""
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Thresholds (for background analysis, not agent control)
        self.stuck_threshold = 0.70  # 70% of agents stuck = knowledge gap detected
        self.min_agents_for_synthesis = 3  # Need at least 3 agents for meaningful synthesis
        self.max_interventions_per_game = 3  # Track intervention history
        
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create coordinator tables."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS stuck_game_interventions (
                    intervention_id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    
                    -- Analysis
                    bottleneck_level INTEGER,
                    agents_stuck INTEGER,
                    total_agents INTEGER,
                    stuck_ratio REAL,
                    
                    -- Knowledge synthesis
                    death_zones_found INTEGER DEFAULT 0,
                    dangerous_objects_found INTEGER DEFAULT 0,
                    theories_found INTEGER DEFAULT 0,
                    hypotheses_found INTEGER DEFAULT 0,
                    
                    -- Gaps identified
                    knowledge_gaps TEXT,  -- JSON list
                    
                    -- Interventions applied
                    interventions_applied TEXT,  -- JSON list
                    action_budget_boost REAL DEFAULT 0,
                    investigators_assigned INTEGER DEFAULT 0,
                    experiments_requested INTEGER DEFAULT 0,
                    
                    -- Outcome tracking
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_generation INTEGER,
                    breakthrough_action TEXT,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_stuck_game_lookup
                ON stuck_game_interventions (game_type, resolved, generation)
            """)
            
            # Table for agent stuck reports (agents report when they're stuck)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS agent_stuck_reports (
                    report_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    level_number INTEGER,
                    actions_taken INTEGER,
                    best_score REAL,
                    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_stuck_reports_game
                ON agent_stuck_reports (game_type, level_number)
            """)
            
            # Table for agent breakthrough reports (agents share what worked)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS agent_breakthrough_reports (
                    report_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    level_number INTEGER,
                    what_worked TEXT,
                    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_breakthrough_reports_game
                ON agent_breakthrough_reports (game_type, level_number)
            """)
            
        except Exception as e:
            self.logger.debug(f"Coordinator tables setup: {e}")
    
    def check_for_stuck_games(self, generation: int) -> List[StuckGameAnalysis]:
        """
        Check for games where agents are collectively stuck.
        
        Returns list of stuck game analyses with full knowledge synthesis.
        """
        stuck_games = []
        
        try:
            # Find games where many agents are making no progress
            # Using agent_frustration_states from the old system
            game_stats = self.db.execute_query("""
                SELECT 
                    stuck_on_game_id as game_id,
                    COUNT(*) as total_agents,
                    SUM(CASE WHEN games_without_progress >= 2 THEN 1 ELSE 0 END) as stuck_agents,
                    AVG(frustration_level) as avg_frustration,
                    MAX(games_without_progress) as max_no_progress
                FROM agent_frustration_states
                WHERE generation = ? 
                  AND stuck_on_game_id IS NOT NULL
                GROUP BY stuck_on_game_id
                HAVING total_agents >= ?
            """, (generation, self.min_agents_for_coordination))
            
            if not game_stats:
                return []
            
            for stat in game_stats:
                game_id = stat['game_id']
                total = stat['total_agents']
                stuck = stat['stuck_agents']
                stuck_ratio = stuck / total if total > 0 else 0
                
                if stuck_ratio >= self.stuck_threshold:
                    # Check if we haven't over-intervened
                    recent_interventions = self.db.execute_query("""
                        SELECT COUNT(*) as count FROM stuck_game_interventions
                        WHERE game_id = ? AND generation >= ? AND resolved = 0
                    """, (game_id, generation - 5))
                    
                    if recent_interventions and recent_interventions[0]['count'] >= self.max_interventions_per_game:
                        continue  # Already tried interventions, don't spam
                    
                    # Perform full analysis
                    analysis = self._analyze_stuck_game(game_id, generation, stuck, total)
                    if analysis:
                        stuck_games.append(analysis)
            
            return stuck_games
            
        except Exception as e:
            self.logger.error(f"Error checking for stuck games: {e}")
            return []
    
    def _analyze_stuck_game(self, game_id: str, generation: int,
                            stuck_count: int, total_count: int) -> Optional[StuckGameAnalysis]:
        """
        Perform deep analysis of why agents are stuck on this game.
        
        Synthesizes ALL knowledge from:
        - Death zones
        - Dangerous objects  
        - Game-over theories
        - Scientific theories
        - Network hypotheses
        """
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id[:4]
            
            # Find bottleneck level (most common death point)
            bottleneck = self._find_bottleneck_level(game_type)
            
            analysis = StuckGameAnalysis(
                game_id=game_id,
                game_type=game_type,
                bottleneck_level=bottleneck,
                agents_stuck=stuck_count,
                total_agents_on_game=total_count
            )
            
            # 1. Gather death zones
            analysis.death_zones = self._get_death_zones(game_type, bottleneck)
            
            # 2. Gather dangerous objects
            analysis.dangerous_objects = self._get_dangerous_objects(game_type, bottleneck)
            
            # 3. Gather game-over theories
            analysis.game_over_theories = self._get_game_over_theories(game_type, bottleneck)
            
            # 4. Gather scientific theories
            analysis.scientific_theories = self._get_scientific_theories(game_type, bottleneck)
            
            # 5. Gather network hypotheses
            analysis.network_hypotheses = self._get_network_hypotheses(game_type, bottleneck)
            
            # 6. Identify knowledge gaps
            analysis.knowledge_gaps = self._identify_knowledge_gaps(analysis)
            
            # 7. Find untested experiments
            analysis.untested_experiments = self._find_untested_experiments(game_type, bottleneck)
            
            # 8. Check for self-model issues
            analysis.missing_self_model = self._check_self_model_status(game_type, bottleneck)
            
            # 9. Generate recommended interventions
            analysis.recommended_actions = self._generate_interventions(analysis)
            
            self.logger.info(
                f"[COORDINATOR] Analyzed stuck game {game_type}: "
                f"L{bottleneck} bottleneck, {len(analysis.death_zones)} death zones, "
                f"{len(analysis.dangerous_objects)} dangerous objects, "
                f"{len(analysis.knowledge_gaps)} gaps identified"
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing stuck game {game_id}: {e}")
            return None
    
    def _find_bottleneck_level(self, game_type: str) -> int:
        """Find which level is causing agents to get stuck."""
        try:
            # Look at game results to see where scores plateau
            level_stats = self.db.execute_query("""
                SELECT 
                    CAST(final_score AS INTEGER) as level_reached,
                    COUNT(*) as attempts
                FROM game_results
                WHERE game_id LIKE ? || '%'
                GROUP BY level_reached
                ORDER BY attempts DESC
                LIMIT 3
            """, (game_type,))
            
            if level_stats:
                # Most common stopping point is likely the bottleneck
                most_common = level_stats[0]['level_reached']
                # Bottleneck is the NEXT level after most common score
                return most_common + 1
            
            return 1  # Default to level 1
            
        except Exception as e:
            self.logger.debug(f"Error finding bottleneck: {e}")
            return 1
    
    def _get_death_zones(self, game_type: str, level: int) -> List[Dict]:
        """Get all death zones for this game/level."""
        try:
            zones = self.db.execute_query("""
                SELECT zone_id, zone_x, zone_y, zone_radius, death_count,
                       confidence, last_death_at, times_challenged, times_validated
                FROM death_zones
                WHERE game_type = ? AND level_number = ? AND is_active = 1
                ORDER BY death_count DESC
                LIMIT 20
            """, (game_type, level))
            return zones or []
        except:
            return []
    
    def _get_dangerous_objects(self, game_type: str, level: int) -> List[Dict]:
        """Get all dangerous object patterns for this game/level."""
        try:
            objects = self.db.execute_query("""
                SELECT object_id, object_color, danger_type, death_count,
                       confidence, propagated_zones
                FROM dangerous_objects
                WHERE game_type = ? AND level_number = ? AND is_active = 1
                ORDER BY death_count DESC
                LIMIT 20
            """, (game_type, level))
            return objects or []
        except:
            return []
    
    def _get_game_over_theories(self, game_type: str, level: int) -> List[Dict]:
        """Get all game-over theories from terminal pattern detector."""
        try:
            theories = self.db.execute_query("""
                SELECT pattern_id, frame_hash, fatal_action, pre_death_sequence,
                       death_count, first_seen_at
                FROM terminal_patterns
                WHERE game_type = ? AND level_number = ?
                ORDER BY death_count DESC
                LIMIT 20
            """, (game_type, level))
            return theories or []
        except:
            return []
    
    def _get_scientific_theories(self, game_type: str, level: int) -> List[Dict]:
        """Get all theories from Scientific Method Engine."""
        try:
            theories = self.db.execute_query("""
                SELECT theory_id, theory_type, description, formal_statement,
                       confidence, status, tests_conducted, tests_successful
                FROM agent_theories
                WHERE game_type = ? AND (level_number = ? OR level_number = -1)
                  AND is_active = 1
                ORDER BY confidence DESC
                LIMIT 20
            """, (game_type, level))
            return theories or []
        except:
            return []
    
    def _get_network_hypotheses(self, game_type: str, level: int) -> List[Dict]:
        """Get all network control hypotheses."""
        try:
            hypotheses = self.db.execute_query("""
                SELECT hypothesis_id, controlled_object_id, control_mechanism,
                       reliability_score, validation_attempts, validated_by_win,
                       best_score_achieved
                FROM network_object_control_hypotheses
                WHERE game_type = ? AND level = ? AND is_active = 1
                ORDER BY best_score_achieved DESC
                LIMIT 20
            """, (game_type, level))
            return hypotheses or []
        except:
            return []
    
    def _identify_knowledge_gaps(self, analysis: StuckGameAnalysis) -> List[str]:
        """Identify what we DON'T know about the stuck game."""
        gaps = []
        
        # Gap 1: No death zones = we don't know WHERE death happens
        if not analysis.death_zones:
            gaps.append("NO_DEATH_ZONE_KNOWLEDGE: We don't know WHERE death occurs")
        
        # Gap 2: No dangerous objects = we don't know WHAT kills us
        if not analysis.dangerous_objects:
            gaps.append("NO_DANGER_OBJECT_KNOWLEDGE: We don't know WHAT objects are dangerous")
        
        # Gap 3: No scientific theories = we haven't formed any testable hypotheses
        if not analysis.scientific_theories:
            gaps.append("NO_SCIENTIFIC_THEORIES: No testable hypotheses have been formed")
        
        # Gap 4: Low confidence theories = we're uncertain about what we think we know
        low_confidence = [t for t in analysis.scientific_theories 
                         if t.get('confidence', 0) < 0.5]
        if len(low_confidence) > len(analysis.scientific_theories) * 0.7:
            gaps.append("LOW_CONFIDENCE_THEORIES: Most theories are uncertain (<50% confidence)")
        
        # Gap 5: No control hypotheses = we don't know what we control
        if not analysis.network_hypotheses:
            gaps.append("NO_CONTROL_HYPOTHESES: We don't know what objects we control")
        
        # Gap 6: No validated hypotheses = nothing has been confirmed
        validated = [h for h in analysis.network_hypotheses if h.get('validated_by_win')]
        if analysis.network_hypotheses and not validated:
            gaps.append("NO_VALIDATED_HYPOTHESES: We have theories but none confirmed by success")
        
        # Gap 7: Missing self-model
        if analysis.missing_self_model:
            gaps.append("MISSING_SELF_MODEL: Agents don't know which object they control")
        
        # Gap 8: No goal theory
        goal_theories = [t for t in analysis.scientific_theories 
                        if t.get('theory_type') == 'goal_hypothesis']
        if not goal_theories:
            gaps.append("NO_GOAL_THEORY: We don't know what the objective is")
        
        return gaps
    
    def _find_untested_experiments(self, game_type: str, level: int) -> List[str]:
        """Find experiments that haven't been tried yet."""
        untested = []
        
        try:
            # Check if all actions have been tried
            action_coverage = self.db.execute_query("""
                SELECT DISTINCT action_type FROM action_traces
                WHERE game_id LIKE ? || '%'
                  AND level_number = ?
            """, (game_type, level))
            
            all_actions = {'ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 
                          'ACTION5', 'ACTION6', 'ACTION7'}
            tried_actions = {a['action_type'] for a in (action_coverage or [])}
            untried = all_actions - tried_actions
            
            for action in untried:
                untested.append(f"TRY_ACTION: {action} has not been attempted on level {level}")
            
            # Check if object clicking has been systematic
            click_count = self.db.execute_query("""
                SELECT COUNT(*) as clicks FROM action_traces
                WHERE game_id LIKE ? || '%'
                  AND level_number = ?
                  AND action_type = 'ACTION6'
            """, (game_type, level))
            
            if click_count and click_count[0]['clicks'] < 10:
                untested.append("EXPLORE_CLICKS: Systematic object clicking not performed")
            
        except Exception as e:
            self.logger.debug(f"Error finding untested experiments: {e}")
        
        return untested
    
    def _check_self_model_status(self, game_type: str, level: int) -> bool:
        """Check if agents have established a self-model for this game."""
        try:
            self_model = self.db.execute_query("""
                SELECT COUNT(*) as count FROM controlled_object_discoveries
                WHERE game_type = ? AND level = ?
                  AND control_verified = 1
            """, (game_type, level))
            
            return not self_model or self_model[0]['count'] == 0
            
        except:
            return True  # Assume missing if we can't check
    
    def _generate_interventions(self, analysis: StuckGameAnalysis) -> List[Dict[str, Any]]:
        """Generate specific interventions based on the analysis."""
        interventions = []
        
        # Intervention 1: If no self-model, prioritize object discovery
        if analysis.missing_self_model or "MISSING_SELF_MODEL" in str(analysis.knowledge_gaps):
            interventions.append({
                'type': 'BOOST_DISCOVERY_PHASE',
                'priority': 'HIGH',
                'description': 'Extend object discovery phase to 50 actions (from 20)',
                'parameter': 'discovery_phase_actions',
                'value': 50,
                'reason': 'Agents dont know what they control'
            })
        
        # Intervention 2: If no goal theory, request goal experiments
        if "NO_GOAL_THEORY" in str(analysis.knowledge_gaps):
            interventions.append({
                'type': 'REQUEST_GOAL_EXPERIMENTS',
                'priority': 'HIGH',
                'description': 'Scientific Method Engine should prioritize goal hypothesis testing',
                'target_level': analysis.bottleneck_level,
                'reason': 'No understanding of game objective'
            })
        
        # Intervention 3: If many death zones but still dying, try challenge mechanism
        if len(analysis.death_zones) > 5:
            interventions.append({
                'type': 'CHALLENGE_DEATH_ZONES',
                'priority': 'MEDIUM',
                'description': 'Some death zones may be stale - enable challenge testing',
                'zones_to_challenge': [z['zone_id'] for z in analysis.death_zones[:5]],
                'reason': 'Many death zones recorded but still dying - some may be invalid'
            })
        
        # Intervention 4: If no dangerous objects identified, boost danger detection
        if not analysis.dangerous_objects:
            interventions.append({
                'type': 'BOOST_DANGER_DETECTION',
                'priority': 'HIGH',
                'description': 'Increase sensitivity of dangerous object detection',
                'reason': 'Dying without knowing what kills us'
            })
        
        # Intervention 5: Boost action budget for investigation
        stuck_ratio = analysis.agents_stuck / analysis.total_agents_on_game
        if stuck_ratio > 0.8:
            interventions.append({
                'type': 'BOOST_ACTION_BUDGET',
                'priority': 'MEDIUM',
                'description': 'Grant 50% extra actions for this game',
                'budget_multiplier': 1.5,
                'game_type': analysis.game_type,
                'reason': f'{stuck_ratio*100:.0f}% of agents stuck - need more exploration time'
            })
        
        # Intervention 6: If experiments exist but weren't tried, request them
        if analysis.untested_experiments:
            interventions.append({
                'type': 'QUEUE_EXPERIMENTS',
                'priority': 'HIGH',
                'description': 'Queue specific experiments that havent been tried',
                'experiments': analysis.untested_experiments[:5],
                'reason': 'Obvious experiments not attempted'
            })
        
        # Intervention 7: Synthesize and share knowledge to all agents on this game
        if analysis.scientific_theories or analysis.network_hypotheses:
            interventions.append({
                'type': 'SYNTHESIZE_AND_SHARE',
                'priority': 'HIGH',
                'description': 'Combine all theories and share synthesis to stuck agents',
                'theories_to_combine': len(analysis.scientific_theories),
                'hypotheses_to_combine': len(analysis.network_hypotheses),
                'reason': 'Knowledge exists but may not be reaching all agents'
            })
        
        # Intervention 8: If low-confidence theories, request more testing
        low_conf = [t for t in analysis.scientific_theories if t.get('confidence', 0) < 0.5]
        if low_conf:
            interventions.append({
                'type': 'REQUEST_THEORY_TESTING',
                'priority': 'MEDIUM',
                'description': f'Test {len(low_conf)} uncertain theories more rigorously',
                'theories': [t['theory_id'] for t in low_conf[:5]],
                'reason': 'Have theories but not confident in them'
            })
        
        return interventions
    
    def apply_interventions(self, analysis: StuckGameAnalysis, generation: int) -> str:
        """
        Apply the recommended interventions.
        
        Returns intervention_id for tracking.
        """
        intervention_id = f"stuck_int_{uuid.uuid4().hex[:12]}"
        
        try:
            interventions_applied = []
            action_budget_boost = 0
            investigators_assigned = 0
            experiments_requested = 0
            
            for intervention in analysis.recommended_actions:
                int_type = intervention['type']
                
                if int_type == 'BOOST_DISCOVERY_PHASE':
                    # Store in a config that agents will read
                    self._set_game_config(
                        analysis.game_type, 
                        'discovery_phase_actions', 
                        intervention['value']
                    )
                    interventions_applied.append(intervention)
                    self.logger.info(f"[INTERVENTION] Boosted discovery phase for {analysis.game_type}")
                
                elif int_type == 'BOOST_ACTION_BUDGET':
                    action_budget_boost = intervention['budget_multiplier']
                    self._set_game_config(
                        analysis.game_type,
                        'action_budget_multiplier',
                        action_budget_boost
                    )
                    interventions_applied.append(intervention)
                    self.logger.info(f"[INTERVENTION] Boosted action budget {action_budget_boost}x for {analysis.game_type}")
                
                elif int_type == 'QUEUE_EXPERIMENTS':
                    # Add experiments to the scientific method queue
                    experiments_requested = len(intervention.get('experiments', []))
                    self._queue_experiments(analysis.game_type, intervention['experiments'])
                    interventions_applied.append(intervention)
                    self.logger.info(f"[INTERVENTION] Queued {experiments_requested} experiments for {analysis.game_type}")
                
                elif int_type == 'SYNTHESIZE_AND_SHARE':
                    # Trigger knowledge synthesis
                    self._trigger_knowledge_synthesis(analysis)
                    interventions_applied.append(intervention)
                    self.logger.info(f"[INTERVENTION] Triggered knowledge synthesis for {analysis.game_type}")
                
                elif int_type == 'CHALLENGE_DEATH_ZONES':
                    # Mark zones for challenge
                    self._mark_zones_for_challenge(intervention.get('zones_to_challenge', []))
                    interventions_applied.append(intervention)
                    self.logger.info(f"[INTERVENTION] Marked {len(intervention.get('zones_to_challenge', []))} zones for challenge")
            
            # Record the intervention
            self.db.execute_query("""
                INSERT INTO stuck_game_interventions (
                    intervention_id, game_id, game_type, generation,
                    bottleneck_level, agents_stuck, total_agents, stuck_ratio,
                    death_zones_found, dangerous_objects_found,
                    theories_found, hypotheses_found,
                    knowledge_gaps, interventions_applied,
                    action_budget_boost, investigators_assigned, experiments_requested
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                intervention_id, analysis.game_id, analysis.game_type, generation,
                analysis.bottleneck_level, analysis.agents_stuck, 
                analysis.total_agents_on_game,
                analysis.agents_stuck / analysis.total_agents_on_game,
                len(analysis.death_zones), len(analysis.dangerous_objects),
                len(analysis.scientific_theories), len(analysis.network_hypotheses),
                json.dumps(analysis.knowledge_gaps),
                json.dumps([i['type'] for i in interventions_applied]),
                action_budget_boost, investigators_assigned, experiments_requested
            ))
            
            # Notify CODS about the stuck game (may suggest primitive unlocks)
            self.notify_cods_of_stuck_game(analysis)
            
            self.logger.info(
                f"[COORDINATOR] Applied {len(interventions_applied)} interventions for {analysis.game_type}"
            )
            
            return intervention_id
            
        except Exception as e:
            self.logger.error(f"Error applying interventions: {e}")
            return intervention_id
    
    def _set_game_config(self, game_type: str, key: str, value: Any):
        """Store game-specific configuration that agents will read."""
        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO game_specific_config (
                    game_type, config_key, config_value, updated_at
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (game_type, key, json.dumps(value)))
        except:
            # Table may not exist, create it
            try:
                self.db.execute_query("""
                    CREATE TABLE IF NOT EXISTS game_specific_config (
                        game_type TEXT,
                        config_key TEXT,
                        config_value TEXT,
                        updated_at TIMESTAMP,
                        PRIMARY KEY (game_type, config_key)
                    )
                """)
                self.db.execute_query("""
                    INSERT OR REPLACE INTO game_specific_config (
                        game_type, config_key, config_value, updated_at
                    ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (game_type, key, json.dumps(value)))
            except Exception as e:
                self.logger.debug(f"Failed to set game config: {e}")
    
    def _queue_experiments(self, game_type: str, experiments: List[str]):
        """Queue experiments for the Scientific Method Engine."""
        try:
            for exp in experiments:
                self.db.execute_query("""
                    INSERT INTO queued_experiments (
                        experiment_id, game_type, description, priority, created_at
                    ) VALUES (?, ?, ?, 'HIGH', CURRENT_TIMESTAMP)
                """, (f"queued_{uuid.uuid4().hex[:8]}", game_type, exp))
        except:
            # Table may not exist
            try:
                self.db.execute_query("""
                    CREATE TABLE IF NOT EXISTS queued_experiments (
                        experiment_id TEXT PRIMARY KEY,
                        game_type TEXT,
                        description TEXT,
                        priority TEXT,
                        executed BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP
                    )
                """)
                for exp in experiments:
                    self.db.execute_query("""
                        INSERT INTO queued_experiments (
                            experiment_id, game_type, description, priority, created_at
                        ) VALUES (?, ?, ?, 'HIGH', CURRENT_TIMESTAMP)
                    """, (f"queued_{uuid.uuid4().hex[:8]}", game_type, exp))
            except Exception as e:
                self.logger.debug(f"Failed to queue experiments: {e}")
    
    def _trigger_knowledge_synthesis(self, analysis: StuckGameAnalysis):
        """Synthesize all knowledge about the stuck game."""
        try:
            # Create a synthesis record
            synthesis = {
                'game_type': analysis.game_type,
                'level': analysis.bottleneck_level,
                'death_zones_summary': len(analysis.death_zones),
                'dangerous_colors': list(set(
                    d.get('object_color') for d in analysis.dangerous_objects
                )),
                'confirmed_theories': [
                    t['description'] for t in analysis.scientific_theories
                    if t.get('confidence', 0) > 0.7
                ],
                'best_hypotheses': [
                    h.get('control_mechanism') for h in analysis.network_hypotheses
                    if h.get('validated_by_win')
                ][:3]
            }
            
            self.db.execute_query("""
                INSERT INTO knowledge_synthesis (
                    synthesis_id, game_type, level, synthesis_data, created_at
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                f"synth_{uuid.uuid4().hex[:8]}",
                analysis.game_type,
                analysis.bottleneck_level,
                json.dumps(synthesis)
            ))
            
        except:
            # Create table if needed
            try:
                self.db.execute_query("""
                    CREATE TABLE IF NOT EXISTS knowledge_synthesis (
                        synthesis_id TEXT PRIMARY KEY,
                        game_type TEXT,
                        level INTEGER,
                        synthesis_data TEXT,
                        created_at TIMESTAMP
                    )
                """)
            except:
                pass
    
    def _mark_zones_for_challenge(self, zone_ids: List[str]):
        """Mark death zones for challenge testing."""
        try:
            for zone_id in zone_ids:
                self.db.execute_query("""
                    UPDATE death_zones
                    SET should_challenge = 1
                    WHERE zone_id = ?
                """, (zone_id,))
        except Exception as e:
            self.logger.debug(f"Failed to mark zones for challenge: {e}")
    
    def check_resolution(self, game_type: str, generation: int) -> bool:
        """
        Check if a previously stuck game has been resolved.
        
        A game is resolved if:
        - Agents are making progress again
        - Win achieved
        - Score improved significantly
        """
        try:
            # Check recent game results
            recent_results = self.db.execute_query("""
                SELECT final_score, level_completions
                FROM game_results
                WHERE game_id LIKE ? || '%'
                  AND generation = ?
                ORDER BY final_score DESC
                LIMIT 5
            """, (game_type, generation))
            
            if not recent_results:
                return False
            
            # Check if anyone made progress
            best_score = max(r['final_score'] for r in recent_results)
            
            # Get previous best
            prev_best = self.db.execute_query("""
                SELECT MAX(final_score) as best FROM game_results
                WHERE game_id LIKE ? || '%'
                  AND generation < ?
            """, (game_type, generation))
            
            prev_best_score = prev_best[0]['best'] if prev_best and prev_best[0]['best'] else 0
            
            # Resolved if we improved
            if best_score > prev_best_score:
                # Mark interventions as resolved
                self.db.execute_query("""
                    UPDATE stuck_game_interventions
                    SET resolved = 1, resolution_generation = ?, resolved_at = CURRENT_TIMESTAMP
                    WHERE game_type = ? AND resolved = 0
                """, (generation, game_type))
                
                self.logger.info(
                    f"[COORDINATOR] Game {game_type} RESOLVED! "
                    f"Score improved from {prev_best_score} to {best_score}"
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error checking resolution: {e}")
            return False
    
    def get_game_config(self, game_type: str, key: str, default: Any = None) -> Any:
        """Get game-specific configuration."""
        try:
            result = self.db.execute_query("""
                SELECT config_value FROM game_specific_config
                WHERE game_type = ? AND config_key = ?
            """, (game_type, key))
            
            if result and result[0]['config_value']:
                return json.loads(result[0]['config_value'])
            return default
            
        except:
            return default
    
    def notify_cods_of_stuck_game(self, analysis: StuckGameAnalysis):
        """
        Notify CODS engine about a stuck game for primitive gap detection.
        
        Stuck games are signals that we may be missing crucial primitives.
        """
        try:
            # Record as a CODS hint if we have knowledge gaps suggesting primitives
            for gap in analysis.knowledge_gaps:
                if 'NO_GOAL_THEORY' in gap:
                    # Missing goal understanding might need goal-detection primitive
                    self.db.execute_query("""
                        INSERT OR IGNORE INTO cods_primitive_hints (
                            hint_id, game_type, source, hint_type,
                            confidence, details, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        f"stuck_{analysis.game_type}_{uuid.uuid4().hex[:6]}",
                        analysis.game_type,
                        'network_knowledge_synthesis',
                        'GOAL_DETECTION_NEEDED',
                        0.7,
                        json.dumps({'gap': gap, 'bottleneck_level': analysis.bottleneck_level})
                    ))
                    
                elif 'NO_CONTROL_HYPOTHESES' in gap:
                    # Missing control understanding might need control primitives
                    self.db.execute_query("""
                        INSERT OR IGNORE INTO cods_primitive_hints (
                            hint_id, game_type, source, hint_type,
                            confidence, details, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        f"stuck_{analysis.game_type}_{uuid.uuid4().hex[:6]}",
                        analysis.game_type,
                        'network_knowledge_synthesis',
                        'CONTROL_PRIMITIVE_NEEDED',
                        0.8,
                        json.dumps({'gap': gap, 'bottleneck_level': analysis.bottleneck_level})
                    ))
                    
        except Exception as e:
            self.logger.debug(f"Failed to notify CODS: {e}")
    # ========================================================================
    # AGENT-ACCESSIBLE QUERY INTERFACE
    # ========================================================================
    # These methods are for agents to PULL knowledge when they need it.
    # This service doesn't make decisions - agents use it as a tool.
    # ========================================================================
    
    def query_network_knowledge(self, game_type: str, level: int = None) -> Dict[str, Any]:
        """
        Agent-accessible method to query synthesized network knowledge.
        
        Called by agents when THEY decide they need help, not pushed by coordinator.
        Returns everything the network knows about this game/level.
        
        Args:
            game_type: Game type prefix (e.g., 'vc33')
            level: Specific level to query (None = bottleneck level)
            
        Returns:
            Dict with all synthesized knowledge for agent to use
        """
        try:
            # Find bottleneck if level not specified
            if level is None:
                level = self._find_bottleneck_level(game_type)
            
            knowledge = {
                'game_type': game_type,
                'level': level,
                'has_knowledge': False,
                
                # Where agents died
                'death_zones': [],
                'avoid_coordinates': [],
                
                # What's dangerous
                'dangerous_objects': [],
                'danger_object_ids': [],
                
                # Why agents died (theories)
                'game_over_theories': [],
                'scientific_theories': [],
                
                # Control hypotheses from network
                'control_hypotheses': [],
                
                # What's NOT been tried
                'untested_experiments': [],
                'knowledge_gaps': [],
                
                # Recommendations (agent can ignore these)
                'suggestions': []
            }
            
            # Gather death zones
            death_zones = self._get_death_zones(game_type, level)
            if death_zones:
                knowledge['death_zones'] = death_zones
                knowledge['avoid_coordinates'] = [
                    {'x': dz.get('zone_x'), 'y': dz.get('zone_y'), 'radius': dz.get('zone_radius', 1)}
                    for dz in death_zones if dz.get('zone_x') is not None
                ]
            
            # Gather dangerous objects
            dangerous = self._get_dangerous_objects(game_type, level)
            if dangerous:
                knowledge['dangerous_objects'] = dangerous
                knowledge['danger_object_ids'] = [
                    d.get('object_id') for d in dangerous if d.get('object_id')
                ]
            
            # Gather theories
            knowledge['game_over_theories'] = self._get_game_over_theories(game_type, level)
            knowledge['scientific_theories'] = self._get_scientific_theories(game_type, level)
            
            # Gather control hypotheses
            knowledge['control_hypotheses'] = self._get_network_hypotheses(game_type, level)
            
            # Gather untested experiments
            knowledge['untested_experiments'] = self._find_untested_experiments(game_type, level)
            
            # Build simple analysis for gap detection
            temp_analysis = StuckGameAnalysis(
                game_id=f"{game_type}-query",
                game_type=game_type,
                bottleneck_level=level,
                death_zones=death_zones or [],
                dangerous_objects=dangerous or [],
                game_over_theories=knowledge['game_over_theories'] or [],
                scientific_theories=knowledge['scientific_theories'] or [],
                network_hypotheses=knowledge['control_hypotheses'] or []
            )
            knowledge['knowledge_gaps'] = self._identify_knowledge_gaps(temp_analysis)
            
            # Generate suggestions (agent can ignore)
            if knowledge['avoid_coordinates']:
                knowledge['suggestions'].append(
                    f"Avoid coordinates: {knowledge['avoid_coordinates'][:3]}"
                )
            if knowledge['danger_object_ids']:
                knowledge['suggestions'].append(
                    f"Beware objects: {knowledge['danger_object_ids'][:3]}"
                )
            if knowledge['untested_experiments']:
                knowledge['suggestions'].append(
                    f"Try: {knowledge['untested_experiments'][0]}"
                )
            if 'NO_CONTROL_HYPOTHESES' in str(knowledge['knowledge_gaps']):
                knowledge['suggestions'].append(
                    "Network has no control hypotheses - try discovering what you control"
                )
            
            # Mark if we have useful knowledge
            knowledge['has_knowledge'] = bool(
                death_zones or dangerous or 
                knowledge['game_over_theories'] or 
                knowledge['scientific_theories'] or
                knowledge['control_hypotheses']
            )
            
            self.logger.debug(
                f"[COORDINATOR] Agent query for {game_type}@L{level}: "
                f"{len(death_zones or [])} death zones, "
                f"{len(dangerous or [])} dangers, "
                f"{len(knowledge['control_hypotheses'] or [])} hypotheses"
            )
            
            return knowledge
            
        except Exception as e:
            self.logger.debug(f"Knowledge query failed: {e}")
            return {
                'game_type': game_type,
                'level': level,
                'has_knowledge': False,
                'error': str(e)
            }
    
    def report_stuck(self, agent_id: str, game_type: str, level: int, 
                     actions_taken: int, best_score: float) -> None:
        """
        Agent reports that it's stuck. Updates network knowledge.
        
        This is the agent telling the network about its struggle,
        not the coordinator detecting it.
        """
        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO agent_stuck_reports (
                    report_id, agent_id, game_type, level_number,
                    actions_taken, best_score, reported_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                f"stuck_{agent_id}_{game_type}_{level}",
                agent_id, game_type, level, actions_taken, best_score
            ))
        except Exception as e:
            # Table might not exist, that's okay
            self.logger.debug(f"Stuck report failed: {e}")
    
    def report_breakthrough(self, agent_id: str, game_type: str, level: int,
                           what_worked: str) -> None:
        """
        Agent reports a breakthrough. Updates network knowledge.
        
        This is how agents share what worked, so other stuck agents
        can query and learn.
        """
        try:
            self.db.execute_query("""
                INSERT INTO agent_breakthrough_reports (
                    report_id, agent_id, game_type, level_number,
                    what_worked, reported_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                f"break_{agent_id}_{game_type}_{level}_{uuid.uuid4().hex[:6]}",
                agent_id, game_type, level, what_worked
            ))
            
            # Mark any interventions as resolved
            self.db.execute_query("""
                UPDATE stuck_game_interventions 
                SET resolved = 1, resolved_at = CURRENT_TIMESTAMP, 
                    breakthrough_action = ?
                WHERE game_type = ? AND resolved = 0
            """, (what_worked, game_type))
            
        except Exception as e:
            self.logger.debug(f"Breakthrough report failed: {e}")