@echo off
title THE JUNCTION - Frontend Dashboard
cd /d "%~dp0frontend"
echo ==============================================
echo  Starting THE JUNCTION React Frontend...
echo  Dashboard: http://localhost:5173
echo ==============================================
call npm.cmd run dev
pause
