#!/usr/bin/env python3
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Migration: Add Frame Embeddings Tables
======================================

Adds tables for storing learned representations from Self-Supervised Dynamics.

Tables Added:
- frame_embeddings: Stores 128-dim embeddings for action traces
- representation_model_history: Tracks model training runs

See architecture/Self_Supervised_Dynamics_Implementation.md for full design.
"""

import sqlite3
from pathlib import Path


def run_migration(db_path: str = "core_data.db"):
    """
    Add frame_embeddings and representation_model_history tables.

    Safe to run multiple times (uses IF NOT EXISTS).
    """
    print(f"[MIGRATION] Adding frame embeddings tables to {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Table 1: Frame Embeddings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS frame_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id INTEGER NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,

                -- The learned representation (128 floats = 512 bytes)
                embedding BLOB NOT NULL,

                -- Context for weighted similarity
                action_taken INTEGER,
                score_delta REAL DEFAULT 0.0,
                frame_changed BOOLEAN DEFAULT FALSE,

                -- Metadata
                model_version TEXT DEFAULT 'v1',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (trace_id) REFERENCES action_traces(id),
                UNIQUE(trace_id)
            )
        """)
        print("  [OK] Created frame_embeddings table")

        # Index for game context queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_frame_embeddings_game_level
            ON frame_embeddings(game_type, level_number)
        """)
        print("  [OK] Created idx_frame_embeddings_game_level index")

        # Index for trace lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_frame_embeddings_trace
            ON frame_embeddings(trace_id)
        """)
        print("  [OK] Created idx_frame_embeddings_trace index")

        # Table 2: Model Training History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS representation_model_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version TEXT NOT NULL,
                training_samples INTEGER NOT NULL,
                final_loss REAL,
                training_duration_seconds REAL,
                trained_at TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)
        print("  [OK] Created representation_model_history table")

        conn.commit()
        print("[MIGRATION] Frame embeddings tables added successfully")

    except Exception as e:
        conn.rollback()
        print(f"[MIGRATION] Failed: {e}")
        raise
    finally:
        conn.close()


def check_tables_exist(db_path: str = "core_data.db") -> bool:
    """Check if migration has already been applied."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('frame_embeddings', 'representation_model_history')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        return 'frame_embeddings' in tables and 'representation_model_history' in tables
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "core_data.db"

    if check_tables_exist(db_path):
        print(f"[MIGRATION] Tables already exist in {db_path}")
    else:
        run_migration(db_path)
