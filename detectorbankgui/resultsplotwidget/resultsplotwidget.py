#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Display multiple output plots
"""
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QLabel, QToolBar, QSpinBox, 
                            QStackedWidget)

from .legendwidget import LegendWidget
from .plotpage import PlotPage
from .plotwidget import PlotWidget

from customQObjects.widgets import VSplitter
from customQObjects.gui import getIconFromTheme
import numpy as np
import itertools

class ResultsPlotWidget(QWidget):
    """ Widget containing QStackedWidget of PlotPages """
    def __init__(self, parent, *args, sr=None, **kwargs):
        super().__init__()
        
        ## toolbar and pages ##
        self.toolbar = QToolBar()
        self.stack = QStackedWidget()
        self.legendWidget = LegendWidget(self)
        
        ## grid dimensions ##
        self.rowsBox = QSpinBox()
        self.colsBox = QSpinBox()
        self.rowsBox.setPrefix("Rows: ")
        self.colsBox.setPrefix("Columns: ")
        self.rowsBox.setValue(2)
        self.colsBox.setValue(2)
        self.rowsBox.setMinimum(1)
        self.colsBox.setMinimum(1)
        
        ## toolbar ##
        self.toolbar.addAction(parent.analyseAction)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.rowsBox)
        self.toolbar.addWidget(self.colsBox)
        self.applyGridAction = self.toolbar.addAction("Apply")
        if (icon := getIconFromTheme("ok")) is not None:
            self.applyGridAction.setIcon(icon)
        self.applyGridAction.triggered.connect(self._resetGrid)
        
        self.toolbar.addSeparator()
        
        ## pages ##
        self.pageLabel = QLabel()
        
        self.previousPageAction = self.toolbar.addAction("Previous page")
        if (icon := getIconFromTheme("go-previous")) is not None:
            self.previousPageAction.setIcon(icon)
        
        self.toolbar.addWidget(self.pageLabel)
        
        self.nextPageAction = self.toolbar.addAction("Next page")
        if (icon := getIconFromTheme("go-next")) is not None:
            self.nextPageAction.setIcon(icon)
        
        self.previousPageAction.triggered.connect(self._previousPage)
        self.nextPageAction.triggered.connect(self._nextPage)
        
        self.toolbar.addSeparator()
        
        ## clear##
        self.clearAction = self.toolbar.addAction("Clear")
        if (icon := getIconFromTheme("edit-clear")) is not None:
            self.clearAction.setIcon(icon)
        self.clearAction.triggered.connect(self.clear)
        
        ## plots ##
        # from matplotlib.colours.CSS4_COLORS 
        # ['yellow', 'red', 'firebrick', 'darkorange', 'deeppink', 'darkmagenta', 
        # 'mediumvioletred', 'green', 'lime',  'darkslategrey', 'lightslategrey', 'skyblue', 'blue']
        self.colours = ['#FFFF00', '#FF0000', '#B22222', '#FF8C00', '#FF1493',
                        '#8B008B', '#C71585', '#008000', '#00FF00', '#2F4F4F',
                        '#778899', '#87CEEB', '#0000FF']
        self._plots = []
        
        self.page = 0
        
        self.sr = sr
        
        self._splitter = VSplitter()
        self._splitter.addWidget(self.stack)
        self._splitter.addWidget(self.legendWidget)
        self._splitter.setStretchFactors([10,1])
        self._splitter.setSizes([500,10])
        
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self._splitter)
        self.setLayout(layout)
        
    def resizeEvent(self, event):
        self.legendWidget.updateWidth(event.size().width())
        
    @property
    def page(self):
        """ Return current page index """
        return self.stack.currentIndex()
    
    @page.setter
    def page(self, idx):
        """ Set current page index and associated values """
        # store our own pageCount because QStackedWidget.count is unreliable
        # when pages have been deleted
        if self._pageCount == 0:
            self.pageLabel.setText("Page 0/0")
            return
        if idx < 0:
            idx = 0
        elif idx >= self._pageCount:
            idx = self._pageCount - 1
        self.stack.setCurrentIndex(idx)
        self.pageLabel.setText(f"Page {idx+1}/{self._pageCount}")
        
    def _newPage(self):
        page = PlotPage()
        self.stack.insertWidget(self._pageCount, page)
        return page
    
    def _previousPage(self):
        """ Go to previous page """
        self.page -= 1
        
    def _nextPage(self):
        """ Go to next page """
        self.page += 1
        
    @property
    def rows(self):
        """ Return user's chosen number of rows for plot grid """
        return self.rowsBox.value()
    
    @property
    def cols(self):
        """ Return user's chosen number of columns for plot grid """
        return self.colsBox.value()
    
    @property
    def _pageCount(self):
        """ Return number of pages required to show all plots in _plots list """
        pages = int(np.ceil(len(self._plots) / (self.rows * self.cols)))
        return pages
        
    @property
    def sr(self):
        """ Return sample rate of audio """
        return self._sr
    
    @sr.setter
    def sr(self, value):
        self._sr = value
        
    def setSampleRate(self, value):
        """ Set sample rate """
        self.sr = value
        
    def _resetGrid(self):
        """ Remove all plots and re-add them with current grid dimensions """
        # remove all pages (but keep _plots list)
        self._clearStack()
        
        # new first page
        page = self._newPage()
        row, col = 0, 0
            
        # add plots
        for p, _ in self._plots:
            if row >= self.rows:
                page = self._newPage()
                row, col = 0, 0
                
            page.addPlot(p, row, col)
                
            col += 1
            if col == self.cols:
                col = 0
                row += 1
        self.page = 1
        
    def clear(self):
        """ Remove all pages from stack """
        self._plots = []
        self._clearStack()
        
    def _clearStack(self):
        """ Remove all widgets from stack and reset current page index """
        for idx in reversed(range(self.stack.count())):
            widget = self.stack.widget(idx)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.page = 0
        
    def _ensurePlotVisible(self, plot):
        """ Show page containing `plot` """
        for idx in range(self._pageCount):
            page = self.stack.widget(idx)
            if plot in page:
                self.page = idx
                return idx
        return None
        
    def addPlots(self, freqs, segments) -> list[int]:
        """ Create empty plots for the given segments, which will contain data for the given frequencies 
        
            Return list of indices of the plots.
        """
        
        if self._pageCount == 0:
            page = self._newPage()
            row, col = 0, 0
        else:
            page = self.stack.widget(self._pageCount-1)
            row, col = page.getNextRowCol()
        
        if len(self._plots) == 0:
            self.legendWidget.makeLegend(freqs, self.colours)
        
        idx = []
        
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
                
            p = PlotWidget(self, title=title, freqs=freqs)
            p.highlightChannel.connect(self.legendWidget.highlightLabel)
            page.addPlot(p, row, col)
            idx.append(len(self._plots))
            self._plots.append((p, segment))
                
            if self.sr is not None:
                p.setLabel('bottom', "Time", units="s")
            else:
                p.setLabel('bottom', "Samples")
                
            col += 1
            if col == self.cols:
                col = 0
                row += 1
                
        return idx
    
    def addData(self, idx, data):
        """ Plot `data` on plot for `segment` """
        p, segment = self._plots[idx]
        
        chans, size = data.shape
        
        s0, s1 = segment.samples
        
        if self.sr is not None:
            t = np.linspace(s0/self.sr, s1/self.sr, size)
        else:
            t = np.linspace(s0, s1, size)
        
        colours = itertools.cycle(self.colours)
        
        for k, resp in enumerate(data):
            pen = next(colours)
            p.plot(t, resp, pen=pen, name=p.freqs[k])
            
        self._ensurePlotVisible(p)
