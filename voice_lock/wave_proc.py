import io
import numpy as np
import math as m
import matplotlib.pyplot as mpl
import scipy.io.wavfile as siw

### ~~~ WAV file encryption ~~~ ###

def encrypt_wav(file_in, file_out, cipher):
    with open(file_in, 'rb') as f:
        data = f.read()
    cipher.save_data(data, file_out)

def encrypt_wavs(dirname, n, cipher):
    '''Use this code to encrypt `n` samples from the `dirname` directory using `cipher`'''

    for i in range(1, 9):
        encrypt_wav(file_in='%d.wav' % i, file_out='%s/%d.wav.enc' % (dirname, i), cipher=cipher)


### ~~~ Waveform loading ~~~ ###

def get_enc_wav_data(filename, cipher):
    '''Get data from encrypted WAV file'''

    # Get encrypted binary data
    data_raw = cipher.load_data(filename)

    # Read decrypted binary data as normal WAV file w/o saving it
    sample_rate, data_np = siw.read(io.BytesIO(data_raw))

    # Get rid of stereo by estimating the mean for both channels
    if isinstance(data_np[0], np.ndarray):
        data_np = data_np.mean(1)

    return data_np

def get_wave_data(wave_filename):
    '''Get data from raw WAV file'''
    sample_rate, wave_data = siw.read(wave_filename)
    if isinstance(wave_data[0], np.ndarray): # стерео
        wave_data = wave_data.mean(1)
    return wave_data

def make_enc_wave(filename, cipher):
    '''Create appropriate waveform from encrypted .wav file'''
    return envelope(denoise(normalize(get_enc_wav_data(filename, cipher))))

def make_wave(filename):
    '''Create appropriate waveform from raw .wav file'''
    return envelope(denoise(normalize(get_wave_data(filename))))


### ~~~ Waveform processing ~~~ ###

def normalize(wave_data):
    return wave_data / np.amax(wave_data)

def denoise(wave_data):
    for i in range(len(wave_data)):
        wave_data[i] = (wave_data[i]-0.9*wave_data[i-1])*(0.54-0.46*m.cos((i-6)*2*m.pi/180))
    return wave_data

def envelope(wave):
    '''Get signal envelope'''
    plus=[]
    minus=[]
    a=[]
    b=[]
    for elm in wave:
        if elm>=0:
            plus.append(elm)
        else:
            minus.append(abs(elm))

    for i in range(0, (len(plus) - len(plus)%75), 75):
        a.append(np.mean(plus[i:i+75]))
    for i in range(0, (len(minus)-len(minus)%75), 75):
        b.append(np.mean(minus[i:i+75]))
    return (a, b)

def corr(wave1, wave2):

    wave1 = np.asarray(wave1)
    wave2 = np.asarray(wave2)

    # make waves of the same array size by zero padding
    f = abs(len(wave1) - len(wave2))
    if len(wave1) < len(wave2):
        wave1 = np.pad(wave1, pad_width=(0, f), mode='constant')
    elif len(wave1) > len(wave2):
        wave2 = np.pad(wave2, pad_width=(0, f), mode='constant')

    cor=np.zeros(2 * len(wave1) + 1)
    wave=np.zeros(3 * len(wave1))
    for i in range(len(wave1)):
        wave[i+len(wave1)]=wave1[i] # duplicate wave1 3 times and store in wave

    for i in range(2 * len(wave1) + 1):
        for j in range(len(wave2)):
            cor[i] += min(wave2[j], wave[i + j])

    mxx1 = np.sum(wave1)
    mxx2 = np.sum(wave2)

    return np.max(cor) / max(mxx1, mxx2)

def corr_tuple(tup1,tup2):
    return (corr(tup1[0], tup2[0]) + corr(tup1[1], tup2[1])) / 2


### ~~~ Plotting ~~~ ###

def plot_waveform(wave_data):
    mpl.plot(np.arange(len(wave_data)), wave_data)
    mpl.grid()
    mpl.show()