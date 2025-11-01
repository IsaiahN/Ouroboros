#!/usr/bin/env python3
"""
Real-Time Evolution Monitor
===========================

Displays live stats while evolution runs in another terminal.
Refreshes every 30 seconds.

Usage:
    python monitor_evolution.py
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import time
from datetime import datetime, timedelta
from database_interface import DatabaseInterface

def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def format_timedelta(td):
    """Format timedelta nicely."""
    seconds = int(td.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def get_stats(db):
    """Get current evolution stats."""
    
    # Population stats
    pop = db.execute_query("""
        SELECT 
            COUNT(*) as total_active,
            MAX(generation) as max_gen,
            MIN(generation) as min_gen
        FROM agents WHERE is_active = 1
    """)
    
    total_active = pop[0][0] if pop else 0
    max_gen = pop[0][1] if pop else 0
    min_gen = pop[0][2] if pop else 0
    
    # Recent activity (last hour)
    recent = db.execute_query("""
        SELECT 
            COUNT(*) as games,
            SUM(level_completions) as levels,
            AVG(total_actions) as avg_actions,
            MAX(end_time) as last_game
        FROM game_results
        WHERE end_time > datetime('now', '-1 hour')
    """)
    
    recent_games = recent[0][0] if recent else 0
    recent_levels = recent[0][1] if recent and recent[0][1] else 0
    recent_avg_actions = recent[0][2] if recent and recent[0][2] else 0
    last_game_time = recent[0][3] if recent and recent[0][3] else None
    
    # All-time stats
    all_time = db.execute_query("""
        SELECT 
            COUNT(*) as total_games,
            SUM(level_completions) as total_levels,
            SUM(CASE WHEN level_completions > 0 THEN 1 ELSE 0 END) as games_with_levels
        FROM game_results
    """)
    
    total_games = all_time[0][0] if all_time else 0
    total_levels = all_time[0][1] if all_time and all_time[0][1] else 0
    games_with_levels = all_time[0][2] if all_time else 0
    
    # Top performers
    top_agents = db.execute_query("""
        SELECT agent_id, generation, total_games_played, avg_score_per_game
        FROM agents 
        WHERE is_active = 1 AND total_games_played > 5
        ORDER BY avg_score_per_game DESC
        LIMIT 5
    """)
    
    # Generation breakdown
    gen_breakdown = db.execute_query("""
        SELECT generation, COUNT(*) as count
        FROM agents WHERE is_active = 1
        GROUP BY generation
        ORDER BY generation DESC
        LIMIT 5
    """)
    
    # Community memory
    sequences = db.execute_query("""
        SELECT COUNT(*) as count
        FROM winning_sequences
    """)
    
    sequence_count = sequences[0][0] if sequences else 0
    
    return {
        'total_active': total_active,
        'max_gen': max_gen,
        'min_gen': min_gen,
        'recent_games': recent_games,
        'recent_levels': recent_levels,
        'recent_avg_actions': recent_avg_actions,
        'last_game_time': last_game_time,
        'total_games': total_games,
        'total_levels': total_levels,
        'games_with_levels': games_with_levels,
        'top_agents': top_agents,
        'gen_breakdown': gen_breakdown,
        'sequence_count': sequence_count
    }

def display_stats(stats):
    """Display stats in formatted output."""
    clear_screen()
    
    print("="*80)
    print("🐍 OUROBOROS EVOLUTION MONITOR".center(80))
    print("="*80)
    print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Population
    print("📊 POPULATION")
    print("-"*80)
    print(f"  Active Agents: {stats['total_active']}")
    print(f"  Current Generation: {stats['max_gen']}")
    print(f"  Generation Range: {stats['min_gen']} - {stats['max_gen']}")
    print()
    
    if stats['gen_breakdown']:
        print("  Generation Breakdown:")
        for row in stats['gen_breakdown']:
            gen = row[0] if not isinstance(row, dict) else row['generation']
            count = row[1] if not isinstance(row, dict) else row['count']
            bar = "█" * (count // 5)
            print(f"    Gen {gen:2d}: {count:3d} agents {bar}")
        print()
    
    # Recent Activity
    print("⚡ LAST HOUR")
    print("-"*80)
    print(f"  Games Played: {stats['recent_games']}")
    print(f"  Levels Completed: {stats['recent_levels']}")
    
    if stats['recent_games'] > 0:
        success_rate = (stats['recent_levels'] / stats['recent_games']) * 100
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Avg Actions/Game: {stats['recent_avg_actions']:.0f}")
    
    if stats['last_game_time']:
        last_game = datetime.fromisoformat(stats['last_game_time'])
        time_since = datetime.now() - last_game
        print(f"  Last Game: {format_timedelta(time_since)} ago")
        
        if time_since.total_seconds() > 600:  # 10 minutes
            print(f"  ⚠️  WARNING: No games in 10+ minutes!")
    print()
    
    # All-Time Stats
    print("📈 ALL-TIME STATS")
    print("-"*80)
    print(f"  Total Games: {stats['total_games']}")
    print(f"  Total Levels: {stats['total_levels']}")
    
    if stats['total_games'] > 0:
        success_rate = (stats['games_with_levels'] / stats['total_games']) * 100
        avg_levels = stats['total_levels'] / stats['total_games']
        print(f"  Games with Levels: {stats['games_with_levels']} ({success_rate:.1f}%)")
        print(f"  Avg Levels/Game: {avg_levels:.3f}")
    print()
    
    # Top Performers
    print("🏆 TOP 5 PERFORMERS")
    print("-"*80)
    if stats['top_agents']:
        for row in stats['top_agents']:
            agent_id = row[0] if not isinstance(row, dict) else row['agent_id']
            gen = row[1] if not isinstance(row, dict) else row['generation']
            games = row[2] if not isinstance(row, dict) else row['total_games_played']
            avg_score = row[3] if not isinstance(row, dict) else row['avg_score_per_game']
            
            print(f"  {agent_id[:20]:20s} | Gen {gen:2d} | {games:3d} games | {avg_score:.3f} avg")
    else:
        print("  No agents with >5 games yet")
    print()
    
    # Community Memory
    print("🧠 COMMUNITY MEMORY")
    print("-"*80)
    print(f"  Winning Sequences Discovered: {stats['sequence_count']}")
    print()
    
    # System Health
    print("💚 SYSTEM HEALTH")
    print("-"*80)
    
    health_checks = []
    
    # Check population
    if 50 <= stats['total_active'] <= 200:
        health_checks.append(("✅", "Population controlled (50-200)"))
    elif stats['total_active'] > 200:
        health_checks.append(("⚠️", f"Population high ({stats['total_active']})"))
    else:
        health_checks.append(("ℹ️", f"Population growing ({stats['total_active']})"))
    
    # Check recent activity
    if stats['recent_games'] > 0:
        health_checks.append(("✅", "Games being played"))
    else:
        health_checks.append(("⚠️", "No recent games"))
    
    # Check level completions
    if stats['recent_levels'] > 0:
        health_checks.append(("✅", "Levels being completed"))
    else:
        health_checks.append(("ℹ️", "No recent level completions"))
    
    # Check action counts
    if 0 < stats['recent_avg_actions'] <= 3000:
        health_checks.append(("✅", "Action limits enforced"))
    elif stats['recent_avg_actions'] > 3000:
        health_checks.append(("⚠️", "Action counts high"))
    
    for emoji, message in health_checks:
        print(f"  {emoji} {message}")
    
    print()
    print("="*80)
    print("Press Ctrl+C to stop monitoring".center(80))
    print("="*80)

def main():
    """Main monitoring loop."""
    db = DatabaseInterface()
    
    print("Starting evolution monitor...")
    print("This will refresh every 30 seconds")
    print()
    
    try:
        while True:
            try:
                stats = get_stats(db)
                display_stats(stats)
                time.sleep(30)  # Update every 30 seconds
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)
                
    except KeyboardInterrupt:
        clear_screen()
        print("\n\nMonitoring stopped.")
        print("Evolution may still be running in another terminal.")
        print()

if __name__ == "__main__":
    main()
