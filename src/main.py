#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 14:31:04 2022

@author: keziah
"""
from qtpy.QtWidgets import QMainWindow, QVBoxLayout
from .audioplot import AudioPlotWidget

class DBGui(QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.audioplot = AudioPlotWidget(self)
        
        self.setCentralWidget(self.audioplot)