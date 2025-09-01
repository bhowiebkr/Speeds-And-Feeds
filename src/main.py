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

        self.toolDiameter.editingFinished.connect(self.mm_to_in)
        self.toolDiameterImp.editingFinished.connect(self.in_to_mm)
        self.mm_to_in()

    def mm_to_in(self):
        self.toolDiameterImp.setValue(self.toolDiameter.value() * MM_TO_IN)

    def in_to_mm(self):
        self.toolDiameter.setValue(self.toolDiameterImp.value() * IN_TO_MM)


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
        self.IPT.setDecimals(4)
        self.IPT.setMinimum(0.000)
        self.IPT.setSingleStep(0.001)
        self.MMPT.setDecimals(4)
        self.MMPT.setSingleStep(0.001)
        self.MMPT.setMinimum(0.000)
        self.SFM.setMaximum(10000)
        self.SMM.setMaximum(10000)
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

        self.DOC.editingFinished.connect(self.doc_to_others)
        self.DOC_IMP.editingFinished.connect(self.doc_imp_to_others)
        self.WOC.editingFinished.connect(self.woc_to_others)
        self.WOC_IMP.editingFinished.connect(self.woc_imp_to_others)
        self.DOC_percent.editingFinished.connect(self.doc_percent_to_others)
        self.WOC_percent.editingFinished.connect(self.woc_percent_to_others)
        self.IPT.editingFinished.connect(self.ipt_to_mmpt)
        self.MMPT.editingFinished.connect(self.mmpt_to_ipt)
        self.SFM.editingFinished.connect(self.sfm_to_others)
        self.SMM.editingFinished.connect(self.smm_to_others)
        self.SMMM.editingFinished.connect(self.smmm_to_others)

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
        self.DOC_percent.setValue(doc / diameter * 100)
        self.DOC.setValue(doc)

    def woc_imp_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        woc = self.WOC_IMP.value() * IN_TO_MM
        if woc > diameter:
            self.WOC.setValue(diameter)
            self.WOC_percent.setValue(100)
        else:
            self.WOC_percent.setValue(woc / diameter * 100)

    def doc_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        doc = self.DOC.value()
        self.DOC_percent.setValue(doc / diameter * 100)
        self.DOC_IMP.setValue(doc * MM_TO_IN)

    def woc_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        woc = self.WOC.value()
        if woc > diameter:
            self.WOC.setValue(diameter)
            self.WOC_percent.setValue(100)
        else:
            self.WOC_percent.setValue(woc / diameter * 100)

        self.WOC_IMP.setValue(woc * MM_TO_IN)

    def doc_percent_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        doc_percent = self.DOC_percent.value()
        mm = diameter * doc_percent / 100
        self.DOC.setValue(mm)
        self.DOC_IMP.setValue(mm * MM_TO_IN)

    def woc_percent_to_others(self):
        diameter = self.parent().parent().tool_box.toolDiameter.value()
        woc_percent = self.WOC_percent.value()
        mm = diameter * woc_percent / 100
        self.WOC.setValue(mm)
        self.WOC_IMP.setValue(mm * MM_TO_IN)

    def ipt_to_mmpt(self):
        ipt = self.IPT.value()
        self.MMPT.setValue(ipt * IN_TO_MM)

    def mmpt_to_ipt(self):
        mmpt = self.MMPT.value()
        self.IPT.setValue(mmpt * MM_TO_IN)

    def sfm_to_others(self):
        sfm = self.SFM.value()
        self.SMMM.setValue(sfm * FT_TO_MM)
        self.SMM.setValue(sfm * FT_TO_M)

    def smm_to_others(self):
        smm = self.SMM.value()
        self.SFM.setValue(smm * M_TO_FT)
        self.SMMM.setValue(smm * 1000)

    def smmm_to_others(self):
        smmm = self.SMMM.value()
        self.SFM.setValue(smmm * MM_TO_FT)
        self.SMM.setValue(smmm * 0.001)


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

        form.addRow("Min (RPM)", self.minRPM)
        form.addRow("⭐ Preferred (RPM)", self.preferredRPM)
        form.addRow("Max (RPM)", self.maxRPM)


class ResultsBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ResultsBox, self).__init__(parent)
        self.setTitle("📊 Results")
        self.setObjectName("results_box")
        mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(mainLayout)

        formLeft = QtWidgets.QFormLayout()
        formRight = QtWidgets.QFormLayout()

        for form in [formLeft, formRight]:
            form.setLabelAlignment(QtCore.Qt.AlignRight)
            form.setVerticalSpacing(12)
            form.setHorizontalSpacing(15)

        mainLayout.addStretch()
        mainLayout.addLayout(formLeft)
        mainLayout.addStretch()
        mainLayout.addLayout(formRight)
        mainLayout.addStretch()

        # Result widgets with better initial styling
        self.rpm = QtWidgets.QLabel("<b>0</b>")
        self.feed = QtWidgets.QLabel("<b>0 mm/min</b>")
        self.feed_imp = QtWidgets.QLabel("<b>0 inches/min</b>")
        self.mrr = QtWidgets.QLabel("<b>0 cm³/min</b>")
        self.kw = QtWidgets.QLabel("<b>0 kW</b>")
        self.hp = QtWidgets.QLabel("<b>0 HP</b>")
        
        # Set tooltips for results
        self.rpm.setToolTip("Spindle speed - should be within machine limits")
        self.feed.setToolTip("Feed rate in millimeters per minute")
        self.feed_imp.setToolTip("Feed rate in inches per minute")
        self.mrr.setToolTip("Material removal rate - volume of material removed per minute")
        self.kw.setToolTip("Power required in kilowatts")
        self.hp.setToolTip("Power required in horsepower")

        formLeft.addRow("🔄 RPM:", self.rpm)
        formLeft.addRow("📊 MRR:", self.mrr)
        formLeft.addRow("⚡ Power (kW):", self.kw)
        formLeft.addRow("🐎 Power (HP):", self.hp)
        formRight.addRow("🟢 Feed (mm/min):", self.feed)
        formRight.addRow("🟢 Feed (in/min):", self.feed_imp)


class GUI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(GUI, self).__init__(parent)
        self.settings = None

        self.setWindowTitle(
            "⚙️ Speeds & Feeds Calculator v2.0 - Enhanced"
        )
        self.setMinimumSize(1000, 750)  # Increased height to accommodate better spacing
        self.resize(1200, 800)
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

        # Logic
        self.tool_box.fluteNum.editingFinished.connect(self.update)
        self.cutting_box.DOC.editingFinished.connect(self.update)
        self.cutting_box.WOC.editingFinished.connect(self.update)
        self.cutting_box.SMM.editingFinished.connect(self.update)
        self.cutting_box.SFM.editingFinished.connect(self.update)
        self.cutting_box.SMMM.editingFinished.connect(self.update)
        self.cutting_box.MMPT.editingFinished.connect(self.update)
        self.cutting_box.IPT.editingFinished.connect(self.update)
        self.tool_box.toolDiameter.editingFinished.connect(self.toolDiameterChanged)
        self.tool_box.toolDiameterImp.editingFinished.connect(self.toolDiameterChanged)

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
    
    def apply_result_styling(self, label, status, value):
        """Apply color styling to result labels"""
        if status == "good":
            color = "#4CAF50"
            bg_color = "rgba(76, 175, 80, 0.1)"
        elif status == "warning":
            color = "#FF9800"
            bg_color = "rgba(255, 152, 0, 0.1)"
        elif status == "danger":
            color = "#F44336"
            bg_color = "rgba(244, 67, 54, 0.1)"
        else:
            color = "#2196F3"
            bg_color = "rgba(33, 150, 243, 0.1)"
        
        label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: {bg_color};
                border: 1px solid {color};
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11pt;
            }}
        """)
        label.setText(f"<b>{value}</b>")

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

        # fs.print_values()

        # Do the formulas
        fs.calculate()
        
        # Get RPM status for color coding
        rpm_status, rpm_message = self.get_rpm_status(fs.rpm)
        
        # Apply colored styling to results
        self.apply_result_styling(self.results_box.rpm, rpm_status, f"{round(fs.rpm):,}")
        self.apply_result_styling(self.results_box.feed, "info", f"{fs.feed:.2f} mm/min")
        self.apply_result_styling(self.results_box.feed_imp, "info", f"{fs.feed*0.0393701:.2f} inches/min")
        self.apply_result_styling(self.results_box.mrr, "info", f"{fs.mrr:.2f} cm³/min")
        self.apply_result_styling(self.results_box.kw, "info", f"{fs.kw:.2f} kW")
        self.apply_result_styling(self.results_box.hp, "info", f"{fs.kw * 1.34102:.2f} HP")
        
        # Set tooltip for RPM with status message
        self.results_box.rpm.setToolTip(f"RPM Status: {rpm_message}")

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
