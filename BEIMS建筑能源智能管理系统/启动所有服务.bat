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
echo BEIMS - 启动所有服务
echo ========================================
echo.
echo 主启动入口: %~f0
echo.
echo 正在检查环境...
echo.

REM 检查 Python
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python
    echo 请安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Node.js
    echo 请安装 Node.js 16+
    pause
    exit /b 1
)

echo [OK] Python 已找到
echo [OK] Node.js 已找到
echo.

REM 确保 backend/frontend 目录存在
if not exist "%BACKEND_DIR%\requirements.txt" (
    echo [错误] 后端目录无效: %BACKEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
    echo [错误] 前端目录无效: %FRONTEND_DIR%
    pause
    exit /b 1
)

REM 确保 backend .env 存在
if not exist "%BACKEND_ENV%" (
    if exist "%BACKEND_ENV_EXAMPLE%" (
        copy "%BACKEND_ENV_EXAMPLE%" "%BACKEND_ENV%" >nul
        echo [OK] 已从 .env.example 创建 backend/.env
    ) else (
        echo [警告] 未找到 backend/.env.example，使用默认配置
    )
)

REM 检查后端依赖是否已安装
echo 检查后端依赖...
pushd "%BACKEND_DIR%"
"%PYTHON_EXE%" -c "import fastapi, sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo 正在安装后端依赖...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
) else (
    echo [OK] 后端依赖已安装
)
popd

REM 检查前端依赖是否已安装
echo 检查前端依赖...
pushd "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo 正在安装前端依赖...
    npm install
) else (
    echo [OK] 前端依赖已安装
)
popd

echo.
echo ========================================
echo 正在启动后端服务...
echo ========================================
echo.

start "BEIMS 后端" /D "%BACKEND_DIR%" "%PYTHON_EXE%" -m uvicorn app.main:app --host 0.0.0.0 --port 8001

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo 正在启动智能助手服务 (8082)...
echo ========================================
echo.

if /I "%START_ASSISTANT%"=="true" (
    if exist "%ASSISTANT_ENTRY%" (
        start "BEIMS 智能助手" /D "%WORKSPACE_DIR%" "%PYTHON_EXE%" "%ASSISTANT_ENTRY%"
    ) else (
        echo [警告] 未找到智能助手入口: %ASSISTANT_ENTRY%
    )
) else (
    echo [信息] 智能助手自动启动已禁用
)

timeout /t 4 /nobreak >nul

echo.
echo ========================================
echo 正在启动前端服务...
echo ========================================
echo.

if exist "%FRONTEND_LOG%" del /f /q "%FRONTEND_LOG%" >nul 2>&1

if /I "%FRONTEND_MODE%"=="preview" (
    echo [信息] 未找到前端源代码，使用 dist 目录预览模式
    start "BEIMS 前端" /D "%FRONTEND_DIR%" cmd /c "npx vite preview --host 0.0.0.0 --port 3000 > ""%FRONTEND_LOG%"" 2>&1"
) else (
    start "BEIMS 前端" /D "%FRONTEND_DIR%" cmd /c "npm run dev > ""%FRONTEND_LOG%"" 2>&1"
)

timeout /t 4 /nobreak >nul

set "BACKEND_OK="
set "FRONTEND_OK="
set "ASSISTANT_OK="
for /f "delims=" %%A in ('netstat -ano ^| find ":8001" ^| find "LISTENING"') do set "BACKEND_OK=1"
for /f "delims=" %%A in ('netstat -ano ^| find ":3000" ^| find "LISTENING"') do set "FRONTEND_OK=1"
for /f "delims=" %%A in ('netstat -ano ^| find ":8082" ^| find "LISTENING"') do set "ASSISTANT_OK=1"

echo.
echo 运行状态检查:
if defined BACKEND_OK (
    echo [OK] 后端服务已在 8001 端口启动
) else (
    echo [警告] 后端服务尚未在 8001 端口启动
)
if defined FRONTEND_OK (
    echo [OK] 前端服务已在 3000 端口启动
) else (
    echo [警告] 前端服务尚未在 3000 端口启动
    echo [信息] 前端日志: %FRONTEND_LOG%
)
if defined ASSISTANT_OK (
    echo [OK] 智能助手服务已在 8082 端口启动
) else (
    echo [警告] 智能助手服务尚未在 8082 端口启动 ^(模型可能仍在加载中，请在 30-60 秒后重试^)
)

echo.
echo ========================================
echo BEIMS 服务启动成功!
echo ========================================
echo.
echo 后端服务:  http://localhost:8001
echo API 文档:  http://localhost:8001/docs
echo 前端服务:  http://localhost:3000
echo 智能助手:  http://localhost:8082
echo.
echo 启动脚本已完成。服务窗口将保持运行。
echo.
pause