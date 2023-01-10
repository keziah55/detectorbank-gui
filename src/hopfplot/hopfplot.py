#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Display multiple output plots
"""
from pyqtgraph import PlotWidget, InfiniteLine, mkPen
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QLabel, QToolBar, QSpinBox, 
                            QStackedWidget, QGridLayout)
from qtpy.QtCore import Qt, Slot, QTimer, QPointF
from qtpy.QtGui import QIcon, QPen
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
    
class PlotPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        
    def addPlot(self, plot, row, col):
        return self.layout.addWidget(plot, row, col)
    
    def clear(self):
        for idx in reversed(range(self.layout.count(), 0)):
            item = self.layout.takeAt(idx)
            widget = item.widget()
            widget.deleteLater()
        
    def getNextRowCol(self):
        """ Return row and column of next empty space """
        if self.layout.count() == 0:
            return 0, 0
        else:
            row = self.layout.rowCount()
            col = self.layout.columnCount()
            rem = self.layout.count() % (row*col)
            if rem == col:
                row += 1
                col = 0
            return row, col

class HopfPlot(QWidget):
    def __init__(self, parent, *args, sr=None, **kwargs):
        super().__init__()
        
        ## toolbar and pages ##
        self.toolbar = QToolBar()
        self.stack = QStackedWidget()
        # TODO legend
        
        ## grid dimensions ##
        self.rowsBox = QSpinBox()
        self.colsBox = QSpinBox()
        self.rowsBox.setPrefix("Rows: ")
        self.colsBox.setPrefix("Columns: ")
        self.rowsBox.setValue(2)
        self.colsBox.setValue(2)
        
        self.toolbar.addWidget(self.rowsBox)
        self.toolbar.addWidget(self.colsBox)
        self.applyGridAction = self.toolbar.addAction("Apply")
        if (icon := QIcon.fromTheme("ok")) is not None:
            self.applyGridAction.setIcon(icon)
        self.applyGridAction.triggered.connect(self._resetGrid)
        
        self.toolbar.addSeparator()
        
        ## pages ##
        self.pageLabel = QLabel()
        
        self.previousPageAction = self.toolbar.addAction("Previous page")
        if (icon := QIcon.fromTheme("go-previous")) is not None:
            self.previousPageAction.setIcon(icon)
        
        self.toolbar.addWidget(self.pageLabel)
        
        self.nextPageAction = self.toolbar.addAction("Next page")
        if (icon := QIcon.fromTheme("go-next")) is not None:
            self.nextPageAction.setIcon(icon)
        
        self.previousPageAction.triggered.connect(self._previousPage)
        self.nextPageAction.triggered.connect(self._nextPage)
        
        # manually count pages in stack
        # stack.count() is unreliable when pages are deleted
        self._pageCount = 0
        self.page = 0
        
        self.toolbar.addSeparator()
        
        ## export and clear##
        self.exportAction = self.toolbar.addAction("Export")
        if (icon := QIcon.fromTheme("document-save-as")) is not None:
            self.exportAction.setIcon(icon)
            
        self.clearAction = self.toolbar.addAction("Clear")
        if (icon := QIcon.fromTheme("edit-clear")) is not None:
            self.clearAction.setIcon(icon)
        self.clearAction.triggered.connect(self.removeAll)
        
        ## plots ##
        
        # from matplotlib.colours.CSS4_COLORS 
        # ['yellow', 'red', 'firebrick', 'darkorange', 'deeppink', 'darkmagenta', 
        # 'mediumvioletred', 'green', 'lime',  'darkslategrey', 'lightslategrey', 'skyblue', 'blue']
        self.colours = ['#FFFF00', '#FF0000', '#B22222', '#FF8C00', '#FF1493',
                        '#8B008B', '#C71585', '#008000', '#00FF00', '#2F4F4F',
                        '#778899', '#87CEEB', '#0000FF']
        self._plots = []
        
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.stack)
        self.setLayout(layout)
        
    @property
    def page(self):
        return self.stack.currentIndex()
    
    @page.setter
    def page(self, idx):
        if idx < 0:
            idx = 0
        elif idx >= self._pageCount:
            idx = self._pageCount - 1
        self.stack.setCurrentIndex(idx)
        self.pageLabel.setText(f"Page {idx+1}/{self._pageCount}")
        
    def _newPage(self):
        page = PlotPage()
        self.stack.insertWidget(self._pageCount, page)
        self._pageCount += 1
        return page
    
    def _previousPage(self):
        self.page -= 1
        
    def _nextPage(self):
        self.page += 1
        
    @property
    def rows(self):
        return self.rowsBox.value()
    
    @property
    def cols(self):
        return self.colsBox.value()
        
    @property
    def sr(self):
        return self._sr
    
    @sr.setter
    def sr(self, value):
        self._sr = value
        
    def setSampleRate(self, value):
        self.sr = value
        
    def _resetGrid(self):
        """ Remove all plots and re-add them with current grid dimensions """
        # remove all pages
        self._clearStack()
        
        # new first page
        page = self._newPage()
        row, col = 0, 0
            
        # add plots
        for p in self._plots:
            if row >= self.rows:
                page = self._newPage()
                row, col = 0, 0
                
            page.addPlot(p, row, col)
                
            col += 1
            if col == self.cols:
                col = 0
                row += 1
        self.page = 1
        
    def removeAll(self):
        for idx in range(self.stack.count()):
            page = self.stack.widget(idx)
            page.clear()
        self.clear()
        
    def clear(self):
        """ Remove all pages from stack """
        self._clearStack()
        self._plots = []
            
    def _clearStack(self):
        """ Remove all widgets from stack and reset current page index and count """
        for i in reversed(range(self.stack.count(), 0)):
            item = self.stack.takeAt(i)
            widget = item.widget()
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self._pageCount = 0
        self.page = 0
        
    def export(self):
        """ Export all plots """
        pass
        
    def addPlots(self, freqs, segments):
        """ Create empty plots for the given segments, which will contain data for the given frequencies """
        
        if self._pageCount == 0:
            page = self._newPage()
            row, col = 0, 0
        else:
            page = self.stack.widget(self._pageCount-1)
            row, col = page.getNextRowCol()
        
        for segment in segments:
        
            if row >= self.rows:
                page = self._newPage()
                row, col = 0, 0
        
            s0, s1 = segment.samples
            
            if self.sr is not None:
                title = f"{s0/self.sr:.4g}-{s1/self.sr:.4g} seconds"
            else:
                title = f"{s0}-{s1} samples"
            if segment.colour is not None:
                title = f'<span style="color:{segment.colour}">{title}</span>'
                
            p = SegmentPlotWidget(self, title=title, freqs=freqs, segment=segment)
            page.addPlot(p, row, col)
            self._plots.append(p)
                
            if self.sr is not None:
                p.setLabel('bottom', "Time", units="s")
            else:
                p.setLabel('bottom', "Samples")
                
            col += 1
            if col == self.cols:
                col = 0
                row += 1
                
    def addData(self, idx, data):
        """ Plot `data` on plot at index `idx` """
        p = self._plots[idx]
        self.page = idx // (self.rows*self.cols)
        
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
            
