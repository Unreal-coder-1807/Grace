"""
Main authentication handler for the gesture-voice control system.
Coordinates between different authentication methods and manages the overall auth flow.
"""
import os
import logging
from typing import Optional, Dict, Any, Tuple

from ..logging.log_manager import get_logger
from .user_manager import UserManager
from .permission_manager import PermissionManager
from .session_manager import SessionManager
from .voice_auth import VoiceAuthenticator
from .password_auth import PasswordAuthenticator

logger = get_logger(__name__)

class AuthManager:
    """Main authentication manager that orchestrates different auth methods."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the authentication manager.
        
        Args:
            config_path: Path to authentication configuration file
        """
        # Load configuration if provided, otherwise use default
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.user_manager = UserManager()
        self.permission_manager = PermissionManager()
        self.session_manager = SessionManager()
        
        # Initialize authenticators
        self.password_auth = PasswordAuthenticator()
        self.voice_auth = VoiceAuthenticator()
        
        # Set available auth methods
        self.auth_methods = {
            'password': self.password_auth,
            'voice': self.voice_auth
        }
        
        logger.info("Authentication manager initialized")
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load authentication configuration."""
        if not config_path:
            config_path = os.path.join("config", "settings", "auth.yaml")
            
        # TODO: Implement config loading logic
        # For now, return default configuration
        return {
            'session_expiry': 3600,  # 1 hour in seconds
            'allowed_auth_methods': ['password', 'voice'],
            'required_auth_level': 1,
            'multi_factor_required': False
        }
    
    def authenticate(self, username: str, credentials: Dict[str, Any], method: str = 'password') -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Authenticate a user using the specified method.
        
        Args:
            username: The username to authenticate
            credentials: Authentication credentials (depends on the method)
            method: Authentication method to use ('password' or 'voice')
            
        Returns:
            Tuple containing:
            - Success status (bool)
            - Session token if successful, None otherwise
            - Additional information including user details and permissions if successful
        """
        if method not in self.auth_methods:
            logger.warning(f"Authentication method {method} not supported")
            return False, None, {'error': 'Authentication method not supported'}
        
        # Check if user exists
        user = self.user_manager.get_user(username)
        if not user:
            logger.warning(f"Authentication failed: User {username} not found")
            return False, None, {'error': 'User not found'}
        
        # Authenticate using the selected method
        auth_method = self.auth_methods[method]
        success = auth_method.authenticate(username, credentials)
        
        if not success:
            logger.warning(f"Authentication failed for user {username} using {method} method")
            return False, None, {'error': 'Authentication failed'}
        
        # Create a new session for the authenticated user
        token = self.session_manager.create_session(username)
        
        # Get user permissions
        permissions = self.permission_manager.get_user_permissions(username)
        
        logger.info(f"User {username} authenticated successfully using {method} method")
        return True, token, {
            'user': user,
            'permissions': permissions,
            'auth_method': method
        }
    
    def validate_session(self, token: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate a session token.
        
        Args:
            token: Session token to validate
            
        Returns:
            Tuple containing:
            - Validity status (bool)
            - Username if valid, None otherwise
            - Additional session information if valid
        """
        session_info = self.session_manager.validate_session(token)
        if not session_info:
            return False, None, {'error': 'Invalid or expired session'}
        
        username = session_info.get('username')
        if not username:
            return False, None, {'error': 'Invalid session data'}
        
        # Get user permissions for the validated session
        permissions = self.permission_manager.get_user_permissions(username)
        
        return True, username, {
            'permissions': permissions,
            'session_info': session_info
        }
    
    def logout(self, token: str) -> bool:
        """
        End a user session.
        
        Args:
            token: Session token to invalidate
            
        Returns:
            Success status (bool)
        """
        success = self.session_manager.end_session(token)
        if success:
            logger.info(f"User session ended for token {token[:8]}...")
        else:
            logger.warning(f"Failed to end session for token {token[:8]}...")
        return success
    
    def check_permission(self, token: str, required_permission: str) -> bool:
        """
        Check if the user has the required permission.
        
        Args:
            token: Session token
            required_permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        # Validate session
        valid, username, _ = self.validate_session(token)
        if not valid or not username:
            return False
        
        # Check permission
        return self.permission_manager.has_permission(username, required_permission)