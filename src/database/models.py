"""
Database models for the Gesture & Voice Controlled AI Assistant.

This module defines SQLAlchemy models for persistence of users, permissions,
logs, events, and other entities required by the application.
"""

import datetime
import enum
import uuid
import sqlalchemy
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, 
    Boolean, ForeignKey, Enum, Text, JSON, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from . import Base

# User Authentication Models

class PermissionLevel(enum.Enum):
    """Permission levels for the application."""
    GUEST = 0
    USER = 1
    POWER_USER = 2
    ADMIN = 3
    SYSTEM = 4

class User(Base):
    """User model for authentication and identification."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(128), nullable=True)  # Hashed password
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_voice_authenticated = Column(Boolean, default=False)
    voice_print_ref = Column(String(255), nullable=True)  # Reference to voice biometric data
    
    # Relationships
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    log_entries = relationship("LogEntry", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Role(Base):
    """Role model for role-based access control."""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship("User", secondary="user_roles", back_populates="roles")
    permissions = relationship("Permission", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

# Association table for many-to-many User to Role relationship
class UserRole(Base):
    """Association table for User to Role relationship."""
    __tablename__ = 'user_roles'
    
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"

class Permission(Base):
    """Permission model for access control."""
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'))
    resource = Column(String(100), nullable=False)  # The resource or feature
    action = Column(String(50), nullable=False)     # The action (read, write, execute)
    level = Column(Enum(PermissionLevel), default=PermissionLevel.USER)
    
    # Relationships
    role = relationship("Role", back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, resource='{self.resource}', action='{self.action}')>"

class UserSession(Base):
    """User session for tracking active sessions."""
    __tablename__ = 'user_sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    token = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 addresses can be long
    user_agent = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id={self.user_id})>"

# Logging Models

class LogLevel(enum.Enum):
    """Log levels for the application."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class LogEntry(Base):
    """Log entry for tracking user actions and system events."""
    __tablename__ = 'log_entries'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    level = Column(Enum(LogLevel), default=LogLevel.INFO)
    module = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    source_ip = Column(String(45), nullable=True)
    request_path = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)  # Additional structured data
    
    # Relationships
    user = relationship("User", back_populates="log_entries")
    
    def __repr__(self):
        return f"<LogEntry(id={self.id}, level={self.level.name}, module='{self.module}')>"

class SystemEvent(Base):
    """System event for tracking system-level events."""
    __tablename__ = 'system_events'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    event_type = Column(String(50), nullable=False)
    component = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    success = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<SystemEvent(id={self.id}, event_type='{self.event_type}', component='{self.component}')>"

# Voice and Gesture Recognition Models

class Intent(Base):
    """Intent model for mapping voice commands to actions."""
    __tablename__ = 'intents'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    pattern = Column(String(255), nullable=False)  # Regex or pattern to match
    action_module = Column(String(100), nullable=False)
    action_function = Column(String(100), nullable=False)
    parameters = Column(JSON, nullable=True)  # Additional parameters for the action
    required_permission = Column(Enum(PermissionLevel), default=PermissionLevel.USER)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Intent(id={self.id}, name='{self.name}')>"

class GestureMapping(Base):
    """Gesture mapping model for storing gesture to action mappings."""
    __tablename__ = 'gesture_mappings'
    
    id = Column(Integer, primary_key=True)
    gesture_name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    action_module = Column(String(100), nullable=False)
    action_function = Column(String(100), nullable=False)
    parameters = Column(JSON, nullable=True)  # Additional parameters for the action
    required_permission = Column(Enum(PermissionLevel), default=PermissionLevel.USER)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<GestureMapping(id={self.id}, gesture_name='{self.gesture_name}')>"

class UserPreference(Base):
    """User preference model for storing user-specific settings."""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(JSON, nullable=True)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Composite unique constraint
    __table_args__ = (
        sqlalchemy.UniqueConstraint('user_id', 'preference_key', name='uix_user_preference'),
    )
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, key='{self.preference_key}')>"