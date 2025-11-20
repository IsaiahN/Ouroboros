#!/usr/bin/env python3
"""
Enhanced Database Interface with Schema Auto-Maintenance
=========================================================

Wrapper around DatabaseInterface that adds schema auto-maintenance hooks.
Use this instead of DatabaseInterface to get automatic schema export.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from schema_auto_maintenance import SchemaAutoMaintenance
import logging

logger = logging.getLogger(__name__)

class EnhancedDatabaseInterface(DatabaseInterface):
    """DatabaseInterface with schema auto-maintenance."""
    
    def __init__(self, db_path: str = "core_data.db"):
        """Initialize with schema auto-maintenance."""
        super().__init__(db_path)
        
        # Add schema maintenance
        try:
            self.schema_maintenance = SchemaAutoMaintenance(db_path)
            logger.info("Schema auto-maintenance enabled")
        except Exception as e:
            logger.warning(f"Schema auto-maintenance not available: {e}")
            self.schema_maintenance = None
    
    def execute_query(self, query: str, params=()) -> list:
        """Execute query with auto-schema export on schema changes."""
        # Execute the query using parent method
        result = super().execute_query(query, params)
        
        # Auto-export schema if this was a schema change
        if self.schema_maintenance and any(keyword in query.upper() for keyword in ['CREATE TABLE', 'ALTER TABLE', 'DROP TABLE']):
            try:
                self.schema_maintenance.regenerate_schema_file()
                logger.info("✓ Schema auto-exported after schema change")
            except Exception as e:
                logger.warning(f"Schema auto-export failed: {e}")
        
        return result

if __name__ == "__main__":
    # Test the enhanced interface
    db = EnhancedDatabaseInterface()
    
    print("=" * 70)
    print("ENHANCED DATABASE INTERFACE TEST")
    print("=" * 70)
    
    # Test schema change detection
    print("\nCreating test table...")
    db.execute_query("CREATE TABLE IF NOT EXISTS integration_test (id INTEGER, value TEXT)")
    
    print("\n✅ Enhanced database interface working!")
    print("Schema should have been auto-exported")
    
    # Clean up
    db.execute_query("DROP TABLE IF EXISTS integration_test")
    db.close()
