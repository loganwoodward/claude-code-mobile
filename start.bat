@echo off
title Claude Code Mobile Bridge
echo ==============================
echo   Claude Code Mobile Bridge
echo   Auto-restart enabled
echo ==============================
echo.

:: Paste your Telegram bot token below
set TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE

:loop
echo [%date% %time%] Starting bridge...
python "%~dp0bridge.py"
echo [%date% %time%] Bridge stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
