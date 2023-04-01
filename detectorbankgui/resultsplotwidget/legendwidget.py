#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Legend for all plots
"""
from pyqtgraph import LegendItem, PlotDataItem
from qtpy.QtWidgets import  QGraphicsView, QGraphicsScene
import itertools

class LegendWidget(QGraphicsView):
    """ Widget showing legend for all plots """
    
    def __init__(self, parent):
        super().__init__(parent)
        self._width = parent.size().width()
        self._itemWidth = 180
        self._highlighted = None
        self.legendItem = LegendItem()
        self._scene = QGraphicsScene(parent=self)
        self.setScene(self._scene)
        self.scene().addItem(self.legendItem)
        
    def makeLegend(self, freqs, colours):
        """ Create legend from list of frequencies and colours """
        cols = self._width // self._itemWidth
        self.legendItem.setColumnCount(cols)
        for freq, colour in zip(freqs, itertools.cycle(colours)):
            item = PlotDataItem(pen=colour)
            label = f"{freq:g}Hz"
            self.legendItem.addItem(item, label)
            
        self._labelItems = [self.legendItem.layout.itemAt(idx) 
                            for idx in range(1, self.legendItem.layout.count(), 2)] # label is every second item in layout
        self._labelColour = self._labelItems[0].opts['color']
        self._labelItems = list(zip(self._labelItems, itertools.cycle(colours)))
        
    def updateWidth(self, width):
        """ Update the width of the legend """
        cols = width // self._itemWidth
        if cols == 0:
            return
        self._width = width
        self.legendItem.setColumnCount(cols)
        
    def highlightLabel(self, channel=None):
        """ Highlight the text of the chosen channel's label """
        if self._highlighted is not None:
            labelItem, _ = self._labelItems[self._highlighted]
            labelItem.setText(labelItem.text, bold=False, color=self._labelColour)
            
        if channel is not None:
            labelItem, colour = self._labelItems[channel]
            labelItem.setText(labelItem.text, bold=True, color=colour)
        self._highlighted = channel
        
    def clear(self):
        """ Remove all items from legend """
        self.legendItem.clear()