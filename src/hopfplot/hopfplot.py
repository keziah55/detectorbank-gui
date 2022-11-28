#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Display multiple output plots
"""
from pyqtgraph import PlotWidget, InfiniteLine
from qtpy.QtWidgets import QScrollArea, QSizePolicy, QWidget, QHBoxLayout, QLabel, QVBoxLayout
from qtpy.QtCore import Qt, Slot
import numpy as np
import itertools

class SegmentPlotWidget(QWidget):
    def __init__(self, parent, *args, freqs=None, segment=None, **kwargs):
        super().__init__(parent)
        self.freqs = freqs
        self.segment = segment
        self.parent = parent
        
        self.plotLabel = QLabel(self)
        self.plotWidget = PlotWidget(*args, **kwargs)
        
        # crosshairs on plot
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.plotWidget.plotItem.addItem(self.vLine, ignoreBounds=True)
        self.plotWidget.plotItem.addItem(self.hLine, ignoreBounds=True)
        self.plotWidget.plotItem.showGrid(True, True)
        
        self.plotWidget.scene().sigMouseMoved.connect(self.mouseMoved)
        
        plotLayout = QVBoxLayout()
        plotLayout.addWidget(self.plotWidget)
        plotLayout.addWidget(self.plotLabel)
        
        self.setLayout(plotLayout)
        
    @Slot(object)
    def mouseMoved(self, pos):
        if self.plotItem.sceneBoundingRect().contains(pos) and len(self.plotWidget.plotItem.dataItems) > 0:
            mousePoint = self.plotWidget.plotItem.vb.mapSceneToView(pos)
            
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            
            xData = self.plotWidget.plotItem.dataItems[0]._dataset.x # should all have same x values
            idx = np.abs(xData-mousePoint.x()).argmin()
            
            yData = np.array([item._dataset.y[idx] for item in self.plotWidget.plotItem.dataItems])
            channel = np.abs(yData-mousePoint.y()).argmin()
            # TODO define max distance that still counts
            
            self.setHoverLabel(xData[idx], yData[channel], channel)
            
    def setHoverLabel(self, x, y, channel):
        xunits = "seconds" if self.parent.sr is not None else "samples"
        colour = self.plotWidget.plotItem.dataItems[channel].opts['pen']
        self.plotLabel.setText(f'<span>{x:g} {xunits};</span> <span style="color:{colour}">{self.freqs[channel]:g}Hz: {y:g}</span>')
            
    def __getattr__(self, name):
        return getattr(self.plotWidget, name)

class HopfPlot(QScrollArea):
    def __init__(self, parent, *args, sr=None, **kwargs):
        super().__init__()
        # self.widget = GraphicsLayoutWidget(parent=parent)
        self.widget = _HopfPlot(parent, *args, sr=None, **kwargs)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
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
        
    def addPlot(self, freqs, segment) -> int:
        """ Add empty plot for `segment`, which will show responses for freqencies `freqs` 
        
            Return index of plot in layout
        """
        layoutIdx = segment.idx
        
        s0, s1 = segment.samples
        
        if self.sr is not None:
            title = f"{s0/self.sr:.4g}-{s1/self.sr:.4g} seconds"
        else:
            title = f"{s0}-{s1} samples"
        if segment.colour is not None:
            title = f'<span style="color:{segment.colour}">{title}</span>'
            
        if layoutIdx is None:
            layoutIdx = self.layout.count()
            
        p = SegmentPlotWidget(self, title=title, freqs=freqs, segment=segment)
        # p.scene().sigMouseMoved.connect(lambda pos: self._mouseHover(p, pos))
        self.layout.insertWidget(layoutIdx, p)
        self._plots.append(p)
            
        if self.sr is not None:
            p.setLabel('bottom', "Time", units="s")
        else:
            p.setLabel('bottom', "Samples")
            
        return layoutIdx
    
    def addData(self, idx, data):
        p = self.layout.itemAt(idx).widget()
        
        chans, size = data.shape
        
        s0, s1 = p.segment.samples
        
        if self.sr is not None:
            t = np.linspace(s0/self.sr, s1/self.sr, size)
        else:
            # TODO downsampling
            t = np.arange(s0, s1)
        
        colours = itertools.cycle(self.colours)
        
        for k, resp in enumerate(data):
            pen = next(colours)
            p.plot(t, resp, pen=pen, name=p.freqs[k])
        
    def addResponse(self, data, segment=None, sampleRange=None, titleColour=None, layoutIdx=None):
        """ Plot `data`. 
        
            If `segment` is given, `sampleRange`, `titleColour` and `layoutIdx`
            will be retreived from attributes.
            
            If not giving `segment`, provide these values, where desired.
        """
        # TODO make all plots before starting analysis, then add data when it's ready?
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
        p.scene().sigMouseMoved.connect(lambda pos: self._mouseHover(p, pos))
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
        
        
    # def _mouseHover(self, plotwidget, pos):
        
    #     width = height = 50
    #     x = pos.x() + width / 2
    #     y = pos.y() + height / 2
    #     rect = QRectF(x, y, width, height)
    #     items = plotwidget.scene().items(rect)
    #     print(f"\nplot {plotwidget} hovered; pos: {pos}; items: {items}")
        
            
        