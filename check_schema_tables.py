"""
Check if new tables exist in database and if they're in the schema file.
"""

import sqlite3

DB_PATH = "core_data.db"

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = [row[0] for row in cursor.fetchall()]

# Check for our new tables
new_tables = [
    "agent_performance_history",
    "sequence_validation_queue",
    "schema_versions",
    "scorecard_analysis_history",
    "analytics_snapshots",
]

print("🔍 Checking for new tables in database...")
print("=" * 70)

found_tables = []
missing_tables = []

for table in new_tables:
    if table in all_tables:
        found_tables.append(table)
        print(f"✅ {table} - EXISTS")
    else:
        missing_tables.append(table)
        print(f"❌ {table} - MISSING")

print("\n" + "=" * 70)
print(f"Found: {len(found_tables)}/{len(new_tables)}")
print(f"Missing: {len(missing_tables)}/{len(new_tables)}")

# Check schema file
print("\n🔍 Checking complete_database_schema.sql...")
print("=" * 70)

try:
    with open("complete_database_schema.sql", "r", encoding="utf-8") as f:
        schema_content = f.read()

    for table in new_tables:
        if (
            f"CREATE TABLE {table}" in schema_content
            or f"CREATE TABLE IF NOT EXISTS {table}" in schema_content
        ):
            print(f"✅ {table} - IN SCHEMA FILE")
        else:
            print(f"❌ {table} - NOT IN SCHEMA FILE")
except Exception as e:
    print(f"Error reading schema file: {e}")

conn.close()

print("\n" + "=" * 70)
print(f"Total tables in database: {len(all_tables)}")
