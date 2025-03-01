"""
Utility functions for the Streamlit application.
These helpers support various UI components and functionality across pages.
"""

import streamlit as st
import sys
from pathlib import Path
import datetime
import json
import os
import yaml
from typing import Dict, List, Any, Optional, Union

# Add the parent directory to path to enable relative imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from logging.log_manager import get_logger
from utils.system.file_utils import safe_read_file, safe_write_file
from utils.system.encryption import encrypt_data, decrypt_data

logger = get_logger(__name__)

def load_config(config_name: str) -> Dict[str, Any]:
    """
    Load configuration from the config directory.
    
    Args:
        config_name: Name of the configuration file without extension
        
    Returns:
        Dictionary containing configuration values
    """
    config_path = Path(parent_dir) / "config" / "settings" / f"{config_name}.yaml"
    
    try:
        if config_path.exists():
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        else:
            logger.warning(f"Configuration file {config_name}.yaml not found")
            return {}
    except Exception as e:
        logger.error(f"Error loading configuration {config_name}: {str(e)}")
        return {}

def save_config(config_name: str, config_data: Dict[str, Any]) -> bool:
    """
    Save configuration to the config directory.
    
    Args:
        config_name: Name of the configuration file without extension
        config_data: Dictionary containing configuration values
        
    Returns:
        True if saved successfully, False otherwise
    """
    config_path = Path(parent_dir) / "config" / "settings" / f"{config_name}.yaml"
    
    try:
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as file:
            yaml.dump(config_data, file, default_flow_style=False)
        
        logger.info(f"Configuration {config_name} saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration {config_name}: {str(e)}")
        return False

def display_notification(message: str, type: str = "info", duration: int = 5) -> None:
    """
    Display a notification message in the Streamlit UI.
    
    Args:
        message: The message to display
        type: Type of notification (info, success, warning, error)
        duration: Duration in seconds to display the message
    """
    if type == "info":
        placeholder = st.info(message)
    elif type == "success":
        placeholder = st.success(message)
    elif type == "warning":
        placeholder = st.warning(message)
    elif type == "error":
        placeholder = st.error(message)
    else:
        placeholder = st.info(message)
    
    # Auto-dismiss after duration if greater than 0
    if duration > 0:
        import time
        time.sleep(duration)
        placeholder.empty()

def format_timestamp(timestamp: Union[float, datetime.datetime, str]) -> str:
    """
    Format a timestamp into a human-readable string.
    
    Args:
        timestamp: Unix timestamp, datetime object, or ISO format string
        
    Returns:
        Formatted timestamp string
    """
    try:
        if isinstance(timestamp, float) or isinstance(timestamp, int):
            dt = datetime.datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, datetime.datetime):
            dt = timestamp
        elif isinstance(timestamp, str):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            return str(timestamp)
        
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error formatting timestamp: {str(e)}")
        return str(timestamp)

def get_user_settings(user_id: str) -> Dict[str, Any]:
    """
    Get user-specific settings.
    
    Args:
        user_id: User identifier
        
    Returns:
        Dictionary of user settings
    """
    settings_path = Path(parent_dir) / "data" / "user_settings" / f"{user_id}.json"
    
    try:
        if settings_path.exists():
            content = safe_read_file(settings_path)
            if content:
                return json.loads(content)
        
        # Return default settings if file doesn't exist
        return {
            "theme": "light",
            "voice_enabled": True,
            "gesture_enabled": True,
            "hotword": "Hey Assistant",
            "voice_sensitivity": 0.7,
            "gesture_sensitivity": 0.7,
            "notifications_enabled": True
        }
    except Exception as e:
        logger.error(f"Error loading user settings for {user_id}: {str(e)}")
        return {}

def save_user_settings(user_id: str, settings: Dict[str, Any]) -> bool:
    """
    Save user-specific settings.
    
    Args:
        user_id: User identifier
        settings: Dictionary of user settings
        
    Returns:
        True if saved successfully, False otherwise
    """
    settings_dir = Path(parent_dir) / "data" / "user_settings"
    settings_path = settings_dir / f"{user_id}.json"
    
    try:
        # Ensure directory exists
        settings_dir.mkdir(parents=True, exist_ok=True)
        
        content = json.dumps(settings, indent=2)
        return safe_write_file(settings_path, content)
    except Exception as e:
        logger.error(f"Error saving user settings for {user_id}: {str(e)}")
        return False

def get_theme_css() -> str:
    """
    Get custom CSS for the current theme.
    
    Returns:
        CSS string for the current theme
    """
    # Check if user is logged in and has theme preference
    theme = "light"
    if st.session_state.get("authenticated") and st.session_state.get("user_id"):
        user_settings = get_user_settings(st.session_state.user_id)
        theme = user_settings.get("theme", "light")
    
    # Define theme CSS
    if theme == "dark":
        return """
        .main-title {
            color: #ffffff;
        }
        .metric-value {
            color: #4e8df5;
        }
        .highlight {
            background-color: #2c3e50;
            padding: 5px;
            border-radius: 5px;
        }
        """
    else:  # light theme
        return """
        .main-title {
            color: #1e3a8a;
        }
        .metric-value {
            color: #4e8df5;
        }
        .highlight {
            background-color: #f1f5f9;
            padding: 5px;
            border-radius: 5px;
        }
        """

def apply_custom_css() -> None:
    """Apply custom CSS to the Streamlit app"""
    css = get_theme_css()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def create_key_metric(label: str, value: Any, delta: Optional[Any] = None, 
                     delta_color: str = "normal") -> None:
    """
    Create a styled key metric display.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Change in metric (optional)
        delta_color: Color of delta (normal, good, bad)
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color
    )

def format_log_level(level: str) -> str:
    """
    Format log level with appropriate color.
    
    Args:
        level: Log level string (INFO, WARNING, ERROR, etc.)
        
    Returns:
        HTML formatted string with appropriate color
    """
    level_upper = level.upper()
    if level_upper == "ERROR":
        return f"<span style='color:red'>{level_upper}</span>"
    elif level_upper == "WARNING":
        return f"<span style='color:orange'>{level_upper}</span>"
    elif level_upper == "INFO":
        return f"<span style='color:blue'>{level_upper}</span>"
    elif level_upper == "DEBUG":
        return f"<span style='color:gray'>{level_upper}</span>"
    else:
        return level_upper

def show_device_status(device_name: str, status: bool) -> None:
    """
    Show device status with color indicator.
    
    Args:
        device_name: Name of the device
        status: True if device is connected/active, False otherwise
    """
    if status:
        st.markdown(f"<span style='color:green'>●</span> {device_name}: Connected", 
                   unsafe_allow_html=True)
    else:
        st.markdown(f"<span style='color:red'>●</span> {device_name}: Disconnected", 
                   unsafe_allow_html=True)

def paginate_dataframe(df, page_size, page_num):
    """
    Paginate a dataframe for display.
    
    Args:
        df: Pandas DataFrame to paginate
        page_size: Number of rows per page
        page_num: Current page number (1-based)
        
    Returns:
        Sliced DataFrame for the current page
    """
    total_pages = (len(df) + page_size - 1) // page_size
    
    # Ensure valid page number
    page_num = max(1, min(page_num, total_pages))
    
    # Calculate start and end indices
    start_idx = (page_num - 1) * page_size
    end_idx = min(start_idx + page_size, len(df))
    
    return df.iloc[start_idx:end_idx], page_num, total_pages