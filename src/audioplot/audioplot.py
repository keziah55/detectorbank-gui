#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 14:44:18 2022

@author: keziah
"""
from pyqtgraph import PlotWidget, LinearRegionItem, mkColor
import numpy as np
import os
import itertools
import soundfile as sf
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QPushButton
from .segmentlist import SegmentList

class AudioPlotWidget(QWidget):
    
    def __init__(self, parent=None):
        
        super().__init__(parent=parent)
        
        alpha = "32"
        colours = ["#0000ff", "#ff0000", "#00ff00", "#ffe523", "#ed21ff", 
                   "#ff672b", "#9718ff", "#00ffaa"]
        self._segmentColours = [mkColor(f"{colour}{alpha}") for colour in colours]
        
        self.plotWidget = AudioPlot(colours=self._segmentColours)
        self.segmentList = SegmentList(colours=self._segmentColours)
        
        self.segmentList.requestNewSegment.connect(self.plotWidget.addSegment)
        self.segmentList.requestRemoveSegment.connect(self.plotWidget.removeSegment)
        self.segmentList.segmentRangeChanged.connect(self.plotWidget.setSegmentRange)
        
        self.plotWidget.requestSetSegmentRange.connect(self.segmentList.setSegmentRange)
        
        vbox = QVBoxLayout()
        
        self.selectFileButton = QPushButton("Select audio file")
        self.selectFileButton.clicked.connect(self._selectAudioFile)
        vbox.addWidget(self.selectFileButton)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.plotWidget)
        hbox.addWidget(self.segmentList)
        
        vbox.addLayout(hbox)
        
        self.setLayout(vbox)
        
    def _selectAudioFile(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select audio file", os.getcwd(),
                                               "Audio files (*.wav)")
        if fname is not None:
            self._openAudio(fname)
            
    def _openAudio(self, fname):
        audio, sr = sf.read(fname)

        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=-1)
            
        self.plotWidget.setAudioData(audio, sr)
        self.segmentList.setMaximum(len(audio)/sr)
        
class AudioPlot(PlotWidget):
    
    requestSetSegmentRange = Signal(int, object, object)
    """ **signal** requestSetSegmentRange(int `idx`, float `start`, float `stop`) 
    
        Emitted when a segment range is change by user.
    """
    
    def __init__(self, colours, *args, **kwargs):
        super().__init__()
        self.segments = []
        self._colours = itertools.cycle(colours)
        
        self.plotItem.setLabel('bottom',text='Time (s)')
        self.addSegment()
    
    def setAudioData(self, data, sr):
        """ Plot `data`, with sample rate `sr`. """
        x = np.linspace(0, len(data)/sr, len(data))
        self.plot(x, data)
        self.segments[0].setRegion((0, len(data)/sr))
        
    def addSegment(self, start=None, stop=None):
        """ Add a new segment selection, optionally supplying range. """
        brush = next(self._colours)
        segment = LinearRegionItem(brush=brush)
        self._setSegmentRange(segment, start, stop)
        self.plotItem.addItem(segment)
        self.segments.append(segment)
        segment.sigRegionChangeFinished.connect(self._emitSetSegmentRange)
        
    def removeSegment(self, idx):
        """ Remove segment at index `idx`. """
        segment = self.segments.pop(idx)
        self.plotItem.removeItem(segment)
        
    def _emitSetSegmentRange(self, segment):
        """ Find `segment` in list and emit :attr:`requestSetSegmentRange` """
        idx = self.segments.index(segment)
        start, stop = segment.getRegion()
        self.requestSetSegmentRange.emit(idx, start, stop)
        
    def _setSegmentRange(self, segment, start=None, stop=None):
        """ Set bounds of LinearRegionItem `segment` """
        if start is not None:
            segment.lines[0].setValue(start)
        if stop is not None:
            segment.lines[1].setValue(stop)
        
    def setSegmentRange(self, idx, start=None, stop=None):
        """ Update range of segment `idx` """
        segment = self.segments[idx]
        self._setSegmentRange(segment, start, stop)
        