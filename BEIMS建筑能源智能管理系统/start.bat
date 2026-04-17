@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"
set "WORKSPACE_DIR=%SCRIPT_DIR%.."
set "ASSISTANT_ENTRY=%WORKSPACE_DIR%\api_server.py"
set "FRONTEND_LOG=%FRONTEND_DIR%\frontend_start.log"
set "BACKEND_ENV=%BACKEND_DIR%\.env"
set "BACKEND_ENV_EXAMPLE=%BACKEND_DIR%\.env.example"
set "VENV_PY=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
set "PYTHON_EXE=python"
set "START_ASSISTANT=true"

if exist "%VENV_PY%" (
    set "PYTHON_EXE=%VENV_PY%"
)

set "FRONTEND_MODE=dev"
if not exist "%FRONTEND_DIR%\src\main.js" (
    set "FRONTEND_MODE=preview"
)

echo ========================================
echo BEIMS - Building Energy Intelligent Management System
echo ========================================
echo.
echo Main startup entry: %~f0
echo.
echo Checking environment...
echo.

REM Check Python
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found
    echo Please install Node.js 16+
    pause
    exit /b 1
)

echo [OK] Python found
echo [OK] Node.js found
echo.

REM Ensure backend/frontend directories exist
if not exist "%BACKEND_DIR%\requirements.txt" (
    echo [ERROR] Backend directory is invalid: %BACKEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
    echo [ERROR] Frontend directory is invalid: %FRONTEND_DIR%
    pause
    exit /b 1
)

REM Ensure backend .env exists
if not exist "%BACKEND_ENV%" (
    if exist "%BACKEND_ENV_EXAMPLE%" (
        copy "%BACKEND_ENV_EXAMPLE%" "%BACKEND_ENV%" >nul
        echo [OK] backend/.env created from .env.example
    ) else (
        echo [WARN] backend/.env.example not found, continue with defaults
    )
)

REM Check if backend dependencies are installed
echo Checking backend dependencies...
pushd "%BACKEND_DIR%"
"%PYTHON_EXE%" -c "import fastapi, sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo Installing backend dependencies...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
) else (
    echo [OK] Backend dependencies already installed
)
popd

REM Check if frontend dependencies are installed
echo Checking frontend dependencies...
pushd "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
) else (
    echo [OK] Frontend dependencies already installed
)
popd

echo.
echo ========================================
echo Starting Backend Server...
echo ========================================
echo.

start "BEIMS Backend" /D "%BACKEND_DIR%" "%PYTHON_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8001

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Starting Assistant Service (8082)...
echo ========================================
echo.

if /I "%START_ASSISTANT%"=="true" (
    if exist "%ASSISTANT_ENTRY%" (
        start "BEIMS Assistant" /D "%WORKSPACE_DIR%" "%PYTHON_EXE%" "%ASSISTANT_ENTRY%"
    ) else (
        echo [WARN] Assistant entry not found: %ASSISTANT_ENTRY%
    )
) else (
    echo [INFO] Assistant autostart disabled
)

timeout /t 4 /nobreak >nul

echo.
echo ========================================
echo Starting Frontend Server...
echo ========================================
echo.

if exist "%FRONTEND_LOG%" del /f /q "%FRONTEND_LOG%" >nul 2>&1

if /I "%FRONTEND_MODE%"=="preview" (
    echo [INFO] Frontend source not found, using preview mode from dist
    start "BEIMS Frontend" /D "%FRONTEND_DIR%" cmd /c "npx vite preview --host 0.0.0.0 --port 3000 > ""%FRONTEND_LOG%"" 2>&1"
) else (
    start "BEIMS Frontend" /D "%FRONTEND_DIR%" cmd /c "npm run dev > ""%FRONTEND_LOG%"" 2>&1"
)

timeout /t 4 /nobreak >nul

set "BACKEND_OK="
set "FRONTEND_OK="
set "ASSISTANT_OK="
for /f "delims=" %%A in ('netstat -ano ^| find ":8001" ^| find "LISTENING"') do set "BACKEND_OK=1"
for /f "delims=" %%A in ('netstat -ano ^| find ":3000" ^| find "LISTENING"') do set "FRONTEND_OK=1"
for /f "delims=" %%A in ('netstat -ano ^| find ":8082" ^| find "LISTENING"') do set "ASSISTANT_OK=1"

echo.
echo Runtime check:
if defined BACKEND_OK (
    echo [OK] Backend is listening on 8001
) else (
    echo [WARN] Backend is not listening on 8001 yet
)
if defined FRONTEND_OK (
    echo [OK] Frontend is listening on 3000
) else (
    echo [WARN] Frontend is not listening on 3000 yet
    echo [INFO] Frontend log: %FRONTEND_LOG%
)
if defined ASSISTANT_OK (
    echo [OK] Assistant is listening on 8082
) else (
    echo [WARN] Assistant is not listening on 8082 yet ^(model may still be loading, retry in 30-60s^)
)

echo.
echo ========================================
echo BEIMS Started Successfully!
echo ========================================
echo.
echo Backend:  http://localhost:8001
echo API Docs: http://localhost:8001/docs
echo Frontend: http://localhost:3000
echo Assistant: http://localhost:8082
echo.
echo Startup script finished. Service windows keep running.
echo.
exit /b 0
