#!/usr/bin/env python
"""
Theory Alignment Checker - Self-Diagnostic System

This module checks if the actual code behavior aligns with the theoretical
requirements from the three unified theories:
1. Consciousness Theory (Two Streams, Personas, I-Thread)
2. Metalearning Theory (CODS, Primitives, Oracle)
3. Network Theory (Viral Packages, Prestige, Database-as-Organism)

The system can:
- Trace code paths to find WHERE things fail
- Compare actual behavior vs theory requirements
- Generate specific fix recommendations
- Test its own primitives and grade performance
"""

import os
import sys
import ast
import inspect
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface


class TheoryLayer(Enum):
    CONSCIOUSNESS = "consciousness"
    METALEARNING = "metalearning"
    NETWORK = "network"
    INTEGRATION = "integration"


class AlignmentStatus(Enum):
    ALIGNED = "aligned"
    PARTIAL = "partial"
    MISALIGNED = "misaligned"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass
class TheoryRequirement:
    """A requirement from the theoretical architecture."""
    theory: TheoryLayer
    requirement_id: str
    description: str
    expected_behavior: str
    code_locations: List[str] = field(default_factory=list)
    database_tables: List[str] = field(default_factory=list)
    test_query: Optional[str] = None
    fix_suggestion: Optional[str] = None


@dataclass
class AlignmentResult:
    """Result of checking a theory requirement against actual code."""
    requirement: TheoryRequirement
    status: AlignmentStatus
    actual_behavior: str
    evidence: Dict[str, Any]
    root_cause: Optional[str] = None
    fix_recommendation: Optional[str] = None
    code_trace: List[str] = field(default_factory=list)


class TheoryAlignmentChecker:
    """
    Cross-checks code behavior against theoretical requirements.
    
    This is the "self-grading" system that determines WHERE and WHY
    the code deviates from the intended architecture.
    """
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.requirements = self._load_theory_requirements()
        self.results: List[AlignmentResult] = []
        
    def _load_theory_requirements(self) -> List[TheoryRequirement]:
        """Load all theory requirements that should be validated."""
        return [
            # ============================================================
            # CONSCIOUSNESS THEORY REQUIREMENTS
            # ============================================================
            TheoryRequirement(
                theory=TheoryLayer.CONSCIOUSNESS,
                requirement_id="CON-001",
                description="Two Streams Architecture: Stream A (private) vs Stream B (collective)",
                expected_behavior="Agent actions should be weighted by wA/wB balance. "
                                 "Stream A = private experience, Stream B = viral packages from CODS.",
                code_locations=[
                    "core_gameplay.py:_select_action",
                    "core_gameplay.py:_compute_stream_weights",
                ],
                database_tables=["agents.self_network_bias"],
                test_query="""
                    SELECT 
                        AVG(self_network_bias) as avg_bias,
                        MIN(self_network_bias) as min_bias,
                        MAX(self_network_bias) as max_bias,
                        COUNT(*) as agent_count
                    FROM agents WHERE is_active = TRUE
                """,
                fix_suggestion="Ensure _select_action computes wA/wB from self_network_bias "
                              "and uses it to weight Stream A vs Stream B proposals."
            ),
            TheoryRequirement(
                theory=TheoryLayer.CONSCIOUSNESS,
                requirement_id="CON-002",
                description="Persona Ensemble: Multiple internal perspectives propose actions",
                expected_behavior="Personas should generate diverse proposals. "
                                 "persona_proposal_count should be > 1 for deliberation.",
                code_locations=[
                    "persona_runtime.py:PersonaManager",
                    "core_gameplay.py:_collect_persona_proposals",
                ],
                database_tables=["action_traces.persona_proposal_count"],
                test_query="""
                    SELECT 
                        COUNT(*) as total_actions,
                        SUM(CASE WHEN persona_proposal_count > 1 THEN 1 ELSE 0 END) as multi_proposal,
                        AVG(COALESCE(persona_proposal_count, 0)) as avg_proposals
                    FROM action_traces
                    WHERE created_at >= datetime('now', '-6 hours')
                """,
                fix_suggestion="PersonaManager.get_proposals() should return multiple proposals "
                              "from different personas (Cautious, Explorer, etc.)"
            ),
            TheoryRequirement(
                theory=TheoryLayer.CONSCIOUSNESS,
                requirement_id="CON-003",
                description="I-Thread Synthesis: Conflicting proposals should be synthesized",
                expected_behavior="When Stream A and Stream B conflict, synthesis should occur. "
                                 "synthesis_enabled should be TRUE when conflict detected.",
                code_locations=[
                    "core_gameplay.py:_synthesize_conflicting_proposals",
                    "core_gameplay.py:_detect_stream_conflict",
                ],
                database_tables=["action_traces.synthesis_enabled"],
                test_query="""
                    SELECT 
                        COUNT(*) as total_actions,
                        SUM(CASE WHEN synthesis_enabled = TRUE THEN 1 ELSE 0 END) as synthesized
                    FROM action_traces
                    WHERE created_at >= datetime('now', '-6 hours')
                """,
                fix_suggestion="Implement conflict detection between Stream A and B proposals. "
                              "When conflict > threshold, enable synthesis mode."
            ),
            TheoryRequirement(
                theory=TheoryLayer.CONSCIOUSNESS,
                requirement_id="CON-004",
                description="Theory-Gating: Actions should be gated by current working theory",
                expected_behavior="Actions should be scored against agent_theories table. "
                                 "Theory-aligned actions should score higher.",
                code_locations=[
                    "core_gameplay.py:_apply_theory_gating",
                    "scientific_method_engine.py",
                ],
                database_tables=["agent_theories", "action_traces.grounding_score"],
                test_query="""
                    SELECT 
                        COUNT(*) as total_theories,
                        COUNT(DISTINCT game_type) as games_with_theories
                    FROM agent_theories
                    WHERE is_active = 1 AND last_tested_at >= datetime('now', '-6 hours')
                """,
                fix_suggestion="Ensure _select_action queries agent_theories for current game "
                              "and scores proposals against the active hypothesis."
            ),
            
            # ============================================================
            # METALEARNING THEORY REQUIREMENTS
            # ============================================================
            TheoryRequirement(
                theory=TheoryLayer.METALEARNING,
                requirement_id="META-001",
                description="CODS Centralized Validation: CODS watches ALL agent gameplay",
                expected_behavior="CODS should analyze cross-agent patterns and validate discoveries. "
                                 "Not per-agent - centralized watching all agents.",
                code_locations=[
                    "cods_engine.py:CODSEngine",
                    "oracle_interface.py:OracleInterface",
                ],
                database_tables=["cods_game_outcomes", "cods_level_outcomes"],
                test_query="""
                    SELECT 
                        COUNT(*) as total_outcomes,
                        COUNT(DISTINCT agent_id) as unique_agents
                    FROM cods_game_outcomes
                    WHERE created_at >= datetime('now', '-6 hours')
                """,
                fix_suggestion="CODS should be a singleton watching all gameplay, not per-agent. "
                              "Create centralized CODSOracle that aggregates all agent RLVR data."
            ),
            TheoryRequirement(
                theory=TheoryLayer.METALEARNING,
                requirement_id="META-002",
                description="Primitive Unlocking: Agents earn primitives by demonstrating understanding",
                expected_behavior="Agents compose seed primitives -> CODS validates -> unlock polished version. "
                                 "primitive_status should show progression.",
                code_locations=[
                    "primitive_unlock_manager.py",
                    "cods_engine.py:evaluate_for_unlock",
                ],
                database_tables=["primitive_status", "primitive_unlock_attempts"],
                test_query="""
                    SELECT 
                        SUM(CASE WHEN status = 'unlocked' THEN 1 ELSE 0 END) as unlocked,
                        SUM(CASE WHEN status = 'seed' THEN 1 ELSE 0 END) as seed,
                        SUM(CASE WHEN status = 'locked' THEN 1 ELSE 0 END) as locked,
                        COUNT(*) as total
                    FROM primitive_status
                """,
                fix_suggestion="When composed_operators success_rate > threshold, "
                              "check if it matches a locked primitive and unlock it."
            ),
            TheoryRequirement(
                theory=TheoryLayer.METALEARNING,
                requirement_id="META-003",
                description="Operator Composition: Agents combine primitives into composed operators",
                expected_behavior="Agents should create composed_operators from seed primitives. "
                                 "RLVR validates effectiveness across games.",
                code_locations=[
                    "cods_engine.py:compose_operator",
                    "operator_composer.py",
                ],
                database_tables=["composed_operators"],
                test_query="""
                    SELECT 
                        COUNT(*) as total_operators,
                        SUM(CASE WHEN success_rate > 0.1 THEN 1 ELSE 0 END) as effective,
                        AVG(success_rate) as avg_success
                    FROM composed_operators
                """,
                fix_suggestion="Ensure operators are being composed during gameplay "
                              "and their success is tracked via RLVR."
            ),
            TheoryRequirement(
                theory=TheoryLayer.METALEARNING,
                requirement_id="META-004",
                description="Five-Stage Discovery: Salience -> Hypothesis -> Experiment -> Correspondence -> Generalization",
                expected_behavior="Agents should form agent_theories via scientific method. "
                                 "Theories should have tests_conducted/tests_successful counts.",
                code_locations=[
                    "scientific_method_engine.py",
                    "core_gameplay.py:_form_hypothesis",
                ],
                database_tables=["agent_theories", "theory_experiments"],
                test_query="""
                    SELECT 
                        status, 
                        COUNT(*) as count,
                        AVG(tests_conducted) as avg_tests_conducted,
                        AVG(tests_successful) as avg_tests_successful
                    FROM agent_theories
                    WHERE is_active = 1
                    GROUP BY status
                """,
                fix_suggestion="Implement full scientific method cycle. Theories should be "
                              "created during exploration and updated based on outcomes."
            ),
            
            # ============================================================
            # NETWORK THEORY REQUIREMENTS
            # ============================================================
            TheoryRequirement(
                theory=TheoryLayer.NETWORK,
                requirement_id="NET-001",
                description="Viral Packages: Knowledge spreads via database, not direct communication",
                expected_behavior="Successful patterns should become viral_information_packages. "
                                 "Stream B queries these packages.",
                code_locations=[
                    "horizontal_transfer_engine.py",
                    "core_gameplay.py:_query_stream_b",
                ],
                database_tables=["viral_information_packages", "agent_viral_infections"],
                test_query="""
                    SELECT 
                        COUNT(*) as total_packages,
                        SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active,
                        AVG(success_rate) as avg_success
                    FROM viral_information_packages
                """,
                fix_suggestion="When an agent discovers a winning pattern, create a viral package. "
                              "Other agents' Stream B should query this table."
            ),
            TheoryRequirement(
                theory=TheoryLayer.NETWORK,
                requirement_id="NET-002",
                description="Database-as-Organism: Knowledge persists beyond agent lifetime",
                expected_behavior="Winning sequences, hypotheses, and patterns should persist. "
                                 "New agents should access collective wisdom.",
                code_locations=[
                    "database_interface.py",
                    "core_gameplay.py:_load_network_knowledge",
                ],
                database_tables=["winning_sequences", "network_object_control_hypotheses"],
                test_query="""
                    SELECT 
                        COUNT(*) as total_sequences,
                        COUNT(DISTINCT game_type) as unique_games
                    FROM winning_sequences
                    WHERE is_active = TRUE
                """,
                fix_suggestion="Ensure winning sequences are properly saved and queried. "
                              "New agents should inherit network knowledge on creation."
            ),
            TheoryRequirement(
                theory=TheoryLayer.NETWORK,
                requirement_id="NET-003",
                description="Dual Economy: Prestige (social) != Action Budgets (economic)",
                expected_behavior="Prestige affects trust/credibility, NOT action budgets. "
                                 "Action budgets based on role and performance.",
                code_locations=[
                    "prestige_engine.py",
                    "adaptive_action_limits.py",
                ],
                database_tables=["agents.discovery_prestige", "agents.innovation_score"],
                test_query="""
                    SELECT 
                        AVG(discovery_prestige) as avg_prestige,
                        AVG(innovation_score) as avg_innovation
                    FROM agents
                    WHERE is_active = TRUE
                """,
                fix_suggestion="Verify prestige calculation is separate from action budget. "
                              "High prestige = trusted packages, not more compute."
            ),
            
            # ============================================================
            # INTEGRATION REQUIREMENTS
            # ============================================================
            TheoryRequirement(
                theory=TheoryLayer.INTEGRATION,
                requirement_id="INT-001",
                description="Stream B queries CODS viral packages",
                expected_behavior="Stream B should query viral_information_packages populated by CODS. "
                                 "This is how collective wisdom reaches individual agents.",
                code_locations=[
                    "core_gameplay.py:_query_stream_b",
                    "cods_engine.py:create_viral_package",
                ],
                database_tables=["viral_information_packages"],
                test_query="""
                    SELECT 
                        package_type,
                        COUNT(*) as count,
                        AVG(virulence) as avg_virulence
                    FROM viral_information_packages
                    WHERE is_active = TRUE
                    GROUP BY package_type
                """,
                fix_suggestion="Implement _query_stream_b to query viral packages table. "
                              "CODS should create packages when patterns are validated."
            ),
            TheoryRequirement(
                theory=TheoryLayer.INTEGRATION,
                requirement_id="INT-002",
                description="Roles emerge from wA/wB, not assigned statically",
                expected_behavior="Pioneer/Optimizer/Generalist/Exploiter should emerge from "
                                 "self_network_bias (wA/wB), not population percentages.",
                code_locations=[
                    "agent_operating_mode_system.py:assign_mode",
                    "core_gameplay.py",
                ],
                database_tables=["agents.self_network_bias", "agent_operating_modes"],
                test_query="""
                    SELECT 
                        operating_mode,
                        COUNT(*) as count,
                        AVG(a.self_network_bias) as avg_bias
                    FROM agent_operating_modes aom
                    JOIN agents a ON aom.agent_id = a.agent_id
                    WHERE aom.created_at >= datetime('now', '-6 hours')
                    GROUP BY operating_mode
                """,
                fix_suggestion="Modify assign_mode to derive role from self_network_bias: "
                              "wA > 0.7 = Pioneer, wB > 0.7 = Optimizer, balanced = Generalist."
            ),
            TheoryRequirement(
                theory=TheoryLayer.INTEGRATION,
                requirement_id="INT-003",
                description="Imagination Budget allocation for counterfactuals",
                expected_behavior="Imagination budget should be spent on counterfactual rollouts. "
                                 "budget_spend should be > 0 when exploring alternatives.",
                code_locations=[
                    "imagination_budget.py",
                    "counterfactual_analyzer.py",
                    "core_gameplay.py:_run_counterfactual",
                ],
                database_tables=["action_traces.budget_spend", "action_traces.counterfactual_rollouts_used"],
                test_query="""
                    SELECT 
                        COUNT(*) as total_actions,
                        SUM(CASE WHEN budget_spend > 0 THEN 1 ELSE 0 END) as budget_spent,
                        SUM(CASE WHEN counterfactual_rollouts_used > 0 THEN 1 ELSE 0 END) as cf_used,
                        AVG(COALESCE(budget_spend, 0)) as avg_spend
                    FROM action_traces
                    WHERE created_at >= datetime('now', '-6 hours')
                """,
                fix_suggestion="Ensure counterfactual_analyzer is being called and its "
                              "budget consumption is recorded in action_traces."
            ),
        ]
    
    def check_all(self) -> Dict[str, Any]:
        """Run all theory alignment checks."""
        self.results = []
        
        for req in self.requirements:
            result = self._check_requirement(req)
            self.results.append(result)
        
        # Aggregate by theory
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_requirements': len(self.requirements),
            'by_theory': {},
            'misaligned': [],
            'missing': [],
            'aligned': [],
        }
        
        for theory in TheoryLayer:
            theory_results = [r for r in self.results if r.requirement.theory == theory]
            aligned = sum(1 for r in theory_results if r.status == AlignmentStatus.ALIGNED)
            partial = sum(1 for r in theory_results if r.status == AlignmentStatus.PARTIAL)
            misaligned = sum(1 for r in theory_results if r.status == AlignmentStatus.MISALIGNED)
            missing = sum(1 for r in theory_results if r.status == AlignmentStatus.MISSING)
            
            summary['by_theory'][theory.value] = {
                'total': len(theory_results),
                'aligned': aligned,
                'partial': partial,
                'misaligned': misaligned,
                'missing': missing,
                'score': aligned / len(theory_results) if theory_results else 0,
            }
        
        # Collect issues
        for result in self.results:
            if result.status == AlignmentStatus.MISALIGNED:
                summary['misaligned'].append({
                    'id': result.requirement.requirement_id,
                    'description': result.requirement.description,
                    'root_cause': result.root_cause,
                    'fix': result.fix_recommendation,
                })
            elif result.status == AlignmentStatus.MISSING:
                summary['missing'].append({
                    'id': result.requirement.requirement_id,
                    'description': result.requirement.description,
                    'fix': result.fix_recommendation,
                })
            elif result.status == AlignmentStatus.ALIGNED:
                summary['aligned'].append(result.requirement.requirement_id)
        
        return summary
    
    def _check_requirement(self, req: TheoryRequirement) -> AlignmentResult:
        """Check a single requirement against actual code behavior."""
        evidence = {}
        actual_behavior = "Unknown"
        status = AlignmentStatus.UNKNOWN
        root_cause = None
        fix_recommendation = req.fix_suggestion
        code_trace = []
        
        # Run test query if available
        if req.test_query:
            try:
                query_result = self.db.execute_query(req.test_query)
                evidence['query_result'] = query_result[0] if query_result else None
                
                # Analyze query result to determine status
                status, actual_behavior, root_cause = self._analyze_query_result(
                    req, evidence['query_result']
                )
            except Exception as e:
                evidence['query_error'] = str(e)
                status = AlignmentStatus.UNKNOWN
                actual_behavior = f"Query failed: {e}"
        
        # Check code locations exist
        for location in req.code_locations:
            file_path, func_name = location.split(':') if ':' in location else (location, None)
            code_exists = self._check_code_location(file_path, func_name)
            evidence[f'code_{location}'] = code_exists
            code_trace.append(f"{location}: {'EXISTS' if code_exists else 'MISSING'}")
        
        return AlignmentResult(
            requirement=req,
            status=status,
            actual_behavior=actual_behavior,
            evidence=evidence,
            root_cause=root_cause,
            fix_recommendation=fix_recommendation,
            code_trace=code_trace,
        )
    
    def _analyze_query_result(
        self, req: TheoryRequirement, result: Optional[Dict]
    ) -> Tuple[AlignmentStatus, str, Optional[str]]:
        """Analyze query result to determine alignment status."""
        if result is None:
            return AlignmentStatus.MISSING, "No data returned", "Table may be empty or query failed"
        
        # Requirement-specific analysis
        req_id = req.requirement_id
        
        if req_id == "CON-001":  # Two Streams
            bias_range = (result.get('max_bias', 0) or 0) - (result.get('min_bias', 0) or 0)
            if bias_range > 0.3:
                return AlignmentStatus.ALIGNED, f"wA/wB range={bias_range:.2f}", None
            elif bias_range > 0.1:
                return AlignmentStatus.PARTIAL, f"wA/wB range={bias_range:.2f} (low diversity)", \
                       "Agents not learning to differentiate stream trust"
            else:
                return AlignmentStatus.MISALIGNED, f"wA/wB range={bias_range:.2f} (no diversity)", \
                       "self_network_bias not being updated based on outcomes"
        
        elif req_id == "CON-002":  # Persona Ensemble
            total = result.get('total_actions', 0) or 0
            multi = result.get('multi_proposal', 0) or 0
            if total == 0:
                return AlignmentStatus.MISSING, "No action data", "No actions recorded recently"
            multi_rate = multi / total
            if multi_rate > 0.3:
                return AlignmentStatus.ALIGNED, f"{multi_rate:.0%} multi-proposal", None
            elif multi_rate > 0.05:
                return AlignmentStatus.PARTIAL, f"{multi_rate:.0%} multi-proposal", \
                       "Personas generating some proposals but not consistently"
            else:
                return AlignmentStatus.MISALIGNED, f"{multi_rate:.0%} multi-proposal (none)", \
                       "PersonaManager not being called or not returning multiple proposals"
        
        elif req_id == "CON-003":  # I-Thread Synthesis
            total = result.get('total_actions', 0) or 0
            synth = result.get('synthesized', 0) or 0
            if total == 0:
                return AlignmentStatus.MISSING, "No action data", "No actions recorded recently"
            synth_rate = synth / total
            if synth_rate > 0.1:
                return AlignmentStatus.ALIGNED, f"{synth_rate:.0%} synthesized", None
            elif synth_rate > 0.01:
                return AlignmentStatus.PARTIAL, f"{synth_rate:.0%} synthesized", \
                       "Synthesis rare - conflict detection may be too strict"
            else:
                return AlignmentStatus.MISALIGNED, f"{synth_rate:.0%} synthesized (none)", \
                       "synthesis_enabled never set TRUE - conflict detection not working"
        
        elif req_id == "CON-004":  # Theory-Gating
            theories = result.get('total_theories', 0) or 0
            games = result.get('games_with_theories', 0) or 0
            if theories > 0:
                return AlignmentStatus.ALIGNED, f"{theories} theories across {games} games", None
            else:
                return AlignmentStatus.MISALIGNED, "No working theories", \
                       "Scientific method engine not creating theories"
        
        elif req_id == "META-001":  # CODS Centralized
            outcomes = result.get('total_outcomes', 0) or 0
            agents = result.get('unique_agents', 0) or 0
            if outcomes > 0 and agents > 1:
                return AlignmentStatus.ALIGNED, f"{outcomes} outcomes from {agents} agents", None
            elif outcomes > 0:
                return AlignmentStatus.PARTIAL, f"{outcomes} outcomes from {agents} agent", \
                       "CODS running but may not be aggregating cross-agent"
            else:
                return AlignmentStatus.MISSING, "No CODS outcomes", \
                       "CODS not recording gameplay analysis"
        
        elif req_id == "META-002":  # Primitive Unlocking
            unlocked = result.get('unlocked', 0) or 0
            seed = result.get('seed', 0) or 0
            locked = result.get('locked', 0) or 0
            total = result.get('total', 0) or 0
            
            if unlocked > 0:
                return AlignmentStatus.ALIGNED, f"{unlocked} unlocked, {seed} seed, {locked} locked", None
            elif total > 0:
                return AlignmentStatus.PARTIAL, f"0 unlocked, {seed} seed, {locked} locked", \
                       "Primitives exist but none unlocked yet"
            else:
                return AlignmentStatus.MISSING, "No primitive status data", \
                       "primitive_status table may be empty"
        
        elif req_id == "META-003":  # Operator Composition
            total = result.get('total_operators', 0) or 0
            effective = result.get('effective', 0) or 0
            if total > 0 and effective > 0:
                return AlignmentStatus.ALIGNED, f"{effective}/{total} effective operators", None
            elif total > 0:
                return AlignmentStatus.PARTIAL, f"{total} operators, 0 effective", \
                       "Operators being created but not proving effective"
            else:
                return AlignmentStatus.MISSING, "No composed operators", \
                       "Operator composition not happening"
        
        elif req_id == "META-004":  # Five-Stage Discovery
            # Check if there are theories in different status stages
            if result is None:
                return AlignmentStatus.MISSING, "No data returned", "Query failed"
            
            # Result might be a single row or list of rows by status
            # Try to extract meaningful data
            if isinstance(result, dict):
                status = result.get('status', 'unknown')
                count = result.get('count', 0) or 0
                tests = result.get('avg_tests_conducted', 0) or 0
                if count > 0 and tests > 0:
                    return AlignmentStatus.ALIGNED, f"{count} theories with avg {tests:.1f} tests", None
                elif count > 0:
                    return AlignmentStatus.PARTIAL, f"{count} theories, no testing yet", \
                           "Theories exist but experiments not running"
            return AlignmentStatus.PARTIAL, "Check agent_theories table", None
        
        elif req_id == "NET-001":  # Viral Packages
            total = result.get('total_packages', 0) or 0
            active = result.get('active', 0) or 0
            if active > 0:
                return AlignmentStatus.ALIGNED, f"{active} active viral packages", None
            elif total > 0:
                return AlignmentStatus.PARTIAL, f"{total} packages, none active", \
                       "Packages exist but marked inactive"
            else:
                return AlignmentStatus.MISSING, "No viral packages", \
                       "CODS not creating viral packages from discoveries"
        
        elif req_id == "NET-002":  # Database-as-Organism
            sequences = result.get('total_sequences', 0) or 0
            games = result.get('unique_games', 0) or 0
            if sequences > 0:
                return AlignmentStatus.ALIGNED, f"{sequences} sequences for {games} games", None
            else:
                return AlignmentStatus.MISSING, "No winning sequences", \
                       "Sequences not being saved or all inactive"
        
        elif req_id == "NET-003":  # Dual Economy
            prestige = result.get('avg_prestige', 0) or 0
            return AlignmentStatus.PARTIAL, f"Avg prestige={prestige:.2f}", \
                   "Need to verify prestige != action budget correlation"
        
        elif req_id == "INT-001":  # Stream B -> CODS
            if result:
                return AlignmentStatus.PARTIAL, "Viral packages exist", \
                       "Need to verify Stream B actually queries them"
            else:
                return AlignmentStatus.MISSING, "No viral package data", None
        
        elif req_id == "INT-002":  # Emergent Roles
            # Analyze if bias correlates with role
            return AlignmentStatus.PARTIAL, "Check role-bias correlation", \
                   "Roles may be assigned statically, not emergent"
        
        elif req_id == "INT-003":  # Imagination Budget
            total = result.get('total_actions', 0) or 0
            spent = result.get('budget_spent', 0) or 0
            cf = result.get('cf_used', 0) or 0
            if total == 0:
                return AlignmentStatus.MISSING, "No action data", None
            spend_rate = spent / total
            cf_rate = cf / total
            if spend_rate > 0.05 or cf_rate > 0.01:
                return AlignmentStatus.ALIGNED, f"budget={spend_rate:.0%}, cf={cf_rate:.0%}", None
            else:
                return AlignmentStatus.MISALIGNED, f"budget={spend_rate:.0%}, cf={cf_rate:.0%} (none)", \
                       "Counterfactual analyzer not running or not recording budget"
        
        # Default
        return AlignmentStatus.UNKNOWN, str(result), None
    
    def _check_code_location(self, file_path: str, func_name: Optional[str]) -> bool:
        """Check if a code location exists."""
        try:
            full_path = os.path.join(
                os.path.dirname(__file__),
                file_path
            )
            if not os.path.exists(full_path):
                return False
            
            if func_name:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return f"def {func_name}" in content or f"class {func_name}" in content
            return True
        except Exception:
            return False
    
    def generate_fix_plan(self) -> str:
        """Generate a prioritized fix plan based on misalignments."""
        lines = [
            "# Theory Alignment Fix Plan",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Priority 1: CRITICAL (Missing or Misaligned)",
            "",
        ]
        
        critical = [r for r in self.results if r.status in 
                   (AlignmentStatus.MISALIGNED, AlignmentStatus.MISSING)]
        
        for i, result in enumerate(critical, 1):
            lines.append(f"### {i}. {result.requirement.requirement_id}: {result.requirement.description[:60]}...")
            lines.append(f"**Status**: {result.status.value.upper()}")
            lines.append(f"**Actual**: {result.actual_behavior}")
            if result.root_cause:
                lines.append(f"**Root Cause**: {result.root_cause}")
            lines.append(f"**Fix**: {result.fix_recommendation}")
            lines.append("")
            lines.append("**Code Locations**:")
            for loc in result.requirement.code_locations:
                lines.append(f"- `{loc}`")
            lines.append("")
        
        lines.append("## Priority 2: PARTIAL (Needs Improvement)")
        lines.append("")
        
        partial = [r for r in self.results if r.status == AlignmentStatus.PARTIAL]
        for i, result in enumerate(partial, 1):
            lines.append(f"### {i}. {result.requirement.requirement_id}: {result.actual_behavior}")
            if result.root_cause:
                lines.append(f"- Root cause: {result.root_cause}")
            lines.append("")
        
        return "\n".join(lines)
    
    def print_report(self) -> None:
        """Print a formatted alignment report."""
        summary = self.check_all()
        
        print("\n" + "=" * 70)
        print("       THEORY ALIGNMENT REPORT")
        print("=" * 70)
        print(f"  Timestamp: {summary['timestamp']}")
        print(f"  Total Requirements: {summary['total_requirements']}")
        print("=" * 70)
        
        for theory, data in summary['by_theory'].items():
            score_pct = data['score'] * 100
            status_icon = "[OK]" if score_pct >= 80 else ("[-]" if score_pct >= 50 else "[X]")
            print(f"\n{status_icon} {theory.upper()}: {score_pct:.0f}% aligned")
            print(f"    Aligned: {data['aligned']}, Partial: {data['partial']}, "
                  f"Misaligned: {data['misaligned']}, Missing: {data['missing']}")
        
        if summary['misaligned']:
            print("\n" + "-" * 70)
            print("[X] MISALIGNED (requires fix):")
            for issue in summary['misaligned']:
                print(f"    {issue['id']}: {issue['description'][:50]}...")
                if issue['root_cause']:
                    print(f"      -> Root cause: {issue['root_cause']}")
        
        if summary['missing']:
            print("\n" + "-" * 70)
            print("[?] MISSING (no data):")
            for issue in summary['missing']:
                print(f"    {issue['id']}: {issue['description'][:50]}...")
        
        print("\n" + "=" * 70)


def main():
    """Run theory alignment check."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check code alignment with theories")
    parser.add_argument('--fix-plan', action='store_true', help='Generate fix plan')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--grade', action='store_true', help='Output letter grade')
    args = parser.parse_args()
    
    db = DatabaseInterface()
    checker = TheoryAlignmentChecker(db)
    
    if args.fix_plan:
        checker.check_all()
        print(checker.generate_fix_plan())
    elif args.json:
        import json
        summary = checker.check_all()
        print(json.dumps(summary, indent=2, default=str))
    elif args.grade:
        summary = checker.check_all()
        
        # Calculate weighted score (misaligned = 0, partial = 0.5, aligned = 1)
        total_score = 0
        total_weight = 0
        for theory, data in summary['by_theory'].items():
            weight = 1.0  # Equal weight per theory
            theory_score = (data['aligned'] + 0.5 * data['partial']) / data['total'] if data['total'] > 0 else 0
            total_score += theory_score * weight
            total_weight += weight
        
        overall_pct = (total_score / total_weight * 100) if total_weight > 0 else 0
        
        # Letter grade
        if overall_pct >= 90:
            grade = "A"
        elif overall_pct >= 80:
            grade = "B"
        elif overall_pct >= 70:
            grade = "C"
        elif overall_pct >= 60:
            grade = "D"
        else:
            grade = "F"
        
        critical_issues = len(summary['misaligned']) + len(summary['missing'])
        
        print("=" * 50)
        print("        SELF-GRADE REPORT")
        print("=" * 50)
        print(f"  Overall Score: {overall_pct:.1f}%")
        print(f"  Letter Grade:  {grade}")
        print(f"  Critical Issues: {critical_issues}")
        print("=" * 50)
        
        for theory, data in summary['by_theory'].items():
            theory_pct = data['score'] * 100
            print(f"  {theory.upper():15} {theory_pct:5.0f}%")
        
        print("=" * 50)
        
        if critical_issues > 0:
            print("\n[NEEDS WORK] Run --fix-plan for recommendations")
        else:
            print("\n[PASSING] All critical requirements met")
    else:
        checker.print_report()


if __name__ == '__main__':
    main()
