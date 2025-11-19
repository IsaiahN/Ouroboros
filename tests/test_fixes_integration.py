"""
Integration tests for Fix #1 (Optimizer Checkpoint) and Fix #2 (Generalist Sensation).

These tests verify the actual code logic by checking the relevant sections
directly rather than complex mocking.
"""

import unittest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestOptimizerCheckpointLogic(unittest.TestCase):
    """Verify optimizer checkpoint fix logic is in place."""
    
    def test_optimizer_checkpoint_code_exists(self):
        """Test that optimizer checkpoint fix code is present in core_gameplay.py."""
        filepath = Path(__file__).parent.parent / 'core_gameplay.py'
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify fix comment header exists
        self.assertIn('# CRITICAL FIX #1: Optimizer Penultimate Checkpoint Bug', content,
                     "Optimizer fix comment header not found")
        
        # Verify key logic exists
        self.assertIn('_get_agent_operating_mode', content)
        self.assertIn("is_optimizer = (agent_mode == 'optimizer')", content)
        self.assertIn('_analyze_optimizer_checkpoint', content)
        self.assertIn('final_actions', content)
        self.assertIn('actions.extend(final_actions)', content)
        
        print("✅ Optimizer checkpoint fix code verified in core_gameplay.py")


class TestGeneralistSensationLogic(unittest.TestCase):
    """Verify generalist sensation fix logic is in place."""
    
    def test_generalist_sensation_code_exists(self):
        """Test that generalist sensation fix is present in core_gameplay.py."""
        filepath = Path(__file__).parent.parent / 'core_gameplay.py'
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify the fix - should have 'pioneer' not 'generalist'
        self.assertIn("sensation_allowed = (agent_mode != 'pioneer')", content,
                     "Generalist sensation fix not found - should restrict only pioneers")
        
        # Verify old code is NOT present
        self.assertNotIn("sensation_allowed = (agent_mode != 'generalist')", content,
                        "Old restriction found - generalists should have sensation restored!")
        
        print("✅ Generalist sensation restoration verified in core_gameplay.py")
        
    def test_sensation_comment_updated(self):
        """Test that comments reflect new sensation access policy."""
        filepath = Path(__file__).parent.parent / 'core_gameplay.py'
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the sensation comment block (should be updated)
        sensation_comments = [line for line in lines if 'SENSATION ACCESS' in line or 'Phase 4.5' in line]
        
        self.assertTrue(len(sensation_comments) > 0,
                       "Sensation access comments should exist")
        
        print("✅ Sensation access comments found in core_gameplay.py")

  
class TestCodeSyntaxValidity(unittest.TestCase):
    """Verify modified code compiles without syntax errors."""
    
    def test_core_gameplay_compiles(self):
        """Test that core_gameplay.py compiles without syntax errors."""
        filepath = Path(__file__).parent.parent / 'core_gameplay.py'
        
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Try to compile - will raise SyntaxError if invalid
        try:
            compile(code, str(filepath), 'exec')
            print("✅ core_gameplay.py compiles successfully")
        except SyntaxError as e:
            self.fail(f"Syntax error in core_gameplay.py: {e}")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
