#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window
"""
from qtpy.QtWidgets import QMainWindow, QDockWidget, QAction, QFileDialog
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon, QKeySequence
from .audioplot import AudioPlotWidget
from .argswidget import AbsZArgsWidget
from .audioread import read_audio
from detectorbank import DetectorBank
import numpy as np
import os

class DBGui(QMainWindow):
    
    dockAreas = {'left':Qt.LeftDockWidgetArea, 'right':Qt.RightDockWidgetArea,
                 'top':Qt.TopDockWidgetArea, 'bottom':Qt.BottomDockWidgetArea}
    
    def __init__(self, *args, audioFile=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.audioplot = AudioPlotWidget(self)

        self.argswidget = AbsZArgsWidget(self)

        self.createActions()
        self.connectActions()
        self.createToolBars()
        
        self.statusBar()
        self._statusTimeout = 1500
        
        self.audioplot.statusMessage.connect(self._setTemporaryStatus)
        
        self.widgets = {"audioinput":('Audio Input', self.audioplot, 'left'),
                        "args":('Parameters',self.argswidget, 'right')}
        
        for key, values in self.widgets.items():
            name, widget, area = values
            dockarea = self.dockAreas[area]
            dockwidget = QDockWidget(name)
            dockwidget.setWidget(widget)
            self.addDockWidget(dockarea, dockwidget)
            
        self._openAudioDir = os.getcwd()
        if audioFile is not None:
            self._openAudio(audioFile)
            
    def _openAudioFile(self):
        """ Show open file dialog """
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select audio file", self._openAudioDir, "Wav files (*.wav);;All files (*)")
        if fname:
            self._openAudio(fname)
            
    def _openAudio(self, fname):
        """ Read audio file and set audio plot """
        try:
            audio, self.sr = read_audio(fname)
    
            self.audio = audio
            self.audioplot.setAudio(self.audio, self.sr)
            self.argswidget.setParams(sr=self.sr)
            
            self._openAudioDir = os.path.dirname(fname)
            self._setTemporaryStatus(f"Opened {os.path.basename(fname)}; sample rate {self.sr}Hz")
        except Exception as err:
            self._setTemporaryStatus(f"Cound not open {os.path.basename(fname)}")
            
    def _doAnalysis(self):
        """ Create DetectorBank and call absZ """
        params = self.argswidget.getArgs()
        from pprint import pprint; pprint(params)
        
        # TODO get audio segments
        
        det = self._makeDetectorBank(params)
        z = np.zeros((len(params['freqs']), len(self.audio)), dtype=np.complex128)  
        r = np.zeros(z.shape)
        self._setStatus("Getting DetectorBank response")
        det.getZ(z)
        det.absZ(r, z)
        
    def _makeDetectorBank(self, params):
        det_char = self._makeDetectorCharacteristics(params['freqs'], params['bws'])
        features = params['method'] | params['freqNorm'] | params['ampNorm']
        args = (self.sr, self.audio, params['numThreads'], det_char, features,
                params['damping'], params['gain'])
        det = DetectorBank(*args)
        return det
        
    def _makeDetectorCharacteristics(self, freqs, bws):
        return np.array(list(zip(freqs, bws)))
            
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
        
    def _setTemporaryStatus(self, msg):
        self.statusBar().showMessage(msg, self._statusTimeout)
        
    def _setStatus(self, msg):
        self.statusBar().showMessage(msg)