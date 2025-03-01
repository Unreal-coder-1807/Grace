"""
Actions module for executing gesture-triggered commands

This module maps recognized gestures to system actions using PyAutoGUI 
and other control interfaces from the control_system module.
"""

import logging
import importlib
import yaml
from pathlib import Path
import os

# Initialize logger
logger = logging.getLogger(__name__)

class ActionRegistry:
    """
    Registry for managing mappings between gestures and their corresponding actions.
    """
    
    def __init__(self, config_path):
        """
        Initialize the ActionRegistry with the specified configuration.
        
        Args:
            config_path (str): Path to the gesture configuration file
        """
        self.logger = logging.getLogger(__name__ + ".ActionRegistry")
        self.config_path = config_path
        self.action_map = {}
        self.control_modules = {}
        
        # Load gesture to action mappings from config
        self.load_config(config_path)
    
    def load_config(self, config_path):
        """
        Load gesture-to-action mappings from the configuration file.
        
        Args:
            config_path (str): Path to the YAML configuration file
        """
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            if 'gesture_actions' in config:
                for gesture, action_info in config['gesture_actions'].items():
                    self.action_map[gesture] = action_info
                    self.logger.debug(f"Loaded action mapping: {gesture} -> {action_info}")
            
            self.logger.info(f"Loaded {len(self.action_map)} gesture action mappings from config")
        except Exception as e:
            self.logger.error(f"Error loading gesture actions config: {e}")
            # Set defaults if config fails to load
            self._set_default_mappings()
    
    def _set_default_mappings(self):
        """Set default gesture-to-action mappings if config loading fails."""
        self.action_map = {
            'open_hand': {'module': 'system_control', 'action': 'pause_media'},
            'closed_fist': {'module': 'mouse_control', 'action': 'click'},
            'pointing_up': {'module': 'volume_control', 'action': 'volume_up'},
            'pointing_down': {'module': 'volume_control', 'action': 'volume_down'},
            'thumbs_up': {'module': 'system_control', 'action': 'confirm'},
            'thumbs_down': {'module': 'system_control', 'action': 'cancel'},
            'victory': {'module': 'keyboard_control', 'action': 'copy'},
            'pinch': {'module': 'mouse_control', 'action': 'scroll'},
            'swipe_left': {'module': 'browser_control', 'action': 'back'},
            'swipe_right': {'module': 'browser_control', 'action': 'forward'}
        }
        self.logger.warning("Using default gesture mappings")
    
    def get_action_for_gesture(self, gesture_name):
        """
        Get the action information for a specific gesture.
        
        Args:
            gesture_name (str): The name of the detected gesture
            
        Returns:
            dict or None: Action information if found, None otherwise
        """
        if gesture_name in self.action_map:
            return self.action_map[gesture_name]
        return None
    
    def register_action(self, gesture_name, action_function):
        """
        Register a custom action function for a specific gesture.
        
        Args:
            gesture_name (str): Name of the gesture to map
            action_function (callable): Function to call when gesture is detected
        """
        self.action_map[gesture_name] = {
            'module': 'custom',
            'action': 'custom_function',
            'function': action_function
        }
        self.logger.info(f"Registered custom action function for gesture: {gesture_name}")
    
    def get_control_module(self, module_name):
        """
        Dynamically import and cache a control system module.
        
        Args:
            module_name (str): Name of the control system module to import
            
        Returns:
            module or None: Imported module if successful, None otherwise
        """
        if module_name in self.control_modules:
            return self.control_modules[module_name]
        
        try:
            # Import the appropriate control module
            module_path = f"src.control_system.{module_name}"
            module = importlib.import_module(module_path)
            self.control_modules[module_name] = module
            return module
        except ImportError as e:
            self.logger.error(f"Failed to import control module {module_name}: {e}")
            return None


class GestureActions:
    """
    Executes system actions based on recognized gestures.
    """
    
    def __init__(self, action_registry):
        """
        Initialize the GestureActions with the specified action registry.
        
        Args:
            action_registry (ActionRegistry): Registry of gesture-to-action mappings
        """
        self.logger = logging.getLogger(__name__ + ".GestureActions")
        self.registry = action_registry
        self.last_executed_gesture = None
        self.cooldown_counter = 0
        self.cooldown_threshold = 10  # Frames to wait before executing same gesture again
    
    def execute_action(self, gesture_info):
        """
        Execute the appropriate action for a detected gesture.
        
        Args:
            gesture_info (dict): Information about the detected gesture
                {
                    'name': str,           # Name of the detected gesture
                    'confidence': float,   # Confidence score (0-1)
                    'hand': str,           # 'left' or 'right'
                    'position': (x, y, z)  # 3D coordinates of gesture
                }
                
        Returns:
            bool: True if action was executed, False otherwise
        """
        if not gesture_info or 'name' not in gesture_info:
            return False
        
        gesture_name = gesture_info['name']
        confidence = gesture_info.get('confidence', 0.0)
        
        # Apply cooldown to prevent repeated executions of the same gesture
        if gesture_name == self.last_executed_gesture:
            self.cooldown_counter += 1
            if self.cooldown_counter < self.cooldown_threshold:
                return False
        else:
            self.cooldown_counter = 0
            self.last_executed_gesture = gesture_name
        
        # Get action details for this gesture
        action_info = self.registry.get_action_for_gesture(gesture_name)
        if not action_info:
            self.logger.debug(f"No action defined for gesture: {gesture_name}")
            return False
        
        # Check confidence threshold
        min_confidence = action_info.get('min_confidence', 0.7)
        if confidence < min_confidence:
            self.logger.debug(f"Gesture {gesture_name} below confidence threshold: {confidence} < {min_confidence}")
            return False
        
        # Handle custom function
        if action_info.get('module') == 'custom' and 'function' in action_info:
            try:
                action_info['function'](gesture_info)
                self.logger.info(f"Executed custom action for gesture: {gesture_name}")
                return True
            except Exception as e:
                self.logger.error(f"Error executing custom action for {gesture_name}: {e}")
                return False
        
        # Handle standard module/action
        try:
            module_name = action_info.get('module')
            action_name = action_info.get('action')
            
            if not module_name or not action_name:
                self.logger.error(f"Invalid action specification for gesture {gesture_name}")
                return False
            
            # Get control module
            module = self.registry.get_control_module(module_name)
            if not module:
                return False
            
            # Execute the action with parameters if provided
            params = action_info.get('params', {})
            if hasattr(module, action_name):
                action_method = getattr(module, action_name)
                if params:
                    action_method(**params)
                else:
                    action_method()
                self.logger.info(f"Executed {module_name}.{action_name} for gesture {gesture_name}")
                return True
            else:
                self.logger.error(f"Action {action_name} not found in module {module_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing action for gesture {gesture_name}: {e}")
            return False

    def get_available_actions(self):
        """
        Get a list of all available gesture actions.
        
        Returns:
            dict: Mapping of gesture names to their actions
        """
        return self.registry.action_map