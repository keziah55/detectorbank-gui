#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  9 14:44:18 2022

@author: keziah
"""
from pyqtgraph import (PlotWidget, PlotCurveItem, mkPen, mkBrush, InfiniteLine, 
                       setConfigOptions)
import numpy as np
import os
import soundfile as sf
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QDoubleSpinBox, QFileDialog, QPushButton
from .segmentlist import SegmentList

class AudioPlotWidget(QWidget):
    
    def __init__(self, parent, style="dark"):
        
        super().__init__()
        
        self.plotState = None
        self.plotLabel = None
        self.parent = parent
        
        self._makePlot(parent, style=style)
        
        vbox = QVBoxLayout()
        
        self.selectFileButton = QPushButton("Select audio file")
        self.selectFileButton.clicked.connect(self._selectAudioFile)
        vbox.addWidget(self.selectFileButton)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.plotWidget)
        hbox.addWidget(self.segmentList)
        
        vbox.addLayout(hbox)
        
        self.setLayout(vbox)
        
    def _makePlot(self, *args, **kwargs):
        self.plotWidget = AudioPlot(*args, **kwargs)
        self.segmentList = SegmentList()
        
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
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.plotItem.setLabel('bottom',text='Time (s)')
    
    def setAudioData(self, data, sr):
        x = np.linspace(0, len(data)/sr, len(data))
        self.plot(x, data)