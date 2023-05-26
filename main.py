import sys

import logging

from PySide6 import QtWidgets, QtCore, QtGui

from components.widgets import MaterialCombo, IntInput, DoubleInput
import qdarktheme
from formulas import FeedsAndSpeeds


class ToolBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ToolBox, self).__init__(parent)
        self.setTitle("Tool Info")
        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        # Widgets
        self.toolDiameter = QtWidgets.QDoubleSpinBox()
        self.fluteNum = QtWidgets.QSpinBox()
        self.fluteLen = QtWidgets.QDoubleSpinBox()
        self.leadAngle = QtWidgets.QDoubleSpinBox()

        self.toolDiameter.setValue(12)
        self.fluteNum.setValue(2)
        self.fluteLen.setValue(10)
        self.leadAngle.setValue(90)

        # Add Layout
        form.addRow("Diameter (MM)", self.toolDiameter)
        form.addRow("Number of flutes (#)", self.fluteNum)
        form.addRow("Flute Length (MM)", self.fluteLen)
        form.addRow("Lead Angle (°)", self.leadAngle)


class CuttingBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(CuttingBox, self).__init__(parent)
        self.setTitle("Cutting Operation")
        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        # Widgets
        self.DOC = QtWidgets.QDoubleSpinBox()
        self.WOC = QtWidgets.QDoubleSpinBox()
        self.SFM = QtWidgets.QSpinBox()
        self.SMM = QtWidgets.QSpinBox()
        self.SMMM = QtWidgets.QSpinBox()
        self.IPT = QtWidgets.QDoubleSpinBox()
        self.MMPT = QtWidgets.QDoubleSpinBox()
        self.IPT.setDecimals(4)
        self.IPT.setMinimum(0.000)
        self.SFM.setMaximum(1000)
        # self.useWidthPercentage = QtWidgets.QCheckBox()
        # self.widthPercentage = QtWidgets.QDoubleSpinBox()
        # self.slotting = QtWidgets.QCheckBox()

        self.DOC.setValue(0.5)
        self.WOC.setValue(11)
        self.SFM.setValue(300)
        self.IPT.setValue(0.001)

        spacer = QtWidgets.QWidget()
        spacer.setFixedHeight(10)  # Set the desired height for the spacer

        form.addRow("Depth Of Cut (MM)", self.DOC)
        form.addRow("Width Of Cut (MM)", self.WOC)
        form.addRow(spacer)
        form.addRow("Surface Feet per Minute (SFM)", self.SFM)
        form.addRow("Surface Millimeters per Minute (SMMM)", self.SMMM)
        form.addRow("Surface Meters per Minute (SMM)", self.SMM)
        form.addRow(spacer)

        form.addRow("Inches per Tooth (IPT)", self.IPT)
        form.addRow("Millimeters per tooth (MMPT)", self.MMPT)
        # form.addRow("Width As Percentage", self.useWidthPercentage)
        # form.addRow("Width Percentage (%)", self.widthPercentage)
        # form.addRow("Slotting", self.slotting)

        # self.useWidthPercentage.stateChanged.connect(self.updateGUI)
        # self.slotting.stateChanged.connect(self.updateGUI)

        self.updateGUI()

    def updateGUI(self):
        pass

    # def updateGUI(self):
    #     if self.slotting.isChecked():
    #         self.WOC.setDisabled(True)
    #         self.widthPercentage.setDisabled(True)
    #         self.useWidthPercentage.setDisabled(True)
    #         return
    #     else:
    #         self.useWidthPercentage.setEnabled(True)

    #     if self.useWidthPercentage.isChecked():
    #         self.WOC.setDisabled(True)
    #         self.widthPercentage.setEnabled(True)
    #     else:
    #         self.WOC.setEnabled(True)
    #         self.widthPercentage.setDisabled(True)


class MachineBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(MachineBox, self).__init__(parent)
        self.setTitle("Machine Specs")
        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        # Widgets
        self.minRPM = QtWidgets.QSpinBox()
        self.minRPM.setMaximum(100000)
        self.minRPM.setValue(6000)
        self.maxRPM = QtWidgets.QSpinBox()
        self.maxRPM.setMaximum(100000)
        self.maxRPM.setValue(24000)

        form.addRow("Min (RPM)", self.minRPM)
        form.addRow("Max (RPM)", self.maxRPM)


class ResultsBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ResultsBox, self).__init__(parent)
        self.setTitle("Results")
        mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(mainLayout)

        formLeft = QtWidgets.QFormLayout()
        formRight = QtWidgets.QFormLayout()

        for form in [formLeft, formRight]:
            form.setLabelAlignment(QtCore.Qt.AlignRight)

        mainLayout.addStretch()
        mainLayout.addLayout(formLeft)
        mainLayout.addStretch()
        mainLayout.addLayout(formRight)
        mainLayout.addStretch()

        # Widgets
        self.rpm = QtWidgets.QLabel("<b>18,765</b>")
        self.feed = QtWidgets.QLabel("<b>2000 mm/min</b>")
        self.cutSpeed = QtWidgets.QLabel("<b>10 m/min</b>")
        self.chipLoad = QtWidgets.QLabel("<b>0.065</b>")
        self.mmr = QtWidgets.QLabel("<b>62 cm³/min</b>")

        formLeft.addRow("RPM (n):", self.rpm)
        formLeft.addRow("Surface Speed (Vc):", self.cutSpeed)
        formLeft.addRow("Material Removal Rate (MMR):", self.mmr)
        formRight.addRow("Feed (f):", self.feed)
        formRight.addRow("Chip Load (fz):", self.chipLoad)


class GUI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(GUI, self).__init__(parent)
        self.settings = None

        self.setWindowTitle("Speeds and Feeds Calculator - https://github.com/bhowiebkr/Speeds-And-Feeds")
        settings = QtCore.QSettings("speeds-and-feeds-calc", "SpeedsAndFeedsCalculator")

        try:
            self.restoreGeometry(settings.value("geometry"))

        except AttributeError as e:
            logging.warning("Unable to load settings. First time opening the tool?\n" + str(e))

        # Layouts
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        sections_layout = QtWidgets.QHBoxLayout()

        self.setCentralWidget(main_widget)
        main_widget.setLayout(main_layout)
        form = QtWidgets.QFormLayout()

        self.tool_box = ToolBox()
        self.cutting_box = CuttingBox()
        self.machine_box = MachineBox()

        self.results_box = ResultsBox()

        # widgets
        self.materialCombo = MaterialCombo()

        # Add Widgets
        form.addRow("Material", self.materialCombo)
        main_layout.addLayout(form)
        main_layout.addLayout(sections_layout)
        sections_layout.addWidget(self.tool_box)
        sections_layout.addWidget(self.cutting_box)
        sections_layout.addWidget(self.machine_box)
        main_layout.addWidget(self.results_box)

        # Logic
        self.materialCombo.currentIndexChanged.connect(self.update)

        self.tool_box.toolDiameter.valueChanged.connect(self.update)
        self.tool_box.fluteNum.valueChanged.connect(self.update)
        self.tool_box.fluteLen.valueChanged.connect(self.update)
        self.tool_box.leadAngle.valueChanged.connect(self.update)

        self.cutting_box.DOC.valueChanged.connect(self.update)
        self.cutting_box.WOC.valueChanged.connect(self.update)

        self.update()

    def closeEvent(self, event):
        self.settings = QtCore.QSettings("speeds-and-feeds-calc", "SpeedsAndFeedsCalculator")
        self.settings.setValue("geometry", self.saveGeometry())
        QtWidgets.QWidget.closeEvent(self, event)

    def update(self):
        print("update")

        fs = FeedsAndSpeeds()

        # Material
        fs.hb_min = self.materialCombo.HBMin
        fs.hb_max = self.materialCombo.HBMax
        fs.k_factor = self.materialCombo.k_factor

        # Tool
        fs.diameter = self.tool_box.toolDiameter.value()
        fs.flute_num = self.tool_box.fluteNum.value()
        fs.flute_len = self.tool_box.fluteLen.value()
        fs.lead_angle = self.tool_box.leadAngle.value()

        # Cutting
        fs.doc = self.cutting_box.DOC.value()
        fs.woc = self.cutting_box.WOC.value()

        fs.print_values()

        # Do the formulas

        # Update the output


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    qdarktheme.setup_theme(additional_qss="QToolTip {color: black;}")
    gui = GUI()
    gui.show()
    app.exec()
    sys.exit()
