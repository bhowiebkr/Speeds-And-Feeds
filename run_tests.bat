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

:: Check if test runner exists
if not exist "run_tests.py" (
    echo Error: run_tests.py not found!
    pause
    exit /b 1
)

:: Run the tests
echo Running all tests...
python run_tests.py

:: Check if tests ran successfully
if %ERRORLEVEL% neq 0 (
    echo.
    echo Tests failed with error code %ERRORLEVEL%
) else (
    echo.
    echo All tests completed successfully!
)