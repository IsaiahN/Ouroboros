import os
from datetime import datetime

file_path = r"C:\Users\Admin\Documents\GitHub\BitterTruth-AI\database_interface.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target_content = """        with self._get_connection() as conn:
            conn.execute(\"\"\"
                INSERT OR REPLACE INTO game_results (
                    game_id, session_id, scorecard_id, start_time, end_time, status,
                    final_score, total_actions, actions_taken, available_actions, win_detected,
                    level_completions, frame_changes, coordinate_attempts,
                    coordinate_successes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            \"\"\", (
                game_data['game_id'],
                game_data['session_id'],
                game_data.get('scorecard_id'),  # Store ARC scorecard ID
                game_data.get('start_time', datetime.now()),
                game_data.get('end_time', datetime.now()),
                game_data['status'],
                game_data.get('final_score', 0.0),
                game_data.get('total_actions', 0),
                json.dumps(game_data.get('actions_taken', [])),
                json.dumps(game_data.get('available_actions', [])),
                game_data.get('win_detected', False),
                game_data.get('level_completions', 0),
                game_data.get('frame_changes', 0),
                game_data.get('coordinate_attempts', 0),
                game_data.get('coordinate_successes', 0)
            ))
            conn.commit()

        logger.debug(f"Saved game result: {game_data['game_id']}")"""

replacement_content = """        with self._get_connection() as conn:
            # DEBUG: Trace save_game_result execution
            logger.debug(f"[DB_TRACE] save_game_result called for game={game_data['game_id']} session={game_data['session_id']} levels={game_data.get('level_completions', 0)} status={game_data['status']}")

            # CRITICAL FIX: Try UPDATE first, then INSERT if record doesn't exist
            cursor = conn.execute(\"\"\"
                UPDATE game_results 
                SET 
                    scorecard_id = ?,
                    end_time = ?,
                    status = ?,
                    final_score = ?,
                    total_actions = ?,
                    actions_taken = ?,
                    available_actions = ?,
                    win_detected = ?,
                    level_completions = ?,
                    frame_changes = ?,
                    coordinate_attempts = ?,
                    coordinate_successes = ?
                WHERE game_id = ? AND session_id = ?
            \"\"\", (
                game_data.get('scorecard_id'),
                game_data.get('end_time', datetime.now()),
                game_data['status'],
                game_data.get('final_score', 0.0),
                game_data.get('total_actions', 0),
                json.dumps(game_data.get('actions_taken', [])),
                json.dumps(game_data.get('available_actions', [])),
                game_data.get('win_detected', False),
                game_data.get('level_completions', 0),
                game_data.get('frame_changes', 0),
                game_data.get('coordinate_attempts', 0),
                game_data.get('coordinate_successes', 0),
                game_data['game_id'],
                game_data['session_id']
            ))
            
            # If no rows were updated, insert new record
            logger.debug(f"[DB_TRACE] UPDATE affected {cursor.rowcount} rows for game={game_data['game_id']}")
            if cursor.rowcount == 0:
                conn.execute(\"\"\"
                    INSERT INTO game_results (
                        game_id, session_id, scorecard_id, start_time, end_time, status,
                        final_score, total_actions, actions_taken, available_actions, win_detected,
                        level_completions, frame_changes, coordinate_attempts,
                        coordinate_successes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                \"\"\", (
                    game_data['game_id'],
                    game_data['session_id'],
                    game_data.get('scorecard_id'),
                    game_data.get('start_time', datetime.now()),
                    game_data.get('end_time', datetime.now()),
                    game_data['status'],
                    game_data.get('final_score', 0.0),
                    game_data.get('total_actions', 0),
                    json.dumps(game_data.get('actions_taken', [])),
                    json.dumps(game_data.get('available_actions', [])),
                    game_data.get('win_detected', False),
                    game_data.get('level_completions', 0),
                    game_data.get('frame_changes', 0),
                    game_data.get('coordinate_attempts', 0),
                    game_data.get('coordinate_successes', 0)
                ))
                logger.debug(f"Inserted new game result: {game_data['game_id']}")
            else:
                logger.debug(f"Updated game result: {game_data['game_id']} - score={game_data.get('final_score', 0.0)}, actions={game_data.get('total_actions', 0)}, levels={game_data.get('level_completions', 0)}")
            
            conn.commit()

        logger.debug(f"Saved game result: {game_data['game_id']}")"""

if target_content in content:
    new_content = content.replace(target_content, replacement_content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully applied fix to database_interface.py")
else:
    print("Target content not found in file. Please check indentation and content.")
    # Debug: print first 100 chars of target and where it might mismatch
    print("Target start:", target_content[:100])
