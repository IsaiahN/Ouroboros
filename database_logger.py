import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Database Logging Handler

Custom logging handler that stores all logs in the database instead of files.
Provides thread-safe logging with proper database connection management.
"""

import logging
import threading
import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

class DatabaseLogHandler(logging.Handler):
    """
    Custom logging handler that writes logs to SQLite database.

    This handler ensures all application logs are stored in the database
    rather than creating log files on disk.
    """

    def __init__(self, db_path: str = None, auto_cleanup: bool = True, cleanup_threshold: int = 100000):
        """
        Initialize the database logging handler.

        Args:
            db_path: Path to the SQLite database file
            auto_cleanup: Enable automatic log cleanup (default: True)
            cleanup_threshold: Number of logs before triggering cleanup (default: 100,000)
        """
        super().__init__()

        self.db_path = db_path or os.getenv('DATABASE_PATH', 'core_data.db')
        self._local = threading.local()
        self._lock = threading.Lock()
        
        # Auto-cleanup settings
        self.auto_cleanup = auto_cleanup
        self.cleanup_threshold = cleanup_threshold
        # FIX (2025-01-11): Increased from 5,000 to 50,000 logs
        # 5,000 was too aggressive - only covered 1-2 games of debugging
        # 50,000 gives ~20-30 games of history while still being small (~25 MB)
        # These are NOT used for reasoning, only for diagnostic debugging
        self.retention_keep = 50000
        self._log_count = 0
        self._last_cleanup_check = 0

        # Initialize database schema
        self._ensure_logs_table()

        # Current context for enhanced logging
        self.current_session_id: Optional[str] = None
        self.current_game_id: Optional[str] = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
            try:
                self._local.connection.execute("PRAGMA foreign_keys=ON")
                self._local.connection.execute("PRAGMA journal_mode=WAL")
                self._local.connection.execute("PRAGMA synchronous=NORMAL")
            except Exception:
                pass
        return self._local.connection

    def _ensure_logs_table(self):
        """Ensure the system_logs table exists."""
        try:
            self._initialize_database_from_template()
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    logger_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT,
                    function_name TEXT,
                    line_number INTEGER,
                    session_id TEXT,
                    game_id TEXT,
                    process_id INTEGER,
                    thread_id INTEGER,
                    extra_data TEXT
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp
                ON system_logs(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_logs_level
                ON system_logs(level)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_logs_logger_name
                ON system_logs(logger_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_logs_session_id
                ON system_logs(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_logs_game_id
                ON system_logs(game_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_logs_process_id
                ON system_logs(process_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_logs_thread_id
                ON system_logs(thread_id)
            """)

            conn.commit()

        except Exception as e:
            # Fallback to stderr if database logging fails during setup
            print(f"Warning: Failed to initialize database logging: {e}", file=__import__('sys').stderr)

            conn.commit()

        except Exception as e:
            # Fallback to stderr if database logging fails during setup
            print(f"Warning: Failed to initialize database logging: {e}", file=__import__('sys').stderr)

    def _initialize_database_from_template(self):
        """Initialize database from schema if it doesn't exist."""
        if not os.path.exists(self.db_path):
            self._create_database_from_schema()

    def _create_database_from_schema(self):
        """Create database using the schema file."""
        from pathlib import Path

        schema_path = Path(__file__).parent / "complete_database_schema.sql"

        if not os.path.exists(schema_path):
            return  # Gracefully handle missing schema, logs table will be created below

        try:
            conn = self._get_connection()
            with open(schema_path, 'r') as f:
                schema = f.read()
            conn.executescript(schema)
            conn.commit()
        except Exception as e:
            # If schema execution fails, continue with table creation below
            pass

    def set_context(self, session_id: str = None, game_id: str = None):
        """Set current session and game context for enhanced logging."""
        self.current_session_id = session_id
        self.current_game_id = game_id

    def emit(self, record: logging.LogRecord):
        """
        Emit a log record to the database.

        Args:
            record: The LogRecord to emit
        """
        try:
            # Format the message
            message = self.format(record)

            # Extract additional context
            extra_data = {}
            if hasattr(record, '__dict__'):
                # Store any extra fields that were added to the log record
                standard_fields = {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'lineno', 'funcName', 'created',
                    'msecs', 'relativeCreated', 'thread', 'threadName',
                    'processName', 'process', 'getMessage', 'exc_info',
                    'exc_text', 'stack_info'
                }
                for key, value in record.__dict__.items():
                    if key not in standard_fields and not key.startswith('_'):
                        extra_data[key] = str(value)

            # Prepare log entry
            timestamp = datetime.fromtimestamp(record.created).isoformat()

            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO system_logs (
                        timestamp, level, logger_name, message, module,
                        function_name, line_number, session_id, game_id,
                        process_id, thread_id, extra_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    record.levelname,
                    record.name,
                    message,
                    record.module if hasattr(record, 'module') else record.filename,
                    record.funcName,
                    record.lineno,
                    self.current_session_id,
                    self.current_game_id,
                    record.process,
                    record.thread,
                    json.dumps(extra_data) if extra_data else None
                ))

                conn.commit()

        except Exception as e:
            # If database logging fails, fall back to stderr
            # but don't raise an exception to avoid breaking the application
            try:
                import sys
                error_msg = f"Database logging error: {e}\nOriginal message: {record.getMessage()}"
                print(error_msg, file=sys.stderr)
            except:
                pass  # If even stderr fails, silently continue
        
        # Auto-cleanup check (every 1000 logs)
        if self.auto_cleanup:
            self._log_count += 1
            if self._log_count - self._last_cleanup_check >= 1000:
                self._last_cleanup_check = self._log_count
                self._check_and_cleanup()
    
    def _check_and_cleanup(self):
        """Check log count and cleanup if threshold exceeded."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM system_logs")
            row = cursor.fetchone()
            total_logs = row[0] if row else 0
            
            if total_logs > self.retention_keep:
                # Delete oldest logs, keep most recent retention_keep
                cursor.execute(
                    """
                    DELETE FROM system_logs
                    WHERE id NOT IN (
                        SELECT id FROM system_logs
                        ORDER BY id DESC
                        LIMIT ?
                    )
                    """,
                    (self.retention_keep,)
                )
                conn.commit()
                cursor.execute("SELECT COUNT(*) as count FROM system_logs")
                row = cursor.fetchone()
                new_count = row[0] if row else 0
                print(f"[DatabaseLogHandler] Auto-cleanup: {total_logs:,} → {new_count:,} logs",
                      file=__import__('sys').stderr)
                
        except Exception as e:
            # Silently fail - cleanup is not critical
            pass

    def close(self):
        """Close the handler and clean up resources."""
        if hasattr(self._local, 'connection'):
            try:
                self._local.connection.close()
            except:
                pass
        super().close()


def setup_database_logging(
    level: str = None,
    db_path: str = None,
    logger_name: str = None
) -> DatabaseLogHandler:
    """
    Set up database logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        db_path: Path to database file
        logger_name: Name of logger to configure (None for root logger)

    Returns:
        DatabaseLogHandler instance
    """
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Determine logging level
    if not level:
        level = os.getenv('LOG_LEVEL', 'INFO')

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create database handler
    db_handler = DatabaseLogHandler(db_path)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    db_handler.setFormatter(formatter)
    db_handler.setLevel(log_level)

    # Configure logger
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger()

    # Remove any existing handlers (especially file handlers)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add database handler
    logger.addHandler(db_handler)
    logger.setLevel(log_level)

    # Also add console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    return db_handler


def get_recent_logs(
    db_path: str = None,
    limit: int = 100,
    level: str = None,
    session_id: str = None,
    game_id: str = None
) -> list:
    """
    Retrieve recent logs from the database.

    Args:
        db_path: Path to database file
        limit: Maximum number of logs to retrieve
        level: Filter by log level
        session_id: Filter by session ID
        game_id: Filter by game ID

    Returns:
        List of log entries
    """
    if not db_path:
        db_path = os.getenv('DATABASE_PATH', 'core_data.db')

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query
        conditions = []
        params = []

        if level:
            conditions.append("level = ?")
            params.append(level.upper())

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        if game_id:
            conditions.append("game_id = ?")
            params.append(game_id)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT * FROM system_logs
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)

        cursor.execute(query, params)
        logs = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return logs

    except Exception as e:
        print(f"Error retrieving logs: {e}")
        return []


# Convenience function for quick setup
def init_logging(level: str = None, db_path: str = None) -> DatabaseLogHandler:
    """Initialize database logging with default settings."""
    return setup_database_logging(level=level, db_path=db_path)