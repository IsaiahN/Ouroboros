#!/usr/bin/env python3
"""
Script to apply Fix #2: Generalist Sensation Restoration
Bypasses file editing tool limitations by using direct file I/O
"""

import sys

def apply_generalist_sensation_fix():
    """Apply the one-line fix to restore Generalist sensation."""
    
    filepath = 'core_gameplay.py'
    
    print(f"Reading {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Total lines: {len(lines)}")
    
    # Line 1148 (0-indexed as 1147)
    target_line_idx = 1147
    
    print(f"\nLine {target_line_idx + 1} BEFORE:")
    print(f"  {lines[target_line_idx].rstrip()}")
    
    # Check for the target content (handle both line endings)
    actual_stripped = lines[target_line_idx].rstrip()
    expected_stripped = "        sensation_allowed = (agent_mode != 'generalist')"
    
    if actual_stripped != expected_stripped:
        print(f"\nERROR: Line {target_line_idx + 1} doesn't match expected content!")
        print(f"Expected: {expected_stripped}")
        print(f"Actual:   {actual_stripped}")
        return False
    
    # Get the original line ending
    line_ending = '\r\n' if '\r\n' in lines[target_line_idx] else '\n'
    
    # Apply fix - keep the same line ending
    lines[target_line_idx] = f"        sensation_allowed = (agent_mode != 'pioneer'){line_ending}"
    
    #  Also update the comment block (lines 1145-1147, 0-indexed as 1144-1146)
    lines[1144] = f"        # SENSATION ACCESS BY ROLE (Phase 4.5):{line_ending}"
    lines[1145] = f"        # - Pioneers: NO (pure exploration, no emotional biases){line_ending}"
    lines[1146] = f"        # - Generalists: YES (feelings restored - need emotional intelligence){line_ending}"
    
    print(f"\nLine {target_line_idx + 1} AFTER:")
    print(f"  {lines[target_line_idx].rstrip()}")
    
    print(f"\nWriting changes to {filepath}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Fix #2 applied successfully!")
    print("\nVerifying...")
    with open(filepath, 'r', encoding='utf-8') as f:
        verify_lines = f.readlines()
    print(f"Line 1148: {verify_lines[1147].rstrip()}")
    
    return True

if __name__ == '__main__':
    success = apply_generalist_sensation_fix()
    sys.exit(0 if success else 1)
