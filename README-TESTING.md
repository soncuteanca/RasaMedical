# 🧪 RasaMedical Testing Guide

This document explains how to test RasaMedical chatbot project safely and effectively.

## 📋 Overview

The RasaMedical project includes a comprehensive but minimal testing suite designed to:
- ✅ Validate core business logic
- ⚡ Provide fast feedback during development
- 📊 Measure NLU accuracy when needed
- 🛡️ Use mocks to avoid database dependencies

## 🗂️ Test Structure

```
RasaMedical/
├── tests/
│   ├── test_medical_actions.py     # Doctor listing & specialty search tests
│   ├── test_appointment_actions.py # Appointment booking logic tests
│   ├── test_performance.py         # Performance benchmark tests
│   └── test_nlu_accuracy.py        # NLU accuracy validation tests
└── run_tests.py                    # Smart test runner script
```

## 🚀 Quick Start

### Daily Development Testing (Recommended)
```bash
python run_tests.py
```
- **Speed**: ⚡ Fast (under 1 second)
- **Tests**: Unit tests for business logic
- **Purpose**: Quick validation during development
- **Safe**: Uses mocks, won't interfere with Rasa

### NLU Accuracy Check
```bash
python run_tests.py --nlu
```
- **Speed**: 🐌 Slow (several minutes - loads BERT model)
- **Tests**: Comprehensive NLU accuracy testing
- **Purpose**: Validate intent recognition performance
- **Note**: Requires trained Rasa model in `/models/` directory

### Full Test Suite
```bash
python run_tests.py --all
```
- **Speed**: 🐌 Slow (several minutes)
- **Tests**: All unit tests + NLU accuracy tests
- **Purpose**: Complete validation before deployment

### Help & Options
```bash
python run_tests.py --help
```

## 📊 Test Categories

### 1. Unit Tests (Fast)

#### Medical Actions Tests (`test_medical_actions.py`)
- Tests doctor listing functionality
- Tests `ActionListDoctors` with various scenarios
- Tests `ActionListDoctorsBySpecialty` for specialty searches
- Uses mocked database responses

#### Appointment Tests (`test_appointment_actions.py`)
- Tests appointment booking logic
- Tests `ActionBookAppointment` validation
- Tests appointment conflict detection
- Uses mocked database calls

#### Performance Tests (`test_performance.py`)
- Tests ensuring actions complete within time limits
- Validates response times under reasonable thresholds
- Helps detect performance regressions

### 2. NLU Accuracy Tests (Slow)

#### Comprehensive NLU Testing (`test_nlu_accuracy.py`)
- Tests realistic medical scenarios
- Validates intent recognition accuracy
- Tests various medical conversation patterns
- **Notable**: Appropriately classifies serious symptoms as emergencies

### 3. Manual Testing

#### Interactive Shell Testing
```bash
# Start interactive testing session
rasa shell
```
- Test conversations in real-time
- Validate intent recognition manually
- Debug conversation flows
- Test edge cases interactively
- Example conversation:
  ```
  Your input -> I have chest pain
  Bot -> I understand you're experiencing chest pain. This could be serious...
  ```

#### Web Chat Testing

**Option 1: Use the automated starter (Recommended)**
```bash
# Start all servers automatically
python start_medical.py
```
This will start:
- Flask server (port 5000) - User management
- Rasa actions server (port 5055) - Custom actions  
- Rasa server (port 5005) - Main chat functionality

**Option 2: Manual startup**
```bash
# Terminal 1: Start Flask server
python server.py

# Terminal 2: Start custom actions server
rasa run actions

# Terminal 3: Start main Rasa server
rasa run --enable-api --cors "*"
```

**Testing the Web Interface:**
```bash
# Open web interface in browser
# Navigate to: html/chat_page.html
# Or: html/home_page.html (for user management)
```

**What to Test:**
- Test complete user experience
- Validate web interface functionality
- Test real-time messaging
- Verify UI/UX behavior
- Test user creation and management
- Test on different browsers and devices

#### Manual Test Scenarios
**Doctor Search Testing:**
- "Show me all doctors"
- "I need a cardiologist"
- "Find orthopedic specialists"

**Appointment Testing:**
- "I want to book an appointment"
- "Schedule me with Dr. Smith"
- "Cancel my appointment"

**Symptom Reporting:**
- "I have chest pain" (should trigger emergency)
- "My back hurts" (general symptom)
- "I feel dizzy and nauseous"

## 🛠️ Setup Requirements

### Prerequisites
- Python 3.10+
- Virtual environment activated
- Trained Rasa model (for NLU tests)

### Dependencies
The test runner automatically installs `pytest` if not present. No additional setup required!

## 🔧 Troubleshooting

### Common Issues

#### "Model not found" error
```bash
# Ensure you have a trained model
ls models/
# Should show: *.tar.gz files
```

#### Tests running slowly
- Use `python run_tests.py` (unit tests only) for daily development
- Reserve `--nlu` and `--all` for periodic validation

#### Import errors
```bash
# Ensure you're in the project root and virtual environment is activated
cd /path/to/RasaMedical
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

## 📈 Understanding Test Results

### Unit Test Interpretation
- **All tests passing**: Your core business logic is working correctly
- **Failures**: Check the specific test that failed - likely indicates a logic issue

### NLU Accuracy Interpretation
- **90%+ accuracy**: Excellent performance
- **80-89% accuracy**: Good performance
- **70-79% accuracy**: Moderate - consider more training data
- **<70% accuracy**: Poor - needs significant improvement

## 🚨 Safety Notes

### What These Tests DON'T Do
- ❌ Don't connect to your production database
- ❌ Don't interfere with your running Rasa server
- ❌ Don't modify your training data or models
- ❌ Don't require stopping your chatbot

### What These Tests DO
- ✅ Use mocked database responses
- ✅ Test business logic in isolation
- ✅ Validate NLU model performance
- ✅ Provide fast feedback loops

## 📅 Recommended Testing Schedule

| Frequency | Command | Purpose |
|-----------|---------|---------|
| Every commit | `python run_tests.py` | Catch regressions early |
| Daily development | `rasa shell` | Interactive testing and debugging |
| Weekly | `python run_tests.py --nlu` | Monitor NLU performance |
| Weekly | Web chat testing | Validate user experience |
| Before deployment | `python run_tests.py --all` | Full validation |
| After model retraining | `python run_tests.py --nlu` | Validate improvements |
| After model retraining | Manual test scenarios | Verify conversation quality |

## 🎉 Success Metrics

Your testing setup is working well when you see:
- ✅ Unit tests complete quickly
- ✅ All unit tests passing consistently
- ✅ NLU accuracy at acceptable levels
- ✅ No interference with your production chatbot

---

## 💡 Pro Tips

1. **Daily Development**: Always run `python run_tests.py` before committing code
2. **Performance Monitoring**: Watch for NLU accuracy trends over time
3. **Medical Safety**: Trust the model when it classifies symptoms as emergencies
4. **Fast Feedback**: Use unit tests for rapid iteration, NLU tests for validation

Happy testing! 🚀 