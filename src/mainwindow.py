#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window
"""
from qtpy.QtWidgets import (QMainWindow, QDockWidget, QAction, QFileDialog, 
                            QMessageBox, QProgressBar, QTabBar, QToolBar)
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon, QKeySequence
from customQObjects.core import Settings
from .audioplot import AudioPlotWidget
from .analyser import Analyser
from .argswidget import ArgsWidget
from .audioread import read_audio
from .hopfplot import HopfPlot
from .preferences import PreferencesDialog
import os
from functools import partial
from collections import deque, namedtuple

SegmentAnalysis = namedtuple("SegmentAnalysis", ["segement", "analyser"])
WidgetView = namedtuple("WidgetView", ["dockwidget", "viewmode"])

class DBGui(QMainWindow):
    
    dockAreas = {'left':Qt.LeftDockWidgetArea, 'right':Qt.RightDockWidgetArea,
                 'top':Qt.TopDockWidgetArea, 'bottom':Qt.BottomDockWidgetArea}
    
    def __init__(self, *args, audioFile=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.prefDialog = PreferencesDialog(self)
        
        self._createActions()
        self._createToolBars()
        self._createMenus()
        
        self.audioplot = AudioPlotWidget(self)
        self.argswidget = ArgsWidget(self)
        self.hopfplot = HopfPlot(self)
        
        self.statusBar()
        self._statusTimeout = 1500
        
        self._progressBar = QProgressBar()
        self.statusBar().addPermanentWidget(self._progressBar)
        self._progressQueue = deque()
        
        self.audioplot.statusMessage.connect(self._setTemporaryStatus)
        self.audioplot.requestSelectAudio.connect(self._openAudioFile)
        
        widgets = {"audioinput":('Audio Input', self.audioplot, 'left', 'input'),
                   "args":('Parameters',self.argswidget, 'left', 'input'),
                   "output":("Output", self.hopfplot, 'right', 'output')}
        
        for key, values in widgets.items():
            name, widget, area, viewmode = values
            self.createDockWidget(widget, area, name, viewmode, key)
        
        self._currentAudioFile = None
        self._openAudioDir = os.getcwd()
        if audioFile is not None:
            self._openAudio(audioFile)
            
        self._viewmode = None
        self.show()
        
        # fileDir = os.path.split(__file__)[0]
        # path = os.path.join(fileDir, "..", "images/icon_alpha.png")
        # icon = QIcon(path)
        # self.setWindowIcon(icon)
        
    def show(self):
        settings = Settings()
        settings.beginGroup("window")
        geometry = settings.value("geometry")
        viewmode = settings.value("viewMode")
        settings.endGroup()
        
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            self.showMaximized()
        if viewmode is None:
            viewmode = "all"
        self._switchView(viewmode, savePrevious=False)
        self._viewmode = viewmode
        # Set current view tab
        # This will triggered currentChanged, which will call _switchView
        # but we need to manually call _switchView first so we can pass savePrevious=False
        # When _switchView is called again, it will return immediately, as the
        # 'new' mode is the same as _viewmode
        # Have to do all this to find the index of the required tab...
        idx, *_ = [idx for idx in range(self._viewTabs.count()) 
                   if self._viewTabs.tabText(idx).lower()==self._viewmode]
        self._viewTabs.setCurrentIndex(idx)
        
        # restore previous profile
        profile = settings.value("params/currentProfile", cast=str)
        if profile != "None":
            self.argswidget._loadProfile(profile)
        
        return super().show()
        
    def closeEvent(self, event):
        settings = Settings()
        settings.beginGroup("window")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("viewMode", self._viewmode)
        settings.setValue(f"viewModes/{self._viewmode}", self.saveState())
        settings.endGroup()
        
        profile = self.argswidget.currentProfile if not self.argswidget.currentProfileAltered else None
        settings.setValue("params/currentProfile", profile)
        
        return super().closeEvent(event)

    @property
    def sr(self):
        return self._sr
    
    @sr.setter
    def sr(self, value):
        self._sr = value
        self.argswidget.setParams(sr=value)
        self.hopfplot.setSampleRate(value)
        
    @property
    def running(self):
        return self._running
    
    @running.setter
    def running(self, value):
        self._running = value
        self.runToolBar.setEnabled(not value)
            
    def _openAudioFile(self):
        """ Show open file dialog """
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select audio file", self._openAudioDir, "Wav files (*.wav);;All files (*)")
        if fname:
            self._openAudio(fname)
            
    def _openAudio(self, fname):
        """ Read audio file and set audio plot """
        try:
            self.audio, self.sr = read_audio(fname)
        except Exception as err:
            self._setTemporaryStatus(f"Cound not open {os.path.basename(fname)}")
            self._currentAudioFile = None
        else:
            self.audioplot.setAudio(self.audio, self.sr)
            self._openAudioDir = os.path.dirname(fname)
            self._currentAudioFile = fname
            self._setTemporaryStatus(f"Opened {os.path.basename(fname)}; sample rate {self.sr}Hz")
            
    def _doAnalysis(self):
        """ Create DetectorBank and call absZ """
        params, invalid = self.argswidget.getArgs()
        if len(invalid) > 0 or self._currentAudioFile is None:
            QMessageBox.warning(self, "Cannot run", 
                                f"The following arg(s) are invalid: {', '.join(invalid)}.\n"
                                "Analysis cannot be carried out.")
            return
        
        self._setTemporaryStatus(f"Starting analysis of {self._currentAudioFile}")
        
        settings = Settings()
        downsample = settings.value("plot/downsample", cast=int)
        
        self.analysers = [] 
        segments = self.audioplot.getSegments()
        idxx = self.hopfplot.addPlots(params['detChars'][:,0], segments)
        numSamples = 0
        for idx, segment in zip(idxx, segments):
            n0, n1 = segment.samples
            numSamples += (n1-n0)
            
            analyser = Analyser(self.audio, self.sr, params, n0, n1, downsample)
            
            self.analysers.append(analyser)
            
            analyser.progress.connect(self._incrementProgress)
            analyser.finished.connect(partial(self._analyserFinished, key=idx))
            
        numSamples //= downsample
        self._progressBar.setMaximum(numSamples)
        self._progressQueue.clear()
        
        for analyser in self.analysers:
            analyser.start()
            
        # analyser now not threaded, so all should be done by now
        # if re-introducing threading here, move this to `_analyserFinished`
        self._progressBar.setValue(self._progressBar.maximum())
        
    def _analyserFinished(self, result, key):
        self.hopfplot.addData(key, result)
        
    def _incrementProgress(self, inc):
        self._progressQueue.append(inc)
        self._checkProgressQueue()
        
    def _checkProgressQueue(self):
        while len(self._progressQueue) > 0:
            inc = self._progressQueue.popleft()
            self._progressBar.setValue(self._progressBar.value()+inc)
        
    def createDockWidget(self, widget, area, title, viewmode, key=None):
        if area in self.dockAreas:
            area = self.dockAreas[area]
        dock = QDockWidget()
        dock.setWidget(widget)
        dock.setWindowTitle(title)
        dock.setObjectName(title)
        self.addDockWidget(area, dock)
        if not hasattr(self, "dockWidgets"):
            self.dockWidgets = {}
        if key is None:
            key = title
        self.dockWidgets[key] = WidgetView(dock, viewmode)
    
    def _switchView(self, mode, savePrevious=True):
        """ Switch between showing 'input', 'output' or 'all' widgets. """ 
        if mode == self._viewmode:
            # nothing to be done
            return
        settings = Settings()
        if savePrevious:
            # save current state
            state = self.saveState()
            settings.setValue(f"window/viewModes/{self._viewmode}", state)
            
        self._viewmode = mode
        state = settings.value(f"window/viewModes/{self._viewmode}")
        if state is not None:
            self.restoreState(state)
        else:
            for widget, viewmode in self.dockWidgets.values():
                visible = True if mode == "all" or viewmode == mode else False
                widget.setVisible(visible)
                
    def _viewTabChanged(self, idx):
        """ Slot for view tab bar changed signal """
        mode = self._viewTabs.tabText(idx).lower()
        self._switchView(mode)
            
    def _createActions(self):
        self.openAudioFileAction = QAction(
            "&Open audio file", self, shortcut=QKeySequence.Open, 
            statusTip="Select audio file",
            triggered=self._openAudioFile)
        if (icon := QIcon.fromTheme("audio-x-generic")) is not None:
            self.openAudioFileAction.setIcon(icon)
            
        self.analyseAction = QAction(
            "&Analyse audio file", self, shortcut="F5",
            statusTip="Perform frequency analysis of audio",
            triggered = self._doAnalysis)
        if (icon := QIcon.fromTheme("system-run")) is not None:
            self.analyseAction.setIcon(icon)
            
        self.exitAction = QAction(
            "&Quit", self, shortcut=QKeySequence.Quit,
            statusTip="Quit application",
            triggered=self.close)
        if (icon := QIcon.fromTheme("application-exit")) is not None:
            self.exitAction.setIcon(icon)
            
        self.preferencesAction = QAction(
            "&Preferences", self, shortcut=QKeySequence.Preferences,
            statusTip="Edit preferences",
            triggered=self.prefDialog.show)
        
    def _createToolBars(self):
        
        self.viewToolBar = QToolBar("View")
        self.viewToolBar.setObjectName("View")
        self._viewTabs = QTabBar()
        for label in ["All"]:#, "Output"]:
            idx = self._viewTabs.addTab(label)
            self._viewTabs.setTabToolTip(idx, f"Show {label.lower()} widgets")
        self._viewTabs.currentChanged.connect(self._viewTabChanged)
        self.viewToolBar.addWidget(self._viewTabs)
        # self.addToolBar(self.viewToolBar)
        
        # self.runToolBar = self.addToolBar("Run")
        # self.runToolBar.setObjectName("Run")
        # self.runToolBar.addAction(self.openAudioFileAction)
        # self.runToolBar.addAction(self.analyseAction)
        
    def _createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openAudioFileAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAction)
        
        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.preferencesAction)
        
        self.analyseMenu = self.menuBar().addMenu("&Analysis")
        self.analyseMenu.addAction(self.analyseAction)
        
    def _setTemporaryStatus(self, msg):
        self.statusBar().showMessage(msg, self._statusTimeout)
        
    def _setStatus(self, msg):
        self.statusBar().showMessage(msg)