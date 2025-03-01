"""
Gesture processing module.

This module processes the detected hand landmarks to recognize specific gestures
and provides a high-level gesture recognition interface.
"""

import numpy as np
import logging
import math
from typing import Dict, List, Tuple, Optional, Any, Union
import json
import os
from pathlib import Path

# Set up logger
logger = logging.getLogger(__name__)

class GestureProcessor:
    """Process hand landmarks to recognize gestures."""
    
    # Finger indices in MediaPipe hand landmarks
    FINGER_TIPS = [4, 8, 12, 16, 20]  # Thumb, index, middle, ring, pinky tips
    FINGER_PIPS = [3, 7, 11, 15, 19]  # Middle joints (PIP)
    FINGER_MCPS = [2, 6, 10, 14, 18]  # Knuckles (MCP)
    FINGER_NAMES = ['thumb', 'index', 'middle', 'ring', 'pinky']
    
    # Wrist landmark
    WRIST = 0
    
    def __init__(self, gesture_config_path: Optional[str] = None):
        """
        Initialize the gesture processor.
        
        Args:
            gesture_config_path: Path to gesture configuration file
        """
        self.gestures = {}
        
        # Default gesture parameters
        self.default_params = {
            'finger_open_threshold': 0.3,  # Distance threshold for open fingers
            'pointing_angle_threshold': 30.0,  # Angle threshold for pointing gesture
            'pinch_distance_threshold': 0.05,  # Distance threshold for pinch gesture
            'grab_threshold': 0.15,  # Threshold for grab gesture
        }
        
        # Load custom gesture configurations if provided
        if gesture_config_path and os.path.exists(gesture_config_path):
            self._load_gesture_config(gesture_config_path)
        else:
            # Initialize default gestures
            self._initialize_default_gestures()
        
        logger.info("GestureProcessor initialized")
    
    def _load_gesture_config(self, config_path: str) -> None:
        """
        Load gesture configuration from file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update default parameters
            if 'parameters' in config:
                self.default_params.update(config['parameters'])
            
            # Load gesture definitions
            if 'gestures' in config:
                self.gestures = config['gestures']
            
            logger.info(f"Loaded gesture configuration from {config_path}")
        
        except Exception as e:
            logger.error(f"Failed to load gesture configuration: {str(e)}")
            # Fall back to default gestures
            self._initialize_default_gestures()
    
    def _initialize_default_gestures(self) -> None:
        """Initialize default gesture definitions."""
        self.gestures = {
            'open_palm': {
                'description': 'All fingers extended',
                'function': self._detect_open_palm
            },
            'fist': {
                'description': 'All fingers closed',
                'function': self._detect_fist
            },
            'pointing': {
                'description': 'Index finger pointing',
                'function': self._detect_pointing
            },
            'pinch': {
                'description': 'Thumb and index finger pinching',
                'function': self._detect_pinch
            },
            'grab': {
                'description': 'Fingers curled as if grabbing',
                'function': self._detect_grab
            },
            'thumbs_up': {
                'description': 'Thumb up, other fingers closed',
                'function': self._detect_thumbs_up
            },
            'swipe': {
                'description': 'Horizontal hand movement',
                'function': self._detect_swipe
            },
            'wave': {
                'description': 'Waving hand',
                'function': self._detect_wave
            }
        }
    
    def process_landmarks(self, landmarks: List[Tuple[int, int, float]], 
                         handedness: str = 'Right') -> Dict[str, Any]:
        """
        Process hand landmarks to recognize gestures.
        
        Args:
            landmarks: List of (x, y, z) landmark coordinates
            handedness: 'Left' or 'Right' hand
            
        Returns:
            Dictionary with recognized gestures and confidence scores
        """
        if not landmarks or len(landmarks) < 21:
            logger.warning("Invalid landmarks data")
            return {'gesture': 'unknown', 'confidence': 0.0}
        
        # Normalize coordinates relative to hand size
        normalized_landmarks = self._normalize_landmarks(landmarks)
        
        # Check each gesture
        gesture_scores = {}
        for gesture_name, gesture_info in self.gestures.items():
            # Get gesture detection function
            detect_func = gesture_info.get('function')
            if detect_func and callable(detect_func):
                # Call the detection function
                is_detected, confidence = detect_func(normalized_landmarks, handedness)
                if is_detected:
                    gesture_scores[gesture_name] = confidence
        
        # Determine the most likely gesture
        if gesture_scores:
            best_gesture = max(gesture_scores.items(), key=lambda x: x[1])
            result = {
                'gesture': best_gesture[0],
                'confidence': best_gesture[1],
                'all_gestures': gesture_scores
            }
        else:
            result = {
                'gesture': 'unknown',
                'confidence': 0.0,
                'all_gestures': {}
            }
        
        # Add finger states
        result['finger_states'] = self._get_finger_states(normalized_landmarks)
        
        return result
    
    def _normalize_landmarks(self, landmarks: List[Tuple[int, int, float]]) -> List[Tuple[float, float, float]]:
        """
        Normalize landmarks relative to hand size.
        
        Args:
            landmarks: List of (x, y, z) landmark coordinates
            
        Returns:
            List of normalized (x, y, z) coordinates
        """
        # Get wrist position and middle finger MCP (knuckle) for scale reference
        wrist = landmarks[self.WRIST]
        middle_mcp = landmarks[self.FINGER_MCPS[2]]
        
        # Calculate scale (distance between wrist and middle knuckle)
        dx = middle_mcp[0] - wrist[0]
        dy = middle_mcp[1] - wrist[1]
        scale = math.sqrt(dx*dx + dy*dy)
        
        if scale == 0:
            scale = 1  # Avoid division by zero
        
        # Normalize all landmarks relative to wrist position and hand scale
        normalized = []
        for lm in landmarks:
            nx = (lm[0] - wrist[0]) / scale
            ny = (lm[1] - wrist[1]) / scale
            nz = lm[2]  # Keep z as is (it's already normalized in MediaPipe)
            normalized.append((nx, ny, nz))
        
        return normalized
    
    def _get_finger_states(self, landmarks: List[Tuple[float, float, float]]) -> Dict[str, bool]:
        """
        Determine which fingers are extended/open.
        
        Args:
            landmarks: Normalized landmarks
            
        Returns:
            Dictionary mapping finger names to boolean states (True for extended)
        """
        finger_states = {}
        
        for i, name in enumerate(self.FINGER_NAMES):
            if i == 0:  # Thumb requires special handling
                # For thumb, compare the tip position with the IP (inner joint)
                tip = landmarks[self.FINGER_TIPS[i]]
                ip = landmarks[self.FINGER_PIPS[i]]
                mcp = landmarks[self.FINGER_MCPS[i]]
                
                # Check if thumb tip is further from the wrist than the IP joint
                thumb_extended = tip[0] > ip[0]  # For right hand
                finger_states[name] = thumb_extended
            else:
                # For other fingers, check if tip is higher (lower y) than PIP joint
                tip = landmarks[self.FINGER_TIPS[i]]
                pip = landmarks[self.FINGER_PIPS[i]]
                
                # Finger is extended if tip is further from wrist than PIP
                distance_tip = math.sqrt(tip[0]**2 + tip[1]**2)
                distance_pip = math.sqrt(pip[0]**2 + pip[1]**2)
                
                finger_extended = distance_tip > distance_pip
                finger_states[name] = finger_extended
        
        return finger_states
    
    def _detect_open_palm(self, landmarks: List[Tuple[float, float, float]], 
                         handedness: str) -> Tuple[bool, float]:
        """
        Detect open palm gesture (all fingers extended).
        
        Args:
            landmarks: Normalized landmarks
            handedness: 'Left' or 'Right' hand
            
        Returns:
            Tuple of (is_detected, confidence)
        """
        finger_states = self._get_finger_states(landmarks)
        
        # Count extended fingers
        extended_count = sum(1 for state in finger_states.values() if state)
        
        # Open palm if all fingers are extended
        is_open_palm = extended_count >= 4  # Allow for some detection error
        
        # Confidence based on number of extended fingers
        confidence = extended_count / 5.0 if is_open_palm else 0.0
        
        return is_open_palm, confidence
    
    def _detect_fist(self, landmarks: List[Tuple[float, float, float]],
                   handedness: str) -> Tuple[bool, float]:
        """
        Detect fist gesture (all fingers closed).
        
        Args:
            landmarks: Normalized landmarks
            handedness: 'Left' or 'Right' hand
            
        Returns:
            Tuple of (is_detected, confidence)
        """
        finger_states = self._get_finger_states(landmarks)
        
        # Count closed fingers
        closed_count = sum(1 for state in finger_states.values() if not state)
        
        # Fist if all fingers are closed
        is_fist = closed_count >= 4  # Allow for some detection error
        
        # Confidence based on number of closed fingers
        confidence = closed_count / 5.0 if is_fist else 0.0
        
        return is_fist, confidence
    
    def _detect_pointing(self, landmarks: List[Tuple[float, float, float]],
                       handedness: str) -> Tuple[bool, float]:
        """
        Detect pointing gesture (index finger extended, others closed).
        
        Args:
            landmarks: Normalized landmarks
            handedness: 'Left' or 'Right' hand
            
        Returns:
            Tuple of (is_detected, confidence)
        """
        finger_states = self._get_finger_states(landmarks)
        
        # Pointing if index is extended and other fingers are closed
        is_pointing = (
            finger_states['index'] and 
            not finger_states['middle'] and 
            not finger_states['ring'] and 
            not finger_states['pinky']
        )
        
        # Thumb can be either way for pointing
        confidence = 0.8 if is_pointing else 0.0
        
        return is_pointing, confidence
    
    def _detect_pinch(self, landmarks: List[Tuple[float, float, float]],
                    handedness: str) -> Tuple[bool, float]:
        """
        Detect pinch gesture (thumb and index fingertips close together).
        
        Args:
            landmarks: Normalized landmarks
            handedness: 'Left' or 'Right' hand
            
        Returns:
            Tuple of (is_detected, confidence)
        """
        # Get thumb and index fingertips
        thumb_tip = landmarks[self.FINGER_TIPS[0]]
        index_tip = landmarks[self.FINGER_TIPS[1]]
        
        # Calculate distance between thumb and index fingertips
        dx = thumb_tip[0] - index_tip[0]
        dy = thumb_tip[1] - index_tip[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Pinch if distance is below threshold
        threshold = self.default_params['pinch_distance_threshold']
        is_pinch = distance < threshold
        
        # Confidence inversely proportional to distance
        confidence = max(0, 1.0 - distance / threshold) if is_pinch else 0.0
        
        return is_pinch, confidence
    
    def _detect_grab(self, landmarks: List[Tuple[float, float, float]],
                   handedness: str) -> Tuple[bool, float]:
        """
        Detect grab gesture (fingers curled but not fully closed).
        
        Args:
            landmarks: Normalized landmarks
            handedness: 'Left' or 'Right' hand
            
        Returns:
            Tuple of (is_detected, confidence)
        """
        # Check if fingers are partially closed but not fully
        # This is a simplified detection - a real implementation would be more complex
        
        # Get distances from fingertips to wrist
        tip_distances = []
        for i in range(1, 5):  # Skip thumb
            tip = landmarks[self.FINGER_TIPS[i]]
            distance = math.sqrt(tip[0]**2 + tip[1]**2)
            tip_distances.append(distance)
        
        # Get distances from PIPs (middle joints) to wrist
        pip_distances = []
        for i in range(1, 5):  # Skip thumb
            pip = landmarks[self.FINGER_PIPS[i]]
            distance = math.sqrt(pip[0]**2 + pip[1]**2)
            pip_distances.append(distance)
        
        # For grab gesture, tips should be closer to wrist than PIPs
        # but not too close (which would be a fist)
        grab_threshold = self.default_params['grab_threshold']
        is_grabbing = True
        
        for i in range(4):  # For each finger except thumb
            ratio = tip_distances[i] / pip_distances[i] if pip_distances[i] > 0 else 0
            
            # If tip is too far from palm or too close to PIP, not a grab
            if ratio > 0.9 or ratio < 0.5:
                is_grabbing = False
                break
        
        # Check thumb position for grab
        thumb_tip = landmarks[self.FINGER_TIPS[0]]
        index_tip = landmarks[self.FINGER_TIPS[1]]
        thumb_index_distance = math.sqrt((thumb_tip[0] - index_tip[0])**2 + 
                                         (thumb_tip[1] - index_tip[1])**2)
        
        # Thumb should be somewhat close to other fingertips
        if thumb_index_distance > 0.3:
            is_grabbing = False
        
        # Confidence calculation
        confidence = 0.7 if is_grabbing else 0.0
        
        return is_grabbing, confidence
    
    def _detect_thumbs_up(self, landmarks: List[Tuple[float, float, float]],
                        handedness: str) -> Tuple[bool, float]:
        """
        Detect thumbs up gesture (thumb extended upward, other fingers closed).
        
        Args:
            landmarks: Normalized landmarks
            handedness: 'Left' or 'Right' hand
            
        Returns:
            Tuple of (is_detected, confidence)
        """
        finger_states = self._get_finger_states(landmarks)
        
        # Basic check: thumb extended, other fingers closed
        basic_thumbs_up = (
            finger_states['thumb'] and
            not finger_states['index'] and
            not finger_states['middle'] and
            not finger_states['ring'] and
            not finger_states['pinky']
        )
        
        if not basic_thumbs_up:
            return False, 0.0
        
        # Check thumb orientation (should be pointing upward)
        thumb_tip = landmarks[self.FINGER_TIPS[0]]
        thumb_ip = landmarks[self.FINGER_PIPS[0]]
        
        # Calculate thumb direction
        thumb_direction = (thumb_tip[0] - thumb_ip[0], thumb_tip[1] - thumb_ip[1])
        
        # For a thumbs up, the y component should be negative (pointing up)
        # and the magnitude of y should be greater than x
        is_thumbs_up = (thumb_direction[1] < 0 and 
                      abs(thumb_direction[1]) > abs(thumb_direction[0]))
        
        confidence = 0.8 if is_thumbs_up else 0.0
        
        return is_thumbs_up, confidence
    
    def _detect_swipe(self, landmarks: List[Tuple[float, float, float]],
                    handedness: str) -> Tuple[bool, float]:
        """
        This is a placeholder for swipe detection.
        Actual swipe detection requires tracking hand movement over time.
        
        Args:
            landmarks: Normalized landmarks
            handedness: 'Left' or 'Right' hand
            
        Returns:
            Tuple of (is_detected, confidence)
        """
        # Swipe detection requires tracking motion over time
        # This would be implemented in the main application loop
        # Here we just check if the hand is in a position that could be a swipe
        
        finger_states = self._get_finger_states(landmarks)
        
        # Hand should be flat with most fingers extended
        extended_count = sum(1 for state in finger_states.values() if state)
        
        is_potential_swipe = extended_count >= 3
        
        return False, 0.0  # Always return false since we can't detect motion here
    
    def _detect_wave(self, landmarks: List[Tuple[float, float, float]],
                   handedness: str) -> Tuple[bool, float]:
        """
        This is a placeholder for wave detection.
        Actual wave detection requires tracking hand movement over time.
        
        Args:
            landmarks: Normalized landmarks
            handedness: 'Left' or 'Right' hand
            
        Returns:
            Tuple of (is_detected, confidence)
        """
        # Wave detection requires tracking motion over time
        # This would be implemented in the main application loop
        
        return False, 0.0  # Always return false since we can't detect motion here
    
    def recognize_gesture(self, landmarks: List[Tuple[int, int, float]], 
                         handedness: str = 'Right') -> str:
        """
        Recognize the most likely gesture from landmarks.
        
        Args:
            landmarks: List of (x, y, z) landmark coordinates
            handedness: 'Left' or 'Right' hand
            
        Returns:
            Name of the recognized gesture
        """
        result = self.process_landmarks(landmarks, handedness)
        return result['gesture']


# Helper function for testing
def test_gesture_processor():
    """Test the gesture processor with sample data."""
    import json
    
    # Sample landmarks for an open palm gesture
    sample_landmarks = [
        (100, 100, 0),  # Wrist
        (110, 90, 0),   # Thumb CMC
        (120, 80, 0),   # Thumb MCP
        (130, 70, 0),   # Thumb IP
        (140, 60, 0),   # Thumb tip
        (105, 95, 0),   # Index MCP
        (110, 85, 0),   # Index PIP
        (115, 75, 0),   # Index DIP
        (120, 65, 0),   # Index tip
        (103, 97, 0),   # Middle MCP
        (106, 90, 0),   # Middle PIP
        (109, 83, 0),   # Middle DIP
        (112, 76, 0),   # Middle tip
        (100, 99, 0),   # Ring MCP
        (100, 95, 0),   # Ring PIP
        (100, 90, 0),   # Ring DIP
        (100, 85, 0),   # Ring tip
        (97, 101, 0),   # Pinky MCP
        (94, 100, 0),   # Pinky PIP
        (91, 99, 0),    # Pinky DIP
        (88, 98, 0)     # Pinky tip
    ]
    
    processor = GestureProcessor()
    result = processor.process_landmarks(sample_landmarks)
    
    print("Recognized gesture:", result['gesture'])
    print("Confidence:", result['confidence'])
    print("Finger states:", result['finger_states'])
    print("All detected gestures:", result['all_gestures'])


if __name__ == "__main__":
    # Run test if this file is executed directly
    test_gesture_processor()