"""
Gesture detection module using MediaPipe.

This module provides functionality for detecting and tracking hand gestures
using the MediaPipe framework and OpenCV.
"""

import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional, Any, Union

# Set up logger
logger = logging.getLogger(__name__)

class GestureDetector:
    """Detect and track hand gestures using MediaPipe."""
    
    def __init__(self, 
                 static_image_mode: bool = False,
                 max_num_hands: int = 2,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        """
        Initialize the gesture detector.
        
        Args:
            static_image_mode: Whether to treat input images as a batch of static images
            max_num_hands: Maximum number of hands to detect
            min_detection_confidence: Minimum confidence for hand detection
            min_tracking_confidence: Minimum confidence for hand tracking
        """
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Create Hands object with configuration
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # Store configuration
        self.max_num_hands = max_num_hands
        self.static_image_mode = static_image_mode
        
        logger.info("GestureDetector initialized")
    
    def detect_hands(self, 
                    image: np.ndarray, 
                    draw: bool = True) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Detect hands in an image.
        
        Args:
            image: Input image (BGR format from OpenCV)
            draw: Whether to draw landmarks on the image
            
        Returns:
            Tuple of (processed image, results dictionary)
        """
        # Convert the BGR image to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process the image and get hand landmarks
        results = self.hands.process(image_rgb)
        
        # Prepare results dictionary
        detection_results = {
            'landmarks': [],
            'handedness': [],
            'num_hands_detected': 0,
            'is_hand_present': False
        }
        
        # Check if hands are detected
        if results.multi_hand_landmarks:
            detection_results['is_hand_present'] = True
            detection_results['num_hands_detected'] = len(results.multi_hand_landmarks)
            
            # Process each detected hand
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Convert landmarks to a list of (x, y, z) coordinates
                landmarks = []
                for lm in hand_landmarks.landmark:
                    h, w, c = image.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    landmarks.append((cx, cy, lm.z))
                
                detection_results['landmarks'].append(landmarks)
                
                # Get handedness (left or right hand)
                if results.multi_handedness:
                    handedness = results.multi_handedness[idx].classification[0].label
                    detection_results['handedness'].append(handedness)
                
                # Draw hand landmarks on the image
                if draw:
                    self.mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )
        
        return image, detection_results
    
    def get_hand_position(self, detection_results: Dict[str, Any], hand_index: int = 0) -> Optional[Tuple[int, int]]:
        """
        Get the center position of a hand.
        
        Args:
            detection_results: Results from detect_hands
            hand_index: Index of the hand (if multiple hands detected)
            
        Returns:
            Tuple of (x, y) coordinates or None if hand not detected
        """
        if not detection_results['is_hand_present'] or hand_index >= detection_results['num_hands_detected']:
            return None
        
        # Use the wrist position (landmark 0) as the hand position
        landmarks = detection_results['landmarks'][hand_index]
        if landmarks and len(landmarks) > 0:
            return landmarks[0][0], landmarks[0][1]
        
        return None
    
    def get_finger_positions(self, detection_results: Dict[str, Any], hand_index: int = 0) -> Dict[str, Tuple[int, int]]:
        """
        Get the positions of fingertips.
        
        Args:
            detection_results: Results from detect_hands
            hand_index: Index of the hand (if multiple hands detected)
            
        Returns:
            Dictionary mapping finger names to (x, y) coordinates
        """
        finger_positions = {
            'thumb': None,
            'index': None,
            'middle': None,
            'ring': None,
            'pinky': None
        }
        
        if not detection_results['is_hand_present'] or hand_index >= detection_results['num_hands_detected']:
            return finger_positions
        
        landmarks = detection_results['landmarks'][hand_index]
        if landmarks and len(landmarks) >= 21:
            # MediaPipe hand landmark indices:
            # Thumb tip: 4, Index tip: 8, Middle tip: 12, Ring tip: 16, Pinky tip: 20
            finger_positions['thumb'] = (landmarks[4][0], landmarks[4][1])
            finger_positions['index'] = (landmarks[8][0], landmarks[8][1])
            finger_positions['middle'] = (landmarks[12][0], landmarks[12][1])
            finger_positions['ring'] = (landmarks[16][0], landmarks[16][1])
            finger_positions['pinky'] = (landmarks[20][0], landmarks[20][1])
        
        return finger_positions
    
    def release(self):
        """Release resources used by the detector."""
        self.hands.close()
        logger.info("GestureDetector resources released")


def start_webcam_detection(camera_index: int = 0) -> None:
    """
    Start webcam detection for testing purposes.
    
    Args:
        camera_index: Index of the camera to use
    """
    # Initialize detector
    detector = GestureDetector()
    
    # Initialize webcam
    cap = cv2.VideoCapture(camera_index)
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            logger.error("Failed to read from webcam")
            break
        
        # Detect hands
        image, results = detector.detect_hands(image)
        
        # Display number of hands detected
        num_hands = results['num_hands_detected']
        cv2.putText(image, f"Hands: {num_hands}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display handedness if detected
        for idx, handedness in enumerate(results['handedness']):
            y_pos = 60 + idx * 30
            cv2.putText(image, f"Hand {idx}: {handedness}", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Show the image
        cv2.imshow('MediaPipe Hands', image)
        
        # Exit on 'q' press
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
    
    # Release resources
    detector.release()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Run webcam detection test if this file is executed directly
    start_webcam_detection()