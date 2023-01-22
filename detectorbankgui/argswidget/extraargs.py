#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 16:20:09 2023

@author: keziah
"""

from qtpy.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, 
                            QCheckBox, QSpinBox, 
                            QFileDialog, QVBoxLayout, QScrollArea, QMessageBox)
from qtpy.QtCore import Qt
from customQObjects.widgets import GroupBox, ComboBox
from ..profilemanager import ProfileManager

class ExtraOptionsWidget(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.widget = _ExtraOptionsWidget(*args, **kwargs)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        
    def __getattr__(self, name):
        return getattr(self.widget, name)
    
class _ExtraOptionsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        layout = QVBoxLayout()
        
        downsampleGroup = GroupBox("Downsample", layout="form")
        self.downsampleBox = QSpinBox()
        self.downsampleBox.setMaximum(2**32//2-1) # essentially no max
        self.downsampleBox.setToolTip("Factor by which to downsample the results when plotting")
        downsampleGroup.addRow("Downsample factor: ", self.downsampleBox)
        
        exportGroup = GroupBox("Export csv", layout="hbox")
        self.exportCheckBox = QCheckBox()
        self.exportDirButton = QPushButton("Select dir")
        self.exportDirLabel = QLabel()
        for widget in [self.exportCheckBox, self.exportDirButton, self.exportDirLabel]:
            exportGroup.addWidget(widget)
            
        profileGroup = GroupBox("Profiles", layout="form")
        self.profileBox = ComboBox()
        self.profileBox.addItems(["None"] + ProfileManager().profiles)
        self.profileBox.setToolTip("Default DetectorBank profile")
        profileGroup.addRow("Default profile:", self.profileBox)
        
        for group in [downsampleGroup, exportGroup, profileGroup]:
            layout.addWidget(group)
            
        self.setLayout(layout)