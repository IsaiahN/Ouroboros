#!/usr/bin/env python3
"""
Migration: Add Frontier Level Topology System
Date: January 28, 2026

Adds tables for:
1. frontier_level_topology - Frame transition graph ("stitching")
2. frontier_landmarks - Stable landmark signatures for anchoring
3. frontier_exploration_confidence - Map confidence scoring

Based on bat navigation research: head direction cells anchor to landmarks,
not magnetic fields. The brain "stitches" partial views into a global map.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core_data.db')


def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("[MIGRATE] Adding frontier topology tables...")

    # =========================================================================
    # TABLE 1: frontier_level_topology
    # Tracks frame-to-frame transitions (the "stitching" from bat research)
    # =========================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frontier_level_topology (
            -- Composite key: unique transition
            game_type TEXT NOT NULL,
            level_number INTEGER NOT NULL,
            from_frame_hash TEXT NOT NULL,
            action_taken INTEGER NOT NULL,

            -- Result of this transition
            to_frame_hash TEXT NOT NULL,

            -- Statistics
            times_observed INTEGER DEFAULT 1,
            times_resulted_in_death INTEGER DEFAULT 0,
            times_resulted_in_score INTEGER DEFAULT 0,
            avg_score_delta REAL DEFAULT 0.0,

            -- Metadata
            first_observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (game_type, level_number, from_frame_hash, action_taken)
        )
    """)
    print("  [OK] Created frontier_level_topology table")

    # Index for querying "what actions are available from this frame?"
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_frontier_topology_from_frame
        ON frontier_level_topology(game_type, level_number, from_frame_hash)
    """)

    # Index for querying "how do I reach this frame?"
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_frontier_topology_to_frame
        ON frontier_level_topology(game_type, level_number, to_frame_hash)
    """)
    print("  [OK] Created topology indices")

    # =========================================================================
    # TABLE 2: frontier_landmarks
    # Stable reference points for anchoring position estimates
    # =========================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frontier_landmarks (
            -- Composite key
            game_type TEXT NOT NULL,
            level_number INTEGER NOT NULL,
            landmark_hash TEXT NOT NULL,

            -- Landmark characteristics
            landmark_type TEXT NOT NULL,  -- 'wall', 'goal', 'boundary', 'pattern'
            position_x INTEGER,
            position_y INTEGER,
            color_signature TEXT,         -- JSON: dominant colors
            shape_signature TEXT,         -- JSON: bounding box, area

            -- Stability metrics
            times_observed INTEGER DEFAULT 1,
            frames_present_in INTEGER DEFAULT 1,
            stability_score REAL DEFAULT 1.0,  -- 1.0 = always present, 0.0 = never

            -- Metadata
            first_observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (game_type, level_number, landmark_hash)
        )
    """)
    print("  [OK] Created frontier_landmarks table")

    # =========================================================================
    # TABLE 3: frontier_exploration_confidence
    # Tracks how well we understand each level's map
    # =========================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frontier_exploration_confidence (
            -- Key: one row per frontier level
            game_type TEXT NOT NULL,
            level_number INTEGER NOT NULL,

            -- Exploration metrics
            unique_frames_visited INTEGER DEFAULT 0,
            transitions_learned INTEGER DEFAULT 0,
            dead_ends_found INTEGER DEFAULT 0,
            safe_paths_found INTEGER DEFAULT 0,

            -- Confidence calculation
            -- coverage = transitions_learned / (frames * 7 actions possible)
            coverage_estimate REAL DEFAULT 0.0,
            confidence_score REAL DEFAULT 0.0,  -- 0.0 = unknown, 1.0 = fully mapped

            -- Strategy recommendation
            exploration_mode TEXT DEFAULT 'random',  -- 'random', 'systematic', 'exploit'

            -- Metadata
            last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_attempts INTEGER DEFAULT 0,

            PRIMARY KEY (game_type, level_number)
        )
    """)
    print("  [OK] Created frontier_exploration_confidence table")

    # Index for confidence queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_frontier_confidence_score
        ON frontier_exploration_confidence(game_type, level_number, confidence_score)
    """)
    print("  [OK] Created confidence index")

    conn.commit()
    conn.close()

    print("[MIGRATE] SUCCESS: Frontier topology tables created")


if __name__ == "__main__":
    run_migration()
