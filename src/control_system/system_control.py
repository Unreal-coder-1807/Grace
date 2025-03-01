"""
System control module.

This module handles OS-level system controls like application launching,
system power functions, and file operations.
"""

import logging
import os
import subprocess
import platform
import time
from typing import Dict, List, Optional, Union, Any

logger = logging.getLogger(__name__)

class SystemController:
    """Controller for OS-level system operations."""
    
    def __init__(self):
        """Initialize the system controller."""
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()  # 'Windows', 'Darwin' (macOS), or 'Linux'
        self.logger.info(f"System controller initialized for {self.system}")
    
    def open_application(self, app_name: str, app_path: Optional[str] = None) -> bool:
        """
        Open an application.
        
        Args:
            app_name: Name of the application to open
            app_path: Full path to the application executable (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if app_path and os.path.exists(app_path):
                # If app_path is provided and exists, use it directly
                path_to_use = app_path
            else:
                # If no explicit path, try to find it using the name
                path_to_use = app_name
            
            if self.system == "Windows":
                subprocess.Popen(f"start {path_to_use}", shell=True)
                self.logger.info(f"Opened application: {app_name}")
                return True
            elif self.system == "Darwin":  # macOS
                subprocess.Popen(["open", "-a", path_to_use])
                self.logger.info(f"Opened application: {app_name}")
                return True
            elif self.system == "Linux":
                subprocess.Popen([path_to_use])
                self.logger.info(f"Opened application: {app_name}")
                return True
            else:
                self.logger.warning(f"Unsupported platform: {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error opening application {app_name}: {str(e)}")
            return False
    
    def close_application(self, app_name: str) -> bool:
        """
        Close an application.
        
        Args:
            app_name: Name of the application to close
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.system == "Windows":
                os.system(f"taskkill /f /im {app_name}.exe")
                self.logger.info(f"Closed application: {app_name}")
                return True
            elif self.system == "Darwin":  # macOS
                os.system(f"pkill -x '{app_name}'")
                self.logger.info(f"Closed application: {app_name}")
                return True
            elif self.system == "Linux":
                os.system(f"pkill {app_name}")
                self.logger.info(f"Closed application: {app_name}")
                return True
            else:
                self.logger.warning(f"Unsupported platform: {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error closing application {app_name}: {str(e)}")
            return False
    
    def system_shutdown(self) -> bool:
        """
        Initiate system shutdown.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.system == "Windows":
                os.system("shutdown /s /t 60")
                self.logger.info("Initiated Windows shutdown (60s delay)")
                return True
            elif self.system == "Darwin":  # macOS
                os.system("sudo shutdown -h +1")  # +1 minute
                self.logger.info("Initiated macOS shutdown (1 min delay)")
                return True
            elif self.system == "Linux":
                os.system("sudo shutdown -h +1")  # +1 minute
                self.logger.info("Initiated Linux shutdown (1 min delay)")
                return True
            else:
                self.logger.warning(f"Unsupported platform: {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error initiating shutdown: {str(e)}")
            return False
    
    def system_restart(self) -> bool:
        """
        Initiate system restart.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.system == "Windows":
                os.system("shutdown /r /t 60")
                self.logger.info("Initiated Windows restart (60s delay)")
                return True
            elif self.system == "Darwin":  # macOS
                os.system("sudo shutdown -r +1")  # +1 minute
                self.logger.info("Initiated macOS restart (1 min delay)")
                return True
            elif self.system == "Linux":
                os.system("sudo shutdown -r +1")  # +1 minute
                self.logger.info("Initiated Linux restart (1 min delay)")
                return True
            else:
                self.logger.warning(f"Unsupported platform: {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error initiating restart: {str(e)}")
            return False
    
    def cancel_shutdown(self) -> bool:
        """
        Cancel a pending shutdown/restart.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.system == "Windows":
                os.system("shutdown /a")
                self.logger.info("Cancelled Windows shutdown/restart")
                return True
            elif self.system == "Darwin":  # macOS
                os.system("sudo killall shutdown")
                self.logger.info("Cancelled macOS shutdown/restart")
                return True
            elif self.system == "Linux":
                os.system("sudo shutdown -c")
                self.logger.info("Cancelled Linux shutdown/restart")
                return True
            else:
                self.logger.warning(f"Unsupported platform: {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error cancelling shutdown: {str(e)}")
            return False
    
    def system_sleep(self) -> bool:
        """
        Put the system to sleep/standby.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.system == "Windows":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                self.logger.info("Put Windows system to sleep")
                return True
            elif self.system == "Darwin":  # macOS
                os.system("pmset sleepnow")
                self.logger.info("Put macOS system to sleep")
                return True
            elif self.system == "Linux":
                os.system("systemctl suspend")
                self.logger.info("Put Linux system to sleep")
                return True
            else:
                self.logger.warning(f"Unsupported platform: {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error putting system to sleep: {str(e)}")
            return False
    
    def lock_screen(self) -> bool:
        """
        Lock the system screen.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.system == "Windows":
                os.system("rundll32.exe user32.dll,LockWorkStation")
                self.logger.info("Locked Windows screen")
                return True
            elif self.system == "Darwin":  # macOS
                os.system("/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend")
                self.logger.info("Locked macOS screen")
                return True
            elif self.system == "Linux":
                # This depends on the desktop environment (GNOME, KDE, etc.)
                os.system("xdg-screensaver lock")
                self.logger.info("Locked Linux screen")
                return True
            else:
                self.logger.warning(f"Unsupported platform: {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error locking screen: {str(e)}")
            return False
    
    def get_system_info(self) -> Dict[str, str]:
        """
        Get basic system information.
        
        Returns:
            Dictionary with system information
        """
        try:
            import socket
            import platform
            
            info = {
                "system": platform.system(),
                "node": platform.node(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": socket.gethostname(),
                "ip_address": socket.gethostbyname(socket.gethostname()),
            }
            
            self.logger.info("Retrieved system information")
            return info
        except Exception as e:
            self.logger.error(f"Error getting system info: {str(e)}")
            return {"error": str(e)}
    
    def get_running_processes(self) -> List[str]:
        """
        Get a list of running processes.
        
        Returns:
            List of running process names
        """
        try:
            import psutil
            
            processes = []
            for proc in psutil.process_iter(['name']):
                try:
                    processes.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            self.logger.info(f"Retrieved {len(processes)} running processes")
            return processes
        except ImportError:
            self.logger.error("psutil not installed, cannot get process list")
            return ["Error: psutil not installed"]
        except Exception as e:
            self.logger.error(f"Error getting process list: {str(e)}")
            return [f"Error: {str(e)}"]
    
    def open_file(self, file_path: str) -> bool:
        """
        Open a file with the default application.
        
        Args:
            file_path: Path to the file to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return False
            
            if self.system == "Windows":
                os.startfile(file_path)
                self.logger.info(f"Opened file: {file_path}")
                return True
            elif self.system == "Darwin":  # macOS
                subprocess.call(["open", file_path])
                self.logger.info(f"Opened file: {file_path}")
                return True
            elif self.system == "Linux":
                subprocess.call(["xdg-open", file_path])
                self.logger.info(f"Opened file: {file_path}")
                return True
            else:
                self.logger.warning(f"Unsupported platform: {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"Error opening file {file_path}: {str(e)}")
            return False