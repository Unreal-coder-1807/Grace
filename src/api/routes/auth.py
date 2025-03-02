"""
Authentication API routes.

This module handles user authentication, token management, and registration.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Any, Optional

from auth_module.auth_manager import AuthManager
from auth_module.voice_auth import VoiceAuthenticator
from api.middleware import SecurityMiddleware
from api.utils import success_response, error_response

# Initialize router
router = APIRouter()

# Initialize managers
auth_manager = AuthManager()
voice_auth = VoiceAuthenticator()

# Models
class UserCredentials(BaseModel):
    """User login credentials model."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    username: str
    permissions: list

class UserRegistration(BaseModel):
    """User registration model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class VoiceAuthRequest(BaseModel):
    """Voice authentication request model."""
    username: str
    voice_sample: str  # Base64 encoded audio data

@router.post("/token", response_model=TokenResponse)
async def login(credentials: UserCredentials):
    """
    Authenticate user and issue access token.
    
    Args:
        credentials: Username and password
        
    Returns:
        Access token information
    """
    user = auth_manager.authenticate(
        username=credentials.username,
        password=credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token
    token_data = auth_manager.create_access_token(user_id=user["id"])
    
    # Get user permissions
    permissions = auth_manager.get_user_permissions(user["id"])
    
    return {
        "access_token": token_data["token"],
        "token_type": "bearer",
        "expires_in": token_data["expires_in"],
        "user_id": user["id"],
        "username": user["username"],
        "permissions": permissions
    }

@router.post("/voice-auth", response_model=TokenResponse)
async def voice_login(auth_request: VoiceAuthRequest):
    """
    Authenticate user using voice biometrics.
    
    Args:
        auth_request: Username and voice sample
        
    Returns:
        Access token information if authentication successful
    """
    # Authenticate using voice biometrics
    is_authenticated = voice_auth.authenticate(
        username=auth_request.username,
        voice_sample=auth_request.voice_sample
    )
    
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Voice authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user details
    user = auth_manager.get_user_by_username(auth_request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate token
    token_data = auth_manager.create_access_token(user_id=user["id"])
    
    # Get user permissions
    permissions = auth_manager.get_user_permissions(user["id"])
    
    return {
        "access_token": token_data["token"],
        "token_type": "bearer",
        "expires_in": token_data["expires_in"],
        "user_id": user["id"],
        "username": user["username"],
        "permissions": permissions
    }

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegistration):
    """
    Register a new user.
    
    Args:
        user_data: User registration information
        
    Returns:
        Success message
    """
    # Check if username already exists
    if auth_manager.get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # Check if email already exists
    if auth_manager.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )
    
    # Create the new user
    user_id = auth_manager.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    return success_response(
        message="User registered successfully",
        data={"user_id": user_id}
    )

@router.post("/logout")
async def logout(user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)):
    """
    Logout user by invalidating their current token.
    
    Args:
        user: Authenticated user information
        
    Returns:
        Success message
    """
    # Invalidate the token
    auth_manager.invalidate_token(user["id"])
    
    return success_response(message="Logged out successfully")

@router.get("/me")
async def get_current_user(user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)):
    """
    Get current user information.
    
    Args:
        user: Authenticated user information
        
    Returns:
        User details
    """
    # Remove sensitive information
    user_info = {k: v for k, v in user.items() if k != "password_hash"}
    
    # Add user permissions
    user_info["permissions"] = auth_manager.get_user_permissions(user["id"])
    
    return success_response(
        message="User information retrieved successfully",
        data=user_info
    )

@router.post("/change-password")
async def change_password(
    current_password: str = Body(...),
    new_password: str = Body(..., min_length=8),
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Change user password.
    
    Args:
        current_password: Current password for verification
        new_password: New password
        user: Authenticated user information
        
    Returns:
        Success message
    """
    # Verify current password
    if not auth_manager.verify_password(current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    auth_manager.update_password(user["id"], new_password)
    
    return success_response(message="Password changed successfully")

@router.post("/reset-password-request")
async def request_password_reset(email: str = Body(...)):
    """
    Request password reset.
    
    Args:
        email: User's email address
        
    Returns:
        Success message
    """
    # Check if email exists
    user = auth_manager.get_user_by_email(email)
    if not user:
        # Return success even if email doesn't exist to prevent email enumeration
        return success_response(
            message="If your email is registered, you will receive a password reset link"
        )
    
    # Generate password reset token
    reset_token = auth_manager.create_password_reset_token(user["id"])
    
    # TODO: Send email with reset token (would be handled by an email service)
    
    return success_response(
        message="If your email is registered, you will receive a password reset link"
    )

@router.post("/reset-password")
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(..., min_length=8)
):
    """
    Reset password using reset token.
    
    Args:
        token: Password reset token
        new_password: New password
        
    Returns:
        Success message
    """
    # Verify and use reset token
    user_id = auth_manager.verify_password_reset_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Update password
    auth_manager.update_password(user_id, new_password)
    
    # Invalidate all existing tokens for this user
    auth_manager.invalidate_all_tokens(user_id)
    
    return success_response(message="Password reset successfully")