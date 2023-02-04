import pytest
import os

from detectorbankgui.audioread import read_audio

def _get_data_path():
    p = os.path.dirname(__file__)
    return os.path.join(p, "test", "data")

@pytest.fixture
def audio_results():
    p = _get_data_path()
    csv = os.path.join(p, 'a4.csv')
    return csv

@pytest.fixture
def audio2_results():
    p = _get_data_path()
    csv = [os.path.join(p, f) for f in ['0.csv', '1.csv']]
    return csv

@pytest.fixture
def audiofile():
    p = _get_data_path()
    return os.path.join(p, "a4.wav")

@pytest.fixture
def audiofile2():
    p = _get_data_path()
    return os.path.join(p, "dre48.wav")

@pytest.fixture
def audio(audiofile):
    return read_audio(audiofile)

@pytest.fixture
def audio2(audiofile2):
    return read_audio(audiofile2)

@pytest.fixture
def configfile():
    p = _get_data_path()
    return os.path.join(p, "hopfskipjump.xml")

@pytest.fixture
def atol():
    return 0.01