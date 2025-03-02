#!/usr/bin/env python3
"""
Gesture Voice Control System - Setup Script
-------------------------------------------
Installation script for the Gesture Voice Control System.
"""

import os
import platform
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.egg_info import egg_info


def read_requirements():
    """Read requirements from requirements.txt file."""
    with open('requirements.txt') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


def create_config_directories():
    """Create necessary configuration directories if they don't exist."""
    directories = [
        'config/settings',
        'data/models/gesture',
        'data/models/voice',
        'data/training/gesture_samples',
        'data/training/voice_samples',
        'data/biometric',
        'db/migrations',
        'logs',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")


def create_default_configs():
    """Create default configuration files if they don't exist."""
    default_configs = {
        'config/settings/app.yaml': '''# Default application configuration
version: 1.0
debug: false
log_level: INFO
data_dir: "data"
models_dir: "data/models"
''',
        'config/settings/gesture.yaml': '''# Default gesture recognition configuration
enabled: true
camera_device: 0
detection_confidence: 0.8
tracking_confidence: 0.5
frame_rate: 30
gesture_mapping:
  thumbs_up: "volume_up"
  thumbs_down: "volume_down"
  open_palm: "mouse_move"
  closed_fist: "mouse_click"
  victory: "screenshot"
  pointing: "select"
''',
        'config/settings/voice.yaml': '''# Default voice command configuration
enabled: true
language: "en-US"
hotword:
  enabled: true
  sensitivity: 0.5
  model: "data/models/voice/wake_word.ppn"
whisper:
  model: "base"
text_to_speech:
  rate: 150
  volume: 1.0
intent_recognition:
  confidence_threshold: 0.7
command_timeout: 5.0
''',
        'config/settings/auth.yaml': '''# Default authentication configuration
enabled: true
methods:
  - password
  - voice
session_timeout: 3600
password:
  min_length: 8
  require_special_chars: true
voice:
  confidence_threshold: 0.85
  samples_required: 3
''',
        'config/secrets.yaml': '''# Sensitive credentials and API keys
# WARNING: Do not commit this file to version control
# This is just a template with placeholder values

api_keys:
  openai: "your_openai_api_key_here"
  picovoice: "your_picovoice_api_key_here"

database:
  username: "db_user"
  password: "db_password"
  host: "localhost"
  port: 5432
  name: "gesture_voice_db"
'''
    }
    
    for file_path, content in default_configs.items():
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Created default config: {file_path}")


class PostInstallCommand:
    """Post-installation tasks."""
    
    def run_post_install(self):
        create_config_directories()
        create_default_configs()
        
        # Platform-specific setup
        system = platform.system()
        if system == "Windows":
            print("Setting up Windows-specific components...")
            # Windows-specific setup would go here
        elif system == "Darwin":
            print("Setting up macOS-specific components...")
            # macOS-specific setup would go here
        elif system == "Linux":
            print("Setting up Linux-specific components...")
            # Linux-specific setup would go here
        
        print("\nSetup complete!")
        print("To start the application, run: python src/main.py")
        print("To create an admin user, run: python scripts/create_admin_user.py")
        print("To calibrate gestures, run: python scripts/calibrate_gestures.py")


class PostInstall(install, PostInstallCommand):
    def run(self):
        install.run(self)
        self.run_post_install()


class PostDevelop(develop, PostInstallCommand):
    def run(self):
        develop.run(self)
        self.run_post_install()


class PostEggInfo(egg_info, PostInstallCommand):
    def run(self):
        egg_info.run(self)
        self.run_post_install()


setup(
    name="gesture-voice-control",
    version="0.1.0",
    description="A multimodal computer control system using gesture recognition and voice commands",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/gesture-voice-control",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "gesture-voice-control=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
    ],
    cmdclass={
        'install': PostInstall,
        'develop': PostDevelop,
        'egg_info': PostEggInfo,
    },
)