#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window
"""
from qtpy.QtWidgets import QMainWindow, QDockWidget, QAction, QFileDialog
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon, QKeySequence
from .audioplot import AudioPlotWidget
import soundfile as sf
import numpy as np
import os

class DBGui(QMainWindow):
    
    def __init__(self, *args, audioFile=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.audioplot = AudioPlotWidget(self)
        if audioFile is not None:
            self._openAudio(audioFile)
        
        self.createActions()
        self.connectActions()
        self.createToolBars()
        
        for name, widget in [('Audio Input', self.audioplot)]:
            dockwidget = QDockWidget(name)
            dockwidget.setWidget(widget)
            self.addDockWidget(Qt.LeftDockWidgetArea, dockwidget)
            
    def _openAudioFile(self):
        """ Show open file dialog """
        fname, _ = QFileDialog.getOpenFileName(self, "Select audio file", os.getcwd(),
                                               "Audio files (*.wav)")
        if fname is not None:
            self._openAudio(fname)
            
    def _openAudio(self, fname):
        """ Read audio file and set audio plot """
        audio, self.sr = sf.read(fname)

        if len(audio.shape) > 1:
            # convert stereo to mono
            audio = np.mean(audio, axis=-1)
            
        self.audio = audio
        
        self.audioplot.setAudio(self.audio, self.sr)
            
    def _doAnalysis(self):
        """ Create DetectorBank and call absZ """
        pass
        # print(self.audioplot.getSegments())
            
    def createActions(self):
        self.openAudioFileAction = QAction("&Open audio file", self, shortcut=QKeySequence.Open)
        if (icon := QIcon.fromTheme("audio-x-generic")) is not None:
            self.openAudioFileAction.setIcon(icon)
            
        self.analyseAction = QAction("&Analyse audio file", self, shortcut="F5")
        if (icon := QIcon.fromTheme("system-run")) is not None:
            self.analyseAction.setIcon(icon)
        
    def connectActions(self):
        self.openAudioFileAction.triggered.connect(self._openAudioFile)
        self.analyseAction.triggered.connect(self._doAnalysis)
    
    def createToolBars(self):
        self.runToolBar = self.addToolBar("Run")
        self.runToolBar.addAction(self.openAudioFileAction)
        self.runToolBar.addAction(self.analyseAction)