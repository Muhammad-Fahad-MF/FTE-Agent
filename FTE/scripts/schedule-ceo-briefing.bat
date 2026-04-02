@echo off
REM Schedule CEO Briefing - Windows Task Scheduler Setup
REM Creates a scheduled task to run CEO briefing generation every Monday at 8:00 AM
REM
REM Usage: schedule-ceo-briefing.bat
REM
REM Requirements:
REM - Administrator privileges (for task creation)
REM - Python 3.10+ installed and in PATH
REM - FTE-Agent environment configured

setlocal enabledelayedexpansion

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%PROJECT_DIR%\src\skills\briefing_skills.py

REM Task configuration
set TASK_NAME=FTE_CEO_Briefing
set TASK_TIME=08:00
set TASK_DAY=MONDAY

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator.
    echo Right-click on this file and select "Run as administrator".
    exit /b 1
)

echo ============================================
echo FTE-Agent CEO Briefing Scheduler Setup
echo ============================================
echo.
echo Task Name: %TASK_NAME%
echo Schedule: Every %TASK_DAY% at %TASK_TIME%
echo Script: %PYTHON_SCRIPT%
echo.

REM Check if Python is available
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ and add it to your PATH.
    exit /b 1
)

REM Get Python executable path
for /f "delims=" %%i in ('where python') do set PYTHON_EXE=%%i
echo Python found: %PYTHON_EXE%
echo.

REM Create wrapper script for the task
set WRAPPER_SCRIPT=%SCRIPT_DIR%_ceo_briefing_wrapper.py
echo Creating wrapper script: %WRAPPER_SCRIPT%

(
echo import sys
echo import os
echo from pathlib import Path
echo.
echo # Add project root to path
echo project_root = Path(__file__).parent.parent
echo sys.path.insert(0, str(project_root / "src"))
echo.
echo # Set environment
echo os.environ.setdefault("DEV_MODE", "true")
echo.
echo try:
echo     from skills.briefing_skills import generate_ceo_briefing
echo     from datetime import datetime
echo.
echo     print(f"Starting CEO Briefing Generation at {datetime.now().isoformat()}")
echo     briefing_path = generate_ceo_briefing()
echo     print(f"Briefing generated successfully: {briefing_path}")
echo     print(f"Completed at {datetime.now().isoformat()}")
echo except Exception as e:
echo     print(f"ERROR: Briefing generation failed: {e}", file=sys.stderr)
echo     sys.exit(1)
) > "%WRAPPER_SCRIPT%"

if errorLevel 1 (
    echo ERROR: Failed to create wrapper script.
    exit /b 1
)

REM Delete existing task if it exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo Deleting existing task...
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
)

REM Create the scheduled task
echo.
echo Creating scheduled task...
schtasks /create /tn "%TASK_NAME%" /tr "\"%PYTHON_EXE%\" \"%WRAPPER_SCRIPT%\"" /sc weekly /d %TASK_DAY% /st %TASK_TIME% /ru SYSTEM /f

if %errorLevel% equ 0 (
    echo.
    echo ============================================
    echo SUCCESS: Scheduled task created!
    echo ============================================
    echo.
    echo Task Details:
    echo - Name: %TASK_NAME%
    echo - Schedule: Every %TASK_DAY% at %TASK_TIME%
    echo - Run as: SYSTEM
    echo.
    echo To verify the task:
    echo   schtasks /query /tn "%TASK_NAME%"
    echo.
    echo To run the task manually (for testing):
    echo   schtasks /run /tn "%TASK_NAME%"
    echo.
    echo To disable the task:
    echo   schtasks /change /tn "%TASK_NAME%" /disable
    echo.
    echo To remove the task:
    echo   schtasks /delete /tn "%TASK_NAME%" /f
    echo.
) else (
    echo.
    echo ERROR: Failed to create scheduled task.
    echo Please check that you have administrator privileges.
    exit /b 1
)

endlocal
