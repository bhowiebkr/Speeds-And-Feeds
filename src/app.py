"""
Application entry point and startup logic for the Speeds and Feeds Calculator.

Contains the start() function and application initialization.
"""

import sys
import os
import logging
from PySide6 import QtWidgets
from .ui import load_stylesheet
from .main import GUI


def start():
    """Start the Speeds and Feeds Calculator application."""
    app = QtWidgets.QApplication(sys.argv)
    
    # Apply dark theme stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    gui = GUI()
    gui.show()
    app.exec()
    sys.exit()


if __name__ == "__main__":
    start()