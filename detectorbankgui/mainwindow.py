#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window
"""
from qtpy.QtWidgets import (QMainWindow, QDockWidget, QAction, QMessageBox, 
                            QProgressBar, QTabBar, QToolBar)
from qtpy.QtCore import Qt, QUrl
from qtpy.QtGui import QIcon, QKeySequence, QDesktopServices
from customQObjects.core import Settings
from .audioplot import AudioPlotWidget
from .analyser import Analyser
from .argswidget import ArgsWidget
from .hopfplot import HopfPlot
from .invalidargexception import InvalidArgException
from collections import deque, namedtuple

SegmentAnalysis = namedtuple("SegmentAnalysis", ["segement", "analyser"])
WidgetView = namedtuple("WidgetView", ["dockwidget", "viewmode"])

class DetectorBankGui(QMainWindow):
    
    dockAreas = {'left':Qt.LeftDockWidgetArea, 'right':Qt.RightDockWidgetArea,
                 'top':Qt.TopDockWidgetArea, 'bottom':Qt.BottomDockWidgetArea}
    
    def __init__(self, *args, audioFile=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.audioplot = AudioPlotWidget(self)
        self.argswidget = ArgsWidget(self)
        
        self._createActions()
        self._createToolBars()
        self._createMenus()
        
        # actions have to exist before hopfplot (but after audioplot)
        # might need to come up with a better solution than this...
        self.hopfplot = HopfPlot(self)
        
        self.analyser = Analyser(self.hopfplot)
        
        self.statusBar()
        self._statusTimeout = 1500
        
        self._progressBar = QProgressBar()
        self.statusBar().addPermanentWidget(self._progressBar)
        self._progressQueue = deque()
        
        self.audioplot.statusMessage.connect(self._setTemporaryStatus)
        self.audioplot.audioFileOpened.connect(self.setSampleRate)
        
        self.analyser.progress.connect(self._incrementProgress)
        self.analyser.finished.connect(self._maxProgress)
        
        widgets = {"audioinput":('Audio Input', self.audioplot, 'left', 'input'),
                   "args":('Parameters',self.argswidget, 'left', 'input'),
                   "output":("Output", self.hopfplot, 'right', 'output')}
        
        for key, values in widgets.items():
            name, widget, area, viewmode = values
            self.createDockWidget(widget, area, name, viewmode, key)
        
        if audioFile is not None:
            self.audioplot.openAudioFile(audioFile)
            
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
            self.argswidget.loadProfile(profile)
            
        # get saved downsample factor
        downsample = settings.value("plot/downsample", cast=int, defaultValue=1000)
        self.argswidget.setDownsampleFactor(downsample)
        
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
        
    def setSampleRate(self, sr):
        self.sr = sr
            
    def _doAnalysis(self):
        """ Create DetectorBank and call absZ """
        
        # check that have have all necessary parameters and show warning if not
        errorMsgTitle = "Cannot analyse audio"
        try:
            params = self.argswidget.getArgs()
        except InvalidArgException as exc:
            QMessageBox.warning(self, errorMsgTitle, str(exc))
            return
        if self.audioplot.audio is None:
            QMessageBox.warning(self, errorMsgTitle, "Please select an audio input file")
            return
        
        self._setTemporaryStatus(f"Starting analysis of {self.audioplot.audioFilePath}")
        
        numSamples = self.analyser.setParams(
            self.audioplot.audio, 
            self.sr, 
            params, 
            self.audioplot.getSegments(), 
            self.argswidget.getDownsampleFactor())
        
        self._progressBar.setMaximum(numSamples)
        self._progressQueue.clear()
        
        self.analyser.start()
            
    def _incrementProgress(self, inc):
        self._progressQueue.append(inc)
        self._checkProgressQueue()
        
    def _maxProgress(self):
        self._progressBar.setValue(self._progressBar.maximum())
        
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
            
    def _openGuiDocs(self):
        """ Open GUI docs in browser """
        QDesktopServices.openUrl(QUrl("https://keziah55.github.io/detectorbank-gui/"))
        
    def _openDocs(self):
        """ Open DetectorBank docs in browser """
        QDesktopServices.openUrl(QUrl("https://keziah55.github.io/DetectorBank/"))
        
    def _about(self):
        msg = "DetectorBank GUI\n(C) Keziah Milligan"
        QMessageBox.about(self, "DetectorBank GUI", msg)
        
        
    def _createActions(self):
        self.openAudioFileAction = QAction(
            "&Open audio file", self, shortcut=QKeySequence.Open, 
            statusTip="Select audio file",
            triggered=self.audioplot.openAudioFile)
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
            
        self.openGuiDocsAction = QAction("&Open DetectorBank GUI documentation", self,
                                         triggered=self._openGuiDocs)
        self.openDocsAction = QAction("&Open DetectorBank documentation", self,
                                      triggered=self._openDocs)
        self.aboutAction = QAction("&About", self, triggered=self._about)
            
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
        
        self.analyseMenu = self.menuBar().addMenu("&Analysis")
        self.analyseMenu.addAction(self.analyseAction)
        
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addActions([self.openGuiDocsAction, self.openDocsAction])
        self.helpMenu.addSeparator()
        self.helpMenu.addAction(self.aboutAction)
        
        
    def _setTemporaryStatus(self, msg):
        self.statusBar().showMessage(msg, self._statusTimeout)
        
    def _setStatus(self, msg):
        self.statusBar().showMessage(msg)