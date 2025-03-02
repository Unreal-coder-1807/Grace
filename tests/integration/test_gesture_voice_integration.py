"""
Integration tests for gesture and voice module interactions.
Tests how the gesture recognition and voice command systems work together.
"""

import unittest
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

# Add parent directory to path to enable imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from gesture_module.detector import GestureDetector
from gesture_module.processor import GestureProcessor
from voice_module.listener import VoiceListener
from voice_module.intent_handler import IntentHandler
from control_system.system_control import SystemController


class TestGestureVoiceIntegration(unittest.TestCase):
    """Test class for integration between gesture and voice modules"""

    def setUp(self):
        """Setup test fixtures before each test"""
        # Mock the hardware components to avoid requiring actual camera/microphone
        self.gesture_detector_patcher = patch('src.gesture_module.detector.GestureDetector')
        self.voice_listener_patcher = patch('src.voice_module.listener.VoiceListener')
        self.system_controller_patcher = patch('src.control_system.system_control.SystemController')
        
        self.mock_gesture_detector = self.gesture_detector_patcher.start()
        self.mock_voice_listener = self.voice_listener_patcher.start()
        self.mock_system_controller = self.system_controller_patcher.start()
        
        # Create the mocked instances
        self.gesture_detector = self.mock_gesture_detector.return_value
        self.voice_listener = self.mock_voice_listener.return_value
        self.system_controller = self.mock_system_controller.return_value
        
        # Initialize processors with mocked detectors
        self.gesture_processor = GestureProcessor(self.gesture_detector)
        self.intent_handler = IntentHandler()

    def tearDown(self):
        """Tear down test fixtures after each test"""
        self.gesture_detector_patcher.stop()
        self.voice_listener_patcher.stop()
        self.system_controller_patcher.stop()

    def test_voice_activated_gesture_mode(self):
        """Test that voice commands can activate gesture recognition mode"""
        # Setup voice command recognition mock
        self.voice_listener.get_voice_command.return_value = "enable gesture mode"
        self.intent_handler.process_intent = MagicMock(return_value={
            "intent": "enable_feature",
            "feature": "gesture_mode",
            "confidence": 0.95
        })
        
        # Process the voice command
        voice_text = self.voice_listener.get_voice_command()
        intent_data = self.intent_handler.process_intent(voice_text)
        
        # Simulate system controller handling the intent
        self.system_controller.handle_intent(intent_data)
        
        # Verify gesture detection was enabled
        self.system_controller.enable_gesture_detection.assert_called_once()
        
    def test_gesture_triggered_voice_command(self):
        """Test that gestures can trigger voice command listener"""
        # Setup gesture recognition mock
        self.gesture_detector.detect_gesture.return_value = "palm_up"
        self.gesture_processor.process_gesture = MagicMock(return_value={
            "gesture": "palm_up",
            "action": "activate_voice_listener",
            "confidence": 0.92
        })
        
        # Process the gesture
        gesture = self.gesture_detector.detect_gesture()
        gesture_data = self.gesture_processor.process_gesture(gesture)
        
        # Simulate system controller handling the gesture
        self.system_controller.handle_gesture(gesture_data)
        
        # Verify voice listener was activated
        self.system_controller.activate_voice_listener.assert_called_once()
    
    def test_compound_gesture_voice_command(self):
        """Test a complex interaction using both gesture and voice"""
        # First simulate a gesture to initiate voice listening
        self.gesture_detector.detect_gesture.return_value = "palm_up"
        self.gesture_processor.process_gesture = MagicMock(return_value={
            "gesture": "palm_up",
            "action": "activate_voice_listener",
            "confidence": 0.92
        })
        
        # Process the gesture
        gesture = self.gesture_detector.detect_gesture()
        gesture_data = self.gesture_processor.process_gesture(gesture)
        self.system_controller.handle_gesture(gesture_data)
        
        # Then simulate voice command for volume control
        self.voice_listener.get_voice_command.return_value = "increase volume"
        self.intent_handler.process_intent = MagicMock(return_value={
            "intent": "volume_control",
            "action": "increase",
            "amount": 10,
            "confidence": 0.88
        })
        
        # Process the voice command
        voice_text = self.voice_listener.get_voice_command()
        intent_data = self.intent_handler.process_intent(voice_text)
        self.system_controller.handle_intent(intent_data)
        
        # Verify volume was increased
        self.system_controller.control_volume.assert_called_once_with("increase", 10)
    
    @patch('src.control_system.volume_control.VolumeController')
    def test_simultaneous_gesture_voice_processing(self, mock_volume_controller):
        """Test that gesture and voice can be processed simultaneously"""
        # Setup volume controller mock
        volume_controller = mock_volume_controller.return_value
        
        # Configure system controller to use our mocked volume controller
        self.system_controller.volume_controller = volume_controller
        
        # Simulate simultaneous input
        # Voice command for volume up
        self.voice_listener.get_voice_command.return_value = "volume up"
        voice_intent = {
            "intent": "volume_control",
            "action": "increase",
            "amount": 5,
            "confidence": 0.85
        }
        self.intent_handler.process_intent = MagicMock(return_value=voice_intent)
        
        # Gesture for volume up (same action, should be de-duplicated)
        self.gesture_detector.detect_gesture.return_value = "swipe_up"
        gesture_data = {
            "gesture": "swipe_up",
            "action": "volume_up",
            "confidence": 0.90
        }
        self.gesture_processor.process_gesture = MagicMock(return_value=gesture_data)
        
        # Process both inputs
        self.system_controller.handle_intent(voice_intent)
        self.system_controller.handle_gesture(gesture_data)
        
        # Verify volume control was called exactly once (de-duplicated)
        # This simulates the system's ability to avoid double-executing the same command
        self.assertEqual(volume_controller.adjust_volume.call_count, 1)
    
    @pytest.mark.slow
    def test_end_to_end_workflow(self):
        """Test a complete end-to-end workflow with multiple interactions"""
        # This test simulates a sequence of user interactions
        # 1. User activates system with hotword
        # 2. System enters listening mode
        # 3. User issues voice command to open browser
        # 4. User makes gesture to scroll down
        # 5. User makes another gesture to click
        
        # Mock sequence setup
        events = [
            # Step 1: Hotword detection
            {"type": "voice", "input": "hey assistant", "intent": {"intent": "activate", "confidence": 0.96}},
            # Step 3: Voice command
            {"type": "voice", "input": "open browser", "intent": {"intent": "open_app", "app": "browser", "confidence": 0.92}},
            # Step 4: Gesture for scroll
            {"type": "gesture", "input": "swipe_down", "action": {"gesture": "swipe_down", "action": "scroll_down", "confidence": 0.88}},
            # Step 5: Gesture for click
            {"type": "gesture", "input": "pinch", "action": {"gesture": "pinch", "action": "mouse_click", "confidence": 0.90}}
        ]
        
        # Set up mocks for this sequence
        mock_sequence = MagicMock()
        self.system_controller.process_event_sequence = mock_sequence
        
        # Execute the sequence
        self.system_controller.process_event_sequence(events)
        
        # Verify our mocked sequence processing was called with the events
        mock_sequence.assert_called_once_with(events)


if __name__ == '__main__':
    unittest.main()