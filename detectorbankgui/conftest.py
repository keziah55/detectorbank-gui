import pytest
from pathlib import Path
from qtpy.QtCore import QCoreApplication
from detectorbankgui.audioread import read_audio

def _get_data_path():
    p = Path(__file__).parent.joinpath("test", "data")
    return p

@pytest.fixture
def audio_results():
    p = _get_data_path()
    csv = p.joinpath('a4.csv')
    return csv

@pytest.fixture
def audio2_results():
    p = _get_data_path()
    csv = [p.joinpath(f) for f in ['0.csv', '1.csv']]
    return csv

@pytest.fixture
def audiofile():
    p = _get_data_path()
    return p.joinpath("a4.wav")

@pytest.fixture
def audiofile2():
    p = _get_data_path()
    return p.joinpath("dre48.wav")

@pytest.fixture
def audio(audiofile):
    return read_audio(audiofile)

@pytest.fixture
def audio2(audiofile2):
    return read_audio(audiofile2)

@pytest.fixture
def configfile():
    p = _get_data_path()
    return p.joinpath("hopfskipjump.xml")

@pytest.fixture
def atol():
    """ Absolute tolerance for np.isclose """
    return 0.01

@pytest.fixture
def patch_settings():
    """ Don't use actual settings file """
    app_name = "DetectorBank_test"
    org_name = "SMRG"
    
    QCoreApplication.setApplicationName(app_name)
    QCoreApplication.setOrganizationName(org_name)
