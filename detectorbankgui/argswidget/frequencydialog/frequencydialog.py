#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog to edit detector frequencies and bandwidths
"""

from qtpy.QtWidgets import (QDialog, QTableWidget, QTableWidgetItem, QRadioButton, 
                            QHBoxLayout, QVBoxLayout, QDialogButtonBox, QWidget,
                            QPushButton)
from qtpy.QtCore import Signal, QObject, Qt, QTimer
from customQObjects.widgets import GroupBox, StackedWidget
from customQObjects.gui import getIconFromTheme
from .noterangepage import NoteRangePage
from .equationpage import EquationPage
from .bandwidthpage import BandwidthPage
import numpy as np
    
class PageSelector(QObject):
    """ Object that takes a widget `page` and creates a radio button  for it.
    
        Parameters
        ----------
        key : str
            Identifier for this page
        page : QWidget
            Widget to manage
        label : str
            Label to display
    """
    
    selected = Signal(str, str)
    """ **signal** selected(str `key`, str `label`) 
    
        Emitted when the radio button is checked, with identifying information
    """
    
    def __init__(self, key, page, label=None):
        super().__init__()
        
        self.key = key
        self.page = page
        if label is None:
            label = key
        self.label = label
        self.radioButton = QRadioButton(self.label)
        self.radioButton.toggled.connect(self._buttonToggled)
        
    @property
    def isSelected(self):
        """ Return True if the radio button is checkde """
        return self.radioButton.isChecked()
    
    def setSelected(self):
        """ Set radio button to checked """
        self.radioButton.setChecked(True)
        
    def _buttonToggled(self, checked):
        """ If radio button is checked, emit `selected` signal """
        if checked:
            self.selected.emit(self.key, self.label)
        
class FrequencyDialog(QDialog):
    """ Dialog for users to set frequencies and bandwidths. 
    
        There are a number of different ways to set each. Frequencies can be
        set by giving a note range (NoteRangePage), setting values in an 
        equation (EquationPage) or manually entering in a table.
        Bandwidths can be a constant value for each detector (BandwidthPage)
        or entered manually.
    """
    
    def __init__(self, *args, defaultFreqs=[], defaultBws=[], **kwargs):
        super().__init__(*args, **kwargs)
        
        # buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
        self.okButton.setEnabled(False)
        
        # table of selected frequencies and bandwidths
        self.table = QTableWidget(0,2) 
        self._setTableFrequencies([])
        self._readOnlyFlags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        self._editableFlags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        
        self.addRowButton = QPushButton()
        if (icon := getIconFromTheme('list-add')) is not None:
            self.addRowButton.setIcon(icon)
        else:
            self.addRowButton.setText("Add row")
        self.addRowButton.setEnabled(False)
        self.addRowButton.clicked.connect(self._addTableRow)
        self.addRowButton.setToolTip("Add row to table")
        
        self.clearTableButton = QPushButton()
        if (icon := getIconFromTheme('edit-clear')) is not None:
            self.clearTableButton.setIcon(icon)
        else:
            self.clearTableButton.setText("Clear table")
        self.clearTableButton.clicked.connect(self._clearTable)
        self.clearTableButton.setToolTip("Clear table")
        
        self.tableEditTimer = QTimer()
        self.tableEditTimer.setSingleShot(True)
        self.tableEditTimer.setInterval(50)
        self.tableEditTimer.timeout.connect(self._valueChanged)
        self.table.itemChanged.connect(self.tableEditTimer.start)
        
        # frequency options
        self.freqRangeSelect = GroupBox("Frequency input")
        self.freqRangeStack = StackedWidget()
        self.freqRangeWidgets = [
            PageSelector("note_range", NoteRangePage(invalidColour="#790000"), "Note range"), 
            PageSelector("equation", EquationPage(), "Equation"), 
            PageSelector("manual", QWidget(), "Manual")]
        
        for selector in self.freqRangeWidgets:
            self.freqRangeSelect.addWidget(selector.radioButton)
            selector.selected.connect(self._changeFreqPage)
            self.freqRangeStack.addWidget(selector.page, selector.key)
            if hasattr(selector.page, "values"):
                selector.page.values.connect(self._setTableFrequencies)
        self.freqRangeSelect.addWidget(self.freqRangeStack)
            
        self.freqRangeWidgets[0].setSelected()
        
        # bandwidth options
        self.bwSelect = GroupBox("Bandwidth input")
        self.bwStack = StackedWidget()
        self.bwWidgets = [
            PageSelector("constant", BandwidthPage(), "Constant"), 
            PageSelector("manual", QWidget(), "Manual")]
        
        for selector in self.bwWidgets:
            self.bwSelect.addWidget(selector.radioButton)
            selector.selected.connect(self._changeBwPage)
            self.bwStack.addWidget(selector.page, selector.key)
            if hasattr(selector.page, "values"):
                selector.page.values.connect(self._setTableBandwidths)
        self.bwSelect.addWidget(self.bwStack)
        
        self.bwWidgets[0].setSelected()
        
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
        """Change visible frequency selector page  """
        self.freqRangeStack.setCurrentKey(key)
        editable = key == "manual"
        self._setFreqEditable(editable)
        
    def _changeBwPage(self, key, prettyName):
        """ Change visible bandwidth selector page """
        self.bwStack.setCurrentKey(key)
        editable = key == "manual"
        self._setBwEditable(editable)
        
    def _clearTable(self):
        """ Clear table """
        self.table.clear()
        self.table.setHorizontalHeaderLabels(["Frequency (Hz)", "Bandwidth (Hz)"])
        self.table.resizeColumnsToContents()
        
    def _setTableFrequencies(self, freq):
        """ Clear table and set `freq` as frequencies """
        self._clearTable()
        self.table.setRowCount(len(freq))
        for row, f in enumerate(freq):
            item = QTableWidgetItem(f"{f:g}")
            item.setFlags(self._readOnlyFlags)
            self.table.setItem(row, 0, item)
        self._valueChanged()
            
    def _setTableBandwidths(self, bw):
        """ Set bandwidth value in table. `bw` can be scalar or array """
        if not hasattr(bw, "__len__"):
            bw = [bw] * self.table.rowCount()
        for row in range(self.table.rowCount()):
            item = QTableWidgetItem(f"{bw[row]:g}")
            item.setFlags(self._readOnlyFlags)
            self.table.setItem(row, 1, item)
        self._valueChanged()
            
    def _setFreqEditable(self, editable):
        """ Make frequency column editable """
        self._setTableEditable(editable, 0)
            
    def _setBwEditable(self, editable):
        """ Make bandwidth column editable """
        self._setTableEditable(editable, 1)
            
    def _setTableEditable(self, editable, column):
        """ Set given `column` index editable or readonly. """
        for row in range(self.table.rowCount()):
            if (item := self.table.item(row, column)) is not None:
                flags = self._editableFlags if editable else self._readOnlyFlags
                item.setFlags(flags)
                
        self.addRowButton.setEnabled(editable)
                
        if (item := self.table.item(0, column)) is not None:
            self.table.editItem(item)
            
    def _addTableRow(self):
        """ Add row to table """
        row = self.table.rowCount()
        self.table.insertRow(row)
        
    def _valueChanged(self):
        """ Enable/disable Ok button depending on validity of current values """
        self.okButton.setEnabled(self._validate())
        
    @staticmethod
    def _strIsNumeric(s):
        """ Return True if string `s` can be cast to float. """
        try:
            float(s)
        except:
            return False
        else:
            return True
        
    def _validate(self):
        """ Return True if table is valid, else False. """
        return False if self.values is None else True
                
    @property
    def values(self):
        """ Return array of frequencies and bandwidths from table. 
        
            If table is invlaid, return None.
        """
        if self.table.rowCount() == 0:
            return None
        freqs = []
        bws = []
        for row in range(self.table.rowCount()):
            freqItem = self.table.item(row, 0)
            bwItem = self.table.item(row, 1)
            boolF = freqItem is not None and freqItem.text().strip() != ""
            boolBw = bwItem is not None and bwItem.text().strip() != ""
            if not boolF and not boolBw:
                # whole row is empty, so skip
                continue
            elif boolF != boolBw:
                # one empty, one not empty, so table is not valid
                return None
            else:
                # check that both values are numberic
                if not self._strIsNumeric(freqItem.text()) or not self._strIsNumeric(bwItem.text()):
                    return None 
                else:
                    freqs.append(float(freqItem.text()))
                    bws.append(float(bwItem.text()))
        if len(freqs) == 0 and len(bws) == 0:
            # table is all empty rows
            return None
        return np.column_stack((np.array(freqs), np.array(bws)))
            
    @property
    def valuesStr(self):
        """ Return string representation of `values` """
        if (values := self.values) is not None:
            freqs, bws = values[:,0], values[:,1]
            return f"{len(freqs)} values; ({freqs[0]:g}, {bws[0]:g})...({freqs[-1]:g}, {bws[-1]:g})"
        else:
            return None
                
    def setValues(self, detChars):
        """ Fill in manual frequencies and bandwidths """
        for w in [self.freqRangeWidgets, self.bwWidgets]:
            # 'manual' freqs and bandwidths
            w[-1].setSelected()
        self._setTableFrequencies(detChars[:,0])
        self._setTableBandwidths(detChars[:,1])