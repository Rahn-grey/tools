@echo off
chcp 65001 >nul
set SCRIPT_DIR=%~dp0

REM 尝试自动查找 pythonw.exe
set PYTHONW=

REM 1. 优先使用同目录下的 pythonw（便携版 Python）
if exist "%SCRIPT_DIR%pythonw.exe" set PYTHONW=%SCRIPT_DIR%pythonw.exe

REM 2. 当前环境 conda/Scripts
if not defined PYTHONW if exist "%~dp0..\Scripts\pythonw.exe" set PYTHONW=%~dp0..\Scripts\pythonw.exe

REM 3. Conda 常见路径
if not defined PYTHONW if exist "%ProgramData%\miniconda3\pythonw.exe" set PYTHONW=%ProgramData%\miniconda3\pythonw.exe
if not defined PYTHONW if exist "%ProgramData%\Miniconda3\envs\dev\pythonw.exe" set PYTHONW=%ProgramData%\Miniconda3\envs\dev\pythonw.exe
if not defined PYTHONW if exist "%UserProfile%\.conda\envs\dev\pythonw.exe" set PYTHONW=%UserProfile%\.conda\envs\dev\pythonw.exe

REM 4. 标准 Python 安装
if not defined PYTHONW if exist "%LocalAppData%\Programs\Python\Python313\pythonw.exe" set PYTHONW=%LocalAppData%\Programs\Python\Python313\pythonw.exe
if not defined PYTHONW if exist "%LocalAppData%\Programs\Python\Python312\pythonw.exe" set PYTHONW=%LocalAppData%\Programs\Python\Python312\pythonw.exe

REM 5. 系统 PATH
if not defined PYTHONW for %%i in (pythonw.exe) do set PYTHONW=%%~$PATH:i

if not defined PYTHONW (
    echo [错误] 找不到 pythonw.exe，请先安装 Python 3.9+
    echo 安装依赖：pip install -r requirements.txt
    pause
    exit /b 1
)

start "" "%PYTHONW%" "%SCRIPT_DIR%auth_tool.py" --gui
