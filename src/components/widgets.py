from PySide6 import QtWidgets, QtCore, QtGui


class IntInput(QtWidgets.QLineEdit):
    def __init__(self, val=None):
        super(IntInput, self).__init__(None)
        self.setValidator(QtGui.QIntValidator())

        if val:
            self.setText(str(val))


class DoubleInput(QtWidgets.QLineEdit):
    def __init__(self, val=None):
        super(DoubleInput, self).__init__(None)
        self.setValidator(QtGui.QDoubleValidator())

        if val:
            self.setText(str(val))