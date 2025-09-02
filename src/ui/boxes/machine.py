"""
Machine specifications UI box for the Speeds and Feeds Calculator.

Contains the MachineBox widget for machine specifications and rigidity settings.
"""

from PySide6 import QtWidgets, QtCore
from ...constants.machining import MACHINE_RIGIDITY_FACTORS, MachineRigidity


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
        
        # Add machine rigidity dropdown
        self.rigidityCombo = QtWidgets.QComboBox()
        self.rigidityCombo.addItem("Select Machine Type...")
        
        # Populate with rigidity options
        for rigidity_key, rigidity_data in MACHINE_RIGIDITY_FACTORS.items():
            self.rigidityCombo.addItem(rigidity_data['name'], rigidity_key)
        
        # Set default to DIY/Medium (PrintNC)
        self.rigidityCombo.setCurrentText(MACHINE_RIGIDITY_FACTORS[MachineRigidity.DIY_MEDIUM]['name'])
        self.rigidityCombo.setToolTip("Machine rigidity affects cutting parameters and recommendations")
        
        # Connect signal for rigidity changes
        self.rigidityCombo.currentTextChanged.connect(self.on_rigidity_changed)
        
        # Machine info display
        self.machineInfo = QtWidgets.QLabel()
        self.machineInfo.setWordWrap(True)
        self.machineInfo.setStyleSheet("color: #888; font-size: 10px; padding: 5px; border: 1px solid #444; background-color: #2a2a2a;")
        self.machineInfo.setMinimumHeight(60)
        
        # Initialize machine info display
        self.on_rigidity_changed()

        form.addRow("Min (RPM)", self.minRPM)
        form.addRow("⭐ Preferred (RPM)", self.preferredRPM)
        form.addRow("Max (RPM)", self.maxRPM)
        form.addRow("🔌 Spindle Power", self.spindlePower)
        form.addRow("🏗️ Machine Rigidity", self.rigidityCombo)
        form.addRow("", self.machineInfo)
    
    def on_rigidity_changed(self):
        """Handle machine rigidity selection change."""
        current_text = self.rigidityCombo.currentText()
        if current_text == "Select Machine Type...":
            self.machineInfo.setText("Select your machine type for optimized cutting parameters")
            return
        
        # Find the rigidity key for the selected text
        selected_rigidity = None
        for rigidity_key, rigidity_data in MACHINE_RIGIDITY_FACTORS.items():
            if rigidity_data['name'] == current_text:
                selected_rigidity = rigidity_key
                break
        
        if selected_rigidity:
            rigidity_data = MACHINE_RIGIDITY_FACTORS[selected_rigidity]
            
            # Update machine info display
            info_text = f"{rigidity_data['description']}\n"
            info_text += f"Chipload Reduction: {int((1-rigidity_data['chipload_factor'])*100)}%\n"
            info_text += f"DOC/WOC Reduction: {int((1-rigidity_data['doc_factor'])*100)}%/{int((1-rigidity_data['woc_factor'])*100)}%\n"
            info_text += f"Min RPM: {rigidity_data['min_rpm']} | Steel Limit: {rigidity_data['steel_sfm_limit']} SFM"
            
            self.machineInfo.setText(info_text)
            
            # Auto-adjust RPM recommendations based on machine type
            if selected_rigidity == MachineRigidity.ROUTER:
                # Router recommendations
                self.minRPM.setValue(8000)
                self.preferredRPM.setValue(18000)
                self.maxRPM.setValue(24000)
            elif selected_rigidity == MachineRigidity.DIY_MEDIUM:
                # DIY/PrintNC recommendations  
                self.minRPM.setValue(1000)
                self.preferredRPM.setValue(12000)
                self.maxRPM.setValue(24000)
            elif selected_rigidity == MachineRigidity.VMC_INDUSTRIAL:
                # Industrial VMC recommendations
                self.minRPM.setValue(100)
                self.preferredRPM.setValue(3000)
                self.maxRPM.setValue(12000)
    
    def get_selected_rigidity(self):
        """Get the currently selected machine rigidity level."""
        current_text = self.rigidityCombo.currentText()
        
        # Find the rigidity key for the selected text
        for rigidity_key, rigidity_data in MACHINE_RIGIDITY_FACTORS.items():
            if rigidity_data['name'] == current_text:
                return rigidity_key
        
        # Default to DIY/Medium if nothing selected
        return MachineRigidity.DIY_MEDIUM