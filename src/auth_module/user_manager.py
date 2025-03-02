"""
User management system for gesture-voice control.
Handles user creation, deletion, and updates.
"""
import os
import json
import uuid
from typing import Dict, List, Optional, Any

from ..logging.log_manager import get_logger
from ..database.user_store import UserStore
from .password_auth import PasswordAuthenticator

logger = get_logger(__name__)

class UserManager:
    """Manages user accounts in the system."""
    
    def __init__(self):
        """Initialize the user manager."""
        self.user_store = UserStore()
        self.password_auth = PasswordAuthenticator()
        logger.info("User manager initialized")
    
    def create_user(self, username: str, password: str, email: str, 
                   full_name: str = "", role: str = "user", 
                   voice_profile: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            password: User password
            email: User email address
            full_name: User's full name
            role: User role (default: "user")
            voice_profile: Optional path to voice profile data
            
        Returns:
            New user data or error message
        """
        # Check if username already exists
        if self.user_store.user_exists(username):
            logger.warning(f"User creation failed: Username {username} already exists")
            return {"success": False, "error": "Username already exists"}
        
        # Generate a unique user ID
        user_id = str(uuid.uuid4())
        
        # Hash the password
        password_hash = self.password_auth.hash_password(password)
        
        # Create user data
        user_data = {
            "user_id": user_id,
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "full_name": full_name,
            "role": role,
            "voice_profile": voice_profile,
            "enabled": True,
            "created_at": self.user_store.get_current_timestamp(),
            "last_login": None
        }
        
        # Save user to database
        success = self.user_store.add_user(user_data)
        
        if success:
            logger.info(f"User {username} created successfully")
            return {"success": True, "user_id": user_id}
        else:
            logger.error(f"Failed to create user {username}")
            return {"success": False, "error": "Database error"}
    
    def update_user(self, username: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user data.
        
        Args:
            username: Username to update
            updates: Dictionary of fields to update
            
        Returns:
            Status of update operation
        """
        # Check if user exists
        if not self.user_store.user_exists(username):
            logger.warning(f"User update failed: User {username} not found")
            return {"success": False, "error": "User not found"}
        
        # Handle password update separately if included
        if "password" in updates:
            password = updates.pop("password")
            updates["password_hash"] = self.password_auth.hash_password(password)
        
        # Update timestamp
        updates["updated_at"] = self.user_store.get_current_timestamp()
        
        # Save updated user data
        success = self.user_store.update_user(username, updates)
        
        if success:
            logger.info(f"User {username} updated successfully")
            return {"success": True}
        else:
            logger.error(f"Failed to update user {username}")
            return {"success": False, "error": "Database error"}
    
    def delete_user(self, username: str) -> Dict[str, Any]:
        """
        Delete a user account.
        
        Args:
            username: Username to delete
            
        Returns:
            Status of delete operation
        """
        # Check if user exists
        if not self.user_store.user_exists(username):
            logger.warning(f"User deletion failed: User {username} not found")
            return {"success": False, "error": "User not found"}
        
        # Delete the user
        success = self.user_store.delete_user(username)
        
        if success:
            logger.info(f"User {username} deleted successfully")
            return {"success": True}
        else:
            logger.error(f"Failed to delete user {username}")
            return {"success": False, "error": "Database error"}
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user data by username.
        
        Args:
            username: Username to retrieve
            
        Returns:
            User data or None if not found
        """
        user = self.user_store.get_user(username)
        
        if user:
            # Remove sensitive data before returning
            if "password_hash" in user:
                del user["password_hash"]
                
            return user
        
        return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users in the system.
        
        Returns:
            List of all user records
        """
        users = self.user_store.get_all_users()
        
        # Remove sensitive data before returning
        for user in users:
            if "password_hash" in user:
                del user["password_hash"]
        
        return users
    
    def set_user_enabled(self, username: str, enabled: bool) -> Dict[str, Any]:
        """
        Enable or disable a user account.
        
        Args:
            username: Username to update
            enabled: Whether the account should be enabled
            
        Returns:
            Status of the operation
        """
        return self.update_user(username, {"enabled": enabled})
    
    def update_last_login(self, username: str) -> None:
        """
        Update the last login timestamp for a user.
        
        Args:
            username: Username to update
        """
        self.user_store.update_user(
            username, 
            {"last_login": self.user_store.get_current_timestamp()}
        )