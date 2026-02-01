import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Engine Logger - Unified Logging for All Engines
================================================

Provides consistent logging across all engine modules:
- Auto-tags with engine name
- Outputs to BOTH console AND database (Rule 2)
- Structured context support for debugging
- No Unicode emojis (Rule 11)

Usage:
    from engines.engine_logger import get_engine_logger
    
    logger = get_engine_logger("viral_package")
    logger.info("Package created", package_id=pkg_id)
    logger.error("Failed to create package", exc=e, game_id=game_id)
    
Console output:
    [viral_package:INFO] Package created
    [viral_package:ERROR] Failed to create package

Database storage:
    All logs stored in system_logs table with structured context
"""

import logging
import sys
import json
import traceback
import threading
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from database_interface import DatabaseInterface


# Cache for engine loggers (one per engine name)
_engine_loggers: Dict[str, 'EngineLogger'] = {}
_logger_lock = threading.Lock()

# Global database reference (set during initialization)
_global_db: Optional['DatabaseInterface'] = None


def set_global_db(db: 'DatabaseInterface') -> None:
    """Set the global database interface for all engine loggers."""
    global _global_db
    _global_db = db


def get_engine_logger(engine_name: str) -> 'EngineLogger':
    """
    Get or create a logger for the specified engine.
    
    Args:
        engine_name: Short name like "viral_package", "cods", "registry"
        
    Returns:
        EngineLogger instance for that engine
    """
    with _logger_lock:
        if engine_name not in _engine_loggers:
            _engine_loggers[engine_name] = EngineLogger(engine_name)
        return _engine_loggers[engine_name]


class EngineLogFormatter(logging.Formatter):
    """Custom formatter that adds engine name prefix."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Get engine name from record (set by EngineLogger)
        engine = getattr(record, 'engine_name', 'unknown')
        level = record.levelname
        
        # Format: [engine:LEVEL] message
        prefix = f"[{engine}:{level}]"
        
        # Add context if present
        context = getattr(record, 'context', None)
        if context:
            context_str = ' '.join(f"{k}={v}" for k, v in context.items())
            return f"{prefix} {record.getMessage()} | {context_str}"
        
        return f"{prefix} {record.getMessage()}"


class DatabaseLogHandler(logging.Handler):
    """Handler that writes logs to the database."""
    
    def __init__(self):
        super().__init__()
        self._local = threading.local()
    
    def emit(self, record: logging.LogRecord) -> None:
        """Write log record to database."""
        global _global_db
        
        if _global_db is None:
            return  # No database configured yet
        
        try:
            engine_name = getattr(record, 'engine_name', 'unknown')
            context = getattr(record, 'context', {})
            exc_info = getattr(record, 'exc_text', None)
            
            # Build log entry
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'level': record.levelname,
                'logger_name': f"engine.{engine_name}",
                'message': record.getMessage(),
                'module': record.module,
                'function_name': record.funcName,
                'line_number': record.lineno,
                'extra_data': json.dumps(context) if context else None,
            }
            
            if exc_info:
                log_data['extra_data'] = json.dumps({
                    **(context or {}),
                    'traceback': exc_info
                })
            
            # Insert into system_logs
            _global_db.execute("""
                INSERT INTO system_logs (
                    timestamp, level, logger_name, message,
                    module, function_name, line_number, extra_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_data['timestamp'],
                log_data['level'],
                log_data['logger_name'],
                log_data['message'],
                log_data['module'],
                log_data['function_name'],
                log_data['line_number'],
                log_data.get('extra_data'),
            ))
        except Exception:
            # Never fail on logging - just skip database write
            pass


class EngineLogger:
    """
    Logger for engine modules with console + database output.
    
    Provides a simple API for logging with structured context:
        logger.info("message", key=value, key2=value2)
        logger.error("message", exc=exception, key=value)
    """
    
    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        
        # Create Python logger
        self._logger = logging.getLogger(f"engine.{engine_name}")
        self._logger.setLevel(logging.DEBUG)
        
        # Avoid duplicate handlers
        if not self._logger.handlers:
            # Console handler
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(logging.INFO)
            console.setFormatter(EngineLogFormatter())
            self._logger.addHandler(console)
            
            # Database handler
            db_handler = DatabaseLogHandler()
            db_handler.setLevel(logging.DEBUG)
            self._logger.addHandler(db_handler)
        
        # Don't propagate to root logger
        self._logger.propagate = False
    
    def _log(
        self,
        level: int,
        msg: str,
        exc: Optional[Exception] = None,
        **context: Any
    ) -> None:
        """Internal log method with context support."""
        # Create log record with extra attributes
        extra = {
            'engine_name': self.engine_name,
            'context': context if context else None,
        }
        
        # Handle exception
        exc_info = None
        if exc is not None:
            exc_info = True
            extra['context'] = extra.get('context') or {}
            extra['context']['error_type'] = type(exc).__name__
            extra['context']['error_msg'] = str(exc)
        
        self._logger.log(level, msg, exc_info=exc_info, extra=extra)
    
    def debug(self, msg: str, **context: Any) -> None:
        """Log debug message (database only by default)."""
        self._log(logging.DEBUG, msg, **context)
    
    def info(self, msg: str, **context: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, msg, **context)
    
    def warning(self, msg: str, exc: Optional[Exception] = None, **context: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, msg, exc=exc, **context)
    
    def warn(self, msg: str, exc: Optional[Exception] = None, **context: Any) -> None:
        """Alias for warning()."""
        self.warning(msg, exc=exc, **context)
    
    def error(self, msg: str, exc: Optional[Exception] = None, **context: Any) -> None:
        """Log error message with optional exception."""
        self._log(logging.ERROR, msg, exc=exc, **context)
    
    def critical(self, msg: str, exc: Optional[Exception] = None, **context: Any) -> None:
        """Log critical error."""
        self._log(logging.CRITICAL, msg, exc=exc, **context)


# =============================================================================
# Convenience Functions
# =============================================================================

def log_import_error(engine_name: str, module_path: str, error: Exception) -> None:
    """Log an import error when loading an engine module."""
    logger = get_engine_logger("registry")
    logger.warning(
        f"Failed to import {engine_name}",
        module=module_path,
        error_type=type(error).__name__,
        error_msg=str(error)
    )


def log_engine_init(engine_name: str, success: bool, error: Optional[Exception] = None) -> None:
    """Log engine initialization result."""
    logger = get_engine_logger(engine_name)
    if success:
        logger.debug(f"Engine initialized successfully")
    else:
        logger.error(f"Engine initialization failed", exc=error)


def log_silent_failure(
    engine_name: str,
    operation: str,
    error: Exception,
    **context: Any
) -> None:
    """
    Log what would have been a silent failure.
    
    Use this to replace `except: pass` blocks:
    
    Before:
        except Exception:
            pass
    
    After:
        except Exception as e:
            log_silent_failure("viral_package", "create_package", e, game_id=gid)
    """
    logger = get_engine_logger(engine_name)
    logger.warning(f"Silent failure in {operation}", exc=error, **context)
