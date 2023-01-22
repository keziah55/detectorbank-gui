#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 16:18:14 2023

@author: keziah
"""
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                            QDialog, QFileDialog, QGridLayout, QScrollArea, QMessageBox)
from .detbankargs import DetBankArgsWidget
from .extraargs import ExtraOptionsWidget

class ArgsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.detbankargs = DetBankArgsWidget()
        self.extraargs = ExtraOptionsWidget()
        
        layout = QHBoxLayout()
        for widget in [self.detbankargs, self.extraargs]:
            layout.addWidget(widget)
            
        self.setLayout(layout)