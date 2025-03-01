"""
Database module for the Gesture & Voice Controlled AI Assistant

This module provides database connectivity, models, and storage interfaces
for persistence of users, intents, logs, and system settings.
"""

import logging
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Initialize logger
logger = logging.getLogger(__name__)

# Create SQLAlchemy base class for models
Base = declarative_base()

# Default paths
ROOT_DIR = Path(__file__).parent.parent.parent
DEFAULT_DB_PATH = os.path.join(ROOT_DIR, 'db')

# Database connection singleton
class DatabaseManager:
    """
    Manages database connections and provides session factory for
    all database operations.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path=None, echo=False):
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__ + ".DatabaseManager")
        
        # Configure database paths
        if db_path is None:
            db_path = DEFAULT_DB_PATH
            
        # Ensure the directory exists
        os.makedirs(db_path, exist_ok=True)
        
        # Create connections to the different databases
        auth_db_path = os.path.join(db_path, 'auth.db')
        logs_db_path = os.path.join(db_path, 'logs.db')
        
        # Create engines
        self.auth_engine = create_engine(f'sqlite:///{auth_db_path}', echo=echo)
        self.logs_engine = create_engine(f'sqlite:///{logs_db_path}', echo=echo)
        
        # Create session factories
        self.auth_session_factory = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.auth_engine)
        )
        
        self.logs_session_factory = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.logs_engine)
        )
        
        self._initialized = True
        self.logger.info("Database manager initialized")
    
    def create_all_tables(self):
        """Create all tables defined in the models."""
        from .models import User, Role, Permission, UserRole  # Import here to avoid circular imports
        
        self.logger.info("Creating database tables...")
        Base.metadata.create_all(self.auth_engine)
        self.logger.info("Auth database tables created")
        
        # Import and create logs tables
        from .models import LogEntry, SystemEvent
        Base.metadata.create_all(self.logs_engine)
        self.logger.info("Logs database tables created")
        
        return True
    
    def get_auth_session(self):
        """Get a session for auth database operations."""
        return self.auth_session_factory()
    
    def get_logs_session(self):
        """Get a session for logs database operations."""
        return self.logs_session_factory()
    
    def close_all_sessions(self):
        """Close all active sessions."""
        self.auth_session_factory.remove()
        self.logs_session_factory.remove()
        self.logger.debug("All database sessions closed")

# Export convenience functions
def get_db_manager(db_path=None, echo=False):
    """Get the database manager singleton instance."""
    return DatabaseManager(db_path, echo)

def init_db(db_path=None):
    """Initialize the database, creating all tables."""
    db_manager = get_db_manager(db_path)
    return db_manager.create_all_tables()

# Import models and stores to make them available through the package
from .models import User, Role, Permission, LogEntry, SystemEvent
from .intent_store import IntentStore
from .user_store import UserStore