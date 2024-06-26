#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form to edit DetectorBank args
"""
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QDialog, 
                            QSizePolicy, QScrollArea, QMessageBox, QSpinBox, QCheckBox)
from qtpy.QtCore import Qt, Slot, Signal
from customQObjects.widgets import ElideMixin, GroupBox, ComboBox
from customQObjects.core import Settings
from customQObjects.gui import getIconFromTheme
from .valuewidgets import ValueLabel, ValueComboBox, ValueSpinBox, ValueDoubleSpinBox
from .frequencydialog import FrequencyDialog
from .profiledialog import SaveDialog
from ..profilemanager import ProfileManager
from ..invalidargexception import InvalidArgException
import numpy as np
from detectorbank import DetectorBank
import os
from dataclasses import dataclass
from collections import namedtuple

@dataclass
class Parameter:
    """ Dataclass to store form widgets and associated data """
    widget: QWidget # must have `value` property
    name: str
    toolTip: str = None
    castType: object = None

    def __post_init__(self):
        self.label = QLabel(self.name)
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
    """ Button to select/show frequencies and bandwidths 
    
        Has same API as 'value widgets'
    """
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
        self.valueChanged.emit()
    
    def _showDialog(self):
        reply = self._dialog.exec_()
        if reply == QDialog.Accepted:
            if self._dialog.valuesStr is not None:
                self.setText(self._dialog.valuesStr)
                self.valueChanged.emit()

class DetBankArgsWidget(QScrollArea):
    """ Scroll area containing DetectorBank args and additional options """
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.widget = _DetBankArgsWidget(*args, **kwargs)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
    def __getattr__(self, name):
        return getattr(self.widget, name)
    
class _DetBankArgsWidget(QWidget):
    """ Widget containing form for DetectorBank args, including loading and saving profiles """
    
    def __init__(self, parent=None):
        super().__init__(parent)
         
        # widgets are 'Value' widgets that have 'value' property, 'setValue' method
        # and 'valueChanged' signal
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
        
        numCores = os.cpu_count()
        self.threadsWidget.setMinimum(1)
        self.threadsWidget.setMaximum(numCores)
        self.threadsWidget.setValue(numCores)
        
        # make dict of widgets
        # Parameter objects automatically make labels and set tool tips
        self.widgets = {
            "sr":Parameter(
                self.srWidget, "Sample rate", "Sample rate of audio file", float), 
            "numThreads":Parameter(
                self.threadsWidget, "Threads", 
                "Maximum number of threads to execute concurrently to determine the detector outputs. "
                "Passing a value of less than 1 causes the number of threads to "
                "be set according to the number of reported CPU cores",
                int), 
            "detChars":Parameter(
                self.freqBwWidget, "Frequencies and bandwidths", "Detector characteristics"),
            "damping":Parameter(
                self.dampingWidget, "Damping", 
                "Damping factor for all detectors. Default is 0.0001. "
                "Sensible range is between 0.0001 and 0.0005",
                float),
            "gain":Parameter(
                self.gainWidget, "Gain", "Gain applied to output. Default is 25", float),
            "method":Parameter(
                self.methodWidget, "Numerical method", 
                "Numerical method used to solve equation. Default is fourth order Runge-Kutta"),
            "freqNorm":Parameter(
                self.freqNormWidget, "Frequency normalization", 
                "Whether to normalize frequency. Default is unnormalized"),
            "ampNorm":Parameter(
                self.ampNormWidget, "Amplitude normalization", 
                "Whether to normalize amplitude response. Default is unnormalized")
            }
        
        # profile widgets
        self.loadProfileBox = ComboBox()
        self.loadProfileBox.addItems(ProfileManager().profiles)
        
        self.reloadProfileButton = QPushButton()
        if (icon:=getIconFromTheme("view-refresh")) is not None:
            self.reloadProfileButton.setIcon(icon)
        else:
            self.reloadProfileButton.setText("Reload")
        self.reloadProfileButton.setEnabled(False)
        self.reloadProfileButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            
        profileLabel = QLabel("Profile")
        profileLabel.setAlignment(Qt.AlignRight)
        self.defaultCheckBox = QCheckBox("Set as default")
        self.defaultCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.defaultCheckBox.stateChanged.connect(self._defaultBoxClicked)
        
        self.saveProfileButton = QPushButton()
        if (icon:=getIconFromTheme("document-save")) is not None:
            self.saveProfileButton.setIcon(icon)
        else:
            self.saveProfileButton.setText("Save profile")
        self.saveProfileButton.setToolTip("Save current parameters as new profile")
        self.saveProfileButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            
        # group box of DetectorBank args
        detBankGroup = GroupBox("DetectorBank parameters", layout="grid")
        profileWidgets = [profileLabel, self.loadProfileBox, self.reloadProfileButton, 
                          self.defaultCheckBox, self.saveProfileButton]
        row = 0
        for col, widget in enumerate(profileWidgets):
            detBankGroup.addWidget(widget, row, col)
        colSpan = len(profileWidgets) - 1
        for row, param in enumerate(self.widgets.values()):
            row += 1
            detBankGroup.addWidget(param.label, row, 0, 1, 1)
            detBankGroup.addWidget(param.widget, row, 1, 1, colSpan)
            param.widget.valueChanged.connect(self._valueChanged)
        row += 1
            
        detBankGroup.layout.setRowStretch(row+1, 10)
        
        self._ignoreValueChanged = False
        self._profile = None
        self.currentProfileAltered = False
        self.loadProfileBox.currentTextChanged.connect(self._doLoadProfile)
        self.reloadProfileButton.clicked.connect(self.reloadProfile)
        self.saveProfileButton.clicked.connect(self._saveProfile)
            
        # additional args
        self.subsampleBox = QSpinBox()
        self.subsampleBox.setMinimum(1)
        self.subsampleBox.setMaximum(2**32//2-1) # essentially no max
        self.subsampleBox.valueChanged.connect(self._writeSubsampleFactor)
        self.subsampleBox.setToolTip("Factor by which to subsample the results when plotting")
        
        extraArgsGroup = GroupBox("Additional parameters", layout="grid")
        subsampleLabel = QLabel("Plot subsample factor")
        subsampleLabel.setAlignment(Qt.AlignRight)
        subsampleLabel.setToolTip(self.subsampleBox.toolTip())
        extraArgsGroup.addWidget(subsampleLabel, 0, 0)
        extraArgsGroup.addWidget(self.subsampleBox, 0, 1)
        
        layout = QVBoxLayout()
        layout.addWidget(detBankGroup)
        layout.addWidget(extraArgsGroup)
        
        self.setLayout(layout)
        
        self._ensureDefaultExists()
        
    @property
    def currentProfile(self):
        """ Return current profile name """
        return self._profile
    
    @currentProfile.setter
    def currentProfile(self, name):
        self._profile = name
        
    @property
    def currentProfileAltered(self):
        """ Return True if current profile has been altered by user """
        return self._currentProfileAltered
    
    @currentProfileAltered.setter
    def currentProfileAltered(self, value):
        self._currentProfileAltered = value
        self.reloadProfileButton.setEnabled(value)

    @Slot()
    def _valueChanged(self):
        """ Update `currentProfileAltered` unless ignore flag set """
        if not self._ignoreValueChanged:
            self.currentProfileAltered = True
        
    def _ensureDefaultExists(self):
        """ Create a 'default' profile, if necessary """
        if "default" not in ProfileManager().profiles:
            params = self._getDefaultArgs()
            self.saveProfile("default", params)
        
    def _saveProfile(self):
        """ Show save dialog and save profile """
        dialog = SaveDialog(parent=self)
        reply = dialog.exec_()
        if reply == QDialog.Accepted:
            name = dialog.getProfileName()
            if name: # if name is not empty string
                self.saveProfile(name)
        return name
    
    def _doLoadProfile(self, profile):
        """ Perform loading of `profile` """
        prof = ProfileManager().getProfile(profile)
        if prof is not None:
            keys = ["sr", "damping", "gain", "numThreads", "detChars"]
            params = {key:prof.value(key) for key in keys}
            method, freqNorm, ampNorm = prof.value("features")
            params["method"] = method
            params["freqNorm"] = freqNorm
            params["ampNorm"] = ampNorm
            
            self._ignoreValueChanged = True
            self.setParams(**params)
            self._ignoreValueChanged = False
            
            self.currentProfileAltered = False
    
    def loadProfile(self, profile):
        """ Load `profile` """
        self.currentProfile = profile
        if profile == "None":
            return
        self._doLoadProfile(profile)
        
    def reloadProfile(self):
        """ Reload current profile """
        self._doLoadProfile(self.currentProfile)
            
    def saveProfile(self, name, params=None):
        """ Save profile `param` with `name` 
        
            If `params` is None, the current args are used.
        """
        if params is None:
            try:
                params = self.getArgs()
            except InvalidArgException as exc:
                QMessageBox.warning(self, "Cannot save profile", str(exc))
                return
            
        features = params['method'] | params['freqNorm'] | params['ampNorm']
        audio = np.zeros(1)
        args = (params['sr'], audio, params['numThreads'], params['detChars'], 
                features, params['damping'], params['gain'])
        det = DetectorBank(*args)
        det.saveProfile(name)
        
        # add to profile list
        self.loadProfileBox.addItem(name)
        self.currentProfile = name
        
    def _defaultBoxClicked(self, state):
        """ If 'default' box checked, ensure the current profile is saved """
        if state == Qt.Checked:
            profileWritten = self._writeDefaultProfile()
            if not profileWritten:
                self.defaultCheckBox.setChecked(False)
        
    def _writeDefaultProfile(self):
        """ Write default profile name to config file. 
        
            If no profile is currently active, show the Save Profile dialog.
        """
        name = self.loadProfileBox.currentText()
        if name == "None":
            name = self._saveProfile()
        if name:
            settings = Settings()
            settings.setValue("params/defaultProfile", name)
            return True
        return False
        
    def setParams(self, **kwargs):
        """ Set arg value in form """
        if list(kwargs.keys()) == ['sr']:
            self._ignoreValueChanged = True
        for name, value in kwargs.items():
            if (param := self.widgets.get(name, None)) is not None:
                param.widget.setValue(value)
        self._ignoreValueChanged = False
    
    def getArgs(self) -> dict:
        """ Return dict of DetectorBank args.
        
            If any arg is None, it will be considered invalid and InvalidArgException
            will be raised.
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
                invalid.append(param.name)
        if len(invalid) > 0:
            msg = (f"The following arg(s) are invalid: {', '.join(invalid)}.\n"
                    "Please set valid values and try again.")
            raise InvalidArgException(msg)
        if ret['method'] == DetectorBank.central_difference and np.count_nonzero(ret['detChars'][:,1]) > 0:
            msg = "Central difference method can only be used with minimum bandwidth detectors (0Hz)"
            raise InvalidArgException(msg)
        return ret
    
    @staticmethod
    def _getDefaultArgs():
        """ Return dict of default values for all args """
        f = np.array([440*2**(k/12) for k in range(-48,40)])
        bw = np.zeros(len(f))
        detChars = np.column_stack((f,bw))
        
        params = {
            "sr":48000, 
            "numThreads":os.cpu_count(), 
            "detChars":detChars,
            "damping":0.0001,
            "gain":25,
            "method":DetectorBank.runge_kutta,
            "freqNorm":DetectorBank.freq_unnormalized,
            "ampNorm":DetectorBank.amp_unnormalized
            }
        return params
        
    def _writeSubsampleFactor(self):
        """ Write subsample value to config file """
        settings = Settings()
        settings.setValue("plot/subsample", self.subsampleBox.value())
        
    def setSubsampleFactor(self, subsample: int):
        """ Update 'subsample factor' box value """
        self.subsampleBox.setValue(subsample)
        
    def getSubsampleFactor(self) -> int:
        """ Return current 'subsample factor' box value """
        return int(self.subsampleBox.value())
    