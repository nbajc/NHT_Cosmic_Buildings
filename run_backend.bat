@echo off
title NHT Cosmic Buildings Backend
echo Starting FastAPI Backend...
cd /d "%~dp0"
call .\venv\Scripts\activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
