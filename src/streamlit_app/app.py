"""
Main Streamlit application for the Gesture & Voice Controlled AI Assistant.
This serves as the entry point for the web-based UI.
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add the parent directory to path to enable relative imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from database.user_store import get_user_store
from auth_module.auth_manager import verify_session
from streamlit_app.components.auth_forms import login_form, create_account_form
from utils.system.token_manager import get_token_from_session, store_token_in_session

# Set page configuration
st.set_page_config(
    page_title="Voice & Gesture AI Assistant",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False


def check_authentication():
    """Verify if the user is authenticated via session token"""
    token = get_token_from_session()
    if token:
        user_data = verify_session(token)
        if user_data:
            st.session_state.authenticated = True
            st.session_state.user_id = user_data['id']
            st.session_state.username = user_data['username']
            
            # Check if user has admin role
            if 'admin' in user_data.get('roles', []):
                st.session_state.is_admin = True
            
            return True
    
    # If we got here, authentication failed or no token was found
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.is_admin = False
    return False


def render_sidebar():
    """Render the sidebar with navigation options"""
    with st.sidebar:
        st.title("AI Assistant")
        
        if st.session_state.authenticated:
            st.write(f"Welcome, {st.session_state.username}!")
            
            # Navigation
            st.subheader("Navigation")
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.current_page = "dashboard"
                st.rerun()
                
            if st.button("🎤 Voice Commands", use_container_width=True):
                st.session_state.current_page = "voice"
                st.rerun()
                
            if st.button("👋 Gesture Controls", use_container_width=True):
                st.session_state.current_page = "gesture"
                st.rerun()
                
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.current_page = "settings"
                st.rerun()
            
            # Admin-only options
            if st.session_state.is_admin:
                st.subheader("Administration")
                if st.button("👥 User Management", use_container_width=True):
                    st.session_state.current_page = "user_management"
                    st.rerun()
                    
                if st.button("📊 System Logs", use_container_width=True):
                    st.session_state.current_page = "logs"
                    st.rerun()
            
            # Logout button at the bottom
            st.sidebar.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                # Clear session
                from auth_module.session_manager import end_session
                token = get_token_from_session()
                if token:
                    end_session(token)
                
                # Reset session state
                st.session_state.authenticated = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.is_admin = False
                st.rerun()
        else:
            st.info("Please log in to access the application.")


def main():
    """Main application entry point"""
    initialize_session_state()
    
    # Check if user is authenticated
    authenticated = check_authentication()
    
    # Display sidebar
    render_sidebar()
    
    # Main content area
    if not authenticated:
        # Login/registration page
        st.title("Welcome to the Voice & Gesture AI Assistant")
        
        tab1, tab2 = st.tabs(["Login", "Create Account"])
        
        with tab1:
            login_successful = login_form()
            if login_successful:
                st.rerun()
        
        with tab2:
            account_created = create_account_form()
            if account_created:
                st.success("Account created successfully! You can now log in.")
    else:
        # Render the appropriate page based on session state
        if st.session_state.current_page == "dashboard":
            from streamlit_app.pages.dashboard import render_dashboard
            render_dashboard()
        
        elif st.session_state.current_page == "voice":
            from streamlit_app.pages.voice_commands import render_voice_page
            render_voice_page()
        
        elif st.session_state.current_page == "gesture":
            from streamlit_app.pages.gesture_controls import render_gesture_page
            render_gesture_page()
        
        elif st.session_state.current_page == "settings":
            from streamlit_app.pages.settings import render_settings_page
            render_settings_page()
        
        elif st.session_state.current_page == "user_management" and st.session_state.is_admin:
            from streamlit_app.pages.user_management import render_user_management
            render_user_management()
        
        elif st.session_state.current_page == "logs" and st.session_state.is_admin:
            from streamlit_app.pages.logs import render_logs_page
            render_logs_page()
        
        else:
            # Default to dashboard
            from streamlit_app.pages.dashboard import render_dashboard
            render_dashboard()


if __name__ == "__main__":
    main()