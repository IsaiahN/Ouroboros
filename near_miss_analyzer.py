"""
Near-Miss Analysis System - Learn from High-Score Failures
===========================================================

Analyzes games that scored 15-18/20 (near-wins) to understand what prevented
full completion. Extends performance_analyzer.py with near-miss insights.

Following Rule 2: All analysis stored in database
Following Rule 3: Enhances existing performance analysis
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from database_interface import DatabaseInterface

# Rule 1: Disable pycache
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

logger = logging.getLogger(__name__)


class NearMissAnalyzer:
    """
    Analyzes near-miss games (high scores without wins) to extract learning insights.
    
    Near-miss categories:
    - 15-18/20: Almost won, likely minor mistake or missing final step
    - 10-15/20: Strong partial completion, understand what worked
    - 5-10/20: Some progress, identify partial strategies
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Near-miss thresholds
        self.near_win_threshold = 15.0  # 15-20 points
        self.strong_partial_threshold = 10.0  # 10-15 points
        self.partial_progress_threshold = 5.0  # 5-10 points
        
        # Initialize schema
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create near-miss analysis tables"""
        try:
            # Near-miss game records
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS near_miss_games (
                    near_miss_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    generation INTEGER DEFAULT 0,
                    
                    -- Score details
                    final_score REAL NOT NULL,
                    win_threshold REAL DEFAULT 20.0,
                    score_gap REAL NOT NULL,  -- How many points away from win
                    near_miss_category TEXT NOT NULL,  -- 'near_win', 'strong_partial', 'partial_progress'
                    
                    -- Game execution
                    total_actions INTEGER NOT NULL,
                    actions_sequence TEXT,  -- JSON: action sequence taken
                    coordinates_used TEXT,  -- JSON: coordinates for ACTION6
                    frame_states TEXT,  -- JSON: key frame states during game
                    
                    -- Analysis
                    what_worked TEXT,  -- JSON: successful patterns/actions
                    what_failed TEXT,  -- JSON: failure points
                    missing_elements TEXT,  -- JSON: what was missing for win
                    critical_mistakes TEXT,  -- JSON: identified mistakes
                    
                    -- Recommendations
                    improvement_suggestions TEXT,  -- JSON: specific suggestions
                    estimated_actions_to_win INTEGER,  -- How many more actions might win
                    
                    -- Timestamps
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            # Near-miss patterns (common patterns in near-misses)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS near_miss_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,  -- 'action_sequence', 'coordinate_pattern', 'strategy'
                    pattern_description TEXT NOT NULL,
                    
                    -- Pattern details
                    pattern_signature TEXT NOT NULL,  -- JSON: pattern definition
                    game_types_affected TEXT,  -- JSON: which game types show this
                    
                    -- Occurrence
                    occurrence_count INTEGER DEFAULT 1,
                    affected_agents TEXT,  -- JSON: list of agent IDs
                    
                    -- Impact
                    avg_score_when_present REAL DEFAULT 0.0,
                    prevents_completion BOOLEAN DEFAULT FALSE,
                    correction_strategy TEXT,  -- JSON: how to fix this pattern
                    
                    -- Discovery
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Near-miss insights (agent-specific learnings)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS near_miss_insights (
                    insight_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    
                    -- Insight details
                    insight_type TEXT NOT NULL,  -- 'action_timing', 'coordinate_selection', 'strategy_flaw'
                    insight_description TEXT NOT NULL,
                    supporting_evidence TEXT,  -- JSON: near_miss_ids that support this
                    
                    -- Actionability
                    is_actionable BOOLEAN DEFAULT TRUE,
                    recommended_change TEXT,  -- JSON: specific behavior changes
                    priority REAL DEFAULT 0.5,  -- 0-1, higher = more important
                    
                    -- Validation
                    times_applied INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    effectiveness_score REAL DEFAULT 0.0,
                    
                    -- Timestamps
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_applied TIMESTAMP,
                    
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            # Create indexes
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_near_miss_agent ON near_miss_games(agent_id)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_near_miss_game ON near_miss_games(game_id)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_near_miss_category ON near_miss_games(near_miss_category)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_near_miss_score ON near_miss_games(final_score DESC)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_near_miss_patterns_active ON near_miss_patterns(is_active)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_near_miss_insights_agent ON near_miss_insights(agent_id)")
            
            self.logger.info("Near-miss analysis schema initialized")
            
        except Exception as e:
            self.logger.error(f"Schema initialization error: {e}")
    
    def analyze_near_miss(self, agent_id: str, game_id: str, session_id: str,
                         final_score: float, total_actions: int,
                         generation: int = 0) -> Optional[str]:
        """
        Analyze a near-miss game to extract learning insights.
        
        Args:
            agent_id: Agent who played
            game_id: Game that was played
            session_id: Session ID
            final_score: Final score achieved
            total_actions: Actions taken
            generation: Agent generation
            
        Returns:
            near_miss_id if analyzed, None if not a near-miss
        """
        try:
            # Check if this qualifies as a near-miss
            win_threshold = 20.0
            score_gap = win_threshold - final_score
            
            if final_score < self.partial_progress_threshold:
                return None  # Too low to learn from
            
            if final_score >= win_threshold:
                return None  # This is a win, not a near-miss
            
            # Categorize near-miss
            if final_score >= self.near_win_threshold:
                category = 'near_win'
            elif final_score >= self.strong_partial_threshold:
                category = 'strong_partial'
            else:
                category = 'partial_progress'
            
            # Get action sequence from database
            actions_data = self.db.execute_query("""
                SELECT action_type, coordinates, score_before, score_after,
                       frame_before, frame_after
                FROM arc_action_tracking
                WHERE agent_id = ? AND game_id = ?
                ORDER BY action_timestamp
            """, (agent_id, game_id))
            
            if not actions_data:
                self.logger.warning(f"No action data for near-miss analysis: {game_id}")
                return None
            
            # Extract analysis
            what_worked = self._identify_successful_actions(actions_data)
            what_failed = self._identify_failed_actions(actions_data)
            missing_elements = self._identify_missing_elements(actions_data, final_score, category)
            critical_mistakes = self._identify_critical_mistakes(actions_data, final_score)
            improvement_suggestions = self._generate_improvement_suggestions(
                what_worked, what_failed, missing_elements, critical_mistakes, category
            )
            
            # Estimate actions needed for win
            estimated_actions_to_win = self._estimate_actions_to_win(
                score_gap, total_actions, final_score
            )
            
            # Create near-miss record
            near_miss_id = f"nm_{uuid.uuid4().hex[:12]}"
            
            actions_sequence = [a['action_type'] for a in actions_data]
            coordinates_used = [a['coordinates'] for a in actions_data if a.get('coordinates')]
            
            # Store key frame states (first, middle, last)
            frame_states = []
            if len(actions_data) > 0:
                frame_states.append({
                    'position': 'start',
                    'frame': actions_data[0].get('frame_before')
                })
            if len(actions_data) > 2:
                mid_idx = len(actions_data) // 2
                frame_states.append({
                    'position': 'middle',
                    'frame': actions_data[mid_idx].get('frame_after')
                })
            if len(actions_data) > 0:
                frame_states.append({
                    'position': 'end',
                    'frame': actions_data[-1].get('frame_after')
                })
            
            self.db.execute_query("""
                INSERT INTO near_miss_games (
                    near_miss_id, agent_id, game_id, session_id, generation,
                    final_score, win_threshold, score_gap, near_miss_category,
                    total_actions, actions_sequence, coordinates_used, frame_states,
                    what_worked, what_failed, missing_elements, critical_mistakes,
                    improvement_suggestions, estimated_actions_to_win
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                near_miss_id, agent_id, game_id, session_id, generation,
                final_score, win_threshold, score_gap, category,
                total_actions, json.dumps(actions_sequence),
                json.dumps(coordinates_used), json.dumps(frame_states),
                json.dumps(what_worked), json.dumps(what_failed),
                json.dumps(missing_elements), json.dumps(critical_mistakes),
                json.dumps(improvement_suggestions), estimated_actions_to_win
            ))
            
            self.logger.info(
                f"Analyzed near-miss: {category} (score: {final_score:.1f}/20.0, "
                f"gap: {score_gap:.1f}) - {near_miss_id}"
            )
            
            # Extract patterns and insights
            self._extract_near_miss_patterns(near_miss_id, actions_data, category)
            self._generate_agent_insights(agent_id, near_miss_id, what_worked, what_failed, generation)
            
            return near_miss_id
            
        except Exception as e:
            self.logger.error(f"Error analyzing near-miss: {e}")
            return None
    
    def _identify_successful_actions(self, actions_data: List[Dict]) -> List[Dict]:
        """Identify actions that increased score"""
        successful = []
        
        for action in actions_data:
            score_before = action.get('score_before', 0.0)
            score_after = action.get('score_after', 0.0)
            
            if score_after > score_before:
                successful.append({
                    'action_type': action['action_type'],
                    'coordinates': action.get('coordinates'),
                    'score_gain': score_after - score_before,
                    'context': 'score_improvement'
                })
        
        return successful
    
    def _identify_failed_actions(self, actions_data: List[Dict]) -> List[Dict]:
        """Identify actions that didn't help or hurt progress"""
        failed = []
        
        for action in actions_data:
            score_before = action.get('score_before', 0.0)
            score_after = action.get('score_after', 0.0)
            
            # No progress actions
            if score_after == score_before:
                failed.append({
                    'action_type': action['action_type'],
                    'coordinates': action.get('coordinates'),
                    'issue': 'no_progress',
                    'context': 'wasted_action'
                })
        
        return failed
    
    def _identify_missing_elements(self, actions_data: List[Dict],
                                  final_score: float, category: str) -> List[Dict]:
        """Identify what was missing to achieve win"""
        missing = []
        
        # Check for action diversity
        action_types = [a['action_type'] for a in actions_data]
        unique_actions = set(action_types)
        
        if len(unique_actions) < 3:
            missing.append({
                'element': 'action_diversity',
                'description': 'Limited action variety, may need more exploration',
                'severity': 'moderate'
            })
        
        # Check for coordinate usage (ACTION6)
        coordinate_actions = [a for a in actions_data if a.get('coordinates')]
        
        if category == 'near_win' and len(coordinate_actions) < 10:
            missing.append({
                'element': 'coordinate_precision',
                'description': 'Near win suggests specific coordinates might be needed',
                'severity': 'high'
            })
        
        # Check for sufficient actions
        if len(actions_data) < 30 and category != 'partial_progress':
            missing.append({
                'element': 'action_count',
                'description': 'May need more actions to complete',
                'severity': 'moderate'
            })
        
        # Check score progression
        if len(actions_data) > 0:
            first_score = actions_data[0].get('score_before', 0.0)
            last_score = actions_data[-1].get('score_after', 0.0)
            
            if last_score - first_score < 5.0 and len(actions_data) > 20:
                missing.append({
                    'element': 'score_momentum',
                    'description': 'Low score gain despite many actions',
                    'severity': 'high'
                })
        
        return missing
    
    def _identify_critical_mistakes(self, actions_data: List[Dict],
                                   final_score: float) -> List[Dict]:
        """Identify potential critical mistakes that prevented win"""
        mistakes = []
        
        # Check for action spam (same action repeatedly)
        from collections import Counter
        action_counts = Counter(a['action_type'] for a in actions_data)
        
        for action_type, count in action_counts.items():
            if count > len(actions_data) * 0.4:  # >40% of all actions
                mistakes.append({
                    'mistake_type': 'action_spam',
                    'action_type': action_type,
                    'count': count,
                    'description': f'Overused ACTION{action_type} ({count} times)',
                    'impact': 'high'
                })
        
        # Check for score plateaus (long periods with no improvement)
        plateau_length = 0
        max_plateau = 0
        last_score = 0.0
        
        for action in actions_data:
            current_score = action.get('score_after', 0.0)
            if current_score == last_score:
                plateau_length += 1
                max_plateau = max(max_plateau, plateau_length)
            else:
                plateau_length = 0
            last_score = current_score
        
        if max_plateau > 15:
            mistakes.append({
                'mistake_type': 'score_plateau',
                'plateau_length': max_plateau,
                'description': f'Stuck for {max_plateau} actions without score improvement',
                'impact': 'moderate'
            })
        
        return mistakes
    
    def _generate_improvement_suggestions(self, what_worked: List[Dict],
                                         what_failed: List[Dict],
                                         missing_elements: List[Dict],
                                         critical_mistakes: List[Dict],
                                         category: str) -> List[Dict]:
        """Generate specific improvement suggestions"""
        suggestions = []
        
        # Suggestions based on successful actions
        if what_worked:
            successful_action_types = set(a['action_type'] for a in what_worked)
            suggestions.append({
                'type': 'repeat_success',
                'priority': 'high',
                'description': f'Actions that worked: {successful_action_types}',
                'action': 'Focus more on these action types'
            })
        
        # Suggestions based on missing elements
        for missing in missing_elements:
            if missing['element'] == 'coordinate_precision':
                suggestions.append({
                    'type': 'increase_coordinates',
                    'priority': 'high',
                    'description': 'Need more coordinate-based actions (ACTION6)',
                    'action': 'Try more strategic coordinate placements'
                })
            elif missing['element'] == 'action_diversity':
                suggestions.append({
                    'type': 'diversify_actions',
                    'priority': 'moderate',
                    'description': 'Limited action variety detected',
                    'action': 'Explore different action types'
                })
        
        # Suggestions based on mistakes
        for mistake in critical_mistakes:
            if mistake['mistake_type'] == 'action_spam':
                suggestions.append({
                    'type': 'reduce_spam',
                    'priority': 'high',
                    'description': f'Overusing ACTION{mistake["action_type"]}',
                    'action': 'Reduce repetition and try alternatives'
                })
            elif mistake['mistake_type'] == 'score_plateau':
                suggestions.append({
                    'type': 'break_plateau',
                    'priority': 'high',
                    'description': 'Long period without progress',
                    'action': 'Try completely different approach when stuck'
                })
        
        # Category-specific suggestions
        if category == 'near_win':
            suggestions.append({
                'type': 'final_push',
                'priority': 'critical',
                'description': 'Very close to win, likely missing final step',
                'action': 'Analyze end state carefully for final required action'
            })
        
        return suggestions
    
    def _estimate_actions_to_win(self, score_gap: float, actions_taken: int,
                                final_score: float) -> int:
        """Estimate how many more actions might be needed to win"""
        if final_score == 0:
            return 50  # Complete restart needed
        
        # Calculate score per action efficiency
        score_per_action = final_score / actions_taken if actions_taken > 0 else 0.1
        
        # Estimate actions needed
        if score_per_action > 0:
            estimated = int(score_gap / score_per_action)
            return max(5, min(estimated, 50))  # Clamp between 5-50
        
        return 25  # Default estimate
    
    def _extract_near_miss_patterns(self, near_miss_id: str, actions_data: List[Dict],
                                   category: str):
        """Extract common patterns from near-miss games"""
        try:
            # Check for common failure patterns
            action_sequence = [a['action_type'] for a in actions_data]
            
            # Pattern: Excessive ACTION1 without progress
            action1_count = action_sequence.count('ACTION1')
            if action1_count > len(action_sequence) * 0.5:
                self._record_near_miss_pattern(
                    'action_spam',
                    'Excessive ACTION1 without progress',
                    {'action_type': 'ACTION1', 'threshold': 0.5},
                    [near_miss_id]
                )
            
        except Exception as e:
            self.logger.error(f"Error extracting patterns: {e}")
    
    def _record_near_miss_pattern(self, pattern_type: str, description: str,
                                  signature: Dict, near_miss_ids: List[str]):
        """Record a near-miss pattern"""
        try:
            import hashlib
            sig_str = json.dumps(signature, sort_keys=True)
            pattern_hash = hashlib.md5(sig_str.encode()).hexdigest()[:16]
            pattern_id = f"nmp_{pattern_hash}"
            
            # Check if pattern exists
            existing = self.db.execute_query("""
                SELECT occurrence_count, affected_agents
                FROM near_miss_patterns
                WHERE pattern_id = ?
            """, (pattern_id,))
            
            if existing:
                # Update existing
                count = existing[0]['occurrence_count'] + 1
                self.db.execute_query("""
                    UPDATE near_miss_patterns
                    SET occurrence_count = ?, last_seen = ?
                    WHERE pattern_id = ?
                """, (count, datetime.now().isoformat(), pattern_id))
            else:
                # Create new
                self.db.execute_query("""
                    INSERT INTO near_miss_patterns (
                        pattern_id, pattern_type, pattern_description,
                        pattern_signature, occurrence_count
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    pattern_id, pattern_type, description,
                    json.dumps(signature), 1
                ))
            
        except Exception as e:
            self.logger.error(f"Error recording pattern: {e}")
    
    def _generate_agent_insights(self, agent_id: str, near_miss_id: str,
                                what_worked: List[Dict], what_failed: List[Dict],
                                generation: int):
        """Generate agent-specific insights from near-miss"""
        try:
            insights = []
            
            # Insight: Successful action patterns
            if what_worked:
                insight_id = f"insight_{uuid.uuid4().hex[:12]}"
                successful_actions = set(a['action_type'] for a in what_worked)
                
                insights.append({
                    'insight_id': insight_id,
                    'insight_type': 'successful_actions',
                    'description': f'Actions that score points: {successful_actions}',
                    'recommended_change': {
                        'increase_usage': list(successful_actions)
                    },
                    'priority': 0.8
                })
            
            # Insight: Failed action patterns
            if what_failed and len(what_failed) > 5:
                insight_id = f"insight_{uuid.uuid4().hex[:12]}"
                failed_actions = set(a['action_type'] for a in what_failed)
                
                insights.append({
                    'insight_id': insight_id,
                    'insight_type': 'failed_actions',
                    'description': f'Actions with no effect: {failed_actions}',
                    'recommended_change': {
                        'reduce_usage': list(failed_actions)
                    },
                    'priority': 0.6
                })
            
            # Store insights
            for insight in insights:
                self.db.execute_query("""
                    INSERT INTO near_miss_insights (
                        insight_id, agent_id, generation, insight_type,
                        insight_description, supporting_evidence,
                        recommended_change, priority
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    insight['insight_id'], agent_id, generation,
                    insight['insight_type'], insight['description'],
                    json.dumps([near_miss_id]),
                    json.dumps(insight['recommended_change']),
                    insight['priority']
                ))
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
    
    def get_near_miss_report(self, agent_id: Optional[str] = None,
                            generation: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive near-miss analysis report"""
        try:
            # Overall statistics
            stats = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_near_misses,
                    SUM(CASE WHEN near_miss_category = 'near_win' THEN 1 ELSE 0 END) as near_wins,
                    SUM(CASE WHEN near_miss_category = 'strong_partial' THEN 1 ELSE 0 END) as strong_partials,
                    AVG(final_score) as avg_score,
                    AVG(score_gap) as avg_gap_to_win,
                    AVG(estimated_actions_to_win) as avg_estimated_actions
                FROM near_miss_games
                {} {}
            """.format(
                f"WHERE agent_id = '{agent_id}'" if agent_id else "",
                f"{'AND' if agent_id else 'WHERE'} generation = {generation}" if generation else ""
            ))
            
            # Common patterns
            patterns = self.db.execute_query("""
                SELECT pattern_type, pattern_description, occurrence_count,
                       avg_score_when_present
                FROM near_miss_patterns
                WHERE is_active = TRUE
                ORDER BY occurrence_count DESC
                LIMIT 10
            """)
            
            # Top insights
            insights = self.db.execute_query("""
                SELECT insight_type, insight_description, priority,
                       times_applied, success_count, effectiveness_score
                FROM near_miss_insights
                {} {}
                ORDER BY priority DESC, effectiveness_score DESC
                LIMIT 10
            """.format(
                f"WHERE agent_id = '{agent_id}'" if agent_id else "",
                f"{'AND' if agent_id else 'WHERE'} generation = {generation}" if generation else ""
            ))
            
            return {
                'statistics': stats[0] if stats else {},
                'common_patterns': patterns,
                'top_insights': insights,
                'thresholds': {
                    'near_win': self.near_win_threshold,
                    'strong_partial': self.strong_partial_threshold,
                    'partial_progress': self.partial_progress_threshold
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {}
