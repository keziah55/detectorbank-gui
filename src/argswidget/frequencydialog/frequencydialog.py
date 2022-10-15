#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog to edit detector frequencies and bandwidths
"""

from qtpy.QtWidgets import (QDialog, QTableWidget, QTableWidgetItem, QRadioButton, QVBoxLayout,  
                            QVBoxLayout, QDialogButtonBox, QWidget)
from qtpy.QtCore import Signal, QObject, Qt
from customQObjects.widgets import GroupBox, StackedWidget
from .noterange import NoteRangePage
from .equationdialog import EquationPage
    
class ManualPage(QWidget):
    frequencies = Signal(object)


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
        
        self.freqRangeWidgets = {
            "note_range":FrequencyInputSelector("note_range", NoteRangePage(), "Note range"), 
            "equation":FrequencyInputSelector("equation", EquationPage(), "Equation"), 
            "manual":FrequencyInputSelector("manual", ManualPage(), "Manual")}
        
        self.inputSelect = GroupBox("Frequency range input mode")
        self.freqRangeStack = StackedWidget()
        
        for selector in self.freqRangeWidgets.values():
            self.inputSelect.addWidget(selector.radioButton)
            selector.selected.connect(self._changePage)
            self.freqRangeStack.addWidget(selector.page, selector.name)
            selector.page.frequencies.connect(self._setTableFrequencies)
            
        self.freqRangeWidgets["note_range"].setSelected()
        
        self.table = QTableWidget(0,2) 
        self._setTableFrequencies([])
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        
        self.okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
        
        layout = QVBoxLayout()
        layout.addWidget(self.inputSelect)
        layout.addWidget(self.freqRangeStack)
        layout.addWidget(self.table)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("Set frequencies and bandwidths")
        
    def _changePage(self, key, prettyName):
        self.freqRangeStack.setCurrentKey(key)
        
    def _setTableFrequencies(self, freq):
        self.table.clear()
        self.table.setHorizontalHeaderLabels(["Frequency (Hz)", "Bandwidth (Hz)"])
        self.table.setRowCount(len(freq))
        for row, f in enumerate(freq):
            item = QTableWidgetItem(f"{f:g}")
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item)
            