#!/usr/bin/env python3
"""
Layout Testing Script for Speeds and Feeds Calculator
This script creates the GUI and checks for overlapping elements.
"""

import sys
import os
# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from PySide6 import QtWidgets, QtCore
from src.main import GUI
from src.ui.styles import load_stylesheet

def check_widget_overlaps(parent_widget, widget_name=""):
    """Check if any child widgets are overlapping"""
    overlaps = []
    children = parent_widget.findChildren(QtWidgets.QWidget)
    
    # Filter out widgets that shouldn't be checked
    widgets_to_check = []
    for child in children:
        if (hasattr(child, 'geometry') and 
            child.isVisible() and 
            isinstance(child, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox, QtWidgets.QLabel, QtWidgets.QGroupBox))):
            widgets_to_check.append(child)
    
    for i, widget1 in enumerate(widgets_to_check):
        for widget2 in widgets_to_check[i+1:]:
            if widget1.parent() == widget2.parent():  # Only check siblings
                rect1 = widget1.geometry()
                rect2 = widget2.geometry()
                
                if rect1.intersects(rect2):
                    overlap_area = rect1.intersected(rect2)
                    if overlap_area.width() > 1 and overlap_area.height() > 1:  # Ignore 1px overlaps
                        overlaps.append({
                            'widget1': f"{widget1.__class__.__name__}({widget1.objectName() or 'unnamed'})",
                            'widget2': f"{widget2.__class__.__name__}({widget2.objectName() or 'unnamed'})",
                            'widget1_rect': f"({rect1.x()}, {rect1.y()}, {rect1.width()}x{rect1.height()})",
                            'widget2_rect': f"({rect2.x()}, {rect2.y()}, {rect2.width()}x{rect2.height()})",
                            'overlap_rect': f"({overlap_area.x()}, {overlap_area.y()}, {overlap_area.width()}x{overlap_area.height()})",
                            'parent': widget1.parent().__class__.__name__
                        })
    
    return overlaps

def test_layout_at_sizes():
    """Test layout at different window sizes"""
    app = QtWidgets.QApplication(sys.argv)
    
    # Apply stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    gui = GUI()
    gui.show()
    
    # Force the widget to be fully rendered
    app.processEvents()
    QtCore.QTimer.singleShot(100, lambda: None)  # Small delay
    app.processEvents()
    
    test_sizes = [
        (1000, 1100, "Minimum Size"),
        (800, 600, "Below Minimum"),
        (1200, 1100, "Default Size"),
        (1400, 1200, "Large Size")
    ]
    
    results = {}
    
    for width, height, size_name in test_sizes:
        print(f"\n{'='*60}")
        print(f"Testing {size_name}: {width}x{height}")
        print(f"{'='*60}")
        
        gui.resize(width, height)
        app.processEvents()
        QtCore.QTimer.singleShot(50, lambda: None)
        app.processEvents()
        
        # Check overlaps in each section
        sections = [
            (gui.tool_box, "Tool Box"),
            (gui.cutting_box, "Cutting Box"), 
            (gui.machine_box, "Machine Box"),
            (gui.results_box, "Results Box"),
            (gui, "Main Window")
        ]
        
        size_overlaps = []
        for section_widget, section_name in sections:
            overlaps = check_widget_overlaps(section_widget, section_name)
            if overlaps:
                print(f"\n[!] OVERLAPS FOUND in {section_name}:")
                for overlap in overlaps:
                    print(f"  - {overlap['widget1']} overlaps {overlap['widget2']}")
                    print(f"    Widget1: {overlap['widget1_rect']}")
                    print(f"    Widget2: {overlap['widget2_rect']}")
                    print(f"    Overlap: {overlap['overlap_rect']}")
                size_overlaps.extend(overlaps)
            else:
                print(f"[OK] No overlaps in {section_name}")
        
        results[size_name] = size_overlaps
        
        if not size_overlaps:
            print(f"\n[SUCCESS] No overlaps found at {size_name}")
        else:
            print(f"\n[ERROR] {len(size_overlaps)} overlaps found at {size_name}")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for size_name, overlaps in results.items():
        status = "[PASS]" if not overlaps else f"[FAIL] ({len(overlaps)} overlaps)"
        print(f"{size_name:20} : {status}")
    
    # Don't actually show the GUI, just test and exit
    app.quit()
    return results

if __name__ == "__main__":
    test_results = test_layout_at_sizes()
    
    # Exit with error code if any overlaps found
    total_overlaps = sum(len(overlaps) for overlaps in test_results.values())
    sys.exit(1 if total_overlaps > 0 else 0)