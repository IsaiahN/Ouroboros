"""Test position_death_patterns lookup functionality.

NOTE: This script was updated in Jan 2026.
Original purpose was to test frame hash matching with terminal_patterns.
Now tests position_death_patterns bucket-based death tracking.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_interface import DatabaseInterface
from engines.perception.terminal_pattern_detector import TerminalPatternDetector

db = DatabaseInterface()
detector = TerminalPatternDetector(db)

# Test position-bucket computation
def test_position_bucket(x, y, bucket_size=8):
    bucket_x = x // bucket_size
    bucket_y = y // bucket_size
    return (bucket_x, bucket_y)

# Test cases
test_positions = [
    (0, 0),    # Origin
    (5, 5),    # Same bucket as origin
    (8, 8),    # Next bucket diagonally
    (23, 15),  # Arbitrary position
    (63, 63),  # Edge of typical 64x64 grid
]

print("=== Position Bucket Computation Test ===")
for x, y in test_positions:
    bx, by = test_position_bucket(x, y)
    print(f"  Position ({x}, {y}) -> Bucket ({bx}, {by}) -> Bucket center ({bx*8}, {by*8})")

# Check actual death patterns in DB
print()
print("=== High-frequency death patterns for as66 Level 5 ===")
r = db.execute_query("""
    SELECT bucket_x, bucket_y, bucket_size, fatal_action, death_count, danger_score
    FROM position_death_patterns
    WHERE game_type = 'as66' AND level_number = 5 AND death_count >= 3
    ORDER BY death_count DESC
    LIMIT 10
""")
if r:
    for x in r:
        bx = x.get('bucket_x', 0)
        by = x.get('bucket_y', 0)
        bs = x.get('bucket_size', 8)
        print(f"  Would avoid ACTION{x['fatal_action']} at bucket ({bx*bs},{by*bs}) ({x['death_count']} deaths, danger={x['danger_score']:.2f})")
else:
    print("  No high-frequency patterns found!")

# Test the check_position_danger method
print()
print("=== Testing check_position_danger method ===")
test_result = detector.check_position_danger(
    game_type='as66',
    level_number=5,
    position=(0, 0),  # Start position
    planned_action=1,
    min_danger=0.5
)
if test_result:
    print(f"  DANGER detected at (0,0): {test_result.get('reason', 'Unknown')}")
    print(f"  Suggested alternative: ACTION{test_result.get('suggested_alternative', '?')}")
else:
    print("  No danger detected at (0,0) for ACTION1")
