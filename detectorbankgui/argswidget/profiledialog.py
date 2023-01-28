#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogs to select profile to load or choose name to save.
"""
from qtpy.QtWidgets import (QDialog, QVBoxLayout, QDialogButtonBox,
                            QLineEdit, QLabel, QListWidget, QScrollArea)
from qtpy.QtCore import QTimer
from ..profilemanager import ProfileManager

class SaveDialog(QDialog):
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
            
        # buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
            
        layout = QVBoxLayout()
        layout.addWidget(self.nameScroll)
        layout.addWidget(self.nameEdit)
        layout.addWidget(self.label)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("Save profile")
        
    def getProfileName(self) -> str:
        """ Return chosen profile name """
        return self.nameEdit.text().strip()
    
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