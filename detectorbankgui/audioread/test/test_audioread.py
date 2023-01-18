import scipy.io.wavfile
import soundfile
import numpy as np
import pytest

@pytest.mark.parametrize("use_scipy", [True, False])
def test_read_audio(use_scipy, monkeypatch, audiofile):
    
    import detectorbankgui.audioread
    
    monkeypatch.setattr(detectorbankgui.audioread, "using_scipy", use_scipy)
    if use_scipy:
        f = scipy.io.wavfile.read
    else:
        f = soundfile.read

    monkeypatch.setattr(detectorbankgui.audioread, "read", f)
    
    audio, sr = detectorbankgui.audioread.read_audio(audiofile)
    
    assert sr == 48000
    assert audio.shape == (136864,)
    assert audio.dtype == np.float32
    
