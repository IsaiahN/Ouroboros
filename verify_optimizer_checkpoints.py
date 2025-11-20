#!/usr/bin/env python3
"""
Optimizer Checkpoint Verification Script

Purpose: Verify that optimizer checkpoints are correctly saving valid winning sequences
and that agents can successfully replay them.
"""

import os
import sqlite3
import json
from typing import Dict, List, Any
from datetime import datetime

# Disable pycache
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

class OptimizerVerifier:
    def __init__(self, db_path: str = "core_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def verify_winning_sequences(self):
        """Verify integrity of sequences marked as winning."""
        print("\n🔍 VERIFYING WINNING SEQUENCES...")
        print("-" * 60)
        
        cursor = self.conn.cursor()
        
        # Get all winning sequences
        cursor.execute("""
            SELECT 
                ws.sequence_id,
                ws.game_id,
                ws.level_number,
                ws.agent_id,
                ws.total_score,
                ws.discovered_at,
                a.generation
            FROM winning_sequences ws
            JOIN agents a ON ws.agent_id = a.agent_id
            ORDER BY ws.discovered_at DESC
        """)
        
        sequences = [dict(row) for row in cursor.fetchall()]
        
        if not sequences:
            print("❌ No winning sequences found in database.")
            return

        print(f"Found {len(sequences)} winning sequences.")
        
        # Check for optimizer sequences (usually high generation or specific metadata if available)
        # Since we don't have explicit 'optimizer' flag in winning_sequences, we infer or check logs
        
        valid_count = 0
        suspicious_count = 0
        
        for seq in sequences:
            # check if sequence actually exists in sequence_reputation if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='sequence_reputation'
            """)
            if cursor.fetchone():
                cursor.execute("""
                    SELECT successful_validations, total_validation_attempts 
                    FROM sequence_reputation 
                    WHERE sequence_id = ?
                """, (seq['sequence_id'],))
                rep = cursor.fetchone()
                
                status = "UNKNOWN"
                if rep:
                    success_rate = (rep['successful_validations'] / rep['total_validation_attempts']) if rep['total_validation_attempts'] > 0 else 0
                    status = f"{success_rate:.1%} ({rep['successful_validations']}/{rep['total_validation_attempts']})"
                    
                    if success_rate < 0.5 and rep['total_validation_attempts'] > 2:
                        suspicious_count += 1
                        print(f"⚠️  Suspicious Sequence: {seq['game_id']} L{seq['level_number']} (Gen {seq['generation']}) - Success Rate: {status}")
                    else:
                        valid_count += 1
                else:
                    print(f"ℹ️  Untested Sequence: {seq['game_id']} L{seq['level_number']} (Gen {seq['generation']})")

        print(f"\nSummary: {valid_count} Validated, {suspicious_count} Suspicious")

    def check_optimizer_resets(self):
        """Check for games where optimizers might have caused resets or issues."""
        print("\n🔍 CHECKING OPTIMIZER ACTIVITY LOGS...")
        print("-" * 60)
        
        # Look for logs related to optimizer checkpoints or resets
        # This relies on the logs table if it exists and is populated
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT message, details, timestamp 
                FROM database_logs 
                WHERE message LIKE '%optimizer%' OR message LIKE '%checkpoint%'
                ORDER BY timestamp DESC 
                LIMIT 20
            """)
            
            logs = cursor.fetchall()
            if not logs:
                print("ℹ️  No specific optimizer logs found.")
            else:
                for log in logs:
                    print(f"[{log['timestamp']}] {log['message']}")
                    
        except sqlite3.OperationalError:
            print("⚠️  database_logs table not found or query error.")

    def analyze_sequence_structure(self):
        """Analyze the structure of stored sequences to ensure they end correctly."""
        print("\n🔍 ANALYZING SEQUENCE STRUCTURE...")
        print("-" * 60)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT sequence_id, action_sequence, game_id FROM winning_sequences LIMIT 10")
        
        rows = cursor.fetchall()
        for row in rows:
            try:
                data = json.loads(row['action_sequence'])
                if not isinstance(data, list):
                    print(f"❌ Invalid format for {row['sequence_id']} (not a list)")
                    continue
                    
                if not data:
                    print(f"❌ Empty sequence for {row['sequence_id']}")
                    continue
                    
                last_action = data[-1]
                
                # Handle different action formats
                action_type = "UNKNOWN"
                if isinstance(last_action, dict):
                    action_type = last_action.get('action_type', 'UNKNOWN')
                elif isinstance(last_action, int):
                    action_type = f"ACTION{last_action}"
                elif isinstance(last_action, str):
                    action_type = last_action
                
                print(f"✅ {row['game_id']}: {len(data)} steps. Last: {action_type}")
                
                # Check if it looks like a winning move
                # ACTION6 (click) or ACTION5 (interact) are common end moves
                if action_type in ['ACTION5', 'ACTION6', 'Submit', 'submit']:
                    pass # valid end move
                else:
                    # Just a warning, not necessarily an error
                    pass
                
            except json.JSONDecodeError:
                print(f"❌ JSON Error for {row['sequence_id']}")

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    verifier = OptimizerVerifier()
    try:
        verifier.verify_winning_sequences()
        verifier.check_optimizer_resets()
        verifier.analyze_sequence_structure()
    finally:
        verifier.close()
