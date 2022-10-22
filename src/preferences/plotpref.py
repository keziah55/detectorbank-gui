from qtpy.QtWidgets import QWidget, QVBoxLayout
from customQObjects.widgets import GroupBox
from customQObjects.core import Settings

class PlotPreferences(QWidget):
    
    name = "Plot"
    
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        
        audioGroup = GroupBox("Audio input")
        
        hopfGroup = GroupBox("Output")
        
        layout = QVBoxLayout()
        layout.addWidget(audioGroup)
        layout.addWidget(hopfGroup)
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