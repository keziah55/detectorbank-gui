#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget to display audio and select segments
"""
from pyqtgraph import PlotWidget, LinearRegionItem, InfiniteLine, mkColor
from qtpy.QtCore import Signal, Slot, Qt, QBuffer, QByteArray, QIODevice
from qtpy.QtWidgets import (QHBoxLayout, QVBoxLayout, QWidget, QMenu, QLabel, 
                            QPushButton, QFileDialog, QMessageBox)
from qtpy.QtGui import QCursor
from customQObjects.gui import getIconFromTheme
from .segmentlist import SegmentList
from ..audioread import read_audio
import numpy as np
import itertools
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from pathlib import Path

import qtpy
if qtpy.QT_VERSION.split('.')[0] == '6':
    from qtpy.QtMultimedia import QAudio, QAudioFormat, QAudioSink
else:
    from qtpy.QtMultimedia import QAudio, QAudioFormat, QAudioOutput as QAudioSink
    
def qaudio_state_is_active(state):
    if qtpy.API_NAME == "PyQt6":
        # don't know why this is different in pyqt6
        active_state = QAudio.State.ActiveState
    else:
        # PyQt5, PySide2, PySide6
        active_state = QAudio.ActiveState
    return state == active_state
    
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
    id: UUID = field(default_factory=uuid4)
    
    @property
    def samples(self):
        """ Return tuple of start and stop times in samples """
        if self.sr is not None:
            return tuple([int(t*self.sr) for t in self.time])
        else:
            return None
    
    @property
    def time(self):
        """ Return tuple of start and stop times in seconds """
        return (self.start, self.stop)

class AudioPlotWidget(QWidget):
    """ Widget to display audio plot and segment list and keep them synchronised """
    
    statusMessage = Signal(str)
    """ **signal** statusMessage(str `msg`)
    
        Emitted with a message for the status bar.
    """
    
    audioFileOpened = Signal(int)
    """ **signal** audioFileOpened(int `sr`)
    
        Emitted when audio file is read.
    """
    
    def __init__(self, parent=None):
        
        super().__init__(parent=parent)
        
        self._makeColourIter()
        
        self.plotLabel = QLabel(self)
        self.plotWidget = AudioPlot(self)
        self.segmentList = SegmentList(self)
        
        self.openAudioButton = QPushButton(self)
        if (icon := getIconFromTheme("audio-x-generic")) is not None:
            self.openAudioButton.setIcon(icon)
        else:
            self.openAudioButton.setText("Select audio file")
        self.openAudioButton.setToolTip("Select audio file to analyse")
        
        self.segmentList.requestAddSegment.connect(self.addSegment)
        self.segmentList.requestRemoveSegment.connect(self.removeSegment)
        self.segmentList.requestRemoveAllSegments.connect(self.removeAllSegments)
        self.segmentList.requestSetSegmentRange.connect(self.setSegmentRange)
        self.plotWidget.requestAddSegment.connect(self.addSegment)
        self.plotWidget.requestRemoveSegment.connect(self.removeSegment)
        self.plotWidget.requestSetSegmentRange.connect(self.setSegmentRange)
        
        self.plotWidget.valuesUnderMouse.connect(self.setCrosshairLabel)
        
        self.openAudioButton.clicked.connect(self._openAudioFile)
        
        self.audioOutput = None
        self.audioFormat = QAudioFormat()
        self.audioFormat.setChannelCount(1)
        # QAudioFormat API has changed between qt5 and qt6
        if qtpy.QT_VERSION.split('.')[0] == '6':
            # pyside6 and pyqt6 handle sample format enum differently 
            # and this is not dealt with by qtpy
            try:
                self.audioFormat.setSampleFormat(QAudioFormat.Float) # pyside6
            except AttributeError:
                self.audioFormat.setSampleFormat(QAudioFormat.SampleFormat.Float) # pyqt6
        else:
            self.audioFormat.setSampleType(QAudioFormat.Float)
            self.audioFormat.setSampleSize(32)
            self.audioFormat.setCodec("audio/pcm")
        self.audioBuffer = QBuffer()
        
        self._playingSegment = None
        self.segmentList.requestPlaySegment.connect(self._requestPlaySegment)
        self.segmentList.requestStopSegment.connect(self._requestStopSegment)
        
        plotLayout = QVBoxLayout()
        plotLayout.addWidget(self.plotWidget)
        plotLayout.addWidget(self.plotLabel)
        
        rightLayout = QVBoxLayout()
        rightLayout.addWidget(self.openAudioButton)
        rightLayout.addWidget(self.segmentList)
        
        layout = QHBoxLayout()
        layout.addLayout(plotLayout)
        layout.addLayout(rightLayout)
        
        self.setLayout(layout)
        
        self._openAudioDir = Path.cwd()
        self.audioFilePath = None
        self.audio = None
        self.sr = None
        self._max = 1
        self.addSegment(start=0, stop=self._max)
        
    @property
    def audioFilePath(self):
        return self._currentAudioFile
    
    @audioFilePath.setter
    def audioFilePath(self, p):
        self._currentAudioFile = p
        
    def _openAudioFile(self):
        """ Show open file dialog """
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select audio file", self._openAudioDir, "Wav files (*.wav);;All files (*)")
        if fname:
            self.openAudioFile(fname)
            
    def openAudioFile(self, fname):
        """ Read audio file and set audio plot """
        if not isinstance(fname, Path):
            fname = Path(fname)
        try:
            self.audio, self.sr = read_audio(fname)
        except Exception as err:
            msg = f"Opening '{fname.name}' failed with error:\n{err}"
            QMessageBox.warning(self, "Cannot open audio file", msg)
        else:
            self.setAudio(self.audio, self.sr)
            self.removeAllSegments()
            self._openAudioDir = fname.parent
            self.audioFilePath = fname
            self.audioFileOpened.emit(self.sr)
            self.statusMessage.emit(f"Opened {fname.name}; sample rate {self.sr}Hz")
        
    def setAudio(self, audio, sr):
        """ Set audio and sample rate. """
        self.audio = audio
        self.sr = sr
        self.plotWidget.setAudioData(audio, self.sr)
        self._max = len(audio)/self.sr
        self.segmentList.setMaximum(self._max)
        
        if self.audioOutput is not None:
            self.audioOutput.stateChanged.disconnect()
        self.audioFormat.setSampleRate(sr)
        self.audioOutput = QAudioSink(self.audioFormat, self)
        self.audioOutput.stateChanged.connect(self._audioStateChanged)
        
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
        
    def removeAllSegments(self):
        for idx in reversed(range(len(self.segmentList))):
            self.removeSegment(idx)
        self._makeColourIter()
        self.addSegment(start=0, stop=self._max)
        
    def setSegmentRange(self, idx, start=None, stop=None):
        """ Update range of segment `idx` in both plot and list. """
        self.plotWidget.setSegmentRange(idx, start=start, stop=stop)
        self.segmentList.setSegmentRange(idx, start=start, stop=stop)
        
    def getSegments(self) -> list[Segment]:
        """ Return list of Segments """
        return self.plotWidget.segments
    
    def setCrosshairLabel(self, x, y):
        """ Set plot label text """
        if self.sr is not None and x >= 0:
            self.plotLabel.setText(f"{x:g} seconds; {int(x*self.sr)} samples")
        
    def _requestPlaySegment(self, segment):
        """ Play audio in `segment` """
        if self.sr is None or self.audio is None:
            return None
        start, stop = [int(t*self.sr) for t in segment.values]
        if start < 0:
            start = 0
        if stop >= len(self.audio):
            stop = len(self.audio) - 1
        audio = self.audio[start:stop]
        
        self._requestStopSegment()
        
        data = QByteArray(audio.tobytes())
        self.audioBuffer.setData(data)
        self.audioBuffer.open(QIODevice.ReadOnly)
        self.audioBuffer.seek(0)
        
        self._playingSegment = segment
        self.audioOutput.start(self.audioBuffer)
                
    def _requestStopSegment(self):
        """ Stop any playing audio """
        if qaudio_state_is_active(self.audioOutput.state()):
            self.audioOutput.stop()
        if self.audioBuffer.isOpen():
            self.audioBuffer.close()
            
    def _audioStateChanged(self, state):
        # update SegmentWidget button icon
        if qaudio_state_is_active(state):
            self._playingSegment.playing = True
        else:
            self._playingSegment.playing = False
            
    def _makeColourIter(self):
        alpha = "32"
        colours = ["#0000ff", "#ff0000", "#00ff00", "#ffe523", "#ed21ff", 
                   "#ff672b", "#9718ff", "#00ffaa"]
        self._segmentColours = itertools.cycle([mkColor(f"{colour}{alpha}") for colour in colours])
        
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
        self.sr = None
        
        self.parent = parent
        
        # cross hairs
        self.vLine = InfiniteLine(angle=90, movable=False)
        self.hLine = InfiniteLine(angle=0, movable=False)
        self.plotItem.addItem(self.vLine, ignoreBounds=True)
        self.plotItem.addItem(self.hLine, ignoreBounds=True)
        self.plotItem.scene().sigMouseMoved.connect(self.mouseMoved)
        
        # context menu
        self.contextMenu = QMenu()
        self._addAction = self.contextMenu.addAction("Add region")
        self._addAction.triggered.connect(self._addSegmentAtMouse)
        self._removeAction = self.contextMenu.addAction("Remove region")
        self._removeAction.triggered.connect(self._removeSegmentAtMouse)
        self._contextMenuPos = None
        self.plotItem.setMenuEnabled(False)
        
        self.plotItem.setLabel('bottom',text='Time (s)')
        
        self.plotItem.showGrid(True, True)
        
    @property
    def segments(self) -> list[Segment]:
        """ Return list of SegmentRanges """
        segs = sorted(self._segments, key=lambda seg: seg.getRegion()[0])
        segs = [Segment(*segment.getRegion(), self.sr, segment.brush.color().name()) 
                for idx, segment in enumerate(segs)]
        return segs
    
    def setAudioData(self, data, sr):
        """ Plot `data`, with sample rate `sr`. """
        for dataitem in self.plotItem.listDataItems():
            self.plotItem.removeItem(dataitem)
        self.sr = sr
        x = np.linspace(0, len(data)/sr, len(data))
        self.plot(x, data)
        self._segments[0].sr = sr
        self._segments[0].setRegion((0, len(data)/sr))
        
    def addSegment(self, start=None, stop=None, colour=None):
        """ Add a new segment selection, optionally supplying range. """
        segment = LinearRegionItem(brush=colour)
        self._setSegmentRange(segment, start, stop)
        self.plotItem.addItem(segment)
        segment.sigRegionChangeFinished.connect(self._emitSetSegmentRange)
        self._segments.append(segment)
        
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
                    self.parent.statusMessage.emit("Cannot remove first region")
                except:
                    pass
            
    @Slot(object)
    def mouseMoved(self, pos):
        if self.plotItem.sceneBoundingRect().contains(pos):
            mousePoint = self.plotItem.vb.mapSceneToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            self.valuesUnderMouse.emit(mousePoint.x(), mousePoint.y())