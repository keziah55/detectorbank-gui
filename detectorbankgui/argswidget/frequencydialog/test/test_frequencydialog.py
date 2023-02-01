from detectorbankgui.argswidget.frequencydialog import FrequencyDialog
from qtpy.QtWidgets import QTableWidgetItem
from qtpy.QtCore import Qt
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
            
        expected = np.array([440*2**(n/12) for n in range(valid[0][1],valid[1][1]+1)])
        with qtbot.waitSignal(page.values, check_params_cb=lambda arr: np.all(np.isclose(arr, expected))):
            qtbot.mouseClick(page.doneButton, Qt.LeftButton)
        assert np.all(np.isclose(page.value, expected))
        
        # check values in table
        for row in range(self.widget.table.rowCount()):
            item = self.widget.table.item(row, 0)
            assert item.text() == f"{expected[row]:g}"
            assert item.flags() == Qt.ItemIsSelectable | Qt.ItemIsEnabled
            
        qtbot.wait(100)
        
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
        
        expected = np.array([refFreq*2**(n/edo) for n in range(n0, n1+1)])
        with qtbot.waitSignal(page.values, check_params_cb=lambda arr: np.all(np.isclose(arr, expected))):
            qtbot.mouseClick(page.doneButton, Qt.LeftButton)
        assert np.all(np.isclose(page.value, expected))
        
        # check values in table
        for row in range(self.widget.table.rowCount()):
            item = self.widget.table.item(row, 0)
            assert item.text() == f"{expected[row]:g}"
            assert item.flags() == Qt.ItemIsSelectable | Qt.ItemIsEnabled
            
    def test_bandwidth_constant(self, setup, qtbot):
        
        # set some frequencies, so there are rows in table
        self.widget._setTableFrequencies(np.random.rand(10) * 440)
        
        assert self.widget.bwWidgets[0].isSelected
        
        page = self.widget.bwWidgets[0].page
        value = 2.34
        with qtbot.waitSignal(page.box.valueChanged):
            page.box.setValue(value)
            
        assert page.doneButton.isEnabled()
        with qtbot.waitSignal(page.values, check_params_cb=lambda val: val==value):
            qtbot.mouseClick(page.doneButton, Qt.LeftButton)
        assert page.value == value
        
        # check values in table
        for row in range(self.widget.table.rowCount()):
            item = self.widget.table.item(row, 1)
            assert item.text() == f"{value:g}"
            assert item.flags() == Qt.ItemIsSelectable | Qt.ItemIsEnabled
            
    def test_manual(self, setup, qtbot):
        
        self.widget.freqRangeWidgets[2].setSelected()
        self.widget.bwWidgets[1].setSelected()
        
        for _ in range(4):
            with qtbot.waitSignal(self.widget.addRowButton.clicked):
                qtbot.mouseClick(self.widget.addRowButton, Qt.LeftButton)
                
        assert self.widget.table.rowCount() == 4
        assert self.widget._validate() is False
        assert self.widget.okButton.isEnabled() is False
        
        # set some frequencies
        freq = np.random.rand(3) * 440
        for row, f in enumerate(freq):
            self.widget.table.setItem(row, 0, QTableWidgetItem(f"{f:g}"))
            
        assert self.widget._validate() is False
        assert self.widget.okButton.isEnabled() is False
        
        # set some bandwidths
        bw = np.array([3.5, 4.9, 0])
        for idx in [0, 2]:
            self.widget.table.setItem(idx, 1, QTableWidgetItem(f"{bw[idx]:g}"))
        
        assert self.widget._validate() is False
        assert self.widget.okButton.isEnabled() is False
        
        idx = 1
        self.widget.table.setItem(idx, 1, QTableWidgetItem(f"{bw[idx]:g}"))
                
        assert self.widget._validate() is True
        
        # set invalid value
        self.widget.table.setItem(3, 0, QTableWidgetItem("blah"))
        assert self.widget._validate() is False
        # back to valid
        self.widget.table.setItem(3, 0, QTableWidgetItem(""))
        
        assert self.widget._validate()
        
        for row in range(self.widget.table.rowCount()):
            if row == 3:
                continue
            for col in range(2):
                item = self.widget.table.item(row, col)
                expected = freq[row] if col == 0 else bw[row]
                assert item.text() == f"{expected:g}"
        
        self.widget._valueChanged() # table.itemChanged not emitted by table.setItem?
        assert self.widget.okButton.isEnabled() is True
        
        assert np.all(np.isclose(self.widget.values, np.column_stack((f, bw))))
        
        # was getting weird 'widget already deleted' errors
        # don't know why
        # but disconnecting these here seems to sort it
        self.widget.freqRangeWidgets[0].page.timers["start"].timeout.disconnect()
        self.widget.freqRangeWidgets[0].page.timers["end"].timeout.disconnect()
        
    def test_clear_table(self, setup, qtbot):
        
        f = np.random.rand(10) * 440
        b = np.ones(len(f))
        dc = np.column_stack((f, b))
        self.widget.setValues(dc)
        
        with qtbot.waitSignal(self.widget.clearTableButton.clicked):
            qtbot.mouseClick(self.widget.clearTableButton, Qt.LeftButton)
            
        for row in range(self.widget.table.rowCount()):
            for col in range(2):
                item = self.widget.table.item(row, col)
                assert item is None