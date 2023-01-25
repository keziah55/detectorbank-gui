#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogs to select profile to load or choose name to save, also with check box
to set this as the default profile.
"""
from qtpy.QtWidgets import (QDialog, QRadioButton, QVBoxLayout, QDialogButtonBox,
                            QLineEdit, QLabel, QListWidget, QScrollArea, QCheckBox)
from qtpy.QtCore import QTimer
from customQObjects.widgets import GroupBox
from ..profilemanager import ProfileManager

class _ProfileDialog(QDialog):
    def __init__(self, *args, currentProfile=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.defaultCheckBox = QCheckBox("Set as default")
        
        # buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
        
    def getProfileName(self) -> tuple[str, bool]:
        # abstract method
        raise NotImplementedError()

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
        layout.addWidget(self.defaultCheckBox)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("Load profile")
        
    def getProfileName(self) -> tuple[str, bool]:
        """ Return name of selected profile and whether to set this as the default """
        for name, button in self._buttons.items():
            if button.isChecked():
                break
        return name, self.defaultCheckBox.isChecked()

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
        layout.addWidget(self.defaultCheckBox)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("Save profile")
        
    def getProfileName(self) -> tuple[str, bool]:
        """ Return chosen profile name and whether to set as default profile """
        return self.nameEdit.text().strip(), self.defaultCheckBox.isChecked()
    
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