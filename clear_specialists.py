"""
Clear all specialist assignments from database.
Specialist system replaced by prestige + operating modes.
"""

from database_interface import DatabaseInterface

db = DatabaseInterface()

# Clear all specialist assignments (set to empty JSON since NULL not allowed)
print("Clearing specialist assignments...")
db.execute_query("UPDATE agents SET specialization = '{}' WHERE specialization IS NOT NULL AND specialization != '{}'")

# Verify
result = db.execute_query("SELECT COUNT(*) as cleared FROM agents WHERE specialization = '{}'")
total = db.execute_query("SELECT COUNT(*) as total FROM agents")
still_specialists = db.execute_query("SELECT COUNT(*) as remaining FROM agents WHERE specialization != '{}'")

print(f"✓ Cleared specialist assignments")
print(f"  Total agents: {total[0]['total']}")
print(f"  Non-specialists (empty): {result[0]['cleared']}")
print(f"  Remaining specialists: {still_specialists[0]['remaining']}")
print()
print("Specialist system disabled - natural selection restored!")
print("- Prestige provides earned survival protection (0-80%)")
print("- Operating modes guide mutation (pioneer 5x, optimizer 0.5x, generalist 1x)")
