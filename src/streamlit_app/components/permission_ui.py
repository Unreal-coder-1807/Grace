import streamlit as st
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from auth_module.permission_manager import PermissionManager

def permission_editor(user_id, current_permissions=None, role_permissions=None):
    """
    A UI component for editing user permissions.
    
    Args:
        user_id (str): The ID of the user whose permissions are being edited
        current_permissions (list): List of current user permissions
        role_permissions (list): List of permissions granted by the user's role
    
    Returns:
        bool: True if permissions were updated, False otherwise
    """
    permission_manager = PermissionManager()
    
    # Initialize return value
    permissions_updated = False
    
    # Get all available permissions if not provided
    if current_permissions is None:
        current_permissions = permission_manager.get_user_permissions(user_id)
    
    if role_permissions is None:
        # Get user's role first
        user_role = permission_manager.get_user_role(user_id)
        role_permissions = permission_manager.get_role_permissions(user_role)
    
    # Get all available permissions
    all_permissions = permission_manager.get_available_permissions()
    
    # Group permissions by category for better organization
    permission_categories = {}
    for perm in all_permissions:
        category = perm.split('_')[0] if '_' in perm else 'general'
        if category not in permission_categories:
            permission_categories[category] = []
        permission_categories[category].append(perm)
    
    # Store selected permissions
    selected_permissions = []
    
    # Explanation of permission types
    with st.expander("About Permissions", expanded=False):
        st.markdown("""
        ### Understanding Permissions
        
        Permissions are divided into three types:
        
        1. **Role Permissions** - These are granted automatically based on the user's role.
           - Cannot be removed individually (change the role instead)
           - Shown in gray and disabled
        
        2. **Custom Permissions** - These are granted specifically to this user.
           - Can be added or removed individually
           - Override role-based permissions
        
        3. **Effective Permissions** - What the user can actually do.
           - Combination of role and custom permissions
        
        To modify role-based permissions, go to the Roles & Permissions tab.
        """)
    
    # Create tabs for different views
    permission_tab, effective_tab = st.tabs(["Edit Custom Permissions", "View Effective Permissions"])
    
    # Tab for editing custom permissions
    with permission_tab:
        custom_permissions_form = st.form("custom_permissions_form")
        
        with custom_permissions_form:
            st.markdown("#### Custom User Permissions")
            st.markdown("Select additional permissions to grant to this user beyond their role permissions.")
            
            # Track permissions that will be added or removed
            permissions_to_add = []
            
            # Display permissions by category with better visual organization
            for category, perms in permission_categories.items():
                st.markdown(f"**{category.capitalize()}**")
                
                # Use columns for more compact display
                cols = st.columns(2)
                
                for i, perm in enumerate(perms):
                    # Determine if this permission comes from the role
                    is_role_permission = perm in role_permissions
                    
                    # Determine current state
                    is_custom_permission = perm in current_permissions and not is_role_permission
                    
                    # Which column to place it in
                    col_idx = i % 2
                    
                    # Display differently based on whether it's a role permission
                    if is_role_permission:
                        # Role permissions can't be edited individually
                        cols[col_idx].checkbox(
                            f"{perm.replace('_', ' ').capitalize()} (from role)",
                            value=True,
                            disabled=True,
                            key=f"role_{perm}"
                        )
                    else:
                        # Custom permissions can be edited
                        if cols[col_idx].checkbox(
                            perm.replace('_', ' ').capitalize(),
                            value=is_custom_permission,
                            key=f"custom_{perm}"
                        ):
                            permissions_to_add.append(perm)
            
            submit_button = st.form_submit_button("Update Permissions")
            
            if submit_button:
                # Calculate which permissions need to be added and removed
                permissions_to_remove = [p for p in current_permissions if p not in role_permissions and p not in permissions_to_add]
                
                # Update permissions
                permission_manager.update_user_permissions(
                    user_id=user_id,
                    add_permissions=permissions_to_add,
                    remove_permissions=permissions_to_remove
                )
                
                permissions_updated = True
    
    # Tab for viewing effective permissions
    with effective_tab:
        st.markdown("#### Effective Permissions")
        st.markdown("This shows all permissions the user currently has, including both role and custom permissions.")
        
        # Combine role and custom permissions to get effective permissions
        effective_permissions = list(set(role_permissions + current_permissions))
        
        # Display by category
        for category, perms in permission_categories.items():
            effective_category_perms = [p for p in perms if p in effective_permissions]
            
            if effective_category_perms:
                st.markdown(f"**{category.capitalize()}**")
                
                # Use columns for more compact display
                cols = st.columns(2)
                
                for i, perm in enumerate(effective_category_perms):
                    # Determine source
                    in_role = perm in role_permissions
                    in_custom = perm in current_permissions and not in_role
                    source = "from role" if in_role else "custom"
                    
                    # Display in appropriate column
                    col_idx = i % 2
                    cols[col_idx].markdown(f"✓ {perm.replace('_', ' ').capitalize()} ({source})")
    
    # Add option to reset to role defaults
    st.markdown("---")
    if st.button("Reset to Role Defaults"):
        # This will remove all custom permissions
        permission_manager.reset_user_to_role_permissions(user_id)
        st.success("User permissions reset to role defaults.")
        permissions_updated = True
    
    return permissions_updated

def permission_explainer():
    """
    A component that explains the permission system.
    """
    with st.expander("Permission System Explained"):
        st.markdown("""
        ### Permission System
        
        Our permission system has three main components:
        
        1. **Roles** - Predefined sets of permissions (e.g., admin, user, guest)
           - Each role has a default set of permissions
           - Users are assigned a primary role
        
        2. **Permissions** - Individual access rights (e.g., view_logs, manage_users)
           - Granular control over what actions users can perform
           - Organized by functional categories
        
        3. **Custom User Permissions** - Additional permissions granted to specific users
           - Can override role-based permissions
           - Allows for specialized access without creating new roles
        
        #### Common Permission Categories:
        
        - **view_**: Read-only access to data/features
        - **manage_**: Full control over a feature
        - **create_**: Ability to create new items
        - **delete_**: Ability to remove items
        - **edit_**: Ability to modify existing items
        - **execute_**: Ability to run specific functions/processes
        
        #### Default Roles:
        
        - **admin**: Full system access
        - **user**: Standard user access
        - **guest**: Limited view-only access
        
        Custom roles can be created with specific permission sets for your organization.
        """)

if __name__ == "__main__":
    # This is for testing the component directly
    st.title("Permission UI Component Test")
    
    # Mock data
    mock_user_id = "test_user_123"
    mock_current_permissions = ["view_logs", "view_dashboard", "edit_profile"]
    mock_role_permissions = ["view_dashboard", "view_settings"]
    
    # Display component
    permission_editor(
        user_id=mock_user_id,
        current_permissions=mock_current_permissions,
        role_permissions=mock_role_permissions
    )
    
    # Show explainer
    permission_explainer()