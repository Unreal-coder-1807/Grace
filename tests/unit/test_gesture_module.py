import unittest
import os
import sys
import numpy as np
import cv2
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from gesture_module.detector import GestureDetector
from gesture_module.processor import GestureProcessor
from gesture_module.actions import GestureActionMapper

class TestGestureDetector(unittest.TestCase):
    def setUp(self):
        # Create a mock config for testing
        self.mock_config = {
            'min_detection_confidence': 0.5,
            'min_tracking_confidence': 0.5,
            'use_static_image_mode': False
        }
        
        self.detector = GestureDetector(config=self.mock_config)
        
    @patch('src.gesture_module.detector.mp.solutions.hands.Hands')
    def test_initialize_detector(self, mock_hands):
        # Test if detector initializes with correct parameters
        detector = GestureDetector(config=self.mock_config)
        
        # Check if mediapipe Hands was initialized with correct parameters
        mock_hands.assert_called_once_with(
            static_image_mode=self.mock_config['use_static_image_mode'],
            max_num_hands=2,
            min_detection_confidence=self.mock_config['min_detection_confidence'],
            min_tracking_confidence=self.mock_config['min_tracking_confidence']
        )
    
    def test_process_image_no_hands(self):
        # Create a blank test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Mock the hands.process method to return no hands
        self.detector.hands.process = MagicMock(return_value=MagicMock(multi_hand_landmarks=None))
        
        results = self.detector.detect_gestures(test_image)
        
        # Should return empty list if no hands detected
        self.assertEqual(results, [])

    def test_process_image_with_hands(self):
        # Create a test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Create mock hand landmarks
        mock_landmarks = MagicMock()
        mock_hand_landmarks = [mock_landmarks]
        
        # Mock the process method to return hand landmarks
        self.detector.hands.process = MagicMock(
            return_value=MagicMock(multi_hand_landmarks=mock_hand_landmarks)
        )
        
        # Mock the _extract_landmarks method
        self.detector._extract_landmarks = MagicMock(return_value={'hand_landmarks': 'test'})
        
        results = self.detector.detect_gestures(test_image)
        
        # Should return the landmarks
        self.assertEqual(results, [{'hand_landmarks': 'test'}])

class TestGestureProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = GestureProcessor()
    
    def test_process_pinch_gesture(self):
        # Create mock landmarks for a pinch gesture
        # In a real pinch gesture, thumb tip and index finger tip are close
        mock_landmarks = {
            'thumb_tip': np.array([0.5, 0.5, 0.0]),
            'index_finger_tip': np.array([0.51, 0.51, 0.0]),
            'middle_finger_tip': np.array([0.6, 0.6, 0.0]),
            'wrist': np.array([0.3, 0.7, 0.0])
        }
        
        # Mock the distance calculation to return a small distance
        self.processor._calculate_distance = MagicMock(return_value=0.02)
        
        gesture = self.processor.identify_gesture(mock_landmarks)
        
        self.assertEqual(gesture, 'pinch')
    
    def test_process_open_palm_gesture(self):
        # Create mock landmarks for an open palm gesture
        # In an open palm, fingers are extended away from palm
        mock_landmarks = {
            'thumb_tip': np.array([0.3, 0.3, 0.0]),
            'index_finger_tip': np.array([0.4, 0.2, 0.0]),
            'middle_finger_tip': np.array([0.5, 0.2, 0.0]),
            'ring_finger_tip': np.array([0.6, 0.2, 0.0]),
            'pinky_tip': np.array([0.7, 0.3, 0.0]),
            'wrist': np.array([0.5, 0.7, 0.0])
        }
        
        # Mock finger extension detection to return all fingers extended
        self.processor._is_finger_extended = MagicMock(return_value=True)
        
        gesture = self.processor.identify_gesture(mock_landmarks)
        
        self.assertEqual(gesture, 'open_palm')

class TestGestureActionMapper(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            'gestures': {
                'pinch': 'volume_control',
                'open_palm': 'mouse_move',
                'fist': 'click'
            }
        }
        self.action_mapper = GestureActionMapper(config=self.mock_config)
    
    def test_map_gesture_to_action(self):
        gesture = 'pinch'
        action = self.action_mapper.map_gesture_to_action(gesture)
        self.assertEqual(action, 'volume_control')
    
    def test_map_unknown_gesture(self):
        gesture = 'unknown_gesture'
        action = self.action_mapper.map_gesture_to_action(gesture)
        self.assertIsNone(action)
    
    @patch('src.gesture_module.actions.GestureActionMapper._load_config')
    def test_load_custom_config(self, mock_load_config):
        mock_config = {
            'gestures': {
                'custom_gesture': 'custom_action'
            }
        }
        mock_load_config.return_value = mock_config
        
        # Initialize with a custom config path
        action_mapper = GestureActionMapper(config_path='custom_path.yaml')
        
        # Verify the config was loaded
        mock_load_config.assert_called_once_with('custom_path.yaml')
        self.assertEqual(action_mapper.gesture_map, mock_config['gestures'])

if __name__ == '__main__':
    unittest.main()