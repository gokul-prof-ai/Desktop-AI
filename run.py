import sys
import os
import subprocess
import time
import ctypes
from pathlib import Path

# --- CRITICAL FIX FOR EXE BUNDLING ---
if getattr(sys, 'frozen', False):
    application_path = Path(sys._MEIPASS)
else:
    application_path = Path(__file__).parent.resolve()

# Add the 'src' folder to the Python path
src_path = str(application_path / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def start_and_wait_for_ollama():
    """Start Ollama and wait for it to be ready before proceeding."""
    import requests
    
    ollama_url = "http://localhost:11434"
    
    # 1. Check if already running
    try:
        if requests.get(ollama_url, timeout=2).status_code == 200:
            print("✅ Ollama is already running.")
            return None
    except:
        pass

    print("🚀 Starting Ollama server...")
    
    # 2. Start Ollama silently
    try:
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
    except Exception as e:
        print(f" Failed to start Ollama: {e}")
        return None

    # 3. Wait for Ollama to wake up (up to 15 seconds)
    print("⏳ Waiting for Ollama to initialize...")
    for i in range(15):
        time.sleep(1)
        try:
            if requests.get(ollama_url, timeout=2).status_code == 200:
                print("✅ Ollama is ready! Launching app...")
                return process
        except:
            pass
            
    print("️ Ollama took too long to start. Launching app anyway...")
    return process

def stop_ollama(process):
    """Stop the Ollama server if we started it."""
    if process and process.poll() is None:
        print("🛑 Shutting down Ollama server...")
        process.terminate()
        if os.name == 'nt':
            subprocess.run(["taskkill", "/F", "/PID", str(process.pid)], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Import the GUI
try:
    from PySide6.QtWidgets import QApplication
    from gui.main_window import MainWindow
except Exception as e:
    ctypes.windll.user32.MessageBoxW(0, f"Failed to load app:\n{e}", "Startup Error", 0x10)
    sys.exit(1)

def main():
    # Start Ollama and WAIT for it to be ready
    ollama_proc = start_and_wait_for_ollama()
    
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    finally:
        stop_ollama(ollama_proc)

if __name__ == "__main__":
    main()