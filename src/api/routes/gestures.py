"""
Gesture controls API routes.

This module handles gesture detection, mapping, and configuration.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import base64
import numpy as np
import cv2

from gesture_module.detector import GestureDetector
from gesture_module.processor import GestureProcessor
from gesture_module.actions import ActionMapper
from api.middleware import SecurityMiddleware
from api.utils import success_response, error_response

# Initialize router
router = APIRouter()

# Initialize gesture modules
gesture_detector = GestureDetector()
gesture_processor = GestureProcessor()
action_mapper = ActionMapper()

# Models
class GestureData(BaseModel):
    """Gesture data model."""
    gesture_type: str
    confidence: float
    landmarks: List[Dict[str, float]]
    timestamp: float

class GestureActionMapping(BaseModel):
    """Gesture action mapping model."""
    gesture: str
    action: str
    parameters: Optional[Dict[str, Any]] = None

class GestureCommandRequest(BaseModel):
    """Gesture command request model."""
    image_data: str = Field(..., description="Base64 encoded image data")
    context: Optional[Dict[str, Any]] = None

class GestureCommandResponse(BaseModel):
    """Gesture command response model."""
    detected_gesture: Optional[GestureData] = None
    action: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    success: bool
    message: str

class CustomGestureRegistration(BaseModel):
    """Custom gesture registration model."""
    name: str
    sample_images: List[str] = Field(..., description="List of base64 encoded images")
    user_id: Optional[str] = None

@router.post("/detect", response_model=GestureCommandResponse)
async def detect_gesture(
    command: GestureCommandRequest,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Detect and process a gesture from an image.
    
    Args:
        command: Gesture command request with image data
        user: Authenticated user information
        
    Returns:
        Detected gesture and action information
    """
    try:
        # Decode image
        image_bytes = base64.b64decode(command.image_data)
        image_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        # Add user ID to context if not provided
        context = command.context or {}
        context["user_id"] = user["id"]
        
        # Detect gesture
        detection_result = gesture_detector.detect(image)
        
        # No gesture detected
        if not detection_result:
            return GestureCommandResponse(
                success=False,
                message="No gesture detected"
            )
        
        # Process gesture
        processed_gesture = gesture_processor.process(
            detection_result,
            user_id=user["id"],
            context=context
        )
        
        # Map gesture to action
        action_result = action_mapper.map_action(
            gesture=processed_gesture["gesture_type"],
            user_id=user["id"],
            context=context
        )
        
        # Execute action if needed
        if action_result["action"] and context.get("execute_action", True):
            action_mapper.execute_action(
                action=action_result["action"],
                parameters=action_result["parameters"],
                user_id=user["id"],
                context=context
            )
        
        return GestureCommandResponse(
            detected_gesture=GestureData(
                gesture_type=processed_gesture["gesture_type"],
                confidence=processed_gesture["confidence"],
                landmarks=processed_gesture["landmarks"],
                timestamp=processed_gesture["timestamp"]
            ),
            action=action_result["action"],
            parameters=action_result["parameters"],
            success=True,
            message="Gesture detected and processed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing gesture: {str(e)}"
        )

@router.get("/actions")
async def get_gesture_actions(
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Get all gesture-to-action mappings for a user.
    
    Args:
        user: Authenticated user information
        
    Returns:
        List of gesture-action mappings
    """
    try:
        # Get gesture mappings
        mappings = action_mapper.get_user_mappings(user["id"])
        
        return success_response(
            message="Gesture action mappings retrieved successfully",
            data=mappings
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving gesture action mappings: {str(e)}"
        )

@router.post("/map-action")
async def map_gesture_to_action(
    mapping: GestureActionMapping,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Map a gesture to an action.
    
    Args:
        mapping: Gesture-action mapping information
        user: Authenticated user information
        
    Returns:
        Success message
    """
    try:
        # Map gesture to action
        action_mapper.add_mapping(
            user_id=user["id"],
            gesture=mapping.gesture,
            action=mapping.action,
            parameters=mapping.parameters
        )
        
        return success_response(
            message=f"Successfully mapped gesture '{mapping.gesture}' to action '{mapping.action}'"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error mapping gesture to action: {str(e)}"
        )

@router.delete("/unmap-action/{gesture}")
async def unmap_gesture_action(
    gesture: str,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Remove a gesture-to-action mapping.
    
    Args:
        gesture: Gesture name to unmap
        user: Authenticated user information
        
    Returns:
        Success message
    """
    try:
        # Remove mapping
        success = action_mapper.remove_mapping(
            user_id=user["id"],
            gesture=gesture
        )
        
        if not success:
            return error_response(
                message=f"No mapping found for gesture '{gesture}'"
            )
        
        return success_response(
            message=f"Successfully removed mapping for gesture '{gesture}'"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing gesture mapping: {str(e)}"
        )

@router.get("/available-gestures")
async def get_available_gestures(
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Get all available gestures.
    
    Args:
        user: Authenticated user information
        
    Returns:
        List of available gestures
    """
    try:
        # Get gestures (both system and user-defined)
        gestures = gesture_detector.get_available_gestures(user["id"])
        
        return success_response(
            message="Available gestures retrieved successfully",
            data=gestures
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving available gestures: {str(e)}"
        )

@router.post("/register-custom-gesture")
async def register_custom_gesture(
    custom_gesture: CustomGestureRegistration,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Register a custom gesture for a user.
    
    Args:
        custom_gesture: Custom gesture registration information
        user: Authenticated user information
        
    Returns:
        Success message
    """
    try:
        # Process sample images
        sample_images = []
        for image_data in custom_gesture.sample_images:
            # Decode image
            image_bytes = base64.b64decode(image_data)
            image_array = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            sample_images.append(image)
        
        # Register custom gesture
        success = gesture_detector.register_custom_gesture(
            name=custom_gesture.name,
            user_id=user["id"],
            sample_images=sample_images
        )
        
        if not success:
            return error_response(
                message="Failed to register custom gesture. Please provide clearer samples."
            )
        
        return success_response(
            message=f"Custom gesture '{custom_gesture.name}' registered successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering custom gesture: {str(e)}"
        )

@router.delete("/custom-gesture/{gesture_name}")
async def delete_custom_gesture(
    gesture_name: str,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Delete a custom gesture.
    
    Args:
        gesture_name: Name of the custom gesture to delete
        user: Authenticated user information
        
    Returns:
        Success message
    """
    try:
        # Delete custom gesture
        success = gesture_detector.delete_custom_gesture(
            name=gesture_name,
            user_id=user["id"]
        )
        
        if not success:
            return error_response(
                message=f"Custom gesture '{gesture_name}' not found or cannot be deleted"
            )
        
        # Also remove any mappings for this gesture
        action_mapper.remove_mapping(
            user_id=user["id"],
            gesture=gesture_name
        )
        
        return success_response(
            message=f"Custom gesture '{gesture_name}' deleted successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting custom gesture: {str(e)}"
        )

@router.post("/calibrate")
async def calibrate_gestures(
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Calibrate the gesture detection system for the user.
    
    Args:
        user: Authenticated user information
        
    Returns:
        Success message
    """
    try:
        # Start calibration process
        # In a real implementation, this might return a session ID or
        # instructions for the calibration process
        calibration_data = gesture_detector.start_calibration(user["id"])
        
        return success_response(
            message="Gesture calibration initiated",
            data=calibration_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating gesture calibration: {str(e)}"
        )