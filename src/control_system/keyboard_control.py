"""
Keyboard control module using PyAutoGUI.

This module handles keyboard actions like typing, pressing keys,
and keyboard shortcuts.
"""

import logging
import pyautogui
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class KeyboardController:
    """Controller for keyboard-related actions using PyAutoGUI."""
    
    def __init__(self):
        """Initialize the keyboard controller."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Keyboard controller initialized")
        
        # Define common keyboard shortcuts
        self.shortcuts = {
            "copy": ["ctrl", "c"],
            "paste": ["ctrl", "v"],
            "cut": ["ctrl", "x"],
            "save": ["ctrl", "s"],
            "undo": ["ctrl", "z"],
            "redo": ["ctrl", "y"],
            "select_all": ["ctrl", "a"],
            "find": ["ctrl", "f"],
            "new_tab": ["ctrl", "t"],
            "close_tab": ["ctrl", "w"],
            "switch_tab_right": ["ctrl", "tab"],
            "switch_tab_left": ["ctrl", "shift", "tab"],
            "alt_tab": ["alt", "tab"],
        }
    
    def type_text(self, text: str, interval: float = 0.01) -> None:
        """
        Type the specified text with PyAutoGUI.
        
        Args:
            text: The text to type
            interval: The interval between keypresses (default: 0.01s)
        """
        try:
            pyautogui.write(text, interval=interval)
            self.logger.info(f"Typed text: '{text}'")
        except Exception as e:
            self.logger.error(f"Error typing text: {str(e)}")
            raise
    
    def press_key(self, key: str) -> None:
        """
        Press a single key.
        
        Args:
            key: The key to press (e.g., 'enter', 'esc', 'space')
        """
        try:
            pyautogui.press(key)
            self.logger.info(f"Pressed key: {key}")
        except Exception as e:
            self.logger.error(f"Error pressing key '{key}': {str(e)}")
            raise
    
    def hold_key(self, key: str, duration: float = 0.5) -> None:
        """
        Hold down a key for specified duration.
        
        Args:
            key: The key to hold down
            duration: Duration to hold the key in seconds
        """
        try:
            pyautogui.keyDown(key)
            pyautogui.sleep(duration)
            pyautogui.keyUp(key)
            self.logger.info(f"Held key '{key}' for {duration}s")
        except Exception as e:
            # Make sure to release the key even if there's an error
            try:
                pyautogui.keyUp(key)
            except:
                pass
            self.logger.error(f"Error holding key '{key}': {str(e)}")
            raise
    
    def press_key_combination(self, keys: List[str]) -> None:
        """
        Press a combination of keys (keyboard shortcut).
        
        Args:
            keys: List of keys to press simultaneously
        """
        try:
            pyautogui.hotkey(*keys)
            self.logger.info(f"Pressed key combination: {'+'.join(keys)}")
        except Exception as e:
            self.logger.error(f"Error pressing key combination {keys}: {str(e)}")
            raise
    
    def execute_shortcut(self, shortcut_name: str) -> bool:
        """
        Execute a predefined keyboard shortcut by name.
        
        Args:
            shortcut_name: Name of the shortcut to execute
            
        Returns:
            True if shortcut executed successfully, False if shortcut not found
        """
        if shortcut_name in self.shortcuts:
            try:
                self.press_key_combination(self.shortcuts[shortcut_name])
                self.logger.info(f"Executed shortcut: {shortcut_name}")
                return True
            except Exception as e:
                self.logger.error(f"Error executing shortcut '{shortcut_name}': {str(e)}")
                raise
        else:
            self.logger.warning(f"Shortcut '{shortcut_name}' not found")
            return False
    
    def add_custom_shortcut(self, name: str, keys: List[str]) -> None:
        """
        Add a custom keyboard shortcut.
        
        Args:
            name: Name for the new shortcut
            keys: List of keys for the shortcut
        """
        self.shortcuts[name] = keys
        self.logger.info(f"Added custom shortcut '{name}': {'+'.join(keys)}")