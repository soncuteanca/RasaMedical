@echo off
title Starting Rasa Medical Chatbot

echo ============================================================
echo Starting Rasa Medical Chatbot
echo ============================================================

echo Starting Flask Server...
start "Medical - Flask" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python server.py"
timeout /t 4 >nul

echo Starting Rasa Actions...
start "Medical - Actions" cmd /k "cd /d %~dp0 && venv\Scripts\activate && rasa run actions"
timeout /t 6 >nul

echo Starting Rasa Server...
start "Medical - Rasa" cmd /k "cd /d %~dp0 && venv\Scripts\activate && rasa run -m models --enable-api --cors * --debug"
timeout /t 3 >nul

echo ============================================================
echo All services started in separate windows!
echo ============================================================
echo Flask Server: http://localhost:5000
echo Rasa Server: http://localhost:5005
echo PyCharm: http://localhost:63342/RasaMedical/html/chat_page.html
echo ============================================================
echo Close each window to stop that service
echo ============================================================
pause 