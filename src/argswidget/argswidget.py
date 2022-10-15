#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form to edit DetectorBank args
"""
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                            QGridLayout, QScrollArea, QDialog)
from qtpy.QtCore import Qt
from customQObjects.widgets import ElideLabel
from .valuewidgets import (ValueLabel, ValueLineEdit, ValueComboBox, ValueSpinBox,
                           ValueDoubleSpinBox)
from .frequencydialog import FrequencyDialog
from .profiledialog import LoadDialog, SaveDialog
from detectorbank import DetectorBank
import os
from dataclasses import dataclass
from collections import namedtuple

@dataclass
class Parameter:
    name: str
    widget: QWidget # must have `value` property
    prettyName: str = None
    toolTip: str = None
    castType: object = None

    def __post_init__(self):
        if self.prettyName is None:
            self.prettyName = self.name
        self.label = QLabel(self.prettyName)
        self.label.setAlignment(Qt.AlignRight)
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

class ArgsWidget(QScrollArea):
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
        
        self.srWidget = ValueLabel(suffix=" Hz")
        self.threadsWidget = ValueSpinBox()
        self.freqWidget = ElideLabel("Select frequencies and bandwidths")
        self.bwWidget = ElideLabel("Select frequencies and bandwidths")
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
        
        self._freqBwDialog = FrequencyDialog()
        
        self.freqWidget.clicked.connect(self._showFreqBwDialog)
        self.bwWidget.clicked.connect(self._showFreqBwDialog)
        self.dampingWidget.setSingleStep(0.0001)
        self.dampingWidget.setDecimals(5)
        
        # make dict of widgets
        # Parameter objects automatically make labels and set tool tips
        self.widgets = {
            "sr":Parameter(
                "sr", self.srWidget, "Sample rate", "Sample rate of audio file", float), 
            "numThreads":Parameter(
                "numThreads", self.threadsWidget, "Threads", 
                "Number of threads to execute concurrently to determine the detector outputs. "
                "Passing a value of less than 1 causes the number of threads to "
                "be set according to the number of reported CPU cores",
                int), 
            "freqs":Parameter(
                "freqs", self.freqWidget, "Frequencies", "Frequencies to detect"),
            "bws":Parameter(
                "bws", self.bwWidget, "Bandwidths", "Bandwidth(s) of detectors"),
            "damping":Parameter(
                "damping", self.dampingWidget, "Damping", 
                "Damping factor for all detectors. Default is 0.0001. "
                "Sensible range is between 0.0001 and 0.0005",
                float),
            "gain":Parameter(
                "gain", self.gainWidget, "Gain", "Gain applied to output. Default is 25", float),
            "method":Parameter("method", self.methodWidget, "Numerical method", 
                               "Numerical method used to solve equation. "
                               "Default is fourth order Runge-Kutta"),
            "freqNorm":Parameter("freqNorm", self.freqNormWidget, "Frequency normalization", 
                                 "Whether to normalize frequency. Default is unnormalized"),
            "ampNorm":Parameter("ampNorm", self.ampNormWidget, "Amplitude normalization", 
                                "Whether to normalize amplitude response. Default is unnormalized")}
        
        form = QGridLayout()
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
        
        
    # TODO load and save from profile
    def loadProfile(self):
        dialog = LoadDialog()
        reply = dialog.exec_()
        if reply == QDialog.Accecpted:
            self._loadProfile(dialog.getProfileName())
    
    def saveProfile(self):
        dialog = SaveDialog()
        reply = dialog.exec_()
        if reply == QDialog.Accecpted:
            self._saveProfile(dialog.getProfileName())
    
    def _loadProfile(self, profile):
        pass
    
    def _saveProfile(self, name):
        pass
    
    def _showFreqBwDialog(self):
        self._freqBwDialog.exec_()
    
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