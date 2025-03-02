"""
Unified logging system for the Gesture-Voice Control application.

Provides centralized logging with:
- Structured logging via structlog
- Rich terminal output formatting
- Multiple output destinations (console, file, database)
- Log level configuration
- Context-aware logging
"""

import os
import sys
import enum
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

import structlog
from rich.console import Console
from rich.logging import RichHandler

# Assuming this is defined in your database module
from ..database.models import LogEntry
from ..utils.system.file_utils import ensure_directory_exists


class LogLevel(enum.Enum):
    """Enum representing different log levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


# Global context for structlog
_GLOBAL_LOGGER_CONTEXT = {}

# Default log paths
_DEFAULT_LOG_DIR = Path("logs")
_DEFAULT_LOG_FILE = _DEFAULT_LOG_DIR / "app.log"


def configure_logging(
    console_level: LogLevel = LogLevel.INFO,
    file_level: LogLevel = LogLevel.DEBUG,
    db_level: LogLevel = LogLevel.WARNING,
    log_file: Optional[Union[str, Path]] = None,
    db_enabled: bool = True,
    include_timestamps: bool = True
) -> None:
    """
    Configure the logging system for the application.
    
    Args:
        console_level: Minimum log level for console output
        file_level: Minimum log level for file output
        db_level: Minimum log level for database logging
        log_file: Path to log file (default: logs/app.log)
        db_enabled: Whether to enable database logging
        include_timestamps: Whether to include timestamps in console logs
    """
    # Ensure log directory exists
    log_file = Path(log_file) if log_file else _DEFAULT_LOG_FILE
    ensure_directory_exists(log_file.parent)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set up rich console handler
    console = Console()
    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        omit_repeated_times=False,
        show_time=include_timestamps,
        show_level=True,
        show_path=False,
    )
    rich_handler.setLevel(console_level.value)
    
    # Set up file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(file_level.value)
    
    from .formatters import (
        create_console_formatter,
        create_file_formatter,
        DatabaseLogProcessor
    )
    
    # Configure formatters
    rich_handler.setFormatter(create_console_formatter())
    file_handler.setFormatter(create_file_formatter())
    
    # Set up database logging if enabled
    handlers = [rich_handler, file_handler]
    processors = []
    
    if db_enabled:
        # Create a processor for database logging
        db_processor = DatabaseLogProcessor(min_level=db_level.value)
        processors.append(db_processor)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all logs, let handlers filter
    
    # Remove existing handlers to avoid duplicates when reconfiguring
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    
    # Add our handlers
    for handler in handlers:
        root_logger.addHandler(handler)


def get_logger(name: str, **context) -> structlog.stdlib.BoundLogger:
    """
    Get a logger for the specified module with optional context.
    
    Args:
        name: Name of the module (typically __name__)
        **context: Additional context to be included with all log entries
    
    Returns:
        A structlog bound logger instance
    """
    # Combine global and module-specific context
    combined_context = {**_GLOBAL_LOGGER_CONTEXT, **context}
    
    # Get a structlog logger
    logger = structlog.get_logger(name)
    
    # Bind the combined context
    if combined_context:
        logger = logger.bind(**combined_context)
    
    return logger


def add_global_context(**context) -> None:
    """
    Add context that will be included in all subsequent log entries.
    
    Args:
        **context: Context key-value pairs to add globally
    """
    global _GLOBAL_LOGGER_CONTEXT
    _GLOBAL_LOGGER_CONTEXT.update(context)


def clear_global_context(keys: Optional[List[str]] = None) -> None:
    """
    Clear global context keys. If no keys are provided, clear all global context.
    
    Args:
        keys: Optional list of context keys to clear
    """
    global _GLOBAL_LOGGER_CONTEXT
    
    if keys is None:
        _GLOBAL_LOGGER_CONTEXT.clear()
    else:
        for key in keys:
            _GLOBAL_LOGGER_CONTEXT.pop(key, None)


def log_to_database(
    level: LogLevel,
    message: str,
    logger_name: str,
    context: Dict[str, Any]
) -> None:
    """
    Store a log entry in the database.
    
    Args:
        level: Log level
        message: Log message
        logger_name: Name of the logger
        context: Additional context
    """
    try:
        # Import here to avoid circular imports
        from ..database.models import LogEntry
        from ..database import get_db_session
        
        with get_db_session() as session:
            log_entry = LogEntry(
                level=level.name,
                message=message,
                logger=logger_name,
                context=context
            )
            session.add(log_entry)
            session.commit()
    except Exception as e:
        # Use standard logging to avoid infinite recursion
        logging.error(f"Failed to save log to database: {e}")