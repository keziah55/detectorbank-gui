#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog to edit detector frequencies and bandwidths
"""

from qtpy.QtWidgets import (QDialog, QTableWidget, QLineEdit, QRadioButton, 
                            QDialogButtonBox, QVBoxLayout, QHBoxLayout, 
                            QGridLayout, QWidget, QLabel)
from qtpy.QtCore import Signal, QTimer, QObject
from qtpy.QtGui import QPalette, QColor
from customQObjects.widgets import GroupBox, StackedWidget
from .noterange import NoteRangePage
import re
from dataclasses import dataclass
    
class EquationPage(QWidget):
    pass

class ManualPage(QWidget):
    pass


class FrequencyInputSelector(QObject):
    
    selected = Signal(str, str)
    
    def __init__(self, name, page, prettyName=None):
        super().__init__()
        
        self.name = name
        self.page = page
        if prettyName is None:
            prettyName = name
        self.prettyName = prettyName
        self.radioButton = QRadioButton(self.prettyName)
        self.radioButton.toggled.connect(self._buttonToggled)
        
    @property
    def isSelected(self):
        return self.radioButton.isChecked()
    
    def setSelected(self):
        self.radioButton.setChecked(True)
        
    def _buttonToggled(self, checked):
        if checked:
            self.selected.emit(self.name, self.prettyName)
        
class FrequencyDialog(QDialog):
    def __init__(self, *args, defaultFreqs=[], defaultBws=[], **kwargs):
        super().__init__(*args, **kwargs)
        
        self.widgets = {
            "note_range":FrequencyInputSelector("note_range", NoteRangePage(), "Note range"), 
            "equation":FrequencyInputSelector("equation", EquationPage(), "Equation"), 
            "manual":FrequencyInputSelector("manual", ManualPage(), "Manual")}
        
        self.inputSelect = GroupBox("Frequency range input mode")
        self.stack = StackedWidget()
        
        for selector in self.widgets.values():
            self.inputSelect.addWidget(selector.radioButton)
            selector.selected.connect(self._changePage)
            self.stack.addWidget(selector.page, selector.name)
            
        self.widgets["note_range"].setSelected()
            
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        
        self.okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
        
        layout = QVBoxLayout()
        layout.addWidget(self.inputSelect)
        layout.addWidget(self.stack)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("Set frequencies and bandwidths")
        
    def _changePage(self, key, prettyName):
        self.stack.setCurrentKey(key)