#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 14:31:04 2022

@author: keziah
"""
from qtpy.QtWidgets import QMainWindow, QDockWidget
from qtpy.QtCore import Qt
from .audioplot import AudioPlotWidget

class DBGui(QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.audioplot = AudioPlotWidget(self)
        
        self.docks = {}
        
        for name, widget in [('Audio Input', self.audioplot)]:
            dockwidget = QDockWidget(name)
            dockwidget.setWidget(widget)
            self.addDockWidget(Qt.LeftDockWidgetArea, dockwidget)