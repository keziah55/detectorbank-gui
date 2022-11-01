#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 19 22:06:16 2022

@author: keziah
"""
from pyqtgraph import PlotWidget
from qtpy.QtWidgets import QScrollArea, QSizePolicy, QWidget, QHBoxLayout
from qtpy.QtCore import  Qt
import numpy as np
import itertools

class HopfPlot(QScrollArea):
    def __init__(self, parent, *args, sr=None, **kwargs):
        super().__init__()
        # self.widget = GraphicsLayoutWidget(parent=parent)
        self.widget = _HopfPlot(parent, *args, sr=None, **kwargs)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
    def __getattr__(self, name):
        return getattr(self.widget, name)
        
class _HopfPlot(QWidget):
    def __init__(self, parent, *args, sr=None, **kwargs):
        super().__init__()
        self.sr = sr
        
        # from matplotlib.colours.CSS4_COLORS 
        # ['yellow', 'red', 'firebrick', 'darkorange', 'deeppink', 'darkmagenta', 
        # 'mediumvioletred', 'green', 'lime',  'darkslategrey', 'lightslategrey', 'skyblue', 'blue']
        self.colours = ['#FFFF00', '#FF0000', '#B22222', '#FF8C00', '#FF1493',
                        '#8B008B', '#C71585', '#008000', '#00FF00', '#2F4F4F',
                        '#778899', '#87CEEB', '#0000FF']
        self._plots = []
        
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
    @property
    def sr(self):
        return self._sr
    
    @sr.setter
    def sr(self, value):
        self._sr = value
        
    def setSampleRate(self, value):
        self.sr = value
        
    def addResponse(self, data, segment=None, sampleRange=None, titleColour=None, layoutIdx=None):
        """ Plot `data`. 
        
            If `segment` is given, `sampleRange`, `titleColour` and `layoutIdx`
            will be retreived from attributes.
            
            If not giving `segment`, provide these values, where desired.
        """
        chans, size = data.shape
        
        if segment is not None:
            sampleRange = segment.samples
            titleColour = segment.colour
            layoutIdx = segment.idx
        
        if sampleRange is None:
            sampleRange = (0, size)
        s0, s1 = sampleRange
        
        if self.sr is not None:
            title = f"{s0/self.sr:.4g}-{s1/self.sr:.4g} seconds"
        else:
            title = f"{s0}-{s1} samples"
        if titleColour is not None:
            title = f'<span style="color:{titleColour}">{title}</span>'
            
        if layoutIdx is None:
            layoutIdx = self.layout.count()
            
        p = PlotWidget(title=title)
        self.layout.insertWidget(layoutIdx, p)
        self._plots.append(p)
            
        if self.sr is not None:
            t = np.linspace(s0/self.sr, s1/self.sr, size)
            p.setLabel('bottom', "Time", units="s")
        else:
            # TODO downsampling
            t = np.arange(s0, s1)
            p.setLabel('bottom', "Samples")
        
        colours = itertools.cycle(self.colours)
        
        for resp in data:
            pen = next(colours)
            p.plot(t, resp, pen=pen)
        
        