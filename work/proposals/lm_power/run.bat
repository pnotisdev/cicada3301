@echo off
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
python run.py
exit /b %errorlevel%
