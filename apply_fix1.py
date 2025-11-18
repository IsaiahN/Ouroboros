#!/usr/bin/env python3
"""
Script to apply Fix #1: Optimizer Penultimate Checkpoint Bug
Inserts logic to auto-append final_actions to partial optimizer sequences
"""

import sys

def apply_optimizer_checkpoint_fix():
    """Apply Fix #1 - insert optimizer checkpoint completion logic."""
    
    filepath = 'core_gameplay.py'
    
    print(f"Reading {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Total lines: {len(lines)}")
    
    # Get line ending style
    line_ending = '\r\n' if '\r\n' in lines[0] else '\n'
    
    # Find insertion point: after line 1993 (0-indexed 1992)
    insertion_idx = 1993  # Insert AFTER line 1993, so at index 1993
    
    print(f"\nLine 1993: {lines[1992].rstrip()}")
    print(f"Line 1994: {lines[1993].rstrip()}")
    
    # Verify we're at the right spot
    if "generation = agent_data[0]['generation']" not in lines[1992]:
        print("\nERROR: Insertion point not found!")
        return False
    
    # Code to insert - using raw strings to avoid f-string issues
    fix_code_lines = [
        "                ",
        "                # ================================================================",
        "                # CRITICAL FIX #1: Optimizer Penultimate Checkpoint Bug",
        "                # ================================================================",
        "                # PROBLEM: Optimizers save partial sequences without final actions",
        "                # that guarantee level completion. This causes agents to get stuck.",
        "                #",
        "                # SOLUTION: If current agent is an Optimizer and we have checkpoint ",
        "                # data for this level, automatically append the final_actions before",
        "                # saving. This ensures all optimizer sequences are complete.",
        "                # ================================================================",
        "               ",
        "                # Check if current agent is operating in Optimizer mode",
        "                agent_mode = self._get_agent_operating_mode(agent_id)",
        "                is_optimizer = (agent_mode == 'optimizer')",
        "                ",
        "                if is_optimizer:",
        "                    # Try to get optimizer checkpoint data for this level",
        "                    checkpoint_data = self._analyze_optimizer_checkpoint(game_id, level_number)",
        "                    ",
        "                    if checkpoint_data and checkpoint_data.get('final_actions'):",
        "                        final_actions = checkpoint_data['final_actions']",
        "                        current_action_count = len(actions)",
        "                        target_actions = checkpoint_data.get('target_actions', len(actions))",
        "                        ",
        "                        # Check if current sequence is shorter than optimal (partial)",
        "                        if current_action_count < target_actions:",
        "                            # Append the guaranteed win ending",
        "                            logger.info(f\"🔧 OPTIMIZER FIX: Partial sequence detected ({current_action_count} actions, target: {target_actions})\")",
        "                            logger.info(f\"   Appending {len(final_actions)} final actions to guarantee completion\")",
        "                            ",
        "                            original_length = len(actions)",
        "                            actions.extend(final_actions)",
        "                            ",
        "                            # Update efficiency with new action count",
        "                            efficiency = final_score / len(actions) if len(actions) > 0 else 0.0",
        "                            ",
        "                            logger.info(f\"✅ Sequence completed: {original_length} → {len(actions)} actions (efficiency: {efficiency:.4f})\")",
        "                        else:",
        "                            logger.debug(f\"Optimizer sequence already complete ({current_action_count} actions)\")",
        "                    else:",
        "                        logger.debug(f\"No checkpoint data for {game_id} level {level_number} - saving as-is\")",
    ]
    
    # Insert each line
    for i, code_line in enumerate(fix_code_lines):
        lines.insert(insertion_idx + i, code_line + line_ending)
    
    print(f"\nInserting {len(fix_code_lines)} lines after line 1993...")
    
    print(f"\nWriting changes to {filepath}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Fix #1 applied successfully!")
    print(f"\nNew total lines: {len(lines)}")
    
    # Verify
    print("\nVerifying insertion...")
    with open(filepath, 'r', encoding='utf-8') as f:
        verify_lines = f.readlines()
    
    print(f"Line 1995 (should be blank): {repr(verify_lines[1994])}")
    print(f"Line 1997 (should have CRITICAL FIX): {verify_lines[1996].strip()}")
    print(f"Line 2010 (should have Check if current agent): {verify_lines[2009].strip()}")
    
    return True

if __name__ == '__main__':
    success = apply_optimizer_checkpoint_fix()
    sys.exit(0 if success else 1)
