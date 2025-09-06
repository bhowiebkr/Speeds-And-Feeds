# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CNC ToolHub is a comprehensive CNC tool management and machining optimization application built with PySide6 (Qt for Python). The application combines advanced cutting parameter calculations with project-based tool organization, providing a complete solution for managing CNC operations from tool inventory to optimal machining parameters.

**Major Version**: v2.0 - Enhanced with HSM (High Speed Machining), micro tool support, and comprehensive refactored architecture.

## Running the Application

- **Run application**: `run.bat` (Windows batch file that activates venv and runs the app)
- **Run with Python directly**: `venv/Scripts/python.exe src/cnc_toolhub.py`
- **Install dependencies**: `venv/Scripts/python.exe -m pip install -r requirements.txt`

## Key Features

- **Project Management**: Create, organize, and track multiple CNC projects with tool assignments
- **Tool Library Management**: Comprehensive tool database with filtering and organization
- **Advanced Calculations**: Standard and micro tool machining calculations (<3mm tools)
- **Tool Deflection Analysis**: Cantilever beam theory for all tool sizes with deflection warnings
- **HSM Support**: High Speed Machining mode with chip thinning compensation
- **Machine Rigidity**: Adjustments for Router, DIY/Medium, and Industrial VMC machines
- **Unit System**: Full metric/imperial conversion with real-time switching
- **Material Database**: Comprehensive material properties with coating multipliers
- **Graphical Dashboard**: Real-time visual feedback with gradient bars and status indicators
- **Parameter Validation**: Extensive warnings and recommendations for safe machining

## Testing

- **Run all tests**: `run_tests.bat` (Windows batch file) or `venv/Scripts/python.exe run_tests.py`
- **Run specific test**: `venv/Scripts/python.exe tests/test_layout.py`
- **Layout test**: Comprehensive GUI layout validation that detects overlapping elements

### Testing Guidelines

**IMPORTANT**: When writing unit tests, avoid Unicode characters (checkmarks ✓, emojis 🎉, etc.) as they cause encoding errors on Windows systems. Use plain ASCII characters only in test output and assertions.

## Building

- **Local build**: See `BUILD.md` for detailed Nuitka build instructions
- **GitHub Actions**: Automated builds on version tags, manual releases
- **Output**: Standalone Windows executable (no Python required)

## Architecture

### Entry Points
- `src/cnc_toolhub.py` - Main entry point that imports and calls `src.app.start()`
- `src/app.py` - Application startup and theme loading
- `src/main.py` - Simplified GUI class and main window logic

### Refactored Architecture (v2.0)

The codebase has been comprehensively refactored from large monolithic files into a well-organized modular structure:

#### Constants Package (`src/constants/`)
- `units.py` - Unit conversion constants and physical constants
- `materials.py` - Material properties, coating multipliers, MaterialProperty class
- `machining.py` - Machining constants, machine rigidity definitions, efficiency factors

#### Calculators Package (`src/calculators/`)
- `base.py` - Main `FeedsAndSpeeds` class with strategy pattern for tool size selection
- `standard.py` - `StandardMachiningCalculator` for tools ≥3mm using traditional formulas
- `micro.py` - `MicroMachiningCalculator` for tools <3mm with iterative deflection analysis

#### Formulas Package (`src/formulas/`)
- `basic.py` - Fundamental calculations (RPM, feed rate, surface speed, MRR)
- `power.py` - Power and torque calculations
- `chipload.py` - Chipload calculations, chip thinning, HSM adjustments
- `deflection.py` - Tool deflection calculations using cantilever beam theory
- `validation.py` - Parameter validation, warnings, material database loading

#### UI Package (`src/ui/`)
- `boxes/tool.py` - `ToolBox` widget for tool diameter and flute count with unit switching
- `boxes/material.py` - `MaterialBox` widget for material selection and presets
- `boxes/cutting.py` - `CuttingBox` widget for cutting parameters with unit conversion
- `boxes/machine.py` - `MachineBox` widget for machine specifications and rigidity
- `boxes/results.py` - `ResultsBox` widget with graphical dashboard
- `styles.py` - Theme loading functions

#### Utilities Package (`src/utils/`)
- `conversions.py` - Unit conversion utility functions
- `rigidity.py` - Machine rigidity adjustment functions

#### Components (Unchanged)
- `src/components/widgets.py` - Custom widgets (`MaterialCombo`, input validation)
- `src/components/dashboard_widgets.py` - Graphical dashboard components
- `data/materials.json` - Extended material database

### Data Files
- `data/materials.json` - Material database with hardness ranges and K-factors for power calculations
- `data/projects.json` - Project data with tool assignments and organization
- `data/tool_library.json` - Tool library database with specifications
- `data/backups/` - Automatic backups of all data files

### UI Theme
- Uses a custom dark theme stylesheet in `src/dark_theme.qss`
- Loaded automatically in the `start()` function

### Unit Conversions
The application supports both metric and imperial units with automatic conversions:
- Tool diameter: mm ↔ inches
- Cutting parameters: mm ↔ inches, SFM ↔ SMM
- Real-time updates when values change

### Enhanced Calculation Flow (v2.0)
1. **Tool Setup**: User inputs tool diameter, flute count, selects metric/imperial units
2. **Material Selection**: Choose material (auto-populates Kc, surface speeds, chip loads) and tool coating
3. **Cutting Parameters**: Set depth/width of cut, surface speed, feed per tooth with real-time unit conversion
4. **Machine Configuration**: Select machine rigidity (Router/DIY/Industrial) affecting all parameters
5. **Advanced Options**: Enable HSM mode, chip thinning compensation, set tool stickout for deflection
6. **Smart Calculation**: 
   - **Standard Tools (≥3mm)**: Traditional formulas with rigidity adjustments
   - **Micro Tools (<3mm)**: Iterative deflection analysis with convergence checking
   - **All Tools**: Deflection analysis, force calculations, parameter validation
7. **Results Dashboard**: Graphical display with status indicators, warnings, and advanced metrics
8. **Real-time Updates**: All calculations update automatically when any parameter changes

## Development Notes

### Architecture Benefits
- **Modular Design**: Each module has a single, clear responsibility
- **Better Testability**: Individual components can be tested in isolation
- **Easier Maintenance**: Small, focused files are easier to understand and modify
- **Clear Dependencies**: Import structure makes relationships explicit
- **Extensibility**: New features can be added without touching unrelated code

### Technical Implementation
- **Strategy Pattern**: Calculator selection based on tool diameter (<3mm = micro, ≥3mm = standard)
- **Signal-Slot Architecture**: Qt's mechanism for real-time UI updates and unit conversion
- **Iterative Convergence**: Micro tool calculations use deflection feedback loops
- **Physics-Based Modeling**: Cantilever beam theory for tool deflection analysis
- **Machine Rigidity Aware**: All parameters adjusted based on machine type (Router/DIY/Industrial)
- **Settings Persistence**: QSettings for window geometry and user preferences

### Calculation References
- Standard machining formulas from garrtool.com
- Tool deflection using cantilever beam theory (δ = F×L³/(3×E×I))
- Chip thinning compensation (RCTF = 1/√(1 - [1 - (2×Ae/D)]²))
- Material properties from industry-standard sources (Sandvik, Harvey Tool, Kennametal)

### Code Quality
- **Type Hints**: Comprehensive typing for better IDE support and error prevention  
- **Documentation**: Detailed docstrings for all functions and classes
- **Error Handling**: Graceful handling of invalid inputs and edge cases
- **Validation**: Parameter bounds checking with user-friendly warnings

## Important Instructions

**COMMIT POLICY**: NEVER commit changes automatically. ONLY commit when the user EXPLICITLY asks you to commit. Do not commit on your own initiative - wait for explicit user instruction to commit.