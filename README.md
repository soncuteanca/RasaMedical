# 🏥 RasaMedical - Medical Assistant Chatbot

A sophisticated **Rasa-powered medical chatbot** designed to assist users with healthcare-related queries, doctor searches, appointment booking, and symptom reporting. Features intelligent NLU with BERT, comprehensive testing, and a modern web interface.

---

## 📝 Description

**RasaMedical** is built with **Rasa Open Source** and provides:
- **Smart Medical NLU**: BERT-based intent recognition with 81%+ accuracy
- **Doctor Management**: Search doctors by specialty, list available physicians  
- **Appointment System**: Book, manage, and track medical appointments
- **Symptom Analysis**: Report symptoms with intelligent emergency detection
- **Database Integration**: Full SQLAlchemy integration with MySQL
- **Web Interface**: Modern chat interface with real-time communication
- **Safety-First Design**: Prioritizes patient safety in symptom classification

The system uses advanced Python custom actions and includes comprehensive testing for reliability.

---

## 🛠️ Requirements

### System Requirements
- **Python**: 3.10+ 
- **Database**: MySQL (via PyMySQL)
- **Memory**: 4GB+ RAM (for BERT model)
- **Storage**: 2GB+ free space

### Key Dependencies
- **Rasa**: 3.6.4 (conversational AI framework)
- **TensorFlow**: 2.12.0 (for BERT NLU pipeline)
- **SQLAlchemy**: <2.0 (database ORM)
- **Flask**: Web server for user management
- **PyMySQL**: 1.1.0 (MySQL database connectivity)

---

## 🚀 Key Features

### 🧠 Intelligent NLU
- **BERT-based Processing**: Advanced natural language understanding
- **Medical Intent Recognition**: Specialized for healthcare conversations
- **Emergency Detection**: Automatically identifies urgent medical situations
- **High Accuracy**: 81%+ intent recognition accuracy

### 👨‍⚕️ Medical Functionality  
- **Doctor Search**: Find physicians by specialty (cardiology, orthopedics, etc.)
- **Appointment Booking**: Schedule and manage medical appointments
- **Symptom Reporting**: Report symptoms with intelligent triage
- **Medical Records**: Access patient information and history

### 🛠️ Technical Features
- **Database Integration**: SQLAlchemy with MySQL support via PyMySQL
- **Custom Actions**: Python-based dynamic response system
- **Web Interface**: Modern HTML/JavaScript chat widget
- **Comprehensive Testing**: Unit tests + NLU accuracy validation
- **Safety-First**: Medical safety prioritized in all classifications

---

## 🔧 Installation

### 1. Set Up Environment

```bash
# Clone the repository (or download the project)
# git clone <your-repository-url>

# Navigate to project directory
cd RasaMedical

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Train the Model

```bash
# Train the model
rasa train
```

### 3. Database Setup

Configure your database connection in `actions/db_config.py`:
```python
# Example configuration
DATABASE_URL = "mysql+pymysql://username:password@localhost/rasamedical"
```

### 4. Running the Application

**Option 1: Automated Startup (Recommended)**
```bash
# Start all servers automatically
python start_medical.py
```
This script will:
- Kill any existing processes on ports 5000, 5005, 5055
- Start Flask server (user management)
- Start Rasa actions server (custom actions)
- Start Rasa server (main chat functionality)
- Open separate terminal windows for each service

**Option 2: Manual Startup**
```bash
# Terminal 1: Start Flask backend
python server.py

# Terminal 2: Start custom actions server
rasa run actions

# Terminal 3: Start main Rasa server  
rasa run --enable-api --cors "*"
```

### 5. Access the Application

- **Chat Interface**: Open `html/chat_page.html` in your browser
- **User Management**: Navigate to `html/home_page.html` 
- **API Endpoint**: http://localhost:5005 (Rasa server)
- **Backend API**: http://localhost:5000 (Flask server)

The application architecture:
- **Port 5005**: Rasa server (main chat functionality)
- **Port 5055**: Rasa actions server (custom actions)  
- **Port 5000**: Flask server (user management - optional)

---

## 🧪 Testing

RasaMedical includes comprehensive testing for reliability and accuracy:

### Quick Testing (Recommended)
```bash
# Run fast unit tests (0.24 seconds)
python run_tests.py
```

### NLU Accuracy Testing
```bash
# Run comprehensive NLU accuracy tests (~12 minutes)
python run_tests.py --nlu
```

### Full Test Suite
```bash
# Run all tests (unit + NLU)
python run_tests.py --all
```

**Test Coverage:**
- ✅ 15 unit tests for business logic
- ✅ NLU accuracy validation
- ✅ Performance benchmarks
- ✅ Medical action testing with mocked database

For detailed testing documentation, see [README-TESTING.md](README-TESTING.md).

---

## 🛠️ Development Commands

### Model Training
```bash
rasa train                  # Train complete model
rasa train nlu             # Train only NLU
rasa train core            # Train only dialogue management
```

### Testing & Validation
```bash
rasa shell                 # Interactive testing
rasa data validate         # Validate training data
rasa test nlu             # Generate NLU evaluation report
```

### Development
```bash
rasa run --debug           # Run with detailed logging
rasa interactive           # Interactive learning mode
rasa visualize             # Visualize training stories
```

---

## 🏗️ Architecture

### Core Components
- **NLU Pipeline**: BERT-based intent classification and entity extraction
- **Dialogue Management**: Rule-based and ML-based conversation flow
- **Custom Actions**: Python actions for database operations and business logic
- **Web Interface**: HTML/JavaScript chat widget with real-time messaging

### Database Schema
- **Users**: Patient information and authentication
- **Doctors**: Physician profiles and specialties  
- **Appointments**: Booking system with conflict detection
- **Medical Records**: Patient history and symptoms

### File Structure
```
RasaMedical/
├── actions/              # Custom Python actions
├── data/                 # Training data (NLU, stories, rules)
├── models/               # Trained Rasa models
├── tests/                # Comprehensive test suite
├── html/                 # Web interface files
├── database/             # Database scripts and migrations
├── venv/                 # Python virtual environment
├── config.yml            # Rasa configuration
├── domain.yml            # Domain definition
├── credentials.yml       # Channel credentials
├── endpoints.yml         # Action server endpoints
├── server.py             # Flask backend server
├── run_tests.py          # Test runner script
├── requirements.txt      # Python dependencies
├── README.md             # Main documentation
└── README-TESTING.md     # Testing documentation
```

---

## 📚 Documentation

- **Main Documentation**: This README
- **Testing Guide**: [README-TESTING.md](README-TESTING.md)
- **Rasa Documentation**: [rasa.com/docs](https://rasa.com/docs/)
- **Configuration**: See `config.yml` and `domain.yml`

---

## ⚠️ Important Notes

### Medical Safety
- The system prioritizes patient safety in symptom classification
- Serious symptoms (chest pain, breathing issues) are automatically flagged as emergencies
- Always consult healthcare professionals for medical decisions

### Technical Considerations  
- **Memory Usage**: BERT model requires 4GB+ RAM
- **Startup Time**: Initial model loading takes 30-60 seconds
- **Database**: Ensure proper database configuration before running
- **Testing**: Run tests regularly to maintain system reliability

### Production Deployment
- Configure proper database credentials
- Set up SSL/TLS for secure communication
- Monitor system performance and accuracy
- Regular model retraining with new data

---