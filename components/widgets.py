from PySide6 import QtWidgets, QtCore, QtGui


class Material(object):
    def __init__(self, name, HBMin, HBMax):
        self.name = name
        self.HBMin = HBMin
        self.HBMax = HBMax


materials = []
materials.append(Material('Aluminum Alloys', 28, 50))
materials.append(Material('6061-T6 Series Aluminum', 95, 95))


class MaterialCombo(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(MaterialCombo, self).__init__(parent)

        for mat in materials:            
            self.addItem(mat.name, userData=mat)

    @property
    def HBMin(self):
        return self.currentData().HBMin

    @property
    def HBMax(self):
        return self.currentData().HBMax

    @property
    def material(self):
        return self.currentText()




        

