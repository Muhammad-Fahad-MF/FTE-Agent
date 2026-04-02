@echo off
REM Disable CEO Briefing Scheduled Task
REM Disables the weekly CEO briefing generation task without deleting it
REM
REM Usage: disable-ceo-briefing.bat
REM
REM Requirements: Administrator privileges

setlocal enabledelayedexpansion

set TASK_NAME=FTE_CEO_Briefing

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator.
    echo Right-click on this file and select "Run as administrator".
    exit /b 1
)

echo ============================================
echo FTE-Agent CEO Briefing Scheduler - Disable
echo ============================================
echo.
echo Task Name: %TASK_NAME%
echo Action: Disable (task will be kept but not run)
echo.

REM Check if task exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Task '%TASK_NAME%' not found.
    echo Run schedule-ceo-briefing.bat first to create the task.
    exit /b 1
)

REM Disable the task
schtasks /change /tn "%TASK_NAME%" /disable

if %errorLevel% equ 0 (
    echo.
    echo SUCCESS: Task disabled.
    echo.
    echo To re-enable the task:
    echo   schtasks /change /tn "%TASK_NAME%" /enable
    echo.
) else (
    echo.
    echo ERROR: Failed to disable task.
    exit /b 1
)

endlocal
