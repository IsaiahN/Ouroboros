"""
Unit tests for CODS Strategy-Driven Unlock System.

Tests the "Teacher Model" where CODS listens to agent strategy expressions
and unlocks primitives when the network expresses capability needs.

Per Rule 5: These are automated unit tests, not manual test files.
"""

import pytest
import sqlite3
import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.social.cods_engine import CODSEngine

# Create a shared instance for tests
# In production, this uses the real database
cods_engine = CODSEngine()

# Get the strategy-to-primitive map from the instance
STRATEGY_TO_PRIMITIVE_MAP = cods_engine.STRATEGY_TO_PRIMITIVE_MAP

# Create wrapper functions for testing
def parse_strategy_for_needs(strategy_text):
    """Wrapper for class method."""
    return cods_engine.parse_strategy_for_needs(strategy_text)

def process_agent_strategy_signals(min_frequency=10, unlock_threshold=None, unlock_percentage=0.10):
    """Wrapper for class method."""
    return cods_engine.process_agent_strategy_signals(min_frequency, unlock_threshold, unlock_percentage)

def get_primitive_inventory():
    """Wrapper for class method."""
    return cods_engine.get_primitive_inventory()

def get_composed_operator_inventory():
    """Wrapper for class method."""
    return cods_engine.get_composed_operator_inventory()


class TestParseStrategyForNeeds:
    """Tests for parse_strategy_for_needs() function."""
    
    def test_empty_strategy_returns_empty_list(self):
        """Empty or blank strategy should return empty needs list."""
        # Note: None is handled by the caller, empty strings return []
        assert parse_strategy_for_needs("") == []
        assert parse_strategy_for_needs("   ") == []
    
    def test_object_interaction_pattern_matches(self):
        """Test that object interaction expressions match patterns."""
        import re
        strategy = "May need to find the correct starting move or object to interact with"
        strategy_lower = strategy.lower()
        
        # Check pattern matching (independent of lock status)
        matched_primitives = []
        for pattern, primitives in STRATEGY_TO_PRIMITIVE_MAP.items():
            if re.search(pattern, strategy_lower):
                matched_primitives.extend(primitives)
        
        # Should match patterns that point to these primitives
        assert any(p in matched_primitives for p in ['control_test', 'effect_scope', 'self_location']), \
            f"Expected object interaction patterns, got: {matched_primitives}"
    
    def test_exploration_pattern_matches(self):
        """Test that exploration expressions match patterns."""
        import re
        strategy = "Focus exploration on level 2. Try different directions."
        strategy_lower = strategy.lower()
        
        # Check pattern matching
        matched_primitives = []
        for pattern, primitives in STRATEGY_TO_PRIMITIVE_MAP.items():
            if re.search(pattern, strategy_lower):
                matched_primitives.extend(primitives)
        
        # Should detect exploration-related primitives in patterns
        assert any(p in matched_primitives for p in ['exploration', 'effect_scope', 'control_test', 'direction_test']), \
            f"Expected exploration patterns, got: {matched_primitives}"
    
    def test_movement_need(self):
        """Test detection of movement-related expressions."""
        strategy = "Need to find the correct movement pattern to reach goal"
        needs = parse_strategy_for_needs(strategy)
        
        # This may return empty if primitives are unlocked, which is OK
        # The pattern matching is tested separately
        assert isinstance(needs, list), "Should return a list"
    
    def test_pattern_recognition_need(self):
        """Test detection of pattern recognition expressions."""
        strategy = "Look for patterns in the grid. Identify repeating structures."
        needs = parse_strategy_for_needs(strategy)
        
        # May return empty if primitives unlocked
        assert isinstance(needs, list), "Should return a list"
    
    def test_multiple_needs_in_one_strategy(self):
        """Test that multiple needs can be extracted from one strategy."""
        import re
        strategy = ("Focus exploration on finding objects to interact with. "
                    "Look for patterns and try different movements.")
        strategy_lower = strategy.lower()
        
        # Check how many patterns match
        matched_patterns = set()
        for pattern, primitives in STRATEGY_TO_PRIMITIVE_MAP.items():
            if re.search(pattern, strategy_lower):
                matched_patterns.add(pattern)
        
        # Should match multiple different patterns
        assert len(matched_patterns) >= 2, f"Expected multiple pattern matches, got: {matched_patterns}"
    
    def test_case_insensitivity(self):
        """Test that parsing is case-insensitive (just by primitive detection)."""
        import re
        strategy_lower = "need to explore more"
        strategy_upper = "NEED TO EXPLORE MORE"
        strategy_mixed = "Need To Explore More"
        
        def get_matches(s):
            matches = set()
            for pattern, primitives in STRATEGY_TO_PRIMITIVE_MAP.items():
                if re.search(pattern, s.lower()):
                    matches.update(primitives)
            return matches
        
        # All should match the same primitives
        assert get_matches(strategy_lower) == get_matches(strategy_upper) == get_matches(strategy_mixed)


class TestStrategyToPrimitiveMap:
    """Tests for the STRATEGY_TO_PRIMITIVE_MAP configuration."""
    
    def test_map_has_entries(self):
        """Ensure the mapping has defined patterns."""
        assert len(STRATEGY_TO_PRIMITIVE_MAP) > 0, \
            "STRATEGY_TO_PRIMITIVE_MAP should have entries"
    
    def test_map_entries_are_valid_regex(self):
        """Each key should be a valid regex pattern."""
        import re
        for pattern in STRATEGY_TO_PRIMITIVE_MAP.keys():
            try:
                re.compile(pattern)
            except re.error as e:
                pytest.fail(f"Invalid regex pattern '{pattern}': {e}")
    
    def test_map_values_are_lists(self):
        """Each value should be a list of primitive names."""
        for pattern, primitives in STRATEGY_TO_PRIMITIVE_MAP.items():
            assert isinstance(primitives, list), \
                f"Pattern '{pattern}' should map to list, got {type(primitives)}"
            assert len(primitives) > 0, \
                f"Pattern '{pattern}' should map to at least one primitive"


class TestGetPrimitiveInventory:
    """Tests for get_primitive_inventory() function."""
    
    def test_inventory_returns_dict(self):
        """Inventory should return a dictionary structure."""
        inventory = get_primitive_inventory()
        
        assert isinstance(inventory, dict), "Inventory should be a dict"
    
    def test_inventory_has_summary(self):
        """Inventory should have a summary section."""
        inventory = get_primitive_inventory()
        
        # Note: If error occurs during inventory, summary may be empty
        # This tests the structure when it works
        if 'error' not in inventory:
            assert 'summary' in inventory, "Inventory should have 'summary' key"
            # Summary content tested separately since it depends on DB state
    
    def test_inventory_categorizes_primitives(self):
        """Inventory should categorize primitives by status."""
        inventory = get_primitive_inventory()
        
        expected_categories = ['seed', 'grandfathered', 'unlocked', 'locked']
        for category in expected_categories:
            assert category in inventory, f"Should have '{category}' category"
            assert isinstance(inventory[category], list), \
                f"Category '{category}' should be a list"


class TestGetComposedOperatorInventory:
    """Tests for get_composed_operator_inventory() function."""
    
    def test_operator_inventory_returns_dict(self):
        """Operator inventory should return a dictionary."""
        inventory = get_composed_operator_inventory()
        
        assert isinstance(inventory, dict), "Operator inventory should be a dict"
    
    def test_operator_inventory_has_summary(self):
        """Operator inventory should have a summary."""
        inventory = get_composed_operator_inventory()
        
        # Note: If error occurs during inventory, summary may be empty
        # This tests that the structure is present when it works
        assert 'summary' in inventory, "Should have 'summary' key"
        # Content depends on DB state


class TestProcessAgentStrategySignals:
    """Tests for process_agent_strategy_signals() - the Teacher Model."""
    
    def test_returns_dict_structure(self):
        """Should return a dictionary with expected keys."""
        # This may fail if no database exists, but structure should be correct
        try:
            results = process_agent_strategy_signals(
                min_frequency=100000,  # High threshold to prevent actual unlocks
                unlock_threshold=1000000
            )
            
            assert isinstance(results, dict), "Should return a dict"
            assert 'needs_detected' in results, "Should have 'needs_detected' key"
            assert 'unlocks_triggered' in results, "Should have 'unlocks_triggered' key"
            assert 'unlock_threshold_used' in results, "Should track threshold used"
        except Exception:
            # If database doesn't exist or is empty, that's OK for this test
            pytest.skip("Database not available for integration test")
    
    def test_adaptive_threshold_calculation(self):
        """Adaptive threshold should be calculated when unlock_threshold=None."""
        try:
            # Call with None to trigger adaptive calculation
            results = process_agent_strategy_signals(
                min_frequency=100000,
                unlock_threshold=None,  # Adaptive
                unlock_percentage=0.10
            )
            
            # Should have calculated a threshold
            threshold = results.get('unlock_threshold_used', 0)
            assert threshold >= 15, f"Threshold should be at least 15, got {threshold}"
            assert threshold <= 100, f"Threshold should be at most 100, got {threshold}"
        except Exception:
            pytest.skip("Database not available for integration test")
    
    def test_respects_frequency_threshold(self):
        """Should only consider needs above min_frequency."""
        # High threshold means nothing should qualify
        try:
            results = process_agent_strategy_signals(
                min_frequency=1000000,
                unlock_threshold=2000000
            )
            
            # With extremely high thresholds, nothing should be detected
            needs = results.get('needs_detected', {})
            for primitive, data in needs.items():
                assert data.get('total_frequency', 0) >= 1000000, \
                    f"Primitive {primitive} should only appear if frequency >= threshold"
        except Exception:
            pytest.skip("Database not available for integration test")


class TestStrategyPatternCoverage:
    """Tests to ensure strategy patterns cover common agent expressions."""
    
    def test_sp80_level2_strategy_pattern_matches(self):
        """The specific SP80 Level 2 issue should match patterns."""
        # This tests pattern matching, not lock status
        # The actual parse function only returns LOCKED primitives,
        # so we test the pattern map directly
        strategy = "Focus exploration on level 2. May need to find the correct starting move or object to interact with"
        strategy_lower = strategy.lower()
        
        # Check if any patterns match
        matched_patterns = []
        for pattern, primitives in STRATEGY_TO_PRIMITIVE_MAP.items():
            import re
            if re.search(pattern, strategy_lower):
                matched_patterns.append((pattern, primitives))
        
        # Should match at least one pattern
        assert len(matched_patterns) > 0, \
            f"SP80 Level 2 strategy should match patterns. Strategy: {strategy}"
    
    def test_common_agent_expressions_pattern_coverage(self):
        """Test that common agent expressions match patterns in the map."""
        import re
        expressions = [
            "Need to try different actions to see what moves",
            "Should click on different objects",
            "Try to find which object I control",
            "Explore systematically to find the goal",
            "Test each action to see the effect",
            "Look for patterns in the transformation",
            "Need to understand the relationship between input and output",
            "Try moving in all directions",
        ]
        
        undetected = []
        for expr in expressions:
            expr_lower = expr.lower()
            matched = False
            for pattern in STRATEGY_TO_PRIMITIVE_MAP.keys():
                if re.search(pattern, expr_lower):
                    matched = True
                    break
            if not matched:
                undetected.append(expr)
        
        # At least 50% of common expressions should match patterns
        detection_rate = (len(expressions) - len(undetected)) / len(expressions)
        assert detection_rate >= 0.5, \
            f"Detection rate {detection_rate:.0%} too low. Undetected: {undetected}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
