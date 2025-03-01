import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging.log_manager import LogManager
from auth_module.session_manager import SessionManager

def app():
    """Logs visualization and analysis page."""
    st.title("System Logs")
    
    # Check user authentication
    session_manager = SessionManager()
    if not session_manager.is_authenticated():
        st.error("Please log in to access this page.")
        st.stop()
    
    # Check permissions
    if not session_manager.has_permission("view_logs"):
        st.error("You do not have permission to view logs.")
        st.stop()
    
    # Initialize log manager
    log_manager = LogManager()
    
    # Sidebar filters
    st.sidebar.header("Log Filters")
    
    # Time range filter
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time", "Custom Range"]
    )
    
    if time_range == "Custom Range":
        col1, col2 = st.sidebar.columns(2)
        start_date = col1.date_input("Start Date", datetime.datetime.now() - timedelta(days=7))
        end_date = col2.date_input("End Date", datetime.datetime.now())
        
        # Convert to datetime with time
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
    else:
        # Calculate datetime range based on selection
        now = datetime.datetime.now()
        if time_range == "Last Hour":
            start_datetime = now - timedelta(hours=1)
        elif time_range == "Last 24 Hours":
            start_datetime = now - timedelta(days=1)
        elif time_range == "Last 7 Days":
            start_datetime = now - timedelta(days=7)
        elif time_range == "Last 30 Days":
            start_datetime = now - timedelta(days=30)
        else:  # All Time
            start_datetime = datetime.datetime(1970, 1, 1)
        end_datetime = now
    
    # Log level filter
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    selected_levels = st.sidebar.multiselect("Log Levels", log_levels, default=log_levels)
    
    # Module filter
    modules = log_manager.get_distinct_modules()
    selected_modules = st.sidebar.multiselect("Modules", modules, default=[])
    
    # Search filter
    search_term = st.sidebar.text_input("Search Logs")
    
    # Clear filters button
    if st.sidebar.button("Clear Filters"):
        # This will reset the page and reload with defaults
        st.experimental_rerun()
    
    # Get logs with filters
    logs = log_manager.get_logs(
        start_time=start_datetime,
        end_time=end_datetime,
        levels=selected_levels,
        modules=selected_modules if selected_modules else None,
        search_term=search_term if search_term else None
    )
    
    # Display logs overview
    st.header("Logs Overview")
    
    if logs.empty:
        st.info("No logs found with the current filters.")
    else:
        # Convert timestamp to datetime for better display
        logs['timestamp'] = pd.to_datetime(logs['timestamp'])
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Logs", len(logs))
        
        if not logs.empty:
            col2.metric("Error Rate", f"{(len(logs[logs['level'].isin(['ERROR', 'CRITICAL'])]) / len(logs) * 100):.1f}%")
            col3.metric("Most Common Module", logs['module'].value_counts().index[0] if not logs['module'].value_counts().empty else "N/A")
            col4.metric("Unique Users", logs['user_id'].nunique())
        
        # Visualizations
        st.subheader("Log Analytics")
        
        tab1, tab2, tab3 = st.tabs(["Log Level Distribution", "Time Series", "Module Activity"])
        
        with tab1:
            # Log level distribution
            fig, ax = plt.subplots(figsize=(10, 6))
            level_counts = logs['level'].value_counts().reset_index()
            level_counts.columns = ['level', 'count']
            sns.barplot(x='level', y='count', data=level_counts, palette='viridis', ax=ax)
            ax.set_title('Distribution of Log Levels')
            ax.set_xlabel('Log Level')
            ax.set_ylabel('Count')
            st.pyplot(fig)
            
        with tab2:
            # Time series of logs
            fig, ax = plt.subplots(figsize=(10, 6))
            logs['hour'] = logs['timestamp'].dt.hour
            hourly_logs = logs.groupby(['hour', 'level']).size().unstack().fillna(0)
            hourly_logs.plot(kind='line', ax=ax)
            ax.set_title('Log Activity by Hour')
            ax.set_xlabel('Hour of Day')
            ax.set_ylabel('Number of Logs')
            ax.legend(title='Log Level')
            st.pyplot(fig)
            
        with tab3:
            # Module activity
            fig, ax = plt.subplots(figsize=(10, 6))
            module_counts = logs['module'].value_counts().head(10).reset_index()
            module_counts.columns = ['module', 'count']
            sns.barplot(x='count', y='module', data=module_counts, palette='viridis', ax=ax)
            ax.set_title('Top 10 Active Modules')
            ax.set_xlabel('Count')
            ax.set_ylabel('Module')
            st.pyplot(fig)
        
        # Raw logs table with pagination
        st.subheader("Raw Logs")
        
        # Pagination
        logs_per_page = st.selectbox("Logs per page", [10, 25, 50, 100], index=1)
        total_pages = (len(logs) + logs_per_page - 1) // logs_per_page
        page_number = st.number_input("Page", min_value=1, max_value=max(1, total_pages), step=1)
        
        # Calculate start and end indices for pagination
        start_idx = (page_number - 1) * logs_per_page
        end_idx = min(start_idx + logs_per_page, len(logs))
        
        # Show log details
        st.dataframe(logs.iloc[start_idx:end_idx].drop(columns=['hour'] if 'hour' in logs.columns else []))
        
        # Export logs
        st.download_button(
            "Export Logs as CSV",
            logs.to_csv(index=False).encode('utf-8'),
            "logs_export.csv",
            "text/csv",
            key='download-csv'
        )
    
    # Admin actions (only visible to admins)
    if session_manager.has_permission("manage_logs"):
        st.header("Log Management")
        st.warning("Warning: These actions are permanent and cannot be undone.")
        
        col1, col2 = st.columns(2)
        
        # Clear logs by age
        with col1:
            st.subheader("Clear Old Logs")
            days_to_keep = st.number_input("Keep logs from last X days", min_value=1, value=30)
            if st.button("Clear Old Logs"):
                confirmation = st.text_input("Type 'CONFIRM' to clear logs older than {} days".format(days_to_keep))
                if confirmation == "CONFIRM":
                    cutoff_date = datetime.datetime.now() - timedelta(days=days_to_keep)
                    log_manager.clear_logs_before(cutoff_date)
                    st.success(f"Logs older than {days_to_keep} days have been cleared.")
        
        # Clear logs by type
        with col2:
            st.subheader("Clear Logs by Type")
            level_to_clear = st.selectbox("Select log level to clear", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
            if st.button("Clear Selected Logs"):
                confirmation = st.text_input("Type 'CONFIRM' to clear all {} logs".format(level_to_clear))
                if confirmation == "CONFIRM":
                    log_manager.clear_logs_by_level(level_to_clear)
                    st.success(f"All {level_to_clear} logs have been cleared.")

if __name__ == "__main__":
    app()