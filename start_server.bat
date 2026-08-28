@echo off
echo.
echo  DocuVerify - Forensic Document Analysis System
echo  ================================================
echo  Starting backend server on http://localhost:8000
echo.
echo  API Docs:     http://localhost:8000/docs
echo  Health Check: http://localhost:8000/health
echo  Sample Files: http://localhost:8000/sample-images
echo.
echo  Open index.html in your browser after the server starts.
echo.

cd /d "%~dp0backend"
..\venv\Scripts\python.exe main.py
pause
