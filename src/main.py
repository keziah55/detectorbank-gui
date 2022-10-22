#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window
"""
from qtpy.QtWidgets import (QMainWindow, QDockWidget, QAction, QFileDialog, 
                            QMessageBox, QProgressBar)
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon, QKeySequence
from .audioplot import AudioPlotWidget
from .analyser import Analyser
from .argswidget import ArgsWidget
from .audioread import read_audio
from .hopfplot import HopfPlot
from detectorbank import DetectorBank, DetectorCache, Producer
import numpy as np
import os
from functools import partial
from collections import deque

class DBGui(QMainWindow):
    
    dockAreas = {'left':Qt.LeftDockWidgetArea, 'right':Qt.RightDockWidgetArea,
                 'top':Qt.TopDockWidgetArea, 'bottom':Qt.BottomDockWidgetArea}
    
    def __init__(self, *args, audioFile=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.audioplot = AudioPlotWidget(self)
        self.argswidget = ArgsWidget(self)
        self.hopfplot = HopfPlot(self)

        self.createActions()
        self.connectActions()
        self.createToolBars()
        
        self.statusBar()
        self._statusTimeout = 1500
        
        self._progressBar = QProgressBar()
        self.statusBar().addPermanentWidget(self._progressBar)
        self._progressQueue = deque()
        
        self.audioplot.statusMessage.connect(self._setTemporaryStatus)
        
        widgets = {"audioinput":('Audio Input', self.audioplot, 'left'),
                   "args":('Parameters',self.argswidget, 'right'),
                   "output":("Output", self.hopfplot, 'bottom')}
        
        for key, values in widgets.items():
            name, widget, area = values
            self.createDockWidget(widget, area, name, key)
            
        self._openAudioDir = os.getcwd()
        if audioFile is not None:
            self._openAudio(audioFile)
            
        self.downsample = 10
        self.cacheSegDuration = 30 # cache segment size in ms
        
        self.showMaximized()
            
    @property
    def sr(self):
        return self._sr
    
    @sr.setter
    def sr(self, value):
        self._sr = value
        self.argswidget.setParams(sr=value)
        self.hopfplot.setSampleRate(value)
        
    @property
    def running(self):
        return self._running
    
    @running.setter
    def running(self, value):
        self._running = value
        self.runToolBar.setEnabled(not value)
            
    def _openAudioFile(self):
        """ Show open file dialog """
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select audio file", self._openAudioDir, "Wav files (*.wav);;All files (*)")
        if fname:
            self._openAudio(fname)
            
    def _openAudio(self, fname):
        """ Read audio file and set audio plot """
        try:
            self.audio, self.sr = read_audio(fname)
    
            self.audioplot.setAudio(self.audio, self.sr)
            
            self._openAudioDir = os.path.dirname(fname)
            self._setTemporaryStatus(f"Opened {os.path.basename(fname)}; sample rate {self.sr}Hz")
        except Exception as err:
            self._setTemporaryStatus(f"Cound not open {os.path.basename(fname)}")
            
    def _doAnalysis(self):
        """ Create DetectorBank and call absZ """
        params, invalid = self.argswidget.getArgs()
        if len(invalid) > 0:
            QMessageBox.warning(self, "Cannot run", 
                                f"The following arg(s) are invalid: {', '.join(invalid)}.\n"
                                "Analysis cannot be carried out.")
            return
        
        self.analysers = []
        segments = self.audioplot.getSegments()
        numSamples = 0
        for segment in segments:
            n0, n1 = segment.samples
            numSamples += (n1-n0)
            
            analyser = Analyser(self.audio, self.sr, params, n0, n1, self.downsample)
            self.analysers.append(analyser)
            analyser.progress.connect(self._incrementProgress)
            analyser.finished.connect(
                partial(self.hopfplot.addResponse, sampleRange=segment.samples, segmentColour=segment.colour))
            
        numSamples //= self.downsample
        self._progressBar.setMaximum(numSamples)
        self._progressQueue.clear()
        
        # for i, segment in enumerate(segments):
        #     n0, n1 = segment.samples
        #     channels = self._makeDetectorCache(params, audioSlice=(n0,n1))
        #     result = np.zeros((channels, (n1-n0)//self.downsample))
            
        #     self._setStatus(f"Getting DetectorBank response {i+1} of {len(segments)}")
            
        #     n, idx = 0, 0
            
        #     while n < self.cache.end() and idx < result.shape[1]:
        #         for k in range(channels):
        #             result[k][idx] = self.cache[k,n]
        #         idx += 1
        #         n += self.downsample
        #         self._progressBar.setValue(self._progressBar.value()+1)
            
        #     self.hopfplot.addResponse(result, sampleRange=segment.samples, segmentColour=segment.colour)
            
        self._progressBar.setValue(numSamples)
        self.statusBar().clearMessage()
        
    def _incrementProgress(self, inc):
        self._progressQueue.append(inc)
        self.__checkProgressQueue()
        
    def _checkProgressQueue(self):
        while len(self._progressQueue) > 0:
            inc = self._progressQueue.popleft()
            self._progressBar.setValue(self._progressBar.value()+inc)
        
    def createDockWidget(self, widget, area, title, key=None):
        if area in self.dockAreas:
            area = self.dockAreas[area]
        dock = QDockWidget()
        dock.setWidget(widget)
        dock.setWindowTitle(title)
        dock.setObjectName(title)
        self.addDockWidget(area, dock)
        if not hasattr(self, "dockWidgets"):
            self.dockWidgets = {}
        if key is None:
            key = title
        self.dockWidgets[key] = dock
    
    def createActions(self):
        self.openAudioFileAction = QAction("&Open audio file", self, shortcut=QKeySequence.Open,
                                           statusTip="Select audio file")
        if (icon := QIcon.fromTheme("audio-x-generic")) is not None:
            self.openAudioFileAction.setIcon(icon)
            
        self.analyseAction = QAction("&Analyse audio file", self, shortcut="F5",
                                     statusTip="Perform frequency analysis of audio")
        if (icon := QIcon.fromTheme("system-run")) is not None:
            self.analyseAction.setIcon(icon)
            
        self.exitAction = QAction("&Quit", self, shortcut=QKeySequence.Quit,
                                  statusTip="Quit application")
        if (icon := QIcon.fromTheme("application-exit")) is not None:
            self.exitAction.setIcon(icon)
        
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