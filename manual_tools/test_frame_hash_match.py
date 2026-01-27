"""Test that frame hash computation matches between core_gameplay and terminal_pattern_detector."""
import os
import sys
import hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from terminal_pattern_detector import TerminalPatternDetector
from database_interface import DatabaseInterface

db = DatabaseInterface()
detector = TerminalPatternDetector(db)

# Create a sample frame (just for testing hash algorithm)
sample_frame = [
    [0, 1, 2, 3],
    [4, 5, 6, 7],
    [8, 9, 10, 11]
]

# Method from terminal_pattern_detector
def detector_hash(frame):
    flat = [str(cell) for row in frame for cell in row]
    return hashlib.md5(''.join(flat).encode()).hexdigest()[:16]

# Method from new core_gameplay code
def gameplay_hash(frame):
    flat = [str(cell) for row in frame for cell in row]
    return hashlib.md5(''.join(flat).encode()).hexdigest()[:16]

# Compare
detector_result = detector.compute_frame_hash(sample_frame)
gameplay_result = gameplay_hash(sample_frame)

print(f"Detector hash: {detector_result}")
print(f"Gameplay hash: {gameplay_result}")
print(f"Match: {detector_result == gameplay_result}")

# Now test with a real level 5 frame hash from database
print()
print("=== Checking if L5 frame hashes in DB would be matched ===")
r = db.execute_query("""
    SELECT DISTINCT frame_hash, fatal_action, occurrence_count
    FROM terminal_patterns 
    WHERE game_type = 'as66' AND level_number = 5 AND occurrence_count >= 3
    ORDER BY occurrence_count DESC
    LIMIT 5
""")
if r:
    for x in r:
        print(f"  Would avoid ACTION{x['fatal_action']} when frame_hash={x['frame_hash']} ({x['occurrence_count']} deaths)")
else:
    print("  No high-frequency patterns found!")
