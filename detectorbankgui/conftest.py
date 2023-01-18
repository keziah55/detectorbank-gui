import pytest
import os

from detectorbankgui.audioread import read_audio

@pytest.fixture
def audiofile():
    p = os.path.dirname(__file__)
    return os.path.join(p, "test", "data", "a4.wav")

@pytest.fixture
def audio(audiofile):
    return read_audio(audiofile)