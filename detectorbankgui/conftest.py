import pytest
import os

@pytest.fixture()
def audiofile():
    p = os.path.dirname(__file__)
    return os.path.join(p, "test", "data", "a4.wav")
