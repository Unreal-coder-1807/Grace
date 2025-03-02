"""
Authentication module for the gesture-voice control system.
Provides user authentication, permission management and session handling.
"""

from .auth_manager import AuthManager
from .user_manager import UserManager
from .permission_manager import PermissionManager
from .session_manager import SessionManager
from .voice_auth import VoiceAuthenticator
from .password_auth import PasswordAuthenticator

__all__ = [
    'AuthManager',
    'UserManager',
    'PermissionManager',
    'SessionManager',
    'VoiceAuthenticator',
    'PasswordAuthenticator',
]