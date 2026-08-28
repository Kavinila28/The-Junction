@echo off
title THE JUNCTION - Full Stack Launcher
echo ==============================================
echo  Launching THE JUNCTION (Backend + Frontend)...
echo ==============================================
start "THE JUNCTION Backend" cmd /c "%~dp0start-backend.bat"
timeout /t 3 /nobreak >nul
start "THE JUNCTION Frontend" cmd /c "%~dp0start-frontend.bat"
echo.
echo Both servers are starting up!
echo Frontend Dashboard: http://localhost:5173
echo Backend API Docs:   http://127.0.0.1:8000/docs
echo.
timeout /t 5
