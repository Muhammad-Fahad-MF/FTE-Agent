@echo off
REM Remove CEO Briefing Scheduled Task
REM Permanently deletes the weekly CEO briefing generation task
REM
REM Usage: remove-ceo-briefing.bat
REM
REM Requirements: Administrator privileges

setlocal enabledelayedexpansion

set TASK_NAME=FTE_CEO_Briefing
set WRAPPER_SCRIPT=%~dp0_ceo_briefing_wrapper.py

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator.
    echo Right-click on this file and select "Run as administrator".
    exit /b 1
)

echo ============================================
echo FTE-Agent CEO Briefing Scheduler - Remove
echo ============================================
echo.
echo Task Name: %TASK_NAME%
echo Action: Permanently delete
echo.

REM Check if task exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo Task '%TASK_NAME%' not found.
    echo Nothing to remove.
    goto :cleanup
)

REM Delete the task
schtasks /delete /tn "%TASK_NAME%" /f

if %errorLevel% equ 0 (
    echo SUCCESS: Task deleted.
) else (
    echo ERROR: Failed to delete task.
    exit /b 1
)

:cleanup
REM Clean up wrapper script
if exist "%WRAPPER_SCRIPT%" (
    echo Deleting wrapper script: %WRAPPER_SCRIPT%
    del /f /q "%WRAPPER_SCRIPT%"
)

echo.
echo Cleanup complete.
echo.

endlocal
