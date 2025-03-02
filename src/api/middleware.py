"""
API middleware for authentication, security, and request processing.

This module contains middleware components that handle:
- Authentication validation
- Permission checking
- Request logging
- Security headers
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable

from auth_module.auth_manager import AuthManager
from auth_module.permission_manager import PermissionManager
from logging.log_manager import LogManager
from utils.system.token_manager import decode_token, verify_token

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Initialize managers
auth_manager = AuthManager()
permission_manager = PermissionManager()
log_manager = LogManager()

class SecurityMiddleware:
    """Middleware for handling security concerns."""
    
    @staticmethod
    async def authenticate_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
        """
        Authenticate a user based on their JWT token.
        
        Args:
            token: The JWT token from the Authorization header
            
        Returns:
            Dict containing user information
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Verify the token is valid
            if not verify_token(token):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Decode the token to get user information
            payload = decode_token(token)
            
            # Check if the token has expired
            if datetime.utcnow() > datetime.fromtimestamp(payload.get("exp", 0)):
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Get the user ID from the token
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Validate the user exists in the system
            user = auth_manager.get_user(user_id)
            if user is None:
                raise HTTPException(
                    status_code=401,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            return user
            
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def check_permission(required_permission: str):
        """
        Create a dependency that checks if a user has the required permission.
        
        Args:
            required_permission: The permission string to check for
            
        Returns:
            A dependency function that raises an exception if permission is not granted
        """
        async def permission_checker(user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)):
            if not permission_manager.has_permission(user["id"], required_permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Not authorized to perform this action. Required permission: {required_permission}"
                )
            return user
        return permission_checker

    @staticmethod
    async def log_request(request: Request, call_next):
        """
        Log incoming API requests and their responses.
        
        Args:
            request: The incoming request
            call_next: The next handler in the middleware chain
            
        Returns:
            The response from the next handler
        """
        # Get request details
        start_time = datetime.utcnow()
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else None
        
        # Process the request through the rest of the middleware and route handlers
        response = await call_next(request)
        
        # Calculate request duration
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Log the request
        log_manager.log_api_request(
            method=method,
            url=url,
            status_code=response.status_code,
            duration=duration,
            client_ip=client_ip
        )
        
        return response