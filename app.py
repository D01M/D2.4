"""
OpenSeismo Lite Desktop App
Launches the Flask server and opens the UI in a browser
"""

import subprocess
import webbrowser
import time
import sys
import os
import socket
from pathlib import Path

# Lock file to prevent multiple instances from launching
LOCK_FILE = None

def get_lock_file():
    """Get the lock file path"""
    temp_dir = Path(os.environ.get('TEMP', '/tmp'))
    return temp_dir / 'OpenSeismoLite.lock'

def acquire_lock():
    """Try to acquire a lock to prevent multiple launches"""
    global LOCK_FILE
    LOCK_FILE = get_lock_file()
    
    # Check if lock file exists and if process is still running
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, 'r') as f:
                old_pid = f.read().strip()
                # If the lock file is from an old process, remove it
                # On Windows, we can't reliably check if PID is running, so we'll use a timeout
                try:
                    import psutil
                    if not psutil.pid_exists(int(old_pid)):
                        LOCK_FILE.unlink()
                except:
                    # psutil not available, check file age instead
                    import time as time_module
                    file_age = time_module.time() - LOCK_FILE.stat().st_mtime
                    if file_age > 10:  # If lock is older than 10 seconds, consider it stale
                        LOCK_FILE.unlink()
        except:
            pass
    
    # Try to create lock file
    if not LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, 'w') as f:
                f.write(str(os.getpid()))
            return True
        except:
            return False
    
    return False

def is_port_in_use(port, timeout=1):
    """Check if a port is already in use with timeout"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except:
        return False

def main():
    """Start Flask server and open browser"""
    
    # Get the directory where this script is located
    app_dir = Path(__file__).parent
    
    # Try to acquire lock (prevents multiple launches)
    if not acquire_lock():
        print("OpenSeismo Lite is already running.")
        print("Connect to http://localhost:5000 in your browser.")
        return
    
    try:
        # Final check if server is already running
        if is_port_in_use(5000):
            print("OpenSeismo Lite is already running on http://localhost:5000")
            return
        
        # Start Flask server as a subprocess
        print("Starting OpenSeismo Lite...")
        print("Launching server on http://localhost:5000")
        
        # Suppress output from Flask
        if sys.platform == 'win32':
            # Windows
            server_process = subprocess.Popen(
                [sys.executable, str(app_dir / 'server.py')],
                cwd=str(app_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # macOS/Linux
            server_process = subprocess.Popen(
                [sys.executable, str(app_dir / 'server.py')],
                cwd=str(app_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # Wait for server to start and become responsive
        print("Waiting for server to start...")
        server_ready = False
        for attempt in range(30):  # Try for up to 15 seconds
            if is_port_in_use(5000):
                server_ready = True
                break
            time.sleep(0.5)
        
        if not server_ready:
            print("Warning: Server may not have started properly")
            print("Please visit http://localhost:5000 manually")
        else:
            # Give it a bit more time to fully initialize
            time.sleep(1)
            
            # Open browser ONLY ONCE
            try:
                print("Opening browser...")
                webbrowser.open('http://localhost:5000')
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
                print("Please visit http://localhost:5000 manually in your browser")
        
        # Keep the server running
        try:
            print("OpenSeismo Lite is running. Close this window to stop.")
            server_process.wait()
        except KeyboardInterrupt:
            print("\nShutting down OpenSeismo Lite...")
            server_process.terminate()
            server_process.wait()
            print("Stopped.")
    
    finally:
        # Clean up lock file
        if LOCK_FILE and LOCK_FILE.exists():
            try:
                LOCK_FILE.unlink()
            except:
                pass

if __name__ == "__main__":
    main()
