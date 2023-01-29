#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main window
"""
from qtpy.QtWidgets import QMainWindow, QDockWidget, QAction, QMessageBox, QProgressBar
from qtpy.QtCore import Qt, QUrl
from qtpy.QtGui import QKeySequence, QDesktopServices, QIcon
import qtpy
from customQObjects.core import Settings
from customQObjects.gui import getIconFromTheme
from .aboutdialog import AboutDialog
from .audioplot import AudioPlotWidget
from .analyser import Analyser
from .argswidget import ArgsWidget
from .resultsplotwidget import ResultsPlotWidget
from .invalidargexception import InvalidArgException
from collections import deque
import sys
import os

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
        
        # actions have to exist before resultsplot (but after audioplot)
        # might need to come up with a better solution than this...
        self.resultsplot = ResultsPlotWidget(self)
        
        self.analyser = Analyser(self.resultsplot)
        
        self.statusBar()
        self._statusTimeout = 1500
        
        self._progressBar = QProgressBar()
        self.statusBar().addPermanentWidget(self._progressBar)
        self._progressQueue = deque()
        
        self.audioplot.statusMessage.connect(self._setTemporaryStatus)
        self.audioplot.audioFileOpened.connect(self.setSampleRate)
        
        self.analyser.progress.connect(self._incrementProgress)
        self.analyser.finished.connect(self._maxProgress)
        
        widgets = {"audioinput":('Audio Input', self.audioplot, 'left'),
                   "args":('Parameters',self.argswidget, 'left'),
                   "output":("Output", self.resultsplot, 'right')}
        
        for key, values in widgets.items():
            name, widget, area = values
            self.createDockWidget(widget, area, name, key)
        
        if audioFile is not None:
            self.audioplot.openAudioFile(audioFile)
            
        fileDir = os.path.split(__file__)[0]
        
        qt_api_version = qtpy.PYQT_VERSION if qtpy.API_NAME.startswith("PyQt") else qtpy.PYSIDE_VERSION
        msg = ["DetectorBank GUI",
               f"Python {sys.version_info.major}.{sys.version_info.minor}",
               f"Qt {qtpy.QT_VERSION}, {qtpy.API_NAME} {qt_api_version}",
               "(C) Keziah Milligan"]
        image = os.path.join(fileDir, "..", "images/splash.png")
        self.about = AboutDialog("\n".join(msg), image)
        
        path = os.path.join(fileDir, "..", "images/icon.png")
        icon = QIcon(path)
        self.setWindowIcon(icon)
        
    def show(self):
        settings = Settings()
        geometry = settings.value("window/geometry")
        
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            self.showMaximized()
                
        # restore previous profile
        profile = settings.value("params/currentProfile", cast=str, defaultValue="None")
        if profile == "None":
            profile = "default"
        self.argswidget.loadProfile(profile)
            
        # get saved subsample factor
        subsample = settings.value("plot/subsample", cast=int, defaultValue=1000)
        self.argswidget.setSubsampleFactor(subsample)
        
        return super().show()
        
    def closeEvent(self, event):
        settings = Settings()
        settings.beginGroup("window")
        settings.setValue("geometry", self.saveGeometry())
        settings.endGroup()
        
        profile = self.argswidget.currentProfile #if not self.argswidget.currentProfileAltered else "None"
        settings.setValue("params/currentProfile", profile)
        
        return super().closeEvent(event)

    @property
    def sr(self):
        return self._sr
    
    @sr.setter
    def sr(self, value):
        self._sr = value
        self.argswidget.setParams(sr=value)
        self.resultsplot.setSampleRate(value)
        
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
            self.argswidget.getSubsampleFactor())
        
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
            
    def createDockWidget(self, widget, area, title, key=None):
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
        self.dockWidgets[key] = dock
            
    def _openGuiDocs(self):
        """ Open GUI docs in browser """
        QDesktopServices.openUrl(QUrl("https://keziah55.github.io/detectorbank-gui/"))
        
    def _openDocs(self):
        """ Open DetectorBank docs in browser """
        QDesktopServices.openUrl(QUrl("https://keziah55.github.io/DetectorBank/"))
        
    def _about(self):
        self.about.exec_()
        
    def _createActions(self):
        self.openAudioFileAction = QAction(
            "&Open audio file", self, shortcut=QKeySequence.Open, 
            statusTip="Select audio file",
            triggered=self.audioplot.openAudioFile)
        if (icon := getIconFromTheme("audio-x-generic")) is not None:
            self.openAudioFileAction.setIcon(icon)
            
        self.analyseAction = QAction(
            "&Analyse audio file", self, shortcut="F5",
            statusTip="Perform frequency analysis of audio",
            triggered = self._doAnalysis)
        if (icon := getIconFromTheme("system-run")) is not None:
            self.analyseAction.setIcon(icon)
            
        self.exitAction = QAction(
            "&Quit", self, shortcut=QKeySequence.Quit,
            statusTip="Quit application",
            triggered=self.close)
        if (icon := getIconFromTheme("application-exit")) is not None:
            self.exitAction.setIcon(icon)
            
        self.openGuiDocsAction = QAction("&Open DetectorBank GUI documentation", self,
                                         triggered=self._openGuiDocs)
        self.openDocsAction = QAction("&Open DetectorBank documentation", self,
                                      triggered=self._openDocs)
        self.aboutAction = QAction("&About", self, triggered=self._about)
            
    def _createToolBars(self):
        # self.addToolBar(self.viewToolBar)
        
        # self.runToolBar = self.addToolBar("Run")
        # self.runToolBar.setObjectName("Run")
        # self.runToolBar.addAction(self.openAudioFileAction)
        # self.runToolBar.addAction(self.analyseAction)
        pass
        
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