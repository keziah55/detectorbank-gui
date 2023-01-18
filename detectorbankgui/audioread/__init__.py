try:
    from scipy.io.wavfile import read
    using_scipy = True
except ImportError:
    try:
        from soundfile import read
        using_scipy = False
    except ImportError:
        raise RuntimeError("Neither scipy nor soundfile available.")
        
import numpy as np
    
def read_audio(fname, *args, **kwargs) -> tuple[np.ndarray, int]:
    """ Read audio file `fname` and return 1D numpy array and sample rate.
    
        Returned array will be float32 in range -1 to 1.
        
        `scipy.io.wavfile.read <https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.wavfile.read.html>`_ 
        will be used if it's available; otherwise will use 
        `soundfile.read <https://python-soundfile.readthedocs.io/en/0.11.0/#soundfile.readzz>`_.
        
        Additional args and kwargs will be passed to the `read` method.
    """
    
    ret = read(fname, *args, **kwargs)
    if using_scipy:
        sr, audio = ret
    else:
        audio, sr = ret
       
    # convert stereo to mono
    if len(audio.shape) > 1:
       audio = np.mean(audio, axis=-1)
       
    # normalize to range -1..1
    n = 1
    if audio.dtype == np.int16:
        n = 2**15
    elif audio.dtype == np.int32:
        n = 2**31
    elif audio.dtype == np.uint8:
        n = 2**7
    audio = np.array(audio/n, dtype=np.dtype('float32'))
           
    return audio, sr
        
__all__ = ["read_audio"]