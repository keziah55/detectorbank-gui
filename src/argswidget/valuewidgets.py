#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QWidgets with `setValue` method
"""
from qtpy.QtWidgets import QLabel, QLineEdit
from customQObjects.widgets import ComboBox

class ValueLabel(QLabel):
    def setValue(self, value):
        """ Set label text to `value` """
        self.setText(f"{value}")
        
class ValueLineEdit(QLineEdit):
    def setValue(self, value):
        """ Set line edit text to `value` """
        self.setText(f"{value}")
        
class ValueComboBox(ComboBox):
    def setValue(self, value, strict=True):
        """ Set combo box current text to `value` 
        
            If `strict`, `value` will only be added if it is present in :attr:`items` 
        """
        if strict:
            if value not in self.items:
                return None
        self.setCurrentText(f"{value}")