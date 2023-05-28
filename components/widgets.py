from PyQt5 import QtWidgets, QtCore, QtGui

import json


class Material(object):
    def __init__(self, name, HB_min, HB_max, k_factor):
        self.name = name
        self.HB_min = HB_min
        self.HB_max = HB_max
        self.k_factor = k_factor

    def get_name(self):
        if self.HB_max == self.HB_min:
            return f"{self.name} ({self.HB_max} HB)"
        return f"{self.name} ({self.HB_min}-{self.HB_max} HB)"


materials = []

with open("components/materials.json") as file:
    data = json.load(file)

sorted_materials = sorted(data, key=lambda x: x["material"])

for each in sorted_materials:
    m = Material(each["material"], each["hb_min"], each["hb_max"], each["k-factor"])
    materials.append(m)


class MaterialCombo(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(MaterialCombo, self).__init__(parent)

        for index, mat in enumerate(materials):
            self.addItem(mat.get_name(), userData=mat)
            # print(index, mat.get_name())

        self.setCurrentIndex(60)  # 6061 alu

    @property
    def HBMin(self):
        return self.currentData().HB_min

    @property
    def HBMax(self):
        return self.currentData().HB_max

    @property
    def k_factor(self):
        return self.currentData().k_factor

    @property
    def material(self):
        return self.currentText()


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
