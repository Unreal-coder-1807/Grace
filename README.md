# Grace: Gesture and Voice Control System

![Grace Logo](https://via.placeholder.com/150)  
**Grace** is a **multi-modal human-computer interaction system** that combines **gesture recognition** and **voice commands** to control your computer. Built with Python, Grace allows you to interact with your system using natural hand gestures and voice inputs, making it ideal for hands-free operation, accessibility, and futuristic computing experiences.

---

## **Features**

### **Gesture Control**
- **Cursor Movement**: Track your index finger to move the cursor.
- **Clicks**:
  - Left Click: Index + Thumb extended.
  - Right Click: Middle + Thumb extended.
- **Scrolling**:
  - Scroll Up/Down: Index + Middle fingers extended and moved vertically.
- **Zoom**:
  - Zoom In/Out: Two-hand gesture with index fingers moving apart/closer.
- **Brightness Control**: Adjust brightness with three-finger gestures (Index + Middle + Ring).
- **Volume Control**: Control volume with Index + Pinky fingers.
- **Screenshot**: Capture screenshots with a high-five gesture.
- **Multi-File Selection**: Use a pinch gesture (index + thumb tips touching) for multiple file selection.

### **Voice Control**
- **Hotword Detection**: Wake the system with a custom wake word using **Porcupine**.
- **Speech Recognition**: Convert speech to text using **OpenAI Whisper**.
- **Intent Recognition**: Understand user commands with **Rasa**.
- **Text-to-Speech**: Get audio feedback using **pyttsx3**.

### **System Integration**
- **Mouse/Keyboard Control**: Simulate inputs using **PyAutoGUI**.
- **Volume Control**: Adjust system volume with **pycaw**.
- **Browser Automation**: Automate web tasks with **Selenium**.
- **Brightness Control**: Adjust screen brightness (platform-specific).

### **Security**
- **Voice Authentication**: Verify users based on voice biometrics.
- **Role-Based Access Control (RBAC)**:
  - Admin: Full system control.
  - Standard: Basic controls.
  - Child Mode: Restricted access.
- **Session Management**: Track user sessions and permissions.

### **Streamlit UI**
- **Dashboard**: View system status and command history.
- **Settings**: Configure gesture and voice settings.
- **Logs**: Monitor system logs and error messages.

---

## **Directory Structure**
Grace/
├── config/ # Configuration files
│ ├── settings/ # Application settings
│ └── secrets.yaml # Sensitive credentials
├── data/ # Data storage
│ ├── models/ # Machine learning models
│ ├── training/ # Training data
│ └── biometric/ # Voice biometric data
├── db/ # Database files
│ ├── logs.db # System logs
│ ├── auth.db # Authentication data
│ └── migrations/ # Database migrations
├── src/ # Source code
│ ├── gesture_module/ # Gesture recognition
│ ├── voice_module/ # Voice command processing
│ ├── auth_module/ # Authentication system
│ ├── control_system/ # System control logic
│ ├── streamlit_app/ # Streamlit UI
│ ├── database/ # Database operations
│ ├── logging/ # Logging system
│ ├── utils/ # Shared utilities
│ └── main.py # Application entry point
├── tests/ # Test cases
├── scripts/ # Helper scripts
├── logs/ # Log files
├── docs/ # Documentation
├── requirements.txt # Project dependencies
├── README.md # Project overview
└── setup.py # Installation script

Copy

---

## **Installation**

### **Prerequisites**
- Python 3.8 or higher
- Pip package manager

### **Steps**
1. Clone the repository:
   ```bash
   git clone https://github.com/Unreal-coder-1807/Grace.git
   cd Grace
Install dependencies:

bash
Copy
pip install -r requirements.txt
Set up the database:

bash
Copy
alembic upgrade head
Configure settings:

Update config/settings/ YAML files as needed.

Add API keys and sensitive data to config/secrets.yaml.

Usage
Running the Application
Start the main application:

bash
Copy
python src/main.py
Access the Streamlit UI:

bash
Copy
streamlit run src/streamlit_app/app.py
Gesture Control
Perform gestures in front of your webcam to control the system.

Refer to the Gesture Documentation for detailed gesture mappings.

Voice Control
Use the wake word to activate voice commands.

Speak naturally to perform actions (e.g., "Open browser," "Increase volume").

UI Dashboard
View system status, logs, and command history.

Configure settings and manage users.

Configuration
Gesture Settings
Edit config/settings/gesture.yaml to customize gesture mappings and sensitivity.

Voice Settings
Edit config/settings/voice.yaml to configure:

Wake word

Speech recognition language

Text-to-speech settings

Security Settings
Edit config/settings/auth.yaml to configure:

Role-based permissions

Session timeout

Voice authentication thresholds

Dependencies
Core Libraries
MediaPipe, OpenCV, NumPy, Matplotlib

Voice Processing
Whisper, Porcupine, pyttsx3, SpeechRecognition

System Control
PyAutoGUI, pycaw, Selenium

Database
SQLite, SQLAlchemy, Alembic

UI
Streamlit

Contributing
We welcome contributions! Please follow these steps:

Fork the repository.

Create a new branch:

bash
Copy
git checkout -b feature/your-feature-name
Commit your changes:

bash
Copy
git commit -m "Add your feature"
Push to the branch:

bash
Copy
git push origin feature/your-feature-name
Open a pull request.

License
This project is licensed under the MIT License. See the LICENSE file for details.

Acknowledgments
MediaPipe for gesture recognition.

OpenAI Whisper for speech-to-text.

Picovoice Porcupine for hotword detection.

Streamlit for the user interface.

