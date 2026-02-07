@echo off
REM Activate virtual environment and start the API
call .venv\Scripts\activate
uvicorn app.main:app --reload --port 8000