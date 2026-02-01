"""
Trigger Sequences - Interaction Trigger Chain Recording
=======================================================

Records and manages multi-step interaction sequences:
- Trigger chains (X causes Y which causes Z)
- Proven action sequences for levels
- Conditional triggers (button activates door)

Design Principles:
- Explicit state tracking with clear transitions
- Full audit trail for sequence construction
- No silent failures - validation at each step
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of triggers."""
    CLICK = "click"           # Clicking object
    COLLISION = "collision"   # Colliding with object
    PROXIMITY = "proximity"   # Getting near object
    TIMER = "timer"          # Time-based trigger
    SEQUENCE = "sequence"     # Completing a sequence
    UNKNOWN = "unknown"


class TriggerEffect(Enum):
    """Effects that triggers can have."""
    TOGGLE = "toggle"            # Object toggles state
    DISAPPEAR = "disappear"      # Object disappears
    APPEAR = "appear"            # Object appears
    MOVE = "move"                # Object moves
    COLOR_CHANGE = "color_change" # Object changes color
    SCORE_CHANGE = "score_change" # Score changes
    LEVEL_END = "level_end"      # Level ends
    UNLOCK = "unlock"            # Something unlocks
    SPAWN = "spawn"              # New object spawns
    UNKNOWN = "unknown"


@dataclass
class TriggerStep:
    """A single step in a trigger chain."""
    step_number: int
    action: str              # ACTION1-7 or coordinate click
    target_object: Optional[str]  # Object targeted/affected
    trigger_type: TriggerType
    effect: TriggerEffect
    effect_target: Optional[str]  # What was affected
    frame_before_hash: str   # For verification
    frame_after_hash: str
    score_delta: float = 0.0
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_number': self.step_number,
            'action': self.action,
            'target_object': self.target_object,
            'trigger_type': self.trigger_type.value,
            'effect': self.effect.value,
            'effect_target': self.effect_target,
            'score_delta': self.score_delta,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerStep':
        return cls(
            step_number=data['step_number'],
            action=data['action'],
            target_object=data.get('target_object'),
            trigger_type=TriggerType(data.get('trigger_type', 'unknown')),
            effect=TriggerEffect(data.get('effect', 'unknown')),
            effect_target=data.get('effect_target'),
            frame_before_hash=data.get('frame_before_hash', ''),
            frame_after_hash=data.get('frame_after_hash', ''),
            score_delta=data.get('score_delta', 0.0),
            timestamp=data.get('timestamp', '')
        )


@dataclass 
class TriggerChain:
    """A chain of related triggers."""
    chain_id: str
    game_type: str
    level: int
    steps: List[TriggerStep] = field(default_factory=list)
    is_complete: bool = False
    leads_to_win: bool = False
    total_score: float = 0.0
    created_at: str = ""
    
    @property
    def step_count(self) -> int:
        return len(self.steps)
    
    @property
    def action_sequence(self) -> List[str]:
        return [step.action for step in self.steps]
    
    def add_step(self, step: TriggerStep) -> None:
        step.step_number = len(self.steps) + 1
        self.steps.append(step)
        self.total_score += step.score_delta
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chain_id': self.chain_id,
            'game_type': self.game_type,
            'level': self.level,
            'steps': [s.to_dict() for s in self.steps],
            'is_complete': self.is_complete,
            'leads_to_win': self.leads_to_win,
            'total_score': self.total_score,
            'created_at': self.created_at
        }


@dataclass
class ProvenSequence:
    """A proven action sequence that works."""
    sequence_id: str
    game_type: str
    level: int
    actions: List[str]
    coordinates: List[Tuple[int, int]]  # (y, x) for click actions
    success_count: int = 0
    failure_count: int = 0
    best_score: float = 0.0
    avg_score: float = 0.0
    is_optimal: bool = False
    created_at: str = ""
    
    @property
    def reliability(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    @property
    def action_count(self) -> int:
        return len(self.actions)


class TriggerSequenceTracker:
    """
    Tracks trigger chains and proven sequences.
    
    Usage:
        tracker = TriggerSequenceTracker(db_path)
        
        # Start recording a potential trigger chain
        chain_id = tracker.start_chain("sp80", level=1)
        
        # Record each step
        tracker.record_step(
            chain_id,
            action="ACTION7",
            target_object="color_3",
            frame_before=[[...]],
            frame_after=[[...]],
            score_delta=10.0
        )
        
        # Finalize successful chain
        tracker.finalize_chain(chain_id, success=True, is_win=True)
        
        # Get proven sequences for a level
        sequences = tracker.get_proven_sequences("sp80", level=1)
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        """
        Initialize trigger sequence tracker.
        
        Args:
            db_path: Path to database
        """
        try:
            from database_interface import DatabaseInterface
            self.db = DatabaseInterface(db_path)
        except Exception as e:
            raise RuntimeError(f"[TRIGGER] Failed to connect to database: {e}")
        
        self._active_chains: Dict[str, TriggerChain] = {}
        self._ensure_tables()
        logger.info("[TRIGGER] Initialized")
    
    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS trigger_chains (
                    chain_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    steps_json TEXT,
                    is_complete INTEGER DEFAULT 0,
                    leads_to_win INTEGER DEFAULT 0,
                    total_score REAL DEFAULT 0.0,
                    step_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS proven_sequences (
                    sequence_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    actions_json TEXT NOT NULL,
                    coordinates_json TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    best_score REAL DEFAULT 0.0,
                    avg_score REAL DEFAULT 0.0,
                    is_optimal INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_trigger_chains_game 
                ON trigger_chains(game_type, level)
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_proven_sequences_game
                ON proven_sequences(game_type, level)
            """)
            
            logger.debug("[TRIGGER] Tables verified")
        except Exception as e:
            logger.error(f"[TRIGGER] Table creation failed: {e}")
            raise
    
    def start_chain(
        self,
        game_type: str,
        level: int,
        chain_id: Optional[str] = None
    ) -> str:
        """
        Start recording a new trigger chain.
        
        Args:
            game_type: Game type identifier
            level: Level number
            chain_id: Optional explicit chain ID
            
        Returns:
            Chain ID for this recording session
        """
        if not chain_id:
            chain_id = f"chain_{game_type}_{level}_{datetime.now().strftime('%H%M%S%f')}"
        
        chain = TriggerChain(
            chain_id=chain_id,
            game_type=game_type,
            level=level,
            created_at=datetime.now().isoformat()
        )
        
        self._active_chains[chain_id] = chain
        logger.info(f"[TRIGGER] Started chain {chain_id}")
        
        return chain_id
    
    def record_step(
        self,
        chain_id: str,
        action: str,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        target_object: Optional[str] = None,
        score_delta: float = 0.0
    ) -> Optional[TriggerStep]:
        """
        Record a step in an active chain.
        
        Args:
            chain_id: ID of active chain
            action: Action taken (ACTION1-7 or "CLICK_X_Y")
            frame_before: Frame before action
            frame_after: Frame after action
            target_object: Object targeted (if known)
            score_delta: Change in score
            
        Returns:
            The recorded TriggerStep or None if chain not found
        """
        if chain_id not in self._active_chains:
            logger.warning(f"[TRIGGER] Chain {chain_id} not found")
            return None
        
        chain = self._active_chains[chain_id]
        
        # Analyze frame changes to determine effect
        trigger_type = self._detect_trigger_type(action)
        effect, effect_target = self._detect_effect(
            frame_before, frame_after, target_object, score_delta
        )
        
        step = TriggerStep(
            step_number=chain.step_count + 1,
            action=action,
            target_object=target_object,
            trigger_type=trigger_type,
            effect=effect,
            effect_target=effect_target,
            frame_before_hash=self._hash_frame(frame_before),
            frame_after_hash=self._hash_frame(frame_after),
            score_delta=score_delta,
            timestamp=datetime.now().isoformat()
        )
        
        chain.add_step(step)
        
        logger.debug(
            f"[TRIGGER] Chain {chain_id} step {step.step_number}: "
            f"{action} -> {effect.value} on {effect_target}"
        )
        
        return step
    
    def finalize_chain(
        self,
        chain_id: str,
        success: bool = True,
        is_win: bool = False
    ) -> Optional[TriggerChain]:
        """
        Finalize a trigger chain and optionally save as proven sequence.
        
        Args:
            chain_id: ID of chain to finalize
            success: Whether the chain was successful
            is_win: Whether chain led to level/game win
            
        Returns:
            Finalized chain or None if not found
        """
        if chain_id not in self._active_chains:
            logger.warning(f"[TRIGGER] Cannot finalize - chain {chain_id} not found")
            return None
        
        chain = self._active_chains.pop(chain_id)
        chain.is_complete = True
        chain.leads_to_win = is_win
        
        # Save chain to database
        try:
            self.db.execute_query("""
                INSERT INTO trigger_chains
                (chain_id, game_type, level, steps_json, is_complete, 
                 leads_to_win, total_score, step_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chain.chain_id,
                chain.game_type,
                chain.level,
                json.dumps([s.to_dict() for s in chain.steps]),
                1 if chain.is_complete else 0,
                1 if chain.leads_to_win else 0,
                chain.total_score,
                chain.step_count,
                chain.created_at
            ))
        except Exception as e:
            logger.error(f"[TRIGGER] Failed to save chain {chain_id}: {e}")
        
        # If successful, create/update proven sequence
        if success and chain.step_count > 0:
            self._update_proven_sequence(chain)
        
        logger.info(
            f"[TRIGGER] Finalized chain {chain_id}: "
            f"{chain.step_count} steps, success={success}, win={is_win}"
        )
        
        return chain
    
    def abandon_chain(self, chain_id: str) -> None:
        """
        Abandon an active chain without saving.
        
        Args:
            chain_id: Chain to abandon
        """
        if chain_id in self._active_chains:
            del self._active_chains[chain_id]
            logger.debug(f"[TRIGGER] Abandoned chain {chain_id}")
    
    def get_proven_sequences(
        self,
        game_type: str,
        level: int,
        min_reliability: float = 0.5,
        limit: int = 10
    ) -> List[ProvenSequence]:
        """
        Get proven sequences for a game/level.
        
        Args:
            game_type: Game type identifier
            level: Level number
            min_reliability: Minimum reliability threshold
            limit: Maximum sequences to return
            
        Returns:
            List of ProvenSequence ordered by reliability/score
        """
        try:
            rows = self.db.execute_query("""
                SELECT * FROM proven_sequences
                WHERE game_type = ? AND level = ?
                AND (success_count + failure_count) > 0
                AND CAST(success_count AS REAL) / (success_count + failure_count) >= ?
                ORDER BY 
                    is_optimal DESC,
                    best_score DESC,
                    CAST(success_count AS REAL) / (success_count + failure_count) DESC
                LIMIT ?
            """, (game_type, level, min_reliability, limit))
            
            sequences = []
            for row in rows:
                try:
                    actions = json.loads(row['actions_json']) if row['actions_json'] else []
                    coords_raw = json.loads(row['coordinates_json']) if row['coordinates_json'] else []
                    coordinates = [tuple(c) if c else (0, 0) for c in coords_raw]
                    
                    sequences.append(ProvenSequence(
                        sequence_id=row['sequence_id'],
                        game_type=row['game_type'],
                        level=row['level'],
                        actions=actions,
                        coordinates=coordinates,
                        success_count=row['success_count'],
                        failure_count=row['failure_count'],
                        best_score=row['best_score'],
                        avg_score=row['avg_score'],
                        is_optimal=bool(row['is_optimal']),
                        created_at=row.get('created_at', '')
                    ))
                except Exception as e:
                    logger.warning(f"[TRIGGER] Failed to parse sequence {row['sequence_id']}: {e}")
            
            logger.debug(f"[TRIGGER] Found {len(sequences)} proven sequences for {game_type} L{level}")
            return sequences
            
        except Exception as e:
            logger.error(f"[TRIGGER] Failed to get proven sequences: {e}")
            return []
    
    def update_sequence_result(
        self,
        sequence_id: str,
        success: bool,
        score: float
    ) -> None:
        """
        Update a proven sequence with execution result.
        
        Args:
            sequence_id: Sequence that was executed
            success: Whether it succeeded
            score: Score achieved
        """
        try:
            if success:
                self.db.execute_query("""
                    UPDATE proven_sequences
                    SET success_count = success_count + 1,
                        best_score = MAX(best_score, ?),
                        avg_score = (avg_score * success_count + ?) / (success_count + 1)
                    WHERE sequence_id = ?
                """, (score, score, sequence_id))
            else:
                self.db.execute_query("""
                    UPDATE proven_sequences
                    SET failure_count = failure_count + 1
                    WHERE sequence_id = ?
                """, (sequence_id,))
                
            logger.debug(f"[TRIGGER] Updated sequence {sequence_id}: success={success}, score={score}")
            
        except Exception as e:
            logger.error(f"[TRIGGER] Failed to update sequence result: {e}")
    
    def get_trigger_patterns(
        self,
        game_type: str,
        trigger_type: Optional[TriggerType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get common trigger patterns for a game type.
        
        Args:
            game_type: Game type to query
            trigger_type: Optional filter by trigger type
            
        Returns:
            List of trigger pattern summaries
        """
        try:
            rows = self.db.execute_query("""
                SELECT steps_json, leads_to_win, total_score
                FROM trigger_chains
                WHERE game_type = ? AND is_complete = 1
                ORDER BY leads_to_win DESC, total_score DESC
                LIMIT 50
            """, (game_type,))
            
            # Analyze patterns
            patterns: Dict[str, Dict[str, Any]] = {}
            
            for row in rows:
                steps = json.loads(row['steps_json']) if row['steps_json'] else []
                for step in steps:
                    step_type = step.get('trigger_type', 'unknown')
                    effect = step.get('effect', 'unknown')
                    
                    if trigger_type and step_type != trigger_type.value:
                        continue
                    
                    pattern_key = f"{step_type}->{effect}"
                    if pattern_key not in patterns:
                        patterns[pattern_key] = {
                            'trigger_type': step_type,
                            'effect': effect,
                            'count': 0,
                            'win_rate': 0.0,
                            'examples': []
                        }
                    
                    patterns[pattern_key]['count'] += 1
                    if row['leads_to_win']:
                        patterns[pattern_key]['win_rate'] += 1
            
            # Calculate win rates
            for pattern in patterns.values():
                if pattern['count'] > 0:
                    pattern['win_rate'] /= pattern['count']
            
            return sorted(patterns.values(), key=lambda p: p['count'], reverse=True)
            
        except Exception as e:
            logger.error(f"[TRIGGER] Failed to get trigger patterns: {e}")
            return []
    
    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    
    def _detect_trigger_type(self, action: str) -> TriggerType:
        """Detect trigger type from action."""
        if action == "ACTION7" or action.startswith("CLICK"):
            return TriggerType.CLICK
        elif action in ["ACTION1", "ACTION2", "ACTION3", "ACTION4"]:
            return TriggerType.COLLISION  # Movement can cause collision
        elif action == "ACTION5":
            return TriggerType.SEQUENCE  # Action5 often confirms sequences
        elif action == "ACTION6":
            return TriggerType.CLICK  # Selection is a form of clicking
        return TriggerType.UNKNOWN
    
    def _detect_effect(
        self,
        frame_before: List[List[int]],
        frame_after: List[List[int]],
        target: Optional[str],
        score_delta: float
    ) -> Tuple[TriggerEffect, Optional[str]]:
        """Detect what effect occurred."""
        # Score change is clear effect
        if score_delta != 0:
            return (TriggerEffect.SCORE_CHANGE, None)
        
        # Check for frame changes
        if frame_before == frame_after:
            return (TriggerEffect.UNKNOWN, None)
        
        # Find what changed
        objects_before = self._count_objects(frame_before)
        objects_after = self._count_objects(frame_after)
        
        # Check for appearance/disappearance
        for color, count in objects_after.items():
            if color not in objects_before:
                return (TriggerEffect.APPEAR, f"color_{color}")
        
        for color, count in objects_before.items():
            if color not in objects_after:
                return (TriggerEffect.DISAPPEAR, f"color_{color}")
        
        # Check for toggle (same positions, different colors)
        if target:
            target_color = int(target.replace('color_', '')) if 'color_' in target else 0
            old_count = objects_before.get(target_color, 0)
            new_count = objects_after.get(target_color, 0)
            if old_count != new_count:
                return (TriggerEffect.TOGGLE, target)
        
        # Check for movement
        for color in objects_before:
            if color in objects_after:
                if objects_before[color] != objects_after[color]:
                    return (TriggerEffect.MOVE, f"color_{color}")
        
        return (TriggerEffect.UNKNOWN, None)
    
    def _count_objects(self, frame: List[List[int]]) -> Dict[int, int]:
        """Count objects by color in frame."""
        counts: Dict[int, int] = {}
        for row in frame:
            for color in row:
                if color > 0:
                    counts[color] = counts.get(color, 0) + 1
        return counts
    
    def _hash_frame(self, frame: List[List[int]]) -> str:
        """Create a hash of frame for verification."""
        return str(hash(str(frame)))[:16]
    
    def _update_proven_sequence(self, chain: TriggerChain) -> None:
        """Create or update proven sequence from chain."""
        actions = chain.action_sequence
        if not actions:
            return
        
        sequence_id = f"seq_{chain.game_type}_{chain.level}_{len(actions)}"
        
        # Extract coordinates for click actions
        coordinates = []
        for step in chain.steps:
            if step.action == "ACTION7" and step.target_object:
                # Would need actual coordinates, use (0,0) as placeholder
                coordinates.append((0, 0))
            else:
                coordinates.append((0, 0))
        
        try:
            self.db.execute_query("""
                INSERT INTO proven_sequences
                (sequence_id, game_type, level, actions_json, coordinates_json,
                 success_count, best_score, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(sequence_id) DO UPDATE SET
                    success_count = success_count + 1,
                    best_score = MAX(best_score, excluded.best_score)
            """, (
                sequence_id,
                chain.game_type,
                chain.level,
                json.dumps(actions),
                json.dumps(coordinates),
                chain.total_score,
                chain.created_at
            ))
            
            logger.debug(f"[TRIGGER] Updated proven sequence {sequence_id}")
            
        except Exception as e:
            logger.error(f"[TRIGGER] Failed to update proven sequence: {e}")
