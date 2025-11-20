"""
Sequence Validation Subroutine (Task #7)

This script validates winning sequences by replaying them and updating their reputation scores.
It runs as a background task to ensure sequence quality and community memory accuracy.
"""

import sqlite3
import asyncio
import json
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_gameplay import GameplayEngine
from database_interface import DatabaseInterface

DB_PATH = "core_data.db"


async def validate_sequence(sequence_id: str, game_id: str, db: DatabaseInterface):
    """
    Validate a single sequence by replaying it.

    Args:
        sequence_id: Sequence to validate
        game_id: Game to play
        db: Database interface

    Returns:
        bool: True if validation successful, False otherwise
    """
    try:
        # Get sequence details
        sequence = db.execute_query(
            """
            SELECT *
            FROM winning_sequences
            WHERE sequence_id = ?
        """,
            (sequence_id,),
        )[0]

        # Create gameplay engine with validation config
        config = {
            "enable_pattern_learning": False,  # Don't capture new sequences during validation
            "agent_id": f"validator_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generation": 0,
        }

        engine = GameplayEngine(config, db)

        # Try to replay the sequence
        result = await engine._try_replay_sequence(game_id, sequence)

        if result and result.get("win"):
            print(f"✅ Sequence {sequence_id} validated successfully")
            return True
        else:
            print(f"❌ Sequence {sequence_id} failed validation")
            return False

    except Exception as e:
        print(f"Error validating sequence {sequence_id}: {e}")
        return False


async def run_validation_batch(max_validations: int = 10):
    """
    Run a batch of sequence validations.

    Args:
        max_validations: Maximum number of sequences to validate
    """
    db = DatabaseInterface(DB_PATH)

    try:
        # Get sequences from validation queue (highest priority first)
        queue_items = db.execute_query(
            """
            SELECT queue_id, sequence_id, game_id, priority
            FROM sequence_validation_queue
            WHERE status = 'pending'
            ORDER BY priority DESC, added_at ASC
            LIMIT ?
        """,
            (max_validations,),
        )

        if not queue_items:
            print("No sequences in validation queue")

            # Auto-populate queue with untested sequences
            untested = db.execute_query(
                """
                SELECT ws.sequence_id, ws.game_id
                FROM winning_sequences ws
                LEFT JOIN sequence_reputation sr ON ws.sequence_id = sr.sequence_id
                WHERE ws.is_active = 1
                AND (sr.total_validation_attempts IS NULL OR sr.total_validation_attempts = 0)
                LIMIT ?
            """,
                (max_validations,),
            )

            if untested:
                print(f"Adding {len(untested)} untested sequences to validation queue")
                for seq in untested:
                    db.execute_query(
                        """
                        INSERT OR IGNORE INTO sequence_validation_queue 
                        (sequence_id, game_id, priority, status)
                        VALUES (?, ?, 5, 'pending')
                    """,
                        (seq["sequence_id"], seq["game_id"]),
                    )
                db.checkpoint_wal()

                # Re-query
                queue_items = db.execute_query(
                    """
                    SELECT queue_id, sequence_id, game_id, priority
                    FROM sequence_validation_queue
                    WHERE status = 'pending'
                    ORDER BY priority DESC, added_at ASC
                    LIMIT ?
                """,
                    (max_validations,),
                )

        print(f"Validating {len(queue_items)} sequences...")

        for item in queue_items:
            queue_id = item["queue_id"]
            sequence_id = item["sequence_id"]
            game_id = item["game_id"]

            # Mark as in progress
            db.execute_query(
                """
                UPDATE sequence_validation_queue
                SET status = 'in_progress'
                WHERE queue_id = ?
            """,
                (queue_id,),
            )
            db.checkpoint_wal()

            # Validate
            success = await validate_sequence(sequence_id, game_id, db)

            # Update queue status
            new_status = "completed" if success else "failed"
            db.execute_query(
                """
                UPDATE sequence_validation_queue
                SET status = ?,
                    last_validated_at = CURRENT_TIMESTAMP,
                    validation_count = validation_count + 1
                WHERE queue_id = ?
            """,
                (new_status, queue_id),
            )

            # Record validation attempt (this will trigger reputation update)
            # Note: This would normally be done by _record_sequence_validation in core_gameplay
            # For now, we'll update reputation directly
            db.execute_query(
                """
                INSERT OR REPLACE INTO sequence_reputation (
                    sequence_id, total_validation_attempts, successful_validations,
                    failed_validations, last_updated
                )
                SELECT 
                    ?,
                    COALESCE(total_validation_attempts, 0) + 1,
                    COALESCE(successful_validations, 0) + ?,
                    COALESCE(failed_validations, 0) + ?,
                    CURRENT_TIMESTAMP
                FROM (SELECT * FROM sequence_reputation WHERE sequence_id = ? LIMIT 1)
                UNION ALL
                SELECT ?, 1, ?, ?, CURRENT_TIMESTAMP
                WHERE NOT EXISTS (SELECT 1 FROM sequence_reputation WHERE sequence_id = ?)
                LIMIT 1
            """,
                (
                    sequence_id,
                    1 if success else 0,
                    0 if success else 1,
                    sequence_id,
                    sequence_id,
                    1 if success else 0,
                    0 if success else 1,
                    sequence_id,
                ),
            )

            db.checkpoint_wal()

        print(f"✅ Validation batch complete")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate winning sequences")
    parser.add_argument(
        "--max", type=int, default=10, help="Maximum sequences to validate"
    )
    args = parser.parse_args()

    asyncio.run(run_validation_batch(args.max))
