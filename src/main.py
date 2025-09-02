import sys
import os
import logging

from PySide6 import QtWidgets, QtCore, QtGui

from src.components.widgets import IntInput, DoubleInput


from src.formulas import FeedsAndSpeeds

IN_TO_MM = 25.4
MM_TO_IN = 0.0393701
FT_TO_M = 0.3048
FT_TO_MM = 304.8
MM_TO_FT = 0.00328084
M_TO_FT = 3.28084


class ToolBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ToolBox, self).__init__(parent)
        self.setTitle("🔧 Tool Info")
        self.setObjectName("tool_box")
        form = QtWidgets.QFormLayout()
        form.setVerticalSpacing(8)
        form.setHorizontalSpacing(10)
        self.setLayout(form)

        # Widgets with enhanced properties
        self.toolDiameter = QtWidgets.QDoubleSpinBox()
        self.toolDiameterImp = QtWidgets.QDoubleSpinBox()
        self.fluteNum = QtWidgets.QSpinBox()
        # self.fluteLen = QtWidgets.QDoubleSpinBox()
        # self.leadAngle = QtWidgets.QDoubleSpinBox()

        # Set ranges and defaults
        self.toolDiameter.setRange(0.1, 200.0)
        self.toolDiameter.setSuffix(" mm")
        self.toolDiameter.setValue(12)
        self.toolDiameter.setToolTip("Tool diameter in millimeters")
        
        self.toolDiameterImp.setRange(0.001, 8.0)
        self.toolDiameterImp.setSuffix('"')
        self.toolDiameterImp.setDecimals(3)
        self.toolDiameterImp.setToolTip("Tool diameter in inches")
        
        self.fluteNum.setRange(1, 10)
        self.fluteNum.setValue(2)
        self.fluteNum.setToolTip("Number of cutting flutes on the tool")
        # self.fluteLen.setValue(10)
        # self.leadAngle.setValue(90)

        # Add Layout
        form.addRow("Diameter (MM)", self.toolDiameter)
        form.addRow("Diameter (inches)", self.toolDiameterImp)
        form.addRow("Number of flutes (#)", self.fluteNum)
        # form.addRow("Flute Length (MM)", self.fluteLen)
        # form.addRow("Lead Angle (°)", self.leadAngle)

        self.toolDiameter.valueChanged.connect(self.mm_to_in)
        self.toolDiameterImp.valueChanged.connect(self.in_to_mm)
        self.mm_to_in()

    def mm_to_in(self):
        self.toolDiameterImp.blockSignals(True)
        self.toolDiameterImp.setValue(self.toolDiameter.value() * MM_TO_IN)
        self.toolDiameterImp.blockSignals(False)

    def in_to_mm(self):
        self.toolDiameter.blockSignals(True)
        self.toolDiameter.setValue(self.toolDiameterImp.value() * IN_TO_MM)
        self.toolDiameter.blockSignals(False)


class CuttingBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(CuttingBox, self).__init__(parent)
        self.setTitle("⚙️ Cutting Operation")
        self.setObjectName("cutting_box")
        form = QtWidgets.QFormLayout()
        form.setVerticalSpacing(12)  # Increased to prevent 34px height spinboxes from overlapping
        form.setHorizontalSpacing(10)
        self.setLayout(form)
        self.paused = False

        # Widgets
        self.DOC = QtWidgets.QDoubleSpinBox()
        self.DOC_IMP = QtWidgets.QDoubleSpinBox()
        self.DOC_percent = QtWidgets.QDoubleSpinBox()
        self.WOC = QtWidgets.QDoubleSpinBox()
        self.WOC_IMP = QtWidgets.QDoubleSpinBox()
        self.WOC_percent = QtWidgets.QDoubleSpinBox()
        self.SFM = QtWidgets.QDoubleSpinBox()
        self.SMM = QtWidgets.QDoubleSpinBox()
        self.SMMM = QtWidgets.QDoubleSpinBox()
        self.IPT = QtWidgets.QDoubleSpinBox()
        self.MMPT = QtWidgets.QDoubleSpinBox()
        self.Kc = QtWidgets.QDoubleSpinBox()  # Specific cutting force
        
        self.IPT.setDecimals(4)
        self.IPT.setMinimum(0.000)
        self.IPT.setSingleStep(0.001)
        self.MMPT.setDecimals(4)
        self.MMPT.setSingleStep(0.001)
        self.MMPT.setMinimum(0.000)
        
        # Configure Kc (Specific Cutting Force)
        self.Kc.setMinimum(500.0)
        self.Kc.setMaximum(4000.0)
        self.Kc.setValue(2000.0)  # Default for general steel
        self.Kc.setSuffix(" N/mm²")
        self.Kc.setToolTip("Specific Cutting Force - Material dependent:\nAluminum: 700-900\nMild Steel: 1800-2200\nStainless: 2400-2800\nCast Iron: 1200-1500")
        self.SFM.setMaximum(10000)
        self.SMM.setMaximum(10000)
        self.SMM.setSingleStep(10)
        self.SMMM.setMaximum(1000000)
        self.WOC_percent.setMaximum(100)
        self.DOC_percent.setMaximum(200)

        self.DOC.setValue(0.5)
        self.WOC.setValue(11)
        self.SFM.setValue(1312.34)
        self.IPT.setValue(0.001)

        spacer1 = QtWidgets.QWidget()
        spacer1.setFixedHeight(10)  # Set the desired height for the spacer
        spacer2 = QtWidgets.QWidget()
        spacer2.setFixedHeight(10)  # Set the desired height for the spacer
        spacer3 = QtWidgets.QWidget()
        spacer3.setFixedHeight(10)  # Set the desired height for the spacer

        form.addRow("Depth Of Cut (MM)", self.DOC)
        form.addRow("Depth Of Cut (Inches)", self.DOC_IMP)
        form.addRow("Depth Of Cut (%)", self.DOC_percent)
        form.addRow(spacer1)
        form.addRow("Width Of Cut (MM)", self.WOC)
        form.addRow("Width Of Cut (Inches)", self.WOC_IMP)
        form.addRow("Width Of Cut (%)", self.WOC_percent)
        form.addRow(spacer2)
        form.addRow("Surface Feet per Minute (SFM)", self.SFM)
        form.addRow("Surface Millimeters per Minute (SMMM)", self.SMMM)
        form.addRow("Surface Meters per Minute (SMM)", self.SMM)
        form.addRow(spacer3)

        form.addRow("Inches per Tooth (IPT)", self.IPT)
        form.addRow("Millimeters per tooth (MMPT)", self.MMPT)
        form.addRow("⚡ Specific Cutting Force (Kc)", self.Kc)

        self.DOC.valueChanged.connect(self.doc_to_others)
        self.DOC_IMP.valueChanged.connect(self.doc_imp_to_others)
        self.WOC.valueChanged.connect(self.woc_to_others)
        self.WOC_IMP.valueChanged.connect(self.woc_imp_to_others)
        self.DOC_percent.valueChanged.connect(self.doc_percent_to_others)
        self.WOC_percent.valueChanged.connect(self.woc_percent_to_others)
        self.IPT.valueChanged.connect(self.ipt_to_mmpt)
        self.MMPT.valueChanged.connect(self.mmpt_to_ipt)
        self.SFM.valueChanged.connect(self.sfm_to_others)
        self.SMM.valueChanged.connect(self.smm_to_others)
        self.SMMM.valueChanged.connect(self.smmm_to_others)

    def init(self):
        self.doc_to_others()
        self.woc_to_others()
        self.ipt_to_mmpt()
        self.sfm_to_others()

        # Surface millimeters per minute

    def doc_imp_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        doc_imp = self.DOC_IMP.value()
        doc = doc_imp * IN_TO_MM
        self.DOC_percent.blockSignals(True)
        self.DOC.blockSignals(True)
        self.DOC_percent.setValue(doc / diameter * 100)
        self.DOC.setValue(doc)
        self.DOC_percent.blockSignals(False)
        self.DOC.blockSignals(False)

    def woc_imp_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        woc = self.WOC_IMP.value() * IN_TO_MM
        self.WOC.blockSignals(True)
        self.WOC_percent.blockSignals(True)
        if woc > diameter:
            self.WOC.setValue(diameter)
            self.WOC_percent.setValue(100)
        else:
            self.WOC_percent.setValue(woc / diameter * 100)
        self.WOC.blockSignals(False)
        self.WOC_percent.blockSignals(False)

    def doc_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        doc = self.DOC.value()
        self.DOC_percent.blockSignals(True)
        self.DOC_IMP.blockSignals(True)
        self.DOC_percent.setValue(doc / diameter * 100)
        self.DOC_IMP.setValue(doc * MM_TO_IN)
        self.DOC_percent.blockSignals(False)
        self.DOC_IMP.blockSignals(False)

    def woc_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        woc = self.WOC.value()
        self.WOC_percent.blockSignals(True)
        self.WOC_IMP.blockSignals(True)
        if woc > diameter:
            self.WOC.setValue(diameter)
            self.WOC_percent.setValue(100)
        else:
            self.WOC_percent.setValue(woc / diameter * 100)
        self.WOC_IMP.setValue(woc * MM_TO_IN)
        self.WOC_percent.blockSignals(False)
        self.WOC_IMP.blockSignals(False)

    def doc_percent_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        doc_percent = self.DOC_percent.value()
        mm = diameter * doc_percent / 100
        self.DOC.blockSignals(True)
        self.DOC_IMP.blockSignals(True)
        self.DOC.setValue(mm)
        self.DOC_IMP.setValue(mm * MM_TO_IN)
        self.DOC.blockSignals(False)
        self.DOC_IMP.blockSignals(False)

    def woc_percent_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        woc_percent = self.WOC_percent.value()
        mm = diameter * woc_percent / 100
        self.WOC.blockSignals(True)
        self.WOC_IMP.blockSignals(True)
        self.WOC.setValue(mm)
        self.WOC_IMP.setValue(mm * MM_TO_IN)
        self.WOC.blockSignals(False)
        self.WOC_IMP.blockSignals(False)

    def ipt_to_mmpt(self):
        ipt = self.IPT.value()
        self.MMPT.blockSignals(True)
        self.MMPT.setValue(ipt * IN_TO_MM)
        self.MMPT.blockSignals(False)

    def mmpt_to_ipt(self):
        mmpt = self.MMPT.value()
        self.IPT.blockSignals(True)
        self.IPT.setValue(mmpt * MM_TO_IN)
        self.IPT.blockSignals(False)

    def sfm_to_others(self):
        sfm = self.SFM.value()
        self.SMMM.blockSignals(True)
        self.SMM.blockSignals(True)
        self.SMMM.setValue(sfm * FT_TO_MM)
        self.SMM.setValue(sfm * FT_TO_M)
        self.SMMM.blockSignals(False)
        self.SMM.blockSignals(False)

    def smm_to_others(self):
        smm = self.SMM.value()
        self.SFM.blockSignals(True)
        self.SMMM.blockSignals(True)
        self.SFM.setValue(smm * M_TO_FT)
        self.SMMM.setValue(smm * 1000)
        self.SFM.blockSignals(False)
        self.SMMM.blockSignals(False)

    def smmm_to_others(self):
        smmm = self.SMMM.value()
        self.SFM.blockSignals(True)
        self.SMM.blockSignals(True)
        self.SFM.setValue(smmm * MM_TO_FT)
        self.SMM.setValue(smmm * 0.001)
        self.SFM.blockSignals(False)
        self.SMM.blockSignals(False)


class MachineBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(MachineBox, self).__init__(parent)
        self.setTitle("🏭 Machine Specs")
        self.setObjectName("machine_box")
        form = QtWidgets.QFormLayout()
        form.setVerticalSpacing(8)
        form.setHorizontalSpacing(10)
        self.setLayout(form)

        # Widgets with enhanced styling
        self.minRPM = QtWidgets.QSpinBox()
        self.minRPM.setRange(0, 100000)
        self.minRPM.setSuffix(" RPM")
        self.minRPM.setValue(6000)
        self.minRPM.setToolTip("Minimum spindle speed of your machine")
        
        self.preferredRPM = QtWidgets.QSpinBox()
        self.preferredRPM.setRange(0, 100000)
        self.preferredRPM.setSuffix(" RPM")
        self.preferredRPM.setValue(22000)
        self.preferredRPM.setToolTip("Your preferred spindle speed for optimal performance")
        
        self.maxRPM = QtWidgets.QSpinBox()
        self.maxRPM.setRange(0, 100000)
        self.maxRPM.setSuffix(" RPM")
        self.maxRPM.setValue(24000)
        self.maxRPM.setToolTip("Maximum spindle speed of your machine")
        
        # Add spindle power capacity
        self.spindlePower = QtWidgets.QDoubleSpinBox()
        self.spindlePower.setRange(0.1, 50.0)
        self.spindlePower.setValue(2.2)  # Default to user's 2.2kW spindle
        self.spindlePower.setSuffix(" kW")
        self.spindlePower.setDecimals(1)
        self.spindlePower.setToolTip("Maximum power capacity of your spindle motor")

        form.addRow("Min (RPM)", self.minRPM)
        form.addRow("⭐ Preferred (RPM)", self.preferredRPM)
        form.addRow("Max (RPM)", self.maxRPM)
        form.addRow("🔌 Spindle Power", self.spindlePower)


class ResultsBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ResultsBox, self).__init__(parent)
        self.setTitle("📊 Results Dashboard")
        self.setObjectName("results_box")
        
        # Import dashboard widgets
        from .components.dashboard_widgets import RangeBarWidget, RPMGaugeWidget, StatusIndicatorWidget
        
        # Main layout - directly use the dashboard
        mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(mainLayout)
        
        # Create dashboard view directly
        self._create_dashboard_view(mainLayout)
    
    def _create_dashboard_view(self, main_layout):
        """Create the graphical dashboard view."""
        from .components.dashboard_widgets import RangeBarWidget, GradientType
        
        # All parameters use consistent gradient bars
        bars_layout = QtWidgets.QGridLayout()
        
        # RPM bar - bell curve (optimal RPM in middle based on preferred value)
        self.rpm_bar = RangeBarWidget()
        self.rpm_bar.setLabel("Spindle Speed")
        self.rpm_bar.setUnit("RPM")
        self.rpm_bar.setGradientType(GradientType.BELL_CURVE)
        
        # Feed Rate bars - bell curve (optimal feed rates in middle)
        self.feed_bar = RangeBarWidget()
        self.feed_bar.setLabel("Feed Rate")
        self.feed_bar.setUnit("mm/min")
        self.feed_bar.setGradientType(GradientType.BELL_CURVE)
        
        self.feed_imp_bar = RangeBarWidget() 
        self.feed_imp_bar.setLabel("Feed Rate")
        self.feed_imp_bar.setUnit("in/min")
        self.feed_imp_bar.setGradientType(GradientType.BELL_CURVE)
        
        # MRR bar - bell curve (optimal efficiency in middle)
        self.mrr_bar = RangeBarWidget()
        self.mrr_bar.setLabel("Material Removal Rate") 
        self.mrr_bar.setUnit("cm³/min")
        self.mrr_bar.setGradientType(GradientType.BELL_CURVE)
        
        # Power bars - ascending (higher efficiency is better, but watch limits)
        self.kw_bar = RangeBarWidget()
        self.kw_bar.setLabel("Power")
        self.kw_bar.setUnit("kW")
        self.kw_bar.setGradientType(GradientType.ASCENDING)
        self.kw_bar.setShowPercentage(True)  # Show percentage of spindle capacity
        
        self.hp_bar = RangeBarWidget()
        self.hp_bar.setLabel("Power") 
        self.hp_bar.setUnit("HP")
        self.hp_bar.setGradientType(GradientType.ASCENDING)
        self.hp_bar.setShowPercentage(True)  # Show percentage of spindle capacity
        
        # Add bars to grid layout in logical order
        bars_layout.addWidget(self.rpm_bar, 0, 0, 1, 2)  # RPM spans 2 columns at top
        bars_layout.addWidget(self.feed_bar, 1, 0)
        bars_layout.addWidget(self.feed_imp_bar, 1, 1)
        bars_layout.addWidget(self.mrr_bar, 2, 0) 
        bars_layout.addWidget(self.kw_bar, 3, 0)
        bars_layout.addWidget(self.hp_bar, 3, 1)
        
        main_layout.addLayout(bars_layout)
        main_layout.addStretch()
    
    
    def update_dashboard_values(self, fs, rpm_status, rpm_message, machine_limits, spindle_capacity_kw):
        """Update dashboard widgets with new values."""
        if hasattr(self, 'rpm_bar'):
            min_rpm, preferred_rpm, max_rpm = machine_limits
            
            # Update RPM bar with bell curve gradient centered on preferred RPM
            self.rpm_bar.setRange(min_rpm, max_rpm)
            self.rpm_bar.setPreferredValue(preferred_rpm)
            self.rpm_bar.setValue(fs.rpm)
            
            # Feed Rate bars - use intelligent range centered around optimal feed rate
            optimal_feed = fs.feed if fs.feed > 0 else 1000  # Default to 1000 mm/min if zero
            self.feed_bar.setIntelligentRange(fs.feed, optimal_feed, 1.2)
            self.feed_bar.setValue(fs.feed)
            
            optimal_feed_imp = optimal_feed * 0.0393701
            self.feed_imp_bar.setIntelligentRange(fs.feed * 0.0393701, optimal_feed_imp, 1.2)
            self.feed_imp_bar.setValue(fs.feed * 0.0393701)
            
            # MRR bar - use intelligent range with typical MRR values
            typical_mrr = max(fs.mrr, 5.0) if fs.mrr > 0 else 15.0  # Default typical MRR
            self.mrr_bar.setIntelligentRange(fs.mrr, typical_mrr, 1.8)
            self.mrr_bar.setValue(fs.mrr)
            
            # Power bars - use actual spindle capacity from machine settings
            self.kw_bar.setRange(0, spindle_capacity_kw)
            self.kw_bar.setPreferredValue(spindle_capacity_kw * 0.7)  # 70% efficiency sweet spot
            self.kw_bar.setValue(fs.kw)
            
            spindle_capacity_hp = spindle_capacity_kw * 1.34102
            self.hp_bar.setRange(0, spindle_capacity_hp)  
            self.hp_bar.setPreferredValue(spindle_capacity_hp * 0.7)  # 70% efficiency sweet spot
            self.hp_bar.setValue(fs.kw * 1.34102)


class GUI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(GUI, self).__init__(parent)
        self.settings = None

        self.setWindowTitle(
            "⚙️ Speeds & Feeds Calculator v2.0 - Enhanced"
        )
        self.setMinimumSize(1000, 650)  # Reduced height with compact dashboard layout
        self.resize(1200, 700)
        settings = QtCore.QSettings("speeds-and-feeds-calc", "SpeedsAndFeedsCalculator")

        try:
            self.restoreGeometry(settings.value("geometry"))

        except Exception as e:
            logging.warning(
                "Unable to load settings. First time opening the tool?\n" + str(e)
            )

        # Layouts with improved spacing
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        sections_layout = QtWidgets.QHBoxLayout()
        sections_layout.setSpacing(15)

        self.setCentralWidget(main_widget)
        main_widget.setLayout(main_layout)
        form = QtWidgets.QFormLayout()

        self.tool_box = ToolBox(self)
        self.cutting_box = CuttingBox(self)
        self.machine_box = MachineBox(self)

        self.results_box = ResultsBox()

        # Add Widgets
        main_layout.addLayout(form)
        main_layout.addLayout(sections_layout)
        sections_layout.addWidget(self.tool_box)
        sections_layout.addWidget(self.cutting_box)
        sections_layout.addWidget(self.machine_box)
        main_layout.addWidget(self.results_box)

        # Logic - Use valueChanged for real-time updates
        self.tool_box.fluteNum.valueChanged.connect(self.update)
        self.cutting_box.DOC.valueChanged.connect(self.update)
        self.cutting_box.WOC.valueChanged.connect(self.update)
        self.cutting_box.SMM.valueChanged.connect(self.update)
        self.cutting_box.SFM.valueChanged.connect(self.update)
        self.cutting_box.SMMM.valueChanged.connect(self.update)
        self.cutting_box.MMPT.valueChanged.connect(self.update)
        self.cutting_box.IPT.valueChanged.connect(self.update)
        self.cutting_box.Kc.valueChanged.connect(self.update)
        self.tool_box.toolDiameter.valueChanged.connect(self.toolDiameterChanged)
        self.tool_box.toolDiameterImp.valueChanged.connect(self.toolDiameterChanged)

        self.cutting_box.init()
        self.update()

    def toolDiameterChanged(self):
        self.cutting_box.init()
        self.update()

    def closeEvent(self, event):
        self.settings = QtCore.QSettings(
            "speeds-and-feeds-calc", "SpeedsAndFeedsCalculator"
        )
        self.settings.setValue("geometry", self.saveGeometry())
        QtWidgets.QWidget.closeEvent(self, event)

    def get_rpm_status(self, rpm):
        """Determine RPM status based on machine limits and preferred RPM"""
        min_rpm = self.machine_box.minRPM.value()
        preferred_rpm = self.machine_box.preferredRPM.value()
        max_rpm = self.machine_box.maxRPM.value()
        
        # Check if outside machine limits (danger)
        if rpm < min_rpm:
            return "danger", f"below minimum ({min_rpm:,} RPM)"
        elif rpm > max_rpm:
            return "danger", f"above maximum ({max_rpm:,} RPM)"
        
        # Check if close to preferred RPM (good)
        preferred_tolerance = preferred_rpm * 0.1  # 10% tolerance around preferred
        if abs(rpm - preferred_rpm) <= preferred_tolerance:
            return "good", f"near preferred ({preferred_rpm:,} RPM)"
        
        # Check if approaching limits (warning)
        elif rpm > max_rpm * 0.9:  # Within 90% of max
            return "warning", "approaching maximum"
        elif rpm < min_rpm * 1.1:  # Within 110% of min
            return "warning", "near minimum"
        else:
            return "info", "within safe range"
    

    def update(self):
        fs = FeedsAndSpeeds()

        # Tool
        fs.diameter = self.tool_box.toolDiameter.value()
        fs.flute_num = self.tool_box.fluteNum.value()
        # fs.flute_len = self.tool_box.fluteLen.value()
        # fs.lead_angle = self.tool_box.leadAngle.value()

        # Cutting
        fs.doc = self.cutting_box.DOC.value()
        fs.woc = self.cutting_box.WOC.value()
        fs.smm = self.cutting_box.SMM.value()
        fs.mmpt = self.cutting_box.MMPT.value()
        fs.kc = self.cutting_box.Kc.value()

        # fs.print_values()

        # Do the formulas
        fs.calculate()
        
        # Get RPM status for color coding  
        rpm_status, rpm_message = self.get_rpm_status(fs.rpm)
        
        # Update dashboard widgets
        machine_limits = (
            self.machine_box.minRPM.value(),
            self.machine_box.preferredRPM.value(), 
            self.machine_box.maxRPM.value()
        )
        spindle_capacity = self.machine_box.spindlePower.value()
        self.results_box.update_dashboard_values(fs, rpm_status, rpm_message, machine_limits, spindle_capacity)

        # Update the output


def load_stylesheet():
    """Load the dark theme stylesheet"""
    stylesheet_path = os.path.join(os.path.dirname(__file__), 'dark_theme.qss')
    try:
        with open(stylesheet_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.warning(f"Stylesheet file not found: {stylesheet_path}")
        return ""

def start():
    app = QtWidgets.QApplication(sys.argv)
    
    # Apply dark theme stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    gui = GUI()
    gui.show()
    app.exec()
    sys.exit()
