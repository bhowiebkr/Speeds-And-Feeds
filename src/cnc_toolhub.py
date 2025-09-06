from __future__ import annotations

import sys
import os

# Add the parent directory to Python path to enable src imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.app

src.app.start()