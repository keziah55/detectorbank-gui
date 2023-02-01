#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 18:04:03 2022

@author: keziah
"""
from qtpy.QtWidgets import QLabel
from qtpy.QtCore import Qt
from customQObjects.widgets import SpinBox, DoubleSpinBox
from .abstractpage import AbstractPage, RightLabel
import numpy as np

class EquationPage(AbstractPage):
    """ Widget to set frequency equation variables """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, name="frequencies", **kwargs)
        
        self.equationLabel = QLabel()
        self.equationLabel.setAlignment(Qt.AlignCenter)

        refFreqLabel = RightLabel("Ref. frequency:")
        self.refFreqBox = DoubleSpinBox()
        self.refFreqBox.setMaximum()
        self.refFreqBox.setValue(440)
        self.refFreqBox.setSuffix(" Hz")
        
        edoLabel = RightLabel("EDO:")
        self.edoBox = SpinBox()
        self.edoBox.setValue(12)
        
        n0Label = RightLabel("n0:")
        self.n0Box = SpinBox()
        self.n0Box.setRange()
        self.n0Box.setValue(-12)
        
        n1Label = RightLabel("n1:")
        self.n1Box = SpinBox()
        self.n1Box.setRange()
        self.n1Box.setValue(12)
        
        self._valueChanged()
        
        widgets = [(refFreqLabel, self.refFreqBox),
                   (edoLabel, self.edoBox), 
                   (n0Label, self.n0Box), 
                   (n1Label, self.n1Box)]
        
        for box in [item[1] for item in widgets]:
            box.valueChanged.connect(self._valueChanged)
        
        self.layout.addWidget(self.equationLabel, 0, 0, 1, 2)
        for row, ws in enumerate(widgets):
            for col, w in enumerate(ws):
                self.layout.addWidget(w, row+1, col)
        self.layout.addWidget(self.doneButton, row+2, 0, 1, 2)
        self.layout.setRowStretch(row+3, 10)
        
    def _getValues(self):
        freq = float(self.refFreqBox.value())
        edo = int(self.edoBox.value())
        n0, n1 = sorted([int(box.value()) for box in [self.n0Box, self.n1Box]])
        n1 += 1
        return freq, edo, n0, n1
        
    def _valueChanged(self):
        freq, edo, n0, n1 = self._getValues()
        n1 -= 1
        f0 = freq * 2**(n0/edo)
        f1 = freq * 2**(n1/edo)
        self.equationLabel.setText(f"{freq:g} * 2^({n0}/{edo}) = {f0:g} Hz\n{freq:g} * 2^({n1}/{edo}) = {f1:g} Hz")
        
    @property
    def value(self) -> np.ndarray:
        """ Return numpy array of frequencies """
        freq, edo, n0, n1 = self._getValues()
        f = np.array([freq*2**(n/edo) for n in range(n0, n1)])
        return f