import unittest
import os
import sys
from unittest.mock import MagicMock, patch
import jwt
import datetime
import bcrypt

# Add src to path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from auth_module.auth_manager import AuthManager
from auth_module.user_manager import UserManager
from auth_module.permission_manager import PermissionManager
from auth_module.session_manager import SessionManager
from auth_module.voice_auth import VoiceAuthenticator
from auth_module.password_auth import PasswordAuthenticator

class TestAuthManager(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_user_manager = MagicMock()
        self.mock_session_manager = MagicMock()
        self.mock_password_auth = MagicMock()
        self.mock_voice_auth = MagicMock()
        
        # Create auth manager with mocked dependencies
        self.auth_manager = AuthManager(
            user_manager=self.mock_user_manager,
            session_manager=self.mock_session_manager,
            password_authenticator=self.mock_password_auth,
            voice_authenticator=self.mock_voice_auth
        )
    
    def test_authenticate_with_password(self):
        # Set up test data
        username = 'test_user'
        password = 'test_password'
        user_data = {'username': username, 'role': 'user'}
        
        # Mock password authenticator to return success
        self.mock_password_auth.authenticate.return_value = True
        
        # Mock user manager to return user data
        self.mock_user_manager.get_user.return_value = user_data
        
        # Mock session creation
        self.mock_session_manager.create_session.return_value = 'test_session_token'
        
        # Test authentication
        result = self.auth_manager.authenticate_with_password(username, password)
        
        # Verify results
        self.assertTrue(result['success'])
        self.assertEqual(result['user'], user_data)
        self.assertEqual(result['token'], 'test_session_token')
        
        # Verify method calls
        self.mock_password_auth.authenticate.assert_called_once_with(username, password)
        self.mock_user_manager.get_user.assert_called_once_with(username)
        self.mock_session_manager.create_session.assert_called_once_with(username, user_data)
    
    def test_authenticate_with_password_failure(self):
        # Set up test data
        username = 'test_user'
        password = 'wrong_password'
        
        # Mock password authenticator to return failure
        self.mock_password_auth.authenticate.return_value = False
        
        # Test authentication
        result = self.auth_manager.authenticate_with_password(username, password)
        
        # Verify results
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
        # Verify method calls
        self.mock_password_auth.authenticate.assert_called_once_with(username, password)
        self.mock_user_manager.get_user.assert_not_called()
        self.mock_session_manager.create_session.assert_not_called()
    
    def test_authenticate_with_voice(self):
        # Set up test data
        voice_data = b'test_voice_data'
        user_data = {'username': 'test_user', 'role': 'user'}
        
        # Mock voice authenticator to return a user
        self.mock_voice_auth.authenticate.return_value = ('test_user', 0.85)
        
        # Mock user manager to return user data
        self.mock_user_manager.get_user.return_value = user_data
        
        # Mock session creation
        self.mock_session_manager.create_session.return_value = 'test_session_token'
        
        # Test authentication
        result = self.auth_manager.authenticate_with_voice(voice_data)
        
        # Verify results
        self.assertTrue(result['success'])
        self.assertEqual(result['user'], user_data)
        self.assertEqual(result['token'], 'test_session_token')
        self.assertAlmostEqual(result['confidence'], 0.85)
        
        # Verify method calls
        self.mock_voice_auth.authenticate.assert_called_once_with(voice_data)
        self.mock_user_manager.get_user.assert_called_once_with('test_user')
        self.mock_session_manager.create_session.assert_called_once_with('test_user', user_data)
    
    def test_authenticate_with_voice_failure(self):
        # Set up test data
        voice_data = b'unknown_voice_data'
        
        # Mock voice authenticator to return no user
        self.mock_voice_auth.authenticate.return_value = (None, 0.3)
        
        # Test authentication
        result = self.auth_manager.authenticate_with_voice(voice_data)
        
        # Verify results
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
        # Verify method calls
        self.mock_voice_auth.authenticate.assert_called_once_with(voice_data)
        self.mock_user_manager.get_user.assert_not_called()
        self.mock_session_manager.create_session.assert_not_called()
    
    def test_verify_session(self):
        # Set up test data
        token = 'valid_token'
        user_data = {'username': 'test_user', 'role': 'user'}
        
        # Mock session verification
        self.mock_session_manager.verify_session.return_value = ('test_user', True)
        
        # Mock user manager to return user data
        self.mock_user_manager.get_user.return_value = user_data
        
        # Test verification
        result = self.auth_manager.verify_session(token)
        
        # Verify results
        self.assertTrue(result['valid'])
        self.assertEqual(result['user'], user_data)
        
        # Verify method calls
        self.mock_session_manager.verify_session.assert_called_once_with(token)
        self.mock_user_manager.get_user.assert_called_once_with('test_user')
    
    def test_verify_session_invalid(self):
        # Set up test data
        token = 'invalid_token'
        
        # Mock session verification
        self.mock_session_manager.verify_session.return_value = (None, False)
        
        # Test verification
        result = self.auth_manager.verify_session(token)
        
        # Verify results
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
        
        # Verify method calls
        self.mock_session_manager.verify_session.assert_called_once_with(token)
        self.mock_user_manager.get_user.assert_not_called()

class TestUserManager(unittest.TestCase):
    def setUp(self):
        # Mock database connection
        self.mock_db = MagicMock()
        self.user_manager = UserManager(db=self.mock_db)
    
    def test_create_user(self):
        # Set up test data
        username = 'new_user'
        password = 'secure_password'
        role = 'user'
        hashed_password = b'hashed_password'
        
        # Mock database queries
        self.mock_db.execute_query.side_effect = [
            None,  # No existing user
            {'id': 1}  # User created
        ]
        
        # Mock bcrypt for password hashing
        with patch('src.auth_module.user_manager.bcrypt.hashpw') as mock_hash:
            mock_hash.return_value = hashed_password
            
            # Test user creation
            result = self.user_manager.create_user(username, password, role)
            
            # Verify results
            self.assertTrue(result['success'])
            self.assertEqual(result['username'], username)
            
            # Verify method calls
            mock_hash.assert_called_once()
            self.assertEqual(self.mock_db.execute_query.call_count, 2)
    
    def test_create_duplicate_user(self):
        # Set up test data
        username = 'existing_user'
        password = 'secure_password'
        role = 'user'
        
        # Mock database to return existing user
        self.mock_db.execute_query.return_value = {'username': username}
        
        # Test user creation
        result = self.user_manager.create_user(username, password, role)
        
        # Verify results
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
        # Verify method calls
        self.mock_db.execute_query.assert_called_once()
    
    def test_get_user(self):
        # Set up test data
        username = 'test_user'
        user_data = {
            'username': username,
            'role': 'user',
            'email': 'test@example.com'
        }
        
        # Mock database to return user data
        self.mock_db.execute_query.return_value = user_data
        
        # Test get user
        result = self.user_manager.get_user(username)
        
        # Verify results
        self.assertEqual(result, user_data)
        
        # Verify method calls
        self.mock_db.execute_query.assert_called_once()
    
    def test_update_user(self):
        # Set up test data
        username = 'test_user'
        updates = {
            'email': 'updated@example.com',
            'role': 'admin'
        }
        
        # Mock database update
        self.mock_db.execute_query.return_value = {'affected_rows': 1}
        
        # Test update user
        result = self.user_manager.update_user(username, updates)
        
        # Verify results
        self.assertTrue(result['success'])
        
        # Verify method calls
        self.mock_db.execute_query.assert_called_once()
    
    def test_delete_user(self):
        # Set up test data
        username = 'test_user'
        
        # Mock database deletion
        self.mock_db.execute_query.return_value = {'affected_rows': 1}
        
        # Test delete user
        result = self.user_manager.delete_user(username)
        
        # Verify results
        self.assertTrue(result['success'])
        
        # Verify method calls
        self.mock_db.execute_query.assert_called_once()

class TestPermissionManager(unittest.TestCase):
    def setUp(self):
        # Define role permissions
        self.role_permissions = {
            'admin': ['read', 'write', 'delete', 'manage_users'],
            'user': ['read', 'write'],
            'guest': ['read']
        }
        self.permission_manager = PermissionManager(self.role_permissions)
    
    def test_check_permission_allowed(self):
        # Test admin permissions
        self.assertTrue(self.permission_manager.check_permission('admin', 'read'))
        self.assertTrue(self.permission_manager.check_permission('admin', 'write'))
        self.assertTrue(self.permission_manager.check_permission('admin', 'delete'))
        self.assertTrue(self.permission_manager.check_permission('admin', 'manage_users'))
        
        # Test user permissions
        self.assertTrue(self.permission_manager.check_permission('user', 'read'))
        self.assertTrue(self.permission_manager.check_permission('user', 'write'))
        self.assertFalse(self.permission_manager.check_permission('user', 'delete'))
        
        # Test guest permissions
        self.assertTrue(self.permission_manager.check_permission('guest', 'read'))
        self.assertFalse(self.permission_manager.check_permission('guest', 'write'))
    
    def test_check_permission_invalid_role(self):
        # Test invalid role
        self.assertFalse(self.permission_manager.check_permission('invalid_role', 'read'))
    
    def test_get_role_permissions(self):
        # Test getting all permissions for a role
        admin_permissions = self.permission_manager.get_role_permissions('admin')
        self.assertEqual(set(admin_permissions), set(['read', 'write', 'delete', 'manage_users']))
        
        user_permissions = self.permission_manager.get_role_permissions('user')
        self.assertEqual(set(user_permissions), set(['read', 'write']))
    
    def test_get_permissions_invalid_role(self):
        # Test getting permissions for invalid role
        permissions = self.permission_manager.get_role_permissions('invalid_role')
        self.assertEqual(permissions, [])
    
    def test_add_role_permission(self):
        # Test adding a new permission to a role
        self.permission_manager.add_role_permission('user', 'export')
        
        # Verify permission was added
        self.assertTrue(self.permission_manager.check_permission('user', 'export'))
        self.assertIn('export', self.permission_manager.get_role_permissions('user'))
    
    def test_remove_role_permission(self):
        # Test removing a permission from a role
        self.permission_manager.remove_role_permission('user', 'write')
        
        # Verify permission was removed
        self.assertFalse(self.permission_manager.check_permission('user', 'write'))
        self.assertNotIn('write', self.permission_manager.get_role_permissions('user'))

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.secret_key = 'test_secret_key'
        self.session_manager = SessionManager(secret_key=self.secret_key)
    
    @patch('src.auth_module.session_manager.jwt.encode')
    def test_create_session(self, mock_encode):
        # Set up test data
        username = 'test_user'
        user_data = {'username': username, 'role': 'user'}
        token = 'encoded_jwt_token'
        
        # Mock JWT encode
        mock_encode.return_value = token
        
        # Test session creation
        result = self.session_manager.create_session(username, user_data)
        
        # Verify results
        self.assertEqual(result, token)
        
        # Verify JWT encode was called with correct data
        mock_encode.assert_called_once()
        args, kwargs = mock_encode.call_args
        payload = args[0]
        
        self.assertEqual(payload['username'], username)
        self.assertEqual(payload['user_data'], user_data)
        self.assertIn('exp', payload)
        self.assertEqual(kwargs['key'], self.secret_key)
    
    @patch('src.auth_module.session_manager.jwt.decode')
    def test_verify_valid_session(self, mock_decode):
        # Set up test data
        token = 'valid_token'
        username = 'test_user'
        
        # Mock JWT decode to return valid payload
        mock_decode.return_value = {
            'username': username,
            'exp': datetime.datetime.now().timestamp() + 3600  # Not expired
        }
        
        # Test session verification
        user, valid = self.session_manager.verify_session(token)
        
        # Verify results
        self.assertEqual(user, username)
        self.assertTrue(valid)
        
        # Verify JWT decode was called
        mock_decode.assert_called_once_with(token, self.secret_key, algorithms=['HS256'])
    
    @patch('src.auth_module.session_manager.jwt.decode')
    def test_verify_expired_session(self, mock_decode):
        # Set up test data
        token = 'expired_token'
        
        # Mock JWT decode to raise expired signature error
        mock_decode.side_effect = jwt.ExpiredSignatureError
        
        # Test session verification
        user, valid = self.session_manager.verify_session(token)
        
        # Verify results
        self.assertIsNone(user)
        self.assertFalse(valid)
        
        # Verify JWT decode was called
        mock_decode.assert_called_once_with(token, self.secret_key, algorithms=['HS256'])
    
    @patch('src.auth_module.session_manager.jwt.decode')
    def test_verify_invalid_token(self, mock_decode):
        # Set up test data
        token = 'invalid_token'
        
        # Mock JWT decode to raise generic JWT error
        mock_decode.side_effect = jwt.InvalidTokenError
        
        # Test session verification
        user, valid = self.session_manager.verify_session(token)
        
        # Verify results
        self.assertIsNone(user)
        self.assertFalse(valid)
        
        # Verify JWT decode was called
        mock_decode.assert_called_once_with(token, self.secret_key, algorithms=['HS256'])

class TestPasswordAuthenticator(unittest.TestCase):
    def setUp(self):
        # Mock database
        self.mock_db = MagicMock()
        self.password_auth = PasswordAuthenticator(db=self.mock_db)
    
    def test_authenticate_success(self):
        # Set up test data
        username = 'test_user'
        password = 'correct_password'
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Mock database to return user with hashed password
        self.mock_db.execute_query.return_value = {
            'username': username,
            'password': hashed_password
        }
        
        # Test authentication
        result = self.password_auth.authenticate(username, password)
        
        # Verify results
        self.assertTrue(result)
        
        # Verify database was queried
        self.mock_db.execute_query.assert_called_once()
    
    def test_authenticate_wrong_password(self):
        # Set up test data
        username = 'test_user'
        correct_password = 'correct_password'
        wrong_password = 'wrong_password'
        hashed_password = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt())
        
        # Mock database to return user with hashed password
        self.mock_db.execute_query.return_value = {
            'username': username,
            'password': hashed_password
        }
        
        # Test authentication with wrong password
        result = self.password_auth.authenticate(username, wrong_password)
        
        # Verify results
        self.assertFalse(result)
        
        # Verify database was queried
        self.mock_db.execute_query.assert_called_once()
    
    def test_authenticate_user_not_found(self):
        # Set up test data
        username = 'nonexistent_user'
        password = 'any_password'
        
        # Mock database to return no user
        self.mock_db.execute_query.return_value = None
        
        # Test authentication with nonexistent user
        result = self.password_auth.authenticate(username, password)
        
        # Verify results
        self.assertFalse(result)
        
        # Verify database was queried
        self.mock_db.execute_query.assert_called_once()

if __name__ == '__main__':
    unittest.main()