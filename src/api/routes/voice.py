"""
Voice commands API routes.

This module handles voice command processing, intent recognition,
and voice-related operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from voice_module.listener import VoiceListener
from voice_module.intent_handler import IntentHandler
from voice_module.speaker import Speaker
from api.middleware import SecurityMiddleware
from api.utils import success_response, error_response

# Initialize router
router = APIRouter()

# Initialize voice modules
voice_listener = VoiceListener()
intent_handler = IntentHandler()
speaker = Speaker()

# Models
class VoiceCommandRequest(BaseModel):
    """Voice command request model."""
    audio_data: str = Field(..., description="Base64 encoded audio data")
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class IntentData(BaseModel):
    """Intent data model."""
    name: str
    confidence: float
    parameters: Dict[str, Any] = {}

class VoiceCommandResponse(BaseModel):
    """Voice command response model."""
    transcription: str
    intent: IntentData
    response: str
    actions: List[Dict[str, Any]] = []

class TextCommandRequest(BaseModel):
    """Text command request model."""
    text: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class TrainingPhraseRequest(BaseModel):
    """Training phrase request model."""
    intent: str
    phrases: List[str]

@router.post("/command", response_model=VoiceCommandResponse)
async def process_voice_command(
    command: VoiceCommandRequest,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Process a voice command from audio data.
    
    Args:
        command: Voice command request with audio data
        user: Authenticated user information
        
    Returns:
        Processed command information
    """
    try:
        # Add user ID to context if not provided
        context = command.context or {}
        context["user_id"] = user["id"]
        
        # Transcribe audio
        transcription = voice_listener.transcribe_audio(command.audio_data)
        
        # Process intent
        intent_result = intent_handler.recognize_intent(
            text=transcription,
            user_id=user["id"],
            context=context
        )
        
        # Get response text
        response_text = intent_handler.generate_response(
            intent=intent_result["intent"],
            parameters=intent_result["parameters"],
            context=context
        )
        
        # Execute actions
        actions = intent_handler.execute_actions(
            intent=intent_result["intent"],
            parameters=intent_result["parameters"],
            user_id=user["id"],
            context=context
        )
        
        return VoiceCommandResponse(
            transcription=transcription,
            intent=IntentData(
                name=intent_result["intent"],
                confidence=intent_result["confidence"],
                parameters=intent_result["parameters"]
            ),
            response=response_text,
            actions=actions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice command: {str(e)}"
        )

@router.post("/text-command", response_model=VoiceCommandResponse)
async def process_text_command(
    command: TextCommandRequest,
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Process a text command.
    
    Args:
        command: Text command request
        user: Authenticated user information
        
    Returns:
        Processed command information
    """
    try:
        # Add user ID to context if not provided
        context = command.context or {}
        context["user_id"] = user["id"]
        
        # Process intent
        intent_result = intent_handler.recognize_intent(
            text=command.text,
            user_id=user["id"],
            context=context
        )
        
        # Get response text
        response_text = intent_handler.generate_response(
            intent=intent_result["intent"],
            parameters=intent_result["parameters"],
            context=context
        )
        
        # Execute actions
        actions = intent_handler.execute_actions(
            intent=intent_result["intent"],
            parameters=intent_result["parameters"],
            user_id=user["id"],
            context=context
        )
        
        return VoiceCommandResponse(
            transcription=command.text,
            intent=IntentData(
                name=intent_result["intent"],
                confidence=intent_result["confidence"],
                parameters=intent_result["parameters"]
            ),
            response=response_text,
            actions=actions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing text command: {str(e)}"
        )

@router.post("/train")
async def train_intent(
    training_data: TrainingPhraseRequest,
    user: Dict[str, Any] = Depends(SecurityMiddleware.check_permission("admin"))
):
    """
    Add training phrases for an intent.
    
    Args:
        training_data: Intent and training phrases
        user: Authenticated user with admin permission
        
    Returns:
        Success message
    """
    try:
        # Add training phrases
        intent_handler.add_training_phrases(
            intent=training_data.intent,
            phrases=training_data.phrases
        )
        
        return success_response(
            message=f"Successfully added {len(training_data.phrases)} training phrases to intent '{training_data.intent}'"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding training phrases: {str(e)}"
        )

@router.get("/intents")
async def get_intents(
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Get all available intents.
    
    Args:
        user: Authenticated user information
        
    Returns:
        List of intents
    """
    try:
        intents = intent_handler.get_intents()
        
        return success_response(
            message="Intents retrieved successfully",
            data=intents
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving intents: {str(e)}"
        )

@router.post("/speak")
async def text_to_speech(
    text: str = Body(...),
    voice_id: Optional[str] = Body(None),
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Convert text to speech.
    
    Args:
        text: Text to convert to speech
        voice_id: Optional voice ID to use
        user: Authenticated user information
        
    Returns:
        Base64 encoded audio data
    """
    try:
        # Convert text to speech
        audio_data = speaker.text_to_speech(text, voice_id)
        
        return success_response(
            message="Text converted to speech successfully",
            data={"audio_data": audio_data}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting text to speech: {str(e)}"
        )

@router.post("/enroll-voice")
async def enroll_voice_biometrics(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(SecurityMiddleware.authenticate_user)
):
    """
    Enroll user's voice for biometric authentication.
    
    Args:
        file: Audio file for voice enrollment
        user: Authenticated user information
        
    Returns:
        Success message
    """
    try:
        # Read audio file
        audio_data = await file.read()
        
        # Enroll voice
        from auth_module.voice_auth import VoiceAuthenticator
        voice_auth = VoiceAuthenticator()
        
        enrollment_success = voice_auth.enroll(
            user_id=user["id"],
            voice_sample=audio_data
        )
        
        if not enrollment_success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voice enrollment failed. Please try again with a clearer audio sample."
            )
        
        return success_response(
            message="Voice biometrics enrolled successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enrolling voice biometrics: {str(e)}"
        )