"""
Access control module.

This module handles permission checks for system operations,
enforcing role-based access control (RBAC) for gesture and voice commands.
"""

import logging
from typing import Dict, List, Optional, Union, Any
import json
import os

logger = logging.getLogger(__name__)

# Define permission levels
PERMISSION_LEVELS = {
    "GUEST": 0,
    "USER": 1,
    "POWER_USER": 2,
    "ADMINISTRATOR": 3
}

# Define default permissions for command categories
DEFAULT_PERMISSIONS = {
    "navigation": PERMISSION_LEVELS["GUEST"],       # Basic navigation, scrolling
    "text_input": PERMISSION_LEVELS["USER"],        # Typing, text editing
    "media_control": PERMISSION_LEVELS["USER"],     # Volume, playback control
    "application": PERMISSION_LEVELS["USER"],       # Opening/closing applications
    "system_info": PERMISSION_LEVELS["USER"],       # System status, info
    "browser": PERMISSION_LEVELS["USER"],           # Browser operations
    "file_access": PERMISSION_LEVELS["POWER_USER"], # File operations
    "system_control": PERMISSION_LEVELS["ADMINISTRATOR"],  # Shutdown, restart
    "security": PERMISSION_LEVELS["ADMINISTRATOR"]  # Lock screen, authentication
}

class AccessController:
    """Controller for permission checks and access control."""
    
    def __init__(self, permission_file: Optional[str] = None):
        """
        Initialize the access controller.
        
        Args:
            permission_file: Path to JSON file with permission configuration
        """
        self.logger = logging.getLogger(__name__)
        
        # Set default permission configuration
        self.permission_levels = PERMISSION_LEVELS.copy()
        self.command_permissions = DEFAULT_PERMISSIONS.copy()
        
        # Override with custom permissions from file if provided
        if permission_file and os.path.exists(permission_file):
            self._load_permissions(permission_file)
        
        # Current user context
        self.current_user = None
        self.current_role = None
        self.current_permission_level = PERMISSION_LEVELS["GUEST"]
        
        self.logger.info("Access controller initialized")
    
    def _load_permissions(self, permission_file: str) -> bool:
        """
        Load permission configuration from JSON file.
        
        Args:
            permission_file: Path to JSON permission file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(permission_file, 'r') as f:
                config = json.load(f)
                
                # Update permission levels if provided
                if 'permission_levels' in config:
                    for role, level in config['permission_levels'].items():
                        self.permission_levels[role] = level
                
                # Update command permissions if provided
                if 'command_permissions' in config:
                    for category, level in config['command_permissions'].items():
                        self.command_permissions[category] = level
                
                self.logger.info(f"Loaded permissions from {permission_file}")
                return True
        except Exception as e:
            self.logger.error(f"Error loading permissions from {permission_file}: {str(e)}")
            return False
    
    def set_user_context(self, user: str, role: str) -> bool:
        """
        Set the current user context.
        
        Args:
            user: User identifier
            role: User role (must be in permission_levels)
            
        Returns:
            True if successful, False if role is invalid
        """
        if role not in self.permission_levels:
            self.logger.error(f"Invalid role: {role}")
            return False
        
        self.current_user = user
        self.current_role = role
        self.current_permission_level = self.permission_levels[role]
        self.logger.info(f"Set user context: {user} with role {role} (level {self.current_permission_level})")
        return True
    
    def clear_user_context(self) -> None:
        """Clear the current user context (revert to guest)."""
        self.current_user = None
        self.current_role = None
        self.current_permission_level = PERMISSION_LEVELS["GUEST"]
        self.logger.info("Cleared user context (reverted to guest)")
    
    def check_permission(self, command_category: str) -> bool:
        """
        Check if current user has permission for a command category.
        
        Args:
            command_category: Category of the command
            
        Returns:
            True if access is allowed, False otherwise
        """
        # If category not defined, deny by default
        if command_category not in self.command_permissions:
            self.logger.warning(f"Unknown command category: {command_category}, access denied")
            return False
        
        # Get required permission level for this command category
        required_level = self.command_permissions[command_category]
        
        # Check if current user has sufficient permission
        has_permission = self.current_permission_level >= required_level
        
        if has_permission:
            self.logger.debug(f"Permission granted for {command_category} (required: {required_level}, user: {self.current_permission_level})")
        else:
            self.logger.warning(f"Permission denied for {command_category} (required: {required_level}, user: {self.current_permission_level})")
        
        return has_permission
    
    def check_permission_for_command(self, command: str, command_map: Dict[str, str]) -> bool:
        """
        Check if current user has permission for a specific command.
        
        Args:
            command: The specific command to check
            command_map: Mapping of commands to their categories
            
        Returns:
            True if access is allowed, False otherwise
        """
        if command not in command_map:
            self.logger.warning(f"Unknown command: {command}, access denied")
            return False
        
        command_category = command_map[command]
        return self.check_permission(command_category)
    
    def get_available_commands(self, command_map: Dict[str, str]) -> List[str]:
        """
        Get a list of commands available to the current user.
        
        Args:
            command_map: Mapping of commands to their categories
            
        Returns:
            List of available command names
        """
        available_commands = []
        
        for command, category in command_map.items():
            if self.check_permission(category):
                available_commands.append(command)
        
        self.logger.debug(f"Available commands for current user: {len(available_commands)} commands")
        return available_commands
    
    def get_permission_requirements(self) -> Dict[str, Dict[str, Union[int, str]]]:
        """
        Get the permission requirements for command categories.
        
        Returns:
            Dictionary mapping categories to their required roles and levels
        """
        requirements = {}
        
        # Reverse mapping from permission level to role name
        level_to_role = {level: role for role, level in self.permission_levels.items()}
        
        for category, level in self.command_permissions.items():
            role = level_to_role.get(level, "UNKNOWN")
            requirements[category] = {
                "level": level,
                "role": role
            }
        
        return requirements
    
    def add_custom_command_category(self, category: str, required_level: int) -> bool:
        """
        Add a new command category with permission level.
        
        Args:
            category: New command category name
            required_level: Required permission level
            
        Returns:
            True if successful, False if category already exists
        """
        if category in self.command_permissions:
            self.logger.warning(f"Command category already exists: {category}")
            return False
        
        self.command_permissions[category] = required_level
        self.logger.info(f"Added command category {category} with permission level {required_level}")
        return True
    
    def update_command_permission(self, category: str, required_level: int) -> bool:
        """
        Update permission level for an existing command category.
        
        Args:
            category: Existing command category name
            required_level: New required permission level
            
        Returns:
            True if successful, False if category doesn't exist
        """
        if category not in self.command_permissions:
            self.logger.warning(f"Command category doesn't exist: {category}")
            return False
        
        self.command_permissions[category] = required_level
        self.logger.info(f"Updated command category {category} to permission level {required_level}")
        return True
    
    def save_permissions(self, permission_file: str) -> bool:
        """
        Save current permission configuration to a JSON file.
        
        Args:
            permission_file: Path to save the JSON permission file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config = {
                'permission_levels': self.permission_levels,
                'command_permissions': self.command_permissions
            }
            
            with open(permission_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            self.logger.info(f"Saved permissions to {permission_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving permissions to {permission_file}: {str(e)}")
            return False