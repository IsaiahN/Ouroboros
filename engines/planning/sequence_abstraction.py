#!/usr/bin/env python3
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Sequence Abstraction - Enhanced Template Replay System
=======================================================

ENHANCED: Now provides executable abstract templates, not just hints!

Key capabilities:
1. Abstract Template Generation - Create reusable action templates from multiple sequences
2. Template Replay - Execute templates with coordinate adaptation
3. Frontier Navigation - Skip solved levels using abstracted solutions
4. Invariant Detection - Find what MUST happen vs what CAN vary

The insight: Multiple winning sequences for the same level reveal:
- INVARIANTS = Actions that appear in ALL sequences (required)
- VARIANTS = Actions that differ between sequences (adaptable)
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from database_interface import DatabaseInterface
from engines.engine_logger import get_engine_logger

logger = get_engine_logger("sequence_abstraction")


def _notify_concept_discovery(pattern: str, game_type: str, confidence: float, source: str = "abstraction") -> None:
    """
    Notify ConceptDiscoveryEngine when abstraction discovers a pattern.
    
    This closes the Abstraction -> Concepts gap in the cognitive cycle.
    When sequence invariants are discovered, they become concept candidates.
    """
    try:
        from concept_discovery_engine import ConceptDiscoveryEngine
        db = DatabaseInterface()
        concept_engine = ConceptDiscoveryEngine(db)
        
        # Track this as a successful pattern that might become a concept
        concept_engine.track_successful_operator_pattern(
            operator_id=f"abstraction_{source}",
            game_id=game_type,
            sub_patterns=[pattern]
        )
        
        logger.debug(f"[ABSTRACTION->CONCEPT] Notified concept engine of pattern: {pattern[:50]}")
    except Exception as e:
        # Non-critical - concept discovery is enhancement
        logger.debug(f"[ABSTRACTION->CONCEPT] Notification failed: {e}")


class RelationalPatternCache:
    """Lightweight cache for pattern → outcome pairs harvested from telemetry."""

    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_table()

    def _ensure_table(self) -> None:
        try:
            self.db.execute_query(
                """
                CREATE TABLE IF NOT EXISTS relational_patterns (
                    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_signature TEXT NOT NULL,
                    pattern_json TEXT,
                    context_tags TEXT,
                    outcome REAL,
                    support INTEGER DEFAULT 1,
                    reliability REAL DEFAULT 0.5,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.db.execute_query(
                """
                CREATE INDEX IF NOT EXISTS idx_relational_patterns_signature
                ON relational_patterns(pattern_signature)
                """
            )
        except Exception as exc:
            logger.debug(f"[RELATIONS] table ensure failed: {exc}")

    def upsert_pattern(self, signature: str, pattern_json: str, context: str, outcome: float) -> None:
        try:
            existing = self.db.execute_query(
                """
                SELECT pattern_id, support, reliability
                FROM relational_patterns
                WHERE pattern_signature = ?
                """,
                (signature,),
            )
            if existing:
                row = existing[0]
                new_support = row['support'] + 1
                # Increment reliability mildly toward outcome quality (bounded)
                new_reliability = min(1.0, row['reliability'] + 0.05)
                self.db.execute_query(
                    """
                    UPDATE relational_patterns
                    SET pattern_json = ?, context_tags = ?, outcome = ?,
                        support = ?, reliability = ?, last_seen = CURRENT_TIMESTAMP
                    WHERE pattern_id = ?
                    """,
                    (pattern_json, context, outcome, new_support, new_reliability, row['pattern_id']),
                )
            else:
                self.db.execute_query(
                    """
                    INSERT INTO relational_patterns
                    (pattern_signature, pattern_json, context_tags, outcome, support, reliability)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (signature, pattern_json, context, outcome, 1, 0.55),
                )
        except Exception as exc:
            logger.debug(f"[RELATIONS] upsert failed: {exc}")

    def query_by_context(self, context_like: str, min_support: int = 2, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            rows = self.db.execute_query(
                """
                SELECT pattern_json, context_tags, outcome, support, reliability
                FROM relational_patterns
                WHERE context_tags LIKE ? AND support >= ?
                ORDER BY reliability DESC, support DESC, last_seen DESC
                LIMIT ?
                """,
                (f"%{context_like}%", min_support, limit),
            )
            return rows or []
        except Exception as exc:
            logger.debug(f"[RELATIONS] query failed: {exc}")
            return []


@dataclass
class AbstractTemplate:
    """An executable abstract template derived from multiple winning sequences."""
    game_type: str
    level_number: int
    invariant_actions: List[Dict[str, Any]]  # Actions that MUST happen
    variant_regions: List[Dict[str, Any]]    # Regions where adaptation is allowed
    template_sequence: List[Dict[str, Any]]  # Full template with coordinates
    confidence: float                         # 0.0-1.0 based on sample size
    sample_size: int                          # Number of sequences used
    avg_length: float                         # Average sequence length
    persona_id: Optional[str] = None          # Provenance: which persona produced/used this template
    world_model: Optional[str] = None         # Provenance: world model tag from persona runtime
    problem_signature: Optional[str] = None   # Provenance: problem signature used for selection
    
    def to_executable(self) -> List[Dict[str, Any]]:
        """Convert to executable action sequence."""
        return self.template_sequence
    
    def __repr__(self) -> str:
        return f"AbstractTemplate({self.game_type}@L{self.level_number}, {len(self.invariant_actions)} invariants, conf={self.confidence:.0%})"


class SequenceAbstraction:
    """Simple concept matching for sequences."""
    
    # 3x3 region grid for 64x64 coordinate space
    GRID_SIZE = 64
    REGION_NAMES = {
        (0, 0): 'NW', (1, 0): 'N', (2, 0): 'NE',
        (0, 1): 'W',  (1, 1): 'C', (2, 1): 'E',
        (0, 2): 'SW', (1, 2): 'S', (2, 2): 'SE'
    }
    
    def __init__(self, db_path: str = "core_data.db"):
        """Initialize abstraction engine."""
        self.db = DatabaseInterface(db_path)
        # Cache few-shot relational patterns (action invariants/variants) to avoid repeated queries
        self._relation_cache: Dict[Tuple[str, int], Optional[Dict[str, Any]]] = {}
        self._pattern_cache = RelationalPatternCache(self.db)

    # --------------------------------------------------------------------
    # Few-shot relational pattern mining (minimal support = 2 sequences)
    # --------------------------------------------------------------------
    def get_few_shot_relations(
        self,
        game_type: str,
        level_number: int,
        min_sequences: int = 2,
        max_sequences: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        Derive lightweight relational patterns (invariants/variants) from a handful of sequences.

        This enables few-shot generalization: after 2-3 consistent examples, expose
        the positions that are reliably stable vs flexible without running full
        template synthesis. Safe for emit-only guidance (no direct mutations).
        """
        cache_key = (game_type, level_number)
        if cache_key in self._relation_cache:
            return self._relation_cache[cache_key]

        try:
            sequences = self.db.execute_query(
                """
                SELECT action_sequence, coordinate_sequence
                FROM winning_sequences
                WHERE game_id LIKE ? AND level_number = ?
                ORDER BY total_score DESC, total_actions ASC
                LIMIT ?
                """,
                (f"{game_type}%", level_number, max_sequences),
            )

            if not sequences or len(sequences) < min_sequences:
                self._relation_cache[cache_key] = None
                return None

            patterns: List[List[int]] = []
            coord_sequences: List[List] = []

            for seq in sequences:
                actions = seq.get("action_sequence")
                coords = seq.get("coordinate_sequence")
                try:
                    actions_list = json.loads(actions) if isinstance(actions, str) else actions
                    coords_list = json.loads(coords) if isinstance(coords, str) else coords
                    pattern = self._extract_pattern(actions_list)
                    if pattern:
                        patterns.append(pattern)
                        coord_sequences.append(coords_list if isinstance(coords_list, list) else [])
                except Exception as parse_exc:
                    logger.debug(f"[RELATIONS] parse skip: {parse_exc}")
                    continue

            if len(patterns) < min_sequences:
                self._relation_cache[cache_key] = None
                return None

            min_len = min(len(p) for p in patterns)
            invariants: List[Dict[str, Any]] = []
            variant_regions: List[Dict[str, Any]] = []
            current_variant_start: Optional[int] = None

            for pos in range(min_len):
                actions_at_pos = [p[pos] for p in patterns]
                unique_actions = set(actions_at_pos)

                if len(unique_actions) == 1:
                    action_type = actions_at_pos[0]
                    coords = self._get_averaged_coords(
                        [
                            {
                                "actions": patterns[idx],
                                "coordinates": coord_sequences[idx],
                                "length": len(patterns[idx]),
                            }
                            for idx in range(len(patterns))
                        ],
                        pos,
                    )
                    invariants.append(
                        {
                            "position": pos,
                            "action": action_type,
                            "support": len(patterns),
                            "coordinates": coords,
                        }
                    )
                    if current_variant_start is not None:
                        variant_regions.append(
                            {
                                "start": current_variant_start,
                                "end": pos - 1,
                                "options": self._get_variant_options(
                                    [
                                        {
                                            "actions": patterns[idx],
                                            "coordinates": coord_sequences[idx],
                                            "length": len(patterns[idx]),
                                        }
                                        for idx in range(len(patterns))
                                    ],
                                    current_variant_start,
                                    pos - 1,
                                ),
                            }
                        )
                        current_variant_start = None
                else:
                    if current_variant_start is None:
                        current_variant_start = pos

            if current_variant_start is not None:
                variant_regions.append(
                    {
                        "start": current_variant_start,
                        "end": min_len - 1,
                        "options": self._get_variant_options(
                            [
                                {
                                    "actions": patterns[idx],
                                    "coordinates": coord_sequences[idx],
                                    "length": len(patterns[idx]),
                                }
                                for idx in range(len(patterns))
                            ],
                            current_variant_start,
                            min_len - 1,
                        ),
                    }
                )

            invariant_ratio = len(invariants) / min_len if min_len else 0.0
            sample_confidence = min(len(patterns) / 5.0, 1.0)
            confidence = (invariant_ratio * 0.6) + (sample_confidence * 0.4)

            result = {
                "game_type": game_type,
                "level": level_number,
                "invariants": invariants,
                "variant_regions": variant_regions,
                "sample_size": len(patterns),
                "confidence": confidence,
            }

            self._relation_cache[cache_key] = result
            # Emit to relational pattern cache (emit-only, no control mutations here)
            try:
                signature = json.dumps([inv.get('action') for inv in invariants])
                self._pattern_cache.upsert_pattern(
                    signature=signature,
                    pattern_json=json.dumps(result),
                    context=f"{game_type}@L{level_number}",
                    outcome=confidence,
                )
            except Exception as exc:
                logger.debug(f"[RELATIONS] cache emit failed: {exc}")
            return result

        except Exception as exc:
            logger.debug(f"[RELATIONS] compute failure: {exc}")
            self._relation_cache[cache_key] = None
            return None
    
    def _coords_to_region(self, x: int, y: int) -> str:
        """Convert (x, y) coordinates to region name (NW, N, NE, W, C, E, SW, S, SE)."""
        # Divide 64x64 grid into 3x3 regions (~21x21 each)
        col = min(x // (self.GRID_SIZE // 3), 2)  # 0, 1, or 2
        row = min(y // (self.GRID_SIZE // 3), 2)  # 0, 1, or 2
        return self.REGION_NAMES.get((col, row), 'C')  # Default to center
    
    def get_sequence_by_concept(
        self,
        game_id: str,
        level_number: int,
        current_actions: Optional[List[int]] = None,
        pattern_similarity: float = 0.7
    ) -> Optional[Dict]:
        """
        Match sequences by ACTION PATTERN (concept), not frames.
        
        Action patterns like [1,3,1,3] = "zigzag right-left" work
        across ANY game state!
        """
        candidates = self._get_candidates(game_id, level_number)
        
        if not candidates or not current_actions:
            return candidates[0] if candidates else None
        
        # Score by pattern similarity
        scored = []
        for seq in candidates:
            try:
                seq_actions = json.loads(seq['action_sequence']) if isinstance(seq['action_sequence'], str) else seq['action_sequence']
                seq_pattern = self._extract_pattern(seq_actions)
                
                similarity = self._pattern_similarity(current_actions, seq_pattern)
                
                if similarity >= pattern_similarity:
                    scored.append((seq, similarity))
            except Exception as e:
                logger.debug(f"Error scoring: {e}")
                continue
        
        if scored:
            best_seq, score = max(scored, key=lambda x: x[1])
            logger.info(f"✓ Concept match: {best_seq['sequence_id'][:12]} ({score:.1%} similar)")
            return best_seq
        
        return candidates[0] if candidates else None
    
    def _extract_pattern(self, actions: List) -> List[int]:
        """Extract action type pattern."""
        pattern = []
        for action in actions:
            if isinstance(action, dict):
                action_type = action.get('action', 0)
                if isinstance(action_type, str) and action_type.startswith('ACTION'):
                    action_type = int(action_type.replace('ACTION', ''))
                pattern.append(action_type)
            elif isinstance(action, int):
                pattern.append(action)
        return pattern
    
    def _pattern_similarity(self, p1: List[int], p2: List[int]) -> float:
        """Calculate pattern similarity using LCS."""
        if not p1 or not p2:
            return 0.0
        
        if p1 == p2:
            return 1.0
        
        # Length + overlap similarity
        len_ratio = min(len(p1), len(p2)) / max(len(p1), len(p2))
        lcs_len = self._lcs(p1, p2)
        overlap_ratio = lcs_len / max(len(p1), len(p2))
        
        return (len_ratio * 0.3) + (overlap_ratio * 0.7)
    
    def _lcs(self, s1: List, s2: List) -> int:
        """Longest common subsequence length."""
        if not s1 or not s2:
            return 0
        
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def _get_candidates(self, game_id: str, level_number: int, max_results: int = 50) -> List[Dict]:
        """Get candidate sequences."""
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            sequences = self.db.execute_query("""
                SELECT ws.*, COALESCE(sr.success_rate, 0.5) as success_rate
                FROM winning_sequences ws
                LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                WHERE ws.game_id LIKE ? AND ws.level_number = ?
                ORDER BY sr.success_rate DESC, ws.total_actions ASC
                LIMIT ?
            """, (f"{game_type}%", level_number, max_results))
            
            return sequences or []
        except Exception as e:
            logger.error(f"Error fetching candidates: {e}")
            return []
    
    # ========================================================================
    # ENHANCED: Abstract Template System
    # ========================================================================
    
    def generate_abstract_template(
        self,
        game_type: str,
        level_number: int,
        min_sequences: int = 2,
        persona_id: Optional[str] = None,
        world_model: Optional[str] = None,
        problem_signature: Optional[str] = None,
    ) -> Optional[AbstractTemplate]:
        """
        Generate an executable abstract template from multiple winning sequences.
        
        This is the core enhancement - creates templates that can be REPLAYED,
        not just hints that are displayed.
        
        Args:
            game_type: Game type prefix (e.g., 'vc33')
            level_number: Level to generate template for
            min_sequences: Minimum sequences required (default 2 for more templates)
            
        Returns:
            AbstractTemplate if enough sequences exist, None otherwise
        """
        try:
            # Fetch winning sequences for this game/level
            sequences = self.db.execute_query("""
                SELECT action_sequence, coordinate_sequence, game_id, 
                       level_number, total_actions, total_score
                FROM winning_sequences
                WHERE game_id LIKE ? AND level_number = ?
                ORDER BY total_score DESC, total_actions ASC
                LIMIT 20
            """, (f"{game_type}%", level_number))
            
            if not sequences or len(sequences) < min_sequences:
                logger.debug(f"Not enough sequences for {game_type}@L{level_number}: {len(sequences) if sequences else 0}/{min_sequences}")
                return None
            
            # Parse all sequences
            parsed_sequences = []
            for seq in sequences:
                try:
                    actions = json.loads(seq['action_sequence']) if isinstance(seq['action_sequence'], str) else seq['action_sequence']
                    coords = None
                    if seq.get('coordinate_sequence'):
                        coords = json.loads(seq['coordinate_sequence']) if isinstance(seq['coordinate_sequence'], str) else seq['coordinate_sequence']
                    parsed_sequences.append({
                        'actions': actions,
                        'coordinates': coords,
                        'length': len(actions)
                    })
                except Exception as e:
                    logger.debug(f"Parse error: {e}")
                    continue
            
            if len(parsed_sequences) < min_sequences:
                return None
            
            # Find minimum length (template will be this long)
            min_len = min(p['length'] for p in parsed_sequences)
            avg_len = sum(p['length'] for p in parsed_sequences) / len(parsed_sequences)
            
            # Extract action patterns
            patterns = [self._extract_pattern(p['actions'][:min_len]) for p in parsed_sequences]
            
            # Find invariants (same action at same position in ALL sequences)
            invariant_actions = []
            template_sequence = []
            variant_regions = []
            current_variant_start = None
            
            for pos in range(min_len):
                actions_at_pos = [p[pos] for p in patterns]
                unique_actions = set(actions_at_pos)
                
                if len(unique_actions) == 1:
                    # INVARIANT: All sequences have same action here
                    action_type = actions_at_pos[0]
                    
                    # Get averaged coordinates from all sequences
                    coords = self._get_averaged_coords(parsed_sequences, pos)
                    
                    invariant_actions.append({
                        'position': pos,
                        'action': action_type,
                        'coordinates': coords,
                        'is_invariant': True
                    })
                    
                    template_sequence.append({
                        'action': action_type,
                        'x': coords['x'] if coords else None,
                        'y': coords['y'] if coords else None,
                        'is_invariant': True,
                        'position': pos
                    })
                    
                    # Close any open variant region
                    if current_variant_start is not None:
                        variant_regions.append({
                            'start': current_variant_start,
                            'end': pos - 1,
                            'options': self._get_variant_options(parsed_sequences, current_variant_start, pos - 1)
                        })
                        current_variant_start = None
                else:
                    # VARIANT: Different actions across sequences
                    if current_variant_start is None:
                        current_variant_start = pos
                    
                    # Use most common action as default
                    most_common = max(set(actions_at_pos), key=actions_at_pos.count)
                    coords = self._get_averaged_coords(parsed_sequences, pos)
                    
                    template_sequence.append({
                        'action': most_common,
                        'x': coords['x'] if coords else None,
                        'y': coords['y'] if coords else None,
                        'is_invariant': False,
                        'alternatives': list(unique_actions),
                        'position': pos
                    })
            
            # Close final variant region if open
            if current_variant_start is not None:
                variant_regions.append({
                    'start': current_variant_start,
                    'end': min_len - 1,
                    'options': self._get_variant_options(parsed_sequences, current_variant_start, min_len - 1)
                })
            
            # Calculate confidence based on sample size and invariant ratio
            invariant_ratio = len(invariant_actions) / min_len if min_len > 0 else 0
            sample_confidence = min(len(parsed_sequences) / 5.0, 1.0)  # 5+ sequences = full confidence
            confidence = (invariant_ratio * 0.6) + (sample_confidence * 0.4)
            
            template = AbstractTemplate(
                game_type=game_type,
                level_number=level_number,
                invariant_actions=invariant_actions,
                variant_regions=variant_regions,
                template_sequence=template_sequence,
                confidence=confidence,
                sample_size=len(parsed_sequences),
                avg_length=avg_len,
                persona_id=persona_id,
                world_model=world_model,
                problem_signature=problem_signature,
            )
            
            logger.info(f"[TEMPLATE] Generated {template}")
            try:
                # Store template summary in relational cache for heuristic reuse
                signature = json.dumps([step.get('action') for step in template_sequence[:10]])
                self._pattern_cache.upsert_pattern(
                    signature=signature,
                    pattern_json=json.dumps(template_sequence[:10]),
                    context=f"template:{game_type}@L{level_number}",
                    outcome=confidence,
                )
            except Exception as exc:
                logger.debug(f"[RELATIONS] template cache emit failed: {exc}")
            return template
            
        except Exception as e:
            logger.error(f"Error generating template: {e}")
            return None
    
    def _get_averaged_coords(
        self,
        parsed_sequences: List[Dict],
        position: int
    ) -> Optional[Dict[str, int]]:
        """Get averaged coordinates for a position across all sequences."""
        x_coords = []
        y_coords = []
        
        for seq in parsed_sequences:
            if seq.get('coordinates') and position < len(seq['coordinates']):
                coord = seq['coordinates'][position]
                if coord and len(coord) >= 2:
                    x_coords.append(coord[0])
                    y_coords.append(coord[1])
        
        if not x_coords or not y_coords:
            return None
        
        return {
            'x': int(sum(x_coords) / len(x_coords)),
            'y': int(sum(y_coords) / len(y_coords)),
            'x_variance': max(x_coords) - min(x_coords),
            'y_variance': max(y_coords) - min(y_coords)
        }
    
    def _get_variant_options(
        self,
        parsed_sequences: List[Dict],
        start: int,
        end: int
    ) -> List[List[int]]:
        """Get all variant action subsequences for a region."""
        options = []
        for seq in parsed_sequences:
            pattern = self._extract_pattern(seq['actions'])
            if end < len(pattern):
                options.append(pattern[start:end+1])
        return options

    # --------------------------------------------------------------------
    # Telemetry harvesting (action_proposals_log, lesson_interpretations)
    # --------------------------------------------------------------------
    def harvest_relational_patterns(self, max_rows: int = 200) -> None:
        """Ingest recent telemetry into relational pattern cache (emit-only)."""
        try:
            rows = self.db.execute_query(
                """
                SELECT attempt_id, step_idx, resonance_tags, chosen_action, chosen_reason
                FROM action_proposals_log
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (max_rows,),
            )
            for row in rows or []:
                signature = row.get('resonance_tags') or row.get('chosen_action') or 'unknown'
                context = row.get('chosen_reason') or 'action_proposals'
                pattern_json = json.dumps({
                    'resonance_tags': row.get('resonance_tags'),
                    'chosen_action': row.get('chosen_action'),
                    'step_idx': row.get('step_idx'),
                })
                self._pattern_cache.upsert_pattern(signature=str(signature), pattern_json=pattern_json, context=context, outcome=0.5)
        except Exception as exc:
            logger.debug(f"[RELATIONS] harvest (proposals) failed: {exc}")

        try:
            rows = self.db.execute_query(
                """
                SELECT interpretation, resonance_tags, reasoning_tags, score_delta
                FROM lesson_interpretations
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (max_rows // 2,),
            )
            for row in rows or []:
                signature = row.get('interpretation') or 'lesson'
                context = row.get('reasoning_tags') or 'lesson_interpretation'
                pattern_json = json.dumps({
                    'interpretation': row.get('interpretation'),
                    'resonance_tags': row.get('resonance_tags'),
                })
                outcome = float(row.get('score_delta') or 0.0)
                self._pattern_cache.upsert_pattern(signature=str(signature), pattern_json=pattern_json, context=str(context), outcome=outcome)
        except Exception as exc:
            logger.debug(f"[RELATIONS] harvest (lessons) failed: {exc}")

    # --------------------------------------------------------------------
    # Contrastive near-miss mining (win vs near-miss deltas)
    # --------------------------------------------------------------------
    def generate_contrastive_hints(
        self,
        game_type: str,
        level_number: int,
        near_miss_limit: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """
        Derive minimal contrasts between wins and near-misses (emit-only hints).
        Uses attempts table if available. Safe to ignore failures.
        """
        try:
            wins = self.db.execute_query(
                """
                SELECT action_sequence FROM winning_sequences
                WHERE game_id LIKE ? AND level_number = ?
                ORDER BY total_score DESC, total_actions ASC
                LIMIT 3
                """,
                (f"{game_type}%", level_number),
            )
            if not wins:
                return None

            near = self.db.execute_query(
                """
                SELECT action_sequence, final_score
                FROM attempts
                WHERE game_id LIKE ? AND level_number = ? AND final_score > 0 AND win = 0
                ORDER BY final_score DESC
                LIMIT ?
                """,
                (f"{game_type}%", level_number, near_miss_limit),
            )
            if not near:
                return None

            win_pattern = self._extract_pattern(json.loads(wins[0]['action_sequence'])) if isinstance(wins[0]['action_sequence'], str) else self._extract_pattern(wins[0]['action_sequence'])
            contrasts = []

            for nm in near:
                nm_actions = json.loads(nm['action_sequence']) if isinstance(nm['action_sequence'], str) else nm['action_sequence']
                nm_pattern = self._extract_pattern(nm_actions)
                if not nm_pattern or not win_pattern:
                    continue
                # Find earliest divergence
                min_len = min(len(win_pattern), len(nm_pattern))
                divergence_pos = None
                for idx in range(min_len):
                    if win_pattern[idx] != nm_pattern[idx]:
                        divergence_pos = idx
                        break
                if divergence_pos is not None:
                    contrasts.append({
                        'divergence_at': divergence_pos,
                        'win_action': win_pattern[divergence_pos],
                        'near_action': nm_pattern[divergence_pos],
                        'near_score': nm.get('final_score', 0),
                    })

            if not contrasts:
                return None

            summary = {
                'game_type': game_type,
                'level': level_number,
                'contrasts': contrasts[:5],
            }
            self._pattern_cache.upsert_pattern(
                signature=f"contrast:{game_type}@L{level_number}",
                pattern_json=json.dumps(summary),
                context='contrastive_near_miss',
                outcome=0.6,
            )
            return summary
        except Exception as exc:
            logger.debug(f"[RELATIONS] contrastive hints failed: {exc}")
            return None
    
    def get_template_for_replay(
        self,
        game_type: str,
        level_number: int,
        adapt_to_state: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get an executable action sequence from the abstract template.
        
        This is what agents actually use during gameplay - returns actions
        ready to send to the API.
        
        Args:
            game_type: Game type prefix
            level_number: Level number
            adapt_to_state: Whether to adapt coordinates (future: use current frame)
            
        Returns:
            List of action dicts ready for execution, or None if no template
        """
        template = self.generate_abstract_template(game_type, level_number)
        
        if not template:
            return None
        
        # Convert template to executable actions
        executable = []
        for step in template.template_sequence:
            action_dict = {
                'action': f"ACTION{step['action']}",
                'action_type': step['action']
            }
            
            # Add coordinates if available
            if step.get('x') is not None and step.get('y') is not None:
                action_dict['x'] = step['x']
                action_dict['y'] = step['y']
            
            executable.append(action_dict)
        
        logger.info(f"[REPLAY] Template ready: {len(executable)} actions for {game_type}@L{level_number}")
        return executable
    
    def get_frontier_templates(
        self,
        game_type: str,
        up_to_level: int
    ) -> Dict[int, Optional[AbstractTemplate]]:
        """
        Get templates for all levels up to the frontier.
        
        Used to quickly replay through solved levels to reach unsolved territory.
        
        Args:
            game_type: Game type prefix
            up_to_level: Generate templates for levels 1 through up_to_level
            
        Returns:
            Dict mapping level_number -> AbstractTemplate (or None if unavailable)
        """
        templates = {}
        for level in range(1, up_to_level + 1):
            templates[level] = self.generate_abstract_template(game_type, level)
        
        available = sum(1 for t in templates.values() if t is not None)
        logger.info(f"[FRONTIER] Generated {available}/{up_to_level} templates for {game_type}")
        
        return templates
    
    def should_use_template(
        self,
        game_type: str,
        level_number: int,
        min_confidence: float = 0.5
    ) -> Tuple[bool, Optional[AbstractTemplate]]:
        """
        Decide whether to use a template for this level.
        
        Returns (should_use, template) tuple.
        
        Criteria:
        - Template exists
        - Confidence >= min_confidence
        - At least 2 invariant actions (some structure exists)
        """
        template = self.generate_abstract_template(game_type, level_number)
        
        if not template:
            return (False, None)
        
        if template.confidence < min_confidence:
            logger.debug(f"Template confidence too low: {template.confidence:.0%} < {min_confidence:.0%}")
            return (False, template)
        
        if len(template.invariant_actions) < 2:
            logger.debug(f"Too few invariants: {len(template.invariant_actions)}")
            return (False, template)
        
        return (True, template)
    
    # ========================================================================
    # Original Methods (kept for backwards compatibility)
    # ========================================================================

    def extract_multi_sequence_concept(
        self,
        game_id: str,
        level_number: int,
        min_sequences: int = 3
    ) -> Optional[Dict]:
        """
        Extract common concept from MULTIPLE sequences (same game/level).
        
        Returns what MUST happen (invariants) vs what CAN vary (variants).
        THIS IS TRUE ABSTRACTION!
        """
        try:
            game_type = game_id.split('-')[0] if '-' in game_id else game_id
            
            sequences = self.db.execute_query("""
                SELECT action_sequence, coordinate_sequence, game_id, level_number
                FROM winning_sequences
                WHERE game_id LIKE ? AND level_number = ?
                ORDER BY total_score DESC
                LIMIT 20
            """, (f"{game_type}%", level_number))
            
            if not sequences or len(sequences) < min_sequences:
                return None
            
            # Extract all patterns
            patterns = []
            for seq in sequences:
                try:
                    actions = json.loads(seq['action_sequence']) if isinstance(seq['action_sequence'], str) else seq['action_sequence']
                    pattern = self._extract_pattern(actions)
                    if pattern:
                        patterns.append(pattern)
                except (json.JSONDecodeError, TypeError):
                    continue  # Invalid JSON - skip this sequence
            
            if len(patterns) < min_sequences:
                return None
            
            # Find invariants and variants
            min_len = min(len(p) for p in patterns)
            
            # Find positions where ALL patterns have same action
            invariant_positions = []
            for pos in range(min_len):
                actions_at_pos = [p[pos] for p in patterns]
                if len(set(actions_at_pos)) == 1:  # All same
                    action_type = actions_at_pos[0]
                    
                    # Get coordinates for this position across all sequences
                    coords = []
                    for seq in sequences[:len(patterns)]:
                        try:
                            # Coordinates are in separate 'coordinate_sequence' column
                            if seq.get('coordinate_sequence'):
                                coord_seq = json.loads(seq['coordinate_sequence']) if isinstance(seq['coordinate_sequence'], str) else seq['coordinate_sequence']
                                if pos < len(coord_seq) and coord_seq[pos]:
                                    # coord_seq[pos] is [x, y]
                                    coords.append(tuple(coord_seq[pos]))
                        except Exception as e:
                            logger.debug(f"Error parsing coordinates: {e}")
                            continue
                    
                    # Calculate coordinate approximation
                    coord_info = None
                    if coords:
                        x_coords = [c[0] for c in coords]
                        y_coords = [c[1] for c in coords]
                        
                        # Convert to regions
                        regions = [self._coords_to_region(c[0], c[1]) for c in coords]
                        unique_regions = sorted(set(regions))
                        
                        # Check if coordinates are consistent
                        x_variance = max(x_coords) - min(x_coords) if x_coords else 0
                        y_variance = max(y_coords) - min(y_coords) if y_coords else 0
                        
                        coord_info = {
                            'regions': unique_regions,
                            'region_count': len(unique_regions),
                            'x_range': (min(x_coords), max(x_coords)),
                            'y_range': (min(y_coords), max(y_coords)),
                            'x_mean': sum(x_coords) / len(x_coords),
                            'y_mean': sum(y_coords) / len(y_coords),
                            'is_fixed': (x_variance <= 1 and y_variance <= 1),  # Within 1 cell = fixed
                            'is_regional': len(unique_regions) <= 2  # 1-2 regions = regional pattern
                        }
                    
                    invariant_positions.append({
                        'position': pos,
                        'action': action_type,
                        'coordinates': coord_info
                    })
            
            # Find variable regions
            variable_regions = []
            current_region = None
            
            for pos in range(min_len):
                actions_at_pos = [p[pos] for p in patterns]
                is_variable = len(set(actions_at_pos)) > 1
                
                if is_variable:
                    if current_region is None:
                        current_region = {'start': pos, ' variations': set(actions_at_pos)}
                    else:
                        current_region['variations'].update(actions_at_pos)
                else:
                    if current_region:
                        current_region['end'] = pos - 1
                        variable_regions.append(current_region)
                        current_region = None
            
            if current_region:
                current_region['end'] = min_len - 1
                variable_regions.append(current_region)
            
            # Build template
            template = []
            action_names = {1: "right", 2: "down", 3: "left", 4: "up", 5: "select", 6: "submit", 7: "reset"}
            
            for pos in range(min_len):
                if any(inv['position'] == pos for inv in invariant_positions):
                    action = next(inv['action'] for inv in invariant_positions if inv['position'] == pos)
                    template.append(f"ACTION{action}")
                else:
                    template.append("VARIABLE")
            
            # Description
            if len(invariant_positions) >= 3:
                desc = f"Fixed {len(invariant_positions)} checkpoints"
            elif len(invariant_positions) > 0:
                desc = f"{len(invariant_positions)} required actions"
            else:
                desc = "Flexible strategy"
            
            confidence = min(len(patterns) / 10.0, 1.0)
            
            # =================================================================
            # COGNITIVE INTEGRATION: Abstraction -> Concept Discovery
            # =================================================================
            # When we find strong invariants, notify ConceptDiscoveryEngine
            # This closes the abstraction cycle - templates become patterns
            # =================================================================
            if len(invariant_positions) >= 3 and confidence >= 0.5:
                # Create a pattern description from invariants
                invariant_pattern = ",".join([
                    f"pos{inv['position']}=ACTION{inv['action']}"
                    for inv in invariant_positions[:5]
                ])
                pattern_description = f"sequence_invariant:{game_type}:L{level_number}:{invariant_pattern}"
                
                _notify_concept_discovery(
                    pattern=pattern_description,
                    game_type=game_type,
                    confidence=confidence,
                    source="multi_sequence_invariant"
                )
            
            return {
                'description': desc,
                'invariant_positions': invariant_positions,
                'variable_regions': [
                    {
                        'start': r['start'],
                        'end': r['end'],
                        'options': list(r['variations'])
                    } for r in variable_regions
                ],
                'template': template,
                'sample_size': len(patterns),
                'confidence': confidence,
                'game_type': game_type,
                'level': level_number
            }
        
        except Exception as e:
            logger.error(f"Error extracting concept: {e}")
            return None

    def get_conceptual_hints(self, game_type: str, level_number: int = 1) -> Optional[Dict]:
        """
        Get conceptual hints for exploration when all sequences fail.
        Returns action patterns and invariants that worked across sequences.
        
        Used by 3-try fallback system to guide exploration after sequence failures.
        
        Args:
            game_type: Game type prefix (e.g., 'vc33')
            level_number: Level to get hints for
            
        Returns:
            Dict with 'hints' (action suggestions) and 'avoid' (known failures)
        """
        try:
            # Extract concepts from existing sequences
            concept = self.extract_multi_sequence_concept(game_type, level_number, min_sequences=2)
            
            if not concept:
                return None
            
            hints = []
            avoid = []
            
            # Convert invariants to hints
            action_names = {1: "right", 2: "down", 3: "left", 4: "up", 5: "select", 6: "submit", 7: "reset"}
            
            if concept.get('invariant_positions'):
                for inv in concept['invariant_positions'][:5]:
                    action_num = inv.get('action', 0)
                    action_name = action_names.get(action_num, f"ACTION{action_num}")
                    coord_info = ""
                    if inv.get('coordinates') and inv['coordinates'].get('is_fixed'):
                        c = inv['coordinates']
                        coord_info = f" at ({c['x_mean']:.0f},{c['y_mean']:.0f})"
                    hints.append(f"Try {action_name}{coord_info} early in sequence")
            
            # Check for common starting patterns
            if concept.get('template'):
                template = concept['template'][:5]
                hints.append(f"Common pattern: {' -> '.join(template)}")
            
            return {
                'hints': hints,
                'avoid': avoid,
                'confidence': concept.get('confidence', 0.0),
                'source': 'multi_sequence_concept'
            }
            
        except Exception as e:
            logger.debug(f"Error getting conceptual hints: {e}")
            return None

    # ========================================================================
    # PRIMITIVE-AWARE SEQUENCE ANALYSIS
    # ========================================================================
    # Connect sequence patterns to primitives needed to detect/execute them
    # ========================================================================
    
    def analyze_primitive_requirements(
        self,
        game_type: str,
        level_number: int
    ) -> Dict[str, Any]:
        """
        Analyze what primitives would help detect/execute sequence patterns.
        
        This connects sequence abstraction to CODS:
        - Invariant actions may need specific detection primitives
        - Coordinate patterns may need spatial primitives
        - Action sequences may need temporal primitives
        
        Args:
            game_type: Game type prefix
            level_number: Level to analyze
            
        Returns:
            Dict with:
            - required_primitives: Must have for this sequence type
            - helpful_primitives: Would improve execution
            - detection_strategy: How to detect when to execute
            - confidence: How confident we are in this analysis
        """
        template = self.generate_abstract_template(game_type, level_number)
        
        result = {
            'required_primitives': [],
            'helpful_primitives': [],
            'detection_strategy': None,
            'sequence_type': None,
            'confidence': 0.0
        }
        
        if not template:
            return result
        
        required = set()
        helpful = set()
        
        # Analyze invariant actions for primitive requirements
        for inv in template.invariant_actions:
            action = inv.get('action', 0)
            coords = inv.get('coordinates')
            
            # Movement actions (1-4) need object tracking
            if action in [1, 2, 3, 4]:
                required.add('get_frame')
                helpful.add('detect_movement')
                helpful.add('track_object')
            
            # Selection action (5) needs object detection
            if action == 5:
                required.add('get_frame')
                helpful.add('detect_object')
                helpful.add('identify_goal')
            
            # Submit/click action (6) - coordinate dependent
            if action == 6:
                required.add('get_frame')
                if coords and coords.get('x_variance', 0) < 5:
                    # Fixed coordinate - need precise detection
                    helpful.add('detect_target')
                    helpful.add('get_pixel')
                else:
                    # Variable coordinate - need region detection
                    helpful.add('detect_region')
            
            # Coordinates present - spatial awareness needed
            if coords:
                helpful.add('get_pixel')
                if coords.get('is_fixed'):
                    helpful.add('detect_exact_position')
                if coords.get('is_regional'):
                    helpful.add('detect_region')
        
        # Analyze variant regions for adaptive primitives
        for var_region in template.variant_regions:
            # Multiple options = need decision-making primitives
            if var_region.get('options') and len(var_region['options']) > 1:
                helpful.add('frame_diff')
                helpful.add('detect_change')
        
        # Sequence length analysis
        if len(template.template_sequence) > 10:
            # Long sequences need temporal primitives
            helpful.add('get_action_history')
            helpful.add('get_elapsed_actions')
        
        # Detect sequence type
        action_counts = {}
        for step in template.template_sequence:
            a = step.get('action', 0)
            action_counts[a] = action_counts.get(a, 0) + 1
        
        dominant_action = max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else 0
        
        if dominant_action in [1, 2, 3, 4]:
            result['sequence_type'] = 'movement_dominant'
            required.add('detect_boundary')
        elif dominant_action == 6:
            result['sequence_type'] = 'click_dominant'
            required.add('detect_target')
        elif dominant_action == 5:
            result['sequence_type'] = 'selection_dominant'
            required.add('detect_object')
        else:
            result['sequence_type'] = 'mixed'
        
        # Build detection strategy
        if template.invariant_actions:
            first_invariant = template.invariant_actions[0]
            strategy = {
                'trigger': 'level_start',
                'first_action': first_invariant.get('action'),
                'checkpoint_count': len(template.invariant_actions),
                'adaptable_regions': len(template.variant_regions)
            }
            result['detection_strategy'] = strategy
        
        result['required_primitives'] = list(required)
        result['helpful_primitives'] = list(helpful - required)  # Don't duplicate
        result['confidence'] = template.confidence
        
        return result

    def get_template_with_primitives(
        self,
        game_type: str,
        level_number: int,
        available_primitives: List[str],
        persona_id: Optional[str] = None,
        world_model: Optional[str] = None,
        problem_signature: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a template enriched with primitive-based execution guidance.
        
        This is what formal agents use to execute sequences intelligently,
        not just replay blindly.
        
        Args:
            game_type: Game type prefix
            level_number: Level number
            available_primitives: List of primitives agent has access to
            
        Returns:
            Dict with template, primitive requirements, and execution hints
        """
        template = self.generate_abstract_template(
            game_type,
            level_number,
            persona_id=persona_id,
            world_model=world_model,
            problem_signature=problem_signature,
        )
        requirements = self.analyze_primitive_requirements(game_type, level_number)
        
        if not template:
            return None
        
        # Check if agent has required primitives
        missing_required = [
            p for p in requirements['required_primitives'] 
            if p not in available_primitives
        ]
        
        missing_helpful = [
            p for p in requirements['helpful_primitives']
            if p not in available_primitives
        ]
        
        # Calculate execution readiness
        if not requirements['required_primitives']:
            readiness = 1.0
        else:
            have_required = len(requirements['required_primitives']) - len(missing_required)
            readiness = have_required / len(requirements['required_primitives'])
        
        # Build execution hints based on available primitives
        execution_hints = []
        
        if 'detect_boundary' in available_primitives:
            execution_hints.append("Use boundary detection to know when to turn")
        
        if 'frame_diff' in available_primitives:
            execution_hints.append("Compare frames to detect progress")
        
        if 'get_action_history' in available_primitives:
            execution_hints.append("Track actions to avoid oscillation")
        
        if 'detect_object' in available_primitives:
            execution_hints.append("Identify target objects for clicks")
        
        return {
            'template': template,
            'executable_sequence': template.to_executable(),
            'requirements': requirements,
            'missing_required': missing_required,
            'missing_helpful': missing_helpful,
            'execution_readiness': readiness,
            'execution_hints': execution_hints,
            'can_execute': readiness >= 0.8,  # 80% of required primitives
            'sequence_type': requirements['sequence_type'],
            'persona_provenance': {
                'persona_id': template.persona_id,
                'world_model': template.world_model,
                'problem_signature': template.problem_signature,
            },
        }

    def suggest_primitives_for_game(
        self,
        game_type: str,
        max_level: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze multiple levels to suggest what primitives would help this game.
        
        Used by CODS to prioritize primitive unlocking based on game needs.
        
        Args:
            game_type: Game type prefix
            max_level: How many levels to analyze
            
        Returns:
            Dict with primitive recommendations and unlock priority
        """
        all_required = {}
        all_helpful = {}
        levels_analyzed = 0
        
        for level in range(1, max_level + 1):
            reqs = self.analyze_primitive_requirements(game_type, level)
            
            if reqs['confidence'] > 0:
                levels_analyzed += 1
                
                for p in reqs['required_primitives']:
                    all_required[p] = all_required.get(p, 0) + 1
                
                for p in reqs['helpful_primitives']:
                    all_helpful[p] = all_helpful.get(p, 0) + 1
        
        if levels_analyzed == 0:
            return {'error': 'No templates available for analysis'}
        
        # Sort by frequency
        sorted_required = sorted(all_required.items(), key=lambda x: x[1], reverse=True)
        sorted_helpful = sorted(all_helpful.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'game_type': game_type,
            'levels_analyzed': levels_analyzed,
            'required_primitives': [
                {'primitive': p, 'needed_in_levels': count, 'priority': 'high'}
                for p, count in sorted_required
            ],
            'helpful_primitives': [
                {'primitive': p, 'helpful_in_levels': count, 'priority': 'medium'}
                for p, count in sorted_helpful
            ],
            'unlock_recommendation': (
                sorted_required[0][0] if sorted_required else 
                (sorted_helpful[0][0] if sorted_helpful else None)
            )
        }
    
    def learn_from_outcome(
        self,
        action: Optional[str],
        outcome: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """
        Learn from action outcome to improve abstraction patterns.
        
        This is called by experience_outcome() when cognitive faculties provide
        feedback about action results. Updates template reliability and 
        pattern confidence based on whether abstraction-suggested actions worked.
        
        Args:
            action: The action that was taken
            outcome: Dict with 'score_delta', 'frame_changed'
            context: Dict with 'game_id', 'level'
        """
        try:
            game_id = context.get('game_id', '')
            level = context.get('level', 1)
            score_delta = outcome.get('score_delta', 0)
            
            if not game_id:
                return
            
            # Extract game_type from game_id
            game_type = game_id[:4] if len(game_id) >= 4 else game_id
            
            # Invalidate cache for this game/level if outcome was negative
            # This forces re-computation of patterns
            cache_key = (game_type, level)
            
            if score_delta < 0:
                # Negative outcome - reduce confidence in cached relations
                if cache_key in self._relation_cache:
                    cached = self._relation_cache[cache_key]
                    if cached and 'confidence' in cached:
                        cached['confidence'] = max(0.1, cached['confidence'] * 0.9)
                        logger.debug(
                            f"[ABSTRACTION] Reduced confidence for {game_type}@L{level}: "
                            f"negative outcome"
                        )
            elif score_delta > 0:
                # Positive outcome - boost confidence
                if cache_key in self._relation_cache:
                    cached = self._relation_cache[cache_key]
                    if cached and 'confidence' in cached:
                        cached['confidence'] = min(1.0, cached['confidence'] * 1.05)
                        logger.debug(
                            f"[ABSTRACTION] Boosted confidence for {game_type}@L{level}: "
                            f"positive outcome"
                        )
                        
        except Exception as e:
            logger.debug(f"Abstraction learn_from_outcome failed: {e}")


# Abstraction levels
ABSTRACTION_LEVELS = {
    'exact': 1.0,
    'tight': 0.95,
    'moderate': 0.85,
    'loose': 0.75
}


if __name__ == "__main__":
    import sqlite3
    
    print("=" * 70)
    print("ENHANCED SEQUENCE ABSTRACTION - TEMPLATE REPLAY SYSTEM")
    print("=" * 70)
    
    abstraction = SequenceAbstraction()
    action_names = {1: "right", 2: "down", 3: "left", 4: "up", 5: "select", 6: "submit", 7: "reset"}
    
    # Find game types with most sequences for testing
    print("\n[DISCOVERY] Finding game types with multiple sequences...")
    conn = sqlite3.connect('core_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUBSTR(game_id, 1, 4) as game_type, level_number, COUNT(*) as seq_count
        FROM winning_sequences
        GROUP BY SUBSTR(game_id, 1, 4), level_number
        HAVING COUNT(*) >= 2
        ORDER BY seq_count DESC
        LIMIT 5
    """)
    results = cursor.fetchall()
    conn.close()
    
    if results:
        print(f"  Top game types with 2+ sequences per level:")
        for r in results:
            print(f"    {r[0]} L{r[1]}: {r[2]} sequences")
        
        game_type, level, count = results[0]
        
        # Test 1: Generate Abstract Template
        print(f"\n[TEST 1] Abstract Template Generation ({game_type}@L{level})")
        print("-" * 50)
        
        template = abstraction.generate_abstract_template(game_type, level, min_sequences=2)
        
        if template:
            print(f"  [OK] Generated: {template}")
            print(f"  Confidence: {template.confidence:.0%}")
            print(f"  Sample size: {template.sample_size} sequences")
            print(f"  Invariants: {len(template.invariant_actions)} actions")
            print(f"  Variant regions: {len(template.variant_regions)}")
            
            # Show invariants
            if template.invariant_actions:
                print(f"\n  [INVARIANTS] (MUST do in this order):")
                for inv in template.invariant_actions[:5]:
                    name = action_names.get(inv['action'], f"ACTION{inv['action']}")
                    coord_str = ""
                    if inv.get('coordinates'):
                        c = inv['coordinates']
                        coord_str = f" at ({c['x']}, {c['y']})"
                    print(f"    Pos {inv['position']}: {name}{coord_str}")
                if len(template.invariant_actions) > 5:
                    print(f"    ... and {len(template.invariant_actions) - 5} more")
            
            # Test 2: Get Executable Actions
            print(f"\n[TEST 2] Executable Template")
            print("-" * 50)
            executable = template.to_executable()
            print(f"  Ready for replay: {len(executable)} actions")
            if executable:
                print(f"  First action: {executable[0]}")
            
            # Test 3: Template Replay Method
            print(f"\n[TEST 3] Get Template for Replay API")
            print("-" * 50)
            replay_actions = abstraction.get_template_for_replay(game_type, level)
            if replay_actions:
                print(f"  [OK] API-ready actions: {len(replay_actions)}")
                print(f"  Format: {replay_actions[0]}")
            
            # Test 4: Should Use Template Decision
            print(f"\n[TEST 4] Should Use Template?")
            print("-" * 50)
            should_use, t = abstraction.should_use_template(game_type, level)
            print(f"  Decision: {'[OK] USE TEMPLATE' if should_use else '[X] SKIP (explore instead)'}")
            if t:
                print(f"  Reason: confidence={t.confidence:.0%}, invariants={len(t.invariant_actions)}")
            
            # Test 5: Frontier Templates
            print(f"\n[TEST 5] Frontier Navigation (L1-L3)")
            print("-" * 50)
            frontier = abstraction.get_frontier_templates(game_type, up_to_level=3)
            for lvl, tmpl in frontier.items():
                status = f"[OK] {len(tmpl.invariant_actions)} invariants" if tmpl else "[X] No template"
                print(f"  Level {lvl}: {status}")
        else:
            print(f"  [WARN] Could not generate template")
    else:
        print("  [WARN] No game types with multiple sequences found")
    
    # Summary
    print("\n" + "=" * 70)
    print("ENHANCED CAPABILITIES:")
    print("=" * 70)
    print("  1. generate_abstract_template() - Create reusable templates")
    print("  2. get_template_for_replay()    - Get API-ready action sequence")
    print("  3. should_use_template()        - Smart decision on when to use")
    print("  4. get_frontier_templates()     - Templates for L1..Ln navigation")
    print("  5. AbstractTemplate.to_executable() - Direct conversion to actions")
    print("\n[FLOW] Exact Match -> Loose Match -> TEMPLATE REPLAY -> Pure Exploration")
