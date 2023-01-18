#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogs to select profile to load or choose name to save.
"""
from qtpy.QtWidgets import (QDialog, QRadioButton, QVBoxLayout, QDialogButtonBox,
                            QLineEdit, QLabel, QListWidget, QScrollArea)
from qtpy.QtCore import QTimer
from customQObjects.widgets import GroupBox
from ..profilemanager import ProfileManager

class _ProfileDialog(QDialog):
    def __init__(self, *args, currentProfile=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)

class LoadDialog(_ProfileDialog):
    def __init__(self, *args, currentProfile=None, **kwargs):
        super().__init__(*args, currentProfile=currentProfile, **kwargs)
        
        self.profileGroup = GroupBox("Profiles")
        self._buttons = {}
        
        for profile in ProfileManager().profiles:
            button = QRadioButton(profile)
            if profile == currentProfile:
                button.setChecked(True)
            self.profileGroup.addWidget(button)
            self._buttons[profile] = button
        
        layout = QVBoxLayout()
        layout.addWidget(self.profileGroup)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("Load profile")
        
    def getProfileName(self):
        """ Return name of selected profile """
        for name, button in self._buttons.items():
            if button.isChecked():
                return name

class SaveDialog(_ProfileDialog):
    def __init__(self, *args, currentProfile=None, **kwargs):
        super().__init__(*args, currentProfile=currentProfile, **kwargs)
        
        self.nameList = QListWidget()
        self.nameScroll = QScrollArea()
        self.nameScroll.setWidget(self.nameList)
        self.nameScroll.setWidgetResizable(True)
        
        self.nameList.addItems(ProfileManager().profiles)
        self.nameList.itemClicked.connect(self._listClicked)
        
        self.nameEdit = QLineEdit()
        self.label = QLabel()
        
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._validate)
        self.nameEdit.textChanged.connect(self._timer.start)
        
        if currentProfile is not None:
            self.nameEdit.setText(currentProfile)
            self._validate(currentProfile)
            
        layout = QVBoxLayout()
        layout.addWidget(self.nameScroll)
        layout.addWidget(self.nameEdit)
        layout.addWidget(self.label)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("Save profile")
        
    def getProfileName(self):
        return self.nameEdit.text()
    
    def _validate(self, name=None):
        if name is None:
            name = self.nameEdit.text()
        if (exists := name in ProfileManager().profiles):
            self.label.setText(f"Profile '{name}' already exists.\nDo you want to overwrite it?")
        else:
            self.label.setText("")
        return exists
    
    def _listClicked(self, item):
        name = item.text()
        self.nameEdit.setText(name)