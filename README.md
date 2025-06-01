# Medical Assistant Chatbot

The **Medical Assistant Chatbot** is a Rasa-powered conversational AI designed to assist users with medical-related queries. It features real-time communication, a rich web interface, and customizable intents and actions for a smooth user experience.

---

## 📝 Description

This project is built with **Rasa Open Source** to:
- Recognize user intents and extract entities
- Handle dialogue management with custom rules and stories
- Provide a user-friendly web-based chat interface for interaction
- Respond with rich content like text and images
- Manage user data through a Flask backend
- Support user creation and management

The chatbot uses Python-based custom actions and is integrated with a browser-based chat widget.

---

## 🛠️ Requirements

To run this project, you need:
- **Python**: Version 3.8 or later
- **Rasa Open Source**: Installed via pip
- **Node.js and npm**: (for webchat integration)
- **Browser**: Any modern browser to open the web chat interface
- **PyCharm**: For development and running the application
- **Flask**: For the backend API

---

## 🚀 Features

- **Intent Recognition**: Handles `greet_intent`, `goodbye_intent`, and more
- **Custom Actions**: Uses Python scripts for dynamic responses
- **Rich Responses**: Displays text, buttons, and images
- **Interactive Web Interface**: Engages users with real-time communication
- **Scalable Design**: Easily extendable with new intents and actions
- **User Management**: Create and manage user accounts
- **Database Integration**: Store and retrieve user data

---

## 🔧 Installation

### 1. Set Up Environment

```bash
# Clone the repository
git clone https://github.com/soncuteanca/RasaMedical

# Navigate to project directory
cd RasaMedical

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix/macOS:
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Train the Model

```bash
# Train the model
rasa train
```

### 3. Running the Application

You need to run three servers simultaneously:

1. **Flask Server** (for user management API):
```bash
python server.py
```
This runs on port 5000 and handles user creation and management.

2. **Rasa Action Server** (for custom actions):
```bash
rasa run actions
```
This runs the custom actions like fetching users.

3. **Rasa Server** (for chat functionality):
```bash
rasa run -m models --enable-api --cors "*" --debug
```
This runs the Rasa model and enables the chat API.

### 4. Access the Application

1. Open the project in PyCharm
2. Open `html/home_page.html` in PyCharm (it will open on port 63342)
3. You can now:
   - Use the chat functionality
   - Create new users
   - Access all features of the application

The application uses multiple ports:
- Port 63342: PyCharm's server for serving HTML pages
- Port 5000: Flask server for user management API
- Port 5005: Rasa server for chat functionality

---

## 🛠️ Command Reference

### Basic Commands

```bash
# Train models
rasa train                  # Train both NLU and Core models
rasa train nlu             # Train only NLU components
rasa train core            # Train only Core models

# Testing and Validation
rasa shell                 # Launch interactive bot session
rasa data validate         # Check configuration and training data
rasa test nlu             # Generate detailed NLU report

# Help
rasa -h                    # View all available commands
```

---

## 🌐 Web Interface Setup

### 1. Install Web Chat

```bash
# Install the Rasa Web Chat package
npm install rasa-webchat
```

### 2. Configuration

1. Clone the web interface repository:
   ```bash
   git clone https://github.com/botfront/rasa-webchat
   ```

2. Navigate to the downloaded folder and install dependencies:
   ```bash
   cd rasa-webchat
   npm install
   ```

### 3. Launch Services

```bash
# Start both servers
rasa run actions
rasa run -m models --enable-api --cors "*" --debug
```

---

## 📝 Important Notes

- Always validate your data before training:
  ```bash
  rasa data validate
  ```
- Ensure all three servers (Flask, Rasa, and actions) are running
- The application requires both PyCharm's server and Flask server to be running
- For development, use `--debug` flag with `rasa run` for detailed logs
- Check the [Rasa documentation](https://rasa.com/docs/) for advanced configuration
- Make sure your database is properly configured in `actions/db_config.py`

---