"""
User storage and management for the Gesture & Voice Controlled AI Assistant.

This module provides interfaces for storing, retrieving, and managing
user accounts, roles, and permissions.
"""

import logging
import datetime
import uuid
from typing import List, Dict, Any, Optional, Tuple
import bcrypt
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_

from . import get_db_manager
from .models import User, Role, Permission, UserRole, UserSession, PermissionLevel

# Initialize logger
logger = logging.getLogger(__name__)

class UserStore:
    """
    Manages storage and retrieval of user accounts and related data.
    """
    
    def __init__(self):
        """Initialize the user store."""
        self.logger = logging.getLogger(__name__ + ".UserStore")
        self.db_manager = get_db_manager()
    
    def create_user(self, 
                    username: str, 
                    password: str = None, 
                    email: str = None,
                    roles: List[str] = None) -> Optional[int]:
        """
        Create a new user account.
        
        Args:
            username: Unique username for the account
            password: Password (will be hashed before storage), can be None for voice-only users
            email: Optional email address
            roles: List of role names to assign to the user
            
        Returns:
            int: ID of the newly created user, or None if creation failed
        """
        session = self.db_manager.get_auth_session()
        try:
            # Check if username already exists
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                self.logger.warning(f"User with username '{username}' already exists")
                return None
            
            # Check if email already exists (if provided)
            if email:
                existing = session.query(User).filter(User.email == email).first()
                if existing:
                    self.logger.warning(f"User with email '{email}' already exists")
                    return None
            
            # Hash password if provided
            password_hash = None
            if password:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create new user
            user = User(
                username=username,
                password_hash=password_hash,
                email=email,
                created_at=datetime.datetime.utcnow(),
                is_active=True
            )
            
            session.add(user)
            session.flush()  # To get the user ID
            
            # Assign roles if provided
            if roles:
                for role_name in roles:
                    role = session.query(Role).filter(Role.name == role_name).first()
                    if role:
                        user_role = UserRole(
                            user_id=user.id,
                            role_id=role.id,
                            assigned_at=datetime.datetime.utcnow()
                        )
                        session.add(user_role)
                    else:
                        self.logger.warning(f"Role '{role_name}' not found, skipping assignment")
            
            session.commit()
            self.logger.info(f"Created new user '{username}' with ID {user.id}")
            return user.id
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error creating user '{username}': {e}")
            return None
        finally:
            session.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            Dict or None: User data if authentication succeeds, None otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            user = session.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            
            if not user or not user.password_hash:
                return None
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Update last login time
                user.last_login = datetime.datetime.utcnow()
                session.commit()
                
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'roles': [role.name for role in user.roles],
                    'is_voice_authenticated': user.is_voice_authenticated
                }
            
            return None
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error authenticating user '{username}': {e}")
            return None
        finally:
            session.close()
    
    def authenticate_by_voice(self, voice_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user using voice biometric data.
        
        Args:
            voice_data: Binary voice data for authentication
            
        Returns:
            Dict or None: User data if authentication succeeds, None otherwise
        """
        # This would typically call into voice_auth module to verify the biometric data
        from ..auth_module.voice_auth import verify_voice_identity
        
        session = self.db_manager.get_auth_session()
        try:
            user_id = verify_voice_identity(voice_data)
            if not user_id:
                return None
                
            user = session.query(User).filter(
                User.id == user_id,
                User.is_active == True,
                User.is_voice_authenticated == True
            ).first()
            
            if not user:
                return None
                
            # Update last login time
            user.last_login = datetime.datetime.utcnow()
            session.commit()
            
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'roles': [role.name for role in user.roles],
                'is_voice_authenticated': True
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error in voice authentication: {e}")
            return None
        finally:
            session.close()
    
    def create_session(self, user_id: int) -> Optional[str]:
        """
        Create a new session for a user.
        
        Args:
            user_id: ID of the user to create session for
            
        Returns:
            str: Session token or None if creation failed
        """
        session = self.db_manager.get_auth_session()
        try:
            # Generate a unique session token
            token = str(uuid.uuid4())
            
            # Create session record
            user_session = UserSession(
                user_id=user_id,
                token=token,
                created_at=datetime.datetime.utcnow(),
                expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1),
                is_active=True
            )
            
            session.add(user_session)
            session.commit()
            
            self.logger.info(f"Created new session for user ID {user_id}")
            return token
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error creating session for user ID {user_id}: {e}")
            return None
        finally:
            session.close()
    
    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token and return user information.
        
        Args:
            token: Session token to validate
            
        Returns:
            Dict or None: User data if session is valid, None otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            user_session = session.query(UserSession).filter(
                UserSession.token == token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.datetime.utcnow()
            ).first()
            
            if not user_session:
                return None
                
            user = session.query(User).filter(
                User.id == user_session.user_id,
                User.is_active == True
            ).first()
            
            if not user:
                return None
                
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'roles': [role.name for role in user.roles],
                'is_voice_authenticated': user.is_voice_authenticated,
                'session_expires': user_session.expires_at
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error validating session token: {e}")
            return None
        finally:
            session.close()
    
    def end_session(self, token: str) -> bool:
        """
        End (invalidate) a user session.
        
        Args:
            token: Session token to invalidate
            
        Returns:
            bool: True if session was ended successfully, False otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            user_session = session.query(UserSession).filter(
                UserSession.token == token,
                UserSession.is_active == True
            ).first()
            
            if not user_session:
                return False
                
            user_session.is_active = False
            user_session.ended_at = datetime.datetime.utcnow()
            session.commit()
            
            self.logger.info(f"Ended session for user ID {user_session.user_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error ending session: {e}")
            return False
        finally:
            session.close()
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get information for a specific user.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            Dict or None: User data if found, None otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return None
                
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at,
                'last_login': user.last_login,
                'is_active': user.is_active,
                'is_voice_authenticated': user.is_voice_authenticated,
                'roles': [role.name for role in user.roles]
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving user with ID {user_id}: {e}")
            return None
        finally:
            session.close()
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """
        Update user information.
        
        Args:
            user_id: ID of the user to update
            **kwargs: Fields to update and their new values
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False
            
            # Update password if provided
            if 'password' in kwargs:
                kwargs['password_hash'] = bcrypt.hashpw(
                    kwargs['password'].encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
                del kwargs['password']
            
            # Check if email is being updated and ensure uniqueness
            if 'email' in kwargs and kwargs['email'] != user.email:
                existing = session.query(User).filter(User.email == kwargs['email']).first()
                if existing:
                    self.logger.warning(f"Cannot update user ID {user_id}: email '{kwargs['email']}' already exists")
                    return False
            
            # Check if username is being updated and ensure uniqueness
            if 'username' in kwargs and kwargs['username'] != user.username:
                existing = session.query(User).filter(User.username == kwargs['username']).first()
                if existing:
                    self.logger.warning(f"Cannot update user ID {user_id}: username '{kwargs['username']}' already exists")
                    return False
            
            # Update roles if provided
            if 'roles' in kwargs:
                # Remove existing role associations
                for user_role in user.user_roles:
                    session.delete(user_role)
                
                # Add new role associations
                for role_name in kwargs['roles']:
                    role = session.query(Role).filter(Role.name == role_name).first()
                    if role:
                        user_role = UserRole(
                            user_id=user.id,
                            role_id=role.id,
                            assigned_at=datetime.datetime.utcnow()
                        )
                        session.add(user_role)
                    else:
                        self.logger.warning(f"Role '{role_name}' not found, skipping assignment")
                
                del kwargs['roles']
            
            # Update remaining fields
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            session.commit()
            self.logger.info(f"Updated user ID {user_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error updating user ID {user_id}: {e}")
            return False
        finally:
            session.close()
    
    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user account (soft delete).
        
        Args:
            user_id: ID of the user to deactivate
            
        Returns:
            bool: True if deactivation was successful, False otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False
            
            user.is_active = False
            
            # Also end all active sessions for this user
            active_sessions = session.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).all()
            
            for user_session in active_sessions:
                user_session.is_active = False
                user_session.ended_at = datetime.datetime.utcnow()
            
            session.commit()
            self.logger.info(f"Deactivated user ID {user_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error deactivating user ID {user_id}: {e}")
            return False
        finally:
            session.close()
    
    def reactivate_user(self, user_id: int) -> bool:
        """
        Reactivate a previously deactivated user account.
        
        Args:
            user_id: ID of the user to reactivate
            
        Returns:
            bool: True if reactivation was successful, False otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False
            
            user.is_active = True
            session.commit()
            self.logger.info(f"Reactivated user ID {user_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error reactivating user ID {user_id}: {e}")
            return False
        finally:
            session.close()
    
    def get_user_permissions(self, user_id: int) -> Dict[str, PermissionLevel]:
        """
        Get all permissions for a user based on their roles.
        
        Args:
            user_id: ID of the user to get permissions for
            
        Returns:
            Dict: Mapping of permission names to their levels
        """
        session = self.db_manager.get_auth_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {}
            
            # Collect all permissions from all roles
            permissions = {}
            for role in user.roles:
                for permission in role.permissions:
                    # If permission already exists, use the highest level
                    if permission.name in permissions:
                        if permission.level.value > permissions[permission.name].value:
                            permissions[permission.name] = permission.level
                    else:
                        permissions[permission.name] = permission.level
            
            return permissions
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting permissions for user ID {user_id}: {e}")
            return {}
        finally:
            session.close()
    
    def has_permission(self, user_id: int, permission_name: str, min_level: PermissionLevel = None) -> bool:
        """
        Check if a user has a specific permission at or above the minimum level.
        
        Args:
            user_id: ID of the user to check
            permission_name: Name of the permission to check
            min_level: Minimum required permission level (optional)
            
        Returns:
            bool: True if user has the permission at the required level, False otherwise
        """
        permissions = self.get_user_permissions(user_id)
        
        if permission_name not in permissions:
            return False
        
        if min_level is None:
            return True
        
        return permissions[permission_name].value >= min_level.value
    
    def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for users by username or email.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List: List of matching user data dictionaries
        """
        session = self.db_manager.get_auth_session()
        try:
            # Search by username or email
            users = session.query(User).filter(
                or_(
                    User.username.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%")
                )
            ).limit(limit).all()
            
            results = []
            for user in users:
                results.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'roles': [role.name for role in user.roles]
                })
            
            return results
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error searching users with query '{query}': {e}")
            return []
        finally:
            session.close()
    
    def register_voice_pattern(self, user_id: int, voice_data: bytes) -> bool:
        """
        Register or update voice biometric data for a user.
        
        Args:
            user_id: ID of the user to update
            voice_data: Voice data to register
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        # This would typically call into voice_auth module to store the biometric data
        from ..auth_module.voice_auth import register_voice_pattern as register_voice
        
        session = self.db_manager.get_auth_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False
            
            # Register voice pattern
            success = register_voice(user_id, voice_data)
            if not success:
                return False
            
            # Update user record
            user.is_voice_authenticated = True
            session.commit()
            
            self.logger.info(f"Registered voice pattern for user ID {user_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error registering voice pattern for user ID {user_id}: {e}")
            return False
        finally:
            session.close()


class RoleStore:
    """
    Manages storage and retrieval of roles and permissions.
    """
    
    def __init__(self):
        """Initialize the role store."""
        self.logger = logging.getLogger(__name__ + ".RoleStore")
        self.db_manager = get_db_manager()
    
    def create_role(self, name: str, description: str = None) -> Optional[int]:
        """
        Create a new role.
        
        Args:
            name: Unique name for the role
            description: Optional description of the role
            
        Returns:
            int: ID of the newly created role, or None if creation failed
        """
        session = self.db_manager.get_auth_session()
        try:
            # Check if role already exists
            existing = session.query(Role).filter(Role.name == name).first()
            if existing:
                self.logger.warning(f"Role with name '{name}' already exists")
                return None
            
            # Create new role
            role = Role(
                name=name,
                description=description,
                created_at=datetime.datetime.utcnow()
            )
            
            session.add(role)
            session.commit()
            
            self.logger.info(f"Created new role '{name}' with ID {role.id}")
            return role.id
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error creating role '{name}': {e}")
            return None
        finally:
            session.close()
    
    def add_permission_to_role(self, role_id: int, permission_name: str, 
                              permission_level: PermissionLevel) -> bool:
        """
        Add a permission to a role or update its level if it already exists.
        
        Args:
            role_id: ID of the role to update
            permission_name: Name of the permission to add
            permission_level: Level to set for the permission
            
        Returns:
            bool: True if the operation was successful, False otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            # Get or create permission
            permission = session.query(Permission).filter(
                Permission.name == permission_name
            ).first()
            
            if not permission:
                permission = Permission(
                    name=permission_name,
                    created_at=datetime.datetime.utcnow()
                )
                session.add(permission)
                session.flush()
            
            # Get role
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                self.logger.warning(f"Role with ID {role_id} not found")
                return False
            
            # Check if role already has this permission
            existing = False
            for p in role.permissions:
                if p.id == permission.id:
                    # Update the level
                    p.level = permission_level
                    existing = True
                    break
            
            # Add permission to role if it doesn't already have it
            if not existing:
                role.permissions.append(permission)
                
                # Set the permission level
                for p in role.permissions:
                    if p.id == permission.id:
                        p.level = permission_level
                        break
            
            session.commit()
            self.logger.info(f"Added permission '{permission_name}' to role '{role.name}'")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error adding permission to role: {e}")
            return False
        finally:
            session.close()
    
    def get_role(self, role_id: int) -> Optional[Dict[str, Any]]:
        """
        Get information for a specific role.
        
        Args:
            role_id: ID of the role to retrieve
            
        Returns:
            Dict or None: Role data if found, None otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            role = session.query(Role).filter(Role.id == role_id).first()
            
            if not role:
                return None
            
            permissions = {}
            for permission in role.permissions:
                permissions[permission.name] = permission.level
            
            return {
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'created_at': role.created_at,
                'permissions': permissions
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving role with ID {role_id}: {e}")
            return None
        finally:
            session.close()
    
    def get_all_roles(self) -> List[Dict[str, Any]]:
        """
        Get all roles in the system.
        
        Returns:
            List: List of role data dictionaries
        """
        session = self.db_manager.get_auth_session()
        try:
            roles = session.query(Role).all()
            
            results = []
            for role in roles:
                permissions = {}
                for permission in role.permissions:
                    permissions[permission.name] = permission.level
                
                results.append({
                    'id': role.id,
                    'name': role.name,
                    'description': role.description,
                    'created_at': role.created_at,
                    'permissions': permissions
                })
            
            return results
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving roles: {e}")
            return []
        finally:
            session.close()


# Convenience functions
def get_user_store() -> UserStore:
    """Get a UserStore instance."""
    return UserStore()

def get_role_store() -> RoleStore:
    """Get a RoleStore instance."""
    return RoleStore()