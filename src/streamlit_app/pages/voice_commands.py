"""
Voice Commands page for the Streamlit application.
This page allows users to interact with the voice command system.
"""

import streamlit as st
import sys
from pathlib import Path

# Add the parent directory to path to enable relative imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from voice_module.listener import VoiceListener
from voice_module.intent_handler import IntentHandler
from voice_module.hotword_detector import HotwordDetector
from logging.log_manager import get_logger

logger = get_logger(__name__)

def render_voice_page():
    """Render the voice commands interface"""
    st.title("Voice Command System")
    
    # Voice Command Status
    st.subheader("System Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Hotword Detection", value="Active")
    
    with col2:
        voice_status = st.empty()
        voice_status.metric(label="Voice Recognition", value="Ready")
    
    with col3:
        st.metric(label="Intent Recognition", value="Ready")
    
    # Voice Command Interface
    st.subheader("Voice Command Interface")
    
    listen_col, command_col = st.columns([1, 2])
    
    with listen_col:
        if st.button("Start Listening", use_container_width=True, type="primary"):
            voice_status.metric(label="Voice Recognition", value="Listening")
            st.session_state.listening = True
            # Placeholder for actual voice listening functionality
            st.info("Voice recognition activated. Speak your command.")
            
            # You would integrate with your voice_module here
            # For now, this is just a UI placeholder
            
        if st.button("Stop Listening", use_container_width=True):
            voice_status.metric(label="Voice Recognition", value="Ready")
            st.session_state.listening = False
            st.info("Voice recognition deactivated.")
    
    with command_col:
        st.text_area("Recognized Text", 
                     value=st.session_state.get("recognized_text", "Your speech will appear here..."),
                     height=100,
                     disabled=True)
    
    # Recent Commands Log
    st.subheader("Recent Commands")
    
    # Placeholder data - in a real implementation, you'd pull from a database
    sample_commands = [
        {"timestamp": "2023-09-22 14:32:11", "command": "Open browser", "status": "Executed"},
        {"timestamp": "2023-09-22 14:30:45", "command": "Increase volume", "status": "Executed"},
        {"timestamp": "2023-09-22 14:28:17", "command": "Check weather", "status": "Failed"}
    ]
    
    st.dataframe(sample_commands, use_container_width=True)
    
    # Voice Command Settings
    with st.expander("Voice Command Settings"):
        st.subheader("Hotword Settings")
        st.text_input("Hotword Phrase", value="Hey Assistant")
        st.slider("Sensitivity", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
        
        st.subheader("Voice Recognition Settings")
        st.selectbox("Recognition Model", 
                     options=["Default (Whisper Small)", "Whisper Tiny", "Whisper Base", "Whisper Medium"])
        st.checkbox("Filter Background Noise", value=True)
        
        if st.button("Save Settings"):
            st.success("Settings saved successfully!")
            
    # Voice Training
    with st.expander("Voice Training"):
        st.subheader("Train Your Voice Profile")
        st.write("Training your voice helps the system recognize your commands more accurately.")
        
        st.selectbox("Training Phrase", 
                    options=["The quick brown fox jumps over the lazy dog",
                            "She sells seashells by the seashore",
                            "How much wood would a woodchuck chuck"])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Recording", use_container_width=True):
                st.info("Please read the phrase clearly...")
        with col2:
            if st.button("Submit Recording", use_container_width=True):
                st.success("Voice sample recorded successfully!")
        
        st.progress(st.session_state.get("training_progress", 30))
        st.text("Training progress: 3/10 samples recorded")

if __name__ == "__main__":
    render_voice_page()