@echo off
setlocal
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0bootstrap.ps1"
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo [ERROR] El proceso finalizo con codigo %ERRORLEVEL%.
  pause
)
