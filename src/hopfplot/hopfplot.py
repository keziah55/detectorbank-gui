#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 19 22:06:16 2022

@author: keziah
"""
from pyqtgraph import GraphicsLayoutWidget, PlotWidget, LinearRegionItem, InfiniteLine, mkColor
from qtpy.QtWidgets import QScrollArea, QSizePolicy
from qtpy.QtCore import  Qt

class HopfPlot(QScrollArea):
    def __init__(self, parent, *args, **kwargs):
        super().__init__()
        self.widget = GraphicsLayoutWidget(parent=parent)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
        self.colours = []
        self._plots = []
        
    def addResponse(self, data, colour=None):
        p = self.widget.addPlot(row=0, col=len(self._plots))
        self._plots.append(p)
        for resp in data:
            p.plot(resp)
        
        