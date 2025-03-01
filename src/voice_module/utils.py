"""
Utility functions for the voice module.

This module provides helper functions for voice processing, file operations,
and other common tasks required by the voice module components.
"""

import os
import numpy as np
import pyaudio
import wave
import logging
from typing import Tuple, List, Dict, Optional, Union, Any
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import split_on_silence

# Set up logger for this module
logger = logging.getLogger(__name__)

# Audio constants
RATE = 16000
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
SILENCE_THRESHOLD = 500  # Silence threshold for voice activity detection

def ensure_dir_exists(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Path object to the directory
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_audio_device_info() -> List[Dict[str, Any]]:
    """
    Get information about available audio devices.
    
    Returns:
        List of dictionaries containing device information
    """
    p = pyaudio.PyAudio()
    info = []
    
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        info.append(device_info)
    
    p.terminate()
    return info

def get_default_audio_device() -> Dict[str, Any]:
    """
    Get the default audio input device information.
    
    Returns:
        Dictionary with default device information
    """
    p = pyaudio.PyAudio()
    default_device = p.get_default_input_device_info()
    p.terminate()
    return default_device

def record_audio(duration: int = 5, 
                rate: int = RATE, 
                chunk: int = CHUNK, 
                format: int = FORMAT, 
                channels: int = CHANNELS) -> np.ndarray:
    """
    Record audio for a specified duration.
    
    Args:
        duration: Recording duration in seconds
        rate: Sampling rate
        chunk: Frames per buffer
        format: Audio format
        channels: Number of audio channels
        
    Returns:
        Numpy array of audio data
    """
    p = pyaudio.PyAudio()
    
    stream = p.open(
        format=format,
        channels=channels,
        rate=rate,
        input=True,
        frames_per_buffer=chunk
    )
    
    logger.info(f"Recording for {duration} seconds...")
    frames = []
    
    for i in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)
    
    logger.info("Recording finished")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Convert frames to numpy array
    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
    return audio_data

def save_audio(audio_data: np.ndarray, 
              filename: str, 
              rate: int = RATE, 
              channels: int = CHANNELS) -> str:
    """
    Save audio data to a WAV file.
    
    Args:
        audio_data: Numpy array of audio data
        filename: Output filename
        rate: Sampling rate
        channels: Number of audio channels
        
    Returns:
        Path to the saved file
    """
    # Ensure directory exists
    path = Path(filename)
    ensure_dir_exists(path.parent)
    
    # Save as WAV file
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(rate)
        wf.writeframes(audio_data.tobytes())
    
    logger.info(f"Audio saved to {filename}")
    return str(path)

def load_audio(filename: str) -> np.ndarray:
    """
    Load audio data from a WAV file.
    
    Args:
        filename: Path to WAV file
        
    Returns:
        Numpy array of audio data
    """
    with wave.open(filename, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        audio_data = np.frombuffer(frames, dtype=np.int16)
    
    return audio_data

def detect_voice_activity(audio_data: np.ndarray, 
                         threshold: int = SILENCE_THRESHOLD) -> bool:
    """
    Detect if there is voice activity in the audio data.
    
    Args:
        audio_data: Numpy array of audio data
        threshold: Amplitude threshold for voice activity
        
    Returns:
        True if voice activity is detected, False otherwise
    """
    # Simple energy-based voice activity detection
    energy = np.abs(audio_data).mean()
    return energy > threshold

def extract_audio_features(audio_data: np.ndarray, rate: int = RATE) -> np.ndarray:
    """
    Extract basic audio features (energy, zero-crossing rate) from audio data.
    
    Args:
        audio_data: Numpy array of audio data
        rate: Sampling rate
        
    Returns:
        Numpy array of features
    """
    # Calculate energy
    energy = np.abs(audio_data).mean()
    
    # Calculate zero-crossing rate
    zero_crossings = np.sum(np.abs(np.diff(np.signbit(audio_data)))) / len(audio_data)
    
    # Return features as array
    features = np.array([energy, zero_crossings])
    
    return features

def remove_silence(audio_file: str, min_silence_len: int = 500, silence_thresh: int = -40) -> str:
    """
    Remove silence from an audio file.
    
    Args:
        audio_file: Path to input audio file
        min_silence_len: Minimum length of silence (ms)
        silence_thresh: Silence threshold (dB)
        
    Returns:
        Path to processed audio file
    """
    # Load audio file
    sound = AudioSegment.from_file(audio_file)
    
    # Split on silence
    chunks = split_on_silence(
        sound,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh
    )
    
    # Combine chunks with a short silence between them
    short_silence = AudioSegment.silent(duration=100)
    processed_audio = short_silence
    
    for chunk in chunks:
        processed_audio += chunk + short_silence
    
    # Export processed audio
    output_file = os.path.splitext(audio_file)[0] + "_processed.wav"
    processed_audio.export(output_file, format="wav")
    
    return output_file

def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """
    Normalize audio data to have zero mean and unit variance.
    
    Args:
        audio_data: Numpy array of audio data
        
    Returns:
        Normalized audio data
    """
    # Remove DC offset
    audio_data = audio_data - np.mean(audio_data)
    
    # Normalize amplitude
    if np.std(audio_data) > 0:
        audio_data = audio_data / np.std(audio_data)
    
    return audio_data

def get_audio_duration(filename: str) -> float:
    """
    Get the duration of an audio file in seconds.
    
    Args:
        filename: Path to audio file
        
    Returns:
        Duration in seconds
    """
    with wave.open(filename, 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)
    
    return duration