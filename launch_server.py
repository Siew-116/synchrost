"""Detached server launcher for StudyBiz AI.

Spawns uvicorn as a fully detached child process using
CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS on Windows,
so the server survives even after this script exits.
"""
import os
import sys
import subprocess
import time
import urllib.request

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
PYTHON = r"C:\Users\ASUS\.workbuddy-ai\binaries\python\versions\3.13.12\python.exe"
HOST = "127.0.0.1"
PORT = 8000

def is_server_up():
    try:
        urllib.request.urlopen(f"http://{HOST}:{PORT}/api/health", timeout=2)
        return True
    except Exception:
        return False

def main():
    if is_server_up():
        print(f"Server already running at http://{HOST}:{PORT}")
        return

    env = os.environ.copy()
    env["PYTHONPATH"] = BACKEND_DIR

    # CREATE_NEW_PROCESS_GROUP (0x00000200) | DETACHED_PROCESS (0x00000008)
    DETACHED_FLAGS = 0x00000008 | 0x00000200

    log_file = os.path.join(BACKEND_DIR, "server.log")
    log = open(log_file, "w")

    proc = subprocess.Popen(
        [
            PYTHON,
            "-m", "uvicorn",
            "app.main:app",
            "--host", HOST,
            "--port", str(PORT),
        ],
        cwd=BACKEND_DIR,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=DETACHED_FLAGS,
        close_fds=True,
    )

    print(f"Launched server (PID {proc.pid}) - waiting for startup...")

    # Wait up to 15 seconds for server to come up
    for i in range(30):
        time.sleep(0.5)
        if is_server_up():
            print(f"Server is up at http://{HOST}:{PORT}")
            return

    print(f"Server did not start within 15s. Check {log_file}")
    # Try to show log contents
    try:
        log.flush()
        with open(log_file) as f:
            print(f.read()[-2000:])
    except Exception:
        pass

if __name__ == "__main__":
    main()
