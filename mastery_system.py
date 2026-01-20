"""
Mastery-Gated Replay System
===========================

Philosophy: Sequences are a PRIVILEGE, not a default.
Agents must EARN the right to replay by demonstrating understanding.

Key Metrics:
1. Diversity (30 pts) - Multiple different winning strategies exist
2. Robustness (30 pts) - Winning even when actions skipped (ablation)
3. Consistency (20 pts) - Sequences work across different agents  
4. Efficiency (20 pts) - Sequences improving over time (>5% threshold)

Tier System:
- Novice (0-24): NO replay allowed
- Apprentice (25-49): Study only (essential actions shown)
- Practitioner (50-74): 70% replay / 30% forced exploration
- Expert (75-94): 90% replay / 10% forced exploration  
- Master (95-100): 95% replay / 5% forced exploration

Ablation Difficulty (scales with tier):
- Practitioner: 10-20% actions skipped
- Expert: 20-30% actions skipped
- Master: 30-50% actions skipped (stress test)

Integration Points:
- core_gameplay._get_best_sequence_for_game() - Gating
- core_gameplay._replay_sequence_inline_impl_body() - Stealth ablation
- autonomous_evolution_runner.run_cycle() - Mastery updates

Following Rule 1: PYTHONDONTWRITEBYTECODE=1
Following Rule 2: All data stored in database (level_mastery, ablation_test_results)
Following Rule 11: No Unicode emojis
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1

import json
import uuid
import logging
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MasteryStatus:
    """Mastery status for a game-level."""
    game_type: str
    level_number: int
    tier: str  # novice/apprentice/practitioner/expert/master
    total_score: float
    diversity_score: float
    ablation_score: float
    consistency_score: float
    efficiency_score: float
    unique_sequences: int
    ablation_success_rate: Optional[float]
    unique_agents: int
    cross_agent_success_rate: float
    replay_probability: float
    # Internal tracking
    _decay_applied: bool = field(default=False, repr=False)


class MasterySystem:
    """
    Mastery-gated replay system.
    
    Prevents cargo-cult sequence copying by requiring demonstrated understanding.
    Sequences become dogma without this - agents blindly replay without learning WHY.
    
    Key Principles:
    - Hard reset: All existing sequences start at Novice (no grandfathering)
    - Stealth ablation: Agents don't know when being tested
    - Tiered difficulty: Skip rate scales with claimed mastery
    - Mastery decay: Performance degradation reduces scores
    - Event-driven: Updates on discoveries and ablation results
    """
    
    # Tier thresholds and replay probabilities
    TIER_CONFIG = {
        'novice':       {'min_score': 0,  'max_score': 24,  'replay_prob': 0.00, 'forced_explore': 1.00},
        'apprentice':   {'min_score': 25, 'max_score': 49,  'replay_prob': 0.00, 'forced_explore': 1.00},
        'practitioner': {'min_score': 50, 'max_score': 74,  'replay_prob': 0.70, 'forced_explore': 0.30},
        'expert':       {'min_score': 75, 'max_score': 94,  'replay_prob': 0.90, 'forced_explore': 0.10},
        'master':       {'min_score': 95, 'max_score': 100, 'replay_prob': 0.95, 'forced_explore': 0.05},
    }
    
    # Ablation skip rates by tier (min, max)
    ABLATION_SKIP_RATES = {
        'novice':       (0.00, 0.00),  # No ablation at novice (hasn't earned replay anyway)
        'apprentice':   (0.10, 0.20),  # Gentle test
        'practitioner': (0.10, 0.20),  # Same as apprentice
        'expert':       (0.20, 0.30),  # Moderate stress
        'master':       (0.30, 0.50),  # Serious stress test
    }
    
    def __init__(self, db: 'DatabaseInterface'):
        """
        Initialize mastery system.
        
        Args:
            db: DatabaseInterface instance for data storage
        """
        self.db = db
        self._ensure_tables()
        logger.info("[MASTERY] System initialized")
    
    def _ensure_tables(self):
        """Create mastery tables if they don't exist."""
        # level_mastery table - stores mastery scores per game-level
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS level_mastery (
                mastery_id TEXT PRIMARY KEY,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Diversity Metrics (max 30 points)
                unique_sequence_count INTEGER DEFAULT 0,
                diversity_score REAL DEFAULT 0.0,
                
                -- Ablation Metrics (max 30 points)
                ablation_tests_total INTEGER DEFAULT 0,
                ablation_tests_passed INTEGER DEFAULT 0,
                ablation_success_rate REAL DEFAULT 0.0,
                ablation_score REAL DEFAULT 0.0,
                
                -- Consistency Metrics (max 20 points)
                unique_agents_succeeded INTEGER DEFAULT 0,
                cross_agent_success_rate REAL DEFAULT 0.0,
                consistency_score REAL DEFAULT 0.0,
                
                -- Efficiency Metrics (max 20 points)
                best_actions_ever INTEGER,
                best_actions_generation INTEGER,
                improvement_count INTEGER DEFAULT 0,
                efficiency_score REAL DEFAULT 0.0,
                
                -- Aggregate
                total_mastery_score REAL DEFAULT 0.0,
                mastery_tier TEXT DEFAULT 'novice',
                
                -- Decay tracking
                last_decay_at TIMESTAMP,
                decay_count INTEGER DEFAULT 0,
                
                -- Timestamps
                first_win_at TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated_generation INTEGER DEFAULT 0,
                tier_upgraded_at TIMESTAMP,
                
                UNIQUE(game_type, level_number)
            )
        """)
        
        # ablation_test_results table - records stealth ablation test outcomes
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS ablation_test_results (
                test_id TEXT PRIMARY KEY,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                sequence_id TEXT NOT NULL,
                
                -- Test configuration
                skipped_action_indices TEXT NOT NULL,
                skip_rate REAL NOT NULL,
                mastery_tier_at_test TEXT,
                
                -- Results
                test_passed BOOLEAN NOT NULL,
                actions_taken INTEGER,
                final_score REAL,
                recovery_method TEXT,
                
                -- Context
                agent_id TEXT,
                generation INTEGER,
                tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # sequence_improvements table - tracks significant improvements only (>5%)
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS sequence_improvements (
                improvement_id TEXT PRIMARY KEY,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Before/After
                previous_sequence_id TEXT,
                previous_actions INTEGER NOT NULL,
                new_sequence_id TEXT NOT NULL,
                new_actions INTEGER NOT NULL,
                
                -- Calculated improvement
                reduction_count INTEGER,
                reduction_pct REAL,
                
                -- Context
                discovered_by_agent TEXT,
                generation INTEGER,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indices for efficient queries
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_level_mastery_lookup 
            ON level_mastery(game_type, level_number)
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_level_mastery_tier 
            ON level_mastery(mastery_tier, total_mastery_score DESC)
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_ablation_lookup 
            ON ablation_test_results(game_type, level_number)
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_ablation_recent 
            ON ablation_test_results(tested_at DESC)
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_improvements_game 
            ON sequence_improvements(game_type, level_number)
        """)
        
        logger.debug("[MASTERY] Tables and indices verified")
    
    def calculate_mastery(self, game_type: str, level_number: int) -> MasteryStatus:
        """
        Calculate current mastery score for a game-level.
        
        Uses ONLY data already being collected:
        - winning_sequences (diversity)
        - ablation_test_results (robustness)
        - sequence_validation_attempts (consistency)
        - optimization_status + sequence_improvements (efficiency)
        
        Args:
            game_type: Game type prefix (e.g., 'vc33', 'ls20')
            level_number: Level within the game
            
        Returns:
            MasteryStatus with all calculated metrics
        """
        # ================================================================
        # METRIC 1: DIVERSITY (max 30 points)
        # ================================================================
        # How many structurally DIFFERENT sequences win this level?
        sequences = self.db.execute_query("""
            SELECT sequence_id, action_sequence, total_actions
            FROM winning_sequences
            WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
            ORDER BY discovered_at ASC
        """, (f"{game_type}-%", level_number))
        
        unique_strategies = self._count_unique_sequences(sequences, similarity_threshold=0.8)
        # 0-1 unique = 0 pts, 2 unique = 10 pts, 3+ unique = 20 pts, 5+ unique = 30 pts
        if unique_strategies >= 5:
            diversity_score = 30.0
        elif unique_strategies >= 3:
            diversity_score = 20.0
        elif unique_strategies >= 2:
            diversity_score = 10.0
        else:
            diversity_score = 0.0
        
        # ================================================================
        # METRIC 2: ABLATION ROBUSTNESS (max 30 points)
        # ================================================================
        # During replay, we randomly skip 10-50% of actions (based on tier).
        # If agent STILL wins, they understand the pattern, not just memorizing.
        ablation_results = self.db.execute_query("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN test_passed THEN 1 ELSE 0 END) as passed
            FROM ablation_test_results
            WHERE game_type = ? AND level_number = ?
        """, (game_type, level_number))
        
        ablation_success_rate = None
        if ablation_results and ablation_results[0]['total'] and ablation_results[0]['total'] > 0:
            total = ablation_results[0]['total']
            passed = ablation_results[0]['passed'] or 0
            ablation_success_rate = passed / total
            ablation_score = ablation_success_rate * 30.0
        else:
            ablation_score = 0.0
        
        # ================================================================
        # METRIC 3: CROSS-AGENT CONSISTENCY (max 20 points)
        # ================================================================
        # Do sequences work for DIFFERENT agents? Or only the discoverer?
        validation = self.db.execute_query("""
            SELECT 
                COUNT(DISTINCT agent_id) as unique_agents,
                AVG(CASE WHEN validation_success THEN 1.0 ELSE 0.0 END) as success_rate
            FROM sequence_validation_attempts
            WHERE game_id LIKE ? 
              AND sequence_id IN (
                  SELECT sequence_id FROM winning_sequences 
                  WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
              )
        """, (f"{game_type}-%", f"{game_type}-%", level_number))
        
        unique_agents = 0
        cross_agent_success_rate = 0.0
        if validation and validation[0]['unique_agents']:
            unique_agents = validation[0]['unique_agents']
            cross_agent_success_rate = validation[0]['success_rate'] or 0.0
        
        # Need 3+ unique agents AND >70% success rate for full points
        agent_score = min(unique_agents * 3.0, 10.0)  # Up to 10 pts for agent diversity
        reliability_score = cross_agent_success_rate * 10.0  # Up to 10 pts for reliability
        consistency_score = agent_score + reliability_score
        
        # ================================================================
        # METRIC 4: EFFICIENCY IMPROVEMENT (max 20 points)
        # ================================================================
        # Are sequences getting SIGNIFICANTLY better over time? Or stagnant?
        # Only count improvements > 5% reduction (filters noise optimization)
        optimization = self.db.execute_query("""
            SELECT 
                best_actions,
                generations_without_improvement,
                improvement_rate
            FROM optimization_status
            WHERE game_id LIKE ? AND level_number = ?
            LIMIT 1
        """, (f"{game_type}-%", level_number))
        
        # Get significant improvement count (>5% reduction each)
        improvements = self.db.execute_query("""
            SELECT COUNT(*) as count
            FROM sequence_improvements
            WHERE game_type = ? AND level_number = ?
              AND reduction_pct > 0.05
        """, (game_type, level_number))
        
        significant_improvement_count = 0
        if improvements and improvements[0]['count']:
            significant_improvement_count = improvements[0]['count']
        
        efficiency_score = 0.0
        if optimization and optimization[0]:
            opt = optimization[0]
            # Significant improvements only (>5% reduction each)
            improvement_score = min(significant_improvement_count * 5.0, 10.0)
            # Recent improvements matter more - lose points for stagnation
            gens_without = opt.get('generations_without_improvement') or 0
            recency_score = max(0.0, 10.0 - gens_without)
            efficiency_score = improvement_score + recency_score
        
        # ================================================================
        # AGGREGATE
        # ================================================================
        total_score = diversity_score + ablation_score + consistency_score + efficiency_score
        
        # Determine tier
        tier = self._score_to_tier(total_score)
        
        # Get replay probability from tier config
        replay_probability = self.TIER_CONFIG[tier]['replay_prob']
        
        return MasteryStatus(
            game_type=game_type,
            level_number=level_number,
            tier=tier,
            total_score=total_score,
            diversity_score=diversity_score,
            ablation_score=ablation_score,
            consistency_score=consistency_score,
            efficiency_score=efficiency_score,
            unique_sequences=unique_strategies,
            ablation_success_rate=ablation_success_rate,
            unique_agents=unique_agents,
            cross_agent_success_rate=cross_agent_success_rate,
            replay_probability=replay_probability
        )
    
    def _count_unique_sequences(self, sequences: List[Dict], similarity_threshold: float = 0.8) -> int:
        """
        Count structurally unique sequences using edit distance clustering.
        
        Two sequences are considered the same strategy if similarity > threshold.
        
        Args:
            sequences: List of sequence dicts with 'action_sequence' field
            similarity_threshold: Similarity above which sequences are considered same
            
        Returns:
            Count of unique strategies
        """
        if not sequences:
            return 0
        
        unique_strategies = []
        
        for seq in sequences:
            try:
                action_seq = seq.get('action_sequence', '')
                if isinstance(action_seq, str):
                    actions = json.loads(action_seq)
                else:
                    actions = action_seq
                
                if not actions:
                    continue
                    
            except (json.JSONDecodeError, TypeError):
                continue
            
            is_unique = True
            for unique_actions in unique_strategies:
                distance = self._sequence_edit_distance(actions, unique_actions)
                similarity = 1.0 - distance
                
                if similarity > similarity_threshold:
                    is_unique = False
                    break
            
            if is_unique:
                unique_strategies.append(actions)
        
        return len(unique_strategies)
    
    def _sequence_edit_distance(self, seq_a: List[int], seq_b: List[int]) -> float:
        """
        Calculate normalized edit distance between two action sequences.
        
        Args:
            seq_a, seq_b: Action sequences as lists of action IDs
            
        Returns: 
            0.0 (identical) to 1.0 (completely different)
        """
        if not seq_a or not seq_b:
            return 1.0
        
        m, n = len(seq_a), len(seq_b)
        
        # Dynamic programming table
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq_a[i-1] == seq_b[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        
        # Normalize by max length
        max_len = max(m, n)
        return dp[m][n] / max_len if max_len > 0 else 0.0
    
    def _score_to_tier(self, score: float) -> str:
        """Convert numeric score to tier name."""
        if score >= 95:
            return 'master'
        elif score >= 75:
            return 'expert'
        elif score >= 50:
            return 'practitioner'
        elif score >= 25:
            return 'apprentice'
        else:
            return 'novice'
    
    def should_allow_replay(self, game_type: str, level_number: int) -> Tuple[bool, str, MasteryStatus]:
        """
        Determine if replay should be allowed for this game-level.
        
        Uses probabilistic gating based on mastery tier:
        - Novice/Apprentice: NEVER allow replay (must explore)
        - Practitioner: 70% replay probability
        - Expert: 90% replay probability
        - Master: 95% replay probability
        
        Args:
            game_type: Game type prefix
            level_number: Level within the game
            
        Returns:
            Tuple of (allowed: bool, reason: str, mastery: MasteryStatus)
        """
        mastery = self.get_mastery(game_type, level_number)
        
        roll = random.random()
        
        if roll > mastery.replay_probability:
            return (
                False, 
                f"tier={mastery.tier} score={mastery.total_score:.0f} - FORCED EXPLORATION "
                f"(rolled {roll:.2f} > {mastery.replay_probability:.2f})",
                mastery
            )
        else:
            return (
                True, 
                f"tier={mastery.tier} score={mastery.total_score:.0f} - REPLAY ALLOWED",
                mastery
            )
    
    def get_mastery(self, game_type: str, level_number: int, 
                    current_generation: Optional[int] = None) -> MasteryStatus:
        """
        Get mastery status for a game-level, using cache if fresh.
        
        Args:
            game_type: Game type prefix
            level_number: Level within the game
            current_generation: Current generation (for staleness check)
            
        Returns:
            MasteryStatus for the game-level
        """
        # Check cache first
        result = self.db.execute_query("""
            SELECT * FROM level_mastery
            WHERE game_type = ? AND level_number = ?
        """, (game_type, level_number))
        
        if result:
            m = result[0]
            # Check if stale (older than 1 generation)
            if current_generation is not None:
                last_gen = m.get('last_updated_generation') or 0
                if current_generation - last_gen <= 1:
                    # Return cached value
                    return MasteryStatus(
                        game_type=game_type,
                        level_number=level_number,
                        tier=m['mastery_tier'] or 'novice',
                        total_score=m['total_mastery_score'] or 0.0,
                        diversity_score=m['diversity_score'] or 0.0,
                        ablation_score=m['ablation_score'] or 0.0,
                        consistency_score=m['consistency_score'] or 0.0,
                        efficiency_score=m['efficiency_score'] or 0.0,
                        unique_sequences=m['unique_sequence_count'] or 0,
                        ablation_success_rate=m['ablation_success_rate'],
                        unique_agents=m['unique_agents_succeeded'] or 0,
                        cross_agent_success_rate=m['cross_agent_success_rate'] or 0.0,
                        replay_probability=self.TIER_CONFIG.get(
                            m['mastery_tier'] or 'novice', 
                            {'replay_prob': 0.0}
                        )['replay_prob']
                    )
        
        # Recalculate mastery
        return self.calculate_mastery(game_type, level_number)
    
    def get_ablation_skip_rate(self, tier: str) -> Tuple[float, float]:
        """
        Get ablation skip rate range for a tier.
        
        Higher tiers face harder ablation tests (more actions skipped).
        
        Args:
            tier: Mastery tier name
            
        Returns:
            Tuple of (min_skip_rate, max_skip_rate)
        """
        return self.ABLATION_SKIP_RATES.get(tier, (0.10, 0.20))
    
    def record_ablation_result(
        self,
        game_type: str,
        level_number: int,
        sequence_id: str,
        skipped_indices: List[int],
        skip_rate: float,
        test_passed: bool,
        actions_taken: int,
        final_score: float,
        agent_id: str,
        generation: int,
        tier_at_test: str
    ):
        """
        Record result of a stealth ablation test.
        
        Args:
            game_type: Game type prefix
            level_number: Level within the game
            sequence_id: ID of sequence being tested
            skipped_indices: List of action indices that were skipped
            skip_rate: Percentage of actions that were skipped
            test_passed: Whether agent still won despite skipped actions
            actions_taken: Total actions taken during test
            final_score: Score achieved
            agent_id: ID of agent being tested
            generation: Current generation
            tier_at_test: Mastery tier when test was conducted
        """
        test_id = f"abl_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO ablation_test_results (
                test_id, game_type, level_number, sequence_id,
                skipped_action_indices, skip_rate, mastery_tier_at_test,
                test_passed, actions_taken, final_score,
                recovery_method, agent_id, generation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id,
            game_type, level_number, sequence_id,
            json.dumps(skipped_indices), skip_rate, tier_at_test,
            test_passed, actions_taken, final_score,
            'stealth_replay',
            agent_id, generation
        ))
        
        # Trigger event-driven mastery update
        self.trigger_update(game_type, level_number, 'ablation_complete')
        
        logger.info(f"[ABLATION-RESULT] {'PASSED' if test_passed else 'FAILED'} - "
                   f"tier={tier_at_test}, skipped {len(skipped_indices)} actions "
                   f"({skip_rate:.0%}), score={final_score}")
    
    def record_sequence_improvement(
        self,
        game_type: str,
        level_number: int,
        previous_sequence_id: Optional[str],
        previous_actions: int,
        new_sequence_id: str,
        new_actions: int,
        agent_id: str,
        generation: int
    ) -> bool:
        """
        Record a sequence improvement if significant (>5% reduction).
        
        Args:
            game_type: Game type prefix
            level_number: Level within the game
            previous_sequence_id: ID of previous best sequence
            previous_actions: Action count of previous sequence
            new_sequence_id: ID of new improved sequence
            new_actions: Action count of new sequence
            agent_id: ID of agent who discovered improvement
            generation: Current generation
            
        Returns:
            True if improvement was significant and recorded, False otherwise
        """
        if previous_actions <= 0:
            return False
            
        reduction_count = previous_actions - new_actions
        reduction_pct = reduction_count / previous_actions
        
        # Only record significant improvements (>5%)
        if reduction_pct <= 0.05:
            return False
        
        improvement_id = f"imp_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO sequence_improvements (
                improvement_id, game_type, level_number,
                previous_sequence_id, previous_actions,
                new_sequence_id, new_actions,
                reduction_count, reduction_pct,
                discovered_by_agent, generation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            improvement_id,
            game_type, level_number,
            previous_sequence_id, previous_actions,
            new_sequence_id, new_actions,
            reduction_count, reduction_pct,
            agent_id, generation
        ))
        
        # Trigger event-driven mastery update
        self.trigger_update(game_type, level_number, 'optimization_found')
        
        logger.info(f"[MASTERY-IMPROVEMENT] {game_type} L{level_number}: "
                   f"{previous_actions} -> {new_actions} actions ({reduction_pct:.0%} reduction)")
        
        return True
    
    def trigger_update(self, game_type: str, level_number: int, trigger: str):
        """
        Event-driven mastery update for specific game-level.
        
        Called on significant events rather than waiting for generation end:
        - 'sequence_discovered': New winning sequence found
        - 'ablation_complete': Ablation test just finished
        - 'validation_complete': Cross-agent validation finished
        - 'optimization_found': New shorter sequence discovered
        
        Args:
            game_type: Game type prefix
            level_number: Level within the game
            trigger: Event type that triggered update
        """
        mastery = self.calculate_mastery(game_type, level_number)
        mastery = self._apply_mastery_decay(mastery, game_type, level_number)
        
        # Get current generation
        gen_result = self.db.execute_query(
            "SELECT MAX(generation) as gen FROM game_results"
        )
        current_gen = gen_result[0]['gen'] if gen_result and gen_result[0]['gen'] else 0
        
        self._store_mastery(mastery, current_gen)
        
        logger.debug(f"[MASTERY-EVENT] {trigger}: {game_type} L{level_number} -> "
                    f"tier={mastery.tier} score={mastery.total_score:.1f}")
    
    def _apply_mastery_decay(self, mastery: MasteryStatus, game_type: str, 
                             level_number: int) -> MasteryStatus:
        """
        Apply mastery decay if ablation performance is degrading.
        
        Prevents "master tier lock-in" when performance drops.
        
        Decay triggers:
        - Expert/Master tier with <60% ablation success in last 20 tests
        - Recent ablation success rate dropped 20%+ from historical average
        
        Args:
            mastery: Current MasteryStatus
            game_type: Game type prefix
            level_number: Level within the game
            
        Returns:
            MasteryStatus with decay applied if needed
        """
        mastery._decay_applied = False
        
        # Only apply decay to Expert and Master tiers
        if mastery.tier not in ('expert', 'master'):
            return mastery
        
        # Get recent ablation performance (last 20 tests)
        recent = self.db.execute_query("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN test_passed THEN 1 ELSE 0 END) as passed
            FROM (
                SELECT test_passed 
                FROM ablation_test_results
                WHERE game_type = ? AND level_number = ?
                ORDER BY tested_at DESC
                LIMIT 20
            )
        """, (game_type, level_number))
        
        if not recent or not recent[0]['total'] or recent[0]['total'] < 5:
            return mastery  # Not enough recent data
        
        recent_total = recent[0]['total']
        recent_passed = recent[0]['passed'] or 0
        recent_success_rate = recent_passed / recent_total
        
        # Get historical ablation performance (all time)
        historical = self.db.execute_query("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN test_passed THEN 1 ELSE 0 END) as passed
            FROM ablation_test_results
            WHERE game_type = ? AND level_number = ?
        """, (game_type, level_number))
        
        hist_total = historical[0]['total'] if historical and historical[0]['total'] else 1
        hist_passed = historical[0]['passed'] if historical and historical[0]['passed'] else 0
        historical_success_rate = hist_passed / hist_total
        
        # DECAY TRIGGER: Recent performance <60% OR dropped 20%+ from historical
        should_decay = (
            recent_success_rate < 0.60 or
            (historical_success_rate - recent_success_rate) > 0.20
        )
        
        if should_decay:
            # Apply 20% decay to ablation score
            old_ablation = mastery.ablation_score
            mastery.ablation_score *= 0.80
            
            # Recalculate total and tier
            mastery.total_score = (
                mastery.diversity_score + 
                mastery.ablation_score + 
                mastery.consistency_score + 
                mastery.efficiency_score
            )
            mastery.tier = self._score_to_tier(mastery.total_score)
            mastery.replay_probability = self.TIER_CONFIG[mastery.tier]['replay_prob']
            mastery._decay_applied = True
            
            # Record decay in database
            self.db.execute_query("""
                UPDATE level_mastery
                SET decay_count = COALESCE(decay_count, 0) + 1,
                    last_decay_at = CURRENT_TIMESTAMP
                WHERE game_type = ? AND level_number = ?
            """, (game_type, level_number))
            
            logger.warning(f"[MASTERY-DECAY] {game_type} L{level_number}: "
                          f"ablation {old_ablation:.1f}->{mastery.ablation_score:.1f} "
                          f"(recent={recent_success_rate:.0%}, historical={historical_success_rate:.0%}) "
                          f"tier now={mastery.tier}")
        
        return mastery
    
    def _store_mastery(self, mastery: MasteryStatus, generation: int):
        """
        Store/update mastery in database.
        
        Args:
            mastery: MasteryStatus to store
            generation: Current generation number
        """
        mastery_id = f"mast_{mastery.game_type}_{mastery.level_number}"
        
        # Check if exists for tier upgrade tracking
        existing = self.db.execute_query("""
            SELECT mastery_tier FROM level_mastery
            WHERE mastery_id = ?
        """, (mastery_id,))
        
        old_tier = existing[0]['mastery_tier'] if existing else 'novice'
        tier_upgraded = mastery.tier != old_tier and self._tier_rank(mastery.tier) > self._tier_rank(old_tier)
        
        self.db.execute_query("""
            INSERT OR REPLACE INTO level_mastery (
                mastery_id, game_type, level_number,
                unique_sequence_count, diversity_score,
                ablation_tests_total, ablation_tests_passed, 
                ablation_success_rate, ablation_score,
                unique_agents_succeeded, cross_agent_success_rate, consistency_score,
                improvement_count, efficiency_score,
                total_mastery_score, mastery_tier,
                last_updated, last_updated_generation,
                tier_upgraded_at, first_win_at
            ) VALUES (?, ?, ?, ?, ?, 
                      (SELECT ablation_tests_total FROM level_mastery WHERE mastery_id = ?),
                      (SELECT ablation_tests_passed FROM level_mastery WHERE mastery_id = ?),
                      ?, ?,
                      ?, ?, ?,
                      (SELECT improvement_count FROM level_mastery WHERE mastery_id = ?),
                      ?,
                      ?, ?,
                      CURRENT_TIMESTAMP, ?,
                      CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE 
                          (SELECT tier_upgraded_at FROM level_mastery WHERE mastery_id = ?) END,
                      COALESCE(
                          (SELECT first_win_at FROM level_mastery WHERE mastery_id = ?),
                          CURRENT_TIMESTAMP
                      )
                     )
        """, (
            mastery_id, mastery.game_type, mastery.level_number,
            mastery.unique_sequences, mastery.diversity_score,
            mastery_id,  # For ablation_tests_total subquery
            mastery_id,  # For ablation_tests_passed subquery
            mastery.ablation_success_rate, mastery.ablation_score,
            mastery.unique_agents, mastery.cross_agent_success_rate, mastery.consistency_score,
            mastery_id,  # For improvement_count subquery
            mastery.efficiency_score,
            mastery.total_score, mastery.tier,
            generation,
            tier_upgraded, mastery_id,  # For tier_upgraded_at
            mastery_id  # For first_win_at
        ))
    
    def _tier_rank(self, tier: str) -> int:
        """Get numeric rank for tier comparison."""
        ranks = {'novice': 0, 'apprentice': 1, 'practitioner': 2, 'expert': 3, 'master': 4}
        return ranks.get(tier, 0)
    
    def update_all_mastery(self, generation: int) -> int:
        """
        Recalculate mastery for all game-levels.
        
        Called once per generation by autonomous_evolution_runner.
        Also applies MASTERY DECAY for performance degradation.
        
        Args:
            generation: Current generation number
            
        Returns:
            Number of game-levels updated
        """
        # Get all game-levels with sequences
        game_levels = self.db.execute_query("""
            SELECT DISTINCT 
                SUBSTR(game_id, 1, INSTR(game_id, '-') - 1) as game_type,
                level_number
            FROM winning_sequences
            WHERE is_active = 1
              AND game_id LIKE '%-%'
        """)
        
        updated = 0
        decayed = 0
        tier_changes = {'upgrades': 0, 'downgrades': 0}
        
        for gl in game_levels:
            game_type = gl['game_type']
            level_number = gl['level_number']
            
            if not game_type:
                continue
            
            # Get old tier for comparison
            old_result = self.db.execute_query("""
                SELECT mastery_tier FROM level_mastery
                WHERE game_type = ? AND level_number = ?
            """, (game_type, level_number))
            old_tier = old_result[0]['mastery_tier'] if old_result else 'novice'
            
            # Calculate new mastery
            mastery = self.calculate_mastery(game_type, level_number)
            
            # Apply mastery decay if needed
            mastery = self._apply_mastery_decay(mastery, game_type, level_number)
            if mastery._decay_applied:
                decayed += 1
            
            # Store updated mastery
            self._store_mastery(mastery, generation)
            updated += 1
            
            # Track tier changes
            if self._tier_rank(mastery.tier) > self._tier_rank(old_tier):
                tier_changes['upgrades'] += 1
            elif self._tier_rank(mastery.tier) < self._tier_rank(old_tier):
                tier_changes['downgrades'] += 1
        
        logger.info(f"[MASTERY] Updated {updated} game-levels for generation {generation} "
                   f"(decay={decayed}, upgrades={tier_changes['upgrades']}, "
                   f"downgrades={tier_changes['downgrades']})")
        
        return updated
    
    def get_mastery_report(self) -> Dict[str, Any]:
        """
        Generate network-wide mastery report.
        
        Returns:
            Dict with tier distribution, average scores, and totals
        """
        tiers = self.db.execute_query("""
            SELECT 
                mastery_tier, 
                COUNT(*) as count, 
                AVG(total_mastery_score) as avg_score,
                AVG(diversity_score) as avg_diversity,
                AVG(ablation_score) as avg_ablation,
                AVG(consistency_score) as avg_consistency,
                AVG(efficiency_score) as avg_efficiency
            FROM level_mastery
            GROUP BY mastery_tier
            ORDER BY avg_score DESC
        """)
        
        if not tiers:
            return {
                'tier_distribution': {},
                'avg_scores': {},
                'total_levels': 0,
                'breakdown': {}
            }
        
        return {
            'tier_distribution': {t['mastery_tier']: t['count'] for t in tiers},
            'avg_scores': {t['mastery_tier']: t['avg_score'] or 0 for t in tiers},
            'total_levels': sum(t['count'] for t in tiers),
            'breakdown': {
                t['mastery_tier']: {
                    'count': t['count'],
                    'avg_score': t['avg_score'] or 0,
                    'avg_diversity': t['avg_diversity'] or 0,
                    'avg_ablation': t['avg_ablation'] or 0,
                    'avg_consistency': t['avg_consistency'] or 0,
                    'avg_efficiency': t['avg_efficiency'] or 0
                } for t in tiers
            }
        }
    
    def get_essential_actions(self, game_type: str, level_number: int) -> Dict[str, Any]:
        """
        Get essential actions for Apprentice tier study mode.
        
        Analyzes ablation data to determine which action positions are critical.
        
        Args:
            game_type: Game type prefix
            level_number: Level within the game
            
        Returns:
            Dict with essential positions, total actions, and pattern hints
        """
        # Get ablation results for this level
        ablation_results = self.db.execute_query("""
            SELECT skipped_action_indices, test_passed
            FROM ablation_test_results
            WHERE game_type = ? AND level_number = ?
            ORDER BY tested_at DESC
            LIMIT 50
        """, (game_type, level_number))
        
        # Get a representative sequence
        sequence = self.db.execute_query("""
            SELECT action_sequence, total_actions
            FROM winning_sequences
            WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
            ORDER BY total_actions ASC
            LIMIT 1
        """, (f"{game_type}-%", level_number))
        
        if not sequence:
            return {'essential_positions': [], 'total_actions': 0, 'pattern_hint': None}
        
        try:
            action_seq = sequence[0]['action_sequence']
            if isinstance(action_seq, str):
                actions = json.loads(action_seq)
            else:
                actions = action_seq
            total_actions = len(actions)
        except:
            return {'essential_positions': [], 'total_actions': 0, 'pattern_hint': None}
        
        if not ablation_results:
            # No ablation data - conservatively mark clicks as essential
            essential = [i for i, a in enumerate(actions) if a in (6, 7)]
            # Always include first 2 and last 2
            essential.extend([0, 1, max(0, total_actions-2), max(0, total_actions-1)])
            return {
                'essential_positions': sorted(set(essential)),
                'total_actions': total_actions,
                'pattern_hint': 'Click actions likely essential (no ablation data yet)'
            }
        
        # Analyze ablation data to find which positions cause failures when skipped
        position_skip_failures = {}
        
        for result in ablation_results:
            try:
                skipped = json.loads(result['skipped_action_indices'])
                passed = result['test_passed']
                
                for pos in skipped:
                    if pos not in position_skip_failures:
                        position_skip_failures[pos] = {'failed': 0, 'total': 0}
                    position_skip_failures[pos]['total'] += 1
                    if not passed:
                        position_skip_failures[pos]['failed'] += 1
            except:
                continue
        
        # Essential = positions where skipping causes >50% failure rate
        essential = []
        for pos, counts in position_skip_failures.items():
            if counts['total'] >= 3 and counts['failed'] / counts['total'] > 0.5:
                essential.append(pos)
        
        # Always include first 2 and last 2
        essential.extend([0, 1, max(0, total_actions-2), max(0, total_actions-1)])
        
        # Generate pattern hint
        essential_sorted = sorted(set(essential))
        if len(essential_sorted) < total_actions * 0.3:
            pattern_hint = f"Only {len(essential_sorted)}/{total_actions} actions essential - high redundancy"
        else:
            pattern_hint = f"{len(essential_sorted)}/{total_actions} actions essential - low redundancy"
        
        return {
            'essential_positions': essential_sorted,
            'total_actions': total_actions,
            'pattern_hint': pattern_hint
        }
    
    def initialize_migration(self) -> int:
        """
        Initialize mastery system with ALL levels at Novice (hard reset).
        
        Existing sequences are preserved but cannot be replayed until mastery is earned.
        This forces the network to genuinely demonstrate understanding.
        
        Returns:
            Number of game-levels initialized
        """
        # Get all game-levels with existing sequences
        game_levels = self.db.execute_query("""
            SELECT DISTINCT 
                SUBSTR(game_id, 1, INSTR(game_id, '-') - 1) as game_type,
                level_number
            FROM winning_sequences
            WHERE is_active = 1
              AND game_id LIKE '%-%'
        """)
        
        initialized = 0
        for gl in game_levels:
            game_type = gl['game_type']
            level_number = gl['level_number']
            
            if not game_type:
                continue
            
            mastery_id = f"mast_{game_type}_{level_number}"
            
            # Initialize at NOVICE (no replay allowed)
            self.db.execute_query("""
                INSERT OR IGNORE INTO level_mastery (
                    mastery_id, game_type, level_number,
                    total_mastery_score, mastery_tier,
                    first_win_at
                ) VALUES (?, ?, ?, 0.0, 'novice', CURRENT_TIMESTAMP)
            """, (mastery_id, game_type, level_number))
            
            initialized += 1
        
        logger.info(f"[MIGRATION] Initialized {initialized} game-levels at NOVICE tier")
        logger.warning("[MIGRATION] Existing sequences preserved but replay BLOCKED until mastery earned")
        
        return initialized


# Singleton instance for global access
_mastery_system_instance = None


def get_mastery_system(db=None) -> Optional[MasterySystem]:
    """
    Get or create the global MasterySystem instance.
    
    Args:
        db: Optional DatabaseInterface. Required on first call.
        
    Returns:
        MasterySystem instance or None if db not provided on first call
    """
    global _mastery_system_instance
    
    if _mastery_system_instance is None:
        if db is None:
            return None
        _mastery_system_instance = MasterySystem(db)
    
    return _mastery_system_instance


# CLI for testing and manual operations
if __name__ == "__main__":
    import sys
    
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from database_interface import DatabaseInterface
    
    db = DatabaseInterface()
    system = MasterySystem(db)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == '--migrate':
            print("\n=== MASTERY MIGRATION (HARD RESET) ===")
            print("This will initialize ALL game-levels at NOVICE tier.")
            print("Existing sequences preserved but replay BLOCKED until mastery earned.")
            confirm = input("\nType 'YES' to confirm: ")
            if confirm == 'YES':
                count = system.initialize_migration()
                print(f"\n[OK] Migrated {count} game-levels to NOVICE tier")
            else:
                print("[CANCELLED] Migration aborted")
        
        elif command == '--report':
            report = system.get_mastery_report()
            print("\n=== MASTERY REPORT ===")
            print(f"Total levels tracked: {report['total_levels']}")
            print("\nTier Distribution:")
            for tier in ['master', 'expert', 'practitioner', 'apprentice', 'novice']:
                count = report['tier_distribution'].get(tier, 0)
                avg = report['avg_scores'].get(tier, 0)
                breakdown = report['breakdown'].get(tier, {})
                if count > 0:
                    print(f"  {tier.upper()}: {count} levels (avg score: {avg:.1f})")
                    print(f"    diversity={breakdown.get('avg_diversity', 0):.1f}, "
                          f"ablation={breakdown.get('avg_ablation', 0):.1f}, "
                          f"consistency={breakdown.get('avg_consistency', 0):.1f}, "
                          f"efficiency={breakdown.get('avg_efficiency', 0):.1f}")
        
        elif command == '--check' and len(sys.argv) >= 4:
            game_type = sys.argv[2]
            level_number = int(sys.argv[3])
            mastery = system.calculate_mastery(game_type, level_number)
            print(f"\n=== MASTERY: {game_type} L{level_number} ===")
            print(f"Tier: {mastery.tier.upper()}")
            print(f"Total Score: {mastery.total_score:.1f}/100")
            print(f"  Diversity: {mastery.diversity_score:.1f}/30 ({mastery.unique_sequences} unique sequences)")
            print(f"  Ablation: {mastery.ablation_score:.1f}/30 ({mastery.ablation_success_rate or 'N/A'})")
            print(f"  Consistency: {mastery.consistency_score:.1f}/20 ({mastery.unique_agents} agents)")
            print(f"  Efficiency: {mastery.efficiency_score:.1f}/20")
            print(f"Replay Probability: {mastery.replay_probability:.0%}")
        
        else:
            print("Usage:")
            print("  python mastery_system.py --migrate     # Initialize all levels at NOVICE")
            print("  python mastery_system.py --report      # Show mastery report")
            print("  python mastery_system.py --check <game_type> <level>  # Check specific level")
    else:
        # Default: show report
        report = system.get_mastery_report()
        print("\n=== MASTERY REPORT ===")
        print(f"Total levels tracked: {report['total_levels']}")
        print("\nTier Distribution:")
        for tier in ['master', 'expert', 'practitioner', 'apprentice', 'novice']:
            count = report['tier_distribution'].get(tier, 0)
            avg = report['avg_scores'].get(tier, 0)
            if count > 0:
                print(f"  {tier.upper()}: {count} levels (avg score: {avg:.1f})")
