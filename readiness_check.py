#!/usr/bin/env python3
"""
Phase 4 Readiness Assessment - Check Level 4 Achievement Indicators
"""

from database_interface import DatabaseInterface

def assess_phase4_readiness():
    db = DatabaseInterface()
    
    print('=' * 80)
    print('PHASE 4 READINESS ASSESSMENT')
    print('=' * 80)
    print('Checking Level 4 Achievement Indicators from Roadmap...')
    print()
    
    indicators = {}
    
    # 1. Network knowledge diversity index > 3.0 (Shannon entropy)
    try:
        diversity_result = db.execute_query('''
            SELECT knowledge_diversity_index 
            FROM ecosystem_health_snapshots 
            ORDER BY generation DESC LIMIT 1
        ''')
        diversity = diversity_result[0]['knowledge_diversity_index'] if diversity_result else 0
        indicators['diversity'] = {'value': diversity, 'target': 3.0, 'met': diversity > 3.0}
        status = "✅" if diversity > 3.0 else "❌"
        print(f'1. Knowledge diversity index: {diversity:.3f} (target: >3.0) {status}')
    except Exception as e:
        indicators['diversity'] = {'value': 0, 'target': 3.0, 'met': False}
        print(f'1. Knowledge diversity index: Error - {e}')
    
    # 2. Knowledge redundancy index > 2.0 (average backups per sequence)
    try:
        redundancy_result = db.execute_query('''
            SELECT redundancy_index 
            FROM ecosystem_health_snapshots 
            ORDER BY generation DESC LIMIT 1
        ''')
        redundancy = redundancy_result[0]['redundancy_index'] if redundancy_result else 0
        indicators['redundancy'] = {'value': redundancy, 'target': 2.0, 'met': redundancy > 2.0}
        status = "✅" if redundancy > 2.0 else "❌"
        print(f'2. Knowledge redundancy index: {redundancy:.3f} (target: >2.0) {status}')
    except Exception as e:
        indicators['redundancy'] = {'value': 0, 'target': 2.0, 'met': False}
        print(f'2. Knowledge redundancy index: Error - {e}')
    
    # 3. Network metabolism efficiency > 0.05
    try:
        perf_result = db.execute_query('''
            SELECT AVG(CAST(total_score AS REAL) / NULLIF(total_actions_taken, 0)) as avg_efficiency
            FROM agent_arc_performance 
            WHERE total_actions_taken > 0
        ''')
        metabolism = perf_result[0]['avg_efficiency'] if perf_result and perf_result[0]['avg_efficiency'] else 0
        indicators['metabolism'] = {'value': metabolism, 'target': 0.05, 'met': metabolism > 0.05}
        status = "✅" if metabolism > 0.05 else "❌"
        print(f'3. Network metabolism efficiency: {metabolism:.4f} (target: >0.05) {status}')
    except Exception as e:
        indicators['metabolism'] = {'value': 0, 'target': 0.05, 'met': False}
        print(f'3. Network metabolism efficiency: Error - {e}')
    
    # 4. Top 20% agents contribute 60%+ of network enrichment
    try:
        total_agents_result = db.execute_query('SELECT COUNT(*) FROM agents WHERE is_active = TRUE')
        total_agents = total_agents_result[0]['COUNT(*)'] if total_agents_result else 0
        
        if total_agents > 0:
            top_20_pct = max(1, int(total_agents * 0.2))
            
            top_prestige_result = db.execute_query(f'''
                SELECT SUM(discovery_prestige) as top_prestige 
                FROM (
                    SELECT discovery_prestige 
                    FROM agents 
                    WHERE is_active = TRUE 
                    ORDER BY discovery_prestige DESC 
                    LIMIT {top_20_pct}
                )
            ''')
            
            total_prestige_result = db.execute_query('''
                SELECT SUM(discovery_prestige) as total 
                FROM agents 
                WHERE is_active = TRUE
            ''')
            
            if (top_prestige_result and total_prestige_result and 
                total_prestige_result[0]['total'] and total_prestige_result[0]['total'] > 0):
                
                contribution_pct = (top_prestige_result[0]['top_prestige'] / 
                                   total_prestige_result[0]['total']) * 100
                indicators['contribution'] = {'value': contribution_pct, 'target': 60.0, 'met': contribution_pct >= 60.0}
                status = "✅" if contribution_pct >= 60.0 else "❌"
                print(f'4. Top 20% network contribution: {contribution_pct:.1f}% (target: ≥60%) {status}')
            else:
                indicators['contribution'] = {'value': 0, 'target': 60.0, 'met': False}
                print('4. Top 20% network contribution: No prestige data ❌')
        else:
            indicators['contribution'] = {'value': 0, 'target': 60.0, 'met': False}
            print('4. Top 20% network contribution: No agents ❌')
    except Exception as e:
        indicators['contribution'] = {'value': 0, 'target': 60.0, 'met': False}
        print(f'4. Top 20% network contribution: Error - {e}')
    
    # 5. At least 10 distinct viral packages propagating
    try:
        vp_result = db.execute_query('SELECT COUNT(*) FROM viral_information_packages')
        vp_count = vp_result[0]['COUNT(*)'] if vp_result else 0
        indicators['viral_packages'] = {'value': vp_count, 'target': 10, 'met': vp_count >= 10}
        status = "✅" if vp_count >= 10 else "❌"
        print(f'5. Viral packages: {vp_count} (target: ≥10) {status}')
    except Exception as e:
        indicators['viral_packages'] = {'value': 0, 'target': 10, 'met': False}
        print(f'5. Viral packages: Error - {e}')
    
    # 6. Viral package infection rate > 60%
    try:
        total_agents_result = db.execute_query('SELECT COUNT(*) FROM agents WHERE is_active = TRUE')
        total_agents = total_agents_result[0]['COUNT(*)'] if total_agents_result else 0
        
        if total_agents > 0:
            infection_result = db.execute_query('SELECT COUNT(DISTINCT agent_id) FROM agent_viral_infections')
            infection_count = infection_result[0]['COUNT(DISTINCT agent_id)'] if infection_result else 0
            infection_rate = (infection_count / total_agents) * 100
            indicators['infection_rate'] = {'value': infection_rate, 'target': 60.0, 'met': infection_rate > 60.0}
            status = "✅" if infection_rate > 60.0 else "❌"
            print(f'6. Viral infection rate: {infection_rate:.1f}% (target: >60%) {status}')
        else:
            indicators['infection_rate'] = {'value': 0, 'target': 60.0, 'met': False}
            print('6. Viral infection rate: No agents ❌')
    except Exception as e:
        indicators['infection_rate'] = {'value': 0, 'target': 60.0, 'met': False}
        print(f'6. Viral infection rate: Error - {e}')
    
    # 7. At least 5 distinct failure patterns (pariahs) identified
    try:
        pariah_result = db.execute_query('SELECT COUNT(*) FROM pariahs')
        pariah_count = pariah_result[0]['COUNT(*)'] if pariah_result else 0
        indicators['pariahs'] = {'value': pariah_count, 'target': 5, 'met': pariah_count >= 5}
        status = "✅" if pariah_count >= 5 else "❌"
        print(f'7. Pariahs (failure patterns): {pariah_count} (target: ≥5) {status}')
    except Exception as e:
        indicators['pariahs'] = {'value': 0, 'target': 5, 'met': False}
        print(f'7. Pariahs: Error - {e}')
    
    # 8. Pariah awareness rate > 50%
    try:
        if total_agents > 0:
            awareness_result = db.execute_query('SELECT COUNT(DISTINCT agent_id) FROM agent_pariah_awareness')
            awareness_count = awareness_result[0]['COUNT(DISTINCT agent_id)'] if awareness_result else 0
            awareness_rate = (awareness_count / total_agents) * 100
            indicators['pariah_awareness'] = {'value': awareness_rate, 'target': 50.0, 'met': awareness_rate > 50.0}
            status = "✅" if awareness_rate > 50.0 else "❌"
            print(f'8. Pariah awareness rate: {awareness_rate:.1f}% (target: >50%) {status}')
        else:
            indicators['pariah_awareness'] = {'value': 0, 'target': 50.0, 'met': False}
            print('8. Pariah awareness rate: No agents ❌')
    except Exception as e:
        indicators['pariah_awareness'] = {'value': 0, 'target': 50.0, 'met': False}
        print(f'8. Pariah awareness rate: Error - {e}')
    
    # Calculate overall readiness score
    met_indicators = sum(1 for i in indicators.values() if i['met'])
    total_indicators = len(indicators)
    readiness_score = (met_indicators / total_indicators) * 100
    
    print()
    print('=' * 80)
    print(f'PHASE 4 READINESS SCORE: {readiness_score:.1f}% ({met_indicators}/{total_indicators} indicators met)')
    print('=' * 80)
    
    if readiness_score >= 80:
        print('🚀 READY FOR PHASE 4 IMPLEMENTATION!')
        print('   All critical systems operational, metrics meet thresholds')
        recommendation = "PROCEED"
    elif readiness_score >= 60:
        print('⚠️  MOSTLY READY - Consider Phase 4 implementation')
        print('   Core systems working, some metrics need improvement')
        recommendation = "PROCEED_WITH_CAUTION"
    else:
        print('❌ NOT READY for Phase 4')
        print('   Need more evolution cycles to improve metrics')
        recommendation = "WAIT"
    
    print()
    print('ANALYSIS:')
    
    # Show what's working
    working_systems = [name for name, data in indicators.items() if data['met']]
    if working_systems:
        print(f'✅ Working systems: {", ".join(working_systems)}')
    
    # Show what needs work
    needs_work = [name for name, data in indicators.items() if not data['met']]
    if needs_work:
        print(f'❌ Needs improvement: {", ".join(needs_work)}')
    
    print()
    print('RECOMMENDATION:', recommendation)
    
    return recommendation, readiness_score, indicators

if __name__ == '__main__':
    assess_phase4_readiness()