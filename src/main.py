#!/usr/bin/env python3
"""
Gesture Voice Control System
----------------------------
Main application entry point for a multimodal computer control system
using gesture recognition and voice commands.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path to ensure imports work correctly
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import modules
from gesture_module.detector import GestureDetector
from voice_module.listener import VoiceListener
from voice_module.hotword_detector import HotwordDetector
from auth_module.auth_manager import AuthManager
from control_system.system_control import SystemController
from logging.log_manager import LogManager
from database.models import initialize_database
from utils.system.file_utils import load_config


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Gesture and Voice Control System")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/settings/app.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["voice", "gesture", "both"], 
        default="both",
        help="Operation mode: voice, gesture, or both"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    parser.add_argument(
        "--no-auth", 
        action="store_true", 
        help="Disable authentication (not recommended for production)"
    )
    return parser.parse_args()


class Application:
    """Main application class managing all components."""
    
    def __init__(self, config_path, mode="both", debug=False, auth_enabled=True):
        """Initialize the application with configurations."""
        # Setup logging
        self.logger = LogManager().get_logger(__name__)
        self.logger.info("Initializing Gesture Voice Control System")
        
        # Load configurations
        self.config = load_config(config_path)
        self.debug = debug
        self.mode = mode
        
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug("Debug mode enabled")
        
        # Initialize database
        initialize_database()
        
        # Initialize authentication system
        self.auth_enabled = auth_enabled
        if self.auth_enabled:
            self.auth_manager = AuthManager()
            self.logger.info("Authentication system initialized")
        else:
            self.logger.warning("Authentication disabled - running in unsecured mode")
        
        # Initialize system controller
        self.system_controller = SystemController(self.config)
        
        # Initialize modules based on mode
        self.gesture_detector = None
        self.voice_listener = None
        self.hotword_detector = None
        
        if mode in ["gesture", "both"]:
            self.gesture_detector = GestureDetector(
                self.config["gesture"],
                self.system_controller
            )
            self.logger.info("Gesture module initialized")
            
        if mode in ["voice", "both"]:
            # Initialize hotword detector first
            self.hotword_detector = HotwordDetector(
                self.config["voice"]["hotword"],
                callback=self._hotword_detected
            )
            
            # Initialize voice listener
            self.voice_listener = VoiceListener(
                self.config["voice"],
                self.system_controller
            )
            self.logger.info("Voice module initialized")
    
    def _hotword_detected(self):
        """Callback when hotword is detected."""
        self.logger.debug("Hotword detected, listening for command")
        if self.voice_listener:
            self.voice_listener.listen_for_command()
    
    def authenticate_user(self):
        """Authenticate the user before starting the system."""
        if not self.auth_enabled:
            return True
            
        # Implement authentication logic based on configured methods
        auth_methods = self.config["auth"]["methods"]
        
        if "voice" in auth_methods and self.voice_listener:
            self.logger.info("Attempting voice authentication")
            return self.auth_manager.authenticate_by_voice(self.voice_listener)
        elif "password" in auth_methods:
            self.logger.info("Attempting password authentication")
            # In a real implementation, this would prompt for credentials
            # Here we'll just return True for demonstration
            return self.auth_manager.authenticate_by_password("username", "password")
        
        self.logger.error("No valid authentication method available")
        return False
    
    def start(self):
        """Start the application."""
        self.logger.info(f"Starting application in {self.mode} mode")
        
        # Authenticate user if enabled
        if self.auth_enabled and not self.authenticate_user():
            self.logger.error("Authentication failed. Exiting.")
            return False
        
        # Start appropriate modules
        try:
            if self.mode in ["gesture", "both"] and self.gesture_detector:
                self.gesture_detector.start()
                
            if self.mode in ["voice", "both"] and self.hotword_detector:
                self.hotword_detector.start()
                
            self.logger.info("All systems started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting application: {str(e)}")
            return False
    
    def stop(self):
        """Stop all modules and clean up."""
        self.logger.info("Stopping application")
        
        if self.gesture_detector:
            self.gesture_detector.stop()
            
        if self.voice_listener:
            self.voice_listener.stop()
            
        if self.hotword_detector:
            self.hotword_detector.stop()
            
        self.logger.info("Application stopped")


def main():
    """Main function to run the application."""
    args = parse_arguments()
    
    app = Application(
        config_path=args.config,
        mode=args.mode,
        debug=args.debug,
        auth_enabled=not args.no_auth
    )
    
    if app.start():
        try:
            # Keep the application running
            # In a real implementation, this might integrate with an event loop
            # or a UI framework like Streamlit
            print("Application running. Press Ctrl+C to exit.")
            
            # Simple loop to keep the application running
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            app.stop()
    else:
        print("Failed to start application. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()