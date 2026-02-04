#!/usr/bin/env python3
"""Test decision system with vc33 context to debug ACTION6 coordinates."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from decision_rung_system import DecisionRungSystem


def main():
    # Create decision system
    ds = DecisionRungSystem()

    # Simulate vc33 context (ACTION6-only game)
    context = {
        'game_type': 'vc33',
        'level': 1,
        'available_actions': [6],
        'agent_id': 'test_agent',
        'action_count': 1,
        'frame': [[0]*64 for _ in range(64)],  # Simple frame
    }
    game_state = context['frame']

    print("Testing decision system with vc33 context (ACTION6-only)...")
    print(f"Available actions: {context['available_actions']}")
    print()

    # Test decision
    action, reason = ds.decide(game_state, context)
    print(f"Decision: {action}")
    print(f"Reason: {reason}")
    print(f"Metadata: {ds.last_decision_metadata}")
    print()

    # Check if coordinates are present
    metadata = ds.last_decision_metadata
    if metadata:
        if 'x' in metadata and 'y' in metadata:
            print(f"[OK] Coordinates found: ({metadata['x']}, {metadata['y']})")
        elif 'grid_target' in metadata:
            gt = metadata['grid_target']
            print(f"[OK] Grid target found: ({gt.get('x')}, {gt.get('y')})")
        elif 'pixel_position' in metadata:
            px, py = metadata['pixel_position']
            print(f"[OK] Pixel position found: ({px}, {py})")
        elif 'target' in metadata:
            t = metadata['target']
            print(f"[OK] Target found: ({t.get('x')}, {t.get('y')})")
        else:
            print("[FAIL] No coordinates in metadata!")
            print(f"  Available keys: {list(metadata.keys())}")
    else:
        print("[FAIL] No metadata returned!")

    # Test a few more actions to see pattern
    print("\n--- Testing 5 consecutive decisions ---")
    for i in range(5):
        context['action_count'] = i + 1
        action, reason = ds.decide(game_state, context)
        metadata = ds.last_decision_metadata
        coords = "NONE"
        if metadata:
            if 'x' in metadata and 'y' in metadata:
                coords = f"({metadata['x']}, {metadata['y']})"
            elif 'grid_target' in metadata:
                gt = metadata['grid_target']
                coords = f"grid:({gt.get('x')}, {gt.get('y')})"
        print(f"  [{i+1}] {action} | coords={coords} | {reason[:60]}...")


if __name__ == '__main__':
    main()
