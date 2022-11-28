#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form to edit DetectorBank args
"""
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QDialog, 
                            QGridLayout, QScrollArea, QSizePolicy, QMessageBox)
from qtpy.QtCore import Qt, Slot, Signal
from customQObjects.widgets import ElideMixin, GroupBox
from .valuewidgets import ValueLabel, ValueComboBox, ValueSpinBox, ValueDoubleSpinBox
from .frequencydialog import FrequencyDialog
from .profiledialog import LoadDialog, SaveDialog
from ..profilemanager import ProfileManager
import numpy as np
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

class FreqBwButton(ElideMixin, QPushButton):
    
    valueChanged = Signal()
    
    def __init__(self, *args, **kwargs):
        super(). __init__(*args, **kwargs)
        self._dialog = FrequencyDialog()
        self.clicked.connect(self._showDialog)
        
    @property
    def value(self):
        return self._dialog.values
    
    def setValue(self, detChars):
        self._dialog.setValues(detChars)
        self.setText(self._dialog.valuesStr)
    
    def _showDialog(self):
        reply = self._dialog.exec_()
        if reply == QDialog.Accepted:
            if self._dialog.valuesStr is not None:
                self.setText(self._dialog.valuesStr)
                self.valueChanged.emit()
                
class ProfileLabel(QLabel):
    def __init__(self, *args, name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setName(name)
        
    def setName(self, name):
        if name is None:
            name = ""
        self._name = name
        self.setText(f"Name: {name}")
        self.setToolTip(f"Current profile: {name}")
        
    def profileAltered(self):
        if self._name:
            text = f"Name: <i>{self._name}</i>"
            self.setText(text)
            self.setToolTip("Profile altered by user")

class ArgsWidget(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.widget = _AbsZArgsWidget(*args, **kwargs)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        
    def __getattr__(self, name):
        return getattr(self.widget, name)
    
class _AbsZArgsWidget(QWidget):
    def __init__(self, parent=None, sr=None, profile=None, numThreads=None, freq=None, 
                 bw=None, method=None, freqNorm=None, ampNorm=None, damping=None, gain=None):
        super().__init__(parent)
        
        self.srWidget = ValueLabel(suffix=" Hz")
        self.threadsWidget = ValueSpinBox()
        self.freqBwWidget = FreqBwButton()
        self.freqBwWidget.setText("Select frequencies and bandwidths")
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
                "sr", self.srWidget, "Sample rate", "Sample rate of audio file", float), 
            "numThreads":Parameter(
                "numThreads", self.threadsWidget, "Threads", 
                "Maximum number of threads to execute concurrently to determine the detector outputs. "
                "Passing a value of less than 1 causes the number of threads to "
                "be set according to the number of reported CPU cores",
                int), 
            "detChars":Parameter(
                "detChars", self.freqBwWidget, "Frequencies and bandwidths", "Detector characteristics"),
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
            param.widget.valueChanged.connect(self._valueChanged)
        form.setRowStretch(row+1, 10)
        
        self.restoreDefaultsButton = QPushButton("Restore defaults")
        self.loadProfileButton = QPushButton("Load")
        self.saveProfileButton = QPushButton("Save")
        self.currentProfileLabel = ProfileLabel()
        
        self._ignoreValueChanged = False
        self._profile = None
        self.loadProfileButton.clicked.connect(self.loadProfile)
        self.saveProfileButton.clicked.connect(self.saveProfile)
        
        self.restoreDefaultsButton.clicked.connect(self._setDefaults)
        
        profileGroup = GroupBox("Profile", layout="hbox")
        for button in [self.currentProfileLabel, self.saveProfileButton, self.loadProfileButton]:
            profileGroup.addWidget(button)
            
        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(profileGroup)
        
        layout.addWidget(self.restoreDefaultsButton)
            
        self.setLayout(layout)
        
        self._setDefaults()
        
    @property
    def currentProfile(self):
        return self._profile
    
    @currentProfile.setter
    def currentProfile(self, name):
        self._profile = name
        if name is not None:
            self.currentProfileLabel.setName(name)
        else:
            self.currentProfileLabel.profileAltered()
        
    @Slot()
    def _valueChanged(self):
        if not self._ignoreValueChanged:
            self.currentProfileLabel.profileAltered()
        
    def loadProfile(self):
        dialog = LoadDialog(parent=self, currentProfile=self._profile)
        reply = dialog.exec_()
        if reply == QDialog.Accepted:
            self._loadProfile(dialog.getProfileName())
    
    def saveProfile(self):
        dialog = SaveDialog(parent=self)
        reply = dialog.exec_()
        if reply == QDialog.Accepted:
            self._saveProfile(dialog.getProfileName())
    
    def _loadProfile(self, profile):
        self.currentProfile = profile
        
        prof = ProfileManager().getProfile(profile)
        keys = ["sr", "damping", "gain", "numThreads", "detChars"]
        params = {key:prof.value(key) for key in keys}
        method, freqNorm, ampNorm = prof.value("features")
        params["method"] = method,
        params["freqNorm"] = freqNorm,
        params["ampNorm"]  =ampNorm,
        
        self._ignoreValueChanged = True
        self.setParams(**params)
        self._ignoreValueChanged = False
    
    def _saveProfile(self, name):
        params, invalid = self.getArgs()
        if len(invalid) > 0:
            QMessageBox.warning(self, "Cannot save profile", 
                                f"The following arg(s) are invalid: {', '.join(invalid)}.\n"
                                "Please set valid values and try again.")
            return
            
        features = params['method'] | params['freqNorm'] | params['ampNorm']
        audio = np.zeros(1)
        args = (params['sr'], audio, params['numThreads'], params['detChars'], 
                features, params['damping'], params['gain'])
        det = DetectorBank(*args)
        det.saveProfile(name)
        
    def setParams(self, **kwargs):
        """ Set arg value in form """
        for name, value in kwargs.items():
            if (param := self.widgets.get(name, None)) is not None:
                param.widget.setValue(value)
    
    def getArgs(self) -> tuple[dict, list]:
        """ Return dict of DetectorBank args and list of any invalid args.
        
            If any arg is None, it will be considered invalid.
        """
        ret = {}
        invalid = []
        for name, param in self.widgets.items():
            try:
                value = param.value
            except ValueError:
                value = None
            ret[name] = value
            if value is None:
                invalid.append(param.prettyName)
        return ret, invalid
    
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