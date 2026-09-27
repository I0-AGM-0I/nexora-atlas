@echo off
echo ========================================================
echo   NEXORA ATLAS - Starting Vite Frontend (Port 5173)
echo ========================================================
cd /d "%~dp0apps\web"
call npm.cmd run dev
