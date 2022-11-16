#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget to display audio and select segments
"""
from pyqtgraph import PlotWidget, LinearRegionItem, InfiniteLine, mkColor
from qtpy.QtCore import Signal, Slot, Qt, QObject, QThread
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QMenu, QLabel
from qtpy.QtGui import QCursor
from .segmentlist import SegmentList

import numpy as np
import itertools
from dataclasses import dataclass
from collections import deque, namedtuple
import sounddevice as sd


class AudioPlayWorker(QObject):
    
    stopped = Signal()
    
    stoppedManually = Signal()
    
    def __init__(self, audio=None, sr=None):
        super().__init__()
        self.audio = None
        self.sr = None
        
        self._fadeSize = 10 # number of samples over which to fade in and out
        
        self.setParams(audio, sr)
        
        
    def setParams(self, audio=None, sr=None):
        if audio is not None:
            fade = np.concatenate((
                np.linspace(0, 1, num=self._fadeSize, dtype=np.float32),
                np.ones(len(audio)-2*self._fadeSize, dtype=np.float32),
                np.linspace(1, 0, num=self._fadeSize, dtype=np.float32)))
            self.audio = audio * fade
        if sr is not None:
            self.sr = sr
        
    def play(self):
        print("worker play")
        sd.play(self.audio, self.sr, blocking=True)
        self.stopped.emit()
        
    def stop(self):
        print("worker stop")
        sd.stop()
        print("worker stopped")
        self.stoppedManually.emit()
        
PlayQueueItem = namedtuple("PlayAudio", ["segment", "audio", "sr"])

@dataclass
class Segment:
    """ Class to store start and stop values of a segment.
    
        By default these are stored as times; the equivalent sample values can 
        be accesssed via :meth:`samples`
        
        The segment's colour is also stored
    """
    start: float
    stop: float
    sr: int
    colour: str = None
    idx: int = None
    
    @property
    def samples(self):
        """ Return tuple of start and stop times in samples """
        return tuple([int(t*self.sr) for t in self.time])
    
    @property
    def time(self):
        """ Return tuple of start and stop times in seconds """
        return (self.start, self.stop)

class AudioPlotWidget(QWidget):
    
    statusMessage = Signal(str)
    """ **signal** statusMessage(str `msg`)
    
        Emitted with a message for the status bar.
    """
    
    def __init__(self, parent=None):
        
        super().__init__(parent=parent)
        
        alpha = "32"
        colours = ["#0000ff", "#ff0000", "#00ff00", "#ffe523", "#ed21ff", 
                   "#ff672b", "#9718ff", "#00ffaa"]
        self._segmentColours = itertools.cycle([mkColor(f"{colour}{alpha}") for colour in colours])
        
        self.plotLabel = QLabel(self)
        self.plotWidget = AudioPlot(self)
        self.segmentList = SegmentList(self)
        
        self.segmentList.requestAddSegment.connect(self.addSegment)
        self.segmentList.requestRemoveSegment.connect(self.removeSegment)
        self.segmentList.requestSetSegmentRange.connect(self.setSegmentRange)
        self.plotWidget.requestAddSegment.connect(self.addSegment)
        self.plotWidget.requestRemoveSegment.connect(self.removeSegment)
        self.plotWidget.requestSetSegmentRange.connect(self.setSegmentRange)
        
        self.plotWidget.valuesUnderMouse.connect(self.setCrosshairLabel)
        
        self._playQueue = deque()
        self._playWorker = AudioPlayWorker()
        
        self._playThread = QThread()
        self._playThread.setTerminationEnabled()
        self._playWorker.moveToThread(self._playThread)
        self._playThread.started.connect(self._playWorker.play)
        self._playWorker.stopped.connect(self._playFinished)
        self._playWorker.stoppedManually.connect(self._playThread.quit)
        self._playThread.finished.connect(self._playFromQueue)
        
        self._playingSegment = None
        self.segmentList.requestPlaySegment.connect(self._requestPlaySegment)
        self.segmentList.requestStopSegment.connect(self._requestStopSegment)
        
        plotLayout = QVBoxLayout()
        plotLayout.addWidget(self.plotWidget)
        plotLayout.addWidget(self.plotLabel)
        
        hbox = QHBoxLayout()
        # hbox.addWidget(self.plotWidget)
        hbox.addLayout(plotLayout)
        hbox.addWidget(self.segmentList)
        
        self.setLayout(hbox)
        
        self.audio = None
        self.sr = None
        self._max = 1
        self.addSegment(start=0, stop=self._max)
        
    def setAudio(self, audio, sr):
        """ Set audio and sample rate. """
        self.audio = audio
        self.sr = sr
        self.plotWidget.setAudioData(audio, self.sr)
        self._max = len(audio)/self.sr
        self.segmentList.setMaximum(self._max)
        
    def addSegment(self, start=None, stop=None):
        """ Add segment in both plot and list. """
        colour = next(self._segmentColours)
        if start is None and len(self.plotWidget._segments) > 0:
            # use time of last segment as start of new segment
            start = max([segment.getRegion()[1] for segment in self.plotWidget._segments])
            if start > self._max:
                start = self._max
        if stop is None:
            stop = start + 1
        self.plotWidget.addSegment(start=start, stop=stop, colour=colour)
        self.segmentList.addSegment(start=start, stop=stop, colour=colour)
        
        msg = "New segment added"
        if start is not None:
            msg += f" at {start:g}s"
        self.statusMessage.emit(msg)
        
    def removeSegment(self, idx):
        """ Remove segment at index `idx` from both plot and list. """
        self.plotWidget.removeSegment(idx)
        self.segmentList.removeSegment(idx)
        self.statusMessage.emit("Segment removed")
        
    def setSegmentRange(self, idx, start=None, stop=None):
        """ Update range of segment `idx` in both plot and list. """
        self.plotWidget.setSegmentRange(idx, start=start, stop=stop)
        self.segmentList.setSegmentRange(idx, start=start, stop=stop)
        
    def getSegments(self) -> list[tuple]:
        """ Return list of start/stop samples """
        return self.plotWidget.segments #[segment.samples for segment in self.plotWidget.segments]
    
    def setCrosshairLabel(self, x, y):
        """ Set plot label text """
        if self.sr is not None and x >= 0:
            self.plotLabel.setText(f"{x:g} seconds; {int(x*self.sr)} samples")
        
    def _requestPlaySegment(self, segment):
        if self.sr is None or self.audio is None:
            return None
        start, stop = [int(t*self.sr) for t in segment.values]
        if start < 0:
            start = 0
        if stop >= len(self.audio):
            stop = len(self.audio) - 1
        audio = self.audio[start:stop]
        playAudioInfo = PlayQueueItem(segment, audio, self.sr)
        self._playQueue.append(playAudioInfo)
        print(f"added {start/self.sr:g} to {stop/self.sr:g} to queue")
        self._requestStopSegment()
        
    def _playFromQueue(self):
        print(f"thread running: {self._playThread.isRunning()}")
        if len(self._playQueue) == 0:
            print("nothing in queue")
            return None
        segment, audio, sr = self._playQueue.popleft()
        print(f"about to play {segment.values[0]} to {segment.values[1]}")
        print("playing")
        self._playingSegment = segment
        self._playWorker.setParams(audio, sr)
        self._playThread.start()
        
    def _requestStopSegment(self):
        import inspect; print(f"_requestStopSegment called by {inspect.stack()[1].function}; thread running: {self._playThread.isRunning()}")
        self.segmentList.stopSegment(self._playingSegment)
        if self._playThread.isRunning():
            print("thread is running")
            self._playWorker.stop()
            self._playThread.quit()
            # self._playThread.wait()
            # print("wait returned")
        else:
            self._playFromQueue()
            
    def _playFinished(self):
        self.segmentList.stopSegment(self._playingSegment)
        self._playingSegment = None
        self._playThread.quit()
        print(f"play finished normally; thread running: {self._playThread.isRunning()}")
        
        
class AudioPlot(PlotWidget):
    
    requestAddSegment = Signal(object, object)
    """ **signal** requestAddSegment(float `start`, float `stop`) 
    
        Emitted when 'add segment' selected in context menu.
    """
    
    requestRemoveSegment = Signal(int)
    """ **signal** requestRemoveSegment(int `index`)
    
        Emitted when 'remove segment' selected in context menu.
    """
    
    requestSetSegmentRange = Signal(int, object, object)
    """ **signal** requestSetSegmentRange(int `idx`, float `start`, float `stop`) 
    
        Emitted when a segment range is change by user.
    """
    
    valuesUnderMouse = Signal(float, float)
    """ **signal** valuesUnderMouse(float `x`, float `y`)
    
        Emitted when mouse hovers over plot.
    """
    
    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(parent=parent)
        self._segments = []
        
        self.parent = parent
        
        # cross hairs
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.plotItem.addItem(self.vLine, ignoreBounds=True)
        self.plotItem.addItem(self.hLine, ignoreBounds=True)
        self.plotItem.scene().sigMouseMoved.connect(self.mouseMoved)
        
        # context menu
        self.contextMenu = QMenu()
        self._addAction = self.contextMenu.addAction("Add segment")
        self._addAction.triggered.connect(self._addSegmentAtMouse)
        self._removeAction = self.contextMenu.addAction("Remove segment")
        self._removeAction.triggered.connect(self._removeSegmentAtMouse)
        self._contextMenuPos = None
        self.plotItem.setMenuEnabled(False)
        
        self.plotItem.setLabel('bottom',text='Time (s)')
        
        self.plotItem.showGrid(True, True)
        
    @property
    def segments(self) -> list[Segment]:
        """ Return list of SegmentRanges """
        segs = sorted(self._segments, key=lambda seg: seg.getRegion()[0])
        segs = [Segment(*segment.getRegion(), self.sr, segment.brush.color().name(), idx=idx) 
                for idx, segment in enumerate(segs)]
        return segs
    
    def setAudioData(self, data, sr):
        """ Plot `data`, with sample rate `sr`. """
        for dataitem in self.plotItem.listDataItems():
            self.plotItem.removeItem(dataitem)
            
        self.sr = sr
        x = np.linspace(0, len(data)/sr, len(data))
        self.plot(x, data)
        self._segments[0].setRegion((0, len(data)/sr))
        
    def addSegment(self, start=None, stop=None, colour=None):
        """ Add a new segment selection, optionally supplying range. """
        segment = LinearRegionItem(brush=colour)
        self._setSegmentRange(segment, start, stop)
        self.plotItem.addItem(segment)
        self._segments.append(segment)
        segment.sigRegionChangeFinished.connect(self._emitSetSegmentRange)
        
    def removeSegment(self, idx):
        """ Remove segment at index `idx`. """
        segment = self._segments.pop(idx)
        self.plotItem.removeItem(segment)
        
    def _emitSetSegmentRange(self, segment):
        """ Find `segment` in list and emit :attr:`requestSetSegmentRange` """
        idx = self._segments.index(segment)
        start, stop = segment.getRegion()
        self.requestSetSegmentRange.emit(idx, start, stop)
        
    def _setSegmentRange(self, segment, start=None, stop=None):
        """ Set bounds of LinearRegionItem `segment` """
        if start is not None:
            segment.lines[0].setValue(start)
        if stop is not None:
            segment.lines[1].setValue(stop)
        
    def setSegmentRange(self, idx, start=None, stop=None):
        """ Update range of segment `idx` """
        segment = self._segments[idx]
        self._setSegmentRange(segment, start, stop)
        
    def contextMenuEvent(self, event):
        self._contextMenuPos = event.pos()
        self._removeAction.setEnabled(self._allowRemove)
        self.contextMenu.popup(self.mapToGlobal(event.pos()))
        
    @property
    def _contextMenuPos(self):
        """ Return x position of context menu in plot coordinates """
        return self._contextMenuXPos
        
    @_contextMenuPos.setter
    def _contextMenuPos(self, pos):
        if pos is not None:
            pos = self.plotItem.vb.mapSceneToView(pos).x()
        self._contextMenuXPos = pos
        
    @property
    def _allowRemove(self):
        """ Return True if mouse is over a segment and the segment is not the first. """
        underMouse, idx = self._segmentUnderMouse()
        return underMouse and idx > 0 
        
    def _addSegmentAtMouse(self):
        if self._contextMenuPos is not None:
            self.requestAddSegment.emit(self._contextMenuXPos, None)
            
    def _removeSegmentAtMouse(self):
        if self._contextMenuPos is not None:
            pass
        _, idx = self._segmentUnderMouse()
        self.requestRemoveSegment.emit(idx)
            
    def _segmentUnderMouse(self):
        if self._contextMenuPos is None:
            return False, None
        for idx, segment in enumerate(self.segments):
            t0, t1 = segment.time
            if t0 <= self._contextMenuPos <= t1:
                return True, idx
        return False, None
    
    def keyPressEvent(self, event):
        """ If delete key pressed over segment, request its removal """
        if event.key() == Qt.Key_Delete:
            self._contextMenuPos = self.mapFromGlobal(QCursor.pos())
            if self._allowRemove:
                self._removeSegmentAtMouse()
            else:
                try:
                    self.parent.statusMessage.emit("Cannot remove first segment")
                except:
                    pass
            
    @Slot(object)
    def mouseMoved(self, pos):
        if self.plotItem.sceneBoundingRect().contains(pos):
            mousePoint = self.plotItem.vb.mapSceneToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            self.valuesUnderMouse.emit(mousePoint.x(), mousePoint.y())