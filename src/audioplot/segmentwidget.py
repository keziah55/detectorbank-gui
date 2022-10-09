#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget managing two spin boxes, to set the start and stop points of a segment.
"""
from qtpy.QtWidgets import QHBoxLayout, QWidget, QDoubleSpinBox
from qtpy.QtCore import Signal, Slot

class SegmentWidget(QWidget):
    """ Widget managing two spin boxes, to set the start and stop points of a segment.
    
        Signals :attr:`startValueChanged` and :attr:`stopValueChanged` are emitted
        when the values are changed. This widget also ensures that, for each 
        spin box, start <= value <= stop.
        
        Parameters
        ----------
        minimum : float, optional
            Minimum value for the spinboxes. Default is 0. See also :meth:`setMinimum`
        maximum : float, optional
            Maximum value for the spinboxes. Default is unset. See also :meth:`setMaximum`
    """
    
    startValueChanged = Signal(float)
    stopValueChanged = Signal(float)
    
    def __init__(self, minimum=None, maximum=None):
        super().__init__()
        
        self.startbox = QDoubleSpinBox()
        self.stopbox = QDoubleSpinBox()
        
        if minimum is None:
            minimum = 0
        self.setMinimum(minimum)
        
        if maximum is not None:
            self.setMaximum(maximum)
            
        self.startbox.valueChanged.connect(self._startChanged)
        self.stopbox.valueChanged.connect(self._stopChanged)
        
        layout = QHBoxLayout()
        for spinbox in self.boxes:
            layout.addWidget(spinbox)
            
        self.setLayout(layout)
        
    @property
    def boxes(self):
        """ Return both spinboxes managed by this widget """
        return [self.startbox, self.stopbox]
    
    def setMinimum(self, minimum):
        """ Set minimum value of both spinboxes """
        for spinbox in self.boxes:
            spinbox.setMinimum(minimum)
            
    def setMaximum(self, maximum):
        """ Set maximum value of both spinboxes """
        for spinbox in self.boxes:
            spinbox.setMaximum(maximum)
            
    def setStart(self, value):
        """ Set `start` value """
        self.startbox.setValue(value)
        
    def setStop(self, value):
        """ Set `stop` value """
        self.stopbox.setValue(value)
            
    @Slot(float)
    def _startChanged(self, value):
        """ Emit :attr:`startValueChanged`. 
        
            If `value` greater than current stop value, update it and emit :attr:`stopValueChanged`
        """
        if value > self.stopbox.value():
            self.stopbox.setValue(value)
            self.stopValueChanged.emit(value)
        self.startValueChanged.emit(value)
            
    @Slot(float)
    def _stopChanged(self, value):
        """ Emit :attr:`stopValueChanged`. 
        
            If `value` less than current start value, update it and emit :attr:`startValueChanged`
        """
        if value < self.startbox.value():
            self.startbox.setValue(value)
            self.startValueChanged.emit(value)
        self.stopValueChanged.emit(value)
        
        