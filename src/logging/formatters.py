"""
Custom log formatters for the Gesture-Voice Control application.

Provides formatters for different logging outputs:
- Rich console output with color and formatting
- File output with detailed structured information
- Database logging processor
"""

import json
import logging
import datetime
from typing import Any, Dict, List, Optional
import sys
import structlog
from rich.logging import RichHandler


def create_console_formatter() -> logging.Formatter:
    """
    Create a formatter for console output using Rich formatting.
    
    Returns:
        Configured formatter for console output
    """
    return logging.Formatter("%(message)s")


def create_file_formatter() -> logging.Formatter:
    """
    Create a formatter for file output with detailed information.
    
    Returns:
        Configured formatter for file output
    """
    return logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s - %(context)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with context support."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with additional context.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted log string
        """
        # Get the regular formatted message
        message = super().format(record)
        
        # Add context information if available
        if hasattr(record, "_context"):
            context_str = " ".join(f"{k}={v}" for k, v in record._context.items())
            if context_str:
                message = f"{message} - {context_str}"
                
        return message


class DatabaseLogProcessor:
    """
    Structlog processor that stores log entries in the database.
    
    Stores logs of sufficient severity level in the database
    while allowing the log event to continue through the processor chain.
    """
    
    def __init__(self, min_level: int = logging.WARNING):
        """
        Initialize the database log processor.
        
        Args:
            min_level: Minimum log level to store in database
        """
        self.min_level = min_level
    
    def __call__(
        self, 
        logger: str, 
        level: str, 
        event_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process the log event and store in database if level is sufficient.
        
        Args:
            logger: Logger name
            level: Log level name
            event_dict: Log event dictionary
            
        Returns:
            Unmodified event dictionary to continue processing
        """
        numeric_level = getattr(logging, level.upper(), logging.NOTSET)
        
        if numeric_level >= self.min_level:
            try:
                # Extract basic log information
                message = event_dict.get("event", "")
                
                # Create a copy of the event dict for context
                context = event_dict.copy()
                
                # Remove standard keys for cleaner context
                for key in ["event", "level", "logger", "timestamp"]:
                    context.pop(key, None)
                
                # Log to database without blocking the logging flow
                self._log_to_database_async(numeric_level, level, message, logger, context)
            except Exception as e:
                # Use standard logging to avoid infinite recursion
                logging.error(f"Failed to process database log: {e}")
        
        # Return unmodified event dict to continue with other processors
        return event_dict
    
    def _log_to_database_async(
        self, 
        numeric_level: int,
        level_name: str,
        message: str, 
        logger: str, 
        context: Dict[str, Any]
    ) -> None:
        """
        Store log in database asynchronously.
        
        Args:
            numeric_level: Numeric log level
            level_name: String log level name
            message: Log message
            logger: Logger name
            context: Log context dictionary
        """
        try:
            from ..database.models import LogEntry
            from ..database import get_db_session
            
            # Serialize complex objects in context
            serialized_context = {}
            for key, value in context.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    serialized_context[key] = value
                else:
                    try:
                        # Try to convert to string representation
                        serialized_context[key] = str(value)
                    except Exception:
                        serialized_context[key] = "<non-serializable>"
            
            # Get database session and create log entry
            with get_db_session() as session:
                log_entry = LogEntry(
                    timestamp=datetime.datetime.now(),
                    level=level_name,
                    message=message,
                    logger=logger,
                    context=json.dumps(serialized_context)
                )
                session.add(log_entry)
                session.commit()
        except Exception as e:
            # Use standard logging to avoid infinite recursion
            logging.error(f"Failed to save log to database: {e}")


class ColorFormatter(logging.Formatter):
    """
    Custom formatter that adds color coding to console logs based on level.
    Used as a fallback when Rich formatting is disabled.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[94m',     # Blue
        'INFO': '\033[92m',      # Green
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[91m\033[1m',  # Bold Red
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with color coding.
        
        Args:
            record: Log record to format
            
        Returns:
            Color-formatted log message
        """
        # Check if terminal supports colors
        use_colors = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        
        level_name = record.levelname
        msg = super().format(record)
        
        if use_colors and level_name in self.COLORS:
            return f"{self.COLORS[level_name]}{msg}{self.COLORS['RESET']}"
        else:
            return msg