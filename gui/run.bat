@echo off
cd /d "%~dp0"

python -c "import flask" 2>NUL
if errorlevel 1 (
    echo Installing Flask, one time only...
    pip install flask
)

echo.
echo Starting Tool-X GUI...
echo Open this in your browser: http://127.0.0.1:5000
echo.

python app.py
pause
