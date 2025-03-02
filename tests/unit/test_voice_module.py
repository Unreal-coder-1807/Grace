import unittest
import os
import sys
import numpy as np
from unittest.mock import MagicMock, patch
import tempfile
import wave
import struct

# Add src to path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from voice_module.listener import VoiceListener
from voice_module.speaker import VoiceSpeaker
from voice_module.intent_handler import IntentHandler
from voice_module.hotword_detector import HotwordDetector
from voice_module.voice_authentication import VoiceAuthenticator

class TestVoiceListener(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            'sample_rate': 16000,
            'chunk_size': 1024,
            'silence_threshold': 500,
            'timeout': 5.0,
            'whisper_model': 'base'
        }
        self.listener = VoiceListener(config=self.mock_config)
    
    @patch('src.voice_module.listener.pyaudio.PyAudio')
    def test_initialize_listener(self, mock_pyaudio):
        listener = VoiceListener(config=self.mock_config)
        mock_pyaudio.assert_called_once()
    
    @patch('src.voice_module.listener.whisper.load_model')
    def test_load_model(self, mock_load_model):
        self.listener._load_model()
        mock_load_model.assert_called_once_with(self.mock_config['whisper_model'])

    @patch('src.voice_module.listener.VoiceListener.listen')
    @patch('src.voice_module.listener.VoiceListener._transcribe_audio')
    def test_listen_and_transcribe(self, mock_transcribe, mock_listen):
        # Create mock audio data
        mock_audio_data = b'test_audio_data'
        mock_listen.return_value = mock_audio_data
        
        # Mock the transcription result
        mock_transcribe.return_value = "test transcription"
        
        # Call the method
        result = self.listener.listen_and_transcribe()
        
        # Assert the mocks were called and correct result returned
        mock_listen.assert_called_once()
        mock_transcribe.assert_called_once_with(mock_audio_data)
        self.assertEqual(result, "test transcription")

class TestVoiceSpeaker(unittest.TestCase):
    def setUp(self):
        self.speaker = VoiceSpeaker()
    
    @patch('src.voice_module.speaker.pyttsx3.init')
    def test_initialize_speaker(self, mock_init):
        speaker = VoiceSpeaker()
        mock_init.assert_called_once()
    
    @patch('src.voice_module.speaker.VoiceSpeaker._get_engine')
    def test_speak_text(self, mock_get_engine):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        
        test_text = "Hello, this is a test"
        self.speaker.speak(test_text)
        
        mock_engine.say.assert_called_once_with(test_text)
        mock_engine.runAndWait.assert_called_once()
    
    @patch('src.voice_module.speaker.VoiceSpeaker._get_engine')
    def test_set_voice_properties(self, mock_get_engine):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        
        # Mock available voices
        mock_voice1 = MagicMock()
        mock_voice1.id = 'voice1'
        mock_voice2 = MagicMock()
        mock_voice2.id = 'voice2'
        mock_engine.getProperty.return_value = [mock_voice1, mock_voice2]
        
        # Test setting voice
        self.speaker.set_voice('voice2')
        mock_engine.setProperty.assert_called_with('voice', 'voice2')
        
        # Test setting rate
        self.speaker.set_rate(150)
        mock_engine.setProperty.assert_called_with('rate', 150)
        
        # Test setting volume
        self.speaker.set_volume(0.8)
        mock_engine.setProperty.assert_called_with('volume', 0.8)

class TestIntentHandler(unittest.TestCase):
    def setUp(self):
        # Mock out Rasa initialization
        with patch('src.voice_module.intent_handler.Agent') as mock_agent:
            self.intent_handler = IntentHandler()
            self.mock_agent = mock_agent
    
    def test_extract_intent(self):
        test_utterance = "What's the weather like today?"
        
        # Mock Rasa response
        mock_response = {
            'intent': {'name': 'weather_query', 'confidence': 0.95},
            'entities': [{'entity': 'time', 'value': 'today'}]
        }
        self.intent_handler.agent.parse = MagicMock(return_value=mock_response)
        
        intent, entities, confidence = self.intent_handler.extract_intent(test_utterance)
        
        self.assertEqual(intent, 'weather_query')
        self.assertEqual(entities, [{'entity': 'time', 'value': 'today'}])
        self.assertEqual(confidence, 0.95)
    
    def test_handle_intent(self):
        # Mock intent mapping and handlers
        self.intent_handler.intent_handlers = {
            'weather_query': MagicMock(return_value="Here's the weather")
        }
        
        response = self.intent_handler.handle_intent(
            'weather_query', 
            [{'entity': 'time', 'value': 'today'}]
        )
        
        self.intent_handler.intent_handlers['weather_query'].assert_called_once_with(
            [{'entity': 'time', 'value': 'today'}]
        )
        self.assertEqual(response, "Here's the weather")
    
    def test_handle_unknown_intent(self):
        response = self.intent_handler.handle_intent('unknown_intent', [])
        self.assertEqual(response, "I'm not sure how to handle that request")

class TestHotwordDetector(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            'access_key': 'test_key',
            'keyword_paths': ['test_keyword.ppn'],
            'sensitivities': [0.5]
        }
        
        # Patch pvporcupine to avoid actual initialization
        patcher = patch('src.voice_module.hotword_detector.pvporcupine.create')
        self.mock_create = patcher.start()
        self.addCleanup(patcher.stop)
        
        self.mock_create.return_value = MagicMock()
        self.detector = HotwordDetector(config=self.mock_config)
    
    def test_initialize_hotword_detector(self):
        detector = HotwordDetector(config=self.mock_config)
        
        # Verify porcupine was initialized with correct parameters
        self.mock_create.assert_called_once_with(
            access_key=self.mock_config['access_key'],
            keyword_paths=self.mock_config['keyword_paths'],
            sensitivities=self.mock_config['sensitivities']
        )
    
    @patch('src.voice_module.hotword_detector.pyaudio.PyAudio')
    def test_start_detection(self, mock_pyaudio):
        # Mock stream
        mock_stream = MagicMock()
        mock_pyaudio.return_value.open.return_value = mock_stream
        
        # Mock porcupine process method to detect hotword on second frame
        self.detector.porcupine.process = MagicMock(side_effect=[-1, 0, -1])
        
        # Mock audio data
        mock_data = struct.pack('h', 0) * self.detector.frame_length
        mock_stream.read.return_value = mock_data
        
        # Start detection in non-blocking mode to avoid infinite loop
        self.detector.start_detection(blocking=False, max_frames=3)
        
        # Verify stream was started
        mock_pyaudio.return_value.open.assert_called_once()
        # Process should have been called 3 times
        self.assertEqual(self.detector.porcupine.process.call_count, 3)

class TestVoiceAuthenticator(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            'sample_rate': 16000,
            'embedding_dim': 64,
            'threshold': 0.7,
            'model_path': 'test_model.h5'
        }
        self.authenticator = VoiceAuthenticator(config=self.mock_config)
    
    @patch('src.voice_module.voice_authentication.np.load')
    def test_load_user_embeddings(self, mock_load):
        # Mock user embeddings
        mock_embeddings = {
            'user1': np.random.random(self.mock_config['embedding_dim']),
            'user2': np.random.random(self.mock_config['embedding_dim'])
        }
        mock_load.return_value = mock_embeddings
        
        self.authenticator.load_user_embeddings('test_embeddings.npy')
        
        mock_load.assert_called_once_with('test_embeddings.npy', allow_pickle=True)
        self.assertEqual(self.authenticator.user_embeddings, mock_embeddings)
    
    @patch('src.voice_module.voice_authentication.VoiceAuthenticator._compute_embedding')
    def test_authenticate_user(self, mock_compute):
        # Create mock embeddings
        user_embedding = np.array([0.1, 0.2, 0.3, 0.4])
        test_embedding = np.array([0.11, 0.19, 0.31, 0.4])
        
        # Set up authenticator with mock user embeddings
        self.authenticator.user_embeddings = {'test_user': user_embedding}
        
        # Mock compute embedding to return test embedding
        mock_compute.return_value = test_embedding
        
        # Test successful authentication
        user, score = self.authenticator.authenticate_user(b'test_audio')
        
        self.assertEqual(user, 'test_user')
        self.assertGreater(score, self.mock_config['threshold'])
    
    @patch('src.voice_module.voice_authentication.VoiceAuthenticator._compute_embedding')
    def test_authentication_failure(self, mock_compute):
        # Create mock embeddings
        user_embedding = np.array([0.1, 0.2, 0.3, 0.4])
        # Very different embedding
        test_embedding = np.array([0.9, 0.8, 0.7, 0.6])
        
        # Set up authenticator with mock user embeddings
        self.authenticator.user_embeddings = {'test_user': user_embedding}
        
        # Mock compute embedding to return test embedding
        mock_compute.return_value = test_embedding
        
        # Test authentication failure
        user, score = self.authenticator.authenticate_user(b'test_audio')
        
        self.assertIsNone(user)
        self.assertLess(score, self.mock_config['threshold'])

if __name__ == '__main__':
    unittest.main()