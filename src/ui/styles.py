"""
Styles and theme loading for the Speeds and Feeds Calculator.

Contains functions for loading and applying the dark theme.
"""

import os
import logging


def load_stylesheet():
    """Load the dark theme stylesheet"""
    stylesheet_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dark_theme.qss')
    try:
        with open(stylesheet_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.warning(f"Stylesheet file not found: {stylesheet_path}")
        return ""