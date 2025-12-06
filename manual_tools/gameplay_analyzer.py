"""
Gameplay Progression Analyzer
=============================
Reusable tool for analyzing agent gameplay performance across generations.

Usage:
    python manual_tools/gameplay_analyzer.py                    # Default: last 3 hours
    python manual_tools/gameplay_analyzer.py --hours 6          # Last 6 hours
    python manual_tools/gameplay_analyzer.py --generations 270  # From generation 270+
    python manual_tools/gameplay_analyzer.py --compare          # Include baseline comparison
    python manual_tools/gameplay_analyzer.py --full             # Full analysis with all options
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

import sqlite3
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_db_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Get database connection with row factory."""
    if db_path is None:
        # Find core_data.db relative to this script
        script_dir = Path(__file__).parent.parent
        db_path = str(script_dir / 'core_data.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def analyze_recent_games(conn: sqlite3.Connection, hours: int = 3, limit: int = 30) -> list:
    """Analyze recent game results."""
    recent = conn.execute('''
        SELECT 
            strftime('%H:%M', created_at) as time,
            game_id,
            final_score,
            level_completions,
            total_actions,
            win_detected,
            created_at
        FROM game_results
        WHERE created_at >= datetime('now', ? || ' hours')
        ORDER BY created_at DESC
        LIMIT ?
    ''', (f'-{hours}', limit)).fetchall()
    
    return [dict(r) for r in recent]


def get_summary_stats(conn: sqlite3.Connection, hours: int = 3) -> dict:
    """Get summary statistics for recent games."""
    summary = conn.execute('''
        SELECT 
            COUNT(*) as total_games,
            SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as positive_scores,
            SUM(CASE WHEN win_detected = 1 THEN 1 ELSE 0 END) as games_won,
            AVG(final_score) as avg_score,
            AVG(level_completions) as avg_levels,
            MAX(final_score) as best_score,
            MAX(level_completions) as best_levels
        FROM game_results
        WHERE created_at >= datetime('now', ? || ' hours')
    ''', (f'-{hours}',)).fetchone()
    
    return dict(summary)


def get_winning_sequences(conn: sqlite3.Connection, hours: int = 3) -> dict:
    """Get new winning sequences in time period."""
    seqs = conn.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
            COUNT(DISTINCT game_id) as unique_games
        FROM winning_sequences
        WHERE discovered_at >= datetime('now', ? || ' hours')
    ''', (f'-{hours}',)).fetchone()
    
    return dict(seqs)


def get_agents_by_generation(conn: sqlite3.Connection, min_generation: int = 0) -> list:
    """Get active agents grouped by generation."""
    agents = conn.execute('''
        SELECT 
            generation,
            COUNT(*) as count,
            AVG(total_games_played) as avg_games,
            AVG(total_score_achieved) as avg_score
        FROM agents
        WHERE generation >= ? AND is_active = 1
        GROUP BY generation
        ORDER BY generation
    ''', (min_generation,)).fetchall()
    
    return [dict(a) for a in agents]


def get_baseline_comparison(conn: sqlite3.Connection, current_hours: int = 3, baseline_hours: int = 24) -> dict:
    """Compare current performance against baseline."""
    baseline = conn.execute('''
        SELECT 
            AVG(final_score) as avg_score,
            AVG(level_completions) as avg_levels,
            COUNT(*) as games
        FROM game_results
        WHERE created_at BETWEEN datetime('now', ? || ' hours') AND datetime('now', ? || ' hours')
    ''', (f'-{baseline_hours}', f'-{current_hours}')).fetchone()
    
    current = conn.execute('''
        SELECT 
            AVG(final_score) as avg_score,
            AVG(level_completions) as avg_levels,
            COUNT(*) as games
        FROM game_results
        WHERE created_at >= datetime('now', ? || ' hours')
    ''', (f'-{current_hours}',)).fetchone()
    
    return {
        'baseline': dict(baseline),
        'current': dict(current)
    }


def get_game_distribution(conn: sqlite3.Connection, hours: int = 3) -> list:
    """Get distribution of games played."""
    dist = conn.execute('''
        SELECT 
            SUBSTR(game_id, 1, 4) as game_type,
            COUNT(*) as count,
            AVG(final_score) as avg_score,
            MAX(final_score) as best_score,
            SUM(level_completions) as total_levels
        FROM game_results
        WHERE created_at >= datetime('now', ? || ' hours')
        GROUP BY SUBSTR(game_id, 1, 4)
        ORDER BY count DESC
    ''', (f'-{hours}',)).fetchall()
    
    return [dict(d) for d in dist]


def print_analysis(hours: int = 3, min_generation: int = 0, include_baseline: bool = True, 
                   include_games: bool = True, limit: int = 30):
    """Print full gameplay analysis."""
    conn = get_db_connection()
    
    print('=' * 70)
    print(f'GAMEPLAY PROGRESSION ANALYSIS')
    print(f'Time Range: Last {hours} hours | Min Generation: {min_generation}')
    print('=' * 70)
    
    # Recent games
    if include_games:
        recent = analyze_recent_games(conn, hours, limit)
        print(f'\nRECENT GAME RESULTS (Last {hours} Hours, limit {limit}):')
        print('-' * 70)
        print(f'{"Time":5} | {"Game ID":25} | {"Score":5} | {"Lvls":4} | {"Actions":7} | {"Won":3}')
        print('-' * 70)
        for r in recent:
            gid = (r["game_id"] or "N/A")[:25]
            score = r["final_score"] or 0
            lvls = r["level_completions"] or 0
            actions = r["total_actions"] or 0
            won = "YES" if r["win_detected"] else "no"
            print(f'{r["time"]:5} | {gid:25} | {score:5} | {lvls:4} | {actions:7} | {won:3}')
    
    # Summary stats
    summary = get_summary_stats(conn, hours)
    print(f'\n\nSUMMARY (Last {hours} Hours):')
    print('-' * 70)
    total = summary["total_games"] or 1
    positive = summary["positive_scores"] or 0
    print(f'  Total Games: {summary["total_games"]}')
    print(f'  Positive Scores: {positive} ({positive/total*100:.1f}%)')
    print(f'  Game Wins: {summary["games_won"]}')
    print(f'  Avg Score: {summary["avg_score"] or 0:.2f}')
    print(f'  Avg Levels: {summary["avg_levels"] or 0:.2f}')
    print(f'  Best Score: {summary["best_score"]}')
    print(f'  Best Levels: {summary["best_levels"]}')
    
    # Game distribution
    dist = get_game_distribution(conn, hours)
    if dist:
        print(f'\n\nGAME TYPE DISTRIBUTION:')
        print('-' * 70)
        print(f'{"Type":6} | {"Count":5} | {"Avg Score":9} | {"Best":5} | {"Total Lvls":10}')
        print('-' * 70)
        for d in dist[:10]:
            print(f'{d["game_type"]:6} | {d["count"]:5} | {d["avg_score"] or 0:9.2f} | {d["best_score"] or 0:5} | {d["total_levels"] or 0:10}')
    
    # Winning sequences
    seqs = get_winning_sequences(conn, hours)
    print(f'\n\nNEW WINNING SEQUENCES (Last {hours} Hours):')
    print('-' * 70)
    print(f'  Total New: {seqs["total"]}')
    print(f'  Active: {seqs["active"]}')
    print(f'  Unique Games: {seqs["unique_games"]}')
    
    # Agents by generation
    if min_generation > 0:
        agents = get_agents_by_generation(conn, min_generation)
        if agents:
            print(f'\n\nACTIVE AGENTS BY GENERATION (>= {min_generation}):')
            print('-' * 70)
            print(f'{"Gen":4} | {"Count":5} | {"Avg Games":9} | {"Avg Total Score":15}')
            print('-' * 70)
            for a in agents:
                print(f'{a["generation"]:4} | {a["count"]:5} | {a["avg_games"] or 0:9.1f} | {a["avg_score"] or 0:.1f}')
    
    # Baseline comparison
    if include_baseline:
        comp = get_baseline_comparison(conn, hours, 24)
        baseline = comp['baseline']
        current = comp['current']
        
        print(f'\n\nBASELINE COMPARISON:')
        print('-' * 70)
        if baseline["games"] and baseline["games"] > 0:
            b_avg = baseline["avg_score"] or 0
            b_lvl = baseline["avg_levels"] or 0
            c_avg = current["avg_score"] or 0
            c_lvl = current["avg_levels"] or 0
            print(f'  Baseline ({hours}-24h ago): Avg Score: {b_avg:.2f} | Avg Levels: {b_lvl:.2f} ({baseline["games"]} games)')
            print(f'  Current (last {hours}h):    Avg Score: {c_avg:.2f} | Avg Levels: {c_lvl:.2f} ({current["games"]} games)')
            if b_avg > 0:
                score_diff = ((c_avg - b_avg) / b_avg) * 100
                print(f'  Score Change: {score_diff:+.1f}%')
            if b_lvl > 0:
                lvl_diff = ((c_lvl - b_lvl) / b_lvl) * 100
                print(f'  Level Change: {lvl_diff:+.1f}%')
        else:
            print(f'  No baseline data available')
    
    conn.close()
    print('\n' + '=' * 70)


def main():
    parser = argparse.ArgumentParser(description='Analyze gameplay progression')
    parser.add_argument('--hours', type=int, default=3, help='Hours to analyze (default: 3)')
    parser.add_argument('--generations', type=int, default=0, help='Minimum generation to include')
    parser.add_argument('--compare', action='store_true', help='Include baseline comparison')
    parser.add_argument('--no-games', action='store_true', help='Skip individual game listing')
    parser.add_argument('--limit', type=int, default=30, help='Max games to show (default: 30)')
    parser.add_argument('--full', action='store_true', help='Full analysis with all options')
    
    args = parser.parse_args()
    
    if args.full:
        args.compare = True
        args.hours = 6
        args.limit = 50
    
    print_analysis(
        hours=args.hours,
        min_generation=args.generations,
        include_baseline=args.compare or args.full,
        include_games=not args.no_games,
        limit=args.limit
    )


if __name__ == '__main__':
    main()
