#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 18:28:38 2022

@author: keziah
"""
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                            QGridLayout, QScrollArea)
from qtpy.QtCore import Qt
from .valuewidgets import (ValueLabel, ValueLineEdit, ValueComboBox, ValueSpinBox,
                           ValueDoubleSpinBox)
from detectorbank import DetectorBank
import os
from dataclasses import dataclass
from collections import namedtuple

@dataclass
class Parameter:
    name : str
    prettyName : str
    widget : QWidget # must have `value` property
    toolTip : str = None
    castType: object = None

    def __post_init__(self):
        self.label = QLabel(self.prettyName)
        for widget in [self.label, self.widget]:
            widget.setToolTip(self.toolTip)
        
    @property
    def value(self):
        """ Return value, cast to type if `castType` is not None """
        value = self.widget.value
        if self.castType is not None:
            return self.castType(value)
        else:
            return value
        
Feature = namedtuple("Feature", ["name", "value"]) # used when making combobox of DB features

class AbsZArgsWidget(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.widget = _AbsZArgsWidget(*args, **kwargs)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
    def __getattr__(self, name):
        return getattr(self.widget, name)

class _AbsZArgsWidget(QWidget):
    def __init__(self, parent=None, sr=None, profile=None, numThreads=None, freq=None, 
                 bw=None, method=None, freqNorm=None, ampNorm=None, damping=None, gain=None):
        super().__init__(parent)
        
        # sr (read only)
        # num threads
        # frequencies
        # bandwidths
        # numerical method
        # freq norm
        # amp norm
        # damping
        # gain
        
        form = QGridLayout()
        
        self.srWidget = ValueLabel(suffix=" Hz")
        self.threadsWidget = ValueSpinBox()
        self.freqWidget = ValueLineEdit()
        self.bwWidget = ValueLineEdit()
        self.dampingWidget = ValueDoubleSpinBox()
        self.gainWidget = ValueDoubleSpinBox()
        self.methodWidget = ValueComboBox(
            values=[Feature("Fourth order Runge-Kutta", DetectorBank.runge_kutta),
                    Feature("Central difference", DetectorBank.central_difference)])
        self.freqNormWidget = ValueComboBox(
            values=[Feature("Unnormalized", DetectorBank.freq_unnormalized),
                    Feature("Search normalized", DetectorBank.search_normalized)])
        self.ampNormWidget = ValueComboBox(
            values=[Feature("Unnormalized", DetectorBank.amp_unnormalized),
                    Feature("Normalized", DetectorBank.amp_normalized)])
        
        self.dampingWidget.setSingleStep(0.0001)
        self.dampingWidget.setDecimals(5)
        
        # make dict of widgets
        # Parameter objects automatically make labels and set tool tips
        self.widgets = {
            "sr":Parameter(
                "sr", "Sample rate", self.srWidget, "Sample rate of audio file", float), 
            "numThreads":Parameter(
                "numThreads", "Threads", self.threadsWidget, 
                "Number of threads to execute concurrently to determine the detector outputs. "
                "Passing a value of less than 1 causes the number of threads to "
                "be set according to the number of reported CPU cores",
                int), 
            "freqs":Parameter(
                "freqs", "Frequencies", self.freqWidget, "Frequencies to detect"),
            "bws":Parameter(
                "bws", "Bandwidths", self.bwWidget, "Bandwidth(s) of detectors"),
            "damping":Parameter(
                "damping", "Damping", self.dampingWidget, 
                "Damping factor for all detectors. Default is 0.0001. "
                "Sensible range is between 0.0001 and 0.0005",
                float),
            "gain":Parameter(
                "gain", "Gain", self.gainWidget, "Gain applied to output. Default is 25", float),
            "method":Parameter("method", "Numerical method", self.methodWidget, 
                               "Numerical method used to solve equation. "
                               "Default is fourth order Runge-Kutta"),
            "freqNorm":Parameter("freqNorm", "Frequency normalization", self.freqNormWidget, 
                                 "Whether to normalize frequency. Default is unnormalized"),
            "ampNorm":Parameter("ampNorm", "Amplitude normalization", self.ampNormWidget, 
                                "Whether to normalize amplitude response. Default is unnormalized")}
        
        for row, param in enumerate(self.widgets.values()):
            form.addWidget(param.label, row, 0)
            form.addWidget(param.widget, row, 1)
        form.setRowStretch(row+1, 10)
        
        self.restoreDefaultsButton = QPushButton("Restore defaults")
        self.loadProfileButton = QPushButton("Load profile")
        self.saveProfileButton = QPushButton("Save profile")
        
        self.restoreDefaultsButton.clicked.connect(self._setDefaults)
        
        buttonLayout = QHBoxLayout()
        for button in [self.loadProfileButton, self.saveProfileButton]:
            buttonLayout.addWidget(button)
            
        layout = QVBoxLayout()
        layout.addLayout(buttonLayout)
        layout.addLayout(form)
        layout.addWidget(self.restoreDefaultsButton)
            
        self.setLayout(layout)
        
        self._setDefaults()
        
    def loadProfile(self, profile):
        pass
    
    def setParams(self, **kwargs):
        """ Set arg value in form """
        for name, value in kwargs.items():
            if (param := self.widgets.get(name, None)) is not None:
                param.widget.setValue(value)
    
    def getArgs(self) -> dict:
        """ Return dict of DetectorBank args """
        ret = {}
        for name, param in self.widgets.items():
            ret[name] = param.value
        return ret
    
    def _setDefaults(self):
        
        # num threads
        numCores = os.cpu_count()
        self.threadsWidget.setMinimum(1)
        self.threadsWidget.setMaximum(numCores)
        self.threadsWidget.setValue(numCores)
        
        # damping
        self.dampingWidget.setValue(0.0001)
        
        # gain
        self.gainWidget.setValue(25)
        
        # features
        for widget in [self.methodWidget, self.freqNormWidget, self.ampNormWidget]:
            widget.setCurrentIndex(0)