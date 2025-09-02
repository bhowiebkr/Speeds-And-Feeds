"""
Test suite for dashboard widgets functionality.

Tests the custom dashboard widgets including:
- RangeBarWidget functionality and display
- RPMGaugeWidget animation and status
- StatusIndicatorWidget state changes
- Integration with the main application
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from PySide6 import QtWidgets, QtCore, QtTest, QtGui
from PySide6.QtCore import QTimer

# Add src to path so we can import the modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from components.dashboard_widgets import RangeBarWidget, RPMGaugeWidget, StatusIndicatorWidget


class TestRangeBarWidget(unittest.TestCase):
    """Test cases for the RangeBarWidget."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for testing."""
        if not QtWidgets.QApplication.instance():
            cls.app = QtWidgets.QApplication(sys.argv)
        else:
            cls.app = QtWidgets.QApplication.instance()
    
    def setUp(self):
        """Set up test fixture."""
        self.widget = RangeBarWidget()
    
    def tearDown(self):
        """Clean up after test."""
        self.widget.close()
    
    def test_initialization(self):
        """Test widget initializes with correct defaults."""
        self.assertEqual(self.widget._value, 0.0)
        self.assertEqual(self.widget._min_value, 0.0) 
        self.assertEqual(self.widget._max_value, 100.0)
        self.assertEqual(self.widget._preferred_value, 50.0)
        self.assertEqual(self.widget._unit, "")
        self.assertEqual(self.widget._label, "")
    
    def test_set_value(self):
        """Test setting values updates the widget correctly."""
        # Test normal value
        self.widget.setValue(25.5, animated=False)
        self.assertEqual(self.widget._value, 25.5)
        
        # Test value clamping
        self.widget.setValue(150.0, animated=False)  # Above max
        self.assertEqual(self.widget._value, 100.0)
        
        self.widget.setValue(-10.0, animated=False)  # Below min
        self.assertEqual(self.widget._value, 0.0)
    
    def test_set_range(self):
        """Test setting the range updates min/max values."""
        self.widget.setRange(10, 200)
        self.assertEqual(self.widget._min_value, 10)
        self.assertEqual(self.widget._max_value, 200)
        
        # Test that existing value gets updated
        self.widget.setValue(50, animated=False)
        self.assertEqual(self.widget._value, 50)
    
    def test_set_unit_and_label(self):
        """Test setting unit and label strings."""
        self.widget.setUnit("mm/min")
        self.widget.setLabel("Feed Rate")
        
        self.assertEqual(self.widget._unit, "mm/min")
        self.assertEqual(self.widget._label, "Feed Rate")
    
    def test_preferred_value(self):
        """Test setting preferred value."""
        self.widget.setPreferredValue(75.0)
        self.assertEqual(self.widget._preferred_value, 75.0)
    
    def test_animation_properties(self):
        """Test animation properties are set correctly."""
        self.assertIsNotNone(self.widget._animation)
        self.assertEqual(self.widget._animation.duration(), 250)
    
    def test_tooltip_updates(self):
        """Test tooltip updates with value changes."""
        self.widget.setUnit("RPM")
        self.widget.setRange(0, 2000)  # Set range to accommodate test value
        self.widget.setValue(1500.0, animated=False)
        self.assertEqual(self.widget.toolTip(), "1500.00 RPM")


class TestRPMGaugeWidget(unittest.TestCase):
    """Test cases for the RPMGaugeWidget."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for testing."""
        if not QtWidgets.QApplication.instance():
            cls.app = QtWidgets.QApplication(sys.argv)
        else:
            cls.app = QtWidgets.QApplication.instance()
    
    def setUp(self):
        """Set up test fixture."""
        self.widget = RPMGaugeWidget()
    
    def tearDown(self):
        """Clean up after test."""
        self.widget.close()
    
    def test_initialization(self):
        """Test widget initializes with correct defaults."""
        self.assertEqual(self.widget._value, 0.0)
        self.assertEqual(self.widget._min_value, 0.0)
        self.assertEqual(self.widget._max_value, 30000.0)
        self.assertEqual(self.widget._preferred_value, 22000.0)
        self.assertEqual(self.widget._needle_angle, -90.0)
    
    def test_set_value(self):
        """Test setting RPM values."""
        self.widget.setValue(15000.0, animated=False)
        self.assertEqual(self.widget._value, 15000.0)
        
        # Test negative values get clamped to 0
        self.widget.setValue(-100.0, animated=False)
        self.assertEqual(self.widget._value, 0.0)
    
    def test_needle_angle_calculation(self):
        """Test needle angle is calculated correctly."""
        # At 0 RPM, needle should be at -90°
        self.widget.setValue(0.0, animated=False)
        self.assertEqual(self.widget._needle_angle, -90.0)
        
        # At max RPM, needle should be at +90°
        self.widget.setValue(30000.0, animated=False)
        self.assertEqual(self.widget._needle_angle, 90.0)
        
        # At half max RPM, needle should be at 0°
        self.widget.setValue(15000.0, animated=False)
        self.assertEqual(self.widget._needle_angle, 0.0)
    
    def test_set_range(self):
        """Test setting RPM range."""
        self.widget.setRange(5000, 40000)
        self.assertEqual(self.widget._min_value, 5000)
        self.assertEqual(self.widget._max_value, 40000)
    
    def test_preferred_value(self):
        """Test setting preferred RPM."""
        self.widget.setPreferredValue(25000.0)
        self.assertEqual(self.widget._preferred_value, 25000.0)
    
    def test_status_calculation(self):
        """Test RPM status calculation."""
        self.widget.setRange(6000, 30000)
        self.widget.setPreferredValue(22000)
        
        # Test danger status (below min)
        self.widget.setValue(5000, animated=False)
        self.assertEqual(self.widget.getStatus(), "danger")
        
        # Test danger status (above max)
        self.widget.setValue(35000, animated=False)
        self.assertEqual(self.widget.getStatus(), "danger")
        
        # Test good status (near preferred)
        self.widget.setValue(22000, animated=False)
        self.assertEqual(self.widget.getStatus(), "good")
        
        # Test warning status (approaching max)
        self.widget.setValue(28000, animated=False)  # > 90% of max
        self.assertEqual(self.widget.getStatus(), "warning")
    
    def test_animation_properties(self):
        """Test animation is configured correctly."""
        self.assertIsNotNone(self.widget._animation)
        self.assertEqual(self.widget._animation.duration(), 300)


class TestStatusIndicatorWidget(unittest.TestCase):
    """Test cases for StatusIndicatorWidget."""
    
    @classmethod 
    def setUpClass(cls):
        """Set up QApplication for testing."""
        if not QtWidgets.QApplication.instance():
            cls.app = QtWidgets.QApplication(sys.argv)
        else:
            cls.app = QtWidgets.QApplication.instance()
    
    def setUp(self):
        """Set up test fixture."""
        self.widget = StatusIndicatorWidget()
    
    def tearDown(self):
        """Clean up after test.""" 
        self.widget.close()
    
    def test_initialization(self):
        """Test widget initializes correctly."""
        self.assertEqual(self.widget._status, "info")
        self.assertEqual(self.widget._pulsing, False)
        self.assertEqual(self.widget._pulse_value, 1.0)
    
    def test_set_status(self):
        """Test setting different status values."""
        # Test good status
        self.widget.setStatus("good", pulse=False)
        self.assertEqual(self.widget._status, "good")
        self.assertEqual(self.widget._pulsing, False)
        
        # Test warning status with pulsing
        self.widget.setStatus("warning", pulse=True)
        self.assertEqual(self.widget._status, "warning")
        self.assertEqual(self.widget._pulsing, True)
        
        # Test danger status
        self.widget.setStatus("danger", pulse=True)
        self.assertEqual(self.widget._status, "danger")
        self.assertEqual(self.widget._pulsing, True)
    
    def test_pulse_animation(self):
        """Test pulse animation properties."""
        self.assertIsNotNone(self.widget._pulse_animation)
        self.assertEqual(self.widget._pulse_animation.loopCount(), -1)  # Infinite
        self.assertEqual(self.widget._pulse_animation.duration(), 1000)


class TestDashboardWidgetCompatibility(unittest.TestCase):
    """Test compatibility and basic functionality of dashboard widgets together."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for testing."""
        if not QtWidgets.QApplication.instance():
            cls.app = QtWidgets.QApplication(sys.argv)
        else:
            cls.app = QtWidgets.QApplication.instance()
    
    def test_widgets_can_coexist(self):
        """Test that dashboard widgets can be created together."""
        # Create all widgets
        range_bar = RangeBarWidget()
        rpm_gauge = RPMGaugeWidget()
        status_indicator = StatusIndicatorWidget()
        
        # Test they can be configured
        range_bar.setRange(0, 1000)
        range_bar.setValue(500, animated=False)
        
        rpm_gauge.setRange(1000, 25000)
        rpm_gauge.setValue(15000, animated=False)
        
        status_indicator.setStatus("good", pulse=False)
        
        # Verify values
        self.assertEqual(range_bar._value, 500)
        self.assertEqual(rpm_gauge._value, 15000)
        self.assertEqual(status_indicator._status, "good")
        
        # Clean up
        range_bar.close()
        rpm_gauge.close()
        status_indicator.close()
    
    def test_widget_consistency(self):
        """Test consistent behavior across widgets."""
        range_bar = RangeBarWidget()
        rpm_gauge = RPMGaugeWidget()
        
        # Test both handle negative values appropriately
        range_bar.setValue(-50, animated=False)
        rpm_gauge.setValue(-1000, animated=False)
        
        # Range bar clamps to min, RPM gauge clamps to 0
        self.assertEqual(range_bar._value, 0)  # Default min is 0
        self.assertEqual(rpm_gauge._value, 0)
        
        # Clean up
        range_bar.close()
        rpm_gauge.close()


def run_dashboard_tests():
    """Run all dashboard tests."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases using the modern approach
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestRangeBarWidget))
    suite.addTests(loader.loadTestsFromTestCase(TestRPMGaugeWidget))
    suite.addTests(loader.loadTestsFromTestCase(TestStatusIndicatorWidget))
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardWidgetCompatibility))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_dashboard_tests()
    sys.exit(0 if success else 1)