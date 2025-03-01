"""
Settings page for the Streamlit application.
"""

import streamlit as st
import time
from streamlit_app.components.auth_forms import voice_enrollment_form

def render_settings_page():
    """Render the settings page"""
    st.title("Settings")
    
    tabs = st.tabs(["Account", "Voice Recognition", "Gesture Control", "System"])
    
    with tabs[0]:
        render_account_settings()
    
    with tabs[1]:
        render_voice_settings()
    
    with tabs[2]:
        render_gesture_settings()
    
    with tabs[3]:
        render_system_settings()


def render_account_settings():
    """Render account settings section"""
    st.header("Account Settings")
    
    # User profile information
    with st.container():
        st.subheader("Profile Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            current_username = st.session_state.username
            username = st.text_input("Username", value=current_username)
            email = st.text_input("Email", value="user@example.com")  # Would be fetched from database
        
        with col2:
            st.text_input("First Name", value="")
            st.text_input("Last Name", value="")
        
        if st.button("Update Profile", use_container_width=True):
            # This would update the user's profile in the database
            with st.spinner("Updating profile..."):
                time.sleep(1)
                st.success("Profile updated successfully!")
    
    # Password change
    with st.container():
        st.markdown("---")
        st.subheader("Change Password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            current_password = st.text_input("Current Password", type="password")
        
        with col2:
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.button("Change Password", use_container_width=True):
            if not current_password or not new_password or not confirm_password:
                st.error("All fields are required.")
            elif new_password != confirm_password:
                st.error("New passwords do not match.")
            else:
                # This would update the password in the database
                with st.spinner("Updating password..."):
                    time.sleep(1)
                    st.success("Password updated successfully!")
    
    # Voice authentication
    with st.container():
        st.markdown("---")
        st.subheader("Voice Authentication")
        
        voice_auth_enabled = st.checkbox("Enable Voice Authentication", value=False)
        
        if voice_auth_enabled:
            voice_enrollment_form()
        else:
            st.info("Enable voice authentication to log in using just your voice.")
    
    # Account deletion
    with st.container():
        st.markdown("---")
        st.subheader("Danger Zone")
        
        with st.expander("Delete Account"):
            st.warning("This action cannot be undone. All your data will be permanently deleted.")
            
            confirm_delete = st.text_input("Type your username to confirm deletion")
            
            if st.button("Permanently Delete Account", use_container_width=True):
                if confirm_delete == st.session_state.username:
                    # This would delete the user account
                    with st.spinner("Deleting account..."):
                        time.sleep(1)
                        st.success("Account deleted successfully. Redirecting to login page...")
                        time.sleep(2)
                        
                        # Reset session state
                        st.session_state.authenticated = False
                        st.session_state.user_id = None
                        st.session_state.username = None
                        st.session_state.is_admin = False
                        st.rerun()
                else:
                    st.error("Username doesn't match. Account not deleted.")


def render_voice_settings():
    """Render voice recognition settings section"""
    st.header("Voice Recognition Settings")
    
    # Wake word settings
    with st.container():
        st.subheader("Wake Word")
        
        wake_word = st.text_input("Wake Word or Phrase", value="Hey Assistant")
        wake_word_sensitivity = st.slider("Wake Word Sensitivity", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
        
        if st.button("Update Wake Word", use_container_width=True):
            with st.spinner("Updating wake word..."):
                time.sleep(1)
                st.success(f"Wake word updated to '{wake_word}'")
    
    # Voice recognition settings
    with st.container():
        st.markdown("---")
        st.subheader("Recognition Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            language = st.selectbox(
                "Primary Language",
                ["English (US)", "English (UK)", "Spanish", "French", "German", "Japanese", "Chinese"]
            )
            
            voice_timeout = st.slider("Voice Command Timeout (seconds)", min_value=1, max_value=10, value=5)
        
        with col2:
            continuous_listening = st.checkbox("Enable Continuous Listening", value=True)
            voice_feedback = st.checkbox("Voice Command Feedback", value=True)
    
    # Voice response settings
    with st.container():
        st.markdown("---")
        st.subheader("Voice Response")
        
        enable_voice_response = st.checkbox("Enable Voice Responses", value=True)
        
        if enable_voice_response:
            col1, col2 = st.columns(2)
            
            with col1:
                voice_type = st.selectbox(
                    "Voice Type",
                    ["Female 1", "Female 2", "Male 1", "Male 2"]
                )
            
            with col2:
                voice_speed = st.slider("Voice Speed", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
            
            # Test voice button
            if st.button("Test Voice Response", use_container_width=True):
                with st.spinner("Generating voice..."):
                    time.sleep(1)
                    st.success("Voice response test complete!")
                    # This would actually play an audio sample
        else:
            st.info("Voice responses are disabled. The system will only provide visual feedback.")
    
    # Save settings
    st.markdown("---")
    if st.button("Save All Voice Settings", use_container_width=True, type="primary"):
        with st.spinner("Saving settings..."):
            time.sleep(1)
            st.success("Voice recognition settings saved successfully!")


def render_gesture_settings():
    """Render gesture control settings section"""
    st.header("Gesture Control Settings")
    
    # Enable/disable gesture control
    enable_gestures = st.checkbox("Enable Gesture Control", value=True)
    
    if enable_gestures:
        # Gesture sensitivity
        with st.container():
            st.subheader("Sensitivity Settings")
            
            gesture_sensitivity = st.slider("Gesture Detection Sensitivity", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
            gesture_timeout = st.slider("Gesture Command Timeout (seconds)", min_value=1, max_value=5, value=2)
        
        # Gesture customization
        with st.container():
            st.markdown("---")
            st.subheader("Gesture Mapping")
            st.write("Configure which actions are performed by each gesture.")
            
            gestures = [
                "Open palm", 
                "Closed fist",
                "Index finger pointing",
                "Two fingers (peace sign)",
                "Thumb up",
                "OK sign (thumb and index finger)"
            ]
            
            actions = [
                "Pause/Resume",
                "Select/Click",
                "Navigate Back",
                "Scroll Up/Down",
                "Volume Up",
                "Volume Down",
                "Next Item",
                "Previous Item",
                "Open Context Menu",
                "Cancel Operation"
            ]
            
            # Create mappings
            for gesture in gestures:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(gesture)
                with col2:
                    current_action = "Select/Click" if gesture == "Index finger pointing" else actions[0]
                    st.selectbox(f"Action for {gesture}", actions, index=actions.index(current_action), key=f"gesture_{gesture}")
        
        # Gesture calibration
        with st.container():
            st.markdown("---")
            st.subheader("Gesture Calibration")
            
            if st.button("Calibrate Gestures", use_container_width=True):
                with st.spinner("Please prepare to show gestures to the camera..."):
                    # This would open camera and run calibration
                    time.sleep(2)
                    st.info("Calibration wizard would open camera here")
                    # In a real implementation, this would launch a calibration wizard
    else:
        st.info("Gesture control is currently disabled. Enable it to configure gesture settings.")
    
    # Save settings
    st.markdown("---")
    if st.button("Save All Gesture Settings", use_container_width=True, type="primary"):
        with st.spinner("Saving settings..."):
            time.sleep(1)
            st.success("Gesture control settings saved successfully!")


def render_system_settings():
    """Render system settings section"""
    st.header("System Settings")
    
    # Startup settings
    with st.container():
        st.subheader("Startup Options")
        
        start_with_system = st.checkbox("Start on system boot", value=True)
        start_minimized = st.checkbox("Start minimized", value=False)
    
    # Performance settings
    with st.container():
        st.markdown("---")
        st.subheader("Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            camera_resolution = st.selectbox(
                "Camera Resolution",
                ["640x480", "1280x720", "1920x1080"]
            )
            
            max_cpu_usage = st.slider("Max CPU Usage (%)", min_value=10, max_value=100, value=50)
        
        with col2:
            frame_rate = st.slider("Gesture Detection Frame Rate", min_value=5, max_value=60, value=15)
            background_processing = st.checkbox("Allow Background Processing", value=True)
    
    # Logging settings
    with st.container():
        st.markdown("---")
        st.subheader("Logging and Privacy")
        
        log_level = st.selectbox(
            "Log Level",
            ["Error", "Warning", "Info", "Debug"]
        )
        
        command_history = st.slider("Keep Command History (days)", min_value=1, max_value=90, value=30)
        
        collect_analytics = st.checkbox("Share Anonymous Usage Statistics", value=True)
        st.info("This helps us improve the system by collecting anonymous usage patterns.")
    
    # System maintenance
    with st.container():
        st.markdown("---")
        st.subheader("System Maintenance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Clear All Logs", use_container_width=True):
                with st.spinner("Clearing logs..."):
                    time.sleep(1)
                    st.success("Logs cleared successfully!")
        
        with col2:
            if st.button("Reset to Default Settings", use_container_width=True):
                with st.spinner("Resetting settings..."):
                    time.sleep(1)
                    st.success("Settings reset to default values!")
    
    # Save settings
    st.markdown("---")
    if st.button("Save All System Settings", use_container_width=True, type="primary"):
        with st.spinner("Saving settings..."):
            time.sleep(1)
            st.success("System settings saved successfully!")