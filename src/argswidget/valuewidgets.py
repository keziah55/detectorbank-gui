#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QWidgets with `setValue` method and `value` property.
"""
from qtpy.QtWidgets import QLabel, QLineEdit, QSpinBox, QDoubleSpinBox
from customQObjects.widgets import ComboBox, ElideLabel

class ValueLabel(QLabel):
    def __init__(self, *args, suffix="", **kwargs):
        super().__init__(*args, **kwargs)
        self._suffix = suffix
        
    def setValue(self, value):
        """ Set label text to `value` """
        self.setText(f"{value}{self._suffix}")
        
    @property
    def value(self):
        text = self.text()
        return text.removesuffix(self._suffix)
        
class ValueLineEdit(QLineEdit):
    def setValue(self, value):
        """ Set line edit text to `value` """
        self.setText(f"{value}")
        
    @property
    def value(self):
        return self.text
        
class ValueComboBox(ComboBox):
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