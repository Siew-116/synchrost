@echo off
set PYTHONPATH=%~dp0backend
cd /d "%~dp0backend"
"C:\Users\ASUS\.workbuddy-ai\binaries\python\versions\3.13.12\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
