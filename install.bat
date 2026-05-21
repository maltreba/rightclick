@echo off
:: Runs the PowerShell installer with ExecutionPolicy Bypass so it works
:: even when the system policy blocks .ps1 files.
:: Double-click this file from Windows Explorer to install.
::
:: Store the batch directory in a variable first to avoid cmd.exe misreading
:: parentheses in the path (e.g. "Downloads\repo (4)\...") as shell syntax.
setlocal
set "BATDIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%BATDIR%scripts\install-ai-markdown-context-menu.ps1" %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo Installation failed. See the error above.
    pause
    exit /b %ERRORLEVEL%
)
pause
endlocal
