from detectorbankgui.analyser.analyser import Analyser, AnalysisWorker
from detectorbank import DetectorBank
import numpy as np
import os
import pytest 

pytest_plugin = "pytest-qt"

class MockResultsWidget:
    def __init__(self):
        self.results = {}
        
    def addPlots(self, det_chars, segments):
        return list(range(len(segments)))
    
    def addData(self, key, result): 
        self.results[key] = result

class Segment:
    def __init__(self, n0, n1):
        self.samples = (n0, n1)

def test_analyser(audio2, audio2_results, qtbot):
    results_widget = MockResultsWidget()
    analyser = Analyser(results_widget)
    
    audio, sr = audio2
    
    f = np.array([440*2**(k/12) for k in range(-12,13)])
    bw = np.zeros(len(f))
    det_char = np.column_stack((f,bw))
    detBankParams = {
        "numThreads":os.cpu_count(),
        "damping":0.0001,
        "gain":25,
        "detChars":det_char,
        "method":DetectorBank.runge_kutta,
        "freqNorm":DetectorBank.freq_unnormalized,
        "ampNorm":DetectorBank.amp_unnormalized
        }
    
    segments = [Segment(0, 48000*4), Segment(48000*5, 48000*9)]
    subsample = 1000
    analyser.setParams(audio, sr, detBankParams, segments, subsample)
    
    with qtbot.waitSignal(analyser.finished, timeout=30000):
        analyser.start()
        
    for result_file in audio2_results:
        fname = os.path.basename(result_file)
        key = int(os.path.splitext(fname)[0])
        
        expected = np.loadtxt(result_file)
        
        result = results_widget.results[key]
        
        assert np.all(np.isclose(result, expected, atol=0.01))
        
def test_subsample(audio2, audio2_results, qtbot):
    results_widget = MockResultsWidget()
    analyser = Analyser(results_widget)
    
    audio, sr = audio2
    
    f = np.array([440*2**(k/12) for k in range(-12,13)])
    bw = np.zeros(len(f))
    det_char = np.column_stack((f,bw))
    detBankParams = {
        "numThreads":os.cpu_count(),
        "damping":0.0001,
        "gain":25,
        "detChars":det_char,
        "method":DetectorBank.runge_kutta,
        "freqNorm":DetectorBank.freq_unnormalized,
        "ampNorm":DetectorBank.amp_unnormalized
        }
    
    segments = [Segment(0, 48000*4), Segment(48000*5, 48000*9)]
    subsample = 10000
    analyser.setParams(audio, sr, detBankParams, segments, subsample)
    
    with qtbot.waitSignal(analyser.finished, timeout=30000):
        analyser.start()
        
    for result_file in audio2_results:
        fname = os.path.basename(result_file)
        key = int(os.path.splitext(fname)[0])
        
        expected = np.loadtxt(result_file)
        
        result = results_widget.results[key]
        
        assert result.shape[1] < expected.shape[1]
        assert result.shape[1]  == expected.shape[1] // 10
        
def test_analyse_full_audio(audio, audio_results, qtbot):
    
    audio, sr = audio
    
    f = np.array([440*2**(k/12) for k in range(-12,13)])
    bw = np.zeros(len(f))
    det_char = np.column_stack((f,bw))
    detBankParams = {
        "numThreads":os.cpu_count(),
        "damping":0.0001,
        "gain":25,
        "detChars":det_char,
        "method":DetectorBank.runge_kutta,
        "freqNorm":DetectorBank.freq_unnormalized,
        "ampNorm":DetectorBank.amp_unnormalized
        }
    
    analyser = AnalysisWorker(audio, sr, detBankParams)
    
    with qtbot.waitSignal(analyser.finished, timeout=30000):
        analyser.start()
        
    expected = np.loadtxt(audio_results)
    assert np.all(np.isclose(analyser.result, expected, atol=0.01))