#!/usr/bin/env python3
"""
Viral Package Engine - Phase 3
================================
Implements bidirectional evolution through viral information packages and pariahs.

Viral Packages = Positive Selection (successful patterns that spread like viruses)
Pariahs = Negative Selection (failure patterns that agents learn to avoid)

Together they accelerate evolution by teaching both what TO do and what NOT to do.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from database_interface import DatabaseInterface

# Phase 4.5: Import sensation engine for emotional context in viral packages
try:
    from sensation_engine import SensationEngine
    SENSATION_AVAILABLE = True
except ImportError:
    SENSATION_AVAILABLE = False

class ViralPackageEngine:
    """
    Manages viral information packages and pariah patterns.
    
    Viral packages spread successful strategies horizontally across unrelated agents.
    Pariahs mark failure patterns for the network to avoid.
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_frontier_columns()
        self._ensure_pariah_level_column()  # Backfill pariah source levels
        
        # Phase 4.5: Initialize sensation engine if available
        if SENSATION_AVAILABLE:
            self.sensation_engine = SensationEngine(db)
        else:
            self.sensation_engine = None
    
    def _ensure_pariah_level_column(self):
        """
        Ensure pariahs have source_level_number and backfill existing ones.
        
        Backfill logic: Use game's max completed level as the source level.
        Example: If as66 has been beaten to level 4, all as66 pariahs get source_level_number=4.
        This means on level 5 (frontier), those pariahs apply at only 5% strength.
        """
        try:
            # Check if column exists
            self.db.execute_query("SELECT source_level_number FROM pariahs LIMIT 1")
        except Exception:
            # Column doesn't exist - add it
            try:
                self.db.execute_query("""
                    ALTER TABLE pariahs ADD COLUMN source_level_number INTEGER DEFAULT 1
                """)
                print("[SCHEMA] Added source_level_number to pariahs table")
            except Exception:
                pass
        
        # Only backfill pariahs that still have source_level_number = 1 (default/unknown)
        # Use game's max beaten level as the assumed source level
        try:
            # First, count how many need updating
            need_update = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM pariahs 
                WHERE source_level_number = 1 
                AND source_game_id IS NOT NULL
                AND EXISTS (
                    SELECT 1 FROM game_results gr2
                    WHERE gr2.game_id LIKE substr(pariahs.source_game_id, 1, 4) || '%'
                    AND gr2.level_completions > 1
                )
            """)
            
            if need_update and need_update[0].get('cnt', 0) > 0:
                # Only update and print if there are actually pariahs to backfill
                self.db.execute_query("""
                    UPDATE pariahs 
                    SET source_level_number = (
                        SELECT COALESCE(MAX(gr.level_completions), 1)
                        FROM game_results gr
                        WHERE gr.game_id LIKE substr(pariahs.source_game_id, 1, 4) || '%'
                        AND gr.level_completions > 0
                    )
                    WHERE source_level_number = 1 
                    AND source_game_id IS NOT NULL
                    AND EXISTS (
                        SELECT 1 FROM game_results gr2
                        WHERE gr2.game_id LIKE substr(pariahs.source_game_id, 1, 4) || '%'
                        AND gr2.level_completions > 1
                    )
                """)
                print(f"[PARIAH] Backfilled {need_update[0]['cnt']} pariahs with source_level_number")
        except Exception as e:
            pass  # Silently continue if backfill fails
    
    def _ensure_frontier_columns(self):
        """Ensure frontier package columns exist in viral_information_packages table."""
        try:
            # Check if columns exist, add if missing
            columns_to_add = [
                ("is_frontier_temp", "BOOLEAN DEFAULT FALSE"),
                ("frontier_level", "INTEGER"),
                ("frontier_game_type", "TEXT"),
                ("deactivated_reason", "TEXT"),
                # USEFULNESS TRACKING: Track if package actually helps agents
                ("retrieval_count", "INTEGER DEFAULT 0"),
                ("improvement_count", "INTEGER DEFAULT 0"),  # Times retrieval led to score improvement
                ("last_retrieval_generation", "INTEGER")
            ]
            
            for col_name, col_def in columns_to_add:
                try:
                    self.db.execute_query(f"SELECT {col_name} FROM viral_information_packages LIMIT 1")
                except Exception:
                    # Column doesn't exist, add it
                    self.db.execute_query(f"ALTER TABLE viral_information_packages ADD COLUMN {col_name} {col_def}")
                    print(f"[SCHEMA] Added column {col_name} to viral_information_packages")
        except Exception as e:
            # Table might not exist yet, will be created later
            pass
    
    # ========================================================================
    # VIRAL PACKAGE CREATION (Positive Selection)
    # ========================================================================
    
    def create_viral_package_from_sequence(self, 
                                          sequence_id: str,
                                          agent_id: str,
                                          generation: int,
                                          skip_if_exists: bool = True) -> Optional[str]:
        """
        Create a viral package from a winning sequence.
        
        This extracts the successful pattern and packages it as a "virus"
        that can spread to other agents.
        
        DEDUPLICATION: By default, skips creating a new package if one already
        exists for this sequence_id. Different sequences for the same level
        will still each get their own viral package (diversity preserved).
        
        Args:
            sequence_id: ID of winning sequence to package
            agent_id: Agent who discovered this
            generation: Current generation
            skip_if_exists: If True, return existing package_id instead of creating duplicate
            
        Returns:
            package_id if created/exists, None if failed
        """
        # DEDUPLICATION CHECK: Don't create duplicate viral packages for same sequence
        if skip_if_exists:
            existing = self.db.execute_query(
                "SELECT package_id FROM viral_information_packages WHERE source_sequence_id = ? AND is_active = 1",
                (sequence_id,)
            )
            if existing:
                # Package already exists for this sequence - return existing ID
                # This prevents pollution from 1000x replays of the same sequence
                return existing[0]['package_id']
        
        # Get sequence data
        sequence = self.db.execute_query(
            "SELECT * FROM winning_sequences WHERE sequence_id = ?",
            (sequence_id,)
        )
        
        if not sequence:
            return None
        
        seq = sequence[0]
        
        # Create package
        package_id = f"viral_{uuid.uuid4().hex[:12]}"
        
        try:
            # ================================================================
            # CRITICAL FIX (2025-12-06): Generate meaningful meta_strategy_description
            # Analyze the winning sequence to describe WHAT strategy worked
            # ================================================================
            meta_strategy = self._generate_meta_strategy_description(
                seq['action_sequence'],
                seq.get('coordinate_sequence'),
                seq.get('level_number', 1)
            )
            
            self.db.execute_query("""
                INSERT INTO viral_information_packages (
                    package_id, package_name, package_type,
                    action_sequence, coordinate_pattern,
                    virulence, transmission_rate, mutation_rate,
                    discovery_generation, source_sequence_id, generation_discovered,
                    is_active, last_successful_use_generation, meta_strategy_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                package_id,
                f"Package_{seq['game_id'][:8]}_{generation}",
                'action_sequence',
                seq['action_sequence'],  # JSON array of actions
                seq['coordinate_sequence'],  # JSON array of coordinates
                0.5,  # Initial virulence
                0.3,  # Initial transmission rate
                0.05,  # Initial mutation rate
                generation,
                sequence_id,
                generation,
                True,  # is_active
                generation,
                meta_strategy  # Now has meaningful description
            ))
            
            # Phase 4.5: Capture emotional context during package creation
            if self.sensation_engine and agent_id:
                try:
                    # Get agent's emotional state when package was created
                    agent_result = self.db.execute_query(
                        "SELECT navigation_state, sensation_profile FROM agents WHERE agent_id = ?",
                        (agent_id,)
                    )
                    
                    if agent_result:
                        emotional_context = {
                            'creation_navigation_state': agent_result[0]['navigation_state'],
                            'creation_timestamp': datetime.now().isoformat(),
                            'successful_emotional_range': [
                                agent_result[0]['navigation_state'] - 0.3,  # Lower bound for compatibility
                                agent_result[0]['navigation_state'] + 0.3   # Upper bound for compatibility
                            ]
                        }
                        
                        # Store emotional context with the package
                        self.add_emotional_context_to_package(package_id, emotional_context)
                
                except Exception as e:
                    print(f"[VIRAL] Warning: Could not capture emotional context: {e}")
            
            # Auto-infect the discoverer
            self._infect_agent(agent_id, package_id, generation, 'discovery', None)
            
            return package_id
            
        except Exception as e:
            print(f"[VIRAL] Error creating package: {e}")
            return None
    
    def create_viral_package_from_operator(
        self,
        operator_id: str,
        operator_name: str,
        primitives: List[str],
        agent_id: str,
        generation: int,
        game_type: Optional[str] = None,
        level_number: Optional[int] = None
    ) -> Optional[str]:
        """
        Create a viral package from a synthesized CODS operator.
        
        This bridges the gap between CODS operator synthesis and viral distribution.
        When CODS creates a new composed operator, this packages it as a "virus"
        that can spread to other agents, teaching them to USE the operator.
        
        ADDED 2025-12-28: Fixes the Operator -> Viral distribution gap.
        
        Args:
            operator_id: ID of the composed operator
            operator_name: Human-readable name
            primitives: List of primitive names in the composition
            agent_id: Agent who triggered the synthesis
            generation: Current generation
            game_type: Optional game type this operator excels at
            level_number: Optional level number
            
        Returns:
            package_id if created, None if failed
        """
        # Check for existing package for this operator (deduplication)
        existing = self.db.execute_query(
            """SELECT package_id FROM viral_information_packages 
               WHERE package_type = 'operator' AND meta_strategy_description LIKE ?
               AND is_active = 1""",
            (f"%{operator_id}%",)
        )
        if existing:
            return existing[0]['package_id']
        
        package_id = f"viral_op_{uuid.uuid4().hex[:12]}"
        
        try:
            # Build meta strategy description
            primitives_str = " + ".join(primitives)
            meta_strategy = f"OPERATOR: {operator_name}. Composition: {primitives_str}. "
            if game_type:
                meta_strategy += f"Discovered for {game_type}"
                if level_number:
                    meta_strategy += f" L{level_number}"
                meta_strategy += ". "
            meta_strategy += f"operator_id={operator_id}"
            
            # Store the primitives as a pseudo action sequence for compatibility
            # Agents can use this to know which primitives to invoke
            primitives_json = json.dumps(primitives)
            
            self.db.execute_query("""
                INSERT INTO viral_information_packages (
                    package_id, package_name, package_type,
                    action_sequence, coordinate_pattern,
                    virulence, transmission_rate, mutation_rate,
                    discovery_generation, generation_discovered,
                    is_active, last_successful_use_generation, meta_strategy_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                package_id,
                f"Operator_{operator_name[:20]}_{generation}",
                'operator',  # NEW package type for operators
                primitives_json,  # Store primitives list instead of actions
                None,  # No coordinates for operators
                0.6,  # Higher virulence - operators are valuable
                0.4,  # Higher transmission - spread good operators
                0.02,  # Low mutation - operators should stay stable
                generation,
                generation,
                True,  # is_active
                generation,
                meta_strategy
            ))
            
            # Auto-infect the discoverer/synthesizer
            self._infect_agent(agent_id, package_id, generation, 'discovery', None)
            
            print(f"[VIRAL-OP] Created operator package: {operator_name} ({primitives_str})")
            
            return package_id
            
        except Exception as e:
            print(f"[VIRAL-OP] Error creating operator package: {e}")
            return None

    def _generate_meta_strategy_description(
        self,
        action_sequence: str,
        coordinate_sequence: Optional[str],
        level_number: int
    ) -> str:
        """
        Generate a meaningful meta-strategy description for a viral package.
        
        ADDED (2025-12-06): Viral packages need descriptions to be useful.
        Analyzes the winning action pattern to describe the strategy:
        - Dominant direction (up-focused, diagonal movement, etc.)
        - Key techniques (clicking, waiting, navigation)
        - Efficiency characteristics
        
        Returns:
            Descriptive strategy string for network learning
        """
        try:
            actions = json.loads(action_sequence) if isinstance(action_sequence, str) else action_sequence
        except:
            return f"Level {level_number} win sequence"
        
        if not actions:
            return f"Level {level_number} win sequence (empty)"
        
        from collections import Counter
        action_counts = Counter(actions)
        
        # Map action numbers to names
        action_names = {
            1: 'up', 2: 'down', 3: 'left', 4: 'right',
            5: 'wait', 6: 'click', 7: 'submit'
        }
        
        strategies = []
        
        # Identify dominant movement direction
        vertical = action_counts.get(1, 0) + action_counts.get(2, 0)  # up + down
        horizontal = action_counts.get(3, 0) + action_counts.get(4, 0)  # left + right
        
        if vertical > horizontal * 1.5:
            if action_counts.get(1, 0) > action_counts.get(2, 0):
                strategies.append("upward navigation")
            else:
                strategies.append("downward navigation")
        elif horizontal > vertical * 1.5:
            if action_counts.get(4, 0) > action_counts.get(3, 0):
                strategies.append("rightward navigation")
            else:
                strategies.append("leftward navigation")
        elif vertical > 0 and horizontal > 0:
            strategies.append("diagonal/mixed navigation")
        
        # Check for clicking strategy
        click_ratio = action_counts.get(6, 0) / len(actions)
        if click_ratio > 0.3:
            strategies.append("click-heavy interaction")
        elif click_ratio > 0.1:
            strategies.append("periodic clicking")
        
        # Check for waiting strategy
        wait_ratio = action_counts.get(5, 0) / len(actions)
        if wait_ratio > 0.2:
            strategies.append("timing-based (uses wait)")
        
        # Efficiency indicator
        if len(actions) < 20:
            strategies.append(f"efficient ({len(actions)} actions)")
        elif len(actions) > 100:
            strategies.append(f"complex ({len(actions)} actions)")
        
        # Combine into description
        if strategies:
            return f"L{level_number}: {', '.join(strategies)}"
        else:
            return f"L{level_number}: {len(actions)}-action sequence"
    
    def _infect_agent(self, 
                     agent_id: str, 
                     package_id: str,
                     generation: int,
                     source: str,
                     infected_by: Optional[str]):
        """
        Infect an agent with a viral package.
        
        Args:
            agent_id: Agent to infect
            package_id: Package to infect with
            generation: Current generation
            source: 'discovery', 'horizontal_transfer', 'inheritance', 'mutation'
            infected_by: Agent who spread it (if horizontal_transfer)
        """
        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO agent_viral_infections (
                    agent_id, package_id,
                    infection_generation, infection_source, infected_by_agent,
                    infection_strength, expression_level,
                    is_active, last_used_generation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id, package_id,
                generation, source, infected_by,
                0.7 if source == 'discovery' else 0.5,  # Discoverers express more strongly
                0.6 if source == 'discovery' else 0.4,
                True,
                generation
            ))
            
            # Update package total_infections count
            self.db.execute_query("""
                UPDATE viral_information_packages 
                SET total_infections = total_infections + 1,
                    active_infections = active_infections + 1
                WHERE package_id = ?
            """, (package_id,))
            
        except Exception as e:
            print(f"[VIRAL] Error infecting agent: {e}")
    
    def spread_viral_package(self,
                            package_id: str,
                            from_agent_id: str,
                            to_agent_id: str,
                            generation: int) -> bool:
        """
        Horizontally transfer a viral package from one agent to another.
        
        This is the "infection" mechanism - successful packages spread
        through the population like actual viruses.
        
        Args:
            package_id: Package to spread
            from_agent_id: Agent spreading the package
            to_agent_id: Agent receiving the package
            generation: Current generation
            
        Returns:
            True if infection successful, False if failed/already infected
        """
        # Check if already infected
        existing = self.db.execute_query("""
            SELECT * FROM agent_viral_infections
            WHERE agent_id = ? AND package_id = ? AND is_active = TRUE
        """, (to_agent_id, package_id))
        
        if existing:
            return False  # Already infected
        
        # Get package transmission rate
        package = self.db.execute_query(
            "SELECT transmission_rate FROM viral_information_packages WHERE package_id = ?",
            (package_id,)
        )
        
        if not package:
            return False
        
        transmission_rate = package[0]['transmission_rate']
        
        # Probabilistic infection based on transmission rate
        import random
        if random.random() > transmission_rate:
            return False  # Failed to transmit
        
        # Infect the target agent
        self._infect_agent(to_agent_id, package_id, generation, 'horizontal_transfer', from_agent_id)
        
        return True
    
    # ========================================================================
    # PARIAH CREATION (Negative Selection)
    # ========================================================================
    
    def create_pariah_from_failure(self,
                                   game_id: str,
                                   agent_id: str,
                                   failed_actions: List[int],
                                   failed_coordinates: List[Tuple[int, int]],
                                   final_score: float,
                                   generation: int,
                                   source_level_number: int = 1) -> Optional[str]:
        """
        Create a pariah (failure pattern) from a failed game.
        
        This extracts the failure pattern so the network can learn to avoid it.
        
        FIXED (2025-12-06): Now generates specific, actionable failure descriptions
        instead of generic "Failed with score X" messages. Pariahs are also marked
        as active and set to influence action selection.
        
        FIXED (2025-12-26): Added source_level_number for level-scoped pariah penalties.
        Pariahs from beaten levels apply weakly to frontier levels.
        
        Args:
            game_id: Game where failure occurred
            agent_id: Agent who failed
            failed_actions: Action sequence that failed
            failed_coordinates: Coordinate sequence that failed
            final_score: Final score (low = worse failure)
            generation: Current generation
            source_level_number: Level where failure occurred (for level-scoped penalties)
            
        Returns:
            pariah_id if created, None if failed
        """
        # Only create pariahs for severe failures (score < 1.0)
        if final_score >= 1.0:
            return None
        
        pariah_id = f"pariah_{uuid.uuid4().hex[:12]}"
        
        try:
            # Calculate toxicity based on how badly it failed
            toxicity = max(0.0, min(1.0, 1.0 - (final_score / 10.0)))  # 0 score = 1.0 toxicity
            
            # ================================================================
            # CRITICAL FIX (2025-12-06): Generate specific failure description
            # Analyze the action sequence to identify WHY it failed
            # ================================================================
            failure_description = self._analyze_failure_pattern(failed_actions, failed_coordinates, final_score)
            
            # Add source_level_number column if it doesn't exist (migration)
            try:
                self.db.execute_query("""
                    ALTER TABLE pariahs ADD COLUMN source_level_number INTEGER DEFAULT 1
                """)
                # Backfill existing pariahs using game's max completed level
                # Per user suggestion: "use game types top level completed as source_level_number"
                self.db.execute_query("""
                    UPDATE pariahs 
                    SET source_level_number = COALESCE(
                        (SELECT MAX(level_completions) 
                         FROM game_results 
                         WHERE game_id LIKE substr(pariahs.source_game_id, 1, 4) || '%'
                         AND level_completions > 0),
                        1
                    )
                    WHERE source_level_number IS NULL OR source_level_number = 1
                """)
            except Exception:
                pass  # Column already exists
            
            self.db.execute_query("""
                INSERT INTO pariahs (
                    pariah_id, pariah_name, pariah_type,
                    action_sequence, coordinate_pattern, failure_description,
                    toxicity, detection_difficulty, context_specificity,
                    trigger_count, avg_score_loss,
                    discovery_generation, source_game_id, source_agent_id, source_level_number,
                    is_active, last_triggered_generation, avoidance_success_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pariah_id,
                f"Pariah_{game_id[:8]}_L{source_level_number}_{generation}",
                'action_sequence',
                json.dumps(failed_actions),
                json.dumps(failed_coordinates),
                failure_description,  # Now specific instead of generic
                toxicity,
                0.3,  # Initial detection difficulty
                0.5,  # Initial context specificity
                1,  # trigger_count (this failure)
                10.0 - final_score,  # avg_score_loss
                generation,
                game_id,
                agent_id,
                source_level_number,  # NEW: Level where failure occurred
                True,  # is_active
                generation,
                0.0  # No avoidance data yet
            ))
            
            # Make discoverer aware of this pariah
            self._make_agent_aware_of_pariah(agent_id, pariah_id, generation, 'self_discovery', None)
            
            return pariah_id
            
        except Exception as e:
            print(f"[PARIAH] Error creating pariah: {e}")
            return None
    
    def _make_agent_aware_of_pariah(self,
                                    agent_id: str,
                                    pariah_id: str,
                                    generation: int,
                                    source: str,
                                    learned_from: Optional[str]):
        """
        Make an agent aware of a failure pattern.
        
        Args:
            agent_id: Agent to make aware
            pariah_id: Pariah they should know about
            generation: Current generation
            source: 'self_discovery', 'horizontal_transfer', 'inheritance'
            learned_from: Agent who taught them (if horizontal_transfer)
        """
        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO agent_pariah_awareness (
                    agent_id, pariah_id,
                    awareness_generation, awareness_source, learned_from_agent,
                    awareness_level, avoidance_priority,
                    is_active, last_encountered_generation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id, pariah_id,
                generation, source, learned_from,
                0.8 if source == 'self_discovery' else 0.6,  # Discoverers are more aware
                0.7 if source == 'self_discovery' else 0.5,
                True,
                generation
            ))
            
            # Update pariah awareness count
            self.db.execute_query("""
                UPDATE pariahs
                SET total_awareness = total_awareness + 1,
                    active_awareness = active_awareness + 1
                WHERE pariah_id = ?
            """, (pariah_id,))
            
        except Exception as e:
            print(f"[PARIAH] Error making agent aware: {e}")
    
    def spread_pariah_awareness(self,
                               pariah_id: str,
                               from_agent_id: str,
                               to_agent_id: str,
                               generation: int) -> bool:
        """
        Spread pariah awareness from one agent to another (horizontal transfer).
        
        Like warning others about danger - "Don't try this, it failed for me!"
        
        Args:
            pariah_id: Pariah to warn about
            from_agent_id: Agent spreading awareness
            to_agent_id: Agent learning about pariah
            generation: Current generation
            
        Returns:
            True if awareness spread, False if already aware or failed
        """
        # Check if already aware
        existing = self.db.execute_query("""
            SELECT * FROM agent_pariah_awareness
            WHERE agent_id = ? AND pariah_id = ? AND is_active = TRUE
        """, (to_agent_id, pariah_id))
        
        if existing:
            return False  # Already aware
        
        # Make agent aware
        self._make_agent_aware_of_pariah(to_agent_id, pariah_id, generation, 'horizontal_transfer', from_agent_id)
        
        return True
    
    # ========================================================================
    # FRONTIER EXPLORATION PACKAGES (Temporary - auto-cleaned when sequences exist)
    # ========================================================================
    
    def create_frontier_exploration_package(
        self,
        game_type: str,
        level_number: int,
        agent_id: str,
        action_traces: List[Dict],
        final_score: float,
        generation: int
    ) -> Optional[str]:
        """
        Create a temporary viral package from frontier exploration.
        
        These packages capture partial progress at frontier levels where no
        winning sequences exist yet. They help future agents reach the frontier
        faster by sharing what actions were tried.
        
        IMPORTANT: These are TEMPORARY and will be auto-cleaned once enough
        winning sequences exist for this level (see cleanup_obsolete_frontier_packages).
        
        Args:
            game_type: Game type (e.g., 'as66')
            level_number: The frontier level number
            agent_id: Agent who explored
            action_traces: List of action traces from frontier exploration
            final_score: Final score achieved
            generation: Current generation
            
        Returns:
            package_id if created, None if failed
        """
        package_id = f"frontier_{uuid.uuid4().hex[:12]}"
        
        try:
            # Extract action sequence from traces
            actions = []
            coords = []
            for trace in action_traces:
                action_type = trace.get('action_type', '')
                if isinstance(action_type, str) and action_type.startswith('ACTION'):
                    try:
                        actions.append(int(action_type.replace('ACTION', '')))
                    except:
                        pass
                if trace.get('coordinates'):
                    try:
                        coord = json.loads(trace['coordinates']) if isinstance(trace['coordinates'], str) else trace['coordinates']
                        coords.append(coord)
                    except:
                        pass
            
            if not actions:
                return None
            
            # Generate meta-strategy description
            meta_strategy = f"Frontier L{level_number} exploration: {len(actions)} actions tried. "
            
            # Analyze action distribution
            from collections import Counter
            action_counts = Counter(actions)
            dominant = action_counts.most_common(1)[0] if action_counts else (0, 0)
            action_names = {1: 'up', 2: 'down', 3: 'left', 4: 'right', 5: 'toggle', 6: 'click', 7: 'undo'}
            meta_strategy += f"Dominant: {action_names.get(dominant[0], 'unknown')} ({dominant[1]}x). "
            meta_strategy += f"Score at failure: {final_score:.1f}"
            
            self.db.execute_query("""
                INSERT INTO viral_information_packages (
                    package_id, package_name, package_type,
                    action_sequence, coordinate_pattern,
                    virulence, transmission_rate, mutation_rate,
                    discovery_generation, generation_discovered,
                    is_active, is_frontier_temp, frontier_level, frontier_game_type,
                    meta_strategy_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                package_id,
                f"Frontier_{game_type}_L{level_number}_{generation}",
                'frontier_exploration',
                json.dumps(actions),
                json.dumps(coords) if coords else None,
                0.3,  # Lower virulence (temporary package)
                0.2,  # Lower transmission
                0.1,  # Higher mutation (encourage variation)
                generation,
                generation,
                True,  # is_active
                True,  # is_frontier_temp - FLAG FOR CLEANUP
                level_number,
                game_type,
                meta_strategy
            ))
            
            return package_id
            
        except Exception as e:
            print(f"[FRONTIER] Error creating frontier package: {e}")
            return None
    
    def cleanup_obsolete_frontier_packages(self, min_sequences_to_cleanup: int = 3) -> int:
        """
        Clean up frontier exploration packages that are no longer needed.
        
        Called periodically (e.g., start of each generation) to remove temporary
        frontier packages once real winning sequences exist for that level.
        
        Args:
            min_sequences_to_cleanup: Minimum active sequences required before cleanup
            
        Returns:
            Number of packages cleaned up
        """
        try:
            # Find frontier packages where sequences now exist
            obsolete = self.db.execute_query("""
                SELECT vip.package_id, vip.frontier_game_type, vip.frontier_level
                FROM viral_information_packages vip
                WHERE vip.is_frontier_temp = 1 AND vip.is_active = 1
                AND EXISTS (
                    SELECT 1 FROM winning_sequences ws
                    WHERE ws.game_id LIKE vip.frontier_game_type || '-%'
                    AND ws.level_number = vip.frontier_level
                    AND ws.is_active = 1
                    GROUP BY ws.level_number
                    HAVING COUNT(*) >= ?
                )
            """, (min_sequences_to_cleanup,))
            
            # ALSO find useless packages: retrieved 10+ times but 0 improvements
            useless = self.db.execute_query("""
                SELECT package_id, frontier_game_type, frontier_level, retrieval_count, improvement_count
                FROM viral_information_packages
                WHERE is_frontier_temp = 1 AND is_active = 1
                  AND retrieval_count >= 10
                  AND improvement_count = 0
            """)
            
            if not obsolete and not useless:
                return 0
            
            cleaned = 0
            
            # Clean obsolete (sequences exist)
            for pkg in (obsolete or []):
                self.db.execute_query("""
                    UPDATE viral_information_packages
                    SET is_active = 0, deactivated_reason = 'sequences_exist'
                    WHERE package_id = ?
                """, (pkg['package_id'],))
                cleaned += 1
                print(f"[CLEANUP] Deactivated frontier package {pkg['package_id'][:12]} "
                      f"for {pkg['frontier_game_type']} L{pkg['frontier_level']} (sequences exist)")
            
            # Clean useless (retrieved but never helped)
            for pkg in (useless or []):
                self.db.execute_query("""
                    UPDATE viral_information_packages
                    SET is_active = 0, deactivated_reason = 'useless_no_improvement'
                    WHERE package_id = ?
                """, (pkg['package_id'],))
                cleaned += 1
                print(f"[CLEANUP] Deactivated useless frontier package {pkg['package_id'][:12]} "
                      f"(retrieved {pkg['retrieval_count']}x, 0 improvements)")
            
            return cleaned
            
        except Exception as e:
            print(f"[CLEANUP] Error cleaning frontier packages: {e}")
            return 0
    
    def track_package_retrieval(self, package_id: str, generation: int) -> None:
        """Track that a package was retrieved for use."""
        try:
            self.db.execute_query("""
                UPDATE viral_information_packages
                SET retrieval_count = COALESCE(retrieval_count, 0) + 1,
                    last_retrieval_generation = ?
                WHERE package_id = ?
            """, (generation, package_id))
        except Exception:
            pass
    
    def track_package_improvement(self, package_id: str) -> None:
        """Track that a package retrieval led to score improvement."""
        try:
            self.db.execute_query("""
                UPDATE viral_information_packages
                SET improvement_count = COALESCE(improvement_count, 0) + 1
                WHERE package_id = ?
            """, (package_id,))
        except Exception:
            pass
    
    def track_agent_packages_improvement(self, agent_id: str) -> int:
        """
        Track improvement for all packages an agent carries.
        
        Called when agent completes a level - all packages they carry
        contributed to that success.
        
        Args:
            agent_id: The agent who just succeeded
            
        Returns:
            Number of packages that received improvement tracking
        """
        try:
            # Get all active packages for this agent
            infections = self.db.execute_query("""
                SELECT package_id FROM agent_viral_infections
                WHERE agent_id = ? AND is_active = TRUE
            """, (agent_id,))
            
            if not infections:
                return 0
            
            # Track improvement for each package
            for infection in infections:
                self.track_package_improvement(infection['package_id'])
            
            return len(infections)
        except Exception:
            return 0
    
    # ========================================================================
    # ACTION SELECTION (Bidirectional Influence)
    # ========================================================================
    
    def _analyze_failure_pattern(
        self,
        failed_actions: List[int],
        failed_coordinates: List[Tuple[int, int]],
        final_score: float
    ) -> str:
        """
        Analyze a failure to generate a specific, actionable description.
        
        ADDED (2025-12-06): Pariahs need specific descriptions to be useful.
        This analyzes the action pattern to identify common failure modes:
        - Oscillation (repeated back-and-forth)
        - Edge trapping (stuck at boundaries)
        - Inefficiency (too many actions without progress)
        - Specific action overuse
        
        Returns:
            Specific failure description for network learning
        """
        if not failed_actions:
            return f"Empty action sequence, score {final_score:.2f}"
        
        descriptions = []
        
        # Detect oscillation (e.g., up-down-up-down or left-right-left-right)
        oscillation_count = 0
        for i in range(len(failed_actions) - 2):
            if failed_actions[i] == failed_actions[i + 2] and failed_actions[i] != failed_actions[i + 1]:
                oscillation_count += 1
        
        if oscillation_count >= 3:
            descriptions.append(f"oscillation detected ({oscillation_count} reversals)")
        
        # Detect action overuse (>40% same action)
        from collections import Counter
        action_counts = Counter(failed_actions)
        most_common_action, most_common_count = action_counts.most_common(1)[0]
        if most_common_count / len(failed_actions) > 0.4:
            action_names = {1: 'up', 2: 'down', 3: 'left', 4: 'right', 5: 'wait', 6: 'click', 7: 'submit'}
            action_name = action_names.get(most_common_action, f'action{most_common_action}')
            descriptions.append(f"overused {action_name} ({most_common_count}/{len(failed_actions)} actions)")
        
        # Detect edge trapping from coordinates
        if failed_coordinates:
            x_coords = [c[0] for c in failed_coordinates if c]
            y_coords = [c[1] for c in failed_coordinates if c]
            
            if x_coords and y_coords:
                # Check if stuck at edges (0 or max values repeated)
                edge_x = sum(1 for x in x_coords if x <= 1 or x >= 28) / len(x_coords)
                edge_y = sum(1 for y in y_coords if y <= 1 or y >= 28) / len(y_coords)
                
                if edge_x > 0.5:
                    if sum(1 for x in x_coords if x <= 1) > sum(1 for x in x_coords if x >= 28):
                        descriptions.append("trapped at left edge")
                    else:
                        descriptions.append("trapped at right edge")
                if edge_y > 0.5:
                    if sum(1 for y in y_coords if y <= 1) > sum(1 for y in y_coords if y >= 28):
                        descriptions.append("trapped at top edge")
                    else:
                        descriptions.append("trapped at bottom edge")
        
        # Detect inefficiency (many actions, no progress)
        if len(failed_actions) > 50 and final_score < 0.5:
            descriptions.append(f"inefficient ({len(failed_actions)} actions for score {final_score:.1f})")
        
        # Combine descriptions or use default
        if descriptions:
            return f"FAILURE: {'; '.join(descriptions)}"
        else:
            return f"Unknown failure pattern, score {final_score:.2f}, {len(failed_actions)} actions"
    
    def get_package_action_weights(self, agent_id: str, generation: int = 0, track_retrieval: bool = True) -> Dict[int, float]:
        """
        Get action weights from viral packages this agent carries.
        
        Phase 4.5 Enhancement: Includes emotional context compatibility.
        Packages with emotional context matching agent's current state get boosted weights.
        
        Also tracks package retrieval for usefulness metrics (Gap 5/6 fix).
        
        Args:
            agent_id: The agent to get weights for
            generation: Current generation for tracking
            track_retrieval: Whether to track this retrieval (default True)
        
        Returns:
            Dict mapping action_id -> weight (higher = prefer this action)
        """
        # Get all active packages for this agent
        infections = self.db.execute_query("""
            SELECT 
                vi.package_id,
                vi.infection_strength,
                vi.expression_level,
                vp.action_sequence,
                vp.success_rate,
                vi.total_uses
            FROM agent_viral_infections vi
            JOIN viral_information_packages vp ON vi.package_id = vp.package_id
            WHERE vi.agent_id = ? AND vi.is_active = TRUE AND vp.is_active = TRUE
        """, (agent_id,))
        
        action_weights = {}
        
        # Track which packages were retrieved (Gap 5 fix: wire up tracking)
        # FIXED 2025-12-28: Removed generation > 0 guard - was preventing ALL tracking
        if track_retrieval and infections:
            for infection in infections:
                self.track_package_retrieval(infection['package_id'], generation)
        
        # Phase 4.5: Get agent's current emotional state for compatibility
        agent_navigation_state = 0.0
        if self.sensation_engine:
            try:
                agent_result = self.db.execute_query(
                    "SELECT navigation_state FROM agents WHERE agent_id = ?",
                    (agent_id,)
                )
                if agent_result:
                    agent_navigation_state = agent_result[0]['navigation_state']
            except Exception:
                pass  # Continue without emotional enhancement if error

        for infection in infections:
            # Parse action sequence
            try:
                actions = json.loads(infection['action_sequence'])
                
                # Use success_rate if available, otherwise use baseline of 0.5 for untested packages
                # This allows new packages to be tried before they have usage data
                success_rate = infection['success_rate'] if infection['total_uses'] > 0 else 0.5
                
                # Base weight calculation
                base_weight = (infection['infection_strength'] * 
                              infection['expression_level'] * 
                              success_rate)
                
                # Phase 4.5: Apply emotional context multiplier
                emotional_multiplier = self._calculate_emotional_compatibility(
                    infection['package_id'], agent_navigation_state
                ) if self.sensation_engine else 1.0
                
                # Final weight with emotional enhancement
                weight = base_weight * emotional_multiplier
                
                for action in actions:
                    action_weights[action] = action_weights.get(action, 0.0) + weight
                    
            except (json.JSONDecodeError, TypeError):
                continue
        
        return action_weights
    
    def get_pariah_action_penalties(self, agent_id: str, 
                                     game_id: str = None,
                                     current_level: int = None) -> Dict[int, float]:
        """
        Get action penalties from pariahs this agent is aware of.
        
        FIXED (2025-12-26): Now applies level-aware decay.
        Pariahs from beaten levels apply weakly to frontier levels.
        
        Level Decay Logic:
        - Same level as pariah source: 100% penalty
        - Adjacent level (+/- 1): 40% penalty
        - 2+ levels away: 15% penalty
        - On frontier AND pariah from beaten level: 5% penalty (just a hint)
        
        Args:
            agent_id: Agent to get penalties for
            game_id: Current game (for level context)
            current_level: Current level number (for decay calculation)
        
        Returns:
            Dict mapping action_id -> penalty (higher = avoid this action more)
        """
        # Get max beaten level for this game (to detect frontier)
        max_beaten_level = 0
        if game_id:
            try:
                result = self.db.execute_query("""
                    SELECT MAX(level_completions) as max_level
                    FROM game_results 
                    WHERE game_id LIKE ? AND level_completions > 0
                """, (f"{game_id[:4]}%",))
                if result and result[0].get('max_level'):
                    max_beaten_level = result[0]['max_level']
            except Exception:
                pass
        
        is_frontier = current_level is not None and current_level > max_beaten_level
        
        # Get all pariahs this agent is aware of (with level info)
        awareness = self.db.execute_query("""
            SELECT 
                pa.pariah_id,
                pa.awareness_level,
                pa.avoidance_priority,
                p.action_sequence,
                p.toxicity,
                p.source_game_id,
                COALESCE(p.source_level_number, 1) as source_level_number
            FROM agent_pariah_awareness pa
            JOIN pariahs p ON pa.pariah_id = p.pariah_id
            WHERE pa.agent_id = ? AND pa.is_active = TRUE AND p.is_active = TRUE
        """, (agent_id,))
        
        action_penalties = {}
        
        for aware in awareness:
            # Parse action sequence
            try:
                actions = json.loads(aware['action_sequence'])
                
                # Base penalty from awareness, priority, and toxicity
                base_penalty = (aware['awareness_level'] * 
                               aware['avoidance_priority'] * 
                               aware['toxicity'])
                
                # ============================================================
                # LEVEL-AWARE DECAY (2025-12-26)
                # Pariahs from beaten levels shouldn't block frontier exploration
                # ============================================================
                level_decay = 1.0  # Default: full penalty
                
                pariah_game_id = aware.get('source_game_id', '')
                pariah_level = aware.get('source_level_number', 1)
                
                # Only apply level decay if we have context AND same game
                if current_level is not None and game_id and pariah_game_id:
                    # Check if pariah is from same game type
                    same_game = (game_id[:4] == pariah_game_id[:4])
                    
                    if same_game:
                        level_distance = abs(current_level - pariah_level)
                        
                        if is_frontier and pariah_level <= max_beaten_level:
                            # On frontier, pariahs from beaten territory = very weak
                            level_decay = 0.05  # 5% - just a faint hint
                        elif level_distance == 0:
                            # Same level - full penalty
                            level_decay = 1.0
                        elif level_distance == 1:
                            # Adjacent level - moderate decay
                            level_decay = 0.4
                        else:
                            # 2+ levels away - heavy decay
                            level_decay = 0.15
                    else:
                        # Different game entirely - weak cross-game hint
                        level_decay = 0.1
                
                # Apply decayed penalty
                final_penalty = base_penalty * level_decay
                
                # FIX (2025-01-XX): Use SET of unique actions to avoid over-penalizing
                # sequences like [6,6,6...6] 100 times which was adding 100x penalty!
                # The penalty should be "this sequence contains action 6" not 
                # "this sequence has 100 action 6s so 100x more bad"
                unique_actions = set(actions)
                for action in unique_actions:
                    action_penalties[action] = action_penalties.get(action, 0.0) + final_penalty
                    
            except (json.JSONDecodeError, TypeError):
                continue
        
        # ====================================================================
        # ESSENTIAL ACTION PROTECTION (2025-01-XX)
        # If an action appears in winning sequences for this game, reduce penalty
        # This prevents blocking actions that are CORE to winning the game
        # Example: VC33 uses ACTION6 as the primary mechanic - can't penalize it
        # ====================================================================
        if game_id and action_penalties:
            try:
                # Get winning sequences for this game type
                winning_seqs = self.db.execute_query("""
                    SELECT action_sequence 
                    FROM winning_sequences 
                    WHERE game_id LIKE ? AND is_active = 1
                    LIMIT 20
                """, (f"{game_id[:4]}%",))
                
                if winning_seqs:
                    # Count action frequency in winning sequences
                    action_in_wins = {}
                    total_wins = len(winning_seqs)
                    
                    for seq in winning_seqs:
                        try:
                            actions = json.loads(seq['action_sequence'])
                            unique = set(actions)
                            for a in unique:
                                action_in_wins[a] = action_in_wins.get(a, 0) + 1
                        except:
                            continue
                    
                    # If action appears in >50% of winning sequences, reduce penalty by 90%
                    for action, penalty in list(action_penalties.items()):
                        win_count = action_in_wins.get(action, 0)
                        if total_wins > 0 and win_count / total_wins > 0.5:
                            # This action is ESSENTIAL - almost always in wins
                            action_penalties[action] = penalty * 0.1  # 90% reduction
                        elif total_wins > 0 and win_count / total_wins > 0.25:
                            # Action appears often in wins - moderate reduction
                            action_penalties[action] = penalty * 0.3  # 70% reduction
                            
            except Exception as e:
                pass  # If we can't check wins, keep penalties as-is
        
        return action_penalties
    
    # ========================================================================
    # USAGE TRACKING (Critical for Phase 3 to work!)
    # ========================================================================
    
    def record_package_usage(self, agent_id: str, package_id: str, 
                            success: bool, score_change: float, generation: int):
        """
        Record that an agent used a viral package and track its effectiveness.
        
        This is CRITICAL for Phase 3 - without usage tracking, success_rate stays 0!
        
        Args:
            agent_id: Agent that used the package
            package_id: Package that was used
            success: Whether the package led to success
            score_change: Score change from using this package
            generation: Current generation
        """
        # Update infection usage stats
        self.db.execute_query("""
            UPDATE agent_viral_infections
            SET total_uses = total_uses + 1,
                success_count = success_count + ?,
                failure_count = failure_count + ?,
                avg_score_boost = ((avg_score_boost * total_uses) + ?) / (total_uses + 1),
                last_used_generation = ?
            WHERE agent_id = ? AND package_id = ?
        """, (
            1 if success else 0,
            0 if success else 1,
            score_change,
            generation,
            agent_id,
            package_id
        ))
        
        # Update package-level stats
        self.db.execute_query("""
            UPDATE viral_information_packages
            SET total_infections = (
                    SELECT COUNT(*) FROM agent_viral_infections 
                    WHERE package_id = ? AND is_active = TRUE
                ),
                active_infections = (
                    SELECT COUNT(*) FROM agent_viral_infections
                    WHERE package_id = ? AND is_active = TRUE 
                    AND last_used_generation >= ? - 5
                ),
                success_rate = (
                    SELECT CAST(SUM(success_count) AS REAL) / 
                           NULLIF(SUM(total_uses), 0)
                    FROM agent_viral_infections
                    WHERE package_id = ?
                ),
                avg_score_contribution = (
                    SELECT AVG(avg_score_boost)
                    FROM agent_viral_infections
                    WHERE package_id = ? AND total_uses > 0
                ),
                last_successful_use_generation = CASE WHEN ? THEN ? ELSE last_successful_use_generation END
            WHERE package_id = ?
        """, (
            package_id,
            package_id,
            generation,
            package_id,
            package_id,
            success,
            generation,
            package_id
        ))
    
    # ========================================================================
    # PACKAGE/PARIAH MANAGEMENT
    # ========================================================================
    
    def check_package_obsolescence(self, generation: int, threshold_generations: int = 20):
        """
        Check if any viral packages have become obsolete.
        
        Packages that haven't succeeded in threshold_generations are marked obsolete.
        """
        self.db.execute_query("""
            UPDATE viral_information_packages
            SET obsolescence_score = 1.0,
                is_active = FALSE
            WHERE last_successful_use_generation < ? - ?
            AND is_active = TRUE
        """, (generation, threshold_generations))
    
    def check_pariah_obsolescence(self, generation: int, threshold_generations: int = 30):
        """
        Check if any pariahs have become obsolete.
        
        CRITICAL FIX: Decay runs FIRST on ALL pariahs, then obsolescence check runs AFTER.
        Per agi_unified_theory.md: "Forgetting is not a bug - it's essential for intelligence."
        
        Pariahs are only marked obsolete if:
        1. Toxicity has decayed to minimum (0.1) AND
        2. Not triggered in threshold_generations (50+ gens)
        
        Low-toxicity pariahs remain ACTIVE to provide weak warnings.
        """
        # STEP 1: Apply toxicity decay FIRST to ALL pariahs (active or not)
        self.decay_pariah_toxicity(generation)
        
        # STEP 2: Reactivate decayed pariahs that were incorrectly marked inactive
        # Pariahs with toxicity > min should stay active for weak warnings
        reactivated = self.db.execute_query("""
            UPDATE pariahs
            SET is_active = TRUE, obsolescence_score = 0.0
            WHERE is_active = FALSE 
            AND toxicity > 0.15
            RETURNING pariah_id
        """)
        if reactivated:
            print(f"[PARIAH] Reactivated {len(reactivated)} previously-obsolete pariahs")
        
        # STEP 3: Only mark truly obsolete pariahs (min toxicity AND very old)
        # Increased threshold to 50 generations - give more time
        self.db.execute_query("""
            UPDATE pariahs
            SET obsolescence_score = 1.0,
                is_active = FALSE
            WHERE last_triggered_generation < ? - 50
            AND toxicity <= 0.15
            AND is_active = TRUE
        """, (generation,))
    
    def decay_pariah_toxicity(self, generation: int, decay_rate: float = 0.03, min_toxicity: float = 0.1):
        """
        Apply relevance decay to pariah toxicity.
        
        Philosophy (from agi_unified_theory.md):
        "Forgetting is not a bug - it's essential for intelligence."
        Pariahs should fade naturally if not re-validated by newer generations.
        
        FIXED: Now operates on ALL pariahs, not just active ones.
        This ensures pariahs decay properly before obsolescence check.
        
        Decay Formula (exponential decay):
        new_toxicity = current_toxicity * decay_factor
        where decay_factor = max(0.3, 1.0 - decay_rate * generations_since_trigger)
        
        Args:
            generation: Current generation
            decay_rate: How fast toxicity decays per generation (default 3% - slower decay)
            min_toxicity: Minimum toxicity floor to maintain some warning (default 0.1)
        """
        try:
            # FIXED: Operate on ALL pariahs, not just active ones
            # This ensures decay happens before obsolescence marking
            pariahs = self.db.execute_query("""
                SELECT pariah_id, toxicity, discovery_generation, 
                       COALESCE(last_triggered_generation, discovery_generation) as last_trigger
                FROM pariahs
                WHERE toxicity > ?
            """, (min_toxicity,))
            
            if not pariahs:
                return
            
            decayed_count = 0
            for p in pariahs:
                last_trigger = p['last_trigger'] or p['discovery_generation'] or 0
                generations_since_trigger = max(0, generation - last_trigger)
                
                # Apply decay based on age
                # FIXED: Cap at 30 generations to prevent over-decay
                decay_factor = 1.0 - (decay_rate * min(generations_since_trigger, 30))
                decay_factor = max(0.3, decay_factor)  # Floor at 30% of original
                
                new_toxicity = max(min_toxicity, p['toxicity'] * decay_factor)
                
                # Only update if toxicity actually changed significantly
                if abs(new_toxicity - p['toxicity']) > 0.005:
                    self.db.execute_query("""
                        UPDATE pariahs 
                        SET toxicity = ?
                        WHERE pariah_id = ?
                    """, (new_toxicity, p['pariah_id']))
                    decayed_count += 1
            
            if decayed_count > 0:
                print(f"[PARIAH] Decayed toxicity for {decayed_count} pariahs (gen {generation})")
                
        except Exception as e:
            print(f"[PARIAH] Error in toxicity decay: {e}")
    
    def get_role_adjusted_pariah_penalties(
        self, 
        agent_id: str, 
        agent_role: str = 'generalist',
        game_id: str = None,
        level_number: int = None
    ) -> Dict[int, float]:
        """
        Get pariah penalties adjusted for agent role (pariah tolerance).
        
        Per Master Ruleset: 
        - Exploiters and Optimizers should have immunity/tolerance to pariahs
        - This prevents analysis paralysis on well-explored games
        
        Role Tolerance Levels:
        - exploiter: 0.8 (80% pariah penalty ignored)
        - optimizer: 0.6 (60% penalty ignored) 
        - pioneer: 0.3 (30% penalty ignored - still cautious on frontier)
        - generalist: 0.0 (full penalty applied)
        
        Args:
            agent_id: Agent to get penalties for
            agent_role: Agent's current role
            game_id: Optional - for network paralysis boost
            level_number: Optional - for level-specific paralysis detection
            
        Returns:
            Dict mapping action_id -> adjusted_penalty
        """
        # Role-based pariah tolerance
        ROLE_TOLERANCE = {
            'exploiter': 0.8,   # Nearly immune - meant to break through
            'optimizer': 0.6,   # Significant immunity - refining known paths
            'pioneer': 0.3,     # Some tolerance - exploring frontier
            'generalist': 0.0   # Full sensitivity - maintains network wisdom
        }
        
        base_tolerance = ROLE_TOLERANCE.get(agent_role.lower(), 0.0)
        
        # Check for network-level paralysis on this game/level
        paralysis_boost = 0.0
        if game_id and level_number:
            paralysis_boost = self._detect_network_paralysis(game_id, level_number)
        
        # Combined tolerance (capped at 0.95 - always some caution)
        final_tolerance = min(0.95, base_tolerance + paralysis_boost)
        
        # Get base pariah penalties with level-aware decay
        base_penalties = self.get_pariah_action_penalties(agent_id, game_id, level_number)
        
        # Apply tolerance reduction
        adjusted_penalties = {}
        for action, penalty in base_penalties.items():
            adjusted_penalties[action] = penalty * (1.0 - final_tolerance)
        
        return adjusted_penalties
    
    def _detect_network_paralysis(self, game_id: str, level_number: int, 
                                   lookback_generations: int = 5,
                                   frozen_threshold: int = 5) -> float:
        """
        Detect if the network is experiencing paralysis on a specific game/level.
        
        If multiple agents are getting stuck ("frozen state") on the same level,
        temporarily boost pariah tolerance to encourage breakthrough attempts.
        
        Args:
            game_id: Game to check
            level_number: Level to check
            lookback_generations: How many generations to look back
            frozen_threshold: Number of frozen failures to trigger boost
            
        Returns:
            Paralysis boost (0.0 to 0.4) to add to role tolerance
        """
        try:
            # Get current generation
            gen_result = self.db.execute_query(
                "SELECT MAX(generation) as max_gen FROM agents WHERE is_active = 1"
            )
            current_gen = gen_result[0]['max_gen'] if gen_result else 0
            
            # Count recent frozen state failures on this game
            # Use game_results with low scores and specific level
            frozen_count = self.db.execute_query("""
                SELECT COUNT(*) as cnt
                FROM game_results
                WHERE game_id LIKE ? || '%'
                AND level_completions = ?
                AND final_score <= 1.0
                AND created_at >= datetime('now', '-24 hours')
            """, (game_id[:4], level_number))
            
            if not frozen_count:
                return 0.0
            
            count = frozen_count[0]['cnt'] or 0
            
            if count >= frozen_threshold:
                # Network paralysis detected - boost tolerance proportionally
                # Max boost of 0.4 when 15+ agents stuck
                boost = min(0.4, (count - frozen_threshold) * 0.05 + 0.1)
                print(f"[PARALYSIS] Detected on {game_id[:8]} L{level_number}: "
                      f"{count} frozen failures. Boosting pariah tolerance by {boost:.2f}")
                return boost
            
            return 0.0
            
        except Exception as e:
            print(f"[PARALYSIS] Detection error: {e}")
            return 0.0
    
    def get_top_packages(self, limit: int = 10) -> List[Dict]:
        """Get top performing viral packages by success rate."""
        return self.db.execute_query("""
            SELECT package_id, package_name, package_type,
                   success_rate, avg_score_contribution,
                   total_infections, active_infections,
                   generation_discovered
            FROM viral_information_packages
            WHERE is_active = TRUE
            ORDER BY success_rate DESC, total_infections DESC
            LIMIT ?
        """, (limit,))
    
    def get_top_pariahs(self, limit: int = 10) -> List[Dict]:
        """Get most toxic pariahs by trigger count and toxicity."""
        return self.db.execute_query("""
            SELECT pariah_id, pariah_name, pariah_type,
                   toxicity, trigger_count, avg_score_loss,
                   total_awareness, active_awareness,
                   avoidance_success_rate, discovery_generation
            FROM pariahs
            WHERE is_active = TRUE
            ORDER BY toxicity DESC, trigger_count DESC
            LIMIT ?
        """, (limit,))
    
    def cleanup_obsolete_pariahs(self, current_generation: int) -> int:
        """
        Soft-retire pariahs that are no longer valid traps.
        
        A pariah should be retired when:
        1. High avoidance success rate (90%+) - agents easily avoid it, not a real trap
        2. Very old without recent triggers (50+ generations stale)
        3. Only triggered once (single failure, not a pattern)
        
        SOFT RETIREMENT: We don't delete, just deactivate (is_active = FALSE).
        This preserves history while removing from active queries.
        
        Returns:
            Number of pariahs soft-retired
        """
        try:
            retired = 0
            
            # 1. High avoidance success = not a real trap
            high_avoidance = self.db.execute_query("""
                SELECT pariah_id FROM pariahs
                WHERE is_active = TRUE
                  AND avoidance_success_rate >= 0.9
                  AND total_awareness >= 5
            """)
            for p in (high_avoidance or []):
                self.db.execute_query("""
                    UPDATE pariahs SET is_active = FALSE, obsolescence_score = 1.0
                    WHERE pariah_id = ?
                """, (p['pariah_id'],))
                retired += 1
            
            # 2. Stale pariahs (50+ generations without trigger)
            stale_threshold = current_generation - 50
            stale = self.db.execute_query("""
                SELECT pariah_id FROM pariahs
                WHERE is_active = TRUE
                  AND last_triggered_generation < ?
                  AND discovery_generation < ?
            """, (stale_threshold, stale_threshold))
            for p in (stale or []):
                self.db.execute_query("""
                    UPDATE pariahs SET is_active = FALSE, obsolescence_score = 0.8
                    WHERE pariah_id = ?
                """, (p['pariah_id'],))
                retired += 1
            
            # 3. Single-trigger pariahs older than 20 generations (not a pattern, just noise)
            noise_threshold = current_generation - 20
            noise = self.db.execute_query("""
                SELECT pariah_id FROM pariahs
                WHERE is_active = TRUE
                  AND trigger_count <= 1
                  AND discovery_generation < ?
            """, (noise_threshold,))
            for p in (noise or []):
                self.db.execute_query("""
                    UPDATE pariahs SET is_active = FALSE, obsolescence_score = 0.5
                    WHERE pariah_id = ?
                """, (p['pariah_id'],))
                retired += 1
            
            if retired > 0:
                print(f"[CLEANUP] Soft-retired {retired} obsolete pariahs")
            
            return retired
            
        except Exception as e:
            print(f"[CLEANUP] Error retiring pariahs: {e}")
            return 0

    # Phase 4.5: Emotional compatibility methods
    
    def _calculate_emotional_compatibility(self, package_id: str, agent_navigation_state: float) -> float:
        """
        Calculate how compatible a viral package is with agent's current emotional state.
        
        Returns multiplier: 1.0 = neutral, >1.0 = boost, <1.0 = reduce
        """
        if not self.sensation_engine:
            return 1.0  # No emotional enhancement if sensation engine unavailable
        
        try:
            # Check if this package has emotional context metadata
            package_emotion = self._get_package_emotional_context(package_id)
            
            if package_emotion is None:
                return 1.0  # No emotional context, no boost or penalty
            
            # Calculate compatibility based on emotional distance
            emotional_distance = abs(agent_navigation_state - package_emotion)
            
            # Compatibility decreases with emotional distance
            # Close emotions get boost (up to 1.5x), distant emotions get penalty (down to 0.5x)
            if emotional_distance < 0.2:  # Very compatible
                return 1.4
            elif emotional_distance < 0.4:  # Somewhat compatible
                return 1.2
            elif emotional_distance < 0.6:  # Neutral
                return 1.0
            elif emotional_distance < 0.8:  # Somewhat incompatible
                return 0.8
            else:  # Very incompatible
                return 0.6
        
        except Exception:
            return 1.0  # Safe fallback
    
    def _get_package_emotional_context(self, package_id: str) -> Optional[float]:
        """
        Get the emotional context associated with a viral package.
        
        Returns the navigation state when this package was successful.
        """
        try:
            # Get package metadata containing emotional context
            result = self.db.execute_query(
                "SELECT package_metadata FROM viral_information_packages WHERE package_id = ?",
                (package_id,)
            )
            
            if not result or not result[0]['package_metadata']:
                return None
            
            # Parse emotional context
            emotional_context = json.loads(result[0]['package_metadata'])
            return emotional_context.get('creation_navigation_state')
            
        except Exception:
            return None
    
    def add_emotional_context_to_package(self, package_id: str, emotional_context: Dict[str, Any]) -> bool:
        """
        Add emotional context to a viral package.
        
        Args:
            package_id: Package to add context to
            emotional_context: Dict with emotional state information
            
        Returns:
            True if successful, False otherwise
        """
        if not self.sensation_engine:
            return False
        
        try:
            # Store emotional context as JSON metadata
            # This could include: navigation_state when successful, object sensations, etc.
            emotional_json = json.dumps(emotional_context)
            
            # For now, we'll add this as a comment/metadata field
            # In full Phase 5 implementation, this would be a proper schema extension
            self.db.execute_query("""
                UPDATE viral_information_packages 
                SET package_metadata = ? 
                WHERE package_id = ?
            """, (emotional_json, package_id))
            
            return True
            
        except Exception as e:
            print(f"[VIRAL] Error adding emotional context: {e}")
            return False


def display_viral_ecosystem_dashboard(db: DatabaseInterface, generation: int):
    """
    Display the viral ecosystem status - packages and pariahs.
    """
    engine = ViralPackageEngine(db)
    
    print("\n" + "="*80)
    print(f"VIRAL ECOSYSTEM DASHBOARD - Generation {generation}")
    print("="*80)
    
    # Top viral packages
    print("\n[VIRAL] TOP VIRAL PACKAGES (Positive Selection)")
    print("-" * 80)
    packages = engine.get_top_packages(5)
    
    if packages:
        for i, pkg in enumerate(packages, 1):
            print(f"\n  #{i} {pkg['package_name']} ({pkg['package_type']})")
            print(f"      Success Rate: {pkg['success_rate']*100:.1f}%")
            print(f"      Avg Score Boost: +{pkg['avg_score_contribution']:.2f}")
            print(f"      Infections: {pkg['active_infections']}/{pkg['total_infections']} active")
            print(f"      Discovered: Generation {pkg['generation_discovered']}")
    else:
        print("  No viral packages yet - create from winning sequences")
    
    # Top pariahs
    print("\n[SKULL]  TOP PARIAHS (Negative Selection)")
    print("-" * 80)
    pariahs = engine.get_top_pariahs(5)
    
    if pariahs:
        for i, par in enumerate(pariahs, 1):
            print(f"\n  #{i} {par['pariah_name']} ({par['pariah_type']})")
            print(f"      Toxicity: {par['toxicity']*100:.1f}%")
            print(f"      Triggers: {par['trigger_count']} times")
            print(f"      Avg Score Loss: -{par['avg_score_loss']:.2f}")
            print(f"      Awareness: {par['active_awareness']}/{par['total_awareness']} agents")
            print(f"      Avoidance Rate: {par['avoidance_success_rate']*100:.1f}%")
            print(f"      Discovered: Generation {par['discovery_generation']}")
    else:
        print("  No pariahs yet - create from failed games")
    
    # Overall statistics
    stats = db.execute_query("""
        SELECT 
            (SELECT COUNT(*) FROM viral_information_packages WHERE is_active = TRUE) as total_packages,
            (SELECT COUNT(*) FROM agent_viral_infections WHERE is_active = TRUE) as total_infections,
            (SELECT COUNT(*) FROM pariahs WHERE is_active = TRUE) as total_pariahs,
            (SELECT COUNT(*) FROM agent_pariah_awareness WHERE is_active = TRUE) as total_awareness
    """)
    
    if stats:
        s = stats[0]
        print("\n[STATS] ECOSYSTEM STATISTICS")
        print("-" * 80)
        print(f"  Viral Packages: {s['total_packages']} active")
        print(f"  Package Infections: {s['total_infections']} total")
        print(f"  Pariahs: {s['total_pariahs']} active")
        print(f"  Pariah Awareness: {s['total_awareness']} agents aware")
        
        if s['total_packages'] > 0 and s['total_pariahs'] > 0:
            print(f"\n  [TARGET] Bidirectional Evolution ACTIVE")
            print(f"     Packages guide toward success, Pariahs warn of failure")
    
    print("="*80)


# ============================================================================
# TWO-STREAMS: ROLE-COHORT WISDOM
# ============================================================================

def get_cohort_wisdom(
    db: DatabaseInterface,
    agent_id: str,
    game_id: str,
    level_number: int,
    agent_role: str
) -> Dict[str, Any]:
    """
    Get collective wisdom from agents in the same role (cohort).
    
    Two-Streams Philosophy: Agents should trust recommendations from
    agents who share their role more than global averages.
    
    Args:
        db: Database interface
        agent_id: Agent requesting wisdom
        game_id: Current game
        level_number: Current level
        agent_role: Agent's current role (pioneer/optimizer/generalist/exploiter)
        
    Returns:
        Dictionary with:
        - best_sequence_id: Best sequence for this role on this level
        - confidence: How confident the cohort is (0-1)
        - avg_actions: Average actions to win for this cohort
        - emotional_context: Average frustration/satisfaction for cohort
        - sample_size: Number of cohort members contributing
    """
    wisdom = {
        'best_sequence_id': None,
        'confidence': 0.0,
        'avg_actions': 0.0,
        'avg_frustration': 0.5,
        'avg_satisfaction': 0.5,
        'sample_size': 0
    }
    
    # First, try cached cohort wisdom
    cached = db.execute_query("""
        SELECT * FROM role_cohort_wisdom
        WHERE game_id = ? AND level_number = ? AND role = ?
    """, (game_id, level_number, agent_role))
    
    if cached and cached[0]:
        c = cached[0]
        wisdom['best_sequence_id'] = c['best_sequence_id']
        wisdom['confidence'] = c['cohort_confidence']
        wisdom['avg_actions'] = c.get('avg_actions_to_win', 0)
        wisdom['sample_size'] = c['sample_size']
        return wisdom
    
    # If not cached, calculate from role performance data
    # Query agents with same role who succeeded on this game/level
    role_column = f"role_success_{agent_role}"
    
    # Get best performing sequences for this role
    sequences = db.execute_query(f"""
        SELECT 
            ws.sequence_id,
            sr.{role_column} as role_success,
            sr.avg_frustration_on_success,
            sr.avg_satisfaction_on_success,
            ws.action_count,
            ws.efficiency_score
        FROM winning_sequences ws
        LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
        WHERE ws.game_id = ? AND ws.level_number = ? AND ws.is_active = 1
        ORDER BY sr.{role_column} DESC, ws.efficiency_score DESC
        LIMIT 5
    """, (game_id, level_number))
    
    if not sequences:
        return wisdom
    
    # Aggregate cohort data
    total_role_success = 0.0
    total_frustration = 0.0
    total_satisfaction = 0.0
    total_actions = 0.0
    count = 0
    
    for seq in sequences:
        total_role_success += (seq['role_success'] or 0.5)
        total_frustration += (seq['avg_frustration_on_success'] or 0.5)
        total_satisfaction += (seq['avg_satisfaction_on_success'] or 0.5)
        total_actions += (seq['action_count'] or 0)
        count += 1
    
    if count > 0:
        wisdom['best_sequence_id'] = sequences[0]['sequence_id']
        wisdom['confidence'] = total_role_success / count
        wisdom['avg_actions'] = total_actions / count
        wisdom['avg_frustration'] = total_frustration / count
        wisdom['avg_satisfaction'] = total_satisfaction / count
        wisdom['sample_size'] = count
        
        # Cache this wisdom for future queries
        try:
            from datetime import datetime
            import uuid
            db.execute_query("""
                INSERT OR REPLACE INTO role_cohort_wisdom
                (wisdom_id, game_id, level_number, role, avg_success_rate, 
                 best_sequence_id, cohort_confidence, sample_size, avg_actions_to_win, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"cohort_{uuid.uuid4().hex[:12]}",
                game_id, level_number, agent_role,
                wisdom['confidence'], wisdom['best_sequence_id'],
                wisdom['confidence'], wisdom['sample_size'],
                wisdom['avg_actions'],
                datetime.now().isoformat()
            ))
        except Exception:
            pass  # Non-critical cache write
    
    return wisdom


def update_sequence_role_reputation(
    db: DatabaseInterface,
    sequence_id: str,
    agent_role: str,
    success: bool,
    frustration_level: float = 0.5,
    satisfaction_level: float = 0.5
) -> None:
    """
    Update a sequence's reputation for a specific role.
    
    Called after an agent uses a sequence, to track per-role success rates.
    
    Args:
        db: Database interface
        sequence_id: Sequence that was used
        agent_role: Role of agent who used it
        success: Whether the sequence led to success
        frustration_level: Agent's frustration when using sequence
        satisfaction_level: Agent's satisfaction when using sequence
    """
    role_column = f"role_success_{agent_role}"
    
    # Get current reputation
    rep = db.execute_query("""
        SELECT * FROM sequence_reputation WHERE sequence_id = ?
    """, (sequence_id,))
    
    if not rep:
        # Create new reputation record
        try:
            db.execute_query("""
                INSERT INTO sequence_reputation 
                (sequence_id, reliability_score, attempt_count, success_count, failure_count,
                 role_success_pioneer, role_success_optimizer, role_success_exploiter, 
                 role_success_generalist, avg_frustration_on_success, avg_satisfaction_on_success)
                VALUES (?, 0.5, 1, ?, ?, 0.5, 0.5, 0.5, 0.5, ?, ?)
            """, (
                sequence_id,
                1 if success else 0,
                0 if success else 1,
                frustration_level if success else 0.5,
                satisfaction_level if success else 0.5
            ))
        except Exception:
            pass
        return
    
    r = rep[0]
    
    # Update role-specific success rate (exponential moving average)
    current_role_success = r.get(role_column, 0.5) or 0.5
    new_role_success = current_role_success * 0.9 + (1.0 if success else 0.0) * 0.1
    
    # Update emotional context (only on success)
    if success:
        current_frustration = r.get('avg_frustration_on_success', 0.5) or 0.5
        current_satisfaction = r.get('avg_satisfaction_on_success', 0.5) or 0.5
        new_frustration = current_frustration * 0.9 + frustration_level * 0.1
        new_satisfaction = current_satisfaction * 0.9 + satisfaction_level * 0.1
    else:
        new_frustration = r.get('avg_frustration_on_success', 0.5) or 0.5
        new_satisfaction = r.get('avg_satisfaction_on_success', 0.5) or 0.5
    
    # Update the record
    db.execute_query(f"""
        UPDATE sequence_reputation SET
            {role_column} = ?,
            attempt_count = attempt_count + 1,
            success_count = success_count + ?,
            failure_count = failure_count + ?,
            avg_frustration_on_success = ?,
            avg_satisfaction_on_success = ?,
            last_validation = CURRENT_TIMESTAMP
        WHERE sequence_id = ?
    """, (
        new_role_success,
        1 if success else 0,
        0 if success else 1,
        new_frustration,
        new_satisfaction,
        sequence_id
    ))


if __name__ == "__main__":
    # Test the engine
    db = DatabaseInterface()
    display_viral_ecosystem_dashboard(db, 0)
