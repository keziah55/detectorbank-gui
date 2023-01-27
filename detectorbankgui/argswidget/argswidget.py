#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 16:18:14 2023

@author: keziah
"""
from qtpy.QtWidgets import QWidget, QHBoxLayout
from .detbankargs import DetBankArgsWidget
from .extraargs import ExtraOptionsWidget
from customQObjects.widgets import HSplitter

class ArgsWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.detbankargs = DetBankArgsWidget()
        self.extraargs = ExtraOptionsWidget()
        
        spliter = HSplitter()
        for widget in [self.detbankargs, self.extraargs]:
            spliter.addWidget(widget)
        
        layout = QHBoxLayout()
        layout.addWidget(spliter)
        self.setLayout(layout)
        
    def __getattr__(self, name):
        if hasattr(self.detbankargs, name):
            return getattr(self.detbankargs, name)
        elif hasattr(self.extraargs, name):
            return getattr(self.extraargs, name)
        else:
            raise AttributeError(f"ArgsWidget has no attribute {name}")
        
    def getDetBankArgs(self):
        return self.detbankargs.getArgs()
    
    def getExtraArgs(self):
        return self.extraargs.getArgs()