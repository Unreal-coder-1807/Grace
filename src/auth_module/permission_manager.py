"""
Permission management system for gesture-voice control.
Handles role-based permissions and access control.
"""
from typing import Dict, List, Set, Optional, Any
import os
import json

from ..logging.log_manager import get_logger
from ..database.user_store import UserStore

logger = get_logger(__name__)

class PermissionManager:
    """Manages user permissions and access control."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the permission manager.
        
        Args:
            config_path: Optional path to permission configuration file
        """
        self.user_store = UserStore()
        self.role_permissions = self._load_role_permissions(config_path)
        logger.info("Permission manager initialized")
    
    def _load_role_permissions(self, config_path: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Load role-based permissions from configuration.
        
        Args:
            config_path: Path to permissions configuration file
            
        Returns:
            Dictionary mapping roles to their permissions
        """
        if not config_path:
            config_path = os.path.join("config", "settings", "auth.yaml")
        
        # TODO: Load from YAML configuration file
        # For now, return default role permissions
        return {
            "admin": [
                "user:create", "user:read", "user:update", "user:delete",
                "system:control", "voice:admin", "gesture:admin",
                "settings:read", "settings:write",
                "logs:read"
            ],
            "moderator": [
                "user:read",
                "system:control", "voice:use", "gesture:use",
                "settings:read",
                "logs:read"
            ],
            "user": [
                "voice:use", "gesture:use",
                "settings:read:own"
            ],
            "guest": [
                "voice:limited", "gesture:limited"
            ]
        }
    
    def get_user_permissions(self, username: str) -> Set[str]:
        """
        Get all permissions for a user based on their role.
        
        Args:
            username: Username to get permissions for
            
        Returns:
            Set of permission strings
        """
        user = self.user_store.get_user(username)
        if not user:
            logger.warning(f"Permissions request failed: User {username} not found")
            return set()
        
        role = user.get("role", "guest")
        
        # Get default permissions for the role
        permissions = set(self.role_permissions.get(role, []))
        
        # Get any additional custom permissions for this user
        custom_permissions = self.user_store.get_user_custom_permissions(username)
        if custom_permissions:
            permissions.update(custom_permissions)
        
        return permissions
    
    def has_permission(self, username: str, permission: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            username: Username to check
            permission: Permission to verify
            
        Returns:
            True if user has the permission, False otherwise
        """
        user_permissions = self.get_user_permissions(username)
        
        # Check for exact permission
        if permission in user_permissions:
            return True
        
        # Check for wildcard permissions (e.g., "user:*" would grant all user permissions)
        permission_parts = permission.split(":")
        for i in range(len(permission_parts)):
            wildcard = ":".join(permission_parts[:i]) + ":*"
            if wildcard in user_permissions:
                return True
        
        # Check for higher-level permissions
        for i in range(len(permission_parts) - 1, 0, -1):
            higher_level = ":".join(permission_parts[:i])
            if higher_level in user_permissions:
                return True
        
        return False
    
    def add_user_permission(self, username: str, permission: str) -> bool:
        """
        Add a custom permission to a user.
        
        Args:
            username: Username to update
            permission: Permission to add
            
        Returns:
            Success status
        """
        return self.user_store.add_user_permission(username, permission)
    
    def remove_user_permission(self, username: str, permission: str) -> bool:
        """
        Remove a custom permission from a user.
        
        Args:
            username: Username to update
            permission: Permission to remove
            
        Returns:
            Success status
        """
        return self.user_store.remove_user_permission(username, permission)
    
    def change_user_role(self, username: str, new_role: str) -> bool:
        """
        Change a user's role.
        
        Args:
            username: Username to update
            new_role: New role to assign
            
        Returns:
            Success status
        """
        # Check if the role is valid
        if new_role not in self.role_permissions:
            logger.warning(f"Invalid role {new_role} for user {username}")
            return False
        
        # Update the user's role
        return self.user_store.update_user(username, {"role": new_role})
    
    def get_available_roles(self) -> List[str]:
        """
        Get list of all available roles.
        
        Returns:
            List of role names
        """
        return list(self.role_permissions.keys())
    
    def get_role_permissions(self, role: str) -> List[str]:
        """
        Get permissions for a specific role.
        
        Args:
            role: Role name
            
        Returns:
            List of permissions
        """
        return self.role_permissions.get(role, [])