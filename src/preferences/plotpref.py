from qtpy.QtWidgets import QWidget, QVBoxLayout, QSpinBox
from customQObjects.widgets import GroupBox
from customQObjects.core import Settings

class PlotPreferences(QWidget):
    
    name = "Plot"
    
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        
        audioGroup = GroupBox("Audio input")
        
        hopfGroup = GroupBox("Output", layout="form")
        self.downsampleBox = QSpinBox()
        self.downsampleBox.setToolTip("Factor by which to downsample the results when plotting")
        hopfGroup.addRow("Downsample factor: ", self.downsampleBox)
        
        layout = QVBoxLayout()
        layout.addWidget(audioGroup)
        layout.addWidget(hopfGroup)
        self.setLayout(layout)
        
        self.setCurrentValues()
        self.apply()
        
    def setCurrentValues(self):
        settings = Settings()
        settings.beginGroup(self.name.lower())
        
        downsample = settings.value("downsample", cast=int, defaultValue=10)
        self.downsampleBox.setValue(downsample)
        
        settings.endGroup()
        
    def apply(self):
        settings = Settings()
        settings.beginGroup(self.name.lower())
        settings.setValue("downsample", self.downsampleBox.value())
        settings.endGroup()