from qtpy.QtWidgets import QWidget, QVBoxLayout
from customQObjects.widgets import GroupBox, ComboBox
from customQObjects.core import Settings
from ..profilemanager import ProfileManager

class ParamPreferences(QWidget):
    
    name = "Params"
    
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        
        profileGroup = GroupBox("Profiles", layout="form")
        self.profileBox = ComboBox()
        self.profileBox.addItems(["None"] + ProfileManager().profiles)
        self.profileBox.setToolTip("Default DetectorBank profile")
        profileGroup.addRow("Default profile:", self.profileBox)
        
        layout = QVBoxLayout()
        layout.addWidget(profileGroup)
        self.setLayout(layout)
        
        self.setCurrentValues()
        self.apply()
        
    def setCurrentValues(self):
        settings = Settings()
        settings.beginGroup(self.name.lower())
        
        # defaultProfile = settings.value("defaultProfile", cast=str)
        # self.profileBox.setCurrentText(defaultProfile)
        # if defaultProfile != "None":
            # self.mainWindow.argswidget._loadProfile(defaultProfile)
        
        settings.endGroup()
        
    def apply(self):
        settings = Settings()
        settings.beginGroup(self.name.lower())
        settings.setValue("defaultProfile", self.profileBox.currentText())
        settings.endGroup()