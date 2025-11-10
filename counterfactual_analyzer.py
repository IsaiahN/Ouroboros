"""
Counterfactual Reasoning Engine - "What If?" Analysis After Failures
====================================================================

Analyzes failed games to understand "what if I had done X instead?"
Generates alternative action sequences and evaluates their potential.

Following Rule 2: All counterfactual analysis stored in database
Following Rule 3: Enhances existing failure analysis systems
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from database_interface import DatabaseInterface

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

logger = logging.getLogger(__name__)


class CounterfactualAnalyzer:
    """
    Performs "what if?" analysis on failed game attempts to identify
    alternative strategies that might have succeeded.
    
    Counterfactual types:
    1. Action substitution: "What if I used ACTION X instead of Y?"
    2. Timing variation: "What if I acted earlier/later?"
    3. Strategy shift: "What if I changed approach at decision point Z?"
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Analysis parameters
        self.min_actions_for_analysis = 5
        self.max_counterfactuals_per_game = 10
        
        # Initialize schema
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create counterfactual analysis tables"""
        try:
            # Counterfactual scenarios
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS counterfactual_scenarios (
                    scenario_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    generation INTEGER DEFAULT 0,
                    
                    -- Original game (what actually happened)
                    actual_actions TEXT NOT NULL,  -- JSON: actual action sequence
                    actual_score REAL NOT NULL,
                    actual_outcome TEXT NOT NULL,  -- 'failed', 'partial'
                    
                    -- Decision point (where things could have changed)
                    decision_point_index INTEGER NOT NULL,  -- Action index where divergence starts
                    decision_point_score REAL NOT NULL,
                    decision_point_context TEXT,  -- JSON: game state at decision point
                    
                    -- Counterfactual (what if?)
                    counterfactual_type TEXT NOT NULL,  -- 'action_substitution', 'timing_variation', 'strategy_shift'
                    alternative_actions TEXT NOT NULL,  -- JSON: alternative action sequence
                    divergence_reason TEXT NOT NULL,  -- Why this alternative?
                    
                    -- Predicted outcome
                    predicted_score REAL,
                    predicted_outcome TEXT,  -- 'likely_win', 'likely_improve', 'likely_same', 'likely_worse'
                    confidence_in_prediction REAL DEFAULT 0.5,
                    
                    -- Validation (if tested)
                    was_tested BOOLEAN DEFAULT FALSE,
                    actual_test_score REAL,
                    prediction_accuracy REAL,
                    
                    -- Learning value
                    learning_value REAL DEFAULT 0.5,  -- How valuable is this counterfactual?
                    priority REAL DEFAULT 0.5,  -- Should this be tested?
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tested_at TIMESTAMP,
                    
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            # Counterfactual decision points (critical moments where choices mattered)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS decision_points (
                    decision_point_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    
                    -- Decision context
                    action_index INTEGER NOT NULL,
                    score_at_decision REAL NOT NULL,
                    available_actions TEXT,  -- JSON: actions that were available
                    action_taken INTEGER NOT NULL,  -- What agent actually did
                    
                    -- Why is this a decision point?
                    importance_score REAL NOT NULL,  -- How critical was this moment?
                    importance_factors TEXT,  -- JSON: why this matters
                    
                    -- Outcomes
                    immediate_score_change REAL DEFAULT 0.0,
                    final_game_outcome TEXT NOT NULL,
                    
                    -- Alternative analysis
                    counterfactuals_generated INTEGER DEFAULT 0,
                    best_alternative_action INTEGER,
                    best_alternative_predicted_score REAL,
                    
                    -- Timestamps
                    identified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            # Counterfactual learnings (insights from "what if" analysis)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS counterfactual_learnings (
                    learning_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    
                    -- Learning content
                    learning_type TEXT NOT NULL,  -- 'action_preference', 'timing_insight', 'strategy_improvement'
                    learning_description TEXT NOT NULL,
                    supporting_scenarios TEXT,  -- JSON: scenario_ids that support this
                    
                    -- Actionability
                    is_actionable BOOLEAN DEFAULT TRUE,
                    recommended_behavior_change TEXT,  -- JSON: specific changes
                    expected_improvement REAL DEFAULT 0.0,
                    
                    -- Validation
                    times_applied INTEGER DEFAULT 0,
                    success_when_applied INTEGER DEFAULT 0,
                    failure_when_applied INTEGER DEFAULT 0,
                    actual_improvement REAL DEFAULT 0.0,
                    
                    -- Confidence
                    confidence_score REAL DEFAULT 0.5,
                    confidence_source TEXT,  -- 'prediction', 'validation', 'both'
                    
                    -- Timestamps
                    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_applied TIMESTAMP,
                    last_validated TIMESTAMP,
                    
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            # Create indexes
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_counterfactual_agent ON counterfactual_scenarios(agent_id)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_counterfactual_game ON counterfactual_scenarios(game_id)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_counterfactual_tested ON counterfactual_scenarios(was_tested)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_counterfactual_priority ON counterfactual_scenarios(priority DESC)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_decision_points_agent ON decision_points(agent_id)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_decision_points_importance ON decision_points(importance_score DESC)")
            
            self.logger.info("Counterfactual analysis schema initialized")
            
        except Exception as e:
            self.logger.error(f"Schema initialization error: {e}")
    
    def analyze_failure(self, agent_id: str, game_id: str, session_id: str,
                       final_score: float, generation: int = 0) -> List[str]:
        """
        Analyze a failed game and generate counterfactual scenarios.
        
        Args:
            agent_id: Agent who played
            game_id: Failed game
            session_id: Session ID
            final_score: Final score (< 20, indicating failure)
            generation: Agent generation
            
        Returns:
            List of scenario_ids generated
        """
        try:
            # Get actual action sequence from database
            actual_actions = self.db.execute_query("""
                SELECT action_type, coordinate_x, coordinate_y, 
                       score_before_action, score_after_action
                FROM arc_action_tracking
                WHERE agent_id = ? AND game_id = ?
                ORDER BY action_timestamp
            """, (agent_id, game_id))
            
            if not actual_actions or len(actual_actions) < self.min_actions_for_analysis:
                self.logger.info(f"Not enough actions for counterfactual analysis: {len(actual_actions) if actual_actions else 0}")
                return []
            
            # Identify critical decision points
            decision_points = self._identify_decision_points(
                actual_actions, final_score, agent_id, game_id
            )
            
            if not decision_points:
                self.logger.info("No critical decision points identified")
                return []
            
            # Generate counterfactual scenarios
            scenarios = []
            
            for decision_point in decision_points[:self.max_counterfactuals_per_game]:
                # Generate alternative scenarios for this decision point
                alternatives = self._generate_alternatives(
                    decision_point, actual_actions, agent_id, game_id,
                    session_id, final_score, generation
                )
                scenarios.extend(alternatives)
            
            self.logger.info(
                f"Generated {len(scenarios)} counterfactual scenarios from "
                f"{len(decision_points)} decision points"
            )
            
            # Extract learnings from scenarios
            self._extract_counterfactual_learnings(scenarios, agent_id, generation)
            
            return scenarios
            
        except Exception as e:
            self.logger.error(f"Error analyzing failure: {e}")
            return []
    
    def _identify_decision_points(self, actions: List[Dict], final_score: float,
                                 agent_id: str, game_id: str) -> List[Dict]:
        """Identify critical decision points in action sequence"""
        decision_points = []
        
        for i, action in enumerate(actions):
            importance_factors = []
            importance_score = 0.0
            
            # Factor 1: Score change magnitude
            score_before = action.get('score_before_action', 0.0)
            score_after = action.get('score_after_action', 0.0)
            score_change = score_after - score_before
            
            if score_change != 0:
                importance_score += abs(score_change) / 10.0  # Normalize
                importance_factors.append({
                    'factor': 'score_change',
                    'value': score_change,
                    'weight': 0.3
                })
            
            # Factor 2: Position in sequence (early decisions matter more)
            position_weight = 1.0 - (i / len(actions))
            importance_score += position_weight * 0.3
            importance_factors.append({
                'factor': 'early_decision',
                'value': position_weight,
                'weight': 0.3
            })
            
            # Factor 3: Score plateau before this action
            if i > 0:
                plateau_length = 0
                for j in range(i-1, max(0, i-6), -1):
                    if actions[j].get('score_after_action', 0.0) == score_before:
                        plateau_length += 1
                    else:
                        break
                
                if plateau_length > 3:
                    importance_score += 0.4  # Breaking plateau is important
                    importance_factors.append({
                        'factor': 'plateau_break_attempt',
                        'value': plateau_length,
                        'weight': 0.4
                    })
            
            # Only record decision points with significant importance
            if importance_score > 0.5:
                decision_point_id = f"dp_{uuid.uuid4().hex[:12]}"
                
                # Get available actions at this point (from game state)
                available_actions = [1, 2, 3, 4, 5, 6, 7]  # All actions available
                
                self.db.execute_query("""
                    INSERT INTO decision_points (
                        decision_point_id, agent_id, game_id, action_index,
                        score_at_decision, available_actions, action_taken,
                        importance_score, importance_factors, immediate_score_change,
                        final_game_outcome
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    decision_point_id, agent_id, game_id, i,
                    score_before, json.dumps(available_actions),
                    action['action_type'], importance_score,
                    json.dumps(importance_factors), score_change,
                    'failed'
                ))
                
                decision_points.append({
                    'decision_point_id': decision_point_id,
                    'action_index': i,
                    'score': score_before,
                    'action_taken': action['action_type'],
                    'importance_score': importance_score,
                    'available_actions': available_actions
                })
        
        # Sort by importance
        decision_points.sort(key=lambda x: x['importance_score'], reverse=True)
        
        return decision_points
    
    def _generate_alternatives(self, decision_point: Dict, actual_actions: List[Dict],
                              agent_id: str, game_id: str, session_id: str,
                              final_score: float, generation: int) -> List[str]:
        """Generate alternative action sequences from decision point"""
        scenarios = []
        
        dp_index = decision_point['action_index']
        actual_action = decision_point['action_taken']
        available_actions = decision_point['available_actions']
        
        # Generate action substitution counterfactuals
        for alt_action in available_actions:
            if alt_action == actual_action:
                continue  # Skip the action that was actually taken
            
            # Create alternative sequence
            alternative_actions = [a['action_type'] for a in actual_actions]
            alternative_actions[dp_index] = alt_action
            
            # Predict outcome
            predicted_outcome, predicted_score, confidence = self._predict_outcome(
                alternative_actions, actual_actions, dp_index, alt_action
            )
            
            # Calculate learning value (how useful is this counterfactual?)
            learning_value = self._calculate_learning_value(
                decision_point['importance_score'],
                predicted_outcome,
                actual_action,
                alt_action
            )
            
            # Create scenario
            scenario_id = f"cf_{uuid.uuid4().hex[:12]}"
            
            actual_sequence = [a['action_type'] for a in actual_actions]
            
            divergence_reason = f"At critical point (importance: {decision_point['importance_score']:.2f}), " \
                              f"try ACTION{alt_action} instead of ACTION{actual_action}"
            
            self.db.execute_query("""
                INSERT INTO counterfactual_scenarios (
                    scenario_id, agent_id, game_id, session_id, generation,
                    actual_actions, actual_score, actual_outcome,
                    decision_point_index, decision_point_score,
                    counterfactual_type, alternative_actions, divergence_reason,
                    predicted_score, predicted_outcome, confidence_in_prediction,
                    learning_value, priority
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scenario_id, agent_id, game_id, session_id, generation,
                json.dumps(actual_sequence), final_score, 'failed',
                dp_index, decision_point['score'],
                'action_substitution', json.dumps(alternative_actions),
                divergence_reason, predicted_score, predicted_outcome,
                confidence, learning_value, learning_value  # priority = learning_value
            ))
            
            scenarios.append(scenario_id)
        
        return scenarios
    
    def _predict_outcome(self, alternative_actions: List[int],
                        actual_actions: List[Dict], divergence_index: int,
                        alternative_action: int) -> Tuple[str, float, float]:
        """
        Predict outcome of alternative action sequence.
        
        Returns:
            (predicted_outcome, predicted_score, confidence)
        """
        # Simple heuristic-based prediction
        # In a real implementation, this could use learned models
        
        actual_score = actual_actions[-1].get('score_after_action', 0.0) if actual_actions else 0.0
        
        # Check if alternative action was ever successful in other contexts
        # This is a simplified heuristic
        
        confidence = 0.3  # Low confidence by default
        predicted_outcome = 'likely_same'
        predicted_score = actual_score
        
        # If alternative action is ACTION6 (coordinate-based), slightly higher confidence
        if alternative_action == 6:
            confidence = 0.4
            predicted_score = actual_score + 2.0
            predicted_outcome = 'likely_improve'
        
        # If original action led to plateau, alternative likely to be better
        if divergence_index > 0 and divergence_index < len(actual_actions):
            score_before_div = actual_actions[divergence_index].get('score_before_action', 0.0)
            score_after_div = actual_actions[divergence_index].get('score_after_action', 0.0)
            
            if score_after_div == score_before_div:  # No progress with actual action
                confidence = 0.6
                predicted_score = actual_score + 3.0
                predicted_outcome = 'likely_improve'
        
        return predicted_outcome, predicted_score, confidence
    
    def _calculate_learning_value(self, importance: float, predicted_outcome: str,
                                 actual_action: int, alternative_action: int) -> float:
        """Calculate how valuable this counterfactual is for learning"""
        value = importance * 0.5  # Base on importance
        
        # Higher value for predictions that suggest improvement
        if predicted_outcome in ['likely_win', 'likely_improve']:
            value += 0.3
        
        # Diverse actions have higher learning value
        if abs(alternative_action - actual_action) > 2:
            value += 0.2
        
        return min(1.0, value)
    
    def _extract_counterfactual_learnings(self, scenario_ids: List[str],
                                         agent_id: str, generation: int):
        """Extract learnings from counterfactual scenarios"""
        try:
            if not scenario_ids:
                return
            
            # Get all scenarios
            scenarios = self.db.execute_query("""
                SELECT * FROM counterfactual_scenarios
                WHERE scenario_id IN ({})
            """.format(','.join(['?'] * len(scenario_ids))), scenario_ids)
            
            if not scenarios:
                return
            
            # Group by alternative action types
            from collections import defaultdict
            action_predictions = defaultdict(list)
            
            for scenario in scenarios:
                alt_actions = json.loads(scenario['alternative_actions'])
                dp_index = scenario['decision_point_index']
                
                if dp_index < len(alt_actions):
                    alt_action = alt_actions[dp_index]
                    action_predictions[alt_action].append({
                        'predicted_outcome': scenario['predicted_outcome'],
                        'predicted_score': scenario['predicted_score'],
                        'confidence': scenario['confidence_in_prediction']
                    })
            
            # Create learnings
            for action, predictions in action_predictions.items():
                # Count how often this action is predicted to improve
                improve_count = sum(1 for p in predictions if 'improve' in p['predicted_outcome'] or 'win' in p['predicted_outcome'])
                total_count = len(predictions)
                
                if improve_count > total_count * 0.5:  # Majority predict improvement
                    learning_id = f"cf_learning_{uuid.uuid4().hex[:12]}"
                    
                    avg_confidence = sum(p['confidence'] for p in predictions) / total_count
                    
                    description = f"ACTION{action} frequently predicted to improve outcomes " \
                                f"({improve_count}/{total_count} scenarios)"
                    
                    recommended_change = {
                        'increase_action_usage': action,
                        'contexts': 'critical_decision_points',
                        'expected_benefit': 'score_improvement'
                    }
                    
                    self.db.execute_query("""
                        INSERT INTO counterfactual_learnings (
                            learning_id, agent_id, generation, learning_type,
                            learning_description, supporting_scenarios,
                            recommended_behavior_change, confidence_score,
                            confidence_source
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        learning_id, agent_id, generation, 'action_preference',
                        description, json.dumps(scenario_ids),
                        json.dumps(recommended_change), avg_confidence,
                        'prediction'
                    ))
            
        except Exception as e:
            self.logger.error(f"Error extracting learnings: {e}")
    
    def get_priority_counterfactuals(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """Get highest priority counterfactuals for testing"""
        try:
            return self.db.execute_query("""
                SELECT * FROM counterfactual_scenarios
                WHERE agent_id = ? AND was_tested = FALSE
                ORDER BY priority DESC, learning_value DESC
                LIMIT ?
            """, (agent_id, limit))
        except Exception as e:
            self.logger.error(f"Error getting priority counterfactuals: {e}")
            return []
    
    def get_counterfactual_report(self, agent_id: Optional[str] = None,
                                 generation: Optional[int] = None) -> Dict[str, Any]:
        """Get counterfactual analysis report"""
        try:
            where_clauses = []
            params = []
            
            if agent_id:
                where_clauses.append("agent_id = ?")
                params.append(agent_id)
            if generation is not None:
                where_clauses.append("generation = ?")
                params.append(generation)
            
            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Scenario statistics
            scenarios = self.db.execute_query(f"""
                SELECT 
                    COUNT(*) as total_scenarios,
                    SUM(CASE WHEN was_tested = 1 THEN 1 ELSE 0 END) as tested_scenarios,
                    AVG(learning_value) as avg_learning_value,
                    AVG(confidence_in_prediction) as avg_confidence,
                    SUM(CASE WHEN predicted_outcome LIKE '%improve%' OR predicted_outcome LIKE '%win%' THEN 1 ELSE 0 END) as predicted_improvements
                FROM counterfactual_scenarios
                {where_sql}
            """, params)
            
            # Learnings
            learnings = self.db.execute_query(f"""
                SELECT 
                    COUNT(*) as total_learnings,
                    AVG(confidence_score) as avg_confidence,
                    SUM(times_applied) as total_applications,
                    SUM(success_when_applied) as total_successes
                FROM counterfactual_learnings
                {where_sql}
            """, params)
            
            # Top learnings
            top_learnings = self.db.execute_query(f"""
                SELECT learning_type, learning_description,
                       confidence_score, times_applied, success_when_applied
                FROM counterfactual_learnings
                {where_sql}
                ORDER BY confidence_score DESC, success_when_applied DESC
                LIMIT 10
            """, params)
            
            return {
                'scenarios': scenarios[0] if scenarios else {},
                'learnings': learnings[0] if learnings else {},
                'top_learnings': top_learnings
            }
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {}
