#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QScrollArea where :class:`SegmentWidgets` can be added or removed.
"""
from qtpy.QtWidgets import QVBoxLayout, QWidget, QPushButton, QScrollArea
from qtpy.QtCore import Signal,  Qt, QSize
from qtpy.QtGui import QIcon
from .segmentwidget import SegmentWidget

class SegmentList(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.widget = _SegmentList(*args, **kwargs)
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
    def __getattr__(self, name):
        return getattr(self.widget, name)

class _SegmentList(QWidget):
    
    requestAddSegment = Signal()
    """ **signal** requestAddSegment() 
    
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
    
    def __init__(self, defaultMin=None, defaultMax=None):
        super().__init__()
        
        self._min = defaultMin
        self._max = defaultMax
        
        if (icon := QIcon.fromTheme('list-add')) is not None:
            self.addButton = QPushButton(icon, "")
        else:
            self.addButton = QPushButton("Add")
        self.addButton.setToolTip("Add new segment")
            
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.addButton)
        self.layout.addStretch()
        self.setLayout(self.layout)
        
        self.addButton.clicked.connect(self.requestAddSegment)
        
    def sizeHint(self):
        if self.layout.count() > 3:
            return super().sizeHint()
        else:
            height = super().sizeHint().height()
            btn = self._makeRemoveButton()
            width = super().sizeHint().width() + btn.minimumSizeHint().width() + 20 # scroll bar pad
            return QSize(width, height)
        
    def addSegment(self, start=None, stop=None, colour=None):
        """ Add spin boxes for a new segment """
        
        row = self.layout.count() - 1 # last item is stretch
        
        if start is None:
            start = self._min
        if stop is None:
            stop = self._max
        
        segment = SegmentWidget(start, stop, colour=colour)
        self.layout.insertWidget(row, segment)
        segmentLayout = segment.layout()
        segment.startValueChanged.connect(lambda value: self.segmentRangeChanged.emit(row-1, value, None))
        segment.stopValueChanged.connect(lambda value: self.segmentRangeChanged.emit(row-1, None, value))
        
        if row > 1:
            # don't add remove button to first segment
            removeButton = self._makeRemoveButton()
            removeButton.setToolTip("Remove this segment")
            segmentLayout.addWidget(removeButton)
            removeButton.clicked.connect(lambda: self._emitRemoveSegment(row))
        else:
            segmentLayout.addStretch()
            
    def setMaximum(self, value):
        """ Set maximum value for all segments """
        self._max = value
        for row in range(1, self.layout.count()):
            if (widget := self.layout.itemAt(row).widget()) is not None:
                widget.setMaximum(self._max)
            
    def setMinimum(self, value):
        """ Set minimum value for all segments """
        self._min = value
        for row in range(1, self.layout.count()):
            if (widget := self.layout.itemAt(row).widget()) is not None:
                widget.setMinimum(self._min)
            
    def setSegmentRange(self, idx, start=None, stop=None):
        """ Set start/stop value of segment `idx` """
        if (widget := self.layout.itemAt(idx+1).widget()) is not None:
            if start is not None:
                widget.setStart(start)
            if stop is not None:
                widget.setStop(stop)
            
    def _emitRemoveSegment(self, row):
        """ Emit :attr:`requestRemoveSegment` with correct index. """
        self.requestRemoveSegment.emit(row-1)
            
    def removeSegment(self, idx):
        """ Remove segment from row `idx+1` in layout (note that row 0 is 'add button') """
        row = idx + 1
        if (widget := self.layout.itemAt(row).widget()) is not None:
            self.layout.removeWidget(widget)
            widget.deleteLater()
                
    def _makeRemoveButton(self):
        if (icon := QIcon.fromTheme('list-remove')) is not None:
            button = QPushButton(icon, "")
        else:
            button = QPushButton("Remove")
        # button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        return button
    
    def _clearSegments(self):
        for row in reversed(range(1, self.layout.rowCount())-1):
            self.removeSegment(row)