#!/usr/bin/env python3
"""
Main entry point for CNC ToolHub

This is the primary entry point used by Nuitka for building the standalone executable.
It provides a clean interface for the application startup.
"""

def main():
    """Main application entry point"""
    try:
        import src.main
        src.main.start()
    except Exception as e:
        import sys
        import traceback
        
        # In case of startup errors, show them in a message box if possible
        try:
            from PySide6 import QtWidgets
            app = QtWidgets.QApplication(sys.argv)
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setWindowTitle("CNC ToolHub - Startup Error")
            msg.setText("An error occurred while starting the application:")
            msg.setDetailedText(f"{str(e)}\n\n{traceback.format_exc()}")
            msg.exec()
        except:
            # If Qt fails, fall back to console output
            print("Error starting CNC ToolHub:")
            print(f"{str(e)}")
            traceback.print_exc()
            input("Press Enter to exit...")
        
        sys.exit(1)

if __name__ == "__main__":
    main()