#!/usr/bin/env python3
"""Quick bug check script."""
from database_interface import DatabaseInterface

db = DatabaseInterface()
bugs = db.execute_query("""
    SELECT bug_type, severity, status, occurrence_count 
    FROM oracle_reasoning_bugs WHERE status = 'open' 
    ORDER BY occurrence_count DESC LIMIT 10
""")

if bugs:
    print("OPEN BUGS:")
    print("-" * 60)
    for b in bugs:
        print(f"{b['severity']:8} | {b['bug_type']:30} | count={b['occurrence_count']}")
else:
    print("No open bugs")
