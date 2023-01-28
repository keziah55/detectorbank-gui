#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get absZ results from DetectorBank

Created a QObject `AnalysisWorker` so that each instance can be run in a separate
thread, however this is not (currently?) necessary, as the DetectorBank is already
threaded.
"""
from qtpy.QtCore import QObject, Signal
from detectorbank import DetectorBank, DetectorCache, Producer
import numpy as np
import os.path
from functools import partial

class AnalysisWorker(QObject):
    
    progress = Signal(int)
    """ **signal** progress(int `progressIncrement`)
    
        Emitted every time `progressIncrement` samples has been processed.
    """
    
    finished = Signal(object)
    """ **signal** finished(np.ndarrray `result`)
    
        Emitted when the analysis has finished, with the array of results.
    """
    
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
        
    def start(self):
        
        n, idx = 0, 0
        
        while n < self.cache.end() and idx < self.result.shape[1]:
            for k in range(self.channels):
                self.result[k][idx] = self.cache[k,n]
            idx += 1
            n += self.downsample
            if idx % self.progressIncrement == 0:
                self.progress.emit(self.progressIncrement)
            
        self.finished.emit(self.result)
        
class Analyser(QObject):
    
    progress = Signal(int)
    """ **signal** progress(int `samples`)
    
        Emitted every time an AnalysisWorker has processed a given number of samples
    """
    
    finished = Signal()
    """**signal** finished()
    
        Emitted when all segments have been analysed.
    """
    
    def __init__(self, resultWidget):
        super().__init__()
        
        self.hopfplot = resultWidget
        
    def start(self):
        """ Begin analysis of all segments. """
        for analyser in self.analysers:
            analyser.start()
        
    def setParams(self, audio, sr, detBankParams, segments, downsample, saveDir=None) -> int:
        """ Set all parameters needed for analysis 
        
            Parameters
            ----------
            audio : np.ndarray
                Array of audio samples
            sr : int
                Sample rate of audio
            detBankParams : dict
                Dict of DetectorBank parameters, as returned by ArgsWidget.getArgs
            segments : list
                List of segments, as returned by AudioPlot.getSegments
            downsample : int
                Downsample factor
            saveDir : str, optional
                If provided, write results to this directory
                
            Returns
            -------
            numSamples : int
                Total number of samples that will be analysed, after downsampling
        """
        
        if saveDir is not None:
            np.savetxt(os.path.join(saveDir, "frequency_bandwidth.txt"), detBankParams['detChars'])
        
        self.analysers = [] 
        self._finished = [] # list of completed analysers (can't remove from lst/dict, as they are blocking)
        idxx = self.hopfplot.addPlots(detBankParams['detChars'][:,0], segments)
        numSamples = 0
        for idx, segment in zip(idxx, segments):
            n0, n1 = segment.samples
            numSamples += (n1-n0)
            
            analyser = AnalysisWorker(audio, sr, detBankParams, n0, n1, downsample)
            
            self.analysers.append(analyser)
            
            analyser.progress.connect(self.progress)
            
            kwargs = {'key':idx}
            if saveDir is not None:
                kwargs['fname'] = os.path.join(saveDir, f"{n0}-{n1}_samples.txt")
            analyser.finished.connect(partial(self._analyserFinished, **kwargs))
            
        numSamples //= downsample
            
        return numSamples
        
    def _analyserFinished(self, result, key, fname=None):
        self.hopfplot.addData(key, result)
        if fname is not None:
            np.savetxt(fname, result)
        self._finished.append(key)
        
        if len(self._finished) == len(self.analysers):
            self.finished.emit()