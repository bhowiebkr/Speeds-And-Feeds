# Get the current directory (where the script is located)
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Define the path to your virtual environment (assumed to be in the current directory)
$VENV_PATH = Join-Path $SCRIPT_DIR "venv"

# Activate the virtual environment
$activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
& $activateScript

# Run the Python script
python (Join-Path $SCRIPT_DIR "speeds_and_feeds.py")

# Deactivate the virtual environment after the script finishes
deactivate