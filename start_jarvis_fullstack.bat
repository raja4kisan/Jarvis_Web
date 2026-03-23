@echo off
echo ========================================
echo Starting Jarvis AI - Full Stack
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo.
echo [1/2] Starting Backend API...
echo ========================================
start "Jarvis API" cmd /k "python api.py"

timeout /t 3 /nobreak >nul

echo.
echo [2/2] Opening Web UI...
echo ========================================
start "" "web-ui.html"

echo.
echo ========================================
echo ✅ Jarvis AI is now running!
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Web UI: Opened in your browser
echo.
echo To stop: Close the API terminal window
echo.
pause
