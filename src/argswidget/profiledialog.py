#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogs to select profile to load or choose name to save.
"""
from qtpy.QtWidgets import QDialog, QRadioButton, QVBoxLayout, QDialogButtonBox
from customQObjects.widgets import GroupBox
from bs4 import BeautifulSoup
import os.path

class LoadDialog(QDialog):
    def __init__(self, *args, currentProfile=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.okButton =  self.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.clicked.connect(self.accept)
        cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        cancelButton.clicked.connect(self.reject)
        
        self.profileGroup = GroupBox("Profiles")
        self._buttons = {}
        
        with open(os.path.expanduser("~/.config/hopfskipjump.xml")) as fileobj:
            soup = BeautifulSoup(fileobj, "xml")
        profiles = [p['name'] for p in soup.find_all("profile")]
        
        for profile in profiles:
            button = QRadioButton(profile)
            if profile == currentProfile:
                button.setChecked(True)
            self.profileGroup.addWidget(button)
            self._buttons[profile] = button
        
        layout = QVBoxLayout()
        layout.addWidget(self.profileGroup)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("Select profile")
        
    def getProfileName(self):
        """ Return name of selected profile """
        for name, button in self._buttons.items():
            if button.isChecked():
                return name

class SaveDialog(QDialog):
    def getProfileName(self):
        pass