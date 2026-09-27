@echo off
echo ========================================================
echo   NEXORA ATLAS - Launching Full Command Center Stack
echo ========================================================
echo Starting Backend API on http://localhost:8000 ...
start "Nexora Atlas - API" cmd /k "%~dp0run-api.bat"

echo Starting Frontend on http://localhost:5173 ...
start "Nexora Atlas - Web" cmd /k "%~dp0run-web.bat"

echo.
echo Both services launched in separate windows.
echo Frontend will automatically open http://localhost:5173 once ready.
