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
        
        # Phase 4.5: Initialize sensation engine if available
        if SENSATION_AVAILABLE:
            self.sensation_engine = SensationEngine(db)
        else:
            self.sensation_engine = None
    
    # ========================================================================
    # VIRAL PACKAGE CREATION (Positive Selection)
    # ========================================================================
    
    def create_viral_package_from_sequence(self, 
                                          sequence_id: str,
                                          agent_id: str,
                                          generation: int) -> Optional[str]:
        """
        Create a viral package from a winning sequence.
        
        This extracts the successful pattern and packages it as a "virus"
        that can spread to other agents.
        
        Args:
            sequence_id: ID of winning sequence to package
            agent_id: Agent who discovered this
            generation: Current generation
            
        Returns:
            package_id if created, None if failed
        """
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
            self.db.execute_query("""
                INSERT INTO viral_information_packages (
                    package_id, package_name, package_type,
                    action_sequence, coordinate_pattern,
                    virulence, transmission_rate, mutation_rate,
                    discovery_generation, source_sequence_id, generation_discovered,
                    is_active, last_successful_use_generation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                generation
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
    
    def update_package_success(self,
                              package_id: str,
                              agent_id: str,
                              score_contribution: float,
                              success: bool,
                              generation: int):
        """
        Update package fitness based on usage outcome.
        
        Args:
            package_id: Package used
            agent_id: Agent who used it
            score_contribution: Score gained/lost
            success: Whether this helped or hurt
            generation: Current generation
        """
        try:
            # Update agent infection stats
            self.db.execute_query("""
                UPDATE agent_viral_infections
                SET success_count = success_count + ?,
                    failure_count = failure_count + ?,
                    total_uses = total_uses + 1,
                    avg_score_boost = (avg_score_boost * total_uses + ?) / (total_uses + 1),
                    last_used_generation = ?
                WHERE agent_id = ? AND package_id = ?
            """, (
                1 if success else 0,
                0 if success else 1,
                score_contribution,
                generation,
                agent_id,
                package_id
            ))
            
            # Update package global stats
            self.db.execute_query("""
                UPDATE viral_information_packages
                SET last_successful_use_generation = ?
                WHERE package_id = ?
            """, (generation, package_id))
            
            # Recalculate package success rate
            infections = self.db.execute_query("""
                SELECT 
                    AVG(CAST(success_count AS FLOAT) / NULLIF(total_uses, 0)) as success_rate,
                    AVG(avg_score_boost) as avg_score
                FROM agent_viral_infections
                WHERE package_id = ? AND total_uses > 0
            """, (package_id,))
            
            if infections:
                self.db.execute_query("""
                    UPDATE viral_information_packages
                    SET success_rate = ?,
                        avg_score_contribution = ?
                    WHERE package_id = ?
                """, (
                    infections[0]['success_rate'] or 0.0,
                    infections[0]['avg_score'] or 0.0,
                    package_id
                ))
                
        except Exception as e:
            print(f"[VIRAL] Error updating package success: {e}")
    
    # ========================================================================
    # PARIAH CREATION (Negative Selection)
    # ========================================================================
    
    def create_pariah_from_failure(self,
                                   game_id: str,
                                   agent_id: str,
                                   failed_actions: List[int],
                                   failed_coordinates: List[Tuple[int, int]],
                                   final_score: float,
                                   generation: int) -> Optional[str]:
        """
        Create a pariah (failure pattern) from a failed game.
        
        This extracts the failure pattern so the network can learn to avoid it.
        
        Args:
            game_id: Game where failure occurred
            agent_id: Agent who failed
            failed_actions: Action sequence that failed
            failed_coordinates: Coordinate sequence that failed
            final_score: Final score (low = worse failure)
            generation: Current generation
            
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
            
            self.db.execute_query("""
                INSERT INTO pariahs (
                    pariah_id, pariah_name, pariah_type,
                    action_sequence, coordinate_pattern, failure_description,
                    toxicity, detection_difficulty, context_specificity,
                    trigger_count, avg_score_loss,
                    discovery_generation, source_game_id, source_agent_id,
                    is_active, last_triggered_generation, avoidance_success_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pariah_id,
                f"Pariah_{game_id[:8]}_{generation}",
                'action_sequence',
                json.dumps(failed_actions),
                json.dumps(failed_coordinates),
                f"Failed with score {final_score:.2f}",
                toxicity,
                0.3,  # Initial detection difficulty
                0.5,  # Initial context specificity
                1,  # trigger_count (this failure)
                10.0 - final_score,  # avg_score_loss
                generation,
                game_id,
                agent_id,
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
    
    def update_pariah_avoidance(self,
                               pariah_id: str,
                               agent_id: str,
                               avoided_successfully: bool,
                               score_saved: float,
                               generation: int):
        """
        Update pariah avoidance stats.
        
        Args:
            pariah_id: Pariah encountered
            agent_id: Agent who encountered it
            avoided_successfully: Whether agent avoided the trap
            score_saved: Score saved by avoiding (or lost by triggering)
            generation: Current generation
        """
        try:
            self.db.execute_query("""
                UPDATE agent_pariah_awareness
                SET avoidance_success_count = avoidance_success_count + ?,
                    trigger_count = trigger_count + ?,
                    total_encounters = total_encounters + 1,
                    avg_score_saved = (avg_score_saved * total_encounters + ?) / (total_encounters + 1),
                    last_encountered_generation = ?
                WHERE agent_id = ? AND pariah_id = ?
            """, (
                1 if avoided_successfully else 0,
                0 if avoided_successfully else 1,
                score_saved if avoided_successfully else -score_saved,
                generation,
                agent_id,
                pariah_id
            ))
            
            # Update pariah global stats
            if not avoided_successfully:
                self.db.execute_query("""
                    UPDATE pariahs
                    SET trigger_count = trigger_count + 1,
                        last_triggered_generation = ?
                    WHERE pariah_id = ?
                """, (generation, pariah_id))
            
            # Recalculate avoidance success rate
            awareness = self.db.execute_query("""
                SELECT AVG(CAST(avoidance_success_count AS FLOAT) / NULLIF(total_encounters, 0)) as avoidance_rate
                FROM agent_pariah_awareness
                WHERE pariah_id = ? AND total_encounters > 0
            """, (pariah_id,))
            
            if awareness:
                self.db.execute_query("""
                    UPDATE pariahs
                    SET avoidance_success_rate = ?
                    WHERE pariah_id = ?
                """, (awareness[0]['avoidance_rate'] or 0.0, pariah_id))
                
        except Exception as e:
            print(f"[PARIAH] Error updating avoidance: {e}")
    
    # ========================================================================
    # ACTION SELECTION (Bidirectional Influence)
    # ========================================================================
    
    def get_package_action_weights(self, agent_id: str) -> Dict[int, float]:
        """
        Get action weights from viral packages this agent carries.
        
        Phase 4.5 Enhancement: Includes emotional context compatibility.
        Packages with emotional context matching agent's current state get boosted weights.
        
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
    
    def get_pariah_action_penalties(self, agent_id: str) -> Dict[int, float]:
        """
        Get action penalties from pariahs this agent is aware of.
        
        Returns:
            Dict mapping action_id -> penalty (higher = avoid this action more)
        """
        # Get all pariahs this agent is aware of
        awareness = self.db.execute_query("""
            SELECT 
                pa.pariah_id,
                pa.awareness_level,
                pa.avoidance_priority,
                p.action_sequence,
                p.toxicity
            FROM agent_pariah_awareness pa
            JOIN pariahs p ON pa.pariah_id = p.pariah_id
            WHERE pa.agent_id = ? AND pa.is_active = TRUE AND p.is_active = TRUE
        """, (agent_id,))
        
        action_penalties = {}
        
        for aware in awareness:
            # Parse action sequence
            try:
                actions = json.loads(aware['action_sequence'])
                
                # Penalty for each action by awareness level, avoidance priority, and toxicity
                penalty = (aware['awareness_level'] * 
                          aware['avoidance_priority'] * 
                          aware['toxicity'])
                
                for action in actions:
                    action_penalties[action] = action_penalties.get(action, 0.0) + penalty
                    
            except (json.JSONDecodeError, TypeError):
                continue
        
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
    
    def record_pariah_encounter(self, agent_id: str, pariah_id: str,
                               triggered: bool, score_impact: float, generation: int):
        """
        Record that an agent encountered a pariah (either avoided it or triggered it).
        
        Args:
            agent_id: Agent that encountered the pariah
            pariah_id: Pariah that was encountered
            triggered: Whether agent fell into the trap (True) or avoided it (False)
            score_impact: Score change from this encounter
            generation: Current generation
        """
        # Update awareness stats
        self.db.execute_query("""
            UPDATE agent_pariah_awareness
            SET total_encounters = total_encounters + 1,
                avoidance_success_count = avoidance_success_count + ?,
                trigger_count = trigger_count + ?,
                avg_score_saved = ((avg_score_saved * total_encounters) + ?) / (total_encounters + 1),
                last_encountered_generation = ?
            WHERE agent_id = ? AND pariah_id = ?
        """, (
            0 if triggered else 1,
            1 if triggered else 0,
            score_impact,
            generation,
            agent_id,
            pariah_id
        ))
        
        # Update pariah-level stats
        if triggered:
            self.db.execute_query("""
                UPDATE pariahs
                SET trigger_count = trigger_count + 1,
                    avg_score_loss = ((avg_score_loss * trigger_count) + ?) / (trigger_count + 1),
                    last_triggered_generation = ?,
                    avoidance_success_rate = (
                        SELECT CAST(SUM(avoidance_success_count) AS REAL) /
                               NULLIF(SUM(total_encounters), 0)
                        FROM agent_pariah_awareness
                        WHERE pariah_id = ?
                    )
                WHERE pariah_id = ?
            """, (
                abs(score_impact),
                generation,
                pariah_id,
                pariah_id
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
        
        Pariahs that haven't been triggered in threshold_generations may no longer be relevant.
        """
        self.db.execute_query("""
            UPDATE pariahs
            SET obsolescence_score = 1.0,
                is_active = FALSE
            WHERE last_triggered_generation < ? - ?
            AND is_active = TRUE
        """, (generation, threshold_generations))
    
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


if __name__ == "__main__":
    # Test the engine
    db = DatabaseInterface()
    display_viral_ecosystem_dashboard(db, 0)
