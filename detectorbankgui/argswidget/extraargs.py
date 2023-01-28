#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form to edit additional options
"""

from qtpy.QtWidgets import (QWidget, QLabel, QSizePolicy, QCheckBox, QSpinBox, 
                            QGridLayout, QScrollArea)
from qtpy.QtCore import Qt
from customQObjects.widgets import ElideMixin, ClickMixin
from customQObjects.core import Settings

class ElideButton(ElideMixin, ClickMixin, QLabel): pass

class ExtraOptionsWidget(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.widget = _ExtraOptionsWidget(*args, **kwargs)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        
    def __getattr__(self, name):
        return getattr(self.widget, name)
    
class _ExtraOptionsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.layout = QGridLayout()
        
        self.downsampleBox = QSpinBox()
        self.downsampleBox.setMinimum(1)
        self.downsampleBox.setMaximum(2**32//2-1) # essentially no max
        self.downsampleBox.valueChanged.connect(self._writeDownsampleFactor)
        self.downsampleBox.setToolTip("Factor by which to downsample the results when plotting")
        row = 0
        self._addRow(row, self.downsampleBox, "Plot downsample factor")
        
        self.layout.setRowStretch(self.layout.rowCount(), 1)
        
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(2, 10)
        
        self.layout.setColumnStretch(self.layout.columnCount(), 1)
        
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
        return widgets
            
    def _writeDownsampleFactor(self):
        settings = Settings()
        settings.setValue("plot/downsample", self.downsampleBox.value())
        
    def setDownsampleFactor(self, downsample: int):
        """ Update 'downsample factor' box value """
        self.downsampleBox.setValue(downsample)
        
    def getDownsampleFactor(self) -> int:
        """ Return current 'downsample factor' box value """
        return self.downsampleBox.value()
    