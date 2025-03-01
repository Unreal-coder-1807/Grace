"""
Mouse control module using PyAutoGUI.

This module handles mouse actions like movement, clicking, scrolling,
and drag-and-drop operations.
"""

import logging
import pyautogui
from typing import Tuple, Dict, Any, Optional, Union

# Set PyAutoGUI fail-safe to True to allow emergency stop by moving mouse to corner
pyautogui.FAILSAFE = True

logger = logging.getLogger(__name__)

class MouseController:
    """Controller for mouse-related actions using PyAutoGUI."""
    
    def __init__(self):
        """Initialize the mouse controller."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Mouse controller initialized")
        
        # Get screen size for boundary calculations
        self.screen_width, self.screen_height = pyautogui.size()
        self.logger.info(f"Screen size: {self.screen_width}x{self.screen_height}")
    
    def get_current_position(self) -> Tuple[int, int]:
        """
        Get current mouse position.
        
        Returns:
            Tuple of (x, y) coordinates
        """
        x, y = pyautogui.position()
        self.logger.debug(f"Current mouse position: ({x}, {y})")
        return (x, y)
    
    def move_to(self, x: int, y: int, duration: float = 0.2) -> None:
        """
        Move mouse to absolute coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Movement duration in seconds (default: 0.2s)
        """
        try:
            # Ensure coordinates are within screen boundaries
            x = max(0, min(x, self.screen_width - 1))
            y = max(0, min(y, self.screen_height - 1))
            
            pyautogui.moveTo(x, y, duration=duration)
            self.logger.info(f"Moved mouse to ({x}, {y})")
        except Exception as e:
            self.logger.error(f"Error moving mouse to ({x}, {y}): {str(e)}")
            raise
    
    def move_relative(self, x_offset: int, y_offset: int, duration: float = 0.2) -> None:
        """
        Move mouse by a relative offset from current position.
        
        Args:
            x_offset: Horizontal movement (positive = right, negative = left)
            y_offset: Vertical movement (positive = down, negative = up)
            duration: Movement duration in seconds (default: 0.2s)
        """
        try:
            pyautogui.moveRel(x_offset, y_offset, duration=duration)
            self.logger.info(f"Moved mouse by offset ({x_offset}, {y_offset})")
        except Exception as e:
            self.logger.error(f"Error moving mouse by offset ({x_offset}, {y_offset}): {str(e)}")
            raise
    
    def move_to_position_by_name(self, position_name: str, duration: float = 0.2) -> bool:
        """
        Move to a named screen position (center, top-left, etc.).
        
        Args:
            position_name: Name of the position (center, top-left, etc.)
            duration: Movement duration in seconds
            
        Returns:
            True if successful, False if position name not recognized
        """
        positions = {
            "center": (self.screen_width // 2, self.screen_height // 2),
            "top-left": (0, 0),
            "top-right": (self.screen_width - 1, 0),
            "bottom-left": (0, self.screen_height - 1),
            "bottom-right": (self.screen_width - 1, self.screen_height - 1),
            "top-center": (self.screen_width // 2, 0),
            "bottom-center": (self.screen_width // 2, self.screen_height - 1),
            "left-center": (0, self.screen_height // 2),
            "right-center": (self.screen_width - 1, self.screen_height // 2),
        }
        
        if position_name.lower() in positions:
            x, y = positions[position_name.lower()]
            self.move_to(x, y, duration)
            return True
        else:
            self.logger.warning(f"Position name '{position_name}' not recognized")
            return False
    
    def click(self, button: str = "left", clicks: int = 1) -> None:
        """
        Click at the current mouse position.
        
        Args:
            button: Mouse button to click ('left', 'right', or 'middle')
            clicks: Number of clicks (default: 1)
        """
        try:
            pyautogui.click(button=button, clicks=clicks)
            self.logger.info(f"Clicked {button} button {clicks} time(s)")
        except Exception as e:
            self.logger.error(f"Error clicking {button} button: {str(e)}")
            raise
    
    def click_at(self, x: int, y: int, button: str = "left", clicks: int = 1, duration: float = 0.2) -> None:
        """
        Move to specified coordinates and click.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button to click ('left', 'right', or 'middle')
            clicks: Number of clicks (default: 1)
            duration: Movement duration in seconds (default: 0.2s)
        """
        try:
            self.move_to(x, y, duration)
            self.click(button, clicks)
            self.logger.info(f"Clicked at ({x}, {y}) with {button} button {clicks} time(s)")
        except Exception as e:
            self.logger.error(f"Error clicking at ({x}, {y}): {str(e)}")
            raise
    
    def double_click(self) -> None:
        """Perform a double click at the current mouse position."""
        self.click(clicks=2)
    
    def right_click(self) -> None:
        """Perform a right click at the current mouse position."""
        self.click(button="right")
    
    def drag_to(self, x: int, y: int, button: str = "left", duration: float = 0.2) -> None:
        """
        Drag from current position to specified coordinates.
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            button: Mouse button to use for dragging
            duration: Drag duration in seconds
        """
        try:
            pyautogui.dragTo(x, y, button=button, duration=duration)
            self.logger.info(f"Dragged to ({x}, {y}) with {button} button")
        except Exception as e:
            self.logger.error(f"Error dragging to ({x}, {y}): {str(e)}")
            raise
    
    def drag_relative(self, x_offset: int, y_offset: int, button: str = "left", duration: float = 0.2) -> None:
        """
        Drag from current position by a relative offset.
        
        Args:
            x_offset: Horizontal drag distance
            y_offset: Vertical drag distance
            button: Mouse button to use for dragging
            duration: Drag duration in seconds
        """
        try:
            pyautogui.dragRel(x_offset, y_offset, button=button, duration=duration)
            self.logger.info(f"Dragged by offset ({x_offset}, {y_offset}) with {button} button")
        except Exception as e:
            self.logger.error(f"Error dragging by offset ({x_offset}, {y_offset}): {str(e)}")
            raise
    
    def scroll(self, clicks: int) -> None:
        """
        Scroll the mouse wheel.
        
        Args:
            clicks: Number of "clicks" to scroll (positive = up, negative = down)
        """
        try:
            pyautogui.scroll(clicks)
            self.logger.info(f"Scrolled {clicks} clicks {'up' if clicks > 0 else 'down'}")
        except Exception as e:
            self.logger.error(f"Error scrolling: {str(e)}")
            raise