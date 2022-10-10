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
        self._segmentColours = itertools.cycle([mkColor(f"{colour}{alpha}") for colour in colours])
        
        self.plotWidget = AudioPlot()
        self.segmentList = SegmentList()
        
        self.segmentList.requestAddSegment.connect(self.addSegment)
        self.segmentList.requestRemoveSegment.connect(self.removeSegment)
        self.segmentList.segmentRangeChanged.connect(self.setSegmentRange)
        self.plotWidget.requestSetSegmentRange.connect(self.setSegmentRange)
        
        self.selectFileButton = QPushButton("Select audio file")
        self.selectFileButton.clicked.connect(self._selectAudioFile)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.selectFileButton)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.plotWidget)
        hbox.addWidget(self.segmentList)
        
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        
        self._max = 1
        self.addSegment(start=0, stop=self._max)
        
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
        self._max = len(audio)/sr
        self.segmentList.setMaximum(self._max)
        
    def addSegment(self, start=None, stop=None):
        """ Add segment in both plot and list. """
        colour = next(self._segmentColours)
        if start is None and len(self.plotWidget._segments) > 0:
            # use time of last segment as start of new segment
            start = max([segment.getRegion()[1] for segment in self.plotWidget._segments])
            if start > self._max:
                start = self._max
        if stop is None:
            stop = start + 1
        self.plotWidget.addSegment(start=start, stop=stop, colour=colour)
        self.segmentList.addSegment(start=start, stop=stop, colour=colour)
        
    def removeSegment(self, idx):
        """ Remove segment at index `idx` from both plot and list. """
        self.plotWidget.removeSegment(idx)
        self.segmentList.removeSegment(idx)
        
    def setSegmentRange(self, idx, start=None, stop=None):
        """ Update range of segment `idx` in both plot and list. """
        self.plotWidget.setSegmentRange(idx, start=start, stop=stop)
        self.segmentList.setSegmentRange(idx, start=start, stop=stop)
        
class AudioPlot(PlotWidget):
    
    requestSetSegmentRange = Signal(int, object, object)
    """ **signal** requestSetSegmentRange(int `idx`, float `start`, float `stop`) 
    
        Emitted when a segment range is change by user.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._segments = []
        self.plotItem.setLabel('bottom',text='Time (s)')
    
    def setAudioData(self, data, sr):
        """ Plot `data`, with sample rate `sr`. """
        x = np.linspace(0, len(data)/sr, len(data))
        self.plot(x, data)
        self._segments[0].setRegion((0, len(data)/sr))
        
    def addSegment(self, start=None, stop=None, colour=None):
        """ Add a new segment selection, optionally supplying range. """
        segment = LinearRegionItem(brush=colour)
        self._setSegmentRange(segment, start, stop)
        self.plotItem.addItem(segment)
        self._segments.append(segment)
        segment.sigRegionChangeFinished.connect(self._emitSetSegmentRange)
        
    def removeSegment(self, idx):
        """ Remove segment at index `idx`. """
        segment = self._segments.pop(idx)
        self.plotItem.removeItem(segment)
        
    def _emitSetSegmentRange(self, segment):
        """ Find `segment` in list and emit :attr:`requestSetSegmentRange` """
        idx = self._segments.index(segment)
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
        segment = self._segments[idx]
        self._setSegmentRange(segment, start, stop)
        