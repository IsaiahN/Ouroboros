"""
Replay URL Lookup Helper
Quickly construct scorecard URLs from database session data.
The scorecard page has a "Watch replay" button to access the actual replay.

Correct URL Structure: https://three.arcprize.org/scorecards/<arc-session-id>
(NOT the direct replay URL - that requires clicking through from the scorecard page)

Usage:
    python get_replay_url.py <session_id>
    
Example:
    python get_replay_url.py session_abc123_456
    Output: https://three.arcprize.org/scorecards/5e7b312e-120f-49ea-93f4-af323dea6171
"""

import sqlite3
import sys

def get_scorecard_url(session_id: str) -> str:
    """
    Get the scorecard URL for a given session ID.
    From the scorecard page, click "Watch replay" to view the actual replay.
    
    Args:
        session_id: Session ID from database (e.g., session_abc123_456)
    
    Returns:
        Scorecard URL or error message
    """
    db = sqlite3.connect('core_data.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    # Get scorecard_id from game_results
    cursor.execute("""
        SELECT scorecard_id, game_id
        FROM game_results
        WHERE session_id = ?
        LIMIT 1
    """, (session_id,))
    
    result = cursor.fetchone()
    db.close()
    
    if not result:
        return f"Error: No game found for session_id '{session_id}'"
    
    scorecard_id = result['scorecard_id']
    
    if not scorecard_id:
        return f"Error: No scorecard_id found for session '{session_id}'"
    
    scorecard_url = f"https://three.arcprize.org/scorecards/{scorecard_id}"
    return scorecard_url


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python get_replay_url.py <session_id>")
        print("Example: python get_replay_url.py session_abc123_456")
        sys.exit(1)
    
    session_id = sys.argv[1]
    url = get_scorecard_url(session_id)
    print(url)
    print("\nNote: From the scorecard page, click 'Watch replay' to view the actual replay.")
