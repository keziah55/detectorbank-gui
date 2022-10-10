#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QScrollArea where :class:`SegmentWidgets` can be added or removed.
"""
from qtpy.QtWidgets import QGridLayout, QWidget, QPushButton, QScrollArea, QSizePolicy
from qtpy.QtCore import Signal, Slot, Qt, QSize
from qtpy.QtGui import QIcon
from .segmentwidget import SegmentWidget
import itertools

class SegmentList(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.widget = _SegmentList(*args, **kwargs)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setFixedWidth(self.widget.width())
        
    def __getattr__(self, name):
        return getattr(self.widget, name)

class _SegmentList(QWidget):
    
    requestNewSegment = Signal()
    """ **signal** requestNewSegment() 
    
        Emitted when 'add' button clicked.
    """
    
    segmentRangeChanged = Signal(int, object, object)
    """ **signal** segmentRangeChanged(int `index`, float `min`, float `max`) 
    
        Emitted when a segment's range changed in spin box.
    """
    
    requestRemoveSegment = Signal(int)
    """ **signal** requestRemoveSegment(int `index`)
    
        Emitted when SegmentWidget removed.
    """
    
    def __init__(self, colours, defaultMin=None, defaultMax=None):
        super().__init__()
        
        self._colours = itertools.cycle(colours)
        self._min = defaultMin
        self._max = defaultMax
        
        if (icon := QIcon.fromTheme('list-add')) is not None:
            self.addButton = QPushButton(icon, "")
        else:
            self.addButton = QPushButton("Add")
            
        self.layout = QGridLayout()
        self.layout.addWidget(self.addButton, 0, 0, 1, 2)
        self.setLayout(self.layout)
        
        self._segments = []
        self.addSegment()
        
        self.addButton.clicked.connect(self.addSegment)
        
    def sizeHint(self):
        if self.layout.rowCount() > 2:
            return super().sizeHint()
        else:
            height = super().sizeHint().height()
            btn = self._makeRemoveButton()
            width = super().sizeHint().width() + 20 # btn.width()
            return QSize(width, height)
        
    def addSegment(self):
        """ Add spin boxes for a new segment """
        
        row = self.layout.rowCount()
        
        colour = next(self._colours)
        segment = SegmentWidget(self._min, self._max, colour=colour)
        self.layout.addWidget(segment, row, 0)
        self._segments.append(segment)
        segment.startValueChanged.connect(lambda value: self.segmentRangeChanged.emit(row-1, value, None))
        segment.stopValueChanged.connect(lambda value: self.segmentRangeChanged.emit(row-1, None, value))
        
        # don't add remove button to first segment
        if row > 1:
            removeButton = self._makeRemoveButton()
            removeButton.setToolTip("Remove this segment")
                
            self.layout.addWidget(removeButton, row, 1)
            removeButton.clicked.connect(lambda: self._removeSegment(row))
            
        self.requestNewSegment.emit()
            
    def setMaximum(self, value):
        """ Set maximum value for all segments """
        self._max = value
        for row in range(1, self.layout.rowCount()):
            widget = self.layout.itemAtPosition(row, 0).widget()
            widget.setMaximum(self._max)
            
    def setMinimum(self, value):
        """ Set minimum value for all segments """
        self._min = value
        for row in range(1, self.layout.rowCount()):
            widget = self.layout.itemAtPosition(row, 0).widget()
            widget.setMinimum(self._min)
            
    def setSegmentRange(self, idx, start=None, stop=None):
        """ Set start/stop value of segment `idx` """
        widget = self.layout.itemAtPosition(idx+1, 0).widget()
        if start is not None:
            widget.setStart(start)
        if stop is not None:
            widget.setStop(stop)
            
    def _removeSegment(self, row):
        """ Remove segment from row `row` in layout (note that row 0 is 'add button') """
        for col in self.layout.columnCount():
            item = self.layout.itemAtPosition(row, col)
            if (widget := item.widget()) is not None:
                self.layout.removeWidget(widget)
                widget.deleteLater()
        self.requestRemoveSegment.emit(row-1)
                
    def _makeRemoveButton(self):
        if (icon := QIcon.fromTheme('list-remove')) is not None:
            button = QPushButton(icon, "")
        else:
            button = QPushButton("Remove")
        button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        return button
    
    def _clearSegments(self):
        for row in reversed(range(2, self.layout.rowCount())):
            self._removeSegment(row)