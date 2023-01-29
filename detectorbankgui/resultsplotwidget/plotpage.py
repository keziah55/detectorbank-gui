#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page to be added to StackedWidget, holding a grid of plots.
"""

from qtpy.QtWidgets import QWidget, QGridLayout

class PlotPage(QWidget):
    """ Widget with grid layout of PlotWidgets to be used as QStackedWidget page """
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        
    def __contains__(self, plot):
        for idx in range(self.layout.count()):
            item = self.layout.itemAt(idx)
            if item is not None:
                if item.widget() == plot:
                    return True
        return False
        
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