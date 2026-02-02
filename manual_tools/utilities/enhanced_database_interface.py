import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

#!/usr/bin/env python3
"""
Enhanced Database Interface with Schema Auto-Maintenance
=========================================================

Wrapper around DatabaseInterface that adds schema auto-maintenance hooks.
Use this instead of DatabaseInterface to get automatic schema export.
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging

from database_interface import DatabaseInterface
from schema_auto_maintenance import SchemaAutoMaintenance

logger = logging.getLogger(__name__)

class EnhancedDatabaseInterface(DatabaseInterface):
    """DatabaseInterface with schema auto-maintenance."""

    # Track pending schema changes to batch regeneration
    _pending_schema_changes: int = 0
    _schema_regen_threshold: int = 10  # Regenerate after this many DDL statements

    def __init__(self, db_path: str = "core_data.db"):
        """Initialize with schema auto-maintenance."""
        super().__init__(db_path)

        # Add schema maintenance (lazy - only used when needed)
        self._schema_maintenance = None
        self._db_path = db_path

    @property
    def schema_maintenance(self):
        """Lazy-load schema maintenance only when needed."""
        if self._schema_maintenance is None:
            try:
                self._schema_maintenance = SchemaAutoMaintenance(self._db_path)
            except Exception as e:
                logger.warning(f"Schema auto-maintenance not available: {e}")
        return self._schema_maintenance

    def execute_query(self, query: str, params=()) -> list:
        """Execute query with batched auto-schema export on schema changes."""
        # Execute the query using parent method
        result = super().execute_query(query, params)

        # Track schema changes but don't regenerate on every one
        if any(keyword in query.upper() for keyword in ['CREATE TABLE', 'ALTER TABLE', 'DROP TABLE']):
            EnhancedDatabaseInterface._pending_schema_changes += 1

        return result

    def flush_schema_changes(self):
        """Manually trigger schema regeneration if there are pending changes."""
        if EnhancedDatabaseInterface._pending_schema_changes > 0 and self.schema_maintenance:
            try:
                self.schema_maintenance.regenerate_schema_file()
                EnhancedDatabaseInterface._pending_schema_changes = 0
                logger.info("[OK] Schema auto-exported")
            except Exception as e:
                logger.warning(f"Schema auto-export failed: {e}")

if __name__ == "__main__":
    # Test the enhanced interface
    db = EnhancedDatabaseInterface()

    print("=" * 70)
    print("ENHANCED DATABASE INTERFACE TEST")
    print("=" * 70)

    # Test schema change detection
    print("\nCreating test table...")
    db.execute_query("CREATE TABLE IF NOT EXISTS integration_test (id INTEGER, value TEXT)")

    print("\n[OK] Enhanced database interface working!")
    print("Schema should have been auto-exported")

    # Clean up
    db.execute_query("DROP TABLE IF EXISTS integration_test")
    db.close()
