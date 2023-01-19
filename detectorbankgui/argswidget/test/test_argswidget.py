from detectorbankgui.argswidget import ArgsWidget
from detectorbank import DetectorBank
from qtpy.QtCore import Qt
import pytest 
import os
import numpy as np

pytest_plugin = "pytest-qt"

class TestArgsWidget:

    @pytest.fixture
    def setup(self, qtbot):
        self._setup()
        qtbot.addWidget(self.widget)
        self.widget.show()
        
    def _setup(self):
        widget = ArgsWidget()
        self.widget = widget
        
    def test_form(self, setup, qtbot):
        
        test_values = {
            "sr":{"value":48000, "expected":"48000", "default":None},
            "numThreads":{"value":4, "default":os.cpu_count()},
            "damping":{"value":0.0003, "default":0.0001},
            "gain":{"value":20, "default":25},
            "method":{"value":"Central difference", 
                      "expected":DetectorBank.central_difference,
                      "default":DetectorBank.runge_kutta},
            "freqNorm":{"value":"Search normalized", 
                        "expected":DetectorBank.search_normalized,
                        "default":DetectorBank.freq_unnormalized},
            "ampNorm":{"value":"Normalized", 
                       "expected":DetectorBank.amp_normalized,
                       "default":DetectorBank.amp_unnormalized},
            }
        
        for key, test_vals in test_values.items():
            param = self.widget.widgets[key]
            value = test_vals['value']
            expected = test_vals.get('expected', value)
            
            with qtbot.waitSignal(param.widget.valueChanged):
                param.widget.setValue(value)
            assert param.widget.value == expected
            if key == "sr":
                assert param.widget.text() == f"{expected} Hz"
                
        qtbot.mouseClick(self.widget.restoreDefaultsButton, Qt.LeftButton)
        qtbot.wait(50)
        
        for key, test_vals in test_values.items():
            param = self.widget.widgets[key]
            expected = test_vals['default']
            if expected is None:
                continue
            assert param.widget.value == expected
                
    def test_profile(self, setup, qtbot):
        pass
    
    def test_freq_bw_dialog(self, setup, qtbot):
        pass