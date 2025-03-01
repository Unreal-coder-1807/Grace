elif st.session_state.current_page == "voice":
            from streamlit_app.pages.voice_commands import render_voice_page
            render_voice_page()
        
        elif st.session_state.current_page == "gesture":
            from streamlit_app.pages.gesture_controls import render_gesture_page
            render_gesture_page()