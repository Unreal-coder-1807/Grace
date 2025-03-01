"""
Speaker component for text-to-speech conversion.

This module handles text-to-speech output using pyttsx3 with
configurable voice parameters.
"""

import pyttsx3
import threading
import logging
from typing import Optional, Dict, List, Any

# Setup logger
logger = logging.getLogger(__name__)

class Speaker:
    """
    Text-to-speech component for voice output.
    
    Uses pyttsx3 for offline text-to-speech capabilities with
    configurable voice, rate, and volume.
    """
    
    def __init__(
        self,
        rate: int = 150,
        volume: float = 1.0,
        voice_id: Optional[str] = None,
        use_threading: bool = True
    ):
        """
        Initialize the Speaker.
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice_id: Specific voice ID to use
            use_threading: Whether to use threading for speech output
        """
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self.use_threading = use_threading
        self.engine = None
        self.is_speaking = False
        self.speech_thread = None
        
        # Initialize the TTS engine
        self._initialize_engine()
        
    def _initialize_engine(self):
        """Initialize the pyttsx3 engine with configured parameters."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Set voice if specified, otherwise use default
            if self.voice_id:
                self.engine.setProperty('voice', self.voice_id)
            
            logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
            
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get a list of available voices.
        
        Returns:
            List of voice information dictionaries
        """
        if not self.engine:
            self._initialize_engine()
            
        if not self.engine:
            logger.error("TTS engine not available")
            return []
            
        voices = []
        for voice in self.engine.getProperty('voices'):
            voices.append({
                'id': voice.id,
                'name': voice.name,
                'languages': voice.languages,
                'gender': voice.gender,
                'age': voice.age
            })
            
        return voices
        
    def set_voice(self, voice_id: str) -> bool:
        """
        Set the voice to use for speech.
        
        Args:
            voice_id: ID of the voice to use
            
        Returns:
            bool: Success or failure
        """
        if not self.engine:
            self._initialize_engine()
            
        if not self.engine:
            logger.error("TTS engine not available")
            return False
            
        try:
            self.engine.setProperty('voice', voice_id)
            self.voice_id = voice_id
            logger.info(f"Voice set to: {voice_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set voice: {e}")
            return False
            
    def set_rate(self, rate: int) -> bool:
        """
        Set the speech rate.
        
        Args:
            rate: Speech rate (words per minute)
            
        Returns:
            bool: Success or failure
        """
        if not self.engine:
            self._initialize_engine()
            
        if not self.engine:
            logger.error("TTS engine not available")
            return False
            
        try:
            self.engine.setProperty('rate', rate)
            self.rate = rate
            logger.info(f"Speech rate set to: {rate}")
            return True
        except Exception as e:
            logger.error(f"Failed to set speech rate: {e}")
            return False
            
    def set_volume(self, volume: float) -> bool:
        """
        Set the speech volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: Success or failure
        """
        if not self.engine:
            self._initialize_engine()
            
        if not self.engine:
            logger.error("TTS engine not available")
            return False
        
        # Ensure volume is within valid range
        volume = max(0.0, min(1.0, volume))
            
        try:
            self.engine.setProperty('volume', volume)
            self.volume = volume
            logger.info(f"Speech volume set to: {volume}")
            return True
        except Exception as e:
            logger.error(f"Failed to set speech volume: {e}")
            return False
    
    def _speak_thread(self, text: str):
        """
        Thread function for speaking text.
        
        Args:
            text: Text to speak
        """
        try:
            self.is_speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error in speech thread: {e}")
        finally:
            self.is_speaking = False
            
    def speak(self, text: str) -> bool:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            bool: Success or failure
        """
        if not text:
            logger.warning("Empty text provided to speak")
            return False
            
        if not self.engine:
            self._initialize_engine()
            
        if not self.engine:
            logger.error("TTS engine not available")
            return False
            
        # Use threading if configured
        if self.use_threading:
            # Don't start a new thread if already speaking
            if self.is_speaking and self.speech_thread and self.speech_thread.is_alive():
                logger.warning("Already speaking, text ignored")
                return False
                
            self.speech_thread = threading.Thread(target=self._speak_thread, args=(text,))
            self.speech_thread.daemon = True
            self.speech_thread.start()
            logger.info(f"Speaking (threaded): {text[:50]}...")
            return True
        else:
            # Speak directly in the current thread
            try:
                self.is_speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
                logger.info(f"Spoke: {text[:50]}...")
                return True
            except Exception as e:
                logger.error(f"Speech error: {e}")
                return False
            finally:
                self.is_speaking = False
                
    def stop(self):
        """Stop the current speech."""
        if self.engine and self.is_speaking:
            try:
                self.engine.stop()
                logger.info("Speech stopped")
            except Exception as e:
                logger.error(f"Error stopping speech: {e}")
                
    def is_busy(self) -> bool:
        """
        Check if the speaker is currently speaking.
        
        Returns:
            bool: True if speaking, False otherwise
        """
        return self.is_speaking