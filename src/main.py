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
from .argswidget import ArgsWidget
from .audioread import read_audio
from .hopfplot import HopfPlot
from detectorbank import DetectorBank, DetectorCache, Producer
import numpy as np
import os

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
        self.hopfplot.sr = value
        
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
        
        segments = self.audioplot.getSegments()
        numSamples = 0
        for segment in segments:
            n0, n1 = segment.samples
            numSamples += (n1-n0)
        numSamples //= self.downsample
        self._progressBar.setMaximum(numSamples)
        
        for i, segment in enumerate(segments):
            n0, n1 = segment.samples
            channels = self._makeDetectorCache(params, audioSlice=(n0,n1))
            result = np.zeros((channels, (n1-n0)//self.downsample))
            
            self._setStatus(f"Getting DetectorBank response {i+1} of {len(segments)}")
            
            n, idx = 0, 0
            
            while n < self.cache.end():
                for k in range(channels):
                    result[k][idx] = self.cache[k,n]
                idx += 1
                n += self.downsample
                self._progressBar.setValue(self._progressBar.value()+1)
            
            self.hopfplot.addResponse(result, sampleRange=segment.samples, segmentColour=segment.colour)
        self.statusBar().clearMessage()
        
    def _makeDetectorCache(self, params, audioSlice=None):
        det_char = self._makeDetectorCharacteristics(*params['detChars'])
        features = params['method'] | params['freqNorm'] | params['ampNorm']
        if audioSlice is not None:
            n0, n1 = audioSlice
            if n0 < 0:
                n0 = 0
            if n1 > len(self.audio):
                n1 = len(self.audio)
            audio = self.audio[n0:n1]
        else:
            audio = self.audio
        args = (self.sr, audio, params['numThreads'], det_char, features,
                params['damping'], params['gain'])
        self.det = DetectorBank(*args)
        self.p = Producer(self.det)
        segSize = self.cacheSegDuration * self.sr
        numSegs = 10
        self.cache = DetectorCache(self.p, numSegs, segSize)
        channels = self.det.getChans()
        return channels
        
    def _makeDetectorCharacteristics(self, freqs, bws):
        return np.array(list(zip(freqs, bws)))
            
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