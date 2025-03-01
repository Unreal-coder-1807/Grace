"""
Authentication UI components for the Streamlit application.
"""

import streamlit as st
from typing import Tuple, Optional
import time

# Import authentication-related functionality
from auth_module.auth_manager import authenticate_user, create_user
from auth_module.session_manager import create_session
from utils.system.token_manager import store_token_in_session


def login_form() -> bool:
    """
    Render and process the login form.
    
    Returns:
        bool: True if login was successful, False otherwise
    """
    with st.form("login_form"):
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit_button = st.form_submit_button("Login", use_container_width=True)
        with col2:
            voice_login = st.form_submit_button("Login with Voice", use_container_width=True)
        
    if submit_button and username and password:
        # Display a spinner during authentication
        with st.spinner("Authenticating..."):
            # Authenticate user with username and password
            user_data = authenticate_user(username, password)
            
            if user_data:
                # Create session and store token
                token = create_session(user_data['id'])
                if token:
                    store_token_in_session(token)
                    
                    # Update session state
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_data['id']
                    st.session_state.username = user_data['username']
                    
                    # Check if user has admin role
                    if 'admin' in user_data.get('roles', []):
                        st.session_state.is_admin = True
                    
                    return True
                else:
                    st.error("Failed to create session. Please try again.")
            else:
                st.error("Invalid username or password.")
    
    elif voice_login:
        st.info("Please speak your voice authentication phrase...")
        
        # This would be where voice authentication would happen
        # For demonstration, we'll just show a placeholder
        with st.spinner("Listening..."):
            # Simulate processing time
            time.sleep(2)
            st.error("Voice authentication is not implemented in this demo.")
            
            # In a real implementation:
            # 1. Capture audio
            # 2. Process it through voice_authentication.py
            # 3. Get user_id if successful
            # 4. Create session and update state
    
    return False


def create_account_form() -> bool:
    """
    Render and process the account creation form.
    
    Returns:
        bool: True if account was created successfully, False otherwise
    """
    with st.form("create_account_form"):
        st.subheader("Create a New Account")
        
        username = st.text_input("Username", key="create_username")
        email = st.text_input("Email", key="create_email")
        password = st.text_input("Password", type="password", key="create_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="create_confirm_password")
        
        # Terms of service checkbox
        agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        
        submit_button = st.form_submit_button("Create Account", use_container_width=True)
    
    if submit_button:
        # Validate inputs
        if not username or not email or not password:
            st.error("All fields are required.")
            return False
        
        if password != confirm_password:
            st.error("Passwords do not match.")
            return False
        
        if not agree_terms:
            st.error("You must agree to the Terms of Service and Privacy Policy.")
            return False
        
        # Validate email format
        if "@" not in email or "." not in email:
            st.error("Please enter a valid email address.")
            return False
        
        # Validate password strength
        if len(password) < 8:
            st.error("Password must be at least 8 characters long.")
            return False
        
        # Create the user account
        with st.spinner("Creating account..."):
            # Default role for new users
            roles = ["user"]
            
            user_id = create_user(username, password, email, roles)
            
            if user_id:
                return True
            else:
                st.error("Failed to create account. Username or email may already exist.")
    
    return False


def voice_enrollment_form() -> bool:
    """
    Render and process the voice enrollment form for voice authentication.
    
    Returns:
        bool: True if voice enrollment was successful, False otherwise
    """
    st.subheader("Voice Authentication Enrollment")
    st.write("To enable voice authentication, you'll need to record your voice saying a passphrase.")
    
    # Passphrase selection
    passphrase = st.selectbox(
        "Select a passphrase:",
        [
            "My voice is my passport, verify me",
            "Open the system with my voice",
            "Voice control access verify identity",
            "Biometric authentication activate now"
        ]
    )
    
    st.write("You'll need to repeat this phrase 3 times for the system to learn your voice pattern.")
    
    # Record button
    if st.button("Start Recording"):
        # This would be where voice recording and processing would happen
        # For demonstration, we'll just show a placeholder
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(3):
            status_text.text(f"Please say: '{passphrase}' (Recording {i+1}/3)")
            
            # Simulate recording process
            for percent in range(100):
                time.sleep(0.02)
                progress_bar.progress(percent)
            
            time.sleep(0.5)
            progress_bar.progress(0)
        
        status_text.text("Processing voice patterns...")
        progress_bar.progress(100)
        
        # In a real implementation:
        # 1. Record audio samples
        # 2. Process through voice_auth.py's register_voice_pattern
        # 3. Update user record to enable voice authentication
        
        st.success("Voice enrollment completed! You can now use voice authentication.")
        return True
    
    return False