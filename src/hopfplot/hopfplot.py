#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 19 22:06:16 2022

@author: keziah
"""
from pyqtgraph import GraphicsLayoutWidget, PlotWidget, LinearRegionItem, InfiniteLine, mkColor
from qtpy.QtWidgets import QScrollArea, QSizePolicy
from qtpy.QtCore import  Qt
import numpy as np
import itertools

class HopfPlot(QScrollArea):
    def __init__(self, parent, *args, sr=None, **kwargs):
        super().__init__()
        self.widget = GraphicsLayoutWidget(parent=parent)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
        self.sr = sr
        
        # from matplotlib.colours.CSS4_COLORS 
        # ['yellow', 'red', 'firebrick', 'darkorange', 'deeppink', 'darkmagenta', 
        # 'mediumvioletred', 'green', 'lime',  'darkslategrey', 'lightslategrey', 'skyblue', 'blue']
        self.colours = ['#FFFF00', '#FF0000', '#B22222', '#FF8C00', '#FF1493',
                        '#8B008B', '#C71585', '#008000', '#00FF00', '#2F4F4F',
                        '#778899', '#87CEEB', '#0000FF']
        self._plots = []
        
    @property
    def sr(self):
        return self._sr
    
    @sr.setter
    def sr(self, value):
        self._sr = value
        
    def setSampleRate(self, value):
        self.sr = value
        
    def addResponse(self, data, sampleRange=None, segmentColour=None):
        
        chans, size = data.shape
        
        if sampleRange is None:
            sampleRange = (0, size)
        s0, s1 = sampleRange
        
        if self.sr is not None:
            title = f"{s0/self.sr:g}-{s1/self.sr:g} seconds"
        else:
            title = f"{s0}-{s1} samples"
        if segmentColour is not None:
            title = f'<span style="color:{segmentColour}">{title}</span>'
            
        p = self.widget.addPlot(row=0, col=len(self._plots), title=title)
        self._plots.append(p)
            
        if self.sr is not None:
            t = np.linspace(s0/self.sr, s1/self.sr, size)
            p.setLabel('bottom', "Time", units="s")
        else:
            t = np.arange(s0, s1)
            p.setLabel('bottom', "Samples")
        
        colours = itertools.cycle(self.colours)
        
        for resp in data:
            pen = next(colours)
            p.plot(t, resp, pen=pen)
        
        