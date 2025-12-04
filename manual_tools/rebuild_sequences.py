"""Rebuild winning_sequences from valid action_traces data"""
import sqlite3
import json
import uuid
from datetime import datetime

def rebuild_sequences():
    conn = sqlite3.connect('core_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find game_results with level_completions > 0 that have matching action_traces
    # but NO winning_sequences
    cursor.execute('''
        SELECT gr.game_id, gr.session_id, gr.final_score, gr.level_completions, gr.scorecard_id
        FROM game_results gr
        WHERE gr.level_completions > 0
          AND gr.final_score > 0
          AND EXISTS (SELECT 1 FROM action_traces at WHERE at.session_id = gr.session_id)
        ORDER BY gr.final_score DESC, gr.created_at DESC
    ''')
    valid_games = cursor.fetchall()
    
    created_count = 0
    
    for game in valid_games:
        game_id = game['game_id']
        session_id = game['session_id']
        final_score = game['final_score']
        level_completions = game['level_completions']
        scorecard_id = game['scorecard_id']
        
        # Check if sequence already exists for this game
        cursor.execute('SELECT COUNT(*) as cnt FROM winning_sequences WHERE game_id = ?', (game_id,))
        existing_count = cursor.fetchone()['cnt']
        
        # Get action_traces for this session
        cursor.execute('''
            SELECT action_number, coordinates, frame_before, frame_after, level_number
            FROM action_traces
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))
        traces = cursor.fetchall()
        
        if not traces:
            continue
        
        # Extract actions and coordinates
        actions = [t['action_number'] for t in traces]
        coordinates = []
        for t in traces:
            if t['action_number'] == 6 and t['coordinates']:
                try:
                    coord = json.loads(t['coordinates'])
                    coordinates.append(coord)
                except:
                    pass
        
        # Get frames
        initial_frame = json.loads(traces[0]['frame_before']) if traces[0]['frame_before'] else []
        final_frame = json.loads(traces[-1]['frame_after']) if traces[-1]['frame_after'] else []
        
        # Calculate efficiency
        efficiency = final_score / len(actions) if len(actions) > 0 else 0.0
        
        # Determine level_number (score = levels completed)
        level_number = int(final_score)
        
        # Classify game type based on actions
        action_counts = {}
        for a in actions:
            action_counts[a] = action_counts.get(a, 0) + 1
        
        if 6 in action_counts and action_counts[6] > len(actions) * 0.5:
            game_type = 'coordinate_heavy'
        elif len(set(actions)) >= 4:
            game_type = 'diverse_actions'
        else:
            game_type = 'mixed_actions'
        
        # Check if we should create this sequence
        # Skip if we already have 3+ sequences for this game-level with better efficiency
        if existing_count >= 3:
            cursor.execute('''
                SELECT MIN(efficiency_score) as min_eff
                FROM winning_sequences
                WHERE game_id = ? AND level_number = ? AND is_active = 1
            ''', (game_id, level_number))
            min_eff = cursor.fetchone()['min_eff']
            if min_eff and efficiency <= min_eff:
                print(f'  Skipping {game_id} L{level_number} - already have 3+ better sequences')
                continue
        
        # Create sequence
        sequence_id = f"seq_{uuid.uuid4().hex[:16]}"
        
        cursor.execute('''
            INSERT INTO winning_sequences (
                sequence_id, game_id, level_number, agent_id, session_id, scorecard_id,
                action_sequence, coordinate_sequence, total_actions, total_score,
                efficiency_score, initial_frame, final_frame, frame_transitions,
                pattern_tags, game_type, discovered_at, generation_discovered, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sequence_id, game_id, level_number, 'rebuild_script', session_id, scorecard_id,
            json.dumps(actions), json.dumps(coordinates), len(actions),
            final_score, efficiency, json.dumps(initial_frame),
            json.dumps(final_frame), json.dumps([]),  # frame_transitions
            json.dumps([game_type]), game_type, datetime.now().isoformat(),
            0,  # generation_discovered
            1   # is_active
        ))
        
        created_count += 1
        print(f'[OK] Created {sequence_id} for {game_id} L{level_number}: {len(actions)} actions, score={final_score}')
    
    conn.commit()
    conn.close()
    
    print(f'\nDone! Created {created_count} sequences from action_traces')

if __name__ == '__main__':
    rebuild_sequences()
