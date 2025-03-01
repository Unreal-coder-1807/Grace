"""
Intent Handler component for processing and responding to voice commands.

This module uses Rasa NLU to understand user intents from transcribed speech
and maps them to appropriate actions.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple, Union
from pathlib import Path
import sqlite3
import threading
from datetime import datetime

# Import Rasa components
from rasa.nlu.model import Interpreter
from rasa.shared.nlu.training_data.loading import load_data
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.nlu.model import Trainer


# Setup logger
logger = logging.getLogger(__name__)

class IntentHandler:
    """
    Handles intent recognition and processing for voice commands.
    
    Uses Rasa NLU for intent classification and entity extraction from
    transcribed speech, then maps to appropriate actions.
    """
    
    def __init__(
        self,
        model_dir: str = "data/models/voice/intent",
        config_path: str = "config/settings/voice.yaml",
        db_path: str = "db/intent_store.db",
        fallback_threshold: float = 0.3
    ):
        """
        Initialize the intent handler.
        
        Args:
            model_dir: Directory to store/load Rasa model
            config_path: Path to Rasa configuration file
            db_path: Path to SQLite database for intent storage
            fallback_threshold: Confidence threshold for intent recognition
        """
        self.model_dir = Path(model_dir)
        self.config_path = Path(config_path)
        self.db_path = Path(db_path)
        self.fallback_threshold = fallback_threshold
        
        # Runtime properties
        self.interpreter = None
        self.intent_actions = {}
        self.db_lock = threading.Lock()
        
        # Ensure directories exist
        self.model_dir.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Load intent mappings from database
        self._load_intent_mappings()
        
        # Load or train the NLU model
        self._load_model()
        
        logger.info("Intent handler initialized")
        
    def _init_database(self):
        """Initialize the SQLite database for intent storage."""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Create tables if they don't exist
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS intents (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS intent_examples (
                    id INTEGER PRIMARY KEY,
                    intent_id INTEGER,
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (intent_id) REFERENCES intents(id),
                    UNIQUE (intent_id, text)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS intent_actions (
                    id INTEGER PRIMARY KEY,
                    intent_id INTEGER,
                    action_type TEXT,
                    action_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (intent_id) REFERENCES intents(id)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS entity_examples (
                    id INTEGER PRIMARY KEY,
                    entity_id INTEGER,
                    text TEXT,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (entity_id) REFERENCES entities(id)
                )
                ''')
                
                conn.commit()
                conn.close()
                
            logger.info("Intent database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize intent database: {e}")
            raise
            
    def _load_intent_mappings(self):
        """Load intent-to-action mappings from database."""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Query all intents and their actions
                cursor.execute('''
                SELECT i.name, a.action_type, a.action_data
                FROM intents i
                JOIN intent_actions a ON i.id = a.intent_id
                ''')
                
                rows = cursor.fetchall()
                conn.close()
                
            # Build intent_actions dictionary
            for intent_name, action_type, action_data in rows:
                if intent_name not in self.intent_actions:
                    self.intent_actions[intent_name] = []
                    
                self.intent_actions[intent_name].append({
                    'type': action_type,
                    'data': json.loads(action_data)
                })
                
            logger.info(f"Loaded {len(self.intent_actions)} intent action mappings")
            
        except Exception as e:
            logger.error(f"Failed to load intent mappings: {e}")
            
    def _load_model(self):
        """Load the Rasa NLU model or train if it doesn't exist."""
        try:
            # Check if model exists
            model_file = self.model_dir / "nlu_model"
            
            if model_file.exists():
                logger.info("Loading existing NLU model")
                self.interpreter = Interpreter.load(str(model_file))
            else:
                logger.info("No existing model found, training new model")
                self._train_model()
                
        except Exception as e:
            logger.error(f"Failed to load NLU model: {e}")
            raise
            
    def _train_model(self):
        """Train a new Rasa NLU model from database examples."""
        try:
            # Get training data from database
            training_data = self._get_training_data()
            
            # Load Rasa configuration
            with open(self.config_path, 'r') as f:
                config = TrainingData.from_dict(json.load(f))
                
            # Initialize component builder
            # Initialize component builder
            builder = DefaultV1Recipe()
            
            # Train model
            trainer = Trainer(config, builder)
            interpreter = trainer.train(training_data)
            
            # Save model with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = f"nlu_model_{timestamp}"
            model_directory = interpreter.persist(
                path=str(self.model_dir),
                project_name=model_name
            )
            
            # Load the trained model
            self.interpreter = Interpreter.load(model_directory)
            
            # Cleanup old models
            self._cleanup_old_models()
            
            logger.info(f"NLU model trained and saved to {model_directory}")
            
        except Exception as e:
            logger.error(f"Failed to train NLU model: {e}")
            raise

    def _cleanup_old_models(self):
        """Keep only the 3 most recent models."""
        try:
            models = list(self.model_dir.glob("nlu_model_*"))
            models.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for model in models[3:]:
                if model.is_dir():
                    for file in model.iterdir():
                        file.unlink()
                    model.rmdir()
                    logger.debug(f"Removed old model: {model}")
                    
        except Exception as e:
            logger.warning(f"Failed to cleanup old models: {e}")

    def _get_training_data(self) -> TrainingData:
        """Get training data from database for model training."""
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get all intent examples
                cursor.execute('''
                SELECT i.name, e.text
                FROM intents i
                JOIN intent_examples e ON i.id = e.intent_id
                ''')
                
                training_examples = []
                for intent_name, text in cursor.fetchall():
                    example = {
                        "text": text,
                        "intent": intent_name,
                        "entities": []
                    }
                    training_examples.append(example)
                
                # Get all entity examples
                cursor.execute('''
                SELECT en.name, ee.text, ee.value
                FROM entities en
                JOIN entity_examples ee ON en.id = ee.entity_id
                ''')
                
                for entity_name, text, value in cursor.fetchall():
                    for example in training_examples:
                        if text in example["text"]:
                            start = example["text"].find(text)
                            end = start + len(text)
                            entity = {
                                "start": start,
                                "end": end,
                                "value": value,
                                "entity": entity_name
                            }
                            example["entities"].append(entity)
                
                conn.close()
                
                training_data = {
                    "rasa_nlu_data": {
                        "common_examples": training_examples
                    }
                }
                
                return load_data(training_data)
                
        except Exception as e:
            logger.error(f"Failed to get training data: {e}")
            raise

    def process_input(self, text: str) -> Dict[str, Any]:
        """
        Process input text and return intent classification results.
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary containing intent classification and entities
        """
        if not self.interpreter:
            raise RuntimeError("NLU model not loaded")
            
        try:
            result = self.interpreter.parse(text)
            
            if result["intent"]["confidence"] < self.fallback_threshold:
                result["intent"]["name"] = "fallback"
                result["intent"]["confidence"] = 1.0
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to process input: {e}")
            raise

    def execute_actions(self, intent_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute actions associated with the classified intent.
        
        Args:
            intent_result: Intent classification result from process_input
            
        Returns:
            List of action results
        """
        intent_name = intent_result["intent"]["name"]
        entities = intent_result["entities"]
        
        if intent_name not in self.intent_actions:
            logger.warning(f"No actions found for intent: {intent_name}")
            return []
            
        results = []
        for action in self.intent_actions[intent_name]:
            try:
                action_type = action['type']
                action_data = action['data']
                
                # Execute action based on type
                if action_type == 'system_command':
                    result = self._execute_system_command(action_data, entities)
                elif action_type == 'api_call':
                    result = self._execute_api_call(action_data, entities)
                else:
                    logger.warning(f"Unknown action type: {action_type}")
                    continue
                    
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to execute action: {e}")
                continue
                
        return results

    def _execute_system_command(
        self,
        action_data: Dict[str, Any],
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a system command action."""
        # Implementation depends on system requirements
        pass

    def _execute_api_call(
        self,
        action_data: Dict[str, Any],
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute an API call action."""
        # Implementation depends on API requirements
        pass

    def add_intent(
        self,
        name: str,
        description: str,
        examples: List[str]
    ) -> None:
        """
        Add a new intent with examples to the database.
        
        Args:
            name: Intent name
            description: Intent description
            examples: List of example phrases
        """
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Insert intent
                cursor.execute(
                    'INSERT INTO intents (name, description) VALUES (?, ?)',
                    (name, description)
                )
                intent_id = cursor.lastrowid
                
                # Insert examples
                for example in examples:
                    cursor.execute(
                        'INSERT INTO intent_examples (intent_id, text) VALUES (?, ?)',
                        (intent_id, example)
                    )
                
                conn.commit()
                conn.close()
                
            logger.info(f"Added new intent: {name}")
            
        except Exception as e:
            logger.error(f"Failed to add intent: {e}")
            raise

    def add_entity(
        self,
        name: str,
        description: str,
        examples: List[Tuple[str, str]]
    ) -> None:
        """
        Add a new entity with examples to the database.
        
        Args:
            name: Entity name
            description: Entity description
            examples: List of (text, value) tuples
        """
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Insert entity
                cursor.execute(
                    'INSERT INTO entities (name, description) VALUES (?, ?)',
                    (name, description)
                )
                entity_id = cursor.lastrowid
                
                # Insert examples
                for text, value in examples:
                    cursor.execute(
                        'INSERT INTO entity_examples (entity_id, text, value) VALUES (?, ?, ?)',
                        (entity_id, text, value)
                    )
                
                conn.commit()
                conn.close()
                
            logger.info(f"Added new entity: {name}")
            
        except Exception as e:
            logger.error(f"Failed to add entity: {e}")
            raise