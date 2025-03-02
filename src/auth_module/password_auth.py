"""
Password-based authentication module for gesture-voice control system.
Handles password hashing, verification, and password policies.
"""
import os
import re
import bcrypt
from typing import Dict, Any, Optional, List

from ..logging.log_manager import get_logger
from ..database.user_store import UserStore

logger = get_logger(__name__)

class PasswordAuthenticator:
    """Handles password-based authentication."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the password authenticator.
        
        Args:
            config_path: Optional path to password auth configuration file
        """
        self.user_store = UserStore()
        self.config = self._load_config(config_path)
        logger.info("Password authenticator initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load password authentication configuration."""
        if not config_path:
            config_path = os.path.join("config", "settings", "auth.yaml")
            
        # TODO: Implement config loading logic
        # For now, return default configuration
        return {
            'min_password_length': 8,
            'require_mixed_case': True,
            'require_numbers': True,
            'require_special_chars': True,
            'bcrypt_rounds': 12,
            'max_failed_attempts': 5,
            'lockout_duration': 1800  # 30 minutes in seconds
        }
    
    def authenticate(self, username: str, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate a user using password.
        
        Args:
            username: Username to authenticate
            credentials: Dictionary containing password
                {
                    'password': Plain text password
                }
            
        Returns:
            True if authentication successful, False otherwise
        """
        # Check if user exists
        user = self.user_store.get_user(username)
        if not user:
            logger.warning(f"Password authentication failed: User {username} not found")
            return False
        
        # Extract password from credentials
        password = credentials.get('password')
        if not password:
            logger.warning("Password authentication failed: No password provided")
            return False
        
        # Check if account is locked due to too many failed attempts
        if self._is_account_locked(username):
            logger.warning(f"Password authentication failed: Account {username} is locked")
            return False
        
        # Get stored password hash
        stored_hash = user.get('password_hash')
        if not stored_hash:
            logger.warning(f"Password authentication failed: No password hash for user {username}")
            return False
        
        # Verify password
        try:
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            
            if isinstance(password, str):
                password = password.encode('utf-8')
                
            is_valid = bcrypt.checkpw(password, stored_hash)
            
            if is_valid:
                # Reset failed attempts on successful login
                self._reset_failed_attempts(username)
                logger.info(f"Password authentication successful for user {username}")
                return True
            else:
                # Increment failed attempts
                self._increment_failed_attempts(username)
                logger.warning(f"Password authentication failed for user {username}: Invalid password")
                return False
                
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        if isinstance(password, str):
            password = password.encode('utf-8')
            
        salt = bcrypt.gensalt(rounds=self.config['bcrypt_rounds'])
        hashed = bcrypt.hashpw(password, salt)
        
        return hashed.decode('utf-8')
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Check if a password meets the strength requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Validation result with success flag and error messages
        """
        errors = []
        
        # Check length
        if len(password) < self.config['min_password_length']:
            errors.append(f"Password must be at least {self.config['min_password_length']} characters long")
        
        # Check for mixed case if required
        if self.config['require_mixed_case'] and not (any(c.islower() for c in password) and any(c.isupper() for c in password)):
            errors.append("Password must contain both uppercase and lowercase letters")
        
        # Check for numbers if required
        if self.config['require_numbers'] and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        # Check for special characters if required
        if self.config['require_special_chars'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change a user's password.
        
        Args:
            username: Username to update
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Status of password change operation
        """
        # Authenticate with old password
        auth_success = self.authenticate(username, {"password": old_password})
        if not auth_success:
            return {"success": False, "error": "Current password is incorrect"}
        
        # Validate new password strength
        validation = self.validate_password_strength(new_password)
        if not validation["valid"]:
            return {"success": False, "errors": validation["errors"]}
        
        # Hash new password
        new_hash = self.hash_password(new_password)
        
        # Update user record
        success = self.user_store.update_user(
            username,
            {"password_hash": new_hash}
        )
        
        if success:
            logger.info(f"Password changed successfully for user {username}")
            return {"success": True}
        else:
            logger.error(f"Failed to update password for user {username}")
            return {"success": False, "error": "Database error"}
    
    def reset_password(self, username: str, new_password: str) -> Dict[str, Any]:
        """
        Reset a user's password (admin function).
        
        Args:
            username: Username to update
            new_password: New password to set
            
        Returns:
            Status of password reset operation
        """
        # Validate new password strength
        validation = self.validate_password_strength(new_password)
        if not validation["valid"]:
            return {"success": False, "errors": validation["errors"]}
        
        # Hash new password
        new_hash = self.hash_password(new_password)
        
        # Update user record
        success = self.user_store.update_user(
            username,
            {"password_hash": new_hash}
        )
        
        if success:
            # Reset failed attempts counter
            self._reset_failed_attempts(username)
            logger.info(f"Password reset successfully for user {username}")
            return {"success": True}
        else:
            logger.error(f"Failed to reset password for user {username}")
            return {"success": False, "error": "Database error"}
    
    def _is_account_locked(self, username: str) -> bool:
        """
        Check if an account is locked due to too many failed attempts.
        
        Args:
            username: Username to check
            
        Returns:
            True if account is locked, False otherwise
        """
        # Get failed attempts data
        failed_attempts = self.user_store.get_failed_login_attempts(username)
        
        if not failed_attempts:
            return False
        
        count = failed_attempts.get('count', 0)
        timestamp = failed_attempts.get('timestamp', 0)
        
        # Check if max attempts exceeded
        if count >= self.config['max_failed_attempts']:
            # Check if lockout period has passed
            from sys import time
            current_time = int(time.time())
            lockout_end = timestamp + self.config['lockout_duration']
            
            if current_time < lockout_end:
                return True
            else:
                # Reset counter if lockout period has passed
                self._reset_failed_attempts(username)
                return False
        
        return False
    
    def _increment_failed_attempts(self, username: str) -> None:
        """
        Increment the failed attempts counter for a user.
        
        Args:
            username: Username to update
        """
        self.user_store.increment_failed_login_attempts(username)
    
    def _reset_failed_attempts(self, username: str) -> None:
        """
        Reset the failed attempts counter for a user.
        
        Args:
            username: Username to update
        """
        self.user_store.reset_failed_login_attempts(username)