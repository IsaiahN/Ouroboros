#!/usr/bin/env python3
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Resonance Detector - Cross-Role Pattern Resonance Detection

Implements the Resonance Discovery Principle from harmonies theory:
"Truth amplifies itself through cross-domain resonance, not random search."

In our context, "cross-domain" means cross-ROLE:
- When Pioneers (blind exploration), Generalists (network-guided), and 
  Exploiters (micro-optimization) ALL independently converge on the same 
  abstract pattern, that's RESONANCE - evidence of objective truth.

Key Features:
1. Pattern hashing: Abstract fingerprints from inferred beliefs
2. Role diversity scoring: How many different roles found this pattern
3. Resonance amplification: High-resonance patterns get priority
4. Probability gates: Role-specific query frequencies

Theoretical Basis:
- Pioneers have no network bias (frontier isolation)
- Generalists follow network consensus
- Exploiters have 50% sociopathic (ignore network) split
- If all three converge despite radically different biases = objective truth
"""

import sys
import os

# Disable pycache (Rule 1)
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import hashlib
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


# =============================================================================
# RESONANCE QUERY FREQUENCIES BY ROLE
# =============================================================================
# From harmonies theory - role-specific probability gates

RESONANCE_QUERY_THRESHOLDS = {
    # FIX (2025-01-08): Increased pioneer rate from 1% to 15%
    # GAP 3 showed resonance never finding patterns because pioneers were blocked
    'pioneer': 0.15,      # 15% - Frontier exploration needs network patterns
    'optimizer': 0.20,    # 20% - When stuck or seeking inspiration
    'generalist': 0.30,   # 30% - Consistency checks
    'exploiter': 0.10,    # 10% - Occasional sanity checks
}

# Novelty boost for pioneers (when pattern is "interesting")
PIONEER_NOVELTY_BOOST_THRESHOLD = 0.20  # 20% when novelty > 0.7


class ResonanceDetector:
    """
    Detects patterns that resonate across different agent roles.
    
    Resonance = same abstract pattern discovered by >=2 different role types
    independently. This is evidence of objective truth because agents with
    radically different information access and biases converged on the same answer.
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create resonance tracking tables if they don't exist."""
        try:
            # Add pattern_hash column to inferred_beliefs if missing
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS resonance_patterns (
                    pattern_hash TEXT PRIMARY KEY,
                    
                    -- Resonance metrics
                    role_diversity INTEGER DEFAULT 1,
                    roles_found TEXT,  -- JSON list of roles that found this
                    independent_discoverers INTEGER DEFAULT 1,
                    resonance_score REAL DEFAULT 0.0,
                    
                    -- Pattern content (abstract)
                    theory_type TEXT,
                    control_type TEXT,
                    strategy_type TEXT,
                    canonical_beliefs TEXT,  -- JSON of canonicalized beliefs
                    
                    -- Example sequences using this pattern
                    example_sequences TEXT,  -- JSON list of sequence_ids
                    game_types TEXT,  -- JSON list of game types
                    
                    -- Tracking
                    first_detected DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    times_validated INTEGER DEFAULT 0
                )
            """)
            
            # Index for fast resonance lookups
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_resonance_score 
                ON resonance_patterns(resonance_score DESC)
            """)
            
            logger.debug("[RESONANCE] Tables initialized")
            
        except Exception as e:
            logger.debug(f"Resonance table creation (may already exist): {e}")
    
    # =========================================================================
    # PATTERN HASHING - Abstract fingerprints from beliefs
    # =========================================================================
    
    def compute_belief_hash(self, beliefs: Dict[str, Any]) -> str:
        """
        Compute abstract fingerprint from belief structure.
        
        Ignores game-specific details, keeps cognitive structure.
        Two sequences with the same belief hash represent the same
        "way of thinking" even if the raw actions differ.
        
        Args:
            beliefs: Inferred beliefs dict from _extract_inferred_beliefs_from_sequence
            
        Returns:
            16-character hex hash representing abstract pattern
        """
        # Extract and classify theory type
        theory_type = self._classify_theory(beliefs.get('working_theory_required', ''))
        
        # Extract and classify control type
        control_type = self._classify_control(beliefs.get('self_model_required', ''))
        
        # Extract strategy from Q4 inference
        inferences = beliefs.get('inferences', {})
        strategy_type = self._classify_strategy(inferences.get('Q4_strategy', ''))
        
        # Canonical structure (order-independent)
        canonical = {
            'theory': theory_type,
            'control': control_type,
            'strategy': strategy_type
        }
        
        # Hash the canonical structure
        canonical_json = json.dumps(canonical, sort_keys=True)
        return hashlib.md5(canonical_json.encode()).hexdigest()[:16]
    
    def _classify_theory(self, theory: str) -> str:
        """Classify theory into abstract type."""
        if not theory or 'NULL' in theory:
            return 'unknown'
        
        theory_lower = theory.lower()
        
        if 'click' in theory_lower or 'tap' in theory_lower:
            return 'click_puzzle'
        elif 'movement' in theory_lower or 'move' in theory_lower or 'control' in theory_lower:
            return 'movement_puzzle'
        elif 'environment' in theory_lower or 'manipulation' in theory_lower:
            return 'environment_puzzle'
        elif 'pattern' in theory_lower or 'sequence' in theory_lower:
            return 'pattern_puzzle'
        else:
            return 'general'
    
    def _classify_control(self, control: str) -> str:
        """Classify control type into abstract type."""
        if not control or 'NULL' in control:
            return 'unknown'
        
        control_lower = control.lower()
        
        if 'single' in control_lower or 'one' in control_lower:
            return 'single_object'
        elif 'multiple' in control_lower or 'group' in control_lower:
            return 'multi_object'
        elif 'cursor' in control_lower or 'pointer' in control_lower:
            return 'cursor_control'
        else:
            return 'general'
    
    def _classify_strategy(self, strategy: str) -> str:
        """Classify strategy into abstract type."""
        if not strategy or 'NULL' in strategy:
            return 'unknown'
        
        strategy_lower = strategy.lower()
        
        if 'single action' in strategy_lower:
            return 'specialized'
        elif 'limited' in strategy_lower or 'focused' in strategy_lower:
            return 'focused'
        elif 'diverse' in strategy_lower or 'adaptive' in strategy_lower:
            return 'adaptive'
        else:
            return 'general'
    
    # =========================================================================
    # RESONANCE DETECTION - Find patterns with cross-role agreement
    # =========================================================================
    
    def detect_resonance(self, generation: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Detect resonant patterns: same abstract beliefs, different roles.
        
        This is the core resonance detection algorithm. It finds patterns
        where agents with different roles (and thus different biases)
        independently converged on the same solution.
        
        Args:
            generation: Optional generation filter for recent patterns
            
        Returns:
            List of resonant patterns with scores
        """
        try:
            # Query to find patterns with role diversity
            # Joins inferred_beliefs with winning_sequences and agents
            query = """
                SELECT 
                    ib.working_theory_required,
                    ib.self_model_required,
                    ib.inferences,
                    COUNT(DISTINCT a.preferred_role) as role_diversity,
                    COUNT(DISTINCT ws.discovered_by) as independent_discoverers,
                    GROUP_CONCAT(DISTINCT a.preferred_role) as roles_found,
                    GROUP_CONCAT(DISTINCT SUBSTR(ws.game_id, 1, 4)) as game_types,
                    GROUP_CONCAT(DISTINCT ib.sequence_id) as sequence_ids
                FROM inferred_beliefs ib
                JOIN winning_sequences ws ON ib.sequence_id = ws.sequence_id
                JOIN agents a ON ws.discovered_by = a.agent_id
                WHERE ib.working_theory_required NOT LIKE 'NULL%'
                  AND ib.working_theory_required != ''
                GROUP BY ib.working_theory_required, ib.self_model_required
                HAVING role_diversity >= 2
                ORDER BY role_diversity DESC, independent_discoverers DESC
                LIMIT 50
            """
            
            results = self.db.execute_query(query)
            
            resonant_patterns = []
            for row in results:
                # Compute resonance score
                role_diversity = row['role_diversity']
                discoverers = row['independent_discoverers']
                
                # Resonance formula: role_diversity * log(discoverers + 1)
                import math
                resonance_score = role_diversity * math.log(discoverers + 1)
                
                # Build beliefs dict for hashing
                beliefs = {
                    'working_theory_required': row['working_theory_required'],
                    'self_model_required': row['self_model_required'],
                    'inferences': json.loads(row['inferences']) if row['inferences'] else {}
                }
                
                pattern_hash = self.compute_belief_hash(beliefs)
                
                pattern = {
                    'pattern_hash': pattern_hash,
                    'resonance_score': resonance_score,
                    'role_diversity': role_diversity,
                    'independent_discoverers': discoverers,
                    'roles_found': row['roles_found'].split(',') if row['roles_found'] else [],
                    'game_types': row['game_types'].split(',') if row['game_types'] else [],
                    'sequence_ids': row['sequence_ids'].split(',')[:5] if row['sequence_ids'] else [],
                    'theory_type': self._classify_theory(row['working_theory_required']),
                    'control_type': self._classify_control(row['self_model_required'])
                }
                
                resonant_patterns.append(pattern)
                
                # Store/update in resonance_patterns table
                self._store_resonance_pattern(pattern, beliefs)
            
            logger.info(f"[RESONANCE] Detected {len(resonant_patterns)} resonant patterns")
            return resonant_patterns
            
        except Exception as e:
            logger.error(f"Resonance detection failed: {e}")
            return []
    
    def _store_resonance_pattern(self, pattern: Dict[str, Any], beliefs: Dict[str, Any]):
        """Store or update a resonance pattern in the database."""
        try:
            pattern_hash = pattern['pattern_hash']
            
            existing = self.db.execute_query("""
                SELECT pattern_hash, times_validated FROM resonance_patterns
                WHERE pattern_hash = ?
            """, (pattern_hash,))
            
            if existing:
                # Update existing
                self.db.execute_query("""
                    UPDATE resonance_patterns SET
                        role_diversity = ?,
                        roles_found = ?,
                        independent_discoverers = ?,
                        resonance_score = ?,
                        example_sequences = ?,
                        game_types = ?,
                        times_validated = times_validated + 1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE pattern_hash = ?
                """, (
                    pattern['role_diversity'],
                    json.dumps(pattern['roles_found']),
                    pattern['independent_discoverers'],
                    pattern['resonance_score'],
                    json.dumps(pattern['sequence_ids']),
                    json.dumps(pattern['game_types']),
                    pattern_hash
                ))
            else:
                # Insert new
                self.db.execute_query("""
                    INSERT INTO resonance_patterns
                    (pattern_hash, role_diversity, roles_found, independent_discoverers,
                     resonance_score, theory_type, control_type, strategy_type,
                     canonical_beliefs, example_sequences, game_types)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern_hash,
                    pattern['role_diversity'],
                    json.dumps(pattern['roles_found']),
                    pattern['independent_discoverers'],
                    pattern['resonance_score'],
                    pattern['theory_type'],
                    pattern['control_type'],
                    pattern.get('strategy_type', 'general'),
                    json.dumps(beliefs),
                    json.dumps(pattern['sequence_ids']),
                    json.dumps(pattern['game_types'])
                ))
                
        except Exception as e:
            logger.debug(f"Storing resonance pattern failed: {e}")
    
    # =========================================================================
    # RESONANCE QUERIES - Role-specific pattern lookups
    # =========================================================================
    
    def get_resonant_patterns(
        self,
        min_score: float = 1.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get high-resonance patterns for network-wide prioritization.
        
        Args:
            min_score: Minimum resonance score threshold
            limit: Maximum patterns to return
            
        Returns:
            List of resonant patterns ordered by score
        """
        try:
            results = self.db.execute_query("""
                SELECT pattern_hash, resonance_score, role_diversity,
                       roles_found, theory_type, control_type, game_types
                FROM resonance_patterns
                WHERE resonance_score >= ?
                ORDER BY resonance_score DESC
                LIMIT ?
            """, (min_score, limit))
            
            patterns = []
            for row in results:
                patterns.append({
                    'pattern_hash': row['pattern_hash'],
                    'resonance_score': row['resonance_score'],
                    'role_diversity': row['role_diversity'],
                    'roles_found': json.loads(row['roles_found']) if row['roles_found'] else [],
                    'theory_type': row['theory_type'],
                    'control_type': row['control_type'],
                    'game_types': json.loads(row['game_types']) if row['game_types'] else []
                })
            
            return patterns
            
        except Exception as e:
            logger.debug(f"Getting resonant patterns failed: {e}")
            return []
    
    def get_pattern_resonance(self, beliefs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get resonance information for a specific belief pattern.
        
        Use this to check if the current pattern has been validated
        by multiple roles (i.e., is likely objective truth).
        
        Args:
            beliefs: Inferred beliefs dict
            
        Returns:
            Resonance info if pattern exists, None otherwise
        """
        try:
            pattern_hash = self.compute_belief_hash(beliefs)
            
            results = self.db.execute_query("""
                SELECT resonance_score, role_diversity, roles_found,
                       independent_discoverers, theory_type
                FROM resonance_patterns
                WHERE pattern_hash = ?
            """, (pattern_hash,))
            
            if results:
                row = results[0]
                return {
                    'pattern_hash': pattern_hash,
                    'resonance_score': row['resonance_score'],
                    'role_diversity': row['role_diversity'],
                    'roles_found': json.loads(row['roles_found']) if row['roles_found'] else [],
                    'independent_discoverers': row['independent_discoverers'],
                    'is_resonant': row['role_diversity'] >= 2
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Pattern resonance lookup failed: {e}")
            return None
    
    # =========================================================================
    # PROBABILITY GATES - Role-specific query frequencies
    # =========================================================================
    
    def should_query_resonance(
        self,
        agent_role: str,
        pattern_novelty: float = 0.0,
        is_stuck: bool = False
    ) -> bool:
        """
        Determine if agent should query for cross-role resonance this action.
        
        Implements role-specific frequency gates from harmonies theory:
        - Pioneer: 1% base, boosted to 20% on high-novelty patterns
        - Optimizer: 10% base, boosted when stuck
        - Generalist: 30% (consistency checks)
        - Exploiter: 5% (occasional sanity checks)
        
        Args:
            agent_role: Role of the agent (pioneer, optimizer, generalist, exploiter)
            pattern_novelty: 0.0-1.0 novelty score of current pattern
            is_stuck: Whether agent is currently stuck
            
        Returns:
            True if agent should query resonance this action
        """
        base_threshold = RESONANCE_QUERY_THRESHOLDS.get(agent_role.lower(), 0.10)
        
        # Pioneer boost on high-novelty patterns
        if agent_role.lower() == 'pioneer' and pattern_novelty > 0.7:
            base_threshold = PIONEER_NOVELTY_BOOST_THRESHOLD
            logger.debug(f"[RESONANCE] Pioneer novelty boost: {base_threshold}")
        
        # Optimizer boost when stuck
        if agent_role.lower() == 'optimizer' and is_stuck:
            base_threshold = min(0.30, base_threshold * 2.0)
            logger.debug(f"[RESONANCE] Optimizer stuck boost: {base_threshold}")
        
        should_query = random.random() < base_threshold
        
        if should_query:
            logger.debug(f"[RESONANCE] {agent_role} triggered resonance query (threshold: {base_threshold})")
        
        return should_query
    
    # =========================================================================
    # RESONANCE SCORING - Calculate pattern resonance
    # =========================================================================
    
    def calculate_resonance_score(
        self,
        role_diversity: int,
        independent_discoverers: int,
        game_type_diversity: int = 1
    ) -> float:
        """
        Calculate resonance score for a pattern.
        
        Formula: role_diversity * log(discoverers + 1) * (1 + game_diversity * 0.1)
        
        Higher scores indicate:
        - More role types agree (strongest signal)
        - More independent agents found it
        - Pattern works across more game types
        
        Args:
            role_diversity: Number of different roles that found pattern
            independent_discoverers: Number of independent agents
            game_type_diversity: Number of different game types
            
        Returns:
            Resonance score (0.0 = no resonance, higher = stronger)
        """
        import math
        
        if role_diversity < 2:
            return 0.0  # No resonance with single role
        
        base_score = role_diversity * math.log(independent_discoverers + 1)
        game_bonus = 1.0 + (game_type_diversity - 1) * 0.1
        
        return base_score * game_bonus
    
    # =========================================================================
    # NETWORK INTEGRATION - For regulatory engine
    # =========================================================================
    
    def get_resonance_summary(self) -> Dict[str, Any]:
        """
        Get summary of resonance state for regulatory engine.
        
        Returns:
            Summary dict with resonance health metrics
        """
        try:
            # Count total resonant patterns
            total = self.db.execute_query("""
                SELECT COUNT(*) as count, AVG(resonance_score) as avg_score,
                       MAX(resonance_score) as max_score
                FROM resonance_patterns
                WHERE role_diversity >= 2
            """)
            
            # Get role coverage
            role_coverage = self.db.execute_query("""
                SELECT roles_found, COUNT(*) as pattern_count
                FROM resonance_patterns
                WHERE role_diversity >= 2
                GROUP BY roles_found
                ORDER BY pattern_count DESC
                LIMIT 5
            """)
            
            if total and total[0]:
                return {
                    'total_resonant_patterns': total[0]['count'] or 0,
                    'average_resonance_score': total[0]['avg_score'] or 0.0,
                    'max_resonance_score': total[0]['max_score'] or 0.0,
                    'top_role_combinations': [
                        {'roles': r['roles_found'], 'count': r['pattern_count']}
                        for r in role_coverage
                    ] if role_coverage else []
                }
            
            return {
                'total_resonant_patterns': 0,
                'average_resonance_score': 0.0,
                'max_resonance_score': 0.0,
                'top_role_combinations': []
            }
            
        except Exception as e:
            logger.debug(f"Resonance summary failed: {e}")
            return {'error': str(e)}


# =============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# =============================================================================

def should_query_resonance(agent_role: str, pattern_novelty: float = 0.0, is_stuck: bool = False) -> bool:
    """
    Module-level convenience function for role-based resonance query gate.
    
    Can be imported directly without instantiating ResonanceDetector.
    """
    # FIX (2025-01-08): Always query resonance when stuck (GAP 3)
    # Stuck agents desperately need network wisdom - don't block them
    if is_stuck:
        return True
    
    base_threshold = RESONANCE_QUERY_THRESHOLDS.get(agent_role.lower(), 0.10)
    
    if agent_role.lower() == 'pioneer' and pattern_novelty > 0.7:
        base_threshold = PIONEER_NOVELTY_BOOST_THRESHOLD
    
    if agent_role.lower() == 'optimizer':
        # Optimizers should query more often to find proven patterns
        base_threshold = min(0.40, base_threshold * 2.0)
    
    return random.random() < base_threshold
