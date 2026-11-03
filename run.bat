@echo off
setlocal
set "PROJECT_DIR=%~dp0"

if not exist "%PROJECT_DIR%venv\Scripts\python.exe" (
    echo Python virtual environment not found.
    echo Create it and install dependencies with:
    echo   python -m venv venv
    echo   .\venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist "%PROJECT_DIR%frontend\node_modules" (
    echo Frontend dependencies not found. Run:
    echo   cd frontend
    echo   npm ci
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo npm was not found. Install Node.js, then try again.
    pause
    exit /b 1
)

if not exist "%PROJECT_DIR%.env" (
    echo Warning: project .env file is missing. Add GROQ_API_KEY and GROQ_MODEL before chatting.
)

start "Document Reader API" cmd /k "cd /d ""%PROJECT_DIR%"" && set ""PYTHONPATH=%PROJECT_DIR%src"" && ""%PROJECT_DIR%venv\Scripts\python.exe"" -m uvicorn api:app --reload"
start "Document Reader Frontend" cmd /k "cd /d ""%PROJECT_DIR%frontend"" && npm run dev"
