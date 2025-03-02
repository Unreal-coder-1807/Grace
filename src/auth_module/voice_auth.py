"""
Voice-based authentication module for gesture-voice control system.
Provides biometric authentication using voice recognition.
"""
import os
import numpy as np
from typing import Dict, Any, Optional
from sys import time
from ..logging.log_manager import get_logger
from ..voice_module.voice_authentication import VoiceFeatureExtractor, VoiceMatcher
from ..database.user_store import UserStore

logger = get_logger(__name__)

class VoiceAuthenticator:
    """Handles voice-based authentication."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the voice authenticator.
        
        Args:
            config_path: Optional path to voice auth configuration file
        """
        self.user_store = UserStore()
        self.config = self._load_config(config_path)
        
        # Initialize voice feature extractor and matcher
        self.feature_extractor = VoiceFeatureExtractor()
        self.voice_matcher = VoiceMatcher(self.config['similarity_threshold'])
        
        logger.info("Voice authenticator initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load voice authentication configuration."""
        if not config_path:
            config_path = os.path.join("config", "settings", "auth.yaml")
            
        # TODO: Implement config loading logic
        # For now, return default configuration
        return {
            'similarity_threshold': 0.85,  # Minimum similarity score for authentication
            'voice_profiles_path': os.path.join("data", "biometric"),
            'min_audio_length': 3.0,  # Minimum audio length in seconds
            'max_attempts': 3
        }
    
    def authenticate(self, username: str, audio_data: Dict[str, Any]) -> bool:
        """
        Authenticate a user using voice biometrics.
        
        Args:
            username: Username to authenticate
            audio_data: Dictionary containing audio data
                {
                    'audio': numpy array of audio samples,
                    'sample_rate': sample rate of the audio
                }
            
        Returns:
            True if authentication successful, False otherwise
        """
        # Check if user exists
        user = self.user_store.get_user(username)
        if not user:
            logger.warning(f"Voice authentication failed: User {username} not found")
            return False
        
        # Check if user has a voice profile
        voice_profile_path = user.get('voice_profile')
        if not voice_profile_path:
            logger.warning(f"Voice authentication failed: No voice profile for user {username}")
            return False
        
        try:
            # Load user's voice profile
            voice_profile = self._load_voice_profile(voice_profile_path)
            if voice_profile is None:
                logger.error(f"Failed to load voice profile for user {username}")
                return False
            
            # Extract features from input audio
            audio = audio_data.get('audio')
            sample_rate = audio_data.get('sample_rate', 16000)
            
            if audio is None:
                logger.warning("Voice authentication failed: No audio data provided")
                return False
            
            # Check audio length
            audio_length = len(audio) / sample_rate
            if audio_length < self.config['min_audio_length']:
                logger.warning(f"Voice authentication failed: Audio too short ({audio_length:.2f}s)")
                return False
            
            # Extract features from the input audio
            features = self.feature_extractor.extract_features(audio, sample_rate)
            
            # Compare with stored profile
            similarity = self.voice_matcher.compare(features, voice_profile)
            
            if similarity >= self.config['similarity_threshold']:
                logger.info(f"Voice authentication successful for user {username}")
                return True
            else:
                logger.warning(f"Voice authentication failed for user {username}: Similarity {similarity:.2f} below threshold")
                return False
                
        except Exception as e:
            logger.error(f"Voice authentication error: {str(e)}")
            return False
    
    def _load_voice_profile(self, profile_path: str) -> Optional[np.ndarray]:
        """
        Load a voice profile from disk.
        
        Args:
            profile_path: Path to the voice profile file
            
        Returns:
            Voice profile features as a numpy array, or None if loading fails
        """
        try:
            # Ensure path is absolute if not already
            if not os.path.isabs(profile_path):
                profile_path = os.path.join(
                    self.config['voice_profiles_path'],
                    profile_path
                )
            
            # Load the profile
            if os.path.exists(profile_path):
                return np.load(profile_path)
            else:
                logger.error(f"Voice profile not found: {profile_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading voice profile: {str(e)}")
            return None
    
    def enroll_user(self, username: str, audio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enroll a user for voice authentication.
        
        Args:
            username: Username to enroll
            audio_data: Dictionary containing audio data
                {
                    'audio': numpy array of audio samples,
                    'sample_rate': sample rate of the audio
                }
            
        Returns:
            Status of enrollment operation
        """
        # Check if user exists
        user = self.user_store.get_user(username)
        if not user:
            logger.warning(f"Voice enrollment failed: User {username} not found")
            return {"success": False, "error": "User not found"}
        
        try:
            # Extract audio data
            audio = audio_data.get('audio')
            sample_rate = audio_data.get('sample_rate', 16000)
            
            if audio is None:
                return {"success": False, "error": "No audio data provided"}
            
            # Check audio length
            audio_length = len(audio) / sample_rate
            if audio_length < self.config['min_audio_length']:
                return {
                    "success": False, 
                    "error": f"Audio too short ({audio_length:.2f}s). Need at least {self.config['min_audio_length']}s"
                }
            
            # Extract features
            features = self.feature_extractor.extract_features(audio, sample_rate)
            
            # Generate profile file name
            profile_filename = f"{username}_{int(time.time())}.npy"
            profile_path = os.path.join(
                self.config['voice_profiles_path'],
                profile_filename
            )
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(profile_path), exist_ok=True)
            
            # Save the profile
            np.save(profile_path, features)
            
            # Update user record with voice profile path
            success = self.user_store.update_user(
                username,
                {"voice_profile": profile_filename}
            )
            
            if success:
                logger.info(f"Voice enrollment successful for user {username}")
                return {"success": True, "profile_path": profile_filename}
            else:
                logger.error(f"Failed to update user {username} with voice profile")
                # Delete the saved profile if user update failed
                if os.path.exists(profile_path):
                    os.remove(profile_path)
                return {"success": False, "error": "Database error"}
                
        except Exception as e:
            logger.error(f"Voice enrollment error: {str(e)}")
            return {"success": False, "error": str(e)}