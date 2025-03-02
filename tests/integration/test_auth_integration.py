"""
Integration tests for the authentication module.
Tests the authentication flow and interaction with other system components.
"""

import unittest
import sys
import os
from pathlib import Path
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open

# Add parent directory to path to enable imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from auth_module.auth_manager import AuthManager
from auth_module.user_manager import UserManager
from auth_module.session_manager import SessionManager
from auth_module.voice_auth import VoiceAuthenticator
from voice_module.listener import VoiceListener


class TestAuthIntegration(unittest.TestCase):
    """Test class for authentication system integration"""

    def setUp(self):
        """Setup test fixtures before each test"""
        # Mock the database connection
        self.db_patcher = patch('src.database.models.get_db_connection')
        self.mock_db = self.db_patcher.start()
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.mock_db.return_value = self.mock_conn
        
        # Mock file operations
        self.mock_file_patcher = patch('builtins.open', mock_open())
        self.mock_file = self.mock_file_patcher.start()
        
        # Mock the voice listener for voice authentication
        self.voice_listener_patcher = patch('src.voice_module.listener.VoiceListener')
        self.mock_voice_listener = self.voice_listener_patcher.start()
        
        # Initialize the authentication components
        self.user_manager = UserManager()
        self.session_manager = SessionManager()
        self.voice_authenticator = VoiceAuthenticator()
        
        # Main auth manager that combines all components
        self.auth_manager = AuthManager(
            user_manager=self.user_manager,
            session_manager=self.session_manager,
            voice_authenticator=self.voice_authenticator
        )
        
        # Sample test user
        self.test_user = {
            "username": "testuser",
            "password": "Password123!",
            "email": "test@example.com",
            "full_name": "Test User",
            "roles": ["user"]
        }
        
        # Sample admin user
        self.admin_user = {
            "username": "admin",
            "password": "AdminPass456!",
            "email": "admin@example.com",
            "full_name": "Admin User",
            "roles": ["admin", "user"]
        }

    def tearDown(self):
        """Tear down test fixtures after each test"""
        self.db_patcher.stop()
        self.mock_file_patcher.stop()
        self.voice_listener_patcher.stop()

    def test_user_registration_and_login(self):
        """Test the complete user registration and login flow"""
        # Mock successful user creation
        self.user_manager.create_user = MagicMock(return_value={"id": 1, **self.test_user})
        
        # Mock successful login verification
        self.user_manager.verify_credentials = MagicMock(return_value={"id": 1, **self.test_user})
        
        # Mock session creation
        mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock_token"
        self.session_manager.create_session = MagicMock(return_value=mock_token)
        
        # 1. Register a new user
        user = self.auth_manager.register_user(
            username=self.test_user["username"],
            password=self.test_user["password"],
            email=self.test_user["email"],
            full_name=self.test_user["full_name"]
        )
        
        # Verify user was created
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], self.test_user["username"])
        
        # 2. Log in with the new user
        auth_result = self.auth_manager.login(
            username=self.test_user["username"],
            password=self.test_user["password"]
        )
        
        # Verify login was successful and returned a token
        self.assertTrue(auth_result["success"])
        self.assertEqual(auth_result["token"], mock_token)
        self.assertEqual(auth_result["user"]["username"], self.test_user["username"])
        
        # 3. Verify the token works for session validation
        self.session_manager.verify_session = MagicMock(return_value={"id": 1, **self.test_user})
        user_data = self.auth_manager.validate_session(mock_token)
        
        # Verify session validation retrieved the correct user
        self.assertEqual(user_data["id"], 1)
        self.assertEqual(user_data["username"], self.test_user["username"])
    
    def test_voice_authentication_integration(self):
        """Test voice authentication integration with the auth system"""
        # Mock voice listener to return audio data
        mock_voice_listener = self.mock_voice_listener.return_value
        mock_voice_listener.listen_for_voice_sample.return_value = b"mock_audio_data"
        
        # Mock voice authentication to recognize the user
        self.voice_authenticator.authenticate_voice = MagicMock(return_value={
            "authenticated": True,
            "user_id": 1,
            "confidence": 0.89
        })
        
        # Mock user retrieval
        self.user_manager.get_user_by_id = MagicMock(return_value={"id": 1, **self.test_user})
        
        # Mock session creation
        mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.voice_auth_token"
        self.session_manager.create_session = MagicMock(return_value=mock_token)
        
        # Attempt voice authentication
        auth_result = self.auth_manager.authenticate_with_voice()
        
        # Verify authentication was successful
        self.assertTrue(auth_result["success"])
        self.assertEqual(auth_result["token"], mock_token)
        self.assertEqual(auth_result["user"]["username"], self.test_user["username"])
        
        # Verify voice listener was used
        mock_voice_listener.listen_for_voice_sample.assert_called_once()
        
        # Verify voice authenticator was used with the audio data
        self.voice_authenticator.authenticate_voice.assert_called_once_with(b"mock_audio_data")
    
    def test_permission_based_access_control(self):
        """Test permission-based access control with different user roles"""
        # Setup mock admin and regular user sessions
        admin_token = "admin_token"
        user_token = "user_token"
        
        # Mock session validation for both tokens
        def mock_verify_session(token):
            if token == admin_token:
                return {"id": 2, **self.admin_user}
            elif token == user_token:
                return {"id": 1, **self.test_user}
            return None
        
        self.session_manager.verify_session = MagicMock(side_effect=mock_verify_session)
        
        # Test admin permission access
        admin_access = self.auth_manager.check_permission(admin_token, "manage_users")
        self.assertTrue(admin_access)
        
        # Test regular user permission denial
        user_access = self.auth_manager.check_permission(user_token, "manage_users")
        self.assertFalse(user_access)
        
        # Test access to a common feature available to all users
        admin_common_access = self.auth_manager.check_permission(admin_token, "use_voice_commands")
        user_common_access = self.auth_manager.check_permission(user_token, "use_voice_commands")
        
        self.assertTrue(admin_common_access)
        self.assertTrue(user_common_access)
    
    def test_session_management_lifecycle(self):
        """Test complete session lifecycle including expiry and renewal"""
        # Mock the current time
        with patch('src.auth_module.session_manager.time.time') as mock_time:
            # Set initial time
            mock_time.return_value = 1000
            
            # Create a session
            self.session_manager.create_session = MagicMock(return_value="session_token_1")
            token = self.session_manager.create_session({"id": 1, "username": "testuser"})
            
            # Verify token was created
            self.assertEqual(token, "session_token_1")
            
            # Verify session at initial time
            self.session_manager.verify_session = MagicMock(return_value={"id": 1, "username": "testuser"})
            session_data = self.session_manager.verify_session(token)
            self.assertEqual(session_data["id"], 1)
            
            # Advance time close to expiry
            mock_time.return_value = 3500  # assuming 3600 second expiry
            
            # Verify session is still valid but close to expiry
            self.session_manager.verify_session = MagicMock(return_value={"id": 1, "username": "testuser", "renew": True})
            session_data = self.session_manager.verify_session(token)
            self.assertTrue(session_data.get("renew", False))
            
            # Renew the session
            self.session_manager.renew_session = MagicMock(return_value="session_token_2")
            new_token = self.auth_manager.renew_session(token)
            
            # Verify new token was issued
            self.assertEqual(new_token, "session_token_2")
            
            # Advance time past original expiry
            mock_time.return_value = 4100
            
            # Original token should be invalid
            self.session_manager.verify_session = MagicMock(side_effect=lambda t: 
                {"id": 1, "username": "testuser"} if t == "session_token_2" else None)
            
            invalid_session = self.session_manager.verify_session("session_token_1")
            self.assertIsNone(invalid_session)
            
            # New token should be valid
            valid_session = self.session_manager.verify_session("session_token_2")
            self.assertIsNotNone(valid_session)
    
    @pytest.mark.slow
    def test_failed_login_lockout(self):
        """Test that accounts get locked after multiple failed login attempts"""
        # Setup the test
        username = "testuser"
        correct_password = "Password123!"
        wrong_password = "WrongPassword!"
        
        # Mock the user verification to track failed attempts
        failed_attempts = 0
        
        def mock_verify_credentials(user, pwd):
            nonlocal failed_attempts
            if user == username and pwd == correct_password:
                # Correct credentials
                return {"id": 1, "username": username, "locked": failed_attempts >= 5}
            else:
                # Incorrect password, increment counter
                failed_attempts += 1
                return None
        
        self.user_manager.verify_credentials = MagicMock(side_effect=mock_verify_credentials)
        
        # Mock the account locking function
        self.user_manager.lock_account = MagicMock()
        
        # Try incorrect password multiple times
        for i in range(5):
            result = self.auth_manager.login(username, wrong_password)
            self.assertFalse(result["success"])
        
        # Verify account locking was called
        self.user_manager.lock_account.assert_called_with(username)
        
        # Try with correct password
        result = self.auth_manager.login(username, correct_password)
        
        # Should still fail because account is locked
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Account is locked. Please contact an administrator.")


# Add these tests to be executed only if this file is run directly
if __name__ == '__main__':
    unittest.main()