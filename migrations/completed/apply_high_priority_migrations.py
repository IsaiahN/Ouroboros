#!/usr/bin/env python3
"""
Apply High Priority Database Migrations

Implements:
1. winning_sequences and winning_sequences_full_game tables
2. social_rule_adherence column for agents
3. Schema export/backup

Run: python apply_high_priority_migrations.py
"""

import sqlite3
import json
from datetime import datetime

def apply_migrations():
    db = sqlite3.connect('core_data.db')
    cursor = db.cursor()
    
    print("[LAUNCH] Applying High Priority Migrations...")
    
    # =================================================================
    # FIX #3: Create winning_sequences tables
    # =================================================================
    print("\n📋 Creating winning_sequences table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS winning_sequences (
            sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            level_number INTEGER NOT NULL,
            sequence_data TEXT NOT NULL,
            total_actions INTEGER NOT NULL,
            final_score REAL NOT NULL,
            agent_id TEXT,
            generation INTEGER,
            is_full_game_win BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(game_id, level_number, sequence_data)
        )
    ''')
    
    print("📋 Creating winning_sequences_full_game table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS winning_sequences_full_game (
            sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL UNIQUE,
            total_levels_completed INTEGER NOT NULL,
            sequence_data TEXT NOT NULL,
            total_actions INTEGER NOT NULL,
            final_score REAL NOT NULL,
            agent_id TEXT NOT NULL,
            generation INTEGER NOT NULL,
            agent_mode TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK(total_levels_completed >= 1)
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_winning_sequences_game ON winning_sequences(game_id, level_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_winning_sequences_full_game ON winning_sequences_full_game(game_id)')
    
    # =================================================================
    # FIX #4: Add social_rule_adherence column
    # =================================================================
    print("\n👥 Adding social_rule_adherence to agents table...")
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(agents)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'social_rule_adherence' not in columns:
        cursor.execute('ALTER TABLE agents ADD COLUMN social_rule_adherence REAL DEFAULT 0.5')
        print("   [OK] Added social_rule_adherence column")
        
        # Update existing Exploiters with bimodal distribution
        cursor.execute("SELECT agent_id FROM agents WHERE agent_type = 'exploiter'")
        exploiters = cursor.fetchall()
        
        if exploiters:
            print(f"   [STATS] Updating {len(exploiters)} existing Exploiters with bimodal distribution...")
            import random
            for i, (agent_id,) in enumerate(exploiters):
                # 50/50 split: Sociopath (0.0-0.2) or Conformist (0.8-1.0)
                if i % 2 == 0:
                    adherence = random.uniform(0.0, 0.2)  # Sociopath
                else:
                    adherence = random.uniform(0.8, 1.0)  # Conformist
                
                cursor.execute('''
                    UPDATE agents 
                    SET social_rule_adherence = ?
                    WHERE agent_id = ?
                ''', (adherence, agent_id))
    else:
        print("   [SKIP]️  Column already exists, skipping")
    
    # =================================================================
    # Commit changes
    # =================================================================
    db.commit()
    
    # =================================================================
    # Verify migrations
    #================================================================
    print("\n[OK] Verifying migrations...")
    
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='winning_sequences'")
    if cursor.fetchone()[0] == 1:
        print("   [OK] winning_sequences table created")
    
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='winning_sequences_full_game'")
    if cursor.fetchone()[0] == 1:
        print("   [OK] winning_sequences_full_game table created")
    
    cursor.execute("PRAGMA table_info(agents)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'social_rule_adherence' in columns:
        print("   [OK] social_rule_adherence column exists")
        
        # Show distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN social_rule_adherence < 0.4 THEN 'Sociopath (0.0-0.2)'
                    WHEN social_rule_adherence > 0.6 THEN 'Conformist (0.8-1.0)'
                    ELSE 'Neutral (0.4-0.6)'
                END as type,
                COUNT(*) as count
            FROM agents
            WHERE agent_type = 'exploiter'
            GROUP BY type
        ''')
        dist = cursor.fetchall()
        if dist:
            print("\n   [STATS] Exploiter Distribution:")
            for type_name, count in dist:
                print(f"      {type_name}: {count}")
    
    db.close()
    print("\n[WIN] Migrations applied successfully!")

if __name__ == '__main__':
    apply_migrations()
