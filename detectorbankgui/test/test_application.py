from detectorbankgui.mainwindow import DetectorBankGui
import numpy as np
import pytest

pytest_plugin = "pytest-qt"

def test_app(qtbot, audiofile, audio_results, atol, patch_settings):
    app = DetectorBankGui(audioFile=audiofile, profile="default")
    qtbot.addWidget(app)
    app.show()
    
    f = np.array([440*2**(k/12) for k in range(-3,3)])
    bw = np.zeros(len(f))
    det_char = np.column_stack((f,bw))
    app.argswidget.setParams(detChars=det_char)
    
    with qtbot.waitSignal(app.analyser.finished):
        app._doAnalysis()
        
    qtbot.wait(500)
    
    subsample = app.argswidget.getSubsampleFactor()
    results = np.loadtxt(audio_results)
    expected = results[:,::subsample]
    
    assert len(app.resultsplot._plots) == 1
    plotWidget = app.resultsplot._plots[0][0].plotWidget
    assert len(plotWidget.listDataItems()) == len(expected)
    
    for k in range(len(expected)):
        y = plotWidget.listDataItems()[k].curve.yData
        ex = expected[k][:-1] # this ends up with one extra value
        assert np.all(np.isclose(y, ex, atol=atol))