import unittest
import os
import sys
import tempfile
from unittest import mock
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

# Add src directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.models import Base, User, GestureCommand, VoiceCommand, AccessLog
from database.user_store import UserStore
from database.intent_store import IntentStore
from auth_module.permission_manager import PermissionLevel


class TestDatabase(unittest.TestCase):
    """Test database models and operations."""

    def setUp(self):
        """Set up test database."""
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.engine = sa.create_engine(f"sqlite:///{self.db_path}")
        
        # Create all tables in the database
        Base.metadata.create_all(self.engine)
        
        # Create a session factory
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
        # Create the stores
        self.user_store = UserStore(self.engine)
        self.intent_store = IntentStore(self.engine)
        
        # Populate with some test data
        self._populate_test_data()

    def tearDown(self):
        """Clean up test database."""
        self.session.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def _populate_test_data(self):
        """Populate database with test data."""
        # Create test users
        test_user = User(
            username="testuser",
            password_hash="$2b$12$1234567890123456789012",  # Mock hash
            email="test@example.com",
            permission_level=PermissionLevel.USER.value,
            voice_profile_id="user123"
        )
        admin_user = User(
            username="admin",
            password_hash="$2b$12$0987654321098765432109",  # Mock hash
            email="admin@example.com",
            permission_level=PermissionLevel.ADMIN.value,
            voice_profile_id="admin456"
        )
        
        # Create test gesture commands
        test_gesture_cmd = GestureCommand(
            name="volume_up",
            gesture_type="palm_up",
            action="volume_control.increase_volume",
            parameters='{"amount": 10}',
            user_id=None  # Global command
        )
        user_gesture_cmd = GestureCommand(
            name="browser_open",
            gesture_type="peace_sign",
            action="browser_control.open_browser",
            parameters='{"url": "https://example.com"}',
            user_id=1  # Associated with testuser
        )
        
        # Create test voice commands
        test_voice_cmd = VoiceCommand(
            trigger_phrase="increase volume",
            intent="volume_up",
            action="volume_control.increase_volume",
            parameters='{"amount": 10}',
            user_id=None  # Global command
        )
        user_voice_cmd = VoiceCommand(
            trigger_phrase="open my homepage",
            intent="open_homepage",
            action="browser_control.open_browser",
            parameters='{"url": "https://example.com"}',
            user_id=1  # Associated with testuser
        )
        
        # Add to session and commit
        self.session.add_all([
            test_user, 
            admin_user, 
            test_gesture_cmd, 
            user_gesture_cmd, 
            test_voice_cmd, 
            user_voice_cmd
        ])
        self.session.commit()
    
    def test_user_model(self):
        """Test User model operations."""
        # Test user retrieval
        user = self.session.query(User).filter_by(username="testuser").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.permission_level, PermissionLevel.USER.value)
        
        # Test user creation
        new_user = User(
            username="newuser",
            password_hash="$2b$12$abcdefghijklmnopqrstuv",
            email="new@example.com",
            permission_level=PermissionLevel.USER.value
        )
        self.session.add(new_user)
        self.session.commit()
        
        # Verify user was added
        retrieved_user = self.session.query(User).filter_by(username="newuser").first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.email, "new@example.com")
        
    def test_user_store(self):
        """Test UserStore operations."""
        # Test get user by username
        user = self.user_store.get_user_by_username("testuser")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")
        
        # Test get user by voice profile
        user = self.user_store.get_user_by_voice_profile("user123")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        
        # Test user creation
        new_user_id = self.user_store.create_user(
            username="storeuser",
            password_hash="$2b$12$wxyzabcdefghijklmnopqr",
            email="store@example.com",
            permission_level=PermissionLevel.USER.value
        )
        self.assertIsNotNone(new_user_id)
        
        # Test user update
        updated = self.user_store.update_user(
            user_id=new_user_id,
            email="updated@example.com",
            permission_level=PermissionLevel.POWER_USER.value
        )
        self.assertTrue(updated)
        
        # Verify update
        updated_user = self.user_store.get_user_by_id(new_user_id)
        self.assertEqual(updated_user.email, "updated@example.com")
        self.assertEqual(updated_user.permission_level, PermissionLevel.POWER_USER.value)
        
        # Test delete user
        deleted = self.user_store.delete_user(new_user_id)
        self.assertTrue(deleted)
        
        # Verify deletion
        deleted_user = self.user_store.get_user_by_id(new_user_id)
        self.assertIsNone(deleted_user)
    
    def test_gesture_command_model(self):
        """Test GestureCommand model operations."""
        # Test global gesture command retrieval
        cmd = self.session.query(GestureCommand).filter_by(name="volume_up").first()
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.gesture_type, "palm_up")
        self.assertEqual(cmd.action, "volume_control.increase_volume")
        
        # Test user-specific gesture command
        user_cmd = self.session.query(GestureCommand).filter_by(name="browser_open").first()
        self.assertIsNotNone(user_cmd)
        self.assertEqual(user_cmd.user_id, 1)
        
        # Test command creation
        new_cmd = GestureCommand(
            name="scroll_down",
            gesture_type="fist_down",
            action="mouse_control.scroll",
            parameters='{"direction": "down", "amount": 5}',
            user_id=None  # Global command
        )
        self.session.add(new_cmd)
        self.session.commit()
        
        # Verify command was added
        retrieved_cmd = self.session.query(GestureCommand).filter_by(name="scroll_down").first()
        self.assertIsNotNone(retrieved_cmd)
        self.assertEqual(retrieved_cmd.gesture_type, "fist_down")

    def test_voice_command_model(self):
        """Test VoiceCommand model operations."""
        # Test global voice command retrieval
        cmd = self.session.query(VoiceCommand).filter_by(trigger_phrase="increase volume").first()
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.intent, "volume_up")
        self.assertEqual(cmd.action, "volume_control.increase_volume")
        
        # Test user-specific voice command
        user_cmd = self.session.query(VoiceCommand).filter_by(trigger_phrase="open my homepage").first()
        self.assertIsNotNone(user_cmd)
        self.assertEqual(user_cmd.user_id, 1)
        
        # Test command creation
        new_cmd = VoiceCommand(
            trigger_phrase="scroll down",
            intent="scroll_down",
            action="mouse_control.scroll",
            parameters='{"direction": "down", "amount": 5}',
            user_id=None  # Global command
        )
        self.session.add(new_cmd)
        self.session.commit()
        
        # Verify command was added
        retrieved_cmd = self.session.query(VoiceCommand).filter_by(trigger_phrase="scroll down").first()
        self.assertIsNotNone(retrieved_cmd)
        self.assertEqual(retrieved_cmd.intent, "scroll_down")
    
    def test_intent_store(self):
        """Test IntentStore operations."""
        # Test retrieving gesture commands for user
        user = self.session.query(User).filter_by(username="testuser").first()
        gesture_cmds = self.intent_store.get_gesture_commands_for_user(user.id)
        
        # Should include both global and user-specific commands
        self.assertEqual(len(gesture_cmds), 2)
        
        # Test retrieving voice commands for user
        voice_cmds = self.intent_store.get_voice_commands_for_user(user.id)
        self.assertEqual(len(voice_cmds), 2)
        
        # Test adding a new voice command
        new_cmd_id = self.intent_store.add_voice_command(
            trigger_phrase="take screenshot",
            intent="screenshot",
            action="system_control.take_screenshot",
            parameters='{}',
            user_id=user.id
        )
        self.assertIsNotNone(new_cmd_id)
        
        # Verify command was added
        voice_cmds = self.intent_store.get_voice_commands_for_user(user.id)
        self.assertEqual(len(voice_cmds), 3)
        
        # Test adding a new gesture command
        new_cmd_id = self.intent_store.add_gesture_command(
            name="take_screenshot",
            gesture_type="pinch",
            action="system_control.take_screenshot",
            parameters='{}',
            user_id=user.id
        )
        self.assertIsNotNone(new_cmd_id)
        
        # Verify command was added
        gesture_cmds = self.intent_store.get_gesture_commands_for_user(user.id)
        self.assertEqual(len(gesture_cmds), 3)
        
        # Test deleting a voice command
        deleted = self.intent_store.delete_voice_command(new_cmd_id)
        self.assertTrue(deleted)
        
        # Verify deletion
        voice_cmds = self.intent_store.get_voice_commands_for_user(user.id)
        self.assertEqual(len(voice_cmds), 2)

    def test_access_log(self):
        """Test AccessLog model operations."""
        # Create a new log entry
        user = self.session.query(User).filter_by(username="testuser").first()
        log_entry = AccessLog(
            user_id=user.id,
            command_type="voice",
            command_id=1,
            timestamp=sa.func.now(),
            success=True,
            details='{"execution_time": 0.5}'
        )
        self.session.add(log_entry)
        self.session.commit()
        
        # Verify log entry was added
        logs = self.session.query(AccessLog).filter_by(user_id=user.id).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].command_type, "voice")
        self.assertTrue(logs[0].success)
        
        # Add a failed log entry
        failed_log = AccessLog(
            user_id=user.id,
            command_type="gesture",
            command_id=1,
            timestamp=sa.func.now(),
            success=False,
            details='{"error": "Permission denied"}'
        )
        self.session.add(failed_log)
        self.session.commit()
        
        # Verify both logs exist
        logs = self.session.query(AccessLog).filter_by(user_id=user.id).all()
        self.assertEqual(len(logs), 2)
        
        # Test filtering by success
        success_logs = self.session.query(AccessLog).filter_by(user_id=user.id, success=True).all()
        self.assertEqual(len(success_logs), 1)
        
        failed_logs = self.session.query(AccessLog).filter_by(user_id=user.id, success=False).all()
        self.assertEqual(len(failed_logs), 1)


class TestDatabaseIntegration:
    """Integration tests for database with authentication and command modules."""
    
    @pytest.fixture
    def setup_db(self):
        """Set up test database for pytest fixtures."""
        db_fd, db_path = tempfile.mkstemp()
        engine = sa.create_engine(f"sqlite:///{db_path}")
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Yield session for tests
        yield session
        
        # Teardown
        session.close()
        os.close(db_fd)
        os.unlink(db_path)
    
    @pytest.mark.integration
    def test_user_authentication_flow(self, setup_db):
        """Test integration with auth_module."""
        session = setup_db
        
        # Mock auth_manager module
        with mock.patch('src.auth_module.auth_manager.AuthManager') as mock_auth:
            # Configure mock
            mock_auth.return_value.authenticate_user.return_value = True
            mock_auth.return_value.create_session.return_value = "mock_session_token"
            
            # Create a test user
            test_user = User(
                username="testuser",
                password_hash="$2b$12$1234567890123456789012",  # Mock hash
                email="test@example.com",
                permission_level=PermissionLevel.USER.value
            )
            session.add(test_user)
            session.commit()
            
            # Create UserStore with real database
            user_store = UserStore(session.get_bind())
            
            # Get the user
            user = user_store.get_user_by_username("testuser")
            assert user is not None
            
            # Test with mock auth manager
            auth_manager = mock_auth.return_value
            assert auth_manager.authenticate_user("testuser", "password") is True
            
            # Test session creation
            session_token = auth_manager.create_session(user.id)
            assert session_token == "mock_session_token"
    
    @pytest.mark.integration
    def test_voice_command_execution_flow(self, setup_db):
        """Test integration with voice_module."""
        session = setup_db
        
        # Create test user
        test_user = User(
            username="voiceuser",
            password_hash="$2b$12$1234567890123456789012",  # Mock hash
            email="voice@example.com",
            permission_level=PermissionLevel.USER.value
        )
        session.add(test_user)
        
        # Create test voice command
        test_cmd = VoiceCommand(
            trigger_phrase="open browser",
            intent="open_browser",
            action="browser_control.open_browser",
            parameters='{"url": "https://example.com"}',
            user_id=None  # Global command
        )
        session.add(test_cmd)
        session.commit()
        
        # Mock voice module components
        with mock.patch('src.voice_module.intent_handler.IntentHandler') as mock_intent:
            # Configure mock
            mock_intent.return_value.process_intent.return_value = True
            
            # Create IntentStore with real database
            intent_store = IntentStore(session.get_bind())
            
            # Get commands for user
            cmds = intent_store.get_voice_commands_for_user(test_user.id)
            assert len(cmds) == 1
            assert cmds[0].trigger_phrase == "open browser"
            
            # Test with mock intent handler
            intent_handler = mock_intent.return_value
            assert intent_handler.process_intent("open_browser", '{"url": "https://example.com"}') is True
            
            # Record the execution in log
            log_entry = AccessLog(
                user_id=test_user.id,
                command_type="voice",
                command_id=test_cmd.id,
                timestamp=sa.func.now(),
                success=True,
                details='{"execution_time": 0.3}'
            )
            session.add(log_entry)
            session.commit()
            
            # Verify log entry
            logs = session.query(AccessLog).filter_by(user_id=test_user.id).all()
            assert len(logs) == 1
            assert logs[0].command_type == "voice"
            assert logs[0].success is True
    
    @pytest.mark.integration
    def test_gesture_command_execution_flow(self, setup_db):
        """Test integration with gesture_module."""
        session = setup_db
        
        # Create test user
        test_user = User(
            username="gestureuser",
            password_hash="$2b$12$1234567890123456789012",  # Mock hash
            email="gesture@example.com",
            permission_level=PermissionLevel.USER.value
        )
        session.add(test_user)
        
        # Create test gesture command
        test_cmd = GestureCommand(
            name="volume_up",
            gesture_type="palm_up",
            action="volume_control.increase_volume",
            parameters='{"amount": 10}',
            user_id=None  # Global command
        )
        session.add(test_cmd)
        session.commit()
        
        # Mock gesture module components
        with mock.patch('src.gesture_module.processor.GestureProcessor') as mock_processor:
            # Configure mock
            mock_processor.return_value.process_gesture.return_value = True
            
            # Create IntentStore with real database
            intent_store = IntentStore(session.get_bind())
            
            # Get commands for user
            cmds = intent_store.get_gesture_commands_for_user(test_user.id)
            assert len(cmds) == 1
            assert cmds[0].gesture_type == "palm_up"
            
            # Test with mock gesture processor
            processor = mock_processor.return_value
            assert processor.process_gesture("palm_up", test_user.id) is True
            
            # Record the execution in log
            log_entry = AccessLog(
                user_id=test_user.id,
                command_type="gesture",
                command_id=test_cmd.id,
                timestamp=sa.func.now(),
                success=True,
                details='{"execution_time": 0.1}'
            )
            session.add(log_entry)
            session.commit()
            
            # Verify log entry
            logs = session.query(AccessLog).filter_by(user_id=test_user.id).all()
            assert len(logs) == 1
            assert logs[0].command_type == "gesture"
            assert logs[0].success is True


if __name__ == '__main__':
    unittest.main()