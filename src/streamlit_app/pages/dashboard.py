"""
Dashboard page for the Streamlit application.
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

def render_dashboard():
    """Render the main dashboard page"""
    st.title("Dashboard")
    st.subheader(f"Welcome, {st.session_state.username}!")
    
    # System status card
    with st.container():
        st.markdown("### System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Voice Recognition", 
                value="Active", 
                delta="99.2% Accuracy"
            )
        
        with col2:
            st.metric(
                label="Gesture Recognition", 
                value="Active", 
                delta="97.5% Accuracy"
            )
        
        with col3:
            st.metric(
                label="System Health", 
                value="Good", 
                delta="No Issues"
            )
    
    # Recent activity and stats
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Recent Activity")
        
        # Mock activity data
        activity_data = {
            'Time': [
                (datetime.now() - timedelta(minutes=5)).strftime("%H:%M:%S"),
                (datetime.now() - timedelta(minutes=12)).strftime("%H:%M:%S"),
                (datetime.now() - timedelta(minutes=25)).strftime("%H:%M:%S"),
                (datetime.now() - timedelta(minutes=42)).strftime("%H:%M:%S"),
                (datetime.now() - timedelta(hours=1, minutes=15)).strftime("%H:%M:%S")
            ],
            'Activity': [
                "Voice command: 'Open browser'",
                "Gesture detected: Volume up",
                "Voice command: 'Check weather'",
                "Gesture detected: Navigation right",
                "Voice command: 'System status'"
            ],
            'Status': [
                "Completed",
                "Completed",
                "Completed",
                "Completed",
                "Completed"
            ]
        }
        
        activity_df = pd.DataFrame(activity_data)
        st.table(activity_df)
    
    with col2:
        st.markdown("### Usage Statistics")
        
        # Create sample data for the charts
        labels = ['Voice Commands', 'Gestures', 'Combined']
        values = [42, 28, 15]
        
        # Display a pie chart
        st.write("Command Usage Distribution")
        st.pie_chart(pd.DataFrame({'values': values}, index=labels))
        
        # Display metrics
        st.metric(label="Total Commands Today", value=85)
        st.metric(label="Avg. Response Time", value="0.8s")
    
    # Quick actions
    st.markdown("---")
    st.markdown("### Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎤 Test Voice", use_container_width=True):
            with st.spinner("Listening..."):
                # Simulate voice recognition
                time.sleep(1.5)
                st.success("Voice module is working properly!")
    
    with col2:
        if st.button("📷 Test Camera", use_container_width=True):
            with st.spinner("Checking camera..."):
                # Simulate camera check
                time.sleep(1.5)
                st.success("Camera is working properly!")
    
    with col3:
        if st.button("🔊 Test Audio", use_container_width=True):
            with st.spinner("Testing audio output..."):
                # Simulate audio test
                time.sleep(1.5)
                st.success("Audio output is working properly!")
    
    with col4:
        if st.button("🔄 System Check", use_container_width=True):
            with st.spinner("Running diagnostics..."):
                # Simulate system check
                time.sleep(2)
                st.success("All systems operational!")
    
    # Tips and help
    st.markdown("---")
    with st.expander("Tips & Help"):
        st.markdown("""
        ### Getting Started
        
        - Try saying "Hey Assistant" to activate voice commands
        - Raise your hand in front of the camera to activate gesture control
        - Visit the Settings page to customize your experience
        
        ### Top Voice Commands
        
        1. "Open [application]"
        2. "Search for [term]"
        3. "Volume up/down"
        4. "Navigate to [website]"
        5. "What's the weather like?"
        
        ### Top Gestures
        
        1. ✋ Open palm: Pause/resume
        2. 👆 Index finger: Select/click
        3. ✌️ Two fingers: Scroll up/down
        4. 👌 OK sign: Confirm action
        5. ✊ Fist: Cancel/back
        """)