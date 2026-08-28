@echo off
title THE JUNCTION - Backend API
cd /d "%~dp0backend"
echo ==============================================
echo  Starting THE JUNCTION FastAPI Backend...
echo  API URL: http://127.0.0.1:8000
echo  Docs:    http://127.0.0.1:8000/docs
echo ==============================================
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
