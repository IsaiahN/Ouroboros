"""
Quick diagnostic script to check CODS/primitives status.
"""
import os
import sys
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

def check_cods_status():
    # Check database for composed operators
    conn = sqlite3.connect('core_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print('=== COMPOSED OPERATORS IN DATABASE ===')
    try:
        cursor.execute('SELECT COUNT(*) FROM composed_operators')
        total = cursor.fetchone()[0]
        print(f'Total operators: {total}')
        
        cursor.execute('SELECT operator_id, name, status, times_tested, success_rate FROM composed_operators ORDER BY times_tested DESC LIMIT 15')
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row['name']}: status={row['status']}, tested={row['times_tested']}, success={row['success_rate']:.2f}")
    except Exception as e:
        print(f'Error: {e}')

    print()
    print('=== PRIMITIVE STATUS ===')
    try:
        cursor.execute('SELECT status, COUNT(*) as cnt FROM primitive_status GROUP BY status')
        for row in cursor.fetchall():
            print(f"  {row['status']}: {row['cnt']}")
    except Exception as e:
        print(f'Error or table missing: {e}')

    print()
    print('=== OPERATOR TEST RESULTS (recent) ===')
    try:
        cursor.execute('SELECT COUNT(*) FROM operator_test_results')
        total = cursor.fetchone()[0]
        print(f'Total test results: {total}')
        
        if total > 0:
            cursor.execute('''
                SELECT operator_id, game_id, success, 
                       COALESCE(score_after, 0) - COALESCE(score_before, 0) as score_delta 
                FROM operator_test_results 
                ORDER BY created_at DESC LIMIT 5
            ''')
            for row in cursor.fetchall():
                op_id = row['operator_id'][:20] if row['operator_id'] else 'N/A'
                game = row['game_id'][:12] if row['game_id'] else 'N/A'
                print(f"  {op_id}: game={game}, success={row['success']}, delta={row['score_delta']}")
    except Exception as e:
        print(f'Error: {e}')

    print()
    print('=== UNLOCK ATTEMPTS ===')
    try:
        cursor.execute('SELECT COUNT(*) FROM primitive_unlock_attempts')
        total = cursor.fetchone()[0]
        print(f'Total unlock attempts: {total}')
        
        if total > 0:
            cursor.execute('''
                SELECT primitive_name, oracle_verdict, success_rate, unlocked 
                FROM primitive_unlock_attempts 
                ORDER BY created_at DESC LIMIT 5
            ''')
            for row in cursor.fetchall():
                print(f"  {row['primitive_name']}: verdict={row['oracle_verdict']}, success={row['success_rate']:.2f}, unlocked={row['unlocked']}")
    except Exception as e:
        print(f'Error: {e}')

    conn.close()
    
    # Now test live primitive execution
    print()
    print('=== LIVE PRIMITIVE TEST ===')
    try:
        from seed_primitives import get_seed_primitives
        
        registry = get_seed_primitives()
        print(f'Registered primitives: {registry.count()}')
        print(f'Categories: {registry.get_stats()}')
        
        # Set up test frame
        test_frame = [[0, 1, 2], [1, 2, 3], [2, 3, 4]]
        registry.update_frame(test_frame)
        
        # Test primitives
        print(f"get_frame(): {registry.call('get_frame')}")
        print(f"get_frame_size(frame): {registry.call('get_frame_size', test_frame)}")
        print(f"add(5, 3): {registry.call('add', 5, 3)}")
        print(f"equals(2, 2): {registry.call('equals', 2, 2)}")
        print(f"get_pixel(frame, 1, 1): {registry.call('get_pixel', test_frame, 1, 1)}")
        
    except Exception as e:
        import traceback
        print(f'Error: {e}')
        traceback.print_exc()

    # Test CODS engine
    print()
    print('=== CODS ENGINE TEST ===')
    try:
        from engines.social.cods_engine import get_cods_engine
        
        engine = get_cods_engine('core_data.db')
        print('CODS engine initialized')
        
        # Bootstrap operators
        bootstrap_count = engine.bootstrap_operators_from_patterns(limit=10)
        print(f'Bootstrap operators created: {bootstrap_count}')
        
        # Set context
        engine.set_context(game_id='test-game', level_number=1)
        
        # Update frame
        engine.update_frame(test_frame, score=0.0, action_count=1)
        
        # Try applying a seed primitive directly
        result = engine.apply('add', 5, 3)
        print(f"engine.apply('add', 5, 3): success={result.success}, output={result.output}")
        
        # Test seed primitive call directly  
        print()
        print('=== Direct seed primitive execution ===')
        frame = engine.seeds.call('get_frame')
        print(f'get_frame via seeds.call(): {frame}')
        frame_len = engine.seeds.call('len', frame)
        print(f'len(frame): {frame_len}')
        
        # Now test composed operator
        print()
        print('=== Composed operator test ===')
        op = engine.composer.get_operator_by_name('op_get_frame')
        if op:
            print(f'Found operator: {op.operator_id}')
            print(f'Composition tree: {op.composition_tree}')
            try:
                result = engine.composer.execute(op)
                print(f'Execution result: {result}')
            except Exception as e:
                print(f'Execution error: {e}')
                import traceback
                traceback.print_exc()
        else:
            print('Operator op_get_frame not found')
        
    except Exception as e:
        import traceback
        print(f'Error: {e}')
        traceback.print_exc()


if __name__ == '__main__':
    check_cods_status()
