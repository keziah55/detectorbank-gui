from detectorbankgui.argswidget import ArgsWidget
from detectorbankgui.argswidget.profiledialog import SaveDialog
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
    def setup(self, qtbot, patch_settings):
        
        self._setup()
        qtbot.addWidget(self.widget)
        self.widget.show()
        
    @pytest.fixture
    def setup_save_profile(self, qtbot, patch_settings):
        
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
    def setup_load_profile(self, qtbot, configfile, patch_settings):
        
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
        
    def test_form(self, setup_load_profile, qtbot):
        
        self.widget.loadProfileBox.setCurrentText("_test_profile2")
        
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
            
        # set invalid params 
        f = np.array([440*2**(k/12) for k in range(-12,12)])
        bw = np.zeros(len(f))
        bw.fill(1.2)
        det_char = np.column_stack((f,bw))
        param = self.widget.widgets['detChars']
        with qtbot.waitSignal(param.widget.valueChanged):
            param.widget.setValue(det_char)
        
        expected = "Central difference method can only be used with minimum bandwidth detectors (0Hz)"
        with pytest.raises(InvalidArgException) as exc:
            args = self.widget.getArgs()
        assert expected in str(exc) 
                
        assert "default" in self.widget.loadProfileBox.items
        
        self.widget.loadProfileBox.setCurrentText("default")
        
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
        
    def test_reload_profile(self, setup_load_profile, qtbot, monkeypatch):
        profile_name = "default"
        
        self.widget.loadProfileBox.setCurrentText(profile_name)
        assert self.widget.reloadProfileButton.isEnabled() is False
        
        f = np.array([440*2**(k/12) for k in range(-12,12)])
        bw = np.zeros(len(f))
        det_char = np.column_stack((f,bw))
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
                
        assert self.widget.reloadProfileButton.isEnabled()
        with qtbot.waitSignal(self.widget.reloadProfileButton.clicked):
            qtbot.mouseClick(self.widget.reloadProfileButton, Qt.LeftButton)
            
        f = np.array([440*2**(k/12) for k in range(-48,40)])
        bw = np.zeros(len(f))
        det_char = np.column_stack((f,bw))
        expected_values = {
            "sr":48000.0,
            "numThreads":os.cpu_count(),
            "damping":0.0001,
            "gain":25,
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
                
    def test_subsample(self, setup, qtbot):
        subsample = 10
        
        with qtbot.waitSignal(self.widget.subsampleBox.valueChanged):
            self.widget.setSubsampleFactor(subsample)
            
        assert self.widget.getSubsampleFactor() == subsample