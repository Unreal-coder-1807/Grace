"""
Voice Module for gesture-voice-control system.

This module handles all voice-related functionality including:
- Voice command recognition
- Text-to-speech output
- Hotword detection
- Voice-based authentication
- Intent handling
"""

from .listener import VoiceListener
from .speaker import Speaker
from .intent_handler import IntentHandler
from .hotword_detector import HotwordDetector
from .voice_authentication import VoiceAuthenticator

__all__ = [
    'VoiceListener',
    'Speaker',
    'IntentHandler',
    'HotwordDetector',
    'VoiceAuthenticator'
]