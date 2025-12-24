"""Check primitive and operator status in the database."""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sqlite3
import json
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_status():
    conn = sqlite3.connect('core_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print('=== PRIMITIVE STATUS ===')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='primitive_status'")
    if cursor.fetchone():
        cursor.execute('SELECT status, COUNT(*) as cnt FROM primitive_status GROUP BY status')
        for row in cursor.fetchall():
            print(f"  {row['status']}: {row['cnt']}")
    else:
        print('  Table does not exist')

    print('\n=== COMPOSED OPERATORS ===')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='composed_operators'")
    if cursor.fetchone():
        cursor.execute('SELECT COUNT(*) as cnt FROM composed_operators')
        total = cursor.fetchone()['cnt']
        print(f'  Total operators: {total}')
        
        if total > 0:
            print("\n  Operators by status:")
            cursor.execute('SELECT status, COUNT(*) as cnt FROM composed_operators GROUP BY status')
            for row in cursor.fetchall():
                print(f"    {row['status']}: {row['cnt']}")
            
            print("\n  Top 10 by usage:")
            cursor.execute('SELECT name, times_tested, successes, failures, success_rate, status FROM composed_operators ORDER BY times_tested DESC LIMIT 10')
            for row in cursor.fetchall():
                print(f"    {row['name']}: tested={row['times_tested']}, success={row['successes']}, fail={row['failures']}, rate={row['success_rate']:.2f}, status={row['status']}")
    else:
        print('  Table does not exist')

    print('\n=== UNLOCK ATTEMPTS ===')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='primitive_unlock_attempts'")
    if cursor.fetchone():
        cursor.execute('SELECT COUNT(*) as cnt FROM primitive_unlock_attempts')
        total = cursor.fetchone()['cnt']
        print(f'  Total attempts: {total}')
    else:
        print('  Table does not exist')

    conn.close()


def test_operators():
    """Test composed operators to generate usage data."""
    from cods_engine import get_cods_engine
    
    engine = get_cods_engine('core_data.db')
    
    # Create a test frame
    test_frame = [[0, 1, 2], [1, 2, 3], [2, 3, 4]]
    
    # Set context
    engine.set_context(
        game_id='test-001',
        level_number=1,
        agent_id='test-agent',
        generation=1
    )
    
    print('=== Testing composed operators ===')
    results = engine.test_composed_operators(frame=test_frame, score_delta=0.0)
    print(f'Tested {len(results)} operators:')
    for name, success in results.items():
        status = "SUCCESS" if success else "FAIL"
        print(f'  {name}: {status}')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_operators()
        print('')
    
    check_status()
