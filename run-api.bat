@echo off
echo ========================================================
echo   NEXORA ATLAS - Starting FastAPI Backend (Port 8000)
echo ========================================================
cd /d "%~dp0apps\api"
python -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1
