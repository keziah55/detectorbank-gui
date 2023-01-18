#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QWidgets with `setValue` method and `value` property.
"""
from qtpy.QtWidgets import QLabel, QSpinBox, QDoubleSpinBox
from qtpy.QtCore import Signal
from customQObjects.widgets import ComboBox

class ValueLabel(QLabel):
    valueChanged = Signal()
    
    def __init__(self, *args, suffix="", **kwargs):
        super().__init__(*args, **kwargs)
        self._suffix = suffix
        
    def setValue(self, value):
        """ Set label text to `value` """
        self.setText(f"{value}{self._suffix}")
        self.valueChanged.emit()
        
    @property
    def value(self):
        text = self.text()
        return text.removesuffix(self._suffix)
                
class ValueComboBox(ComboBox):
    valueChanged = Signal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.currentIndexChanged.connect(self.valueChanged)
        self.currentTextChanged.connect(self.valueChanged)
        
    def setValue(self, value, strict=True):
        """ Set combo box current text to `value` 
        
            If `strict`, `value` will only be added if it is present in :attr:`items` 
        """
        if strict:
            if value not in self.items:
                return None
        self.setCurrentText(f"{value}")
        
class ValueSpinBox(QSpinBox):
    @property
    def value(self):
        return super().value()
    
class ValueDoubleSpinBox(QDoubleSpinBox):
    @property
    def value(self):
        return super().value()