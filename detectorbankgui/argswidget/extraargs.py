#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 16:20:09 2023

@author: keziah
"""

from qtpy.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, 
                            QCheckBox, QSpinBox, QGridLayout,
                            QFileDialog, QVBoxLayout, QScrollArea, QMessageBox)
from qtpy.QtCore import Qt


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
        
        self.layout = QGridLayout()
        
        self.downsampleBox = QSpinBox()
        self.downsampleBox.setMaximum(2**32//2-1) # essentially no max
        self.downsampleBox.setToolTip("Factor by which to downsample the results when plotting")
        row = 0
        self._addRow(row, self.downsampleBox, "Downsample factor")
        
        self.exportDirButton = QPushButton("Select dir")
        row += 1
        self._addRow(row, self.exportDirButton, "Export csv", True)
            
        self.layout.setRowStretch(self.layout.rowCount(), 1)
        
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(2, 1)
        
        self.setLayout(self.layout)
        
    def _addRow(self, row, widget, label, checkable=False):
        label = QLabel(label)
        widgets = [label, widget]
        if checkable:
            checkBox = QCheckBox()
            widgets.insert(0, checkBox)
        for col, widget in enumerate(widgets):
            if len(widgets) == 2:
                col += 1
            self.layout.addWidget(widget, row, col)