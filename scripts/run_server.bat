@echo off
REM Ejecuta el PS1 con ExecutionPolicy Bypass y reenvía todos los parámetros
powershell -ExecutionPolicy Bypass -File "%~dp0run_server.ps1" %*
