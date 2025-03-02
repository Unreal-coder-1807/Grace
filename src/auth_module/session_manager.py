"""
Session management for the gesture-voice control system.
Handles user sessions, tokens, and session validation.
"""
import os
from sys import time
import uuid
from typing import Dict, Optional, Any

import jwt
from ..logging.log_manager import get_logger
from ..utils.system.token_manager import generate_token, validate_token

logger = get_logger(__name__)

class SessionManager:
    """Manages user sessions and authentication tokens."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the session manager.
        
        Args:
            config_path: Optional path to session configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Active sessions storage
        # In a production environment, this would be stored in a database or Redis
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Session manager initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load session configuration."""
        if not config_path:
            config_path = os.path.join("config", "settings", "auth.yaml")
            
        # TODO: Implement config loading logic
        # For now, return default configuration
        return {
            'session_expiry': 3600,  # 1 hour in seconds
            'token_algorithm': 'HS256',
            'jwt_secret': os.environ.get('JWT_SECRET', 'dev-secret-key')
        }
    
    def create_session(self, username: str) -> str:
        """
        Create a new session for a user.
        
        Args:
            username: Username to create session for
            
        Returns:
            Session token string
        """
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Current timestamp
        now = int(time.time())
        
        # Session expiry time
        expiry = now + self.config['session_expiry']
        
        # Create session data
        session_data = {
            'username': username,
            'created_at': now,
            'expires_at': expiry,
            'last_active': now
        }
        
        # Store session
        self.active_sessions[session_id] = session_data
        
        # Generate JWT token
        payload = {
            'sub': username,
            'session_id': session_id,
            'iat': now,
            'exp': expiry
        }
        
        token = jwt.encode(
            payload,
            self.config['jwt_secret'],
            algorithm=self.config['token_algorithm']
        )
        
        logger.info(f"Created new session for user {username}")
        return token
    
    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token.
        
        Args:
            token: Session token to validate
            
        Returns:
            Session data if valid, None otherwise
        """
        try:
            # Decode and validate JWT token
            payload = jwt.decode(
                token,
                self.config['jwt_secret'],
                algorithms=[self.config['token_algorithm']]
            )
            
            # Get session ID from payload
            session_id = payload.get('session_id')
            if not session_id:
                logger.warning("Session validation failed: No session_id in token")
                return None
            
            # Get session data
            session_data = self.active_sessions.get(session_id)
            if not session_data:
                logger.warning(f"Session validation failed: Session {session_id[:8]}... not found")
                return None
            
            # Check if session has expired
            now = int(time.time())
            if session_data['expires_at'] < now:
                logger.warning(f"Session validation failed: Session {session_id[:8]}... expired")
                self.end_session(token)
                return None
            
            # Update last active timestamp
            session_data['last_active'] = now
            self.active_sessions[session_id] = session_data
            
            return session_data
            
        except jwt.ExpiredSignatureError:
            logger.warning("Session validation failed: Token expired")
            return None
            
        except jwt.InvalidTokenError:
            logger.warning("Session validation failed: Invalid token")
            return None
    
    def end_session(self, token: str) -> bool:
        """
        End a user session.
        
        Args:
            token: Session token to end
            
        Returns:
            Success status
        """
        try:
            # Decode token without verification to get session ID
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            
            # Get session ID from payload
            session_id = payload.get('session_id')
            if not session_id:
                return False
            
            # Remove session if it exists
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Ended session {session_id[:8]}...")
                return True
                
            return False
            
        except jwt.InvalidTokenError:
            logger.warning("Session end failed: Invalid token format")
            return False
    
    def refresh_session(self, token: str) -> Optional[str]:
        """
        Refresh a session token, extending its expiry time.
        
        Args:
            token: Current session token
            
        Returns:
            New session token if successful, None otherwise
        """
        # Validate the current token
        session_data = self.validate_session(token)
        if not session_data:
            return None
        
        # Get username from session data
        username = session_data.get('username')
        if not username:
            return None
        
        try:
            # Decode token to get session ID
            payload = jwt.decode(
                token,
                self.config['jwt_secret'],
                algorithms=[self.config['token_algorithm']]
            )
            
            # Get session ID
            session_id = payload.get('session_id')
            if not session_id:
                return None
            
            # Update session expiry
            now = int(time.time())
            expiry = now + self.config['session_expiry']
            
            session_data['expires_at'] = expiry
            session_data['last_active'] = now
            
            self.active_sessions[session_id] = session_data
            
            # Generate new JWT token
            new_payload = {
                'sub': username,
                'session_id': session_id,
                'iat': now,
                'exp': expiry
            }
            
            new_token = jwt.encode(
                new_payload,
                self.config['jwt_secret'],
                algorithm=self.config['token_algorithm']
            )
            
            logger.info(f"Refreshed session for user {username}")
            return new_token
            
        except jwt.InvalidTokenError:
            logger.warning("Session refresh failed: Invalid token")
            return None
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.
        
        Returns:
            Number of sessions removed
        """
        now = int(time.time())
        expired_sessions = [
            session_id for session_id, data in self.active_sessions.items()
            if data['expires_at'] < now
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
        return len(expired_sessions)