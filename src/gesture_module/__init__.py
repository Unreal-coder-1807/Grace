"""
Gesture Module for the Gesture & Voice Controlled AI Assistant

This module handles the detection, processing, and mapping of hand gestures
to system actions using MediaPipe and OpenCV for gesture recognition.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to support imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

# Import submodules to make them available through the package
from .detector import GestureDetector
from .processor import GestureProcessor
from .actions import GestureActions, ActionRegistry

# Setup module logger
logger = logging.getLogger(__name__)

# Version info
__version__ = "0.1.0"
__author__ = "Gesture & Voice Control Team"

# Create a standard interface for the gesture module
class GestureModule:
    """Main interface for the gesture recognition and control system."""
    
    def __init__(self, config_path=None):
        """Initialize the gesture module components.
        
        Args:
            config_path (str, optional): Path to the gesture configuration file.
                Defaults to the standard config/settings/gesture.yaml file.
        """
        self.logger = logging.getLogger(__name__ + ".GestureModule")
        self.logger.info("Initializing Gesture Module")
        
        # If no config path provided, use default
        if config_path is None:
            config_path = os.path.join(parent_dir, "config", "settings", "gesture.yaml")
        
        # Initialize components
        self.detector = GestureDetector(config_path)
        self.processor = GestureProcessor(config_path)
        self.action_registry = ActionRegistry(config_path)
        self.actions = GestureActions(self.action_registry)
        
        self.logger.info("Gesture Module initialized successfully")
    
    def start(self, camera_index=0):
        """Start the gesture recognition system.
        
        Args:
            camera_index (int, optional): Camera index to use. Defaults to 0.
        
        Returns:
            bool: True if started successfully, False otherwise.
        """
        try:
            self.logger.info(f"Starting gesture detection with camera {camera_index}")
            self.detector.start_camera(camera_index)
            return True
        except Exception as e:
            self.logger.error(f"Failed to start gesture module: {e}")
            return False
    
    def stop(self):
        """Stop the gesture recognition system."""
        try:
            self.logger.info("Stopping gesture detection")
            self.detector.stop_camera()
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop gesture module: {e}")
            return False
    
    def process_frame(self, frame):
        """Process a single frame for gesture detection.
        
        Args:
            frame: OpenCV image frame to process
            
        Returns:
            tuple: (processed_frame, detected_gestures)
        """
        landmarks = self.detector.detect_gestures(frame)
        gestures = self.processor.process_landmarks(landmarks)
        
        if gestures:
            for gesture in gestures:
                self.actions.execute_action(gesture)
                
        return self.detector.draw_landmarks(frame, landmarks), gestures
    
    def register_custom_action(self, gesture_name, action_function):
        """Register a custom action for a specific gesture.
        
        Args:
            gesture_name (str): Name of the gesture to map
            action_function (callable): Function to call when gesture is detected
        """
        self.action_registry.register_action(gesture_name, action_function)
        self.logger.info(f"Registered custom action for gesture: {gesture_name}")

# Default instance for simple usage
default_module = None

def get_gesture_module(config_path=None):
    """Get the default gesture module instance."""
    global default_module
    if default_module is None:
        default_module = GestureModule(config_path)
    return default_module
