#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 17:27:07 2022

@author: keziah
"""

from qtpy.QtWidgets import QLineEdit, QGridLayout, QWidget, QLabel
from qtpy.QtCore import Signal, QTimer
from qtpy.QtGui import QPalette, QColor
import numpy as np
import re
from dataclasses import dataclass

@dataclass
class NoteRangeInfo:
    name: str
    edit: QLineEdit
    freqLabel: QLabel
    k: int = None
    valid: bool = True
    invalidColour: str = "#ff0000"
    
    def __post_init__(self):
        self.label = QLabel(self.name)
        palette = self.edit.palette()
        self.palettes = {"valid":QPalette(palette), "invalid":QPalette(palette)}
        invalidColour = QColor(self.invalidColour)
        self.palettes["invalid"].setColor(QPalette.Base, invalidColour)
    
    def setK(self, k):
        self.k = k
        if k is not None:
            self.freq = 440*2**(k/12)
            self.freqLabel.setText(f"{self.freq:g} Hz")
        else:
            self.freq = None
            self.freqLabel.setText("")
        
    def setValid(self, valid):
        self.valid = valid
        key = 'valid' if valid else 'invalid'
        self.edit.setPalette(self.palettes[key])
        
    @property
    def widgets(self):
        return [self.label, self.edit, self.freqLabel]
    

class NoteRangePage(QWidget):
    valid = Signal(bool)
    
    def __init__(self, *args, defaultStart="A0", defaultEnd="C8", invalidColour="#ff0000", **kwargs):
        super().__init__(*args, **kwargs)
        
        self.widgets = {"start":NoteRangeInfo("Start note:"),
                        "end":NoteRangeInfo("End note:")}
        
        self.timers = {}
        for key in self.widgets:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.setInterval(50)
            self.timers[key] = timer
            
        self.timers["start"].timeout.connect(lambda: self._textChanged("start"))
        self.timers["end"].timeout.connect(lambda: self._textChanged("end"))
            
        self.widgets["start"].edit.textChanged.connect(self.timers["start"].start)
        self.widgets["end"].edit.textChanged.connect(self.timers["end"].start)
        
        self.widgets["start"].edit.setText(defaultStart)
        self.widgets["end"].setText(defaultEnd)
        
        layout = QGridLayout()
        for row, info in enumerate(self.widgets.values()):
            col = 0
            for widget in info.widgets:
                if isinstance(widget, QWidget):
                    layout.addWidget(widget, row, col)
                    col += 1
        self.setLayout(layout)
        
    @property
    def isValid(self):
        """ Return True if both edits contain valid notes """
        return self.widgets["start"].valid and self.widgets["end"].valid
        
    def _textChanged(self, which):
        text = self.widgets[which].edit.text()
        if (k := self._validate(text)) is not False:
            self.widgets[which].setValid(True)
            self.widgets[which].setK(k)
        else:
            self.widgets[which].setValid(False)
            self.widgets[which].setK(None)
            
        self.valid.emit(self.isValid)
        
    @classmethod
    def _validate(cls, value):
        if (m := re.match(r"(?P<note>[A-Ga-g])(?P<alter>[\#|b])?(?P<octave>\d)", value)) is not None:
            note = m.group('note').lower()
            alter = m.group('alter')
            octave = int(m.group('octave'))
            freq = cls._getNoteNumber(note, octave, alter)
            return freq
        else:
            return False
        
    @staticmethod
    def _getNoteNumber(note, octave, alter=None) -> int:
        """ Get note number as difference from A4 """
        
        octaveDiff = octave - 4
        notes = {"a":0, "b":2, "c":-9, "d":-7, "e":-5, "f":-4, "g":-2}
        
        k = notes[note] + (octaveDiff * 12)
        if alter == "#":
            k += 1
        elif alter == "b":
            k -= 1
            
        return k
    
    @property
    def value(self) -> np.ndarray:
        """ Return numpy array of frequencies """
        k0, k1 = sorted([info.k for info in self.widgets.values()])
        k1 += 1
        f = np.array([440*2**k for k in range(k0, k1)])
        return f