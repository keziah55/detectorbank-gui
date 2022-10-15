#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 18:04:03 2022

@author: keziah
"""
from qtpy.QtWidgets import QGridLayout, QWidget, QLabel, QSpinBox, QDoubleSpinBox
from qtpy.QtCore import Qt
from .abstractfrequencypage import AbstractFrequencyPage
import numpy as np

class EquationPage(AbstractFrequencyPage):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.equationLabel = QLabel()
        self.equationLabel.setAlignment(Qt.AlignCenter)

        refFreqLabel = QLabel("Ref. frequency:")
        refFreqLabel.setAlignment(Qt.AlignRight)
        self.refFreqBox = QDoubleSpinBox()
        self.refFreqBox.setMaximum(240000)
        self.refFreqBox.setValue(440)
        self.refFreqBox.setSuffix(" Hz")
        
        edoLabel = QLabel("EDO:")
        edoLabel.setAlignment(Qt.AlignRight)
        self.edoBox = QSpinBox()
        self.edoBox.setValue(12)
        
        n0Label = QLabel("n0:")
        n0Label.setAlignment(Qt.AlignRight)
        self.n0Box = QSpinBox()
        self.n0Box.setRange(-1000, 1000)
        self.n0Box.setValue(-12)
        
        n1Label = QLabel("n1:")
        n1Label.setAlignment(Qt.AlignRight)
        self.n1Box = QSpinBox()
        self.n1Box.setRange(-1000, 1000)
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
        self.equationLabel.setText(f"{freq:g} * 2^({n0}/{edo}) = {f0:g} Hz\n{freq:g} * 2^({n1}/{edo}) = {f1:g} HZ")
        
    @property
    def value(self) -> np.ndarray:
        """ Return numpy array of frequencies """
        freq, edo, n0, n1 = self._getValues()
        f = np.array([freq*2**(n/edo) for n in range(n0, n1)])
        return f