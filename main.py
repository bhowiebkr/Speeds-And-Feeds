import sys

import logging

from PySide6 import QtWidgets, QtCore, QtGui

from components.palette import palette
from components.widgets import MaterialCombo, IntInput, DoubleInput



class ToolBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ToolBox, self).__init__(parent)
        self.setTitle('Tool Info')
        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        # Widgets
        self.toolDiameter = QtWidgets.QDoubleSpinBox()
        self.fluteNum = QtWidgets.QSpinBox()
        self.fluteLen = QtWidgets.QDoubleSpinBox()
        self.leadAngle = QtWidgets.QDoubleSpinBox()

        # Add Layout
        form.addRow('Diameter (MM)', self.toolDiameter)
        form.addRow('Number of flutes (#)', self.fluteNum)
        form.addRow('Flute Length (MM)', self.fluteLen)
        form.addRow('Lead Angle (°)', self.leadAngle)



class CuttingBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(CuttingBox, self).__init__(parent)
        self.setTitle('Cutting Operation')
        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        # Widgets
        self.DOC = QtWidgets.QDoubleSpinBox()
        self.WOC = QtWidgets.QDoubleSpinBox()
        self.useWidthPercentage = QtWidgets.QCheckBox()
        self.widthPercentage = QtWidgets.QDoubleSpinBox()
        self.slotting = QtWidgets.QCheckBox()

        form.addRow('Depth Of Cut (MM)', self.DOC)
        form.addRow('Width Of Cut (MM)', self.WOC)
        form.addRow('Width As Percentage', self.useWidthPercentage)
        form.addRow('Width Percentage (%)', self.widthPercentage)
        form.addRow('Slotting', self.slotting)

        self.useWidthPercentage.stateChanged.connect(self.updateGUI)
        self.slotting.stateChanged.connect(self.updateGUI)

        self.updateGUI()

    def updateGUI(self):

        if self.slotting.isChecked():
            self.WOC.setDisabled(True)
            self.widthPercentage.setDisabled(True)
            self.useWidthPercentage.setDisabled(True)
            return
        else:
            self.useWidthPercentage.setEnabled(True)


        if self.useWidthPercentage.isChecked():
            self.WOC.setDisabled(True)
            self.widthPercentage.setEnabled(True)
        else:
            self.WOC.setEnabled(True)
            self.widthPercentage.setDisabled(True)




class MachineBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(MachineBox, self).__init__(parent)
        self.setTitle('Machine Specs')
        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        # Widgets
        self.minRPM = QtWidgets.QSpinBox()
        self.minRPM.setMaximum(100000)
        self.minRPM.setValue(6000)
        self.maxRPM = QtWidgets.QSpinBox()
        self.maxRPM.setMaximum(100000)
        self.maxRPM.setValue(24000)

        form.addRow('Min (RPM)', self.minRPM)
        form.addRow('Max (RPM)', self.maxRPM)


class ResultsBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ResultsBox, self).__init__(parent)
        self.setTitle('Results')
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
        self.rpm = QtWidgets.QLabel('<b>18,765</b>')
        self.feed = QtWidgets.QLabel('<b>2000 mm/min</b>')
        self.cutSpeed = QtWidgets.QLabel('<b>10 m/min</b>')
        self.chipLoad = QtWidgets.QLabel('<b>0.065</b>')
        self.mmr = QtWidgets.QLabel('<b>62 cm³/min</b>') 

        formLeft.addRow('RPM (n):', self.rpm)
        formLeft.addRow('Surface Speed (Vc):', self.cutSpeed)
        formLeft.addRow('Material Removal Rate (MMR):', self.mmr)
        formRight.addRow('Feed (f):', self.feed)
        formRight.addRow('Chip Load (fz):', self.chipLoad)
 


class GUI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(GUI, self).__init__(parent)
        self.settings = None

        self.setWindowTitle("Speeds and Feeds Calculator - https://github.com/bhowiebkr/Speeds-And-Feeds")
        settings = QtCore.QSettings("speeds-and-feeds-calc", "SpeedsAndFeedsCalculator")

        try:
            self.restoreGeometry(settings.value("geometry"))

        except AttributeError as e:
            logging.warning(
                "Unable to load settings. First time opening the tool?\n" + str(e)
            )

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
        form.addRow('Material', self.materialCombo)
        main_layout.addLayout(form)
        main_layout.addLayout(sections_layout)
        sections_layout.addWidget(self.tool_box)
        sections_layout.addWidget(self.cutting_box)
        sections_layout.addWidget(self.machine_box)
        main_layout.addWidget(self.results_box)
        


        # Logic
        self.materialCombo.currentIndexChanged.connect(self.update)

        self.update()

    def closeEvent(self, event):
        self.settings = QtCore.QSettings("speeds-and-feeds-calc", "SpeedsAndFeedsCalculator")
        self.settings.setValue("geometry", self.saveGeometry())
        QtWidgets.QWidget.closeEvent(self, event)

    def update(self):
        print('update')
        print('Material', self.materialCombo.material)
        print('HB Min', self.materialCombo.HBMin)
        print('HB Max', self.materialCombo.HBMax)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    #app.setPalette(palette)
    gui = GUI()
    gui.show()
    app.exec()
    sys.exit()