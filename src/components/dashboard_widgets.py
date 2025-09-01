"""
Dashboard Widgets for Speeds and Feeds Calculator

Custom Qt widgets for displaying machining parameters in a graphical dashboard format.
Includes gradient progress bars, RPM gauges, and animated indicators.
"""

import math
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QPointF, Qt
from PySide6.QtGui import QPainter, QLinearGradient, QColor, QPainterPath, QFont, QPen
from PySide6.QtWidgets import QWidget


class RangeBarWidget(QWidget):
    """
    Horizontal gradient progress bar with position indicator.
    
    Features:
    - Smooth gradient background (green → yellow → red)
    - Vertical indicator line showing current position
    - Min/max/preferred value markers
    - Animated transitions
    - Tooltip with exact value
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 30)
        self.setMaximumHeight(40)
        
        # Value properties
        self._value = 0.0
        self._min_value = 0.0
        self._max_value = 100.0
        self._preferred_value = 50.0
        self._unit = ""
        self._label = ""
        
        # Visual properties
        self._indicator_pos = 0.0
        self._animation = QPropertyAnimation(self, b"indicatorPos")
        self._animation.setDuration(250)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Colors
        self._good_color = QColor("#4CAF50")
        self._warning_color = QColor("#FF9800")
        self._danger_color = QColor("#F44336")
        self._indicator_color = QColor("#FFFFFF")
        self._text_color = QColor("#FFFFFF")
        
        self.setToolTip("0.0")
    
    @QtCore.Property(float)
    def indicatorPos(self):
        return self._indicator_pos
    
    @indicatorPos.setter
    def indicatorPos(self, pos):
        self._indicator_pos = pos
        self.update()
    
    def setValue(self, value, animated=True):
        """Set the current value with optional animation."""
        self._value = max(self._min_value, min(self._max_value, value))
        
        # Calculate position (0.0 to 1.0)
        if self._max_value > self._min_value:
            target_pos = (self._value - self._min_value) / (self._max_value - self._min_value)
        else:
            target_pos = 0.0
            
        self.setToolTip(f"{self._value:.2f} {self._unit}")
        
        if animated:
            self._animation.setStartValue(self._indicator_pos)
            self._animation.setEndValue(target_pos)
            self._animation.start()
        else:
            self.indicatorPos = target_pos
    
    def setRange(self, min_val, max_val):
        """Set the min and max values for the range."""
        self._min_value = min_val
        self._max_value = max_val
        self.setValue(self._value, animated=False)
    
    def setPreferredValue(self, preferred):
        """Set the preferred value (optimal range center)."""
        self._preferred_value = preferred
        self.update()
    
    def setUnit(self, unit):
        """Set the unit string for display."""
        self._unit = unit
        self.setToolTip(f"{self._value:.2f} {self._unit}")
    
    def setLabel(self, label):
        """Set the label text."""
        self._label = label
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event to draw the gradient bar and indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect().adjusted(10, 5, -10, -5)
        bar_rect = QRect(rect.left(), rect.center().y() - 8, rect.width(), 16)
        
        # Draw gradient background
        gradient = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
        gradient.setColorAt(0.0, self._good_color)
        gradient.setColorAt(0.7, self._warning_color) 
        gradient.setColorAt(1.0, self._danger_color)
        
        painter.setBrush(QtGui.QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bar_rect, 8, 8)
        
        # Draw preferred value marker if set
        if self._min_value <= self._preferred_value <= self._max_value:
            pref_pos = (self._preferred_value - self._min_value) / (self._max_value - self._min_value)
            pref_x = bar_rect.left() + pref_pos * bar_rect.width()
            
            painter.setPen(QPen(QColor("#00E676"), 2))
            painter.drawLine(pref_x, bar_rect.top() - 3, pref_x, bar_rect.bottom() + 3)
        
        # Draw current value indicator
        indicator_x = bar_rect.left() + self._indicator_pos * bar_rect.width()
        
        # Draw indicator line
        painter.setPen(QPen(self._indicator_color, 3))
        painter.drawLine(indicator_x, bar_rect.top() - 5, indicator_x, bar_rect.bottom() + 5)
        
        # Draw value text
        if self._label:
            painter.setPen(self._text_color)
            painter.setFont(QFont("Segoe UI", 8))
            text_rect = QRect(rect.left(), rect.bottom() + 2, rect.width(), 12)
            painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, 
                           f"{self._label}: {self._value:.1f} {self._unit}")


class RPMGaugeWidget(QWidget):
    """
    Semi-circular RPM gauge with color zones and animated needle.
    
    Features:
    - 180° arc display
    - Color segments based on machine limits
    - Animated needle pointing to current value  
    - Digital readout in center
    - Min/max/preferred markers
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 100)
        self.setMaximumSize(200, 130)
        
        # Value properties
        self._value = 0.0
        self._min_value = 0.0
        self._max_value = 30000.0
        self._preferred_value = 22000.0
        
        # Animation properties
        self._needle_angle = -90.0  # Start at left (-90°)
        self._animation = QPropertyAnimation(self, b"needleAngle")
        self._animation.setDuration(300)
        self._animation.setEasingCurve(QEasingCurve.Type.OutBack)
        
        # Colors
        self._good_color = QColor("#4CAF50")
        self._warning_color = QColor("#FF9800") 
        self._danger_color = QColor("#F44336")
        self._needle_color = QColor("#FFFFFF")
        self._text_color = QColor("#FFFFFF")
        
        self.setToolTip("0 RPM")
    
    @QtCore.Property(float)
    def needleAngle(self):
        return self._needle_angle
    
    @needleAngle.setter  
    def needleAngle(self, angle):
        self._needle_angle = angle
        self.update()
    
    def setValue(self, value, animated=True):
        """Set RPM value with optional animation."""
        self._value = max(0, value)
        
        # Calculate needle angle (-90° to +90°)
        if self._max_value > 0:
            normalized = min(self._value / self._max_value, 1.0)
            target_angle = -90.0 + (normalized * 180.0)
        else:
            target_angle = -90.0
            
        self.setToolTip(f"{self._value:.0f} RPM")
        
        if animated:
            self._animation.setStartValue(self._needle_angle)
            self._animation.setEndValue(target_angle)
            self._animation.start()
        else:
            self.needleAngle = target_angle
    
    def setRange(self, min_val, max_val):
        """Set min/max RPM values."""
        self._min_value = max(0, min_val)
        self._max_value = max_val
        self.setValue(self._value, animated=False)
    
    def setPreferredValue(self, preferred):
        """Set preferred RPM value."""
        self._preferred_value = preferred
        self.update()
    
    def getStatus(self):
        """Get current RPM status (good/warning/danger)."""
        if self._value < self._min_value or self._value > self._max_value:
            return "danger"
        elif abs(self._value - self._preferred_value) <= self._preferred_value * 0.1:
            return "good" 
        elif self._value > self._max_value * 0.9:
            return "warning"
        else:
            return "info"
    
    def paintEvent(self, event):
        """Custom paint event for the RPM gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height() * 2) // 2 - 10
        
        # Draw gauge arc background
        painter.setPen(QPen(QColor("#3C3C3C"), 8))
        arc_rect = QRect(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        painter.drawArc(arc_rect, 180 * 16, 180 * 16)  # 180° arc
        
        # Draw colored segments
        if self._max_value > 0:
            # Good range (preferred ±10%)
            pref_start = max(0, (self._preferred_value * 0.9) / self._max_value)
            pref_end = min(1, (self._preferred_value * 1.1) / self._max_value)
            
            # Warning range (90-100% of max)
            warn_start = 0.9
            
            # Draw good segment
            painter.setPen(QPen(self._good_color, 6))
            start_angle = 180 - (pref_start * 180)
            span_angle = -(pref_end - pref_start) * 180
            painter.drawArc(arc_rect, int(start_angle * 16), int(span_angle * 16))
            
            # Draw warning segment  
            painter.setPen(QPen(self._warning_color, 6))
            start_angle = 180 - (warn_start * 180)
            span_angle = -(1.0 - warn_start) * 180
            painter.drawArc(arc_rect, int(start_angle * 16), int(span_angle * 16))
        
        # Draw needle
        needle_length = radius - 20
        needle_angle_rad = math.radians(self._needle_angle)
        needle_end = QPointF(
            center.x() + needle_length * math.cos(needle_angle_rad),
            center.y() + needle_length * math.sin(needle_angle_rad)
        )
        
        painter.setPen(QPen(self._needle_color, 3))
        painter.drawLine(center, needle_end)
        
        # Draw center circle
        painter.setBrush(QtGui.QBrush(QColor("#2C2C2C")))
        painter.setPen(QPen(self._needle_color, 2))
        painter.drawEllipse(center, 8, 8)
        
        # Draw digital readout
        painter.setPen(self._text_color)
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        text_rect = QRect(center.x() - 40, center.y() + 15, 80, 20)
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, f"{self._value:.0f}")
        
        # Draw "RPM" label
        painter.setFont(QFont("Segoe UI", 8))
        label_rect = QRect(center.x() - 20, center.y() + 35, 40, 15)
        painter.drawText(label_rect, QtCore.Qt.AlignmentFlag.AlignCenter, "RPM")


class StatusIndicatorWidget(QWidget):
    """
    LED-style status indicator with color and pulsing animation.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        
        self._status = "info"
        self._pulsing = False
        self._pulse_value = 1.0
        
        # Pulse animation
        self._pulse_animation = QPropertyAnimation(self, b"pulseValue")
        self._pulse_animation.setDuration(1000)
        self._pulse_animation.setLoopCount(-1)  # Infinite loop
        self._pulse_animation.valueChanged.connect(self.update)
    
    @QtCore.Property(float)
    def pulseValue(self):
        return self._pulse_value
    
    @pulseValue.setter
    def pulseValue(self, value):
        self._pulse_value = value
        self.update()
    
    def setStatus(self, status, pulse=False):
        """Set status (good/warning/danger/info) with optional pulsing."""
        self._status = status
        self._pulsing = pulse
        
        if pulse:
            self._pulse_animation.setStartValue(0.3)
            self._pulse_animation.setEndValue(1.0)
            self._pulse_animation.start()
        else:
            self._pulse_animation.stop()
            self._pulse_value = 1.0
        
        self.update()
    
    def paintEvent(self, event):
        """Draw the status LED."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Color based on status
        colors = {
            "good": QColor("#4CAF50"),
            "warning": QColor("#FF9800"),
            "danger": QColor("#F44336"), 
            "info": QColor("#2196F3")
        }
        
        color = colors.get(self._status, colors["info"])
        
        # Apply pulsing effect
        if self._pulsing:
            alpha = int(255 * self._pulse_value)
            color.setAlpha(alpha)
        
        # Draw LED circle
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QPen(color.lighter(150), 1))
        
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawEllipse(rect)
        
        # Draw highlight
        highlight = QColor(255, 255, 255, 80)
        painter.setBrush(QtGui.QBrush(highlight))
        painter.setPen(Qt.NoPen)
        highlight_rect = QRect(rect.left() + 3, rect.top() + 3, rect.width() // 3, rect.height() // 3)
        painter.drawEllipse(highlight_rect)