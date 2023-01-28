from detectorbankgui.argswidget import ArgsWidget
from detectorbankgui.argswidget.profiledialog import SaveDialog, LoadDialog
from detectorbankgui.profilemanager import ProfileManager
from detectorbankgui.invalidargexception import InvalidArgException
from detectorbank import DetectorBank
from qtpy.QtWidgets import QDialog
from qtpy.QtCore import Qt
import pytest 
import os
import shutil
import numpy as np

pytest_plugin = "pytest-qt"

class TestArgsWidget:

    @pytest.fixture
    def setup(self, qtbot):
        
        self._setup()
        qtbot.addWidget(self.widget)
        self.widget.show()
        
    @pytest.fixture
    def setup_save_profile(self, qtbot):
        
        config_file = os.path.expanduser("~/.config/hopfskipjump.xml")
        replace_config = config_file + ".bak"
        os.replace(config_file, replace_config)
        self.config_file = config_file
        
        self._setup()
        qtbot.addWidget(self.widget)
        self.widget.show()
        
        yield
        
        os.replace(replace_config, config_file)
        
    @pytest.fixture
    def setup_load_profile(self, qtbot, configfile):
        
        test_config_file = configfile
        
        config_file = os.path.expanduser("~/.config/hopfskipjump.xml")
        replace_config = config_file + ".bak"
        os.replace(config_file, replace_config) # mv .config/hopfskipjump.xml .config/hopfskipjump.xml.bak
        shutil.copyfile(test_config_file, config_file) # mv test/data/hopfskipjump.xml .config/hopfskipjump.xml
        
        self.config_file = config_file
        
        self._setup()
        qtbot.addWidget(self.widget)
        self.widget.show()
        
        yield
        
        os.replace(replace_config, config_file) # mv .config/hopfskipjump.xml.bak .config/hopfskipjump.xml
        
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
            
        with pytest.raises(InvalidArgException) as exc:
            args = self.widget.getArgs()
        assert "Frequencies and bandwidths" in str(exc)
                
        qtbot.mouseClick(self.widget.restoreDefaultsButton, Qt.LeftButton)
        qtbot.wait(50)
        
        for key, test_vals in test_values.items():
            param = self.widget.widgets[key]
            expected = test_vals['default']
            if expected is None:
                continue
            assert param.widget.value == expected
                
    def test_save_profile(self, setup_save_profile, qtbot, monkeypatch):
        
        f = np.array([440*2**(k/12) for k in range(-12,12)])
        bw = np.zeros(len(f))
        det_char = np.column_stack((f,bw))
        
        profile_name = "_test_profile"
        
        test_values = {
            "sr":48000,
            "numThreads":4,
            "damping":0.0003,
            "gain":20,
            "detChars":det_char,
            "method":"Central difference",
            "freqNorm":"Search normalized",
            "ampNorm":"Normalized"
            }
        
        for key, value in test_values.items():
            param = self.widget.widgets[key]
            with qtbot.waitSignal(param.widget.valueChanged):
                param.widget.setValue(value)
           
        monkeypatch.setattr(SaveDialog, "exec_", lambda *args: QDialog.Accepted)
        monkeypatch.setattr(SaveDialog, "getProfileName", lambda *args: profile_name)
        
        with qtbot.waitSignal(self.widget.saveProfileButton.clicked):
            qtbot.mouseClick(self.widget.saveProfileButton, Qt.LeftButton)
        
        profile_manager = ProfileManager(self.config_file)
        assert profile_name in profile_manager.profiles
        
    @pytest.mark.skip("needs rewritten")
    def test_load_profile(self, setup_load_profile, qtbot, monkeypatch):
        profile_name = "_test_profile2"
        def patch_getProfileName(*args, **kwargs):
            return profile_name, False
        monkeypatch.setattr(LoadDialog, "exec_", lambda *args: QDialog.Accepted)
        monkeypatch.setattr(LoadDialog, "getProfileName", patch_getProfileName)
        
        with qtbot.waitSignal(self.widget.loadProfileButton.clicked):
            qtbot.mouseClick(self.widget.loadProfileButton, Qt.LeftButton)
            
        f = np.array([440*2**(k/12) for k in range(2,11)])
        bw = np.zeros(len(f))
        bw.fill(2)
        det_char = np.column_stack((f,bw))
        
        expected_values = {
            "sr":48000.0,
            "numThreads":4,
            "damping":0.0002,
            "gain":16,
            "detChars":det_char,
            "method":DetectorBank.runge_kutta,
            "freqNorm":DetectorBank.freq_unnormalized,
            "ampNorm":DetectorBank.amp_unnormalized
            }
        
        # will raise exception if any args are invalid
        args = self.widget.getArgs()
        
        for key, expected in expected_values.items():
            value = args[key]
            if key == "detChars":
                assert np.all(np.isclose(value, expected))
            else:
                assert value == expected
        
    @pytest.mark.skip("test not written yet")
    def test_freq_bw_dialog(self, setup, qtbot):
        pass