#!/usr/bin/env python3
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Regulatory Signal Engine - Phase 4: Distributed Regulation

This implements network homeostasis through distributed signals (NOT voting).
Think bacterial quorum sensing - agents emit signals based on local state,
network responds through emergent consensus.

Key Principles:
- Struggling agents emit stress signals
- Thriving agents suppress stress signals  
- Net signal strength drives parameter adjustments
- Emergent homeostasis, no central control
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import uuid
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from database_interface import DatabaseInterface

# Anti-resonance protection for regulatory adjustments
try:
    from trigger_controller import TriggerController
    TRIGGER_CONTROLLER_AVAILABLE = True
except ImportError:
    TRIGGER_CONTROLLER_AVAILABLE = False
    TriggerController = None


class RegulatorySignalEngine:
    """
    Manages distributed network regulation through signal-based homeostasis.
    
    This is NOT democracy - it's bacterial quorum sensing for network health.
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Anti-resonance protection via TriggerController
        if TRIGGER_CONTROLLER_AVAILABLE:
            self.trigger_controller = TriggerController(db)
            self.logger.info("[REGULATION] TriggerController integrated for anti-resonance protection")
        else:
            self.trigger_controller = None
            self.logger.warning("[REGULATION] TriggerController not available - resonance protection disabled")
        
        # Signal types and their target parameters
        self.signal_types = {
            'diversity_stress': {
                'target_parameter': 'knowledge_diversity_boost',
                'adjustment_direction': 'increase',
                'base_magnitude': 0.15
            },
            'metabolism_stress': {
                'target_parameter': 'action_budget_multiplier', 
                'adjustment_direction': 'increase',
                'base_magnitude': 0.1
            },
            'infection_boost': {
                'target_parameter': 'viral_transmission_rate',
                'adjustment_direction': 'increase', 
                'base_magnitude': 0.2
            },
            'exploration_need': {
                'target_parameter': 'mutation_rate',
                'adjustment_direction': 'increase',
                'base_magnitude': 0.05
            },
            'exploitation_focus': {
                'target_parameter': 'selection_pressure',
                'adjustment_direction': 'increase',
                'base_magnitude': 0.1
            },
            'population_pressure': {
                'target_parameter': 'population_size_target',
                'adjustment_direction': 'decrease',
                'base_magnitude': 0.05
            },
            'resonance_amplification': {
                'target_parameter': 'resonance_priority_boost',
                'adjustment_direction': 'increase',
                'base_magnitude': 0.25,
                'description': 'Cross-role pattern agreement detected - amplify exploration'
            },
            # Role Fairness Protocol: Dynamic ATP adjustment based on network needs
            'role_need': {
                'target_parameter': 'role_atp_adjustment',
                'adjustment_direction': 'dynamic',  # Can be + or -
                'base_magnitude': 0.3,  # Max ±0.3 ATP adjustment
                'description': 'Network role demand signal for ATP rebalancing'
            }
        }
    
    def emit_agent_signals(self, generation: int) -> List[str]:
        """
        Have agents emit regulatory signals based on their local state.
        
        This is the core of distributed regulation - no central planning,
        just local responses to local conditions.
        """
        signals_emitted = []
        
        # Get all active agents with performance data
        agents = self.db.execute_query("""
            SELECT a.agent_id, a.avg_score_per_game, a.total_games_won, 
                   a.discovery_prestige, a.action_allowance_per_level
            FROM agents a
            WHERE a.is_active = TRUE
            ORDER BY RANDOM()
            LIMIT 100
        """)
        
        if not agents:
            self.logger.warning("No agents found for signal emission")
            return signals_emitted
        
        # Get network health context
        network_health = self._get_network_health_context(generation)
        
        for agent in agents:
            agent_signals = self._agent_emit_signals(agent, generation, network_health)
            signals_emitted.extend(agent_signals)
        
        # System-level signals based on failing metrics
        system_signals = self._emit_system_signals(generation, network_health)
        signals_emitted.extend(system_signals)
        
        # Role Fairness Protocol: Emit role need signals for ATP adjustment
        role_signals = self.emit_role_need_signals(generation)
        signals_emitted.extend(role_signals)
        
        self.logger.info(f"Emitted {len(signals_emitted)} regulatory signals for generation {generation}")
        return signals_emitted
    
    def _agent_emit_signals(self, agent: Dict, generation: int, network_health: Dict) -> List[str]:
        """
        Individual agent emits signals based on local state and stress level.
        """
        signals = []
        agent_id = agent['agent_id']
        
        # Calculate agent stress level
        stress_level = self._calculate_agent_stress(agent, network_health)
        
        # Agent performance percentile
        performance_percentile = self._get_agent_performance_percentile(agent, generation)
        
        # Struggling agents emit stress signals
        if stress_level > 0.7:  # High stress
            # Diversity stress if agent has low discovery rate
            if agent.get('discovery_prestige', 0) < 1.0:
                signal_id = self._create_signal(
                    signal_type='diversity_stress',
                    source_agent=agent_id,
                    generation=generation,
                    strength=min(stress_level * 2.0, 5.0),
                    context={'agent_stress': stress_level, 'performance': performance_percentile}
                )
                signals.append(signal_id)
            
            # Metabolism stress if agent is action-starved
            if agent.get('action_allowance_per_level', 400) < 300:
                signal_id = self._create_signal(
                    signal_type='metabolism_stress',
                    source_agent=agent_id,
                    generation=generation,
                    strength=min(stress_level * 1.5, 4.0),
                    context={'agent_stress': stress_level, 'budget': agent.get('action_allowance_per_level', 0)}
                )
                signals.append(signal_id)
            
            # Exploration need if agent is stuck
            if agent.get('avg_score_per_game', 0) < 0.1:
                signal_id = self._create_signal(
                    signal_type='exploration_need',
                    source_agent=agent_id,
                    generation=generation,
                    strength=min(stress_level * 1.8, 4.5),
                    context={'agent_stress': stress_level, 'avg_score': agent.get('avg_score_per_game', 0)}
                )
                signals.append(signal_id)
        
        # Thriving agents suppress stress signals or emit focus signals  
        elif stress_level < 0.3:  # Low stress, thriving
            # Check if there are active stress signals to suppress
            active_stress_signals = self.db.execute_query("""
                SELECT signal_id, signal_type, current_strength 
                FROM network_regulatory_signals 
                WHERE generation >= ? AND is_active = TRUE
                AND signal_type IN ('diversity_stress', 'metabolism_stress', 'exploration_need')
                ORDER BY current_strength DESC
                LIMIT 3
            """, (generation - 2,))
            
            # Suppress the strongest stress signal
            if active_stress_signals and performance_percentile > 0.6:
                target_signal = active_stress_signals[0]
                self._suppress_signal(
                    target_signal['signal_id'],
                    agent_id, 
                    generation,
                    suppression_strength=min(2.0 - stress_level, 3.0)
                )
        
        return signals
    
    def _emit_system_signals(self, generation: int, network_health: Dict) -> List[str]:
        """
        System-level signals based on failing network metrics.
        """
        signals = []
        
        # Based on Phase 4 readiness assessment failing metrics:
        
        # 1. Knowledge diversity < 3.0 (currently 1.758)
        if network_health.get('knowledge_diversity_index', 0) < 3.0:
            signal_id = self._create_signal(
                signal_type='diversity_stress',
                source_agent=None,  # System signal
                generation=generation,
                strength=4.0,  # High priority
                context={'current_diversity': network_health.get('knowledge_diversity_index', 0)}
            )
            signals.append(signal_id)
        
        # 2. Viral infection rate < 60% (currently 0.9%)
        if network_health.get('viral_infection_rate', 0) < 60.0:
            signal_id = self._create_signal(
                signal_type='infection_boost',
                source_agent=None,
                generation=generation,
                strength=5.0,  # Critical priority
                context={'current_infection_rate': network_health.get('viral_infection_rate', 0)}
            )
            signals.append(signal_id)
        
        # 3. Population might be too large (hampering performance)
        if network_health.get('active_agents', 0) > 3500:
            signal_id = self._create_signal(
                signal_type='population_pressure',
                source_agent=None,
                generation=generation,
                strength=2.5,
                context={'current_population': network_health.get('active_agents', 0)}
            )
            signals.append(signal_id)
        
        # 4. RESONANCE DETECTION - Cross-role pattern agreement
        # Run resonance detection every generation to find objective truths
        resonance_signals = self._emit_resonance_signals(generation)
        signals.extend(resonance_signals)
        
        return signals
    
    def _emit_resonance_signals(self, generation: int) -> List[str]:
        """
        Detect resonant patterns and emit signals for network prioritization.
        
        Resonance = when different agent roles independently converge on the
        same abstract pattern. This is evidence of objective truth.
        
        When high-resonance patterns are detected, emit signals to:
        1. Prioritize exploration around resonant patterns
        2. Share resonant patterns network-wide
        3. Reduce exploration in low-resonance areas
        """
        signals = []
        
        try:
            from resonance_detector import ResonanceDetector
            detector = ResonanceDetector(self.db)
            
            # Run full resonance detection
            resonant_patterns = detector.detect_resonance(generation)
            
            if not resonant_patterns:
                self.logger.debug("[RESONANCE] No resonant patterns detected this generation")
                return signals
            
            # Get summary for logging
            summary = detector.get_resonance_summary()
            self.logger.info(
                f"[RESONANCE] Detected {summary.get('total_resonant_patterns', 0)} resonant patterns, "
                f"avg score: {summary.get('average_resonance_score', 0):.2f}"
            )
            
            # Emit signals for high-resonance patterns
            high_resonance = [p for p in resonant_patterns if p['resonance_score'] >= 2.0]
            
            for pattern in high_resonance[:3]:  # Top 3 patterns
                signal_id = self._create_signal(
                    signal_type='resonance_amplification',
                    source_agent=None,  # System signal
                    generation=generation,
                    strength=pattern['resonance_score'],
                    context={
                        'pattern_hash': pattern['pattern_hash'],
                        'role_diversity': pattern['role_diversity'],
                        'roles_found': pattern['roles_found'],
                        'game_types': pattern['game_types'],
                        'theory_type': pattern.get('theory_type', 'unknown')
                    }
                )
                signals.append(signal_id)
                self.logger.info(
                    f"[RESONANCE] Amplifying pattern {pattern['pattern_hash'][:8]} "
                    f"(score: {pattern['resonance_score']:.2f}, roles: {pattern['roles_found']})"
                )
            
        except ImportError:
            self.logger.debug("[RESONANCE] Resonance detector not available")
        except Exception as e:
            self.logger.error(f"[RESONANCE] Detection failed: {e}")
        
        return signals

    def emit_role_need_signals(self, generation: int) -> List[str]:
        """
        Emit signals for network role demand to support Role Fairness Protocol.
        
        Analyzes current game state and population distribution to determine
        which roles are needed more/less. Emits role_need signals with ATP adjustments.
        
        When network has mostly unbeaten games -> Pioneer demand ↑
        When network has mostly beaten games -> Optimizer demand ↑
        
        Returns:
            List of signal IDs emitted
        """
        import json
        signals = []
        
        # Get game state distribution from winning_sequences
        # A game is "beaten" if it has at least one full-game winning sequence
        game_stats = self.db.execute_query("""
            SELECT 
                COUNT(DISTINCT CASE WHEN ws.is_active = 1 AND ws.success_rate_when_reused > 0.5 THEN SUBSTR(ws.game_id, 1, 4) END) as beaten_games,
                COUNT(DISTINCT SUBSTR(gr.game_id, 1, 4)) - COUNT(DISTINCT CASE WHEN ws.is_active = 1 AND ws.success_rate_when_reused > 0.5 THEN SUBSTR(ws.game_id, 1, 4) END) as unbeaten_games
            FROM game_results gr
            LEFT JOIN winning_sequences ws ON SUBSTR(gr.game_id, 1, 4) = SUBSTR(ws.game_id, 1, 4)
            WHERE gr.generation >= (SELECT MAX(generation) - 10 FROM game_results)
        """)
        
        beaten = 0
        unbeaten = 0
        if game_stats and len(game_stats) > 0:
            beaten = game_stats[0].get('beaten_games', 0) or 0
            unbeaten = game_stats[0].get('unbeaten_games', 0) or 0
        
        total = beaten + unbeaten
        if total == 0:
            return signals
        
        exploration_ratio = unbeaten / total  # 0.0 = all beaten, 1.0 = none beaten
        
        # Calculate role adjustments based on exploration ratio
        # High exploration_ratio -> need pioneers (+), less need for optimizers (-)
        # Low exploration_ratio -> need optimizers (+), less need for pioneers (-)
        role_needs = {
            'pioneer': (exploration_ratio - 0.5) * 0.6,      # -0.3 to +0.3
            'optimizer': (0.5 - exploration_ratio) * 0.6,    # -0.3 to +0.3
            'generalist': 0.0,                                # Always balanced
            'exploiter': (0.3 - exploration_ratio) * 0.3     # Slight boost when mostly beaten
        }
        
        # Clamp all values to [-0.3, +0.3]
        for role in role_needs:
            role_needs[role] = max(-0.3, min(0.3, role_needs[role]))
        
        # Emit a single role_need signal with all adjustments
        signal_id = self._create_signal(
            signal_type='role_need',
            source_agent=None,  # System signal
            generation=generation,
            strength=1.0,
            context={
                'role_needs': role_needs,
                'exploration_ratio': exploration_ratio,
                'beaten_games': beaten,
                'unbeaten_games': unbeaten
            }
        )
        signals.append(signal_id)
        
        self.logger.info(
            f"[ROLE NEED] Exploration ratio: {exploration_ratio:.2f} "
            f"(beaten={beaten}, unbeaten={unbeaten}) -> "
            f"Pioneer:{role_needs['pioneer']:+.2f}, Optimizer:{role_needs['optimizer']:+.2f}"
        )
        
        return signals

    def process_signal_responses(self, generation: int) -> Dict[str, float]:
        """
        Process agent responses to active signals and calculate net signal strength.
        """
        # Get all active signals for this generation window
        active_signals = self.db.execute_query("""
            SELECT signal_id, signal_type, current_strength, target_parameter,
                   adjustment_direction, adjustment_magnitude
            FROM network_regulatory_signals 
            WHERE generation >= ? AND is_active = TRUE
        """, (generation - 3,))  # 3-generation signal lifetime
        
        net_adjustments = {}
        
        for signal in active_signals:
            signal_id = signal['signal_id']
            
            # Get agent responses to this signal
            responses = self.db.execute_query("""
                SELECT response_type, response_strength, agent_performance_percentile
                FROM agent_signal_responses 
                WHERE signal_id = ? AND generation >= ?
            """, (signal_id, generation - 1))
            
            # Calculate net signal response
            net_amplification = 0.0
            for response in responses:
                if response['response_type'] == 'amplify':
                    net_amplification += response['response_strength']
                elif response['response_type'] == 'suppress':
                    net_amplification -= response['response_strength']
            
            # Update signal strength
            new_strength = max(0.0, signal['current_strength'] + net_amplification * 0.1)
            
            self.db.execute_query("""
                UPDATE network_regulatory_signals 
                SET current_strength = ?, net_amplification = ?,
                    agents_responding = (
                        SELECT COUNT(*) FROM agent_signal_responses 
                        WHERE signal_id = ?
                    )
                WHERE signal_id = ?
            """, (new_strength, net_amplification, signal_id, signal_id))
            
            # Calculate parameter adjustment
            if new_strength > 1.0:  # Threshold for action
                parameter = signal['target_parameter']
                direction = signal['adjustment_direction']
                magnitude = signal['adjustment_magnitude'] * new_strength
                
                if parameter not in net_adjustments:
                    net_adjustments[parameter] = 0.0
                
                if direction == 'increase':
                    net_adjustments[parameter] += magnitude
                elif direction == 'decrease':
                    net_adjustments[parameter] -= magnitude
        
        return net_adjustments
    
    def apply_network_regulation(self, generation: int, net_adjustments: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
        """
        Apply parameter adjustments based on distributed signal consensus.
        
        Uses TriggerController for anti-resonance protection:
        - Cooldowns between same parameter adjustments
        - Damping for consecutive fires
        - Maximum adjustment caps
        
        Returns dict of parameter_name: (old_value, new_value)
        """
        applied_changes = {}
        
        for parameter, adjustment in net_adjustments.items():
            if abs(adjustment) < 0.01:  # Skip tiny adjustments
                continue
            
            # Anti-resonance check via TriggerController
            trigger_name = f"regulate_{parameter}"
            if self.trigger_controller:
                # Check cooldown - prevent rapid-fire adjustments
                if not self.trigger_controller.can_fire(trigger_name, generation):
                    self.logger.debug(f"[REGULATION] {parameter} blocked by cooldown")
                    continue
                
                # Apply damping for consecutive fires
                damped_adjustment = self.trigger_controller.calculate_damped_magnitude(
                    trigger_name, abs(adjustment), generation
                )
                # Preserve direction
                adjustment = damped_adjustment if adjustment > 0 else -damped_adjustment
            
            old_value = self._get_current_parameter_value(parameter)
            new_value = self._calculate_new_parameter_value(parameter, old_value, adjustment)
            
            # Apply the change (this would integrate with your evolution system)
            success = self._set_parameter_value(parameter, new_value)
            
            if success:
                applied_changes[parameter] = (old_value, new_value)
                
                # Record trigger fire for anti-resonance tracking
                if self.trigger_controller:
                    self.trigger_controller.fire_with_safeguards(
                        trigger_name=trigger_name,
                        generation=generation,
                        primary_metric_value=abs(adjustment),
                        secondary_metric_values=[],  # No corroboration needed for signal-driven
                        base_adjustment=abs(adjustment),
                        apply_func=lambda _: True  # Already applied above
                    )
                
                # Record in regulation history
                self._record_regulation_event(
                    generation=generation,
                    parameter_name=parameter,
                    old_value=old_value,
                    new_value=new_value,
                    adjustment_magnitude=adjustment,
                    net_signal_strength=abs(adjustment)
                )
        
        return applied_changes
    
    def _calculate_agent_stress(self, agent: Dict, network_health: Dict) -> float:
        """
        Calculate agent stress level (0.0 = thriving, 1.0 = struggling).
        """
        stress_factors = []
        
        # Performance stress
        avg_score = agent.get('avg_score_per_game', 0)
        if avg_score < 0.1:
            stress_factors.append(0.8)
        elif avg_score < 0.5:
            stress_factors.append(0.4)
        else:
            stress_factors.append(0.1)
        
        # Resource stress (action budget)
        budget = agent.get('action_allowance_per_level', 400)
        if budget < 250:
            stress_factors.append(0.9)
        elif budget < 350:
            stress_factors.append(0.5)
        else:
            stress_factors.append(0.2)
        
        # Social stress (prestige)
        prestige = agent.get('discovery_prestige', 0)
        if prestige < 0.5:
            stress_factors.append(0.6)
        elif prestige < 2.0:
            stress_factors.append(0.3)
        else:
            stress_factors.append(0.1)
        
        # Return average stress
        return sum(stress_factors) / len(stress_factors)
    
    def _get_agent_performance_percentile(self, agent: Dict, generation: int) -> float:
        """
        Get agent's performance percentile relative to current population.
        """
        agent_score = agent.get('avg_score_per_game', 0)
        
        # Get percentile ranking
        percentile_result = self.db.execute_query("""
            SELECT 
                (COUNT(*) * 1.0 / (SELECT COUNT(*) FROM agents WHERE is_active = TRUE)) as percentile
            FROM agents 
            WHERE is_active = TRUE AND avg_score_per_game <= ?
        """, (agent_score,))
        
        return percentile_result[0]['percentile'] if percentile_result else 0.5
    
    def _create_signal(self, signal_type: str, source_agent: Optional[str], 
                      generation: int, strength: float, context: Dict) -> str:
        """
        Create a new regulatory signal.
        """
        signal_id = f"sig_{uuid.uuid4().hex[:12]}"
        signal_config = self.signal_types[signal_type]
        
        expires_gen = generation + 5  # 5-generation lifespan
        
        self.db.execute_query("""
            INSERT INTO network_regulatory_signals (
                signal_id, generation, signal_type, signal_source_agent,
                initial_strength, current_strength, target_parameter,
                adjustment_direction, adjustment_magnitude, expires_generation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_id, generation, signal_type, source_agent,
            strength, strength, signal_config['target_parameter'],
            signal_config['adjustment_direction'], 
            signal_config['base_magnitude'], expires_gen
        ))
        
        return signal_id
    
    def _suppress_signal(self, signal_id: str, agent_id: str, generation: int, suppression_strength: float):
        """
        Agent suppresses an existing signal.
        """
        response_id = f"resp_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT OR REPLACE INTO agent_signal_responses (
                response_id, agent_id, signal_id, generation,
                response_type, response_strength
            ) VALUES (?, ?, ?, ?, 'suppress', ?)
        """, (response_id, agent_id, signal_id, generation, suppression_strength))
    
    def _get_network_health_context(self, generation: int) -> Dict:
        """
        Get current network health metrics for context.
        """
        # Get latest ecosystem snapshot
        snapshot = self.db.execute_query("""
            SELECT knowledge_diversity_index, active_agents, network_growth_rate
            FROM ecosystem_health_snapshots 
            ORDER BY generation DESC LIMIT 1
        """)
        
        # Get viral infection rate
        total_agents = self.db.execute_query("SELECT COUNT(*) as count FROM agents WHERE is_active = TRUE")
        infected_agents = self.db.execute_query("SELECT COUNT(DISTINCT agent_id) as count FROM agent_viral_infections")
        
        viral_infection_rate = 0.0
        if total_agents and infected_agents and total_agents[0]['count'] > 0:
            viral_infection_rate = (infected_agents[0]['count'] / total_agents[0]['count']) * 100
        
        context = {
            'knowledge_diversity_index': snapshot[0]['knowledge_diversity_index'] if snapshot else 0.0,
            'active_agents': snapshot[0]['active_agents'] if snapshot else 0,
            'network_growth_rate': snapshot[0]['network_growth_rate'] if snapshot else 0.0,
            'viral_infection_rate': viral_infection_rate
        }
        
        return context
    
    def _get_current_parameter_value(self, parameter: str) -> float:
        """
        Get current value of an evolution parameter.
        """
        # This would integrate with your actual evolution system
        defaults = {
            'knowledge_diversity_boost': 1.0,
            'action_budget_multiplier': 1.0,
            'viral_transmission_rate': 0.1,
            'mutation_rate': 0.02,
            'selection_pressure': 0.7,
            'population_size_target': 4000
        }
        return defaults.get(parameter, 1.0)
    
    def _calculate_new_parameter_value(self, parameter: str, old_value: float, adjustment: float) -> float:
        """
        Calculate new parameter value with safety bounds.
        """
        new_value = old_value + adjustment
        
        # Apply safety bounds
        bounds = {
            'knowledge_diversity_boost': (0.5, 3.0),
            'action_budget_multiplier': (0.5, 2.0),
            'viral_transmission_rate': (0.05, 0.5),
            'mutation_rate': (0.001, 0.1),
            'selection_pressure': (0.1, 1.0),
            'population_size_target': (1000, 6000)
        }
        
        if parameter in bounds:
            min_val, max_val = bounds[parameter]
            new_value = max(min_val, min(max_val, new_value))
        
        return new_value
    
    def _set_parameter_value(self, parameter: str, value: float) -> bool:
        """
        Set evolution parameter value.
        This would integrate with your actual evolution system.
        """
        # For now, just log the change
        self.logger.info(f"Setting {parameter} = {value:.4f}")
        return True
    
    def _record_regulation_event(self, generation: int, parameter_name: str, 
                                old_value: float, new_value: float, 
                                adjustment_magnitude: float, net_signal_strength: float):
        """
        Record parameter change in regulation history.
        """
        regulation_id = f"reg_{uuid.uuid4().hex[:12]}"
        
        self.db.execute_query("""
            INSERT INTO network_regulation_history (
                regulation_id, generation, parameter_name, old_value, new_value,
                adjustment_magnitude, net_signal_strength
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            regulation_id, generation, parameter_name, old_value, new_value,
            adjustment_magnitude, net_signal_strength
        ))
    
    def cleanup_expired_signals(self, generation: int):
        """
        Remove expired signals and old response data.
        """
        # Mark expired signals as inactive
        self.db.execute_query("""
            UPDATE network_regulatory_signals 
            SET is_active = FALSE 
            WHERE expires_generation <= ? AND is_active = TRUE
        """, (generation,))
        
        # Clean up old responses (keep last 10 generations)
        self.db.execute_query("""
            DELETE FROM agent_signal_responses 
            WHERE generation < ?
        """, (generation - 10,))
        
        # Clean up old propagation events
        self.db.execute_query("""
            DELETE FROM signal_propagation_events 
            WHERE generation < ?
        """, (generation - 10,))
    
    def get_regulation_summary(self, generation: int) -> Dict:
        """
        Get summary of current regulatory state.
        """
        active_signals = self.db.execute_query("""
            SELECT signal_type, COUNT(*) as count, AVG(current_strength) as avg_strength
            FROM network_regulatory_signals 
            WHERE generation >= ? AND is_active = TRUE
            GROUP BY signal_type
        """, (generation - 3,))
        
        recent_regulations = self.db.execute_query("""
            SELECT parameter_name, COUNT(*) as changes, AVG(adjustment_magnitude) as avg_change
            FROM network_regulation_history 
            WHERE generation >= ?
            GROUP BY parameter_name
        """, (generation - 5,))
        
        return {
            'active_signals': {s['signal_type']: {'count': s['count'], 'strength': s['avg_strength']} 
                              for s in active_signals},
            'recent_regulations': {r['parameter_name']: {'changes': r['changes'], 'avg_change': r['avg_change']} 
                                  for r in recent_regulations}
        }


# ============================================================================
# SOCIETAL METRICS SYSTEM - CONTROL ERROR
# Part of autopoiesis monitoring for self-regulation
# ============================================================================

def calculate_control_error(db: DatabaseInterface, generation: int) -> float:
    """
    Calculate divergence between intended vs actual population ratios.
    
    Control Error measures how well the system achieves its targets.
    Higher error = system struggling to maintain homeostasis.
    
    Formula:
        mean(|actual_role_ratio - target_role_ratio|) for all roles
    
    Ideal: < 0.05 (5% deviation)
    Concerning: > 0.15 (15% deviation)
    Critical: > 0.30 (30% deviation)
    
    Args:
        db: DatabaseInterface instance
        generation: Current evolution generation
        
    Returns:
        Mean absolute control error across all role ratios
        
    Part of the Societal Metrics System.
    See DOCS/Societal_Metrics_Implementation_Analysis.md for design rationale.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Target ratios from role system design
        # These can be mode-dependent but defaults are:
        target_ratios = {
            'PIONEER': 0.60,      # Frontier explorers
            'OPTIMIZER': 0.30,    # Efficiency refiners
            'GENERALIST': 0.10,   # Balanced players
            'EXPLOITER': 0.05     # Post-optimization (varies by mode)
        }
        
        # Get actual population counts
        population_result = db.execute_query("""
            SELECT 
                COALESCE(role, 'UNKNOWN') as role,
                COUNT(*) as count
            FROM agents
            WHERE is_active = TRUE
            GROUP BY role
        """)
        
        if not population_result:
            logger.warning("No active agents for control error calculation")
            return 0.0
        
        # Calculate total and actual ratios
        total_agents = sum(r['count'] for r in population_result)
        if total_agents == 0:
            return 0.0
            
        actual_ratios = {
            r['role']: r['count'] / total_agents 
            for r in population_result
        }
        
        # Calculate control error (mean absolute deviation)
        errors = []
        for role, target in target_ratios.items():
            actual = actual_ratios.get(role, 0.0)
            errors.append(abs(target - actual))
        
        control_error = sum(errors) / len(errors) if errors else 0.0
        
        # Store metric in ecosystem_metrics table
        _store_control_error_metric(db, generation, control_error, actual_ratios)
        
        logger.info(f"[CONTROL] Generation {generation}: "
                   f"error={control_error:.3f} "
                   f"(ratios: {actual_ratios})")
        
        return control_error
        
    except Exception as e:
        logger.error(f"Error calculating control error: {e}")
        return 0.0


def _store_control_error_metric(db: DatabaseInterface, generation: int,
                                 control_error: float, actual_ratios: dict):
    """Store control error in ecosystem_metrics table for tracking."""
    import json
    logger = logging.getLogger(__name__)
    
    try:
        # Ensure table exists
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS ecosystem_metrics (
                metric_name TEXT NOT NULL,
                generation INTEGER NOT NULL,
                value REAL NOT NULL,
                measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                PRIMARY KEY (metric_name, generation)
            )
        """)
        
        db.execute_query("""
            INSERT INTO ecosystem_metrics (metric_name, generation, value, metadata)
            VALUES ('control_error', ?, ?, ?)
            ON CONFLICT(metric_name, generation) DO UPDATE SET 
                value = excluded.value,
                metadata = excluded.metadata,
                measured_at = CURRENT_TIMESTAMP
        """, (generation, control_error, json.dumps(actual_ratios)))
        
    except Exception as e:
        logger.error(f"Error storing control error metric: {e}")
