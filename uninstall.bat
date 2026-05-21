@echo off
:: Removes the right-click context menu entries registered by install.bat.
:: Double-click this file from Windows Explorer to uninstall.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\uninstall-context-menu.ps1" -MenuKey RightClickAiMarkdown %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo Uninstall failed. See the error above.
    pause
    exit /b %ERRORLEVEL%
)
pause
