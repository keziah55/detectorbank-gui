#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple About dialog
"""
from qtpy.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QLabel
from qtpy.QtGui import QPixmap
from qtpy.QtCore import Qt
from pathlib import Path

class AboutDialog(QDialog):
    def __init__(self, msg, image=None):
        super().__init__()
        
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        okButton =  buttonBox.button(QDialogButtonBox.Ok)
        okButton.clicked.connect(self.accept)
        
        msg = QLabel(msg)
        msg.setAlignment(Qt.AlignCenter)
        
        layout = QVBoxLayout()
        layout.addWidget(msg)
        if image is not None:
            if isinstance(image, Path):
                image = str(image)
            pixmap = QPixmap(image)
            image = QLabel()
            image.setPixmap(pixmap)
            layout.addWidget(image)
        layout.addWidget(buttonBox)
        self.setLayout(layout)
        
        self.setWindowTitle("About DetectorBank GUI")