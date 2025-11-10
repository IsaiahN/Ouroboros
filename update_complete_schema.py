#!/usr/bin/env python3
"""
Generate complete database schema from current database state
"""

import os
import sys
from pathlib import Path

# Critical: Prevent .pyc file generation per Copilot Instructions Rule 1
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from database_interface import DatabaseInterface

def get_table_schema(db, table_name):
    """Get CREATE TABLE statement for a table."""
    
    try:
        # Get the CREATE TABLE statement
        result = db.execute_query(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        
        if result and result[0]['sql']:
            return result[0]['sql']
        else:
            return None
            
    except Exception as e:
        print(f"Error getting schema for {table_name}: {e}")
        return None

def main():
    """Generate complete database schema from current state."""
    
    print("🗄️ GENERATING COMPLETE DATABASE SCHEMA FROM CURRENT STATE")
    print("=" * 70)
    
    db = DatabaseInterface()
    
    # Get all tables
    tables_result = db.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    
    if not tables_result:
        print("❌ No tables found!")
        return
    
    print(f"📋 Found {len(tables_result)} tables")
    
    # Group tables by category for organization
    core_tables = []
    ouroboros_tables = []
    phase_tables = []
    
    for table in tables_result:
        table_name = table['name']
        
        if any(x in table_name for x in ['training_sessions', 'game_results', 'action_traces', 'score_history', 'global_counters', 'system_logs']):
            core_tables.append(table_name)
        elif any(x in table_name for x in ['agents', 'claude_', 'population_health', 'arc_action_tracking']):
            ouroboros_tables.append(table_name)
        else:
            phase_tables.append(table_name)
    
    schema_content = """-- ============================================================================
-- COMPLETE BITTERTRUTH-AI DATABASE SCHEMA (UPDATED)
-- Generated from current database state including all Phase implementations
-- Following Rule 2: Database-Only Storage - All data in SQLite
-- ============================================================================

-- ============================================================================
-- CORE GAME MECHANICS TABLES
-- ============================================================================

"""
    
    # Add core tables
    for table_name in core_tables:
        schema = get_table_schema(db, table_name)
        if schema:
            schema_content += f"-- {table_name}\n{schema};\n\n"
    
    schema_content += """-- ============================================================================
-- OUROBOROS EVOLUTIONARY FRAMEWORK TABLES
-- ============================================================================

"""
    
    # Add ouroboros tables
    for table_name in ouroboros_tables:
        schema = get_table_schema(db, table_name)
        if schema:
            schema_content += f"-- {table_name}\n{schema};\n\n"
    
    schema_content += """-- ============================================================================
-- PHASE IMPLEMENTATION TABLES
-- (Phases 0-5: Network Intelligence, Prestige, Economy, Recombination,
--  Viral Packages, Distributed Regulation, Sensation System, Horizontal Transfer)
-- ============================================================================

"""
    
    # Add phase tables
    for table_name in sorted(phase_tables):
        schema = get_table_schema(db, table_name)
        if schema:
            schema_content += f"-- {table_name}\n{schema};\n\n"
    
    # Get all indexes
    indexes_result = db.execute_query(
        "SELECT sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL ORDER BY name"
    )
    
    if indexes_result:
        schema_content += """-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

"""
        for index in indexes_result:
            if index['sql']:
                schema_content += f"{index['sql']};\n"
    
    # Write to file
    with open('complete_database_schema.sql', 'w', encoding='utf-8') as f:
        f.write(schema_content)
    
    print("✅ Updated complete_database_schema.sql with current state")
    print(f"   - {len(core_tables)} core tables")
    print(f"   - {len(ouroboros_tables)} ouroboros tables") 
    print(f"   - {len(phase_tables)} phase tables")
    print(f"   - {len(indexes_result)} indexes")
    
    # Show key new tables
    print("\n🆕 KEY PHASE TABLES INCLUDED:")
    key_phase_tables = [
        'sensation_learning_events', 'network_regulatory_signals', 
        'horizontal_transfer_events', 'viral_information_packages',
        'pariahs', 'agent_signal_responses', 'sequence_dependencies'
    ]
    
    for table in key_phase_tables:
        if table in [t['name'] for t in tables_result]:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} (missing)")

if __name__ == "__main__":
    main()