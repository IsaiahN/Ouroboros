#!/usr/bin/env python3
"""Add scorecard_id tracking to database."""

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("Adding scorecard_id tracking to database...")
print("=" * 70)

# Add scorecard_id to game_results
try:
    db.execute_query("ALTER TABLE game_results ADD COLUMN scorecard_id TEXT")
    print("✅ Added scorecard_id to game_results")
except Exception as e:
    if "duplicate column" in str(e).lower():
        print("⚠️  scorecard_id already exists in game_results")
    else:
        print(f"❌ Error adding scorecard_id to game_results: {e}")

# Add scorecard_id to winning_sequences
try:
    db.execute_query("ALTER TABLE winning_sequences ADD COLUMN scorecard_id TEXT")
    print("✅ Added scorecard_id to winning_sequences")
except Exception as e:
    if "duplicate column" in str(e).lower():
        print("⚠️  scorecard_id already exists in winning_sequences")
    else:
        print(f"❌ Error adding scorecard_id to winning_sequences: {e}")

# Create indexes
try:
    db.execute_query("CREATE INDEX IF NOT EXISTS idx_game_results_scorecard ON game_results(scorecard_id)")
    print("✅ Created index idx_game_results_scorecard")
except Exception as e:
    print(f"❌ Error creating game_results index: {e}")

try:
    db.execute_query("CREATE INDEX IF NOT EXISTS idx_winning_sequences_scorecard ON winning_sequences(scorecard_id)")
    print("✅ Created index idx_winning_sequences_scorecard")
except Exception as e:
    print(f"❌ Error creating winning_sequences index: {e}")

print("=" * 70)
print("✅ Scorecard tracking schema updated!")
