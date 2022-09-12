import sys

import logging

from PySide6 import QtWidgets, QtCore, QtGui

from lib.palette import palette


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
        main_layout = QtWidgets.QHBoxLayout()

    def closeEvent(self, event):
        self.settings = QtCore.QSettings("speeds-and-feeds-calc", "SpeedsAndFeedsCalculator")
        self.settings.setValue("geometry", self.saveGeometry())
        QtWidgets.QWidget.closeEvent(self, event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setPalette(palette)
    gui = GUI()
    gui.show()
    app.exec()
    sys.exit()