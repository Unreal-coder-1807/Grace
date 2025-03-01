"""
Intent storage and management for the Gesture & Voice Controlled AI Assistant.

This module provides interfaces for storing, retrieving, and managing
voice command intents and their mappings to system actions.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_

from . import get_db_manager
from .models import Intent, PermissionLevel

# Initialize logger
logger = logging.getLogger(__name__)

class IntentStore:
    """
    Manages storage and retrieval of intent mappings for voice commands.
    """
    
    def __init__(self):
        """Initialize the intent store."""
        self.logger = logging.getLogger(__name__ + ".IntentStore")
        self.db_manager = get_db_manager()
    
    def add_intent(self, 
                   name: str, 
                   pattern: str, 
                   action_module: str, 
                   action_function: str, 
                   description: str = None, 
                   parameters: Dict = None, 
                   required_permission: PermissionLevel = PermissionLevel.USER) -> Optional[int]:
        """
        Add a new intent mapping to the database.
        
        Args:
            name: Unique name for the intent
            pattern: Regex or pattern to match the voice command
            action_module: Module containing the action function
            action_function: Function name to execute
            description: Optional description of the intent
            parameters: Optional parameters for the action function
            required_permission: Permission level required to use this intent
            
        Returns:
            int: ID of the newly created intent, or None if creation failed
        """
        session = self.db_manager.get_auth_session()
        try:
            # Check if intent already exists
            existing = session.query(Intent).filter(Intent.name == name).first()
            if existing:
                self.logger.warning(f"Intent with name '{name}' already exists")
                return None
            
            # Create new intent
            intent = Intent(
                name=name,
                pattern=pattern,
                action_module=action_module,
                action_function=action_function,
                description=description,
                parameters=parameters,
                required_permission=required_permission,
                is_active=True
            )
            
            session.add(intent)
            session.commit()
            self.logger.info(f"Added new intent '{name}' with ID {intent.id}")
            return intent.id
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error adding intent '{name}': {e}")
            return None
        finally:
            session.close()
    
    def get_intent(self, intent_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an intent by its ID.
        
        Args:
            intent_id: ID of the intent to retrieve
            
        Returns:
            Dict or None: Intent data as a dictionary, or None if not found
        """
        session = self.db_manager.get_auth_session()
        try:
            intent = session.query(Intent).filter(Intent.id == intent_id).first()
            if not intent:
                return None
            
            return {
                'id': intent.id,
                'name': intent.name,
                'description': intent.description,
                'pattern': intent.pattern,
                'action_module': intent.action_module,
                'action_function': intent.action_function,
                'parameters': intent.parameters,
                'required_permission': intent.required_permission.name,
                'is_active': intent.is_active
            }
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving intent {intent_id}: {e}")
            return None
        finally:
            session.close()
    
    def get_intent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get an intent by its name.
        
        Args:
            name: Name of the intent to retrieve
            
        Returns:
            Dict or None: Intent data as a dictionary, or None if not found
        """
        session = self.db_manager.get_auth_session()
        try:
            intent = session.query(Intent).filter(Intent.name == name).first()
            if not intent:
                return None
            
            return {
                'id': intent.id,
                'name': intent.name,
                'description': intent.description,
                'pattern': intent.pattern,
                'action_module': intent.action_module,
                'action_function': intent.action_function,
                'parameters': intent.parameters,
                'required_permission': intent.required_permission.name,
                'is_active': intent.is_active
            }
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving intent '{name}': {e}")
            return None
        finally:
            session.close()
    
    def find_matching_intents(self, text: str) -> List[Dict[str, Any]]:
        """
        Find intents that match the given text based on their patterns.
        
        Args:
            text: Text to match against intent patterns
            
        Returns:
            List[Dict]: List of matching intent dictionaries
        """
        # Note: This is a simple implementation. In production, you'd use
        # a more sophisticated NLP approach with Rasa or similar.
        session = self.db_manager.get_auth_session()
        try:
            intents = session.query(Intent).filter(Intent.is_active == True).all()
            
            # For this simple implementation, we'll just do basic contains matching
            matching_intents = []
            for intent in intents:
                # In a real implementation, we would use regex or NLP patterns
                if intent.pattern.lower() in text.lower():
                    matching_intents.append({
                        'id': intent.id,
                        'name': intent.name,
                        'description': intent.description,
                        'pattern': intent.pattern,
                        'action_module': intent.action_module,
                        'action_function': intent.action_function,
                        'parameters': intent.parameters,
                        'required_permission': intent.required_permission.name,
                        'is_active': intent.is_active,
                        'match_score': 1.0  # Simple score for now
                    })
            
            return sorted(matching_intents, key=lambda x: x['match_score'], reverse=True)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error finding matching intents: {e}")
            return []
        finally:
            session.close()
    
    def update_intent(self, intent_id: int, **kwargs) -> bool:
        """
        Update an existing intent.
        
        Args:
            intent_id: ID of the intent to update
            **kwargs: Fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            intent = session.query(Intent).filter(Intent.id == intent_id).first()
            if not intent:
                self.logger.warning(f"Intent with ID {intent_id} not found for update")
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(intent, key):
                    # Handle enum conversion
                    if key == 'required_permission' and isinstance(value, str):
                        value = PermissionLevel[value]
                    setattr(intent, key, value)
            
            session.commit()
            self.logger.info(f"Updated intent '{intent.name}' (ID: {intent_id})")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error updating intent {intent_id}: {e}")
            return False
        finally:
            session.close()
    
    def delete_intent(self, intent_id: int) -> bool:
        """
        Delete an intent by its ID.
        
        Args:
            intent_id: ID of the intent to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        session = self.db_manager.get_auth_session()
        try:
            intent = session.query(Intent).filter(Intent.id == intent_id).first()
            if not intent:
                self.logger.warning(f"Intent with ID {intent_id} not found for deletion")
                return False
            
            session.delete(intent)
            session.commit()
            self.logger.info(f"Deleted intent '{intent.name}' (ID: {intent_id})")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error deleting intent {intent_id}: {e}")
            return False
        finally:
            session.close()
    
    def get_all_intents(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all intents from the database.
        
        Args:
            active_only: If True, only return active intents
            
        Returns:
            List[Dict]: List of intent dictionaries
        """
        session = self.db_manager.get_auth_session()
        try:
            query = session.query(Intent)
            if active_only:
                query = query.filter(Intent.is_active == True)
            
            intents = query.all()
            result = []
            
            for intent in intents:
                result.append({
                    'id': intent.id,
                    'name': intent.name,
                    'description': intent.description,
                    'pattern': intent.pattern,
                    'action_module': intent.action_module,
                    'action_function': intent.action_function,
                    'parameters': intent.parameters,
                    'required_permission': intent.required_permission.name,
                    'is_active': intent.is_active
                })
            
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving all intents: {e}")
            return []
        finally:
            session.close()
    
    def bulk_import_intents(self, intents_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Import multiple intents at once.
        
        Args:
            intents_data: List of intent dictionaries to import
            
        Returns:
            Tuple[int, int]: (number of successful imports, number of failures)
        """
        success_count = 0
        failure_count = 0
        
        for intent_data in intents_data:
            try:
                # Extract required fields
                name = intent_data.get('name')
                pattern = intent_data.get('pattern')
                action_module = intent_data.get('action_module')
                action_function = intent_data.get('action_function')
                
                if not all([name, pattern, action_module, action_function]):
                    self.logger.warning(f"Missing required fields for intent: {intent_data}")
                    failure_count += 1
                    continue
                
                # Extract optional fields
                description = intent_data.get('description')
                parameters = intent_data.get('parameters')
                
                # Handle permission level
                permission_str = intent_data.get('required_permission', 'USER')
                try:
                    permission = PermissionLevel[permission_str]
                except (KeyError, ValueError):
                    permission = PermissionLevel.USER
                
                # Add the intent
                result = self.add_intent(
                    name=name,
                    pattern=pattern,
                    action_module=action_module,
                    action_function=action_function,
                    description=description,
                    parameters=parameters,
                    required_permission=permission
                )
                
                if result is not None:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                self.logger.error(f"Error importing intent: {e}")
                failure_count += 1
        
        self.logger.info(f"Bulk import complete: {success_count} succeeded, {failure_count} failed")
        return success_count, failure_count
    
    def deactivate_intent(self, intent_id: int) -> bool:
        """
        Deactivate an intent without deleting it.
        
        Args:
            intent_id: ID of the intent to deactivate
            
        Returns:
            bool: True if deactivation was successful, False otherwise
        """
        return self.update_intent(intent_id, is_active=False)
    
    def activate_intent(self, intent_id: int) -> bool:
        """
        Activate a previously deactivated intent.
        
        Args:
            intent_id: ID of the intent to activate
            
        Returns:
            bool: True if activation was successful, False otherwise
        """
        return self.update_intent(intent_id, is_active=True)