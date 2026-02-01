#!/usr/bin/env python3
"""
Test Pariah Decay System
========================
Validates the new pariah decay and role-adjusted tolerance mechanisms.
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database_interface import DatabaseInterface
from engines.social.viral_package_engine import ViralPackageEngine


def test_pariah_decay():
    db = DatabaseInterface()
    engine = ViralPackageEngine(db)

    print('=' * 60)
    print('TESTING PARIAH DECAY SYSTEM')
    print('=' * 60)

    # 1. Test decay_pariah_toxicity
    print('\n1. Testing decay_pariah_toxicity (generation 280)...')
    engine.decay_pariah_toxicity(280)

    # 2. Test get_role_adjusted_pariah_penalties for different roles
    print('\n2. Testing role-adjusted penalties for different roles...')

    # Find an agent with pariah awareness
    awareness = db.execute_query('''
        SELECT agent_id, COUNT(*) as cnt
        FROM agent_pariah_awareness
        WHERE is_active = 1
        GROUP BY agent_id
        ORDER BY cnt DESC
        LIMIT 1
    ''')

    if awareness:
        test_agent = awareness[0]['agent_id']
        print(f'   Using test agent: {test_agent} ({awareness[0]["cnt"]} pariahs)')

        for role in ['generalist', 'pioneer', 'optimizer', 'exploiter']:
            penalties = engine.get_role_adjusted_pariah_penalties(
                agent_id=test_agent,
                agent_role=role,
                game_id='lp85-xxx',
                level_number=1
            )
            total_penalty = sum(penalties.values()) if penalties else 0
            print(f'   {role:12}: {len(penalties):3} actions penalized, total penalty: {total_penalty:.2f}')
    else:
        print('   No agents with pariah awareness found')

    # 3. Check pariah toxicity after decay
    print('\n3. Checking pariah toxicity after decay...')
    pariahs = db.execute_query('SELECT pariah_id, toxicity FROM pariahs WHERE is_active = 1 LIMIT 5')
    if pariahs:
        for p in pariahs:
            print(f'   {p["pariah_id"][:25]:25} toxicity: {p["toxicity"]:.2f}')
    else:
        print('   No active pariahs found')

    # 4. Test network paralysis detection
    print('\n4. Testing network paralysis detection...')
    paralysis_boost = engine._detect_network_paralysis('lp85', 1)
    print(f'   lp85 level 1 paralysis boost: {paralysis_boost:.2f}')

    print('\n' + '=' * 60)
    print('PARIAH DECAY SYSTEM TEST COMPLETE')
    print('=' * 60)

if __name__ == '__main__':
    test_pariah_decay()
