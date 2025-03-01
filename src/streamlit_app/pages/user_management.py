import streamlit as st
import pandas as pd
import sys
import os
import time
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_module.user_manager import UserManager
from auth_module.permission_manager import PermissionManager
from auth_module.session_manager import SessionManager
from components.permission_ui import permission_editor
from logging.log_manager import LogManager

def app():
    """User management page for administrators."""
    st.title("User Management")
    
    # Initialize managers
    user_manager = UserManager()
    permission_manager = PermissionManager()
    session_manager = SessionManager()
    log_manager = LogManager()
    
    # Check if user is authenticated
    if not session_manager.is_authenticated():
        st.error("Please log in to access this page.")
        st.stop()
    
    # Check if user has admin permissions
    current_user = session_manager.get_current_user()
    if not session_manager.has_permission("manage_users"):
        st.error("You do not have permission to access user management.")
        st.stop()
    
    # Main tabs
    user_list_tab, create_user_tab, roles_tab = st.tabs(["User List", "Create User", "Roles & Permissions"])
    
    # User List Tab
    with user_list_tab:
        st.subheader("User List")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            role_filter = st.multiselect(
                "Filter by Role",
                permission_manager.get_available_roles(),
                default=[]
            )
        
        with col2:
            status_filter = st.multiselect(
                "Filter by Status",
                ["Active", "Inactive", "Locked"],
                default=["Active"]
            )
            
        with col3:
            search = st.text_input("Search Users", placeholder="Username or email...")
        
        # Get user list with filters
        users = user_manager.get_users(
            roles=role_filter if role_filter else None,
            status=[s.lower() for s in status_filter] if status_filter else None,
            search=search if search else None
        )
        
        # Display user table
        if users:
            # Convert to DataFrame for better display
            user_df = pd.DataFrame(users)
            
            # Don't show password hash or sensitive fields
            if 'password_hash' in user_df.columns:
                user_df = user_df.drop(columns=['password_hash'])
            
            # Format last login
            if 'last_login' in user_df.columns:
                user_df['last_login'] = pd.to_datetime(user_df['last_login']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Select user to view/edit
            selected_username = st.selectbox(
                "Select user to view/edit",
                options=user_df['username'].tolist(),
                index=None
            )
            
            # Display user table
            st.dataframe(user_df, use_container_width=True)
            
            # User detail view
            if selected_username:
                selected_user = user_manager.get_user_by_username(selected_username)
                if selected_user:
                    with st.expander(f"User Details: {selected_username}", expanded=True):
                        st.write(f"**User ID:** {selected_user.get('id', 'N/A')}")
                        st.write(f"**Email:** {selected_user.get('email', 'N/A')}")
                        st.write(f"**Role:** {selected_user.get('role', 'N/A')}")
                        st.write(f"**Status:** {selected_user.get('status', 'N/A').capitalize()}")
                        st.write(f"**Created:** {selected_user.get('created_at', 'N/A')}")
                        st.write(f"**Last Login:** {selected_user.get('last_login', 'N/A')}")
                        
                        # User actions
                        st.subheader("User Actions")
                        
                        # Cannot modify own admin status or lock own account
                        is_self = current_user.get('username') == selected_username
                        
                        col1, col2, col3 = st.columns(3)
                        
                        # Status toggle
                        with col1:
                            if is_self:
                                st.info("Cannot change your own status")
                            else:
                                current_status = selected_user.get('status', 'active')
                                if current_status == 'active':
                                    if st.button("Deactivate User"):
                                        user_manager.update_user_status(selected_user['id'], 'inactive')
                                        log_manager.log(
                                            level="INFO",
                                            module="user_management",
                                            message=f"User deactivated: {selected_username}",
                                            user_id=current_user.get('id', 'unknown')
                                        )
                                        st.success(f"User {selected_username} deactivated.")
                                        time.sleep(1)
                                        st.experimental_rerun()
                                else:
                                    if st.button("Activate User"):
                                        user_manager.update_user_status(selected_user['id'], 'active')
                                        log_manager.log(
                                            level="INFO",
                                            module="user_management",
                                            message=f"User activated: {selected_username}",
                                            user_id=current_user.get('id', 'unknown')
                                        )
                                        st.success(f"User {selected_username} activated.")
                                        time.sleep(1)
                                        st.experimental_rerun()
                        
                        # Lock/Unlock user
                        with col2:
                            if is_self:
                                st.info("Cannot lock your own account")
                            else:
                                is_locked = selected_user.get('status') == 'locked'
                                if is_locked:
                                    if st.button("Unlock User"):
                                        user_manager.update_user_status(selected_user['id'], 'active')
                                        log_manager.log(
                                            level="INFO",
                                            module="user_management",
                                            message=f"User unlocked: {selected_username}",
                                            user_id=current_user.get('id', 'unknown')
                                        )
                                        st.success(f"User {selected_username} unlocked.")
                                        time.sleep(1)
                                        st.experimental_rerun()
                                else:
                                    if st.button("Lock User"):
                                        user_manager.update_user_status(selected_user['id'], 'locked')
                                        log_manager.log(
                                            level="INFO",
                                            module="user_management",
                                            message=f"User locked: {selected_username}",
                                            user_id=current_user.get('id', 'unknown')
                                        )
                                        st.success(f"User {selected_username} locked.")
                                        time.sleep(1)
                                        st.experimental_rerun()
                        
                        # Reset password 
                        with col3:
                            if st.button("Reset Password"):
                                # Generate temporary password
                                temp_password = user_manager.reset_user_password(selected_user['id'])
                                log_manager.log(
                                    level="INFO",
                                    module="user_management",
                                    message=f"Password reset for user: {selected_username}",
                                    user_id=current_user.get('id', 'unknown')
                                )
                                st.success(f"Password reset for {selected_username}.")
                                st.info(f"Temporary password: {temp_password}")
                                st.info("Please store this password securely and share it with the user.")
                        
                        # User role editor
                        st.subheader("User Role")
                        
                        if is_self and selected_user.get('role') == 'admin':
                            st.info("Cannot change your own admin role")
                        else:
                            available_roles = permission_manager.get_available_roles()
                            current_role = selected_user.get('role', 'user')
                            new_role = st.selectbox(
                                "Role",
                                options=available_roles,
                                index=available_roles.index(current_role) if current_role in available_roles else 0
                            )
                            
                            if new_role != current_role:
                                if st.button("Update Role"):
                                    user_manager.update_user_role(selected_user['id'], new_role)
                                    log_manager.log(
                                        level="INFO",
                                        module="user_management",
                                        message=f"Role updated for user {selected_username}: {current_role} -> {new_role}",
                                        user_id=current_user.get('id', 'unknown')
                                    )
                                    st.success(f"Role updated for {selected_username} to {new_role}.")
                                    time.sleep(1)
                                    st.experimental_rerun()
                        
                        # User custom permissions
                        st.subheader("Custom Permissions")
                        
                        # Get user permissions
                        user_permissions = permission_manager.get_user_permissions(selected_user['id'])
                        role_permissions = permission_manager.get_role_permissions(selected_user.get('role', 'user'))
                        
                        # Show permission editor component
                        if permission_editor(
                            user_id=selected_user['id'],
                            current_permissions=user_permissions,
                            role_permissions=role_permissions
                        ):
                            st.success("Permissions updated.")
                            log_manager.log(
                                level="INFO",
                                module="user_management",
                                message=f"Permissions updated for user: {selected_username}",
                                user_id=current_user.get('id', 'unknown')
                            )
                            time.sleep(1)
                            st.experimental_rerun()
                
                # Delete user option
                st.subheader("Delete User")
                st.warning("Warning: This action cannot be undone.")
                
                if is_self:
                    st.info("Cannot delete your own account")
                else:
                    delete_confirm = st.text_input(
                        f"Type '{selected_username}' to confirm deletion",
                        key="delete_confirm"
                    )
                    
                    if delete_confirm == selected_username:
                        if st.button("Delete User", type="primary"):
                            user_manager.delete_user(selected_user['id'])
                            log_manager.log(
                                level="WARNING",
                                module="user_management",
                                message=f"User deleted: {selected_username}",
                                user_id=current_user.get('id', 'unknown')
                            )
                            st.success(f"User {selected_username} has been deleted.")
                            time.sleep(1)
                            st.experimental_rerun()
        else:
            st.info("No users found matching the current filters.")
    
    # Create User Tab
    with create_user_tab:
        st.subheader("Create New User")
        
        # User creation form
        with st.form("create_user_form"):
            username = st.text_input("Username", placeholder="Enter username")
            email = st.text_input("Email", placeholder="Enter email")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            
            available_roles = permission_manager.get_available_roles()
            role = st.selectbox("Role", options=available_roles)
            
            col1, col2 = st.columns(2)
            with col1:
                require_password_change = st.checkbox("Require Password Change on First Login", value=True)
            with col2:
                send_welcome_email = st.checkbox("Send Welcome Email", value=True)
            
            submit_button = st.form_submit_button("Create User")
            
            if submit_button:
                if not username or not email or not password:
                    st.error("Username, email, and password are required.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # Create the user
                    result = user_manager.create_user(
                        username=username,
                        email=email,
                        password=password,
                        role=role,
                        require_password_change=require_password_change
                    )
                    
                    if result["success"]:
                        st.success(f"User {username} created successfully!")
                        
                        # Log the creation
                        log_manager.log(
                            level="INFO",
                            module="user_management",
                            message=f"New user created: {username} with role {role}",
                            user_id=current_user.get('id', 'unknown')
                        )
                        
                        # Welcome email notice
                        if send_welcome_email:
                            st.info("Welcome email would be sent in a complete implementation.")
                    else:
                        st.error(f"Error creating user: {result['message']}")
    
    # Roles & Permissions Tab
    with roles_tab:
        st.subheader("Role Management")
        
        # Get available roles
        available_roles = permission_manager.get_available_roles()
        
        # Role selector
        selected_role = st.selectbox(
            "Select Role to Edit",
            options=available_roles
        )
        
        if selected_role:
            # Get permissions for the role
            role_permissions = permission_manager.get_role_permissions(selected_role)
            all_permissions = permission_manager.get_available_permissions()
            
            # Display role information
            st.write(f"**Role:** {selected_role}")
            
            # Group permissions by category
            permission_categories = {}
            for perm in all_permissions:
                category = perm.split('_')[0] if '_' in perm else 'general'
                if category not in permission_categories:
                    permission_categories[category] = []
                permission_categories[category].append(perm)
            
            # Display permissions by category
            st.subheader("Role Permissions")
            
            # Create form for updating permissions
            with st.form("update_role_permissions"):
                selected_permissions = []
                
                # Display permissions by category
                for category, perms in permission_categories.items():
                    st.write(f"**{category.capitalize()}**")
                    cols = st.columns(2)
                    for i, perm in enumerate(perms):
                        col_idx = i % 2
                        is_checked = perm in role_permissions
                        if cols[col_idx].checkbox(
                            perm.replace('_', ' ').capitalize(),
                            value=is_checked,
                            key=f"perm_{perm}"
                        ):
                            selected_permissions.append(perm)
                
                submit_button = st.form_submit_button("Update Role Permissions")
                
                if submit_button:
                    # Update role permissions
                    permission_manager.update_role_permissions(selected_role, selected_permissions)
                    log_manager.log(
                        level="INFO",
                        module="user_management",
                        message=f"Updated permissions for role: {selected_role}",
                        user_id=current_user.get('id', 'unknown')
                    )
                    st.success(f"Permissions updated for role: {selected_role}")
                    time.sleep(1)
                    st.experimental_rerun()
            
            # Create new role section
            st.subheader("Create New Role")
            with st.form("create_role_form"):
                new_role_name = st.text_input("Role Name", placeholder="Enter new role name")
                
                # Base the new role on existing role
                base_role = st.selectbox(
                    "Base on Existing Role",
                    options=["None"] + available_roles,
                    index=0
                )
                
                submit_button = st.form_submit_button("Create Role")
                
                if submit_button:
                    if not new_role_name:
                        st.error("Role name is required.")
                    elif new_role_name in available_roles:
                        st.error(f"Role '{new_role_name}' already exists.")
                    else:
                        # Create new role
                        base_permissions = []
                        if base_role != "None":
                            base_permissions = permission_manager.get_role_permissions(base_role)
                        
                        permission_manager.create_role(new_role_name, base_permissions)
                        log_manager.log(
                            level="INFO",
                            module="user_management",
                            message=f"New role created: {new_role_name} based on {base_role}",
                            user_id=current_user.get('id', 'unknown')
                        )
                        st.success(f"Role '{new_role_name}' created successfully!")
                        time.sleep(1)
                        st.experimental_rerun()
            
            # Delete role option
            if selected_role not in ["admin", "user"]:  # Prevent deletion of system roles
                st.subheader("Delete Role")
                st.warning("Warning: This action cannot be undone. Users with this role will be reassigned to 'user' role.")
                
                delete_confirm = st.text_input(
                    f"Type '{selected_role}' to confirm deletion",
                    key="delete_role_confirm"
                )
                
                if delete_confirm == selected_role:
                    if st.button("Delete Role", type="primary"):
                        permission_manager.delete_role(selected_role)
                        log_manager.log(
                            level="WARNING",
                            module="user_management",
                            message=f"Role deleted: {selected_role}",
                            user_id=current_user.get('id', 'unknown')
                        )
                        st.success(f"Role '{selected_role}' has been deleted.")
                        time.sleep(1)
                        st.experimental_rerun()

if __name__ == "__main__":
    app()