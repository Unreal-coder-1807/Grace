import streamlit as st
import sys
import os
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_module.auth_manager import AuthManager
from auth_module.session_manager import SessionManager
from auth_module.user_manager import UserManager
from components.auth_forms import login_form, reset_password_form
from logging.log_manager import LogManager

def app():
    """Login page for the application."""
    st.title("Login")
    
    # Initialize managers
    auth_manager = AuthManager()
    session_manager = SessionManager()
    user_manager = UserManager()
    log_manager = LogManager()
    
    # Check if already logged in
    if session_manager.is_authenticated():
        st.success(f"You are already logged in as {session_manager.get_current_user()['username']}")
        
        # Show user info
        user_info = session_manager.get_current_user()
        st.subheader("User Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Username:** {user_info['username']}")
            st.write(f"**Email:** {user_info['email']}")
            st.write(f"**Role:** {user_info['role']}")
        
        with col2:
            st.write(f"**Last Login:** {user_info.get('last_login', 'N/A')}")
            permissions = session_manager.get_user_permissions()
            st.write(f"**Permissions:** {', '.join(permissions) if permissions else 'None'}")
        
        # Logout option
        if st.button("Logout"):
            # Log the logout
            log_manager.log(
                level="INFO",
                module="auth",
                message=f"User logged out: {session_manager.get_current_user()['username']}",
                user_id=session_manager.get_current_user().get('id', 'unknown')
            )
            
            # Clear session
            session_manager.logout()
            st.success("Logged out successfully!")
            time.sleep(1)  # Small delay for better UX
            st.experimental_rerun()
        
        return
    
    # Login tabs
    login_tab, reset_tab = st.tabs(["Login", "Reset Password"])
    
    # Login form
    with login_tab:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            auth_method = st.radio(
                "Authentication Method",
                ["Password", "Voice Recognition"],
                horizontal=True
            )
            
            if auth_method == "Password":
                username, password, submitted = login_form()
                
                if submitted:
                    with st.spinner("Logging in..."):
                        login_result = auth_manager.login(username, password)
                        
                        if login_result["success"]:
                            # Set session
                            session_manager.set_user(login_result["user"])
                            
                            # Log the login
                            log_manager.log(
                                level="INFO",
                                module="auth",
                                message=f"User logged in: {username}",
                                user_id=login_result["user"].get('id', 'unknown')
                            )
                            
                            st.success(f"Welcome back, {username}!")
                            time.sleep(1)  # Small delay for better UX
                            st.experimental_rerun()
                        else:
                            # Log the failed login attempt
                            log_manager.log(
                                level="WARNING",
                                module="auth",
                                message=f"Failed login attempt for user: {username}",
                                user_id="unknown"
                            )
                            
                            st.error(login_result["message"])
            
            else:  # Voice Recognition
                st.subheader("Voice Authentication")
                
                # Voice authentication form
                username = st.text_input("Username", key="voice_username")
                
                # Record voice
                if st.button("Start Voice Recording"):
                    with st.spinner("Listening..."):
                        # In a real implementation, this would connect to the voice_auth module
                        st.info("Voice recognition would be activated here in a real implementation.")
                        st.info("This is a placeholder - in the real system, we would use the voice_auth.py module.")
                        
                        # For demonstration purposes:
                        if username:
                            # Simulate voice auth (in reality, would call the voice_authentication module)
                            st.error("Voice authentication failed. Please try again or use password authentication.")
                            
                            # Log the attempt
                            log_manager.log(
                                level="WARNING",
                                module="auth",
                                message=f"Failed voice authentication attempt for user: {username}",
                                user_id="unknown"
                            )
        
        with col2:
            st.markdown("### Need Help?")
            st.markdown("- Make sure CAPS LOCK is off")
            st.markdown("- Usernames are case-sensitive")
            st.markdown("- Contact your administrator if you can't log in")
            
            # First time setup notice
            st.markdown("---")
            st.markdown("#### First time setup?")
            st.markdown("Run the create_admin_user.py script to create your first admin account.")
    
    # Reset password form
    with reset_tab:
        email, submitted = reset_password_form()
        
        if submitted:
            with st.spinner("Processing request..."):
                # Check if email exists
                user_exists = user_manager.check_email_exists(email)
                
                if user_exists:
                    # In a real implementation, this would send a password reset email
                    st.success("Password reset instructions have been sent to your email.")
                    
                    # Log the password reset request
                    log_manager.log(
                        level="INFO",
                        module="auth",
                        message=f"Password reset requested for email: {email}",
                        user_id="unknown"
                    )
                else:
                    st.error("No account found with that email address.")
                    
                    # Log the failed reset attempt
                    log_manager.log(
                        level="WARNING",
                        module="auth",
                        message=f"Failed password reset attempt for unknown email: {email}",
                        user_id="unknown"
                    )

if __name__ == "__main__":
    app()