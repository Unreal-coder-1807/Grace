"""
Voice-based authentication module.

This module provides functionality for authenticating users based on voice biometrics.
It works with the auth_module to provide voice authentication capabilities.
"""

import os
import numpy as np
import logging
from typing import Tuple, Dict, List, Optional, Union, Any
from pathlib import Path
import json
import pickle
from datetime import datetime, timedelta

from .utils import (
    record_audio, 
    save_audio, 
    load_audio, 
    extract_audio_features, 
    normalize_audio,
    ensure_dir_exists
)

# Import from auth_module for integration
from ..auth_module.auth_manager import AuthManager
from ..logging.log_manager import LogManager

# Set up logger
logger = logging.getLogger(__name__)

class VoiceAuthenticator:
    """Voice biometric authentication system."""
    
    def __init__(self, 
                 biometric_dir: str = 'data/biometric',
                 auth_manager: Optional[AuthManager] = None,
                 threshold: float = 0.75,
                 sample_duration: int = 5):
        """
        Initialize voice authenticator.
        
        Args:
            biometric_dir: Directory to store voice biometric data
            auth_manager: AuthManager instance for integration with auth system
            threshold: Similarity threshold for authentication
            sample_duration: Duration of voice sample recording in seconds
        """
        self.biometric_dir = ensure_dir_exists(biometric_dir)
        self.auth_manager = auth_manager
        self.threshold = threshold
        self.sample_duration = sample_duration
        self.log_manager = LogManager() if LogManager else None
        
        # Cache for voice profiles
        self._voice_profiles = {}
        
        logger.info("Voice authenticator initialized")
    
    def register_user(self, user_id: str, username: str) -> bool:
        """
        Register a new user for voice authentication.
        
        Args:
            user_id: Unique user identifier
            username: User's name for display purposes
            
        Returns:
            Boolean indicating success
        """
        logger.info(f"Registering user {username} for voice authentication")
        
        try:
            # Record voice sample
            voice_data = record_audio(duration=self.sample_duration)
            
            # Extract features
            features = extract_audio_features(normalize_audio(voice_data))
            
            # Create user profile
            user_profile = {
                'user_id': user_id,
                'username': username,
                'features': features.tolist(),
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'samples_count': 1
            }
            
            # Save profile
            profile_path = self._get_user_profile_path(user_id)
            with open(profile_path, 'w') as f:
                json.dump(user_profile, f)
            
            # Save voice sample
            sample_path = self._get_user_sample_path(user_id)
            save_audio(voice_data, sample_path)
            
            # Update cache
            self._voice_profiles[user_id] = user_profile
            
            if self.log_manager:
                self.log_manager.log_event(
                    'voice_auth', 
                    f"User {username} registered for voice authentication",
                    user_id=user_id
                )
            
            logger.info(f"User {username} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register user: {str(e)}")
            return False
    
    def authenticate(self, claimed_user_id: str) -> Tuple[bool, float]:
        """
        Authenticate a user using voice biometrics.
        
        Args:
            claimed_user_id: The user ID to authenticate
            
        Returns:
            Tuple of (is_authenticated, confidence_score)
        """
        logger.info(f"Authenticating user {claimed_user_id}")
        
        try:
            # Check if user profile exists
            profile_path = self._get_user_profile_path(claimed_user_id)
            if not os.path.exists(profile_path):
                logger.warning(f"No voice profile found for user {claimed_user_id}")
                return False, 0.0
            
            # Load user profile
            user_profile = self._get_user_profile(claimed_user_id)
            if not user_profile:
                return False, 0.0
            
            # Record voice sample for authentication
            logger.info("Please speak for voice authentication")
            auth_voice = record_audio(duration=self.sample_duration)
            
            # Extract features
            auth_features = extract_audio_features(normalize_audio(auth_voice))
            
            # Compare features
            stored_features = np.array(user_profile['features'])
            similarity = self._calculate_similarity(stored_features, auth_features)
            
            # Authentication decision
            is_authenticated = similarity >= self.threshold
            
            # Log authentication attempt
            if self.log_manager:
                self.log_manager.log_event(
                    'voice_auth', 
                    f"Authentication {'successful' if is_authenticated else 'failed'} for user {claimed_user_id}",
                    user_id=claimed_user_id,
                    success=is_authenticated,
                    confidence=similarity
                )
            
            if is_authenticated:
                logger.info(f"User {claimed_user_id} authenticated successfully")
                
                # Update voice profile with new sample if authentication is successful
                if similarity > 0.9:  # Only update if very good match
                    self._update_voice_profile(claimed_user_id, auth_features, auth_voice)
            else:
                logger.warning(f"Authentication failed for user {claimed_user_id}")
            
            return is_authenticated, similarity
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False, 0.0
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user's voice profile.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            Boolean indicating success
        """
        try:
            # Delete profile file
            profile_path = self._get_user_profile_path(user_id)
            if os.path.exists(profile_path):
                os.remove(profile_path)
            
            # Delete sample file
            sample_path = self._get_user_sample_path(user_id)
            if os.path.exists(sample_path):
                os.remove(sample_path)
            
            # Remove from cache
            if user_id in self._voice_profiles:
                del self._voice_profiles[user_id]
            
            # Log deletion
            if self.log_manager:
                self.log_manager.log_event(
                    'voice_auth', 
                    f"Voice profile deleted for user {user_id}",
                    user_id=user_id
                )
            
            logger.info(f"Voice profile deleted for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete user profile: {str(e)}")
            return False
    
    def update_profile(self, user_id: str) -> bool:
        """
        Update a user's voice profile with a new sample.
        
        Args:
            user_id: User ID to update
            
        Returns:
            Boolean indicating success
        """
        try:
            # Check if user profile exists
            profile_path = self._get_user_profile_path(user_id)
            if not os.path.exists(profile_path):
                logger.warning(f"No voice profile found for user {user_id}")
                return False
            
            # Record new voice sample
            logger.info("Please speak to update your voice profile")
            new_voice = record_audio(duration=self.sample_duration)
            
            # Extract features
            new_features = extract_audio_features(normalize_audio(new_voice))
            
            # Update profile
            return self._update_voice_profile(user_id, new_features, new_voice)
            
        except Exception as e:
            logger.error(f"Failed to update profile: {str(e)}")
            return False
    
    def _update_voice_profile(self, user_id: str, new_features: np.ndarray, voice_sample: np.ndarray) -> bool:
        """
        Update a user's voice profile with new features.
        
        Args:
            user_id: User ID to update
            new_features: New feature vector
            voice_sample: Raw voice sample
            
        Returns:
            Boolean indicating success
        """
        try:
            # Get current profile
            user_profile = self._get_user_profile(user_id)
            if not user_profile:
                return False
            
            # Update features (average with existing)
            current_features = np.array(user_profile['features'])
            samples_count = user_profile['samples_count']
            
            # Weighted average
            updated_features = (
                (current_features * samples_count + new_features) / (samples_count + 1)
            )
            
            # Update profile
            user_profile['features'] = updated_features.tolist()
            user_profile['samples_count'] += 1
            user_profile['last_updated'] = datetime.now().isoformat()
            
            # Save updated profile
            profile_path = self._get_user_profile_path(user_id)
            with open(profile_path, 'w') as f:
                json.dump(user_profile, f)
            
            # Save new voice sample (optional - could keep multiple samples)
            sample_path = self._get_user_sample_path(user_id)
            save_audio(voice_sample, sample_path)
            
            # Update cache
            self._voice_profiles[user_id] = user_profile
            
            logger.info(f"Voice profile updated for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update voice profile: {str(e)}")
            return False
    
    def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user's voice profile.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile dictionary or None if not found
        """
        # Check cache first
        if user_id in self._voice_profiles:
            return self._voice_profiles[user_id]
        
        # Load from file
        profile_path = self._get_user_profile_path(user_id)
        if not os.path.exists(profile_path):
            return None
        
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)
                
            # Add to cache
            self._voice_profiles[user_id] = profile
            return profile
        
        except Exception as e:
            logger.error(f"Failed to load user profile: {str(e)}")
            return None
    
    def _get_user_profile_path(self, user_id: str) -> str:
        """Get the path to a user's profile file."""
        return os.path.join(self.biometric_dir, f"{user_id}_profile.json")
    
    def _get_user_sample_path(self, user_id: str) -> str:
        """Get the path to a user's voice sample file."""
        return os.path.join(self.biometric_dir, f"{user_id}_sample.wav")
    
    def _calculate_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Calculate similarity between two feature vectors.
        
        This is a simple implementation using cosine similarity.
        In a production system, more sophisticated methods would be used.
        
        Args:
            features1: First feature vector
            features2: Second feature vector
            
        Returns:
            Similarity score between 0 and 1
        """
        # Normalize vectors
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity
        similarity = np.dot(features1, features2) / (norm1 * norm2)
        
        # Convert to range 0-1
        similarity = (similarity + 1) / 2
        
        return similarity

def get_voice_authenticator(auth_manager: Optional[AuthManager] = None) -> VoiceAuthenticator:
    """
    Factory function to get a VoiceAuthenticator instance.
    
    Args:
        auth_manager: Optional AuthManager instance for integration
        
    Returns:
        VoiceAuthenticator instance
    """
    return VoiceAuthenticator(auth_manager=auth_manager)