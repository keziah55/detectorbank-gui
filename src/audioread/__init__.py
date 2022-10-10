try:
    from scipy.io.wavfile import read
    using_scipy = True
except ImportError:
    from soundfile import read
    using_scipy = False
        
import numpy as np
    
def read_audio(fname) -> tuple[np.ndarray, int]:
    """ Read audio file `fname` and return 1D numpy array and sample rate.
    
        Returned array will be float32 in range -1 to 1.
    """
    ret = read(fname)
    if using_scipy:
        sr, audio = ret
    else:
        audio, sr = ret
        
    if len(audio.shape) > 1:
       # convert stereo to mono
       audio = np.mean(audio, axis=-1)
       
    # normalize to range -1..1
    n = 1
    if audio.dtype == np.int16:
        n = 2 ** 15
    elif audio.dtype == np.int32:
        n = 2 ** 31
    elif audio.dtype == np.uint8:
        n = 2 ** 7
    audio = np.array(audio/n, dtype=np.dtype('float32'))
           
    return audio, sr
        
__all__ = ["read_audio"]