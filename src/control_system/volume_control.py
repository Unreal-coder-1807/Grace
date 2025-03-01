"""
Volume control module using pycaw for Windows.

This module handles system volume operations like adjusting volume,
muting/unmuting, and controlling audio devices.
"""

import logging
import platform
from typing import Dict, List, Optional, Union, Tuple

# Set up logger
logger = logging.getLogger(__name__)

class VolumeController:
    """Controller for system volume operations."""
    
    def __init__(self):
        """Initialize the volume controller with platform-specific implementation."""
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
        
        # Check if running on Windows and import pycaw
        if self.system == "Windows":
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                self.devices = AudioUtilities.GetSpeakers()
                self.interface = self.devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))
                self.windows_support = True
                self.logger.info("Volume controller initialized for Windows")
            except ImportError:
                self.logger.warning("pycaw not installed, Windows volume control unavailable")
                self.windows_support = False
            except Exception as e:
                self.logger.error(f"Error initializing Windows volume control: {str(e)}")
                self.windows_support = False
        elif self.system == "Darwin":  # macOS
            try:
                import osascript
                self.macos_support = True
                self.logger.info("Volume controller initialized for macOS")
            except ImportError:
                self.logger.warning("osascript not available, macOS volume control limited")
                self.macos_support = False
        elif self.system == "Linux":
            try:
                import alsaaudio
                self.linux_support = True
                self.logger.info("Volume controller initialized for Linux")
            except ImportError:
                self.logger.warning("alsaaudio not installed, Linux volume control unavailable")
                self.linux_support = False
        else:
            self.logger.warning(f"Unsupported platform: {self.system}")
    
    def get_volume(self) -> float:
        """
        Get the current system volume.
        
        Returns:
            Volume level as a float between 0.0 and 1.0
        """
        try:
            if self.system == "Windows" and hasattr(self, 'windows_support') and self.windows_support:
                # Windows implementation
                current_volume = self.volume.GetMasterVolumeLevelScalar()
                self.logger.debug(f"Current Windows volume: {current_volume:.2f}")
                return current_volume
            elif self.system == "Darwin" and hasattr(self, 'macos_support') and self.macos_support:
                # macOS implementation
                import osascript
                result = osascript.osascript('get output volume of (get volume settings)')
                if result[0] == 0:  # Success
                    volume = float(result[1]) / 100
                    self.logger.debug(f"Current macOS volume: {volume:.2f}")
                    return volume
                else:
                    self.logger.error(f"Error getting macOS volume: {result}")
                    return 0.0
            elif self.system == "Linux" and hasattr(self, 'linux_support') and self.linux_support:
                # Linux implementation
                import alsaaudio
                mixer = alsaaudio.Mixer()
                volume = mixer.getvolume()[0] / 100.0
                self.logger.debug(f"Current Linux volume: {volume:.2f}")
                return volume
            else:
                self.logger.warning(f"Volume get not supported on {self.system}")
                return 0.0
        except Exception as e:
            self.logger.error(f"Error getting volume: {str(e)}")
            return 0.0
    
    def set_volume(self, level: float) -> bool:
        """
        Set the system volume.
        
        Args:
            level: Volume level as a float between 0.0 and 1.0
            
        Returns:
            True if successful, False otherwise
        """
        # Ensure level is between 0 and 1
        level = max(0.0, min(1.0, level))
        
        try:
            if self.system == "Windows" and hasattr(self, 'windows_support') and self.windows_support:
                # Windows implementation
                self.volume.SetMasterVolumeLevelScalar(level, None)
                self.logger.info(f"Set Windows volume to {level:.2f}")
                return True
            elif self.system == "Darwin" and hasattr(self, 'macos_support') and self.macos_support:
                # macOS implementation
                import osascript
                vol_int = int(level * 100)
                result = osascript.osascript(f'set volume output volume {vol_int}')
                if result[0] == 0:  # Success
                    self.logger.info(f"Set macOS volume to {level:.2f}")
                    return True
                else:
                    self.logger.error(f"Error setting macOS volume: {result}")
                    return False
            elif self.system == "Linux" and hasattr(self, 'linux_support') and self.linux_support:
                # Linux implementation
                import alsaaudio
                mixer = alsaaudio.Mixer()
                vol_int = int(level * 100)
                mixer.setvolume(vol_int)
                self.logger.info(f"Set Linux volume to {level:.2f}")
                return True
            else:
                self.logger.warning(f"Volume set not supported on {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error setting volume: {str(e)}")
            return False
    
    def increase_volume(self, amount: float = 0.1) -> bool:
        """
        Increase system volume by specified amount.
        
        Args:
            amount: Amount to increase (0.0 to 1.0, default 0.1)
            
        Returns:
            True if successful, False otherwise
        """
        current = self.get_volume()
        return self.set_volume(current + amount)
    
    def decrease_volume(self, amount: float = 0.1) -> bool:
        """
        Decrease system volume by specified amount.
        
        Args:
            amount: Amount to decrease (0.0 to 1.0, default 0.1)
            
        Returns:
            True if successful, False otherwise
        """
        current = self.get_volume()
        return self.set_volume(current - amount)
    
    def mute(self) -> bool:
        """
        Mute the system volume.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.system == "Windows" and hasattr(self, 'windows_support') and self.windows_support:
                # Windows implementation
                self.volume.SetMute(1, None)
                self.logger.info("Muted Windows audio")
                return True
            elif self.system == "Darwin" and hasattr(self, 'macos_support') and self.macos_support:
                # macOS implementation
                import osascript
                result = osascript.osascript('set volume output muted true')
                if result[0] == 0:  # Success
                    self.logger.info("Muted macOS audio")
                    return True
                else:
                    self.logger.error(f"Error muting macOS audio: {result}")
                    return False
            elif self.system == "Linux" and hasattr(self, 'linux_support') and self.linux_support:
                # Linux implementation
                import alsaaudio
                mixer = alsaaudio.Mixer()
                mixer.setmute(1)
                self.logger.info("Muted Linux audio")
                return True
            else:
                self.logger.warning(f"Mute not supported on {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error muting audio: {str(e)}")
            return False
    
    def unmute(self) -> bool:
        """
        Unmute the system volume.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.system == "Windows" and hasattr(self, 'windows_support') and self.windows_support:
                # Windows implementation
                self.volume.SetMute(0, None)
                self.logger.info("Unmuted Windows audio")
                return True
            elif self.system == "Darwin" and hasattr(self, 'macos_support') and self.macos_support:
                # macOS implementation
                import osascript
                result = osascript.osascript('set volume output muted false')
                if result[0] == 0:  # Success
                    self.logger.info("Unmuted macOS audio")
                    return True
                else:
                    self.logger.error(f"Error unmuting macOS audio: {result}")
                    return False
            elif self.system == "Linux" and hasattr(self, 'linux_support') and self.linux_support:
                # Linux implementation
                import alsaaudio
                mixer = alsaaudio.Mixer()
                mixer.setmute(0)
                self.logger.info("Unmuted Linux audio")
                return True
            else:
                self.logger.warning(f"Unmute not supported on {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error unmuting audio: {str(e)}")
            return False
    
    def toggle_mute(self) -> bool:
        """
        Toggle between muted and unmuted states.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.system == "Windows" and hasattr(self, 'windows_support') and self.windows_support:
                # Windows implementation
                is_muted = self.volume.GetMute()
                self.volume.SetMute(not is_muted, None)
                self.logger.info(f"Toggled Windows mute {'off' if is_muted else 'on'}")
                return True
            elif self.system == "Darwin" and hasattr(self, 'macos_support') and self.macos_support:
                # macOS implementation
                import osascript
                # Get current mute state
                result = osascript.osascript('output muted of (get volume settings)')
                if result[0] == 0:  # Success
                    is_muted = result[1].strip() == "true"
                    toggle_cmd = f'set volume output muted {"false" if is_muted else "true"}'
                    toggle_result = osascript.osascript(toggle_cmd)
                    if toggle_result[0] == 0:  # Success
                        self.logger.info(f"Toggled macOS mute {'off' if is_muted else 'on'}")
                        return True
                return False
            elif self.system == "Linux" and hasattr(self, 'linux_support') and self.linux_support:
                # Linux implementation
                import alsaaudio
                mixer = alsaaudio.Mixer()
                is_muted = mixer.getmute()[0] == 1
                mixer.setmute(0 if is_muted else 1)
                self.logger.info(f"Toggled Linux mute {'off' if is_muted else 'on'}")
                return True
            else:
                self.logger.warning(f"Toggle mute not supported on {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error toggling mute: {str(e)}")
            return False