#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget managing two spin boxes, to set the start and stop points of a segment.
"""
from qtpy.QtWidgets import QHBoxLayout, QWidget, QDoubleSpinBox, QPushButton
from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QPalette, QIcon

class SegmentWidget(QWidget):
    """ Widget managing two spin boxes, to set the start and stop points of a segment.
    
        Signals :attr:`startValueChanged` and :attr:`stopValueChanged` are emitted
        when the values are changed. This widget also ensures that, for each 
        spin box, start <= value <= stop.
        
        Parameters
        ----------
        start : float, optional
            Initial start value. Default is 0
        stop : float, optional
            Initial stop value. Default is 0
        minimum : float, optional
            Minimum value for the spinboxes. Default is 0. See also :meth:`setMinimum`
        maximum : float, optional
            Maximum value for the spinboxes. Default is unset. See also :meth:`setMaximum`
    """
    
    startValueChanged = Signal(float)
    stopValueChanged = Signal(float)
    
    requestPlaySegment = Signal(object)
    """ **signal** requestPlaySegment(SegmentWidget `self`) 
    
        Emitted when user requests segment be played, with the reference to this segment.
    """
    
    requestStopSegment = Signal()
    
    def __init__(self, start=None, stop=None, minimum=None, maximum=None, colour=None):
        super().__init__()
        
        # if (icon := QIcon.fromTheme('media-playback-start')) is not None:
        #     self.playButton = QPushButton(icon, "")
        # else:
        self.playButton = QPushButton()
        self.startbox = QDoubleSpinBox()
        self.stopbox = QDoubleSpinBox()
        
        palette = self.startbox.palette()
        if colour is not None:
            palette.setColor(QPalette.Base, colour)
        for box in self.boxes:
            box.setPalette(palette)
        
        if minimum is None:
            minimum = 0
        self.setMinimum(minimum)
        
        if maximum is not None:
            self.setMaximum(maximum)
            
        if start is not None:
            self.startbox.setValue(start)
            
        if stop is not None:
            self.stopbox.setValue(stop)
            
        self.startbox.valueChanged.connect(self._startChanged)
        self.stopbox.valueChanged.connect(self._stopChanged)
        self.playButton.clicked.connect(lambda *args: self.playStopSegment(emit=True))
        
        self.playing = False
        
        layout = QHBoxLayout()
        for widget in [self.playButton] + self.boxes:
            layout.addWidget(widget)
            
        self.setLayout(layout)
        
    @property
    def boxes(self):
        """ Return both spinboxes managed by this widget """
        return [self.startbox, self.stopbox]
    
    @property
    def values(self):
        return [box.value() for box in self.boxes]
    
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
        
    @property
    def playing(self):
        """ Return True if audio is playing """
        return self._playing 
    
    @playing.setter
    def playing(self, isPlaying):
        self._playing = isPlaying
        if self._playing is False:
            if (icon := QIcon.fromTheme('media-playback-start')) is not None:
                self.playButton.setIcon(icon)
            else:
                self.playButton.setText("Play")
        else:
            if (icon := QIcon.fromTheme('media-playback-stop')) is not None:
                self.playButton.setIcon(icon)
            else:
                self.playButton.setText("Stop")
        
    def playStopSegment(self, play=None, emit=False):
        """ Emit :attr:`requestPlaySegment`. """
        import inspect; print(f"playStopSegment called by {inspect.stack()[1].function}; {play=}; {emit=}")
        if play is None:
            self.playing = not self.playing
        elif self.playing == play: # nothing to be done
            return None
        else:
            self.playing = play
        print(f"{self.values} playStopSegment set playing to {self.playing}")
        if emit:
            if self.playing:
                self.requestPlaySegment.emit(self)
            else:
                self.requestStopSegment.emit()
        
        