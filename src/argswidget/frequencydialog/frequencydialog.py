#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog to edit detector frequencies and bandwidths
"""

from qtpy.QtWidgets import (QDialog, QTableWidget, QTableWidgetItem, QRadioButton, 
                            QHBoxLayout, QVBoxLayout, QDialogButtonBox, QWidget,
                            QPushButton)
from qtpy.QtCore import Signal, QObject, Qt, QTimer
from qtpy.QtGui import QIcon
from customQObjects.widgets import GroupBox, StackedWidget
from .noterange import NoteRangePage
from .equationdialog import EquationPage
from .bandwidthpage import BandwidthPage
import numpy as np
    
class freqRangeSelector(QObject):
    
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
        
        # buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
        self.okButton.setEnabled(False)
        
        # table
        self.table = QTableWidget(0,2) 
        self._setTableFrequencies([])
        self._readOnlyFlags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        self._editableFlags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        
        self.addRowButton = QPushButton()
        if (icon := QIcon.fromTheme('list-add')) is not None:
            self.addRowButton.setIcon(icon)
        else:
            self.addRowButton.setText("Add row")
        self.addRowButton.setEnabled(False)
        self.addRowButton.clicked.connect(self._addTableRow)
        
        self.clearTableButton = QPushButton()
        if (icon := QIcon.fromTheme('edit-clear')) is not None:
            self.clearTableButton.setIcon(icon)
        else:
            self.clearTableButton.setText("Clear table")
        self.clearTableButton.clicked.connect(self._clearTable)
        
        self.tableEditTimer = QTimer()
        self.tableEditTimer.setSingleShot(True)
        self.tableEditTimer.setInterval(50)
        self.tableEditTimer.timeout.connect(self._valueChanged)
        self.table.itemChanged.connect(self.tableEditTimer.start)
        
        # frequency
        self.freqRangeSelect = GroupBox("Frequency input")
        self.freqRangeStack = StackedWidget()
        self.freqRangeWidgets = {
            "note_range":freqRangeSelector("note_range", NoteRangePage(), "Note range"), 
            "equation":freqRangeSelector("equation", EquationPage(), "Equation"), 
            "manual":freqRangeSelector("manual", QWidget(), "Manual")}
        
        for selector in self.freqRangeWidgets.values():
            self.freqRangeSelect.addWidget(selector.radioButton)
            selector.selected.connect(self._changeFreqPage)
            self.freqRangeStack.addWidget(selector.page, selector.name)
            if hasattr(selector.page, "values"):
                selector.page.values.connect(self._setTableFrequencies)
        self.freqRangeSelect.addWidget(self.freqRangeStack)
            
        self.freqRangeWidgets["note_range"].setSelected()
        
        # bandwidth
        self.bwSelect = GroupBox("Bandwidth input")
        self.bwStack = StackedWidget()
        self.bwWidgets = {
            "constant":freqRangeSelector("constant", BandwidthPage(), "Constant"), 
            "manual":freqRangeSelector("manual", QWidget(), "Manual")}
        
        for selector in self.bwWidgets.values():
            self.bwSelect.addWidget(selector.radioButton)
            selector.selected.connect(self._changeBwPage)
            self.bwStack.addWidget(selector.page, selector.name)
            if hasattr(selector.page, "values"):
                selector.page.values.connect(self._setTableBandwidths)
        self.bwSelect.addWidget(self.bwStack)
        
        self.bwWidgets["constant"].setSelected()
        
        freqBwLayout = QVBoxLayout()
        freqBwLayout.addWidget(self.freqRangeSelect)
        freqBwLayout.addWidget(self.bwSelect)
        
        tableButtons = QHBoxLayout()
        tableButtons.addWidget(self.addRowButton)
        tableButtons.addWidget(self.clearTableButton)
        
        tableLayout = QVBoxLayout()
        tableLayout.addWidget(self.table)
        tableLayout.addLayout(tableButtons)
        
        mainHBoxLayout = QHBoxLayout()
        mainHBoxLayout.addLayout(freqBwLayout)
        mainHBoxLayout.addLayout(tableLayout)
        
        layout = QVBoxLayout()
        layout.addLayout(mainHBoxLayout)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("Set frequencies and bandwidths")
        
    def _changeFreqPage(self, key, prettyName):
        self.freqRangeStack.setCurrentKey(key)
        editable = key == "manual"
        self._setFreqEditable(editable)
        
    def _changeBwPage(self, key, prettyName):
        self.bwStack.setCurrentKey(key)
        editable = key == "manual"
        self._setBwEditable(editable)
        
    def _clearTable(self):
        self.table.clear()
        self.table.setHorizontalHeaderLabels(["Frequency (Hz)", "Bandwidth (Hz)"])
        
    def _setTableFrequencies(self, freq):
        self._clearTable()
        self.table.setRowCount(len(freq))
        for row, f in enumerate(freq):
            item = QTableWidgetItem(f"{f:g}")
            item.setFlags(self._readOnlyFlags)
            self.table.setItem(row, 0, item)
        self._valueChanged()
            
    def _setTableBandwidths(self, bw):
        for row in range( self.table.rowCount()):
            item = QTableWidgetItem(f"{bw:g}")
            item.setFlags(self._readOnlyFlags)
            self.table.setItem(row, 1, item)
        self._valueChanged()
            
    def _setFreqEditable(self, editable):
        self._setTableEditable(editable, 0)
            
    def _setBwEditable(self, editable):
        self._setTableEditable(editable, 1)
            
    def _setTableEditable(self, editable, column):
        for row in range(self.table.rowCount()):
            if (item := self.table.item(row, column)) is not None:
                flags = self._editableFlags if editable else self._readOnlyFlags
                item.setFlags(flags)
                
        self.addRowButton.setEnabled(editable)
                
        if (item := self.table.item(0, column)) is not None:
            self.table.editItem(item)
            
    def _addTableRow(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
    def _valueChanged(self):
        self.okButton.setEnabled(self._validate())
        
    def _validate(self):
        if self.table.rowCount() == 0:
            return False
        # iterate through table
        # if any row has a None value and a non-None value, table is invalid
        # (if both items in row are None, can be skiped)
        for row in range(self.table.rowCount()):
            boolF = self.table.item(row, 0) is not None
            boolBw = self.table.item(row, 1) is not None
            if boolF ^ boolBw:
                return False
        return True
        
    @property
    def value(self):
        if not self._validate():
            return None
        freqs = []
        bws = []
        for row in range(self.table.rowCount()):
            # _validate will be False if one item in row is None but other isn't
            if (item := self.table.item(row, 0)) is not None:
                freqs.append(float(item.text()))
            if (item := self.table.item(row, 1)) is not None:
                bws.append(float(item.text()))
        return np.array(freqs), np.array(bws)
                