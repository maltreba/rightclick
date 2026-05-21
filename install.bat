@echo off
:: Runs the PowerShell installer with ExecutionPolicy Bypass so it works
:: even when the system policy blocks .ps1 files.
:: Double-click this file from Windows Explorer to install.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install-ai-markdown-context-menu.ps1" %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo Installation failed. See the error above.
    pause
    exit /b %ERRORLEVEL%
)
pause
