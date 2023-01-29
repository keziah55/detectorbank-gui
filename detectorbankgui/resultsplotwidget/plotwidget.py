#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single PlotWidget, with label underneath sjowing mouse values.
"""
from pyqtgraph import PlotWidget as _PlotWidget, InfiniteLine, mkPen
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel
from qtpy.QtCore import Signal, Slot, QPointF
from qtpy.QtGui import QPen
import numpy as np

class PlotWidget(QWidget):
    """ PlotWidget with label and crosshairs """
    
    highlightChannel = Signal(object)
    
    def __init__(self, parent, *args, freqs=None, segment=None, **kwargs):
        super().__init__(parent)
        self.freqs = freqs
        self.segment = segment
        self.parent = parent
        self.title = kwargs.get('title', None)
        
        self.plotLabel = QLabel(self)
        self.plotWidget = _PlotWidget(*args, **kwargs)
        
        # crosshairs on plot
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.plotWidget.plotItem.addItem(self.vLine, ignoreBounds=True)
        self.plotWidget.plotItem.addItem(self.hLine, ignoreBounds=True)
        self.plotWidget.plotItem.showGrid(True, True)
        self._hoverTolerance = (30,50) # how close in pixels mouse should be  to data to show values in label
        
        self._hoverLineWidth = 5
        self._noHoverLineWidth = None
        self._hoverLine = None
        
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

            # only set values if mouse is close enough to data points       
            dataPos = self.plotWidget.plotItem.vb.mapViewToScene(QPointF(xData[idx], yData[channel]))
            diff = dataPos - pos
            if abs(diff.x()) <= self._hoverTolerance[0] and abs(diff.y()) <= self._hoverTolerance[1]:
                self.setHoverLabel(xData[idx], yData[channel], channel)
            else:
                self.setHoverLabel(xData[idx])
            
    def setHoverLabel(self, x, y=None, channel=None):
        """ Set label which values under mouse.
        
            Also highlights current line, if `channel` is not None.
        """
        xunits = "seconds" if self.parent.sr is not None else "samples"
        if y is not None and channel is not None:
            colour = self._getPen(channel).color().name()
            self.plotLabel.setText(f'<span>{x:g} {xunits};</span> <span style="color:{colour}">{self.freqs[channel]:g}Hz: {y:g}</span>')
        else:
            self.plotLabel.setText(f'<span>{x:g} {xunits}</span>')
        self.setHighlightLine(channel)
            
    def setHighlightLine(self, channel=None):
        """ Change the width of line at index `channel` """
        # changing pen width slightly changes autoscale range, so disable it
        self.plotWidget.plotItem.vb.enableAutoRange(enable=False) 
        if self._hoverLine is not None:
            # reset any previously highlighted line
            self._setChannelPenWidth(self._hoverLine, self._noHoverLineWidth)
        
        if channel is not None:
            # highlight current line
            self._noHoverLineWidth = self._getPen(channel).width()
            self._setChannelPenWidth(channel, self._hoverLineWidth)
        self._hoverLine = channel
        self.highlightChannel.emit(channel)
            
    def __getattr__(self, name):
        return getattr(self.plotWidget, name)
    
    def _getPen(self, channel):
        """ Return pen of line at index `channel` """
        pen = self.plotWidget.plotItem.dataItems[channel].opts['pen']
        if not isinstance(pen, QPen):
            pen = mkPen(pen)
        return pen
    
    def _setChannelPenWidth(self, channel, width):
        pen = self._getPen(channel)
        pen.setWidth(width)
        self.plotWidget.plotItem.dataItems[channel].setPen(pen)
    