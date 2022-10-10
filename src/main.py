#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 14:31:04 2022

@author: keziah
"""
from qtpy.QtWidgets import QMainWindow, QDockWidget, QAction, QFileDialog
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon, QKeySequence
from .audioplot import AudioPlotWidget
import os

class DBGui(QMainWindow):
    
    def __init__(self, *args, audioFile=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.audioplot = AudioPlotWidget(self)
        if audioFile is not None:
            self.audioplot.openAudio(audioFile)
        
        self.createActions()
        self.connectActions()
        self.createToolBars()
        
        for name, widget in [('Audio Input', self.audioplot)]:
            dockwidget = QDockWidget(name)
            dockwidget.setWidget(widget)
            self.addDockWidget(Qt.LeftDockWidgetArea, dockwidget)
            
    def _openAudioFile(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select audio file", os.getcwd(),
                                               "Audio files (*.wav)")
        if fname is not None:
            self.audioplot.openAudio(fname)
            
    def createActions(self):
        self.openAudioFileAction = QAction("&Open audio file", self, shortcut=QKeySequence.Open)
        if (icon := QIcon.fromTheme("audio-x-generic")) is not None:
            self.openAudioFileAction.setIcon(icon)
        
    def connectActions(self):
        self.openAudioFileAction.triggered.connect(self._openAudioFile)
    
    def createToolBars(self):
        self.runToolBar = self.addToolBar("Run")
        self.runToolBar.addAction(self.openAudioFileAction)