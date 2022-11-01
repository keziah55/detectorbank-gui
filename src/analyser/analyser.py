#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get absZ results from DetectorBank (in new thread)
"""
from qtpy.QtCore import QThread, QObject, Signal
from detectorbank import DetectorBank, DetectorCache, Producer
import numpy as np

class AnalysisWorker(QObject):
    
    progress = Signal(int)
    
    finished = Signal()
    
    def __init__(self, audio, sr, params, n0=None, n1=None, downsample=1, progressIncrement=1):
        super().__init__()
        
        self.cacheSegDuration = 30 # cache segment size in ms
        
        self.audio = audio
        self.sr = sr
        n0 = n0 if n0 is not None else 0
        n1 = n1 if n1 is not None else len(audio)
        if n0 < 0:
            n0 = 0
        if n1 > len(self.audio):
            n1 = len(self.audio)
        
        self.channels = self._makeDetectorCache(params, audioSlice=(n0, n1))
        self.downsample = downsample
        self.progressIncrement = progressIncrement
        self.result = np.zeros((self.channels, (n1-n0)//downsample))
        
    def _makeDetectorCache(self, params, audioSlice=None):
        features = params['method'] | params['freqNorm'] | params['ampNorm']
        if audioSlice is not None:
            n0, n1 = audioSlice
            audio = self.audio[n0:n1]
        else:
            audio = self.audio
        args = (self.sr, audio, params['numThreads'], params['detChars'], features,
                params['damping'], params['gain'])
        self.det = DetectorBank(*args)
        self.p = Producer(self.det)
        segSize = self.cacheSegDuration * self.sr
        numSegs = 10
        self.cache = DetectorCache(self.p, numSegs, segSize)
        channels = self.det.getChans()
        return channels
        
    def process(self):
        
        n, idx = 0, 0
        
        while n < self.cache.end() and idx < self.result.shape[1]:
            for k in range(self.channels):
                self.result[k][idx] = self.cache[k,n]
            idx += 1
            n += self.downsample
            if idx % self.progressIncrement == 0:
                self.progress.emit(self.progressIncrement)
            
        self.finished.emit()
        
class Analyser(QObject):
    
    progress = Signal(int)
    
    finished = Signal(object)
    
    def __init__(self, audio, sr, params, n0=None, n1=None, downsample=1):
        super().__init__()
        
        self.worker = AnalysisWorker(audio, sr, params, n0, n1, downsample)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.process)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self._emitResult)
        self.worker.progress.connect(self.progress)
        
    def _emitResult(self):
        self.finished.emit(self.worker.result)
        
    def start(self):
        self.thread.start()