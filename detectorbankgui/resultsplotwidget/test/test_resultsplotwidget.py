from detectorbankgui.resultsplotwidget import ResultsPlotWidget
from detectorbankgui.analyser.analyser import AnalysisWorker
from detectorbank import DetectorBank
from qtpy.QtWidgets import QAction
import numpy as np
import os
import pytest

pytest_plugin = "pytest-qt"

class Segment:
    def __init__(self, n0, n1, colour):
        self.samples = (n0, n1)
        self.colour = colour
        
class MockParent:
    def __init__(self):
        self.analyseAction = QAction("analyse")

def test_resultsplot(audio2, qtbot):
    
    colours = ["#0000ff", "#ff0000", "#00ff00", "#ffe523", "#ed21ff", 
               "#ff672b", "#9718ff", "#00ffaa"]
    regions = [(0, 1.5),
               (2, 2.2),
               (2.2, 3),
               (4, 9),
               (10, 11.1),
               (11.2, 14)]
    colours = colours[:len(regions)]
    
    audio, sr = audio2
    
    regions = [(int(s0*sr), int(s1*sr)) for s0, s1 in regions]
    segments = [Segment(*samples, colour) for samples, colour in zip(regions, colours)]
    
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
    
    parent = MockParent()
    resultWidget = ResultsPlotWidget(parent, sr=sr)
    qtbot.addWidget(resultWidget)
    resultWidget.show()
    resultWidget.setGeometry(0, 0, 1000, 800)
    
    idxx = resultWidget.addPlots(detBankParams['detChars'][:,0], segments)
    
    assert idxx == list(range(len(segments)))
    assert len(resultWidget._plots) == len(segments)
    assert resultWidget._pageCount == int(np.ceil(len(segments) / (resultWidget.rows * resultWidget.cols)))
    assert len(resultWidget.legendWidget._labelItems) == len(f)
    
    for idx, plot_seg in enumerate(resultWidget._plots):
        segment = segments[idx]
        s0, s1 = segment.samples
        plot, seg = plot_seg
        assert seg == segment
        assert plot.plotWidget.plotItem.titleLabel.text ==  f'<span style="color:{segment.colour}">{s0/sr:.4g}-{s1/sr:.4g} seconds</span>'
    
    for idx, segment in zip(idxx, segments):
        s0, s1 = segment.samples
        analyser = AnalysisWorker(audio, sr, detBankParams, n0=s0, n1=s1, subsample=1000)
        with qtbot.waitSignal(analyser.finished):
            analyser.start()
        resultWidget.addData(idx, analyser.result)

    # test change grid
    newRows, newCols = 1, 1
    resultWidget.rowsBox.setValue(newRows)
    resultWidget.colsBox.setValue(newCols)
    with qtbot.waitSignal(resultWidget.applyGridAction.triggered):
        resultWidget.applyGridAction.trigger()
    qtbot.wait(50)
    
    expectedPageCount = int(np.ceil(len(segments) / (newRows * newCols)))
    assert resultWidget._pageCount == expectedPageCount
    resultWidget._ensurePlotVisible(resultWidget._plots[0][0])
    
    assert resultWidget.page == 0
    assert resultWidget.pageLabel.text() == f"Page 1/{expectedPageCount}"
    
    # test reset
    with qtbot.waitSignal(resultWidget.clearAction.triggered):
        resultWidget.clearAction.trigger()
    qtbot.wait(50)
    
    assert resultWidget._pageCount == 0
    assert resultWidget.page == -1 # empty stack
    assert resultWidget.pageLabel.text() == "Page 0/0"
    assert len(resultWidget._plots) == 0