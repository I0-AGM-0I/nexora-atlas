@echo off
echo ========================================================
echo   NEXORA ATLAS - Seeding Deterministic Demo Data
echo ========================================================
cd /d "%~dp0"
python scripts\seed_demo.py
