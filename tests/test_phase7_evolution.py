"""
Phase 7 Tests - Graph Evolution & Process Knowledge.

Tests for:
1. Rung role taxonomy
2. Path crystallization
3. Process knowledge extraction
4. Integration between components
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

from typing import Dict, List

import pytest

from engines.cognition.path_crystallization import (
    CrystallizedPath,
    DomainStats,
    PathCrystallizer,
)
from engines.cognition.process_knowledge import (
    AbstractPattern,
    PatternMatch,
    ProcessKnowledgeExtractor,
)

# Phase 7 imports
from engines.cognition.rung_roles import (
    RUNG_ROLE_MAP,
    RungRole,
    analyze_path_structure,
    count_backtrack_transitions,
    extract_role_sequence,
    get_compatible_roles,
    get_role_for_phase,
    get_rung_role,
    get_rungs_by_role,
    is_backtrack_transition,
    is_valid_transition,
    role_sequence_to_id,
    suggest_next_role,
)

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def crystallizer():
    """Create PathCrystallizer for testing."""
    return PathCrystallizer()


@pytest.fixture
def extractor():
    """Create ProcessKnowledgeExtractor for testing."""
    return ProcessKnowledgeExtractor()


# =============================================================================
# RUNG ROLE TESTS
# =============================================================================

class TestRungRole:
    """Tests for RungRole enum."""

    def test_role_values(self):
        """Test role enum values."""
        assert RungRole.ENTRY.value == "entry"
        assert RungRole.LEVERAGE.value == "leverage"
        assert RungRole.COMPOUNDING.value == "compounding"
        assert RungRole.RESOLUTION.value == "resolution"

    def test_role_descriptions(self):
        """Test role descriptions."""
        assert "starting" in RungRole.ENTRY.description.lower()
        assert "deeper" in RungRole.LEVERAGE.description.lower()
        assert "multiply" in RungRole.COMPOUNDING.description.lower()
        assert "action" in RungRole.RESOLUTION.description.lower()

    def test_confidence_ranges(self):
        """Test typical confidence ranges."""
        entry_range = RungRole.ENTRY.typical_confidence_range
        resolution_range = RungRole.RESOLUTION.typical_confidence_range

        # Entry has lower confidence than resolution
        assert entry_range[1] < resolution_range[1]


class TestRungRoleMapping:
    """Tests for rung role mapping functions."""

    def test_get_rung_role_known(self):
        """Test getting role for known rungs."""
        assert get_rung_role("survey") == RungRole.ENTRY
        assert get_rung_role("control_tracker") == RungRole.LEVERAGE
        assert get_rung_role("network_wisdom") == RungRole.COMPOUNDING
        assert get_rung_role("action_selection") == RungRole.RESOLUTION

    def test_get_rung_role_unknown(self):
        """Test getting role for unknown rung defaults to ENTRY."""
        assert get_rung_role("unknown_rung") == RungRole.ENTRY

    def test_get_role_for_phase(self):
        """Test phase to role mapping."""
        assert get_role_for_phase("exploration") == RungRole.ENTRY
        assert get_role_for_phase("building") == RungRole.LEVERAGE
        assert get_role_for_phase("connecting") == RungRole.COMPOUNDING
        assert get_role_for_phase("resolving") == RungRole.RESOLUTION

    def test_get_rungs_by_role(self):
        """Test getting rungs by role."""
        entry_rungs = get_rungs_by_role(RungRole.ENTRY)
        assert "survey" in entry_rungs

        resolution_rungs = get_rungs_by_role(RungRole.RESOLUTION)
        assert "action_selection" in resolution_rungs


class TestRoleTransitions:
    """Tests for role transition logic."""

    def test_valid_progression(self):
        """Test valid forward progressions."""
        assert is_valid_transition(RungRole.ENTRY, RungRole.LEVERAGE)
        assert is_valid_transition(RungRole.LEVERAGE, RungRole.COMPOUNDING)
        assert is_valid_transition(RungRole.COMPOUNDING, RungRole.RESOLUTION)

    def test_valid_stay(self):
        """Test staying in same role is valid."""
        assert is_valid_transition(RungRole.ENTRY, RungRole.ENTRY)
        assert is_valid_transition(RungRole.LEVERAGE, RungRole.LEVERAGE)

    def test_backtrack_detection(self):
        """Test backtrack transitions."""
        assert is_backtrack_transition(RungRole.LEVERAGE, RungRole.ENTRY)
        assert is_backtrack_transition(RungRole.COMPOUNDING, RungRole.LEVERAGE)
        assert not is_backtrack_transition(RungRole.ENTRY, RungRole.LEVERAGE)


class TestPathAnalysis:
    """Tests for path analysis functions."""

    def test_extract_role_sequence(self):
        """Test extracting role sequence from path."""
        path = ["survey", "control_tracker", "network_wisdom", "action_selection"]
        roles = extract_role_sequence(path)

        assert roles[0] == RungRole.ENTRY
        assert roles[1] == RungRole.LEVERAGE
        assert roles[2] == RungRole.COMPOUNDING
        assert roles[3] == RungRole.RESOLUTION

    def test_role_sequence_to_id(self):
        """Test converting role sequence to ID."""
        roles = [RungRole.ENTRY, RungRole.LEVERAGE, RungRole.RESOLUTION]
        pattern_id = role_sequence_to_id(roles)
        assert pattern_id == "ENTRY->LEVERAGE->RESOLUTION"

    def test_count_backtrack_transitions(self):
        """Test counting backtracks in path."""
        # Progressive path - no backtracks
        progressive = ["survey", "control_tracker", "network_wisdom"]
        assert count_backtrack_transitions(progressive) == 0

        # Path with backtrack - compounding back to entry
        backtrack = ["network_wisdom", "survey"]
        assert count_backtrack_transitions(backtrack) >= 1

    def test_analyze_path_structure(self):
        """Test full path structure analysis."""
        path = ["survey", "control_tracker", "action_selection"]
        analysis = analyze_path_structure(path)

        assert analysis['length'] == 3
        assert analysis['pattern_id'] == "ENTRY->LEVERAGE->RESOLUTION"
        assert 'role_distribution' in analysis


class TestEpistemicCompatibility:
    """Tests for epistemic quadrant compatibility."""

    def test_kk_prefers_resolution(self):
        """KK (known-known) should prefer resolution."""
        roles = get_compatible_roles('KK')
        assert RungRole.RESOLUTION in roles

    def test_uu_prefers_entry(self):
        """UU (unknown-unknown) should prefer entry."""
        roles = get_compatible_roles('UU')
        assert RungRole.ENTRY in roles

    def test_suggest_next_role_high_confidence(self):
        """High confidence should progress toward resolution."""
        assert suggest_next_role(RungRole.ENTRY, 0.8) == RungRole.LEVERAGE
        assert suggest_next_role(RungRole.COMPOUNDING, 0.9) == RungRole.RESOLUTION

    def test_suggest_next_role_low_confidence(self):
        """Low confidence should stay or backtrack."""
        result = suggest_next_role(RungRole.RESOLUTION, 0.3)
        # Should backtrack or stay
        assert result in (RungRole.LEVERAGE, RungRole.COMPOUNDING, RungRole.RESOLUTION)


# =============================================================================
# PATH CRYSTALLIZATION TESTS
# =============================================================================

class TestCrystallizedPath:
    """Tests for CrystallizedPath dataclass."""

    def test_create_path(self):
        """Test creating a crystallized path."""
        cp = CrystallizedPath(
            domain_signature="physics",
            path=["survey", "physics_probe", "action_selection"],
        )
        assert cp.domain_signature == "physics"
        assert len(cp.path) == 3

    def test_path_id(self):
        """Test path ID generation."""
        cp = CrystallizedPath(
            domain_signature="physics",
            path=["a", "b", "c"],
        )
        assert cp.path_id == "a->b->c"

    def test_update_stats(self):
        """Test updating path statistics."""
        cp = CrystallizedPath(domain_signature="physics", path=["a"])

        cp.update_stats(confidence=0.9, ticks=5, success=True)
        assert cp.traversal_count == 1
        assert cp.success_count == 1
        assert cp.avg_confidence == 0.9

        cp.update_stats(confidence=0.8, ticks=7, success=True)
        assert cp.traversal_count == 2
        assert cp.success_count == 2
        assert abs(cp.avg_confidence - 0.85) < 0.0001  # Float comparison

    def test_is_reliable_threshold(self):
        """Test reliability with domain-relative threshold."""
        cp = CrystallizedPath(
            domain_signature="physics",
            path=["a"],
            traversal_count=10,
            success_count=10,
            avg_confidence=0.9,
            avg_ticks=5,
        )

        # With 100 games, threshold = 10, should be reliable
        assert cp.is_reliable(domain_game_count=100) is True

        # With 10 games, threshold = 5, should be reliable
        assert cp.is_reliable(domain_game_count=10) is True

    def test_is_reliable_confidence(self):
        """Test reliability requires high confidence."""
        cp = CrystallizedPath(
            domain_signature="physics",
            path=["a"],
            traversal_count=20,
            success_count=20,
            avg_confidence=0.7,  # Too low
            avg_ticks=5,
        )
        assert cp.is_reliable() is False

    def test_serialization(self):
        """Test to_dict and from_dict."""
        cp = CrystallizedPath(
            domain_signature="physics",
            path=["a", "b"],
            traversal_count=5,
            avg_confidence=0.88,
        )
        data = cp.to_dict()
        restored = CrystallizedPath.from_dict(data)

        assert restored.domain_signature == cp.domain_signature
        assert restored.path == cp.path
        assert restored.traversal_count == cp.traversal_count


class TestPathCrystallizer:
    """Tests for PathCrystallizer."""

    def test_record_successful_path(self, crystallizer):
        """Test recording a successful path."""
        cp = crystallizer.record_successful_path(
            domain="physics",
            path=["survey", "physics_probe", "action_selection"],
            confidence=0.9,
            ticks=8,
        )

        assert cp.domain_signature == "physics"
        assert cp.traversal_count == 1

    def test_multiple_recordings_accumulate(self, crystallizer):
        """Test that multiple recordings accumulate."""
        path = ["a", "b", "c"]

        for i in range(5):
            crystallizer.record_successful_path(
                domain="physics",
                path=path,
                confidence=0.85 + i * 0.02,
                ticks=10 - i,
            )

        # Should be same path record updated
        assert len(crystallizer.path_history["physics"]) == 1
        cp = crystallizer.path_history["physics"][0]
        assert cp.traversal_count == 5

    def test_get_crystallized_path_none(self, crystallizer):
        """Test getting crystallized path when none exists."""
        result = crystallizer.get_crystallized_path("unknown_domain")
        assert result is None

    def test_get_crystallized_path_after_enough_traversals(self, crystallizer):
        """Test crystallization after enough successful traversals."""
        path = ["survey", "control", "action"]

        # Record many successful traversals
        for _ in range(15):
            crystallizer.record_successful_path(
                domain="physics",
                path=path,
                confidence=0.9,
                ticks=5,
            )

        result = crystallizer.get_crystallized_path("physics")
        assert result == path

    def test_domain_stats_tracking(self, crystallizer):
        """Test that domain stats are tracked."""
        crystallizer.record_successful_path(
            domain="physics",
            path=["a"],
            confidence=0.9,
            ticks=5,
        )
        crystallizer.record_failed_path(
            domain="physics",
            path=["a"],
            confidence=0.3,
            ticks=20,
        )

        stats = crystallizer.domain_stats.get("physics")
        assert stats is not None
        assert stats.total_games == 2
        assert stats.successful_games == 1

    def test_get_statistics(self, crystallizer):
        """Test getting crystallizer statistics."""
        crystallizer.record_successful_path(
            domain="physics",
            path=["a", "b"],
            confidence=0.9,
            ticks=5,
        )

        stats = crystallizer.get_statistics()
        assert stats['total_domains'] == 1
        assert stats['total_paths'] == 1


# =============================================================================
# PROCESS KNOWLEDGE TESTS
# =============================================================================

class TestAbstractPattern:
    """Tests for AbstractPattern dataclass."""

    def test_create_pattern(self):
        """Test creating an abstract pattern."""
        pattern = AbstractPattern(
            pattern_id="ENTRY->LEVERAGE->RESOLUTION",
            role_sequence=[RungRole.ENTRY, RungRole.LEVERAGE, RungRole.RESOLUTION],
        )
        assert pattern.pattern_id == "ENTRY->LEVERAGE->RESOLUTION"
        assert len(pattern.role_sequence) == 3

    def test_add_instantiation(self):
        """Test adding domain instantiation."""
        pattern = AbstractPattern(
            pattern_id="ENTRY->RESOLUTION",
            role_sequence=[RungRole.ENTRY, RungRole.RESOLUTION],
        )

        pattern.add_instantiation("physics", ["survey", "action_selection"], success=True)

        assert pattern.success_count == 1
        assert "physics" in pattern.domain_instantiations
        assert pattern.domain_instantiations["physics"] == ["survey", "action_selection"]

    def test_domain_success_rate(self):
        """Test domain-specific success rate tracking."""
        pattern = AbstractPattern(
            pattern_id="ENTRY->RESOLUTION",
            role_sequence=[RungRole.ENTRY, RungRole.RESOLUTION],
        )

        # Add successes and failures
        pattern.add_instantiation("physics", ["a", "b"], success=True)
        pattern.add_instantiation("physics", ["a", "b"], success=True)
        pattern.add_instantiation("physics", ["a", "b"], success=False)

        rate = pattern.get_domain_success_rate("physics")
        assert abs(rate - 2/3) < 0.01

    def test_serialization(self):
        """Test to_dict and from_dict."""
        pattern = AbstractPattern(
            pattern_id="ENTRY->LEVERAGE",
            role_sequence=[RungRole.ENTRY, RungRole.LEVERAGE],
            success_count=5,
        )
        pattern.add_instantiation("physics", ["a", "b"], success=True)

        data = pattern.to_dict()
        restored = AbstractPattern.from_dict(data)

        assert restored.pattern_id == pattern.pattern_id
        assert restored.success_count == 6  # 5 + 1 from add_instantiation
        assert "physics" in restored.domain_instantiations


class TestProcessKnowledgeExtractor:
    """Tests for ProcessKnowledgeExtractor."""

    def test_extract_pattern(self, extractor):
        """Test pattern extraction from path."""
        path = ["survey", "control_tracker", "action_selection"]
        pattern_id = extractor.extract_pattern(path)

        assert "ENTRY" in pattern_id
        assert "LEVERAGE" in pattern_id
        assert "RESOLUTION" in pattern_id

    def test_record_success(self, extractor):
        """Test recording successful path."""
        path = ["survey", "physics_probe", "action_selection"]
        pattern = extractor.record_success("physics", path)

        assert pattern is not None
        assert pattern.success_count == 1
        assert "physics" in pattern.domain_instantiations

    def test_patterns_accumulate(self, extractor):
        """Test that same pattern type accumulates."""
        # Both paths have same role pattern: ENTRY->LEVERAGE->RESOLUTION
        path1 = ["survey", "control_tracker", "action_selection"]
        path2 = ["pattern_recognition", "physics_probe", "final_decision"]

        extractor.record_success("domain1", path1)
        extractor.record_success("domain2", path2)

        # Should create same pattern with two domain instantiations
        pattern_id = extractor.extract_pattern(path1)
        pattern = extractor.patterns.get(pattern_id)

        assert pattern is not None
        assert pattern.success_count == 2
        assert "domain1" in pattern.domain_instantiations
        assert "domain2" in pattern.domain_instantiations

    def test_suggest_path_for_new_domain(self, extractor):
        """Test suggesting path for new domain."""
        # Record some successful paths
        path = ["survey", "control_tracker", "action_selection"]
        for _ in range(5):
            extractor.record_success("physics", path)

        # Available rungs for new domain
        available = {
            "pattern_recognition": RungRole.ENTRY,
            "hypothesis_testing": RungRole.LEVERAGE,
            "optimal_sequence": RungRole.RESOLUTION,
        }

        suggested = extractor.suggest_path_for_new_domain("new_domain", available)

        # Should suggest a path with same role pattern
        assert suggested is not None
        assert len(suggested) == 3

    def test_get_best_pattern_for_domain(self, extractor):
        """Test getting best pattern for a specific domain."""
        # Record different paths in same domain
        path1 = ["survey", "action_selection"]  # ENTRY->RESOLUTION
        path2 = ["survey", "control_tracker", "network_wisdom", "action_selection"]

        # Path1 more successful
        for _ in range(8):
            extractor.record_success("physics", path1)
        for _ in range(2):
            extractor.record_success("physics", path2)

        # Should return more successful path
        result = extractor.get_best_pattern_for_domain("physics")
        assert result == path1

    def test_find_matching_patterns(self, extractor):
        """Test finding patterns that match available rungs."""
        extractor.record_success("physics", ["survey", "action_selection"])
        extractor.record_success("symbolic", ["pattern_recognition", "optimal_sequence"])

        available = {
            "survey": RungRole.ENTRY,
            "action_selection": RungRole.RESOLUTION,
        }

        matches = extractor.find_matching_patterns(available)

        # Should find at least the ENTRY->RESOLUTION pattern
        assert len(matches) >= 1
        assert all(isinstance(m, PatternMatch) for m in matches)

    def test_get_statistics(self, extractor):
        """Test getting extractor statistics."""
        extractor.record_success("physics", ["survey", "action_selection"])
        extractor.record_success("symbolic", ["survey", "action_selection"])

        stats = extractor.get_statistics()

        assert stats['total_patterns'] >= 1
        assert stats['total_paths_recorded'] == 2
        assert stats['domains_covered'] == 2

    def test_compare_domains(self, extractor):
        """Test comparing pattern usage between domains."""
        # Same pattern in both domains
        extractor.record_success("physics", ["survey", "action_selection"])
        extractor.record_success("symbolic", ["survey", "action_selection"])

        # Different pattern only in physics
        extractor.record_success("physics", ["survey", "control_tracker", "action_selection"])

        comparison = extractor.compare_domains("physics", "symbolic")

        assert comparison['similarity'] > 0
        assert len(comparison['shared_patterns']) >= 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestPhase7Integration:
    """Integration tests for Phase 7 components."""

    def test_roles_to_crystallization_flow(self):
        """Test flow from role taxonomy to path crystallization."""
        crystallizer = PathCrystallizer()

        # Create path using role-appropriate rungs
        path = [
            "survey",           # ENTRY
            "control_tracker",  # LEVERAGE
            "network_wisdom",   # COMPOUNDING
            "action_selection", # RESOLUTION
        ]

        # Verify roles
        roles = extract_role_sequence(path)
        assert roles == [
            RungRole.ENTRY,
            RungRole.LEVERAGE,
            RungRole.COMPOUNDING,
            RungRole.RESOLUTION,
        ]

        # Record as successful multiple times
        for _ in range(15):
            crystallizer.record_successful_path(
                domain="test_domain",
                path=path,
                confidence=0.92,
                ticks=6,
            )

        # Should be crystallized
        result = crystallizer.get_crystallized_path("test_domain")
        assert result == path

    def test_crystallization_to_process_knowledge(self):
        """Test flow from crystallization to process knowledge."""
        crystallizer = PathCrystallizer()
        extractor = ProcessKnowledgeExtractor()

        path = ["survey", "physics_probe", "action_selection"]

        # Record in crystallizer
        for _ in range(10):
            crystallizer.record_successful_path(
                domain="physics",
                path=path,
                confidence=0.9,
                ticks=5,
            )
            # Also record in extractor
            extractor.record_success("physics", path)

        # Get crystallized path
        crystallized = crystallizer.get_crystallized_path("physics")

        # Use pattern to suggest for new domain
        available = {
            "pattern_recognition": RungRole.ENTRY,
            "hypothesis_testing": RungRole.LEVERAGE,
            "optimal_sequence": RungRole.RESOLUTION,
        }

        suggested = extractor.suggest_path_for_new_domain("new_domain", available)

        # Should have same role pattern
        original_roles = extract_role_sequence(crystallized)
        suggested_roles = extract_role_sequence(suggested)

        assert original_roles == suggested_roles

    def test_full_phase7_workflow(self):
        """Test complete Phase 7 workflow."""
        crystallizer = PathCrystallizer()
        extractor = ProcessKnowledgeExtractor()

        # Simulate multiple games in multiple domains
        domains = {
            "physics": ["survey", "physics_probe", "action_selection"],
            "symbolic": ["pattern_recognition", "rule_transfer", "optimal_sequence"],
        }

        for domain, path in domains.items():
            for i in range(12):
                # Record successes (80% success rate)
                success = i < 10

                if success:
                    crystallizer.record_successful_path(
                        domain=domain,
                        path=path,
                        confidence=0.88,
                        ticks=7,
                    )
                    extractor.record_success(domain, path)
                else:
                    crystallizer.record_failed_path(
                        domain=domain,
                        path=path,
                        confidence=0.3,
                        ticks=25,
                    )
                    extractor.record_failure(domain, path)

        # Check crystallization
        crystal_stats = crystallizer.get_statistics()
        assert crystal_stats['total_domains'] == 2

        # Check process knowledge
        extract_stats = extractor.get_statistics()
        assert extract_stats['total_patterns'] >= 1

        # Compare domains
        comparison = extractor.compare_domains("physics", "symbolic")
        # Different patterns so similarity might be 0 or low
        assert 'similarity' in comparison


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
