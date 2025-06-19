import subprocess
import time
import os

# Set environment variables to silence SQLAlchemy warnings
os.environ['SQLALCHEMY_SILENCE_UBER_WARNING'] = '1'
os.environ['SQLALCHEMY_WARN_20'] = '0'
print("✅ SQLAlchemy warnings silenced")

# Create and run a temporary .bat file to kill ports
bat_script = """
@echo off
echo Killing any processes on ports 5000 and 5005...
for %%P in (5000 5005 5055) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%P') do (
        echo Killing PID %%a on port %%P
        taskkill /PID %%a /F >nul 2>&1
    )
)
"""

# Write to a temporary file
bat_file = "kill_ports.bat"
with open(bat_file, "w") as f:
    f.write(bat_script)

# Execute the batch file
subprocess.call([bat_file])

# Optionally remove the batch file afterward
os.remove(bat_file)

# Separator
print("=" * 60)
print("Starting Rasa Medical Chatbot")
print("=" * 60)

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Starting Flask Server...")
subprocess.Popen(['cmd', '/c', 'start', 'Medical - Flask', 'cmd', '/k', 'venv\\Scripts\\activate && python server.py'])
time.sleep(4)

print("Starting Rasa Actions...")
subprocess.Popen(['cmd', '/c', 'start', 'Medical - Actions', 'cmd', '/k', 'venv\\Scripts\\activate && rasa run actions'])
time.sleep(6)

print("Starting Rasa Server...")
subprocess.Popen(['cmd', '/c', 'start', 'Medical - Rasa', 'cmd', '/k', 'venv\\Scripts\\activate && rasa run -m models --enable-api --cors * --debug'])

print("=" * 60)
print("All services started!")
print("Flask Server: http://localhost:5000")
print("Rasa Server: http://localhost:5005")
print("=" * 60)
