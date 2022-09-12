import sys

import logging

from PySide6 import QtWidgets, QtCore, QtGui

from components.palette import palette
from components.widgets import MaterialCombo, IntInput, DoubleInput



class ToolBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ToolBox, self).__init__(parent)
        self.setTitle('Tool')
        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        # Widgets
        self.toolDiameter = DoubleInput(6.0)
        self.fluteNum = IntInput(1)
        self.fluteLen = DoubleInput(15.0)
        self.leadAngle = DoubleInput(90.0)

        # Add Layout
        form.addRow('Diameter (MM):', self.toolDiameter)
        form.addRow('Number of flutes:', self.fluteNum)
        form.addRow('Flute Length:', self.fluteLen)
        form.addRow('Lead Angle:', self.leadAngle)



class CuttingBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(CuttingBox, self).__init__(parent)
        self.setTitle('Cutting Operation')
        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        # Widgets
        self.DOC = DoubleInput(1.5)
        self.WOC = DoubleInput(2)
        self.useWidthPercentage = QtWidgets.QCheckBox()
        self.widthPercentage = DoubleInput()
        self.slotting = QtWidgets.QCheckBox()

        form.addRow('Depth Of Cut', self.DOC)
        form.addRow('Width Of Cut', self.WOC)
        form.addRow('Use Width Percentage', self.useWidthPercentage)
        form.addRow('Width Percentage', self.widthPercentage)
        form.addRow('Slotting', self.slotting)

class MachineBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(MachineBox, self).__init__(parent)
        self.setTitle('Machine')
        form = QtWidgets.QFormLayout()
        self.setLayout(form)

        # Widgets
        self.minRPM = IntInput(6000)
        self.maxRPM = IntInput(24000)

        form.addRow('Min RPM', self.minRPM)
        form.addRow('Max RPM', self.maxRPM)




class GUI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(GUI, self).__init__(parent)
        self.settings = None

        self.setWindowTitle("Speeds and Feeds Calculator")
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



        # widgets
        self.materialCombo = MaterialCombo()


        # Add Widgets
        form.addRow('Material', self.materialCombo)
        main_layout.addLayout(form)
        main_layout.addLayout(sections_layout)
        sections_layout.addWidget(self.tool_box)
        sections_layout.addWidget(self.cutting_box)
        sections_layout.addWidget(self.machine_box)
        


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