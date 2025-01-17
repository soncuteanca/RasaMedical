# Medical Assistant Chatbot

The **Medical Assistant Chatbot** is a Rasa-powered conversational AI designed to assist users with medical-related queries. It features real-time communication, a rich web interface, and customizable intents and actions for a smooth user experience.

---

## 📝 Description

This project is built with **Rasa Open Source** to:
- Recognize user intents and extract entities
- Handle dialogue management with custom rules and stories
- Provide a user-friendly web-based chat interface for interaction
- Respond with rich content like text and images

The chatbot uses Python-based custom actions and is integrated with a browser-based chat widget.

---

## 🛠️ Requirements

To run this project, you need:
- **Python**: Version 3.8 or later
- **Rasa Open Source**: Installed via pip
- **Node.js and npm**: (for webchat integration)
- **Browser**: Any modern browser to open the web chat interface

---

## 🚀 Features

- **Intent Recognition**: Handles `greet_intent`, `goodbye_intent`, and more
- **Custom Actions**: Uses Python scripts for dynamic responses
- **Rich Responses**: Displays text, buttons, and images
- **Interactive Web Interface**: Engages users with real-time communication
- **Scalable Design**: Easily extendable with new intents and actions

---

## 🔧 Installation

### 1. Set Up Environment

```bash
# Clone the repository
git clone https://github.com/soncuteanca/RasaMedical

# Navigate to project directory
cd Rasa1

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

### 3. Launch Services

```bash
# Start the action server
rasa run actions

# In a new terminal, start the Rasa server
rasa run -m models --enable-api --cors "*" --debug
```

### 4. Access Web Interface
- Open `html/index.html` in your preferred browser
- Start interacting with the chatbot through the web interface

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
- Ensure both servers (bot and actions) are running for the web interface
- Node.js must be installed before running npm commands
- For development, use `--debug` flag with `rasa run` for detailed logs
- Check the [Rasa documentation](https://rasa.com/docs/) for advanced configuration

---