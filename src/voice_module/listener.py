"""
Voice Listener component for processing audio input and converting it to text.

This module uses OpenAI Whisper as the primary speech-to-text engine,
with fallback to other recognition systems if needed.
"""

import os
import threading
import queue
import numpy as np
import whisper
import pyaudio
import wave
from typing import Optional, Callable, List, Dict, Any, Union
import logging

# Setup logger
logger = logging.getLogger(__name__)

class VoiceListener:
    """
    Handles voice input capture and speech-to-text conversion.
    
    Uses OpenAI's Whisper model for offline speech recognition with
    high accuracy across multiple languages.
    """
    
    def __init__(
        self,
        model_size: str = "base",
        language: str = "en",
        sample_rate: int = 16000,
        device_index: Optional[int] = None,
        chunk_size: int = 1024,
        channels: int = 1,
        format_type: int = pyaudio.paInt16,
        max_queue_size: int = 100,
        callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the VoiceListener.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code for recognition
            sample_rate: Audio sample rate in Hz
            device_index: PyAudio device index for microphone
            chunk_size: Size of audio chunks to process
            channels: Number of audio channels (1 for mono, 2 for stereo)
            format_type: PyAudio format type
            max_queue_size: Maximum size of the audio buffer queue
            callback: Function to call when speech is recognized
        """
        self.model_size = model_size
        self.language = language
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.chunk_size = chunk_size
        self.channels = channels
        self.format_type = format_type
        self.callback = callback
        
        # Audio processing properties
        self.audio_queue = queue.Queue(maxsize=max_queue_size)
        self.is_listening = False
        self.listen_thread = None
        self.process_thread = None
        self.py_audio = None
        self.stream = None
        
        # Load Whisper model
        logger.info(f"Loading Whisper model: {model_size}")
        self.model = whisper.load_model(model_size)
        logger.info("Whisper model loaded successfully")
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for PyAudio to capture audio data."""
        if self.is_listening:
            try:
                self.audio_queue.put(in_data)
            except queue.Full:
                logger.warning("Audio queue is full, dropping audio chunk")
        return (in_data, pyaudio.paContinue)
    
    def start_listening(self):
        """Start listening for audio input."""
        if self.is_listening:
            logger.warning("Already listening")
            return
            
        self.is_listening = True
        
        # Initialize PyAudio
        self.py_audio = pyaudio.PyAudio()
        
        # Open audio stream
        self.stream = self.py_audio.open(
            format=self.format_type,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=self.device_index,
            stream_callback=self._audio_callback
        )
        
        # Start the stream
        self.stream.start_stream()
        logger.info("Audio stream started")
        
        # Start processing thread
        self.process_thread = threading.Thread(target=self._process_audio)
        self.process_thread.daemon = True
        self.process_thread.start()
        logger.info("Voice listener started successfully")
    
    def stop_listening(self):
        """Stop listening for audio input."""
        if not self.is_listening:
            return
            
        self.is_listening = False
        
        # Stop and close the stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        # Terminate PyAudio
        if self.py_audio:
            self.py_audio.terminate()
            self.py_audio = None
            
        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
                
        logger.info("Voice listener stopped")
    
    def _process_audio(self):
        """Process audio chunks and convert to text using Whisper."""
        audio_data = []
        silence_threshold = 300  # Adjust based on your microphone
        silent_chunks = 0
        is_speaking = False
        max_silent_chunks = 30  # About 1-2 seconds of silence
        
        logger.info("Audio processing thread started")
        
        while self.is_listening:
            # Get audio chunk from queue
            try:
                chunk = self.audio_queue.get(timeout=1)
                audio_data.append(chunk)
                
                # Check if this is speech or silence
                chunk_np = np.frombuffer(chunk, dtype=np.int16)
                volume = np.abs(chunk_np).mean()
                
                if volume > silence_threshold:
                    is_speaking = True
                    silent_chunks = 0
                elif is_speaking:
                    silent_chunks += 1
                    
                # If we've collected speech followed by silence, process it
                if is_speaking and silent_chunks > max_silent_chunks:
                    self._transcribe_audio(b''.join(audio_data))
                    audio_data = []
                    is_speaking = False
                    silent_chunks = 0
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                
    def _transcribe_audio(self, audio_data):
        """Transcribe audio data to text using Whisper."""
        if not audio_data:
            return
            
        # Save temporary WAV file
        temp_file = "temp_recording.wav"
        with wave.open(temp_file, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)
            
        try:
            # Transcribe with Whisper
            result = self.model.transcribe(
                temp_file,
                language=self.language,
                fp16=False
            )
            
            transcribed_text = result["text"].strip()
            
            if transcribed_text and self.callback:
                logger.info(f"Transcribed: {transcribed_text}")
                self.callback(transcribed_text)
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
    def record_sample(self, duration=5.0):
        """
        Record an audio sample for a specific duration.
        
        Args:
            duration: Duration to record in seconds
            
        Returns:
            bytes: Raw audio data
        """
        py_audio = pyaudio.PyAudio()
        frames = []
        
        # Create a new stream for recording
        stream = py_audio.open(
            format=self.format_type,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=self.device_index
        )
        
        # Calculate chunks to record
        chunks_to_record = int(self.sample_rate / self.chunk_size * duration)
        
        logger.info(f"Recording {duration} seconds of audio...")
        
        # Record data
        for _ in range(chunks_to_record):
            data = stream.read(self.chunk_size)
            frames.append(data)
            
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        py_audio.terminate()
        
        logger.info("Recording complete")
        
        return b''.join(frames)
    
    def save_audio_sample(self, audio_data, filename):
        """
        Save audio data to a WAV file.
        
        Args:
            audio_data: Raw audio data bytes
            filename: Output filename
        """
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)
            
        logger.info(f"Audio sample saved to {filename}")