from qtpy.QtWidgets import QWidget, QVBoxLayout
from customQObjects.widgets import GroupBox
from customQObjects.core import Settings

class ParamPreferences(QWidget):
    
    name = "Params"
    
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        
        group = GroupBox("Profiles")
        
        layout = QVBoxLayout()
        layout.addWidget(group)
        self.setLayout(layout)
        
        self.setCurrentValues()
        self.apply()
        
    def setCurrentValues(self):
        pass
        # self.settings = Settings()
        # self.settings.beginGroup("params/profiles")
        
        # self.settings.endGroup()
        
    def apply(self):
        pass