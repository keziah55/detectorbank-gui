from detectorbankgui.audioplot import AudioPlotWidget
from qtpy.QtWidgets import QFileDialog, QMessageBox
from qtpy.QtCore import Qt
import pytest 
import numpy as np

import qtpy
audioAvailable = True if qtpy.QT_VERSION.split('.')[0] == '5' else False

pytest_plugin = "pytest-qt"

class TestAudioPlot:

    @pytest.fixture
    def setup_empty(self, qtbot):
        self._setup()
        qtbot.addWidget(self.widget)
        self.widget.show()
        
    @pytest.fixture
    def setup(self, qtbot, audio):
        self._setup()
        qtbot.addWidget(self.widget)
        self.widget.show()
        
        self.audio, self.sr = audio
        self.lenaudio = len(self.audio) / self.sr
        self.widget.setAudio(self.audio, self.sr)
        
    def _setup(self):
        widget = AudioPlotWidget()
        self.widget = widget
        self.label = widget.plotLabel
        self.plot = widget.plotWidget
        self.seglist = widget.segmentList
        
        self.atol = 0.01
        
        self.rmvButtonIndex = 3 if audioAvailable else 2
    
    def test_default_audioplot(self, setup_empty, qtbot):

        assert len(self.seglist) == 1
        segments = self.widget.getSegments()
        assert len(segments) == 1
        segment, *_ = segments
        assert segment.start == 0
        assert segment.stop == 1
        assert segment.sr is None
        assert segment.samples is None
        assert len(self.seglist._segments) == 1
        assert self.seglist._segments[0].values == [0,1]
        
    def test_plot_audiofile(self, setup, qtbot):
        
        segments = self.widget.getSegments()
        assert len(segments) == 1
        segment, *_ = segments
        assert segment.start == 0
        assert np.isclose(segment.stop, self.lenaudio, atol=self.atol)
        assert segment.sr == self.sr
        assert abs(segment.samples[1] - len(self.audio)) <= self.atol*self.sr
        assert all(np.isclose((self.seglist._segments[0].values), [0,self.lenaudio], atol=self.atol))
        
    def test_set_segments(self, setup, qtbot):
        
        seg0 = (0, 1.5)
        segment = self.plot._segments[0]
        segment.setRegion(seg0)
        
        with qtbot.waitSignal(self.seglist.addButton.clicked):
            qtbot.mouseClick(self.seglist.addButton, Qt.LeftButton)
        
        assert len(self.seglist) == 2
        segments = self.widget.getSegments()
        assert len(segments) == 2
        segment = segments[1]
        assert segment.start == seg0[1]
        assert segment.stop == seg0[1] + 1
        
        assert np.isclose(self.seglist._max, self.lenaudio, atol=self.atol)
    
        for segwidget in self.seglist._segments:  
            for box in segwidget.boxes:
                assert np.isclose(box.maximum(), self.lenaudio, atol=self.atol)
        
    def test_remove_segments(self, setup, qtbot):
        
        seg0 = (0, 0.5)
        segment = self.plot._segments[0]
        segment.setRegion(seg0)
        
        for _ in range(2):
            with qtbot.waitSignal(self.seglist.addButton.clicked):
               qtbot.mouseClick(self.seglist.addButton, Qt.LeftButton)
               
        assert len(self.seglist) == 3
        
        # remove seg 1
        segwidget = self.seglist._segments[1]
        button = segwidget.layout().itemAt(self.rmvButtonIndex).widget()
        
        with qtbot.waitSignal(button.clicked):
            qtbot.mouseClick(button, Qt.LeftButton)
            
        assert len(self.seglist) == 2
        
        # remove final seg
        segwidget = self.seglist._segments[1]
        button = segwidget.layout().itemAt(self.rmvButtonIndex).widget()
        
        with qtbot.waitSignal(button.clicked):
            qtbot.mouseClick(button, Qt.LeftButton)
            
        assert len(self.seglist) == 1
        
        segment = self.widget.getSegments()[0]
        assert segment.start == seg0[0]
        assert segment.stop == seg0[1]
        
    def test_remove_all_segments(self, setup, qtbot):
        
        seg0 = (0, 0.5)
        segment = self.plot._segments[0]
        segment.setRegion(seg0)
        
        for _ in range(2):
            with qtbot.waitSignal(self.seglist.addButton.clicked):
               qtbot.mouseClick(self.seglist.addButton, Qt.LeftButton)
               
        assert len(self.seglist) == 3
        
        # remove all
        with qtbot.waitSignal(self.seglist.removeAllButton.clicked):
            qtbot.mouseClick(self.seglist.removeAllButton, Qt.LeftButton)
            
        assert len(self.seglist) == 1
        
        # should be default segment over whole length of audio
        segment = self.widget.getSegments()[0]
        assert segment.start == 0
        assert np.isclose(segment.stop, self.lenaudio, atol=self.atol)
        assert segment.sr == self.sr
        assert abs(segment.samples[1] - len(self.audio)) <= self.atol*self.sr
        assert all(np.isclose((self.seglist._segments[0].values), [0,self.lenaudio], atol=self.atol))
        
    def test_open_audio(self, setup_empty, audiofile, audio, qtbot, monkeypatch):
        
        def patch_getOpenFileName(*args, **kwargs):
            return audiofile, None
        monkeypatch.setattr(QFileDialog, "getOpenFileName", patch_getOpenFileName)
        
        with qtbot.waitSignal(self.widget.audioFileOpened):
            qtbot.mouseClick(self.widget.openAudioButton, Qt.LeftButton)
            
        audio, sr = audio
            
        assert self.widget.audioFilePath == audiofile
        assert np.array_equal(self.widget.audio, audio)
        assert self.widget.sr == sr
        
        assert len(self.plot.plotItem.listDataItems()) == 1
        
        # test error
        def patch_getOpenFileName(*args, **kwargs):
            return "nonexistent/file.wav", None
        monkeypatch.setattr(QFileDialog, "getOpenFileName", patch_getOpenFileName)
        monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
        
        with qtbot.assertNotEmitted(self.widget.audioFileOpened):
            qtbot.mouseClick(self.widget.openAudioButton, Qt.LeftButton)
        
        assert self.widget.audioFilePath == audiofile
        
    def test_open_another_file(self, setup, audiofile2, qtbot, monkeypatch):
        
        seg0 = (0, 1.5)
        segment = self.plot._segments[0]
        segment.setRegion(seg0)
        
        with qtbot.waitSignal(self.seglist.addButton.clicked):
            qtbot.mouseClick(self.seglist.addButton, Qt.LeftButton)
        
        assert len(self.seglist) == 2
        
        # open another file
        def patch_getOpenFileName(*args, **kwargs):
            return audiofile2, None
        monkeypatch.setattr(QFileDialog, "getOpenFileName", patch_getOpenFileName)
        
        with qtbot.waitSignal(self.widget.audioFileOpened):
            qtbot.mouseClick(self.widget.openAudioButton, Qt.LeftButton)
        
        assert len(self.seglist) == 1
        assert len(self.widget.audio) == 719337
        
        qtbot.wait(2000)