"""
System control API routes.

This module handles system-level operations like keyboard/mouse control,
volume adjustment, browser automation, and general system controls.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union

from control_system.keyboard_control import KeyboardController
from control_system.mouse_control import MouseController
from control_system.volume_control import VolumeController
from control_system.browser_control import BrowserController
from control_system.system_control import SystemController
from control_system.access_control import AccessController
from api.middleware import SecurityMiddleware
from api.utils import success_response, error_response

# Initialize router
router = APIRouter()

# Initialize controllers
keyboard_controller = KeyboardController()
mouse_controller = MouseController()
volume_controller = VolumeController()
browser_controller = BrowserController()
system_controller = SystemController()
access_controller = AccessController()

# Models
class KeyboardAction(BaseModel):
    """Keyboard action model."""
    action_type: str = Field(..., description="Type: 'press', 'release', 'type', 'hotkey'")
    keys: Union[str, List[str]]
    duration: Optional[float] = None

class MouseAction(BaseModel):
    """Mouse action model."""
    action_type: str = Field(..., description="Type: 'move', 'click', 'drag', 'scroll'")
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[str] = None
    clicks: Optional[int] = 1
    duration: Optional[float] = None
    relative: Optional[bool] = False
    scroll_amount: Optional[int] = None

class VolumeAction(BaseModel):
    """Volume action model."""
    action_type: str = Field(..., description="Type: 'set', 'increase', 'decrease', 'mute', 'unmute'")
    value: Optional[int] = None
    application: Optional[str] = None

class BrowserAction(BaseModel):
    """Browser action model."""
    action_type: str = Field(..., description="Type: 'open', 'navigate', 'click', 'type', 'close'")
    url: Optional[str] = None
    selector: Optional[str] = None
    text: Optional[str] = None
    browser: Optional[str] = "default"

class SystemAction(BaseModel):
    """System action model."""
    action_type: str = Field(..., description="Type: 'sleep', 'shutdown', 'restart', 'lock', 'launch', 'close'")
    application: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    delay: Optional[int] = None

@router.post("/keyboard")
async def execute_keyboard_action(
    action: KeyboardAction,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Execute a keyboard action.
    
    Args:
        action: Keyboard action details
        user: Authenticated user information
        
    Returns:
        Success message
    """
    # Check permission
    if not access_controller.can_access_keyboard(user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to control the keyboard"
        )
    
    try:
        if action.action_type == "press":
            keyboard_controller.press_key(action.keys)
        elif action.action_type == "release":
            keyboard_controller.release_key(action.keys)
        elif action.action_type == "type":
            keyboard_controller.type_text(action.keys)
        elif action.action_type == "hotkey":
            keyboard_controller.hotkey(action.keys)
        else:
            return error_response(
                message=f"Unknown keyboard action type: {action.action_type}"
            )
        
        return success_response(
            message=f"Keyboard action '{action.action_type}' executed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing keyboard action: {str(e)}"
        )

@router.post("/mouse")
async def execute_mouse_action(
    action: MouseAction,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Execute a mouse action.
    
    Args:
        action: Mouse action details
        user: Authenticated user information
        
    Returns:
        Success message
    """
    # Check permission
    if not access_controller.can_access_mouse(user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to control the mouse"
        )
    
    try:
        if action.action_type == "move":
            mouse_controller.move(
                x=action.x,
                y=action.y,
                duration=action.duration,
                relative=action.relative
            )
        elif action.action_type == "click":
            mouse_controller.click(
                x=action.x,
                y=action.y,
                button=action.button,
                clicks=action.clicks
            )
        elif action.action_type == "drag":
            mouse_controller.drag(
                start_x=action.x,
                start_y=action.y,
                end_x=action.x + (action.scroll_amount or 0),
                end_y=action.y + (action.scroll_amount or 0),
                duration=action.duration
            )
        elif action.action_type == "scroll":
            mouse_controller.scroll(
                amount=action.scroll_amount
            )
        else:
            return error_response(
                message=f"Unknown mouse action type: {action.action_type}"
            )
        
        return success_response(
            message=f"Mouse action '{action.action_type}' executed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing mouse action: {str(e)}"
        )

@router.post("/volume")
async def execute_volume_action(
    action: VolumeAction,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Execute a volume control action.
    
    Args:
        action: Volume action details
        user: Authenticated user information
        
    Returns:
        Success message
    """
    # Check permission
    if not access_controller.can_access_system(user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to control system volume"
        )
    
    try:
        if action.action_type == "set":
            volume_controller.set_volume(
                level=action.value,
                application=action.application
            )
        elif action.action_type == "increase":
            volume_controller.increase_volume(
                amount=action.value,
                application=action.application
            )
        elif action.action_type == "decrease":
            volume_controller.decrease_volume(
                amount=action.value,
                application=action.application
            )
        elif action.action_type == "mute":
            volume_controller.mute(
                application=action.application
            )
        elif action.action_type == "unmute":
            volume_controller.unmute(
                application=action.application
            )
        else:
            return error_response(
                message=f"Unknown volume action type: {action.action_type}"
            )
        
        return success_response(
            message=f"Volume action '{action.action_type}' executed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing volume action: {str(e)}"
        )

@router.post("/browser")
async def execute_browser_action(
    action: BrowserAction,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Execute a browser control action.
    
    Args:
        action: Browser action details
        user: Authenticated user information
        
    Returns:
        Success message and any result data
    """
    # Check permission
    if not access_controller.can_access_browser(user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to control the browser"
        )
    
    try:
        result = None
        
        if action.action_type == "open":
            browser_controller.open_browser(
                browser=action.browser
            )
        elif action.action_type == "navigate":
            browser_controller.navigate(
                url=action.url
            )
        elif action.action_type == "click":
            browser_controller.click_element(
                selector=action.selector
            )
        elif action.action_type == "type":
            browser_controller.type_text(
                selector=action.selector,
                text=action.text
            )
        elif action.action_type == "close":
            browser_controller.close_browser()
        else:
            return error_response(
                message=f"Unknown browser action type: {action.action_type}"
            )
        
        return success_response(
            message=f"Browser action '{action.action_type}' executed successfully",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing browser action: {str(e)}"
        )

@router.post("/system")
async def execute_system_action(
    action: SystemAction,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Execute a system control action.
    
    Args:
        action: System action details
        user: Authenticated user information
        
    Returns:
        Success message
    """
    # Check permission for system-level commands
    if not access_controller.can_access_system(user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to control system functions"
        )
    
    try:
        # Extra validation for potentially destructive actions
        if action.action_type in ["shutdown", "restart"]:
            if not access_controller.has_permission(user["id"], "system:power"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to power off or restart the system"
                )
        
        if action.action_type == "sleep":
            system_controller.sleep()
        elif action.action_type == "shutdown":
            system_controller.shutdown(delay=action.delay)
        elif action.action_type == "restart":
            system_controller.restart(delay=action.delay)
        elif action.action_type == "lock":
            system_controller.lock()
        elif action.action_type == "launch":
            system_controller.launch_application(
                application=action.application,
                params=action.params
            )
        elif action.action_type == "close":
            system_controller.close_application(
                application=action.application
            )
        else:
            return error_response(
                message=f"Unknown system action type: {action.action_type}"
            )
        
        return success_response(
            message=f"System action '{action.action_type}' executed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing system action: {str(e)}"
        )

@router.get("/permissions")
async def get_user_permissions(
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Get current user's system control permissions.
    
    Args:
        user: Authenticated user information
        
    Returns:
        User's permissions
    """
    try:
        # Get user permissions
        permissions = access_controller.get_user_permissions(user["id"])
        
        return success_response(
            message="User permissions retrieved successfully",
            data=permissions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user permissions: {str(e)}"
        )

@router.put("/permissions/{user_id}")
async def update_user_permissions(
    user_id: str,
    permissions: Dict[str, bool],
    user: Dict[str, Any] = Depends(SecurityMiddleware.check_permission("admin"))
):
    """
    Update a user's permissions. Requires admin privileges.
    
    Args:
        user_id: ID of the user to update
        permissions: Dictionary of permission keys and boolean values
        user: Authenticated admin user
        
    Returns:
        Success message
    """
    try:
        # Update user permissions
        success = access_controller.update_permissions(
            user_id=user_id,
            permissions=permissions
        )
        
        if not success:
            return error_response(
                message=f"Failed to update permissions for user {user_id}"
            )
        
        return success_response(
            message=f"Permissions updated successfully for user {user_id}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user permissions: {str(e)}"
        )