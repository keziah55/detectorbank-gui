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
        
    def test_frequency(self, setup, qtbot):
        
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
        qtbot.wait(5000)