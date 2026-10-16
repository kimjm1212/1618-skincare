@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
"C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe" post_pin.py --next >> post_pin.log 2>&1
exit /b %errorlevel%
