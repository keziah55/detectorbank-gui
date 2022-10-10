#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 18:28:38 2022

@author: keziah
"""
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QFormLayout, QSpinBox, QDoubleSpinBox, QScrollArea)
from qtpy.QtCore import Qt
from .valuewidgets import ValueLabel, ValueLineEdit, ValueComboBox
from detectorbank import DetectorBank
import os

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
        # num threads (combobox)
        # frequencies
        # bandwidths
        # numerical method
        # freq norm
        # amp norm
        # damping
        # gain
        
        form = QFormLayout()
        
        self.srWidget = ValueLabel()
        self.threadsWidget = QSpinBox()
        self.freqWidget = ValueLineEdit()
        self.bwWidget = ValueLineEdit()
        self.dampingWidget = QDoubleSpinBox()
        self.gainWidget = QDoubleSpinBox()
        self.methodWidget = ValueComboBox()
        self.freqNormWidget = ValueComboBox()
        self.ampNormWidget = ValueComboBox()
        
        self.methodWidget.addItems(["Fourth order Runge-Kutta", "Central difference"])
        self.freqNormWidget.addItems(["Unnormalized", "Search normalized"])
        self.ampNormWidget.addItems(["Unnormalized", "Normalized"])
        
        self.srWidget.setToolTip("Sample rate of audio file")
        self.threadsWidget.setToolTip("Number of threads to execute concurrently to determine "
                                      "the detector outputs. Passing a value of less than 1 causes the number "
                                      "of threads to be set according to the number of reported CPU cores")
        self.freqWidget.setToolTip("Frequencies to detect")
        self.bwWidget.setToolTip("Bandwidth(s) of detectors")
        self.dampingWidget.setToolTip("Damping factor for all detectors. Default is 0.0001. Sensible range is between 0.0001 and 0.0005")
        self.gainWidget.setToolTip("Gain applied to output. Default is 25")
        self.methodWidget.setToolTip("Numerical method used to solve equation. Default is fourth order Runge-Kutta")
        self.freqNormWidget.setToolTip("Whether to normalize frequency. Default is unnormalized")
        self.ampNormWidget.setToolTip("Whether to normalize amplitude response. Default is unnormalized")
        
        self.dampingWidget.setSingleStep(0.0001)
        self.dampingWidget.setDecimals(5)
        
        self.widgets = {"sr":(self.srWidget, "Sample rate"), 
                        "numThreads":(self.threadsWidget, "Threads"), 
                        "freqs":(self.freqWidget, "Frequencies"),
                        "bws":(self.bwWidget, "Bandwidths"),
                        "damping":(self.dampingWidget, "Damping"),
                        "gain":(self.gainWidget, "Gain"),
                        "method":(self.methodWidget, "Numerical method"),
                        "freqNorm":(self.freqNormWidget, "Frequency normalization"),
                        "ampNorm":(self.ampNormWidget, "Amplitude normalization")}
        
        for widget, label in self.widgets.values():
            form.addRow(label, widget)
            labelWidget = form.labelForField(widget)
            labelWidget.setToolTip(widget.toolTip())
        
        self.restoreDefaultsButton = QPushButton("Restore defaults")
        self.loadProfileButton = QPushButton("Load profile")
        self.saveProfileButton = QPushButton("Save profile")
        
        buttonLayout = QHBoxLayout()
        for button in [self.restoreDefaultsButton, self.loadProfileButton, self.saveProfileButton]:
            buttonLayout.addWidget(button)
            
        layout = QVBoxLayout()
        layout.addLayout(buttonLayout)
        layout.addLayout(form)
            
        self.setLayout(layout)
        
        self._setDefaults()
        
        
    def loadProfile(self, profile):
        pass
    
    def setParams(self, **kwargs):
        for name, value in kwargs.items():
            if (tup := self.widgets.get(name, None)) is not None:
                widget = tup[0]
                widget.setValue(value)
    
    def getArgs(self) -> dict:
        """ Return dict of DetectorBank args """
        pass
    
    def _setDefaults(self):
        
        # sample rate is set by loading audio file, not by user directly
        self.srWidget.setText("")
        
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