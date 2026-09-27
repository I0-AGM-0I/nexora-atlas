Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  NEXORA ATLAS - Launching Full Command Center Stack    " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $rootDir) { $rootDir = (Get-Location).Path }

Write-Host "Starting Backend API on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\apps\api'; python -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1"

Write-Host "Starting Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\apps\web'; npm.cmd run dev"

Write-Host ""
Write-Host "Both services launched in separate windows." -ForegroundColor Yellow
Write-Host "The browser will automatically open to http://localhost:5173 once Vite is ready." -ForegroundColor Green
