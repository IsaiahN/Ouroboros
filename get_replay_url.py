"""
Replay URL Lookup Helper
Quickly construct replay URLs from database session data.

URL Structure: https://three.arcprize.org/replay/<full-game-id>/<arc-session-id>

Usage:
    python get_replay_url.py <session_id>
    
Example:
    python get_replay_url.py session_abc123_456
    Output: https://three.arcprize.org/replay/lp85-d265526edbaa/546dc633-4cb4-4e26-bcf5-33a8a2457582
"""

import sqlite3
import sys

def get_replay_url(session_id: str) -> str:
    """
    Get the replay URL for a given session ID.
    
    Args:
        session_id: Session ID from database (e.g., session_abc123_456)
    
    Returns:
        Full replay URL or error message
    """
    db = sqlite3.connect('core_data.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    # Get game_id and scorecard_id from game_results
    cursor.execute("""
        SELECT game_id, scorecard_id
        FROM game_results
        WHERE session_id = ?
        LIMIT 1
    """, (session_id,))
    
    result = cursor.fetchone()
    db.close()
    
    if not result:
        return f"Error: No game found for session_id '{session_id}'"
    
    game_id = result['game_id']
    scorecard_id = result['scorecard_id']
    
    if not scorecard_id:
        return f"Error: No scorecard_id found for session '{session_id}'"
    
    replay_url = f"https://three.arcprize.org/replay/{game_id}/{scorecard_id}"
    return replay_url


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python get_replay_url.py <session_id>")
        print("Example: python get_replay_url.py session_abc123_456")
        sys.exit(1)
    
    session_id = sys.argv[1]
    url = get_replay_url(session_id)
    print(url)
