import subprocess
import time
import os

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