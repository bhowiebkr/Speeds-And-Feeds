@echo off
setlocal

:: Change to the script's directory
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please create a virtual environment first: python -m venv venv
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Check if Python script exists
if not exist "src\cnc_toolhub.py" (
    echo Error: src\cnc_toolhub.py not found!
    pause
    exit /b 1
)

:: Run the Python script
echo Running CNC ToolHub...
python src\cnc_toolhub.py

:: Check if script ran successfully
if %ERRORLEVEL% neq 0 (
    echo.
    echo Script failed with error code %ERRORLEVEL%
)
