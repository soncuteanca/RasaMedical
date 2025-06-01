import subprocess
import sys
import time
import signal
import os
from threading import Thread


class RasaMedicalLauncher:
    def __init__(self):
        self.processes = []
        self.running = True

    def start_flask_server(self):
        """Start Flask server for user management"""
        print("Starting Flask Server on port 5000...")
        try:
            process = subprocess.Popen([
                sys.executable, "server.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.processes.append(("Flask Server", process))
            return process
        except Exception as e:
            print(f"x Error starting Flask server: {e}")
            return None

    def start_rasa_actions(self):
        """Start Rasa Action Server"""
        print("Starting Rasa Action Server...")
        try:
            process = subprocess.Popen([
                "rasa", "run", "actions"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.processes.append(("Rasa Actions", process))
            return process
        except Exception as e:
            print(f"Error starting Rasa actions: {e}")
            return None

    def start_rasa_server(self):
        """Start Rasa Server"""
        print("Starting Rasa Server on port 5005...")
        try:
            process = subprocess.Popen([
                "rasa", "run", "-m", "models", "--enable-api", "--cors", "*", "--debug"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.processes.append(("Rasa Server", process))
            return process
        except Exception as e:
            print(f"Error starting Rasa server: {e}")
            return None

    def monitor_process(self, name, process):
        """Monitor a process and print its output"""
        if process is None:
            return

        while self.running and process.poll() is None:
            output = process.stdout.readline()
            if output:
                print(f"[{name}] {output.strip()}")

            error = process.stderr.readline()
            if error:
                print(f"[{name} ERROR] {error.strip()}")

    def start_all_services(self):
        """Start all services"""
        print("=" * 60)
        print("🏥 STARTING RASA MEDICAL CHATBOT")
        print("=" * 60)

        # Start Flask server
        flask_process = self.start_flask_server()
        if flask_process:
            Thread(target=self.monitor_process, args=("Flask", flask_process), daemon=True).start()
            time.sleep(3)  # Wait for Flask to start

        # Start Rasa Action server
        actions_process = self.start_rasa_actions()
        if actions_process:
            Thread(target=self.monitor_process, args=("Actions", actions_process), daemon=True).start()
            time.sleep(5)  # Wait for actions to start

        # Start Rasa server
        rasa_process = self.start_rasa_server()
        if rasa_process:
            Thread(target=self.monitor_process, args=("Rasa", rasa_process), daemon=True).start()
            time.sleep(3)  # Wait for Rasa to start

        print("\n" + "=" * 60)
        print("   ALL SERVICES STARTED SUCCESSFULLY!")
        print("=" * 60)
        print("   Services running on:")
        print("   • Flask Server: http://localhost:5000")
        print("   • Rasa Actions: http://localhost:5055")
        print("   • Rasa Server: http://localhost:5005")
        print("   • PyCharm Server: http://localhost:63342")
        print("\n  Access your app:")
        print("   • Open html/home_page.html in PyCharm")
        print("   • Or visit: http://localhost:63342/RasaMedical/html/home_page.html")
        print("\n  Press Ctrl+C to stop all services")
        print("=" * 60)

        # Keep the script running
        try:
            while True:
                time.sleep(1)
                # Check if any process has died
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"⚠️  {name} has stopped unexpectedly!")
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Gracefully shutdown all processes"""
        print("\n  Shutting down all services...")
        self.running = False

        for name, process in self.processes:
            if process.poll() is None:  # Process is still running
                print(f"   Stopping {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   Force killing {name}...")
                    process.kill()
                except Exception as e:
                    print(f"   Error stopping {name}: {e}")

        print("  All services stopped successfully!")
        print("  Goodbye!")


def main():
    launcher = RasaMedicalLauncher()

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        launcher.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Check if model exists
    if not os.path.exists("models"):
        print("  No trained model found!")
        print("  Please run 'rasa train' first to create a model.")
        sys.exit(1)

    launcher.start_all_services()


if __name__ == "__main__":
    main()