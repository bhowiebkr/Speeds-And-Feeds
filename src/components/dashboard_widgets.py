"""
Dashboard Widgets for Speeds and Feeds Calculator

Custom Qt widgets for displaying machining parameters in a graphical dashboard format.
Includes gradient progress bars, RPM gauges, and animated indicators.
"""

import math
from enum import Enum
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QPointF, Qt
from PySide6.QtGui import QPainter, QLinearGradient, QColor, QPainterPath, QFont, QPen
from PySide6.QtWidgets import QWidget


class GradientType(Enum):
    """Gradient types for different parameter visualization needs."""
    BELL_CURVE = "bell_curve"      # Optimal value in middle, worse at extremes
    ASCENDING = "ascending"        # Better values at higher end
    DESCENDING = "descending"      # Better values at lower end


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
        self.setMinimumSize(350, 45)  # Increased height for min/max labels
        self.setFixedHeight(45)  # Fixed height to accommodate labels
        
        # Value properties
        self._value = 0.0
        self._min_value = 0.0
        self._max_value = 100.0
        self._preferred_value = 50.0
        self._unit = ""
        self._label = ""
        self._gradient_type = GradientType.BELL_CURVE
        self._optimal_zone_width = 0.15  # ±15% around preferred value
        self._show_percentage = False
        
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
    
    def setShowPercentage(self, show_percentage=True):
        """Set whether to show percentage alongside the value."""
        self._show_percentage = show_percentage
        self.update()
    
    def setLabel(self, label):
        """Set the label text."""
        self._label = label
        self.update()
    
    def setGradientType(self, gradient_type):
        """Set the gradient type for visualization."""
        self._gradient_type = gradient_type
        self.update()
    
    def setOptimalZoneWidth(self, width):
        """Set the optimal zone width as a fraction (e.g., 0.15 for ±15%)."""
        self._optimal_zone_width = width
        self.update()
    
    def setIntelligentRange(self, current_value, preferred_value, range_factor=1.5):
        """Set an intelligent range centered around preferred value."""
        if preferred_value <= 0:
            preferred_value = current_value if current_value > 0 else 100
            
        # Calculate range with preferred value reasonably centered
        range_span = preferred_value * range_factor
        min_val = max(0, preferred_value - range_span * 0.4)  # 40% below preferred
        max_val = preferred_value + range_span * 0.6  # 60% above preferred
        
        self.setRange(min_val, max_val)
        self.setPreferredValue(preferred_value)
    
    def _create_gradient(self, bar_rect):
        """Create gradient based on the gradient type."""
        gradient = QLinearGradient(bar_rect.topLeft(), bar_rect.topRight())
        
        # Updated softer colors
        optimal_color = QColor("#4CAF50")      # Green
        caution_color = QColor("#FFC107")      # Softer yellow  
        danger_color = QColor("#F44336")       # Red
        
        if self._gradient_type == GradientType.BELL_CURVE:
            # Bell curve: optimal in middle, worse at extremes
            # Calculate preferred position (0.0 to 1.0)
            if self._max_value > self._min_value:
                preferred_pos = (self._preferred_value - self._min_value) / (self._max_value - self._min_value)
            else:
                preferred_pos = 0.5
            
            # Define optimal zone around preferred value
            zone_half_width = self._optimal_zone_width
            optimal_start = max(0.0, preferred_pos - zone_half_width)
            optimal_end = min(1.0, preferred_pos + zone_half_width)
            
            # Create bell curve gradient
            gradient.setColorAt(0.0, danger_color)                    # Red at start
            if optimal_start > 0:
                gradient.setColorAt(optimal_start * 0.5, caution_color)   # Yellow approaching optimal
                gradient.setColorAt(optimal_start, optimal_color)         # Green at optimal zone start
            gradient.setColorAt(preferred_pos, optimal_color)         # Peak green at preferred
            if optimal_end < 1.0:
                gradient.setColorAt(optimal_end, optimal_color)           # Green at optimal zone end
                gradient.setColorAt(optimal_end + (1.0 - optimal_end) * 0.5, caution_color)  # Yellow leaving optimal
            gradient.setColorAt(1.0, danger_color)                    # Red at end
            
        elif self._gradient_type == GradientType.ASCENDING:
            # Better values at higher end (e.g., efficiency metrics)
            gradient.setColorAt(0.0, danger_color)
            gradient.setColorAt(0.3, caution_color) 
            gradient.setColorAt(1.0, optimal_color)
            
        elif self._gradient_type == GradientType.DESCENDING:
            # Better values at lower end (e.g., waste, heat)
            gradient.setColorAt(0.0, optimal_color)
            gradient.setColorAt(0.7, caution_color)
            gradient.setColorAt(1.0, danger_color)
        
        return gradient
    
    def paintEvent(self, event):
        """Custom paint event to draw the gradient bar and indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect().adjusted(5, 5, -5, -5)
        
        # Split widget into 3 sections: label (30%), bar (50%), value (20%)
        label_width = int(rect.width() * 0.3)
        value_width = int(rect.width() * 0.2)
        bar_width = rect.width() - label_width - value_width
        
        label_rect = QRect(rect.left(), rect.top(), label_width, rect.height())
        bar_rect = QRect(rect.left() + label_width + 5, rect.center().y() - 8, bar_width - 10, 16)
        value_rect = QRect(rect.right() - value_width, rect.top(), value_width, rect.height())
        
        # Draw label text on the left
        if self._label:
            painter.setPen(self._text_color)
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(label_rect, QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft, 
                           self._label)
        
        # Draw gradient background bar in the center using the new gradient system
        gradient = self._create_gradient(bar_rect)
        painter.setBrush(QtGui.QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bar_rect, 8, 8)
        
        # Draw optimal zone and preferred value marker
        if self._min_value <= self._preferred_value <= self._max_value:
            pref_pos = (self._preferred_value - self._min_value) / (self._max_value - self._min_value)
            pref_x = bar_rect.left() + pref_pos * bar_rect.width()
            
            # Draw optimal zone highlight for bell curve gradients
            if self._gradient_type == GradientType.BELL_CURVE:
                zone_half_width = self._optimal_zone_width
                zone_start_pos = max(0.0, pref_pos - zone_half_width)
                zone_end_pos = min(1.0, pref_pos + zone_half_width)
                
                zone_start_x = bar_rect.left() + zone_start_pos * bar_rect.width()
                zone_end_x = bar_rect.left() + zone_end_pos * bar_rect.width()
                
                # Draw subtle optimal zone highlight
                painter.setPen(Qt.NoPen)
                painter.setBrush(QtGui.QBrush(QColor(76, 175, 80, 30)))  # Transparent green
                zone_rect = QRect(int(zone_start_x), bar_rect.top(), int(zone_end_x - zone_start_x), bar_rect.height())
                painter.drawRoundedRect(zone_rect, 8, 8)
            
            # Draw preferred value line (brighter and thicker)
            painter.setPen(QPen(QColor("#00E676"), 3))
            painter.drawLine(pref_x, bar_rect.top() - 4, pref_x, bar_rect.bottom() + 4)
            
            # Add small triangular indicator pointing to preferred value
            triangle_points = [
                QPointF(pref_x, bar_rect.top() - 8),
                QPointF(pref_x - 4, bar_rect.top() - 2), 
                QPointF(pref_x + 4, bar_rect.top() - 2)
            ]
            painter.setBrush(QtGui.QBrush(QColor("#00E676")))
            painter.drawPolygon(triangle_points)
        
        # Draw current value indicator
        indicator_x = bar_rect.left() + self._indicator_pos * bar_rect.width()
        
        # Draw indicator line
        painter.setPen(QPen(self._indicator_color, 3))
        painter.drawLine(indicator_x, bar_rect.top() - 5, indicator_x, bar_rect.bottom() + 5)
        
        # Draw value text on the right
        painter.setPen(self._text_color)
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        
        if self._show_percentage and self._max_value > 0:
            percentage = (self._value / self._max_value) * 100
            value_text = f"{self._value:.1f} {self._unit} ({percentage:.0f}%)"
        else:
            value_text = f"{self._value:.1f} {self._unit}"
            
        painter.drawText(value_rect, QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignRight,
                        value_text)
        
        # Draw min/max labels at bar ends for reference
        painter.setFont(QFont("Segoe UI", 7))
        painter.setPen(QColor("#CCCCCC"))
        
        # Min label at start of bar
        min_text = f"{self._min_value:.0f}"
        min_rect = QRect(bar_rect.left() - 5, bar_rect.bottom() + 3, 30, 10)
        painter.drawText(min_rect, QtCore.Qt.AlignmentFlag.AlignLeft, min_text)
        
        # Max label at end of bar  
        max_text = f"{self._max_value:.0f}"
        max_rect = QRect(bar_rect.right() - 25, bar_rect.bottom() + 3, 30, 10)
        painter.drawText(max_rect, QtCore.Qt.AlignmentFlag.AlignRight, max_text)


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
        
        # Draw bell curve colored segments with preferred RPM as optimal
        if self._max_value > 0:
            # Calculate preferred position (0.0 to 1.0 along the arc)
            preferred_pos = self._preferred_value / self._max_value
            
            # Draw segments with bell curve gradient centered on preferred RPM
            num_segments = 36  # Number of segments for smooth gradient
            segment_width = 180.0 / num_segments  # Each segment spans this many degrees
            
            for i in range(num_segments):
                # Calculate position along arc (0.0 to 1.0)
                segment_pos = i / (num_segments - 1)
                
                # Calculate distance from preferred position
                distance_from_preferred = abs(segment_pos - preferred_pos)
                
                # Normalize distance (0.0 = at preferred, 1.0 = maximum distance)
                max_distance = max(preferred_pos, 1.0 - preferred_pos)
                if max_distance > 0:
                    normalized_distance = min(distance_from_preferred / max_distance, 1.0)
                else:
                    normalized_distance = 0.0
                
                # Calculate color based on distance from preferred (bell curve)
                if normalized_distance <= 0.15:  # Within 15% of preferred = green
                    color = self._good_color
                elif normalized_distance <= 0.4:   # 15-40% away = blend to yellow
                    blend_factor = (normalized_distance - 0.15) / 0.25
                    color = QColor(
                        int(self._good_color.red() * (1 - blend_factor) + self._warning_color.red() * blend_factor),
                        int(self._good_color.green() * (1 - blend_factor) + self._warning_color.green() * blend_factor),
                        int(self._good_color.blue() * (1 - blend_factor) + self._warning_color.blue() * blend_factor)
                    )
                elif normalized_distance <= 0.7:   # 40-70% away = yellow
                    color = self._warning_color
                else:  # > 70% away = blend to red
                    blend_factor = min((normalized_distance - 0.7) / 0.3, 1.0)
                    color = QColor(
                        int(self._warning_color.red() * (1 - blend_factor) + self._danger_color.red() * blend_factor),
                        int(self._warning_color.green() * (1 - blend_factor) + self._danger_color.green() * blend_factor),
                        int(self._warning_color.blue() * (1 - blend_factor) + self._danger_color.blue() * blend_factor)
                    )
                
                # Draw this segment
                painter.setPen(QPen(color, 5))
                start_angle = 180 - (i * segment_width)  # Start from left (180°)
                painter.drawArc(arc_rect, int(start_angle * 16), int(-segment_width * 16))
        
        # Draw preferred RPM marker
        if self._max_value > 0:
            preferred_angle = -90.0 + (self._preferred_value / self._max_value * 180.0)
            preferred_angle_rad = math.radians(preferred_angle)
            
            # Draw preferred RPM tick mark
            tick_start = QPointF(
                center.x() + (radius - 15) * math.cos(preferred_angle_rad),
                center.y() + (radius - 15) * math.sin(preferred_angle_rad)
            )
            tick_end = QPointF(
                center.x() + (radius - 5) * math.cos(preferred_angle_rad),
                center.y() + (radius - 5) * math.sin(preferred_angle_rad)
            )
            
            painter.setPen(QPen(QColor("#00E676"), 4))  # Bright green marker
            painter.drawLine(tick_start, tick_end)
            
            # Draw small triangle pointing to preferred value
            triangle_tip = QPointF(
                center.x() + (radius + 8) * math.cos(preferred_angle_rad),
                center.y() + (radius + 8) * math.sin(preferred_angle_rad)
            )
            triangle_base1 = QPointF(
                triangle_tip.x() - 4 * math.cos(preferred_angle_rad + math.pi/6),
                triangle_tip.y() - 4 * math.sin(preferred_angle_rad + math.pi/6)
            )
            triangle_base2 = QPointF(
                triangle_tip.x() - 4 * math.cos(preferred_angle_rad - math.pi/6),
                triangle_tip.y() - 4 * math.sin(preferred_angle_rad - math.pi/6)
            )
            
            painter.setBrush(QtGui.QBrush(QColor("#00E676")))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon([triangle_tip, triangle_base1, triangle_base2])

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