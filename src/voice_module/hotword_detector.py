"""
Hotword detection component using Picovoice Porcupine.

This module enables wake word detection for initiating voice commands
without requiring continuous speech processing.
"""

import os
import pvporcupine
import pyaudio
import struct
import threading
import logging
from typing import Optional, List, Callable, Dict, Any

# Setup logger
logger = logging.getLogger(__name__)

class HotwordDetector:
    """
    Hotword detector using Picovoice Porcupine wake word engine.
    
    Listens for specific wake words to trigger voice command processing.
    """
    
    def __init__(
        self, 
        access_key: str,
        keywords: List[str] = ["alexa", "hey google", "computer"],
        sensitivities: Optional[List[float]] = None,
        model_path: Optional[str] = None,
        library_path: Optional[str] = None,
        callback: Optional[Callable[[str], None]] = None,
        device_index: Optional[int] = None
    ):
        """
        Initialize the hotword detector.
        
        Args:
            access_key: Picovoice access key
            keywords: List of keywords to detect
            sensitivities: Detection sensitivity for each keyword (0-1)
            model_path: Path to Porcupine model (if custom)
            library_path: Path to Porcupine library (if custom)
            callback: Function to call when a hotword is detected
            device_index: PyAudio device index for microphone
        """
        self.access_key = access_key
        self.keywords = keywords
        
        # Set default sensitivities if not provided
        if sensitivities is None:
            self.sensitivities = [0.5] * len(keywords)
        else:
            self.sensitivities = sensitivities
            
        self.model_path = model_path
        self.library_path = library_path
        self.callback = callback
        self.device_index = device_index
        
        # Runtime properties
        self.porcupine = None
        self.py_audio = None
        self.audio_stream = None
        self.is_listening = False
        self.listen_thread = None
        
        # Validate configuration
        if len(self.keywords) != len(self.sensitivities):
            raise ValueError("Number of keywords must match number of sensitivities")
            
        logger.info(f"Hotword detector initialized with keywords: {keywords}")
        
    def start(self):
        """Start listening for hotwords."""
        if self.is_listening:
            logger.warning("Hotword detector already running")
            return
            
        try:
            # Initialize Porcupine
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=self.keywords,
                sensitivities=self.sensitivities,
                model_path=self.model_path,
                library_path=self.library_path
            )
            
            # Initialize PyAudio
            self.py_audio = pyaudio.PyAudio()
            
            # Create audio stream
            self.audio_stream = self.py_audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                input_device_index=self.device_index
            )
            
            # Start listening thread
            self.is_listening = True
            self.listen_thread = threading.Thread(target=self._listen_loop)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            
            logger.info("Hotword detector started successfully")
            
        except Exception as e:
            self._cleanup()
            logger.error(f"Failed to start hotword detector: {e}")
            raise
            
    def stop(self):
        """Stop listening for hotwords."""
        if not self.is_listening:
            return
            
        self.is_listening = False
        
        # Wait for listening thread to finish
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2.0)
            
        self._cleanup()
        logger.info("Hotword detector stopped")
        
    def _cleanup(self):
        """Clean up resources."""
        # Close audio stream
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            
        # Terminate PyAudio
        if self.py_audio:
            self.py_audio.terminate()
            self.py_audio = None
            
        # Delete Porcupine instance
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
            
    def _listen_loop(self):
        """Main listening loop for hotword detection."""
        logger.info("Hotword detection thread started")
        
        while self.is_listening:
            try:
                # Read audio frame
                pcm = self.audio_stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                # Process with Porcupine
                keyword_index = self.porcupine.process(pcm)
                
                # Check if a keyword was detected
                if keyword_index >= 0 and keyword_index < len(self.keywords):
                    detected_keyword = self.keywords[keyword_index]
                    logger.info(f"Hotword detected: {detected_keyword}")
                    
                    # Call the callback if provided
                    if self.callback:
                        self.callback(detected_keyword)
                        
            except Exception as e:
                if self.is_listening:  # Only log if we're supposed to be listening
                    logger.error(f"Error in hotword detection: {e}")
                    
        logger.info("Hotword detection thread stopped")
        
    def get_audio_devices(self) -> List[Dict[str, Any]]:
        """
        Get a list of available audio input devices.
        
        Returns:
            List of dictionaries with device information
        """
        try:
            py_audio_temp = pyaudio.PyAudio()
            devices = []
            
            for i in range(py_audio_temp.get_device_count()):
                device_info = py_audio_temp.get_device_info_by_index(i)
                
                # Only include input devices
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
                    
            py_audio_temp.terminate()
            return devices
            
        except Exception as e:
            logger.error(f"Error getting audio devices: {e}")
            return []