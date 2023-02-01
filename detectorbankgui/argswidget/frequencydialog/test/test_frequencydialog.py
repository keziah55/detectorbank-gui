from detectorbankgui.argswidget.frequencydialog import FrequencyDialog
from detectorbankgui.argswidget.frequencydialog.noterangepage import NoteRangePage
import numpy as np
import pytest

class TestFrequencyBandwidthDialog:
    
    @pytest.fixture
    def setup(self, qtbot):
        
        self.widget = FrequencyDialog()
        qtbot.addWidget(self.widget)
        self.widget.show()
        
    def test_frequency_note_range(self, setup, qtbot):
        
        assert self.widget.freqRangeWidgets[0].isSelected
        
        # test note range
        page = self.widget.freqRangeWidgets[0].page
        qtbot.wait(100)
        assert np.all(np.isclose(page.value, np.array([440*2**(n/12) for n in range(-48,40)])))
        for widget in page.widgets.values():
            assert widget.valid
        # test invalid values
        invalid = ["aa0", "H4", "aba", "1"]
        for idx, value in enumerate(invalid):
            which = "start" if idx % 2 == 0 else "end"
            with qtbot.waitSignal(page.valid, check_params_cb=lambda b: b is False):
                page.widgets[which].edit.setText(value)
            assert page.widgets[which].valid is False
            assert page.widgets[which].freq is None
            assert page.widgets[which].freqLabel.text() == " Hz"
            assert page.doneButton.isEnabled() is False
        # test valid values
        valid = [("F#2", -27), ("bb5", 13)]
        for idx, value in enumerate(valid):
            if idx == 0:
                which = "start"
                both_valid = False
            else:
                which = "end"
                both_valid = True
            value, n = value
            with qtbot.waitSignal(page.valid, check_params_cb=lambda b: b is both_valid):
                    page.widgets[which].edit.setText(value)
            assert page.widgets[which].valid is True
            assert np.isclose(page.widgets[which].freq, 440*2**(n/12))
            assert page.widgets[which].freqLabel.text() == f"{440*2**(n/12):g} Hz"
            assert page.doneButton.isEnabled() is both_valid
        assert np.all(np.isclose(page.value, np.array([440*2**(n/12) for n in range(valid[0][1],valid[1][1]+1)])))
        
    def test_frequency_equation(self, setup, qtbot):
        
        self.widget.freqRangeWidgets[1].setSelected()
        page = self.widget.freqRangeWidgets[1].page
        
        refFreq = 415
        n0 = -12
        n1 = 12
        edo = 12
        with qtbot.waitSignal(page.refFreqBox.valueChanged):
            page.refFreqBox.setValue(refFreq)
        f0 = refFreq * 2**(n0/edo)
        f1 = refFreq * 2**(n1/edo)
        assert page.equationLabel.text() == f"415 * 2^(-12/12) = {f0:g} Hz\n415 * 2^(12/12) = {f1:g} Hz"
        
        n0 = -22
        with qtbot.waitSignal(page.n0Box.valueChanged):
            page.n0Box.setValue(n0)
        f0 = refFreq * 2**(n0/edo)
        assert page.equationLabel.text() == f"415 * 2^(-22/12) = {f0:g} Hz\n415 * 2^(12/12) = {f1:g} Hz"
        
        n1 = -2
        with qtbot.waitSignal(page.n1Box.valueChanged):
            page.n1Box.setValue(n1)
        f1 = refFreq * 2**(n1/edo)
        assert page.equationLabel.text() == f"415 * 2^(-22/12) = {f0:g} Hz\n415 * 2^(-2/12) = {f1:g} Hz"
        
        edo = 19
        with qtbot.waitSignal(page.edoBox.valueChanged):
            page.edoBox.setValue(edo)
            f0 = refFreq * 2**(n0/edo)
        f1 = refFreq * 2**(n1/edo)
        assert page.equationLabel.text() == f"415 * 2^(-22/19) = {f0:g} Hz\n415 * 2^(-2/19) = {f1:g} Hz"
        
        assert page.doneButton.isEnabled()
        
        assert np.all(np.isclose(page.value, np.array([refFreq*2**(n/edo) for n in range(n0, n1+1)])))
        
        
        
        