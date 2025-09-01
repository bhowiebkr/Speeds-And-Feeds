# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Speeds and Feeds Calculator for CNC machines built with PySide6 (Qt for Python). The application calculates optimal cutting parameters (RPM, feed rates, material removal rates) based on tool specifications, material properties, and cutting parameters.

## Running the Application

- **Run application**: `run.bat` (Windows batch file that activates venv and runs the app)
- **Run with Python directly**: `venv/Scripts/python.exe speeds_and_feeds.py`
- **Install dependencies**: `venv/Scripts/python.exe -m pip install -r requirements.txt`

## Testing

- **Run all tests**: `run_tests.bat` (Windows batch file) or `venv/Scripts/python.exe run_tests.py`
- **Run specific test**: `venv/Scripts/python.exe tests/test_layout.py`
- **Layout test**: Comprehensive GUI layout validation that detects overlapping elements

## Architecture

### Entry Points
- `speeds_and_feeds.py` - Main entry point that imports and calls `src.main.start()`
- `src/main.py` - Contains the GUI application logic and startup function

### Core Components
- **GUI Classes**: All UI components are defined in `src/main.py`:
  - `GUI` - Main window and application controller
  - `ToolBox` - Tool diameter and flute count input
  - `CuttingBox` - Cutting parameters (depth/width of cut, surface speeds, feed per tooth)
  - `MachineBox` - Machine specifications (min/max RPM)
  - `ResultsBox` - Calculated results display

- **Calculations**: `src/formulas.py` contains the `FeedsAndSpeeds` class with machining formulas
- **Custom Widgets**: `src/components/widgets.py` provides:
  - `MaterialCombo` - Dropdown for material selection with hardness (HB) and K-factor data
  - `IntInput`/`DoubleInput` - Validated input fields

### Data Files
- `src/components/materials.json` - Material database with hardness ranges and K-factors for power calculations

### UI Theme
- Uses a custom dark theme stylesheet in `src/dark_theme.qss`
- Loaded automatically in the `start()` function

### Unit Conversions
The application supports both metric and imperial units with automatic conversions:
- Tool diameter: mm ↔ inches
- Cutting parameters: mm ↔ inches, SFM ↔ SMM
- Real-time updates when values change

### Calculation Flow
1. User selects material → provides HB range and K-factor
2. User inputs tool parameters → diameter, flute count
3. User inputs cutting parameters → depth/width of cut, surface speed, feed per tooth
4. Application calculates → RPM, feed rate, material removal rate, power requirements
5. Results update automatically when any input changes

## Development Notes

- The application uses Qt's signal-slot mechanism for real-time UI updates
- Settings are persisted using QSettings for window geometry
- All calculations are based on standard machining formulas referenced from garrtool.com