#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget allowing users to select start and stop notes and return the resultant
range of frequencies.
"""

from qtpy.QtWidgets import QLineEdit, QWidget, QLabel
from qtpy.QtCore import QTimer
from qtpy.QtGui import QPalette, QColor
from .abstractpage import AbstractPage, RightLabel
import numpy as np
import re
from dataclasses import dataclass

@dataclass
class NoteRangeInfo:
    """ Data class storing the widgets for a single note selector """
    name: str
    n: int = None
    valid: bool = True
    invalidColour: str = "#ff0000"
    
    def __post_init__(self):
        self.label = RightLabel(self.name)
        self.edit = QLineEdit()
        self.freqLabel = QLabel()
        palette = self.edit.palette()
        self.palettes = {"valid":QPalette(palette), "invalid":QPalette(palette)}
        invalidColour = QColor(self.invalidColour)
        self.palettes["invalid"].setColor(QPalette.Base, invalidColour)
    
    def setN(self, n):
        """ Set note number, relative to A4=440Hz """
        self.n = n
        if n is not None:
            self.freq = 440*2**(n/12)
            self.freqLabel.setText(f"{self.freq:g} Hz")
        else:
            self.freq = None
            self.freqLabel.setText(" Hz")
        
    def setValid(self, valid):
        """ Set palette according to `valid` """
        self.valid = valid
        key = 'valid' if valid else 'invalid'
        self.edit.setPalette(self.palettes[key])
        
    @property
    def widgets(self):
        """ Return widgets managed by this class """
        return [self.label, self.edit, self.freqLabel]
    

class NoteRangePage(AbstractPage):
    """ Widget """
    
    def __init__(self, *args, defaultStart="A0", defaultEnd="C8", invalidColour="#ff0000", **kwargs):
        super().__init__(*args, name="frequencies", **kwargs)
        
        # two lines edits, with labels
        self.widgets = {"start":NoteRangeInfo("Start note:", invalidColour=invalidColour),
                        "end":NoteRangeInfo("End note:", invalidColour=invalidColour)}
        
        # validate and update widgets 100ms after note changed
        self.timers = {}
        for key in self.widgets:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.setInterval(100)
            self.timers[key] = timer
            
        self.timers["start"].timeout.connect(lambda: self._textChanged("start"))
        self.timers["end"].timeout.connect(lambda: self._textChanged("end"))
            
        self.widgets["start"].edit.textChanged.connect(self.timers["start"].start)
        self.widgets["end"].edit.textChanged.connect(self.timers["end"].start)
        
        for row, info in enumerate(self.widgets.values()):
            col = 0
            for widget in info.widgets:
                if isinstance(widget, QWidget):
                    self.layout.addWidget(widget, row, col)
                    col += 1
        self.layout.addWidget(self.doneButton, row+1, 0, 1, 3)
        self.layout.setRowStretch(row+2, 10)
        
        self.widgets["start"].edit.setText(defaultStart)
        self.widgets["end"].edit.setText(defaultEnd)
        
    @property
    def isValid(self):
        """ Return True if both edits contain valid notes """
        return self.widgets["start"].valid and self.widgets["end"].valid
        
    def _textChanged(self, which):
        """ Validate the changed value and update labels """
        text = self.widgets[which].edit.text()
        if (n := self._validate(text)) is not False:
            self.widgets[which].setValid(True)
            self.widgets[which].setN(n)
        else:
            self.widgets[which].setValid(False)
            self.widgets[which].setN(None)
            
        self.valid.emit(self.isValid)
        
    @classmethod
    def _validate(cls, value):
        """ If `value` is a string that can be converted into a frequency, return 
            the frequency.
            
            Otherwise return False.
            
            The valid format is a letter 'A-G', an optional flat or sharp 'b' or '#'
            and an octave number.
        """
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
        n = notes[note] + (octaveDiff * 12)
        if alter == "#":
            n += 1
        elif alter == "b":
            n -= 1
        return n
    
    @property
    def value(self) -> np.ndarray:
        """ Return numpy array of frequencies """
        n0, n1 = sorted([info.n for info in self.widgets.values()])
        n1 += 1
        f = np.array([440*2**(n/12) for n in range(n0, n1)])
        return f