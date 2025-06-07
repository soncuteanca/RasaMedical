@echo off
title Starting Rasa Medical Chatbot

echo ============================================================
echo Starting Rasa Medical Chatbot
echo ============================================================

:: Start Flask Server
echo Starting Flask Server...
start "Flask Server" cmd /k "call venv\Scripts\activate.bat && python server.py"
timeout /t 4 >nul

:: Start Rasa Actions
echo Starting Rasa Actions...
start "Rasa Actions" cmd /k "call venv\Scripts\activate.bat && rasa run actions"
timeout /t 6 >nul

:: Start Rasa Server
echo Starting Rasa Server...
start "Rasa Server" cmd /k "call venv\Scripts\activate.bat && rasa run -m models --enable-api --cors * --debug"
timeout /t 3 >nul

echo ============================================================
echo All services started in separate windows!
echo Flask Server: http://localhost:5000
echo Rasa Server: http://localhost:5005
echo Chat Page: http://localhost:63342/RasaMedical/html/chat_page.html
echo ============================================================
echo Close each window to stop that service
echo ============================================================
pause
