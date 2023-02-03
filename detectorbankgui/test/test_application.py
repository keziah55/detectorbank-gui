from detectorbankgui.mainwindow import DetectorBankGui
import pytest

def test_app(qtbot, audiofile):
    app = DetectorBankGui(audioFile=audiofile, profile="default")
    qtbot.addWidget(app)
    app.show()
    
    with qtbot.waitSignal(app.analyser.finished):
        app._doAnalysis()
        
    # qtbot.wait(3000)
    
    qtbot.wait(500)
    
    assert len(app.resultsplot._plots) == 1