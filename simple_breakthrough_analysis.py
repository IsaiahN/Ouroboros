#!/usr/bin/env python3
"""
Simple ARC Breakthrough Analysis
===============================
Find what's working for Level 2+ agents
"""

from database_interface import DatabaseInterface
import json

def main():
    print("🎯 ARC BREAKTHROUGH ANALYSIS")
    print("=" * 50)
    
    db = DatabaseInterface()
    
    # Get games with actual progress (Level 1+ or Score 2+)
    progress_games = db.execute_query("""
        SELECT game_id, final_score, level_completions, total_actions,
               status, end_time
        FROM game_results 
        WHERE level_completions >= 1 OR final_score >= 2.0
        ORDER BY level_completions DESC, final_score DESC
        LIMIT 20
    """)
    
    print(f"📈 GAMES WITH REAL PROGRESS: {len(progress_games)}")
    print("-" * 50)
    
    if progress_games:
        for i, game in enumerate(progress_games[:10], 1):
            print(f"{i:2}. {game['game_id'][:15]} → Score: {game['final_score']}, Levels: {game['level_completions']}")
            print(f"    Actions: {game['total_actions']}, Status: {game['status']}")
            print()
        
        # Get game types that are showing progress
        game_types = {}
        for game in progress_games:
            game_type = game['game_id'].split('-')[0]  # Extract game prefix
            if game_type not in game_types:
                game_types[game_type] = {'games': 0, 'max_score': 0, 'max_levels': 0}
            game_types[game_type]['games'] += 1
            game_types[game_type]['max_score'] = max(game_types[game_type]['max_score'], game['final_score'])
            game_types[game_type]['max_levels'] = max(game_types[game_type]['max_levels'], game['level_completions'])
        
        print("🎮 GAME TYPES SHOWING PROGRESS:")
        print("-" * 40)
        for game_type, stats in sorted(game_types.items(), key=lambda x: x[1]['max_levels'], reverse=True):
            print(f"{game_type}: {stats['games']} games, Max Score: {stats['max_score']}, Max Levels: {stats['max_levels']}")
    
    # Check winning sequences from these games
    winning_sequences = db.execute_query("""
        SELECT ws.sequence_id, ws.game_id, ws.level_number, ws.score_achieved,
               ws.actions_in_sequence, ws.sequence_data
        FROM winning_sequences ws
        JOIN game_results gr ON ws.game_id = gr.game_id
        WHERE gr.level_completions >= 1 OR gr.final_score >= 2.0
        ORDER BY ws.score_achieved DESC
        LIMIT 10
    """)
    
    print(f"\n🧠 WINNING SEQUENCES FROM PROGRESS GAMES:")
    print("-" * 50)
    
    if winning_sequences:
        for seq in winning_sequences:
            print(f"Seq: {seq['sequence_id'][:12]} (Game: {seq['game_id'][:8]})")
            print(f"  Level {seq['level_number']}: {seq['actions_in_sequence']} actions → {seq['score_achieved']} score")
            
            # Parse sequence data for insights
            try:
                if seq['sequence_data']:
                    seq_data = json.loads(seq['sequence_data'])
                    if 'actions' in seq_data:
                        actions = seq_data['actions'][:5]  # First 5 actions
                        print(f"  Actions: {actions}...")
            except:
                pass
            print()
    
    # Check current population for similar patterns
    print(f"\n🔬 WHAT TO OPTIMIZE:")
    print("-" * 30)
    
    if progress_games and game_types:
        best_game_type = max(game_types.items(), key=lambda x: x[1]['max_levels'])[0]
        print(f"1. Focus on {best_game_type} games (showing best progress)")
        
        # Check if we have specialists for this game type
        specialists = db.execute_query("""
            SELECT COUNT(*) as count 
            FROM agents 
            WHERE specialization LIKE ? AND is_active = 1
        """, [f'%{best_game_type}%'])
        
        if specialists and specialists[0]['count'] > 0:
            print(f"   ✅ Have {specialists[0]['count']} specialists")
        else:
            print(f"   ❌ Need more specialists for {best_game_type}")
    
    print(f"2. Increase breeding priority for agents with Level 1+ achievements")
    print(f"3. Replicate winning sequences from progress games")
    print(f"4. Run focused evolution on game types showing progress")
    
    # Check recent evolution activity
    recent_games = db.execute_query("""
        SELECT COUNT(*) as count
        FROM game_results 
        WHERE end_time > datetime('now', '-6 hours')
    """)
    
    if recent_games and recent_games[0]['count'] == 0:
        print(f"\n⚠️  SYSTEM STATUS: No games in last 6 hours")
        print(f"   → Resume evolution with --specialist mode focused on progress games")
    
    print(f"\n🚀 IMMEDIATE ACTION:")
    print(f"   python run_evolution.py --specialist --max-generations 15")
    print(f"   Focus breeding on agents with Level 1+ achievements")
    
    db.close()

if __name__ == "__main__":
    main()