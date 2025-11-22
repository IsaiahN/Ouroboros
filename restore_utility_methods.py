import os

file_path = r"C:\Users\Admin\Documents\GitHub\BitterTruth-AI\database_interface.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target_content = """    # General logging method
    def log_event(self, logger_name: str, level: str, message: str, **kwargs):"""

replacement_content = """    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def execute_query(self, query: str, params: tuple = ()) -> list:
        \"\"\"Execute a custom query.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of result dictionaries
        \"\"\"
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_database_stats(self) -> dict:
        \"\"\"Get database statistics.

        Returns:
            Dictionary containing database statistics
        \"\"\"
        with self._get_connection() as conn:
            stats = {}

            # Table counts
            tables = ['training_sessions', 'game_results', 'action_traces',
                     'action_effectiveness', 'score_history']

            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                except Exception:
                    stats[f"{table}_count"] = 0

            # Recent activity
            try:
                cursor = conn.execute(\"\"\"
                    SELECT COUNT(*) FROM training_sessions
                    WHERE start_time >= datetime('now', '-24 hours')
                \"\"\")
                stats['sessions_last_24h'] = cursor.fetchone()[0]

                cursor = conn.execute(\"\"\"
                    SELECT COUNT(*) FROM game_results
                    WHERE created_at >= datetime('now', '-24 hours')
                \"\"\")
                stats['games_last_24h'] = cursor.fetchone()[0]
            except Exception:
                pass

            return stats

    # General logging method
    def log_event(self, logger_name: str, level: str, message: str, **kwargs):"""

if target_content in content:
    new_content = content.replace(target_content, replacement_content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully restored utility methods to database_interface.py")
else:
    print("Target content not found in file.")
    print("Target start:", target_content[:50])
