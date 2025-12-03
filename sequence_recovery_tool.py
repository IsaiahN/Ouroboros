"""
Sequence Recovery Tool
======================
Analyzes backup databases and imports ONLY:
1. FRONTIER sequences: Levels we don't have in current DB
2. BETTER sequences: Fewer actions than current best for same level

Created: 2025-12-02
"""

import sys
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

# Paths
CURRENT_DB = Path(__file__).parent / "core_data.db"
BACKUP_DIR = Path(r"E:\Tabula Rasa and Ouroboros Data")


@dataclass
class SequenceInfo:
    """Information about a winning sequence."""
    game_id: str
    level_number: int
    action_count: int
    sequence_data: str
    source_db: str
    validation_success_rate: Optional[float] = None
    created_at: Optional[str] = None
    
    @property
    def game_type(self) -> str:
        """Extract game type from game_id (e.g., 'as66' from 'as66_xyz')."""
        return self.game_id.split('_')[0] if '_' in self.game_id else self.game_id[:4]


def get_current_sequences() -> Dict[Tuple[str, int], int]:
    """
    Get current best sequences from main database.
    Returns: {(game_type, level_number): min_action_count}
    """
    conn = sqlite3.connect(str(CURRENT_DB))
    conn.row_factory = sqlite3.Row
    
    try:
        # Get minimum action count per game_type + level
        # Handle both old schema (action_count) and new schema (total_actions)
        try:
            rows = conn.execute("""
                SELECT 
                    SUBSTR(game_id, 1, 4) as game_type,
                    level_number,
                    MIN(total_actions) as min_actions,
                    COUNT(*) as sequence_count
                FROM winning_sequences
                WHERE total_actions > 0
                GROUP BY game_type, level_number
                ORDER BY game_type, level_number
            """).fetchall()
        except sqlite3.OperationalError:
            # Try old schema
            rows = conn.execute("""
                SELECT 
                    SUBSTR(game_id, 1, 4) as game_type,
                    level_number,
                    MIN(action_count) as min_actions,
                    COUNT(*) as sequence_count
                FROM winning_sequences
                WHERE action_count > 0
                GROUP BY game_type, level_number
                ORDER BY game_type, level_number
            """).fetchall()
        
        result = {}
        for row in rows:
            key = (row['game_type'], row['level_number'])
            result[key] = row['min_actions']
        
        return result
    finally:
        conn.close()


def get_current_max_levels() -> Dict[str, int]:
    """Get maximum level reached per game type in current DB."""
    conn = sqlite3.connect(str(CURRENT_DB))
    conn.row_factory = sqlite3.Row
    
    try:
        # Handle both schemas
        try:
            rows = conn.execute("""
                SELECT 
                    SUBSTR(game_id, 1, 4) as game_type,
                    MAX(level_number) as max_level
                FROM winning_sequences
                WHERE total_actions > 0
                GROUP BY game_type
            """).fetchall()
        except sqlite3.OperationalError:
            rows = conn.execute("""
                SELECT 
                    SUBSTR(game_id, 1, 4) as game_type,
                    MAX(level_number) as max_level
                FROM winning_sequences
                WHERE action_count > 0
                GROUP BY game_type
            """).fetchall()
        
        return {row['game_type']: row['max_level'] for row in rows}
    finally:
        conn.close()


# Known valid max levels per game (user confirmed)
GAME_MAX_LEVELS = {
    'vc33': 4,   # User confirmed: highest valid level is 4
    'lp85': 0,   # Skip entirely - requires symbolic reasoning
    'as66': 20,  # Reasonable upper bound
    'ft09': 20,
    'ls20': 20,
    'sp80': 20,
}


def analyze_backup_db(db_path: Path, current_sequences: Dict[Tuple[str, int], int],
                      current_max_levels: Dict[str, int]) -> Dict[str, List[SequenceInfo]]:
    """
    Analyze a backup database for valuable sequences.
    
    Returns dict with:
    - 'frontier': Sequences for levels we don't have
    - 'better': Sequences with fewer actions than current best
    - 'duplicate': Sequences we already have (equal or worse)
    """
    results = {
        'frontier': [],
        'better': [],
        'duplicate': [],
        'invalid': []  # lp85, bogus levels, or bloated
    }
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30)
        conn.row_factory = sqlite3.Row
    except Exception as e:
        print(f"  [FAIL] Cannot open {db_path.name}: {e}")
        return results
    
    try:
        # Check if winning_sequences table exists
        try:
            tables = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='winning_sequences'
            """).fetchone()
        except sqlite3.DatabaseError as e:
            print(f"  [FAIL] Database error in {db_path.name}: {e}")
            return results
        
        if not tables:
            print(f"  [WARN]  No winning_sequences table in {db_path.name}")
            return results
        
        # Detect schema - check which columns exist
        columns = [col[1] for col in conn.execute("PRAGMA table_info(winning_sequences)").fetchall()]
        
        # Map column names based on schema
        action_col = 'total_actions' if 'total_actions' in columns else 'action_count'
        seq_col = 'action_sequence' if 'action_sequence' in columns else 'sequence_data'
        
        # Get all sequences from backup
        query = f"""
            SELECT 
                game_id,
                level_number,
                {action_col} as action_count,
                {seq_col} as sequence_data,
                discovered_at as created_at
            FROM winning_sequences
            WHERE {action_col} > 0 AND {seq_col} IS NOT NULL
            ORDER BY game_id, level_number, {action_col}
        """
        
        try:
            rows = conn.execute(query).fetchall()
        except sqlite3.OperationalError:
            # Try alternate column for created_at
            query = f"""
                SELECT 
                    game_id,
                    level_number,
                    {action_col} as action_count,
                    {seq_col} as sequence_data,
                    created_at
                FROM winning_sequences
                WHERE {action_col} > 0 AND {seq_col} IS NOT NULL
                ORDER BY game_id, level_number, {action_col}
            """
            rows = conn.execute(query).fetchall()
        
        for row in rows:
            game_type = row['game_id'].split('_')[0] if '_' in row['game_id'] else row['game_id'][:4]
            level = row['level_number']
            actions = row['action_count']
            
            seq_info = SequenceInfo(
                game_id=row['game_id'],
                level_number=level,
                action_count=actions,
                sequence_data=row['sequence_data'],
                source_db=db_path.name,
                created_at=row['created_at']
            )
            
            # Skip lp85 (requires symbolic reasoning)
            if game_type == 'lp85':
                results['invalid'].append(seq_info)
                continue
            
            # Skip sequences with less than 10 actions (likely incomplete/junk)
            if actions < 10:
                results['invalid'].append(seq_info)
                continue
            
            # Check if level exceeds known valid max for this game
            max_valid_level = GAME_MAX_LEVELS.get(game_type, 20)
            if level > max_valid_level:
                results['invalid'].append(seq_info)
                continue
            
            # Check for bloat (>10x what level 1 should take)
            # Level 1 should be ~10-50 actions, so >500 is suspicious
            expected_max = 50 + (level * 100)  # Rough heuristic
            if actions > expected_max * 10:
                results['invalid'].append(seq_info)
                continue
            
            key = (game_type, level)
            current_best = current_sequences.get(key)
            current_max = current_max_levels.get(game_type, 0)
            
            if current_best is None:
                # We don't have this level - it's frontier if beyond our max
                if level > current_max:
                    results['frontier'].append(seq_info)
                else:
                    # We should have it but don't - also valuable
                    results['frontier'].append(seq_info)
            elif actions < current_best:
                # Better than what we have
                results['better'].append(seq_info)
            else:
                # Duplicate or worse
                results['duplicate'].append(seq_info)
        
        return results
        
    finally:
        conn.close()


def print_analysis_report(db_name: str, results: Dict[str, List[SequenceInfo]]):
    """Print analysis report for a backup database."""
    frontier = results['frontier']
    better = results['better']
    duplicate = results['duplicate']
    invalid = results['invalid']
    
    total = len(frontier) + len(better) + len(duplicate) + len(invalid)
    
    print(f"\n{'='*60}")
    print(f"📁 {db_name}")
    print(f"{'='*60}")
    print(f"  Total sequences: {total}")
    print(f"  [LAUNCH] FRONTIER (new levels): {len(frontier)}")
    print(f"  ⚡ BETTER (fewer actions): {len(better)}")
    print(f"  ➖ Duplicate/worse: {len(duplicate)}")
    print(f"  [FAIL] Invalid (lp85/bloated): {len(invalid)}")
    
    if frontier:
        print(f"\n  [LAUNCH] FRONTIER SEQUENCES:")
        # Group by game type
        by_game: Dict[str, List[SequenceInfo]] = {}
        for seq in frontier:
            gt = seq.game_type
            if gt not in by_game:
                by_game[gt] = []
            by_game[gt].append(seq)
        
        for game_type in sorted(by_game.keys()):
            seqs = by_game[game_type]
            levels = sorted(set(s.level_number for s in seqs))
            min_actions = {l: min(s.action_count for s in seqs if s.level_number == l) for l in levels}
            print(f"     {game_type}: Levels {levels} (actions: {[min_actions[l] for l in levels]})")
    
    if better:
        print(f"\n  ⚡ BETTER SEQUENCES:")
        by_game: Dict[str, List[SequenceInfo]] = {}
        for seq in better:
            gt = seq.game_type
            if gt not in by_game:
                by_game[gt] = []
            by_game[gt].append(seq)
        
        for game_type in sorted(by_game.keys()):
            seqs = by_game[game_type]
            # Show improvement potential
            improvements = []
            for seq in seqs:
                key = (seq.game_type, seq.level_number)
                current = current_sequences.get(key, 0)
                if current:
                    improvement = current - seq.action_count
                    improvements.append(f"L{seq.level_number}: {seq.action_count} (saves {improvement})")
            print(f"     {game_type}: {', '.join(improvements[:5])}")


def import_sequences(sequences: List[SequenceInfo], dry_run: bool = True) -> int:
    """
    Import sequences into current database.
    
    Args:
        sequences: List of sequences to import
        dry_run: If True, only simulate (don't actually import)
    
    Returns:
        Number of sequences imported
    """
    if not sequences:
        return 0
    
    if dry_run:
        print(f"\n🔍 DRY RUN - Would import {len(sequences)} sequences")
        return len(sequences)
    
    conn = sqlite3.connect(str(CURRENT_DB))
    imported = 0
    
    try:
        for seq in sequences:
            try:
                # Check if we already have this exact sequence
                check_query = """
                    SELECT sequence_id FROM winning_sequences
                    WHERE game_id = ? AND level_number = ? AND total_actions = ?
                """
                existing = conn.execute(check_query, 
                    (seq.game_id, seq.level_number, seq.action_count)).fetchone()
                
                if existing:
                    continue
                
                # Generate unique sequence_id
                import uuid
                seq_id = f"recovered_{uuid.uuid4().hex[:12]}"
                
                # Insert with all required NOT NULL fields
                conn.execute("""
                    INSERT INTO winning_sequences 
                    (sequence_id, game_id, level_number, agent_id, session_id,
                     discovered_at, action_sequence, total_actions, total_score,
                     efficiency_score, initial_frame, final_frame, game_type,
                     success_rate_when_reused, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    seq_id,
                    seq.game_id,
                    seq.level_number,
                    'recovered_agent',  # agent_id - placeholder
                    'recovered_session',  # session_id - placeholder
                    seq.created_at or datetime.now().isoformat(),
                    seq.sequence_data,
                    seq.action_count,
                    0.0,  # total_score - unknown
                    1.0,  # efficiency_score - assume good since we're importing
                    '[]',  # initial_frame - unknown
                    '[]',  # final_frame - unknown
                    seq.game_type,
                    1.0,  # success_rate_when_reused
                    1     # is_active
                ))
                imported += 1
                print(f"  [OK] Imported {seq.game_id} L{seq.level_number} ({seq.action_count} actions)")
                
            except Exception as e:
                print(f"  [WARN]  Failed to import {seq.game_id} L{seq.level_number}: {e}")
                imported += 1
                
            except Exception as e:
                print(f"  [WARN]  Failed to import {seq.game_id} L{seq.level_number}: {e}")
        
        conn.commit()
        print(f"\n[OK] Imported {imported} sequences")
        return imported
        
    finally:
        conn.close()


def main():
    """Main analysis and import workflow."""
    print("="*60)
    print("SEQUENCE RECOVERY TOOL")
    print("="*60)
    print(f"\nCurrent database: {CURRENT_DB}")
    print(f"Backup directory: {BACKUP_DIR}")
    
    # Get current state
    print("\n[STATS] Analyzing current database...")
    global current_sequences
    current_sequences = get_current_sequences()
    current_max_levels = get_current_max_levels()
    
    print(f"  Current sequences: {len(current_sequences)} (game_type, level) pairs")
    print(f"  Max levels by game:")
    for game, level in sorted(current_max_levels.items()):
        count = sum(1 for k in current_sequences if k[0] == game)
        print(f"    {game}: Level {level} ({count} sequences)")
    
    # Find backup databases
    backup_dbs = list(BACKUP_DIR.glob("core_data*.db"))
    print(f"\n📁 Found {len(backup_dbs)} backup databases")
    
    # Analyze each backup
    all_frontier: List[SequenceInfo] = []
    all_better: List[SequenceInfo] = []
    
    for db_path in sorted(backup_dbs, key=lambda p: p.stat().st_mtime):
        results = analyze_backup_db(db_path, current_sequences, current_max_levels)
        print_analysis_report(db_path.name, results)
        
        # Collect valuable sequences (deduplicate by keeping best)
        for seq in results['frontier']:
            # Check if we already have a better one from another backup
            dominated = False
            for existing in all_frontier:
                if (existing.game_type == seq.game_type and 
                    existing.level_number == seq.level_number and
                    existing.action_count <= seq.action_count):
                    dominated = True
                    break
            if not dominated:
                # Remove any worse ones we already collected
                all_frontier = [s for s in all_frontier 
                               if not (s.game_type == seq.game_type and 
                                      s.level_number == seq.level_number and
                                      s.action_count > seq.action_count)]
                all_frontier.append(seq)
        
        for seq in results['better']:
            dominated = False
            for existing in all_better:
                if (existing.game_type == seq.game_type and 
                    existing.level_number == seq.level_number and
                    existing.action_count <= seq.action_count):
                    dominated = True
                    break
            if not dominated:
                all_better = [s for s in all_better 
                             if not (s.game_type == seq.game_type and 
                                    s.level_number == seq.level_number and
                                    s.action_count > seq.action_count)]
                all_better.append(seq)
    
    # Summary
    print("\n" + "="*60)
    print("RECOVERY SUMMARY")
    print("="*60)
    print(f"\n[LAUNCH] FRONTIER sequences to import: {len(all_frontier)}")
    if all_frontier:
        by_game: Dict[str, List[SequenceInfo]] = {}
        for seq in all_frontier:
            if seq.game_type not in by_game:
                by_game[seq.game_type] = []
            by_game[seq.game_type].append(seq)
        
        for game_type in sorted(by_game.keys()):
            seqs = by_game[game_type]
            levels = sorted(set(s.level_number for s in seqs))
            print(f"   {game_type}: {len(seqs)} sequences for levels {levels}")
    
    print(f"\n⚡ BETTER sequences to import: {len(all_better)}")
    if all_better:
        total_savings = 0
        by_game: Dict[str, List[SequenceInfo]] = {}
        for seq in all_better:
            if seq.game_type not in by_game:
                by_game[seq.game_type] = []
            by_game[seq.game_type].append(seq)
            key = (seq.game_type, seq.level_number)
            current = current_sequences.get(key, 0)
            if current:
                total_savings += current - seq.action_count
        
        print(f"   Total action savings: {total_savings}")
        for game_type in sorted(by_game.keys()):
            seqs = by_game[game_type]
            levels = sorted(set(s.level_number for s in seqs))
            print(f"   {game_type}: {len(seqs)} improvements for levels {levels}")
    
    # Combine for import
    to_import = all_frontier + all_better
    
    if not to_import:
        print("\n[OK] No new sequences to import - current database is up to date!")
        return
    
    print(f"\n[PKG] Total sequences to import: {len(to_import)}")
    
    # Ask for confirmation
    print("\n" + "-"*60)
    response = input("Import these sequences? [y/N/dry]: ").strip().lower()
    
    if response == 'y':
        imported = import_sequences(to_import, dry_run=False)
        print(f"\n[OK] Successfully imported {imported} sequences!")
    elif response == 'dry':
        import_sequences(to_import, dry_run=True)
    else:
        print("\n[FAIL] Import cancelled")


if __name__ == "__main__":
    main()
