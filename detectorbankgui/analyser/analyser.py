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
from functools import partial

class AnalysisWorker(QObject):
    """ Object to perform analysis for a given audio segment
    
        Paremeters
        ----------
        audio : np.ndarray
            Array of audio samples
        sr : int
            Sample rate of audio
        params : dict
            Dict of DetectorBank parameters
        n0 : int, optional
            If provided, start analysis from this sample, rather than beginning of `audio`
        n1 : int, optional
            If provided, stop analysis at this sample, rather than end of `audio`
        subsample : int, optional
            If provided, subsample result by this factor
        progressIncrement : int
            Emit `progress` signal after every `progressIncrement` samples have
            been processed (after downsampling)
    """
    
    progress = Signal(int)
    """ **signal** progress(int `progressIncrement`)
    
        Emitted every time `progressIncrement`*`subsample` samples has been processed.
    """
    
    finished = Signal(object)
    """ **signal** finished(np.ndarrray `result`)
    
        Emitted when the analysis has finished, with the array of results.
    """
    
    def __init__(self, audio, sr, params, n0=None, n1=None, subsample=1, progressIncrement=1):
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
        self.subsample = int(subsample)
        self.progressIncrement = progressIncrement
        self.result = np.zeros((self.channels, (n1-n0)//subsample))
        
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
        self.segSize = self.cacheSegDuration * self.sr // 1000
        numSegs = 10
        self.cache = DetectorCache(self.p, numSegs, self.segSize)
        channels = self.det.getChans()
        return channels
        
    def start(self):
        """ Get subsampled results """
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
    """ Object to manage DetectorBank calculations for audio regions.
    
        Parameters
        ----------
        resultWidget : HopfPlot
            Widget for plotting results
    """
    
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
        
    def setParams(self, audio, sr, detBankParams, segments, subsample) -> int:
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
            subsample : int
                subsample factor
                
            Returns
            -------
            numSamples : int
                Total number of samples that will be analysed, after downsampling
        """
        self.analysers = [] 
        self._finished = [] # list of completed analysers (can't remove from lst/dict, as they are blocking)
        idxx = self.hopfplot.addPlots(detBankParams['detChars'][:,0], segments)
        numSamples = 0
        for idx, segment in zip(idxx, segments):
            n0, n1 = segment.samples
            numSamples += (n1-n0)
            
            analyser = AnalysisWorker(audio, sr, detBankParams, n0, n1, subsample)
            
            self.analysers.append(analyser)
            
            analyser.progress.connect(self.progress)
            
            kwargs = {'key':idx}
            analyser.finished.connect(partial(self._analyserFinished, **kwargs))
            
        numSamples //= subsample
            
        return numSamples
        
    def _analyserFinished(self, result, key):
        """ Plot `result` and check if all analysers are finished. """
        self.hopfplot.addData(key, result)
        self._finished.append(key)
        
        if len(self._finished) == len(self.analysers):
            self.finished.emit()