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
from .bandwidthpage import BandwidthPage
    
class ManualPage(QWidget):
    values = Signal(object)


class InputSelector(QObject):
    
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
            "note_range":InputSelector("note_range", NoteRangePage(), "Note range"), 
            "equation":InputSelector("equation", EquationPage(), "Equation"), 
            "manual":InputSelector("manual", ManualPage(), "Manual")}
        
        self.inputSelect = GroupBox("Frequency input")
        self.freqRangeStack = StackedWidget()
        
        for selector in self.freqRangeWidgets.values():
            self.inputSelect.addWidget(selector.radioButton)
            selector.selected.connect(self._changeFreqPage)
            self.freqRangeStack.addWidget(selector.page, selector.name)
            selector.page.values.connect(self._setTableFrequencies)
        self.inputSelect.addWidget(self.freqRangeStack)
            
        self.freqRangeWidgets["note_range"].setSelected()
        
        self.bwSelect = GroupBox("Bandwidth input")
        self.bwStack = StackedWidget()
        self.bwWidgets = {
            "constant":InputSelector("constant", BandwidthPage(), "Constant"), 
            "manual":InputSelector("manual", ManualPage(), "Manual")}
        
        for selector in self.bwWidgets.values():
            self.bwSelect.addWidget(selector.radioButton)
            selector.selected.connect(self._changeBwPage)
            self.bwStack.addWidget(selector.page, selector.name)
            selector.page.values.connect(self._setTableBandwidths)
        self.bwSelect.addWidget(self.bwStack)
        
        self.table = QTableWidget(0,2) 
        self._setTableFrequencies([])
        
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        
        self.okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
        
        layout = QVBoxLayout()
        layout.addWidget(self.inputSelect)
        # layout.addWidget(self.freqRangeStack)
        layout.addWidget(self.bwSelect)
        layout.addWidget(self.table)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("Set frequencies and bandwidths")
        
    def _changeFreqPage(self, key, prettyName):
        self.freqRangeStack.setCurrentKey(key)
        
    def _changeBwPage(self, key, prettyName):
        self.bwStack.setCurrentKey(key)
        
        
    def _setTableFrequencies(self, freq):
        self.table.clear()
        self.table.setHorizontalHeaderLabels(["Frequency (Hz)", "Bandwidth (Hz)"])
        self.table.setRowCount(len(freq))
        for row, f in enumerate(freq):
            item = QTableWidgetItem(f"{f:g}")
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item)
            
    def _setTableBandwidths(self, bw):
        for row in range( self.table.rowCount()):
            item = QTableWidgetItem(f"{bw:g}")
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row, 1, item)