import numpy as np
import scipy.io.wavfile as wavfile
import os
import librosa


def read_a_wavfile(filename):
    fs, s = wavfile.read(filename)
    if s.dtype == np.dtype('int16'):
        s = s.astype('float32') / np.iinfo(np.dtype('int16')).min
    return fs,s


def extract_mfcc(s,sr, win_len, hop_len):
    mfcc = librosa.feature.mfcc(y=s, sr=sr, n_fft=win_len, hop_length=hop_len, n_mfcc = 13)
    mfcc_delta = librosa.feature.delta(mfcc)
    mfcc_delta_2 = librosa.feature.delta(mfcc, order = 2)
    mfcc40 = librosa.feature.mfcc(y=s, sr=sr, n_fft =win_len, hop_length=hop_len, n_mfcc=40)
    return mfcc, mfcc_delta, mfcc_delta_2, mfcc40

"""
#STFT with n_fft = nextpow2(fs) 
def nextpow2(i):
    n = 1
    while n < i: n *= 2
    return n


def extract_spectral(s, sr, win_len, hop_len):
    n_coef = nextpow2(sr)/2+1
    spectral_complex = librosa.stft(y=s, n_fft= n_coef, win_length=win_len,  hop_length=hop_len)
    spectral = np.abs(spectral_complex)
    spectral = spectral / np.sum(spectral, axis=0)  # normalize using "sum-to-one"
    return spectral
"""


def extract_spectral(s, sr, win_len, hop_len):
    spectral_complex = librosa.stft(y=s, n_fft=win_len, hop_length=hop_len)
    spectral = np.abs(spectral_complex)
    spectral = spectral / np.sum(spectral, axis=0)  # normalize using "sum-to-one"
    return spectral


if __name__ == "__main__":
    d = '../'
    n_microphones = 1
    win_len = 0.04
    hop_len = 0.02
    for i in range(1, n_microphones+1):
        # extract feature
        filename = os.path.join(d, 'combined_0' + str(i) + '.wav')
        fs, s = read_a_wavfile(filename)
        mfcc, mfcc_delta, mfcc_delta_2, mfcc40 = extract_mfcc(s,fs,int(win_len*fs), int(hop_len*fs))
        spectral = extract_spectral(s, fs, int(win_len*fs), int(hop_len*fs))

        # save results to disk
        """
        np.save(os.path.join(d,'mfcc_'+str(i)+'.npy'),mfcc)
        np.save(os.path.join(d, 'mfcc_delta_' + str(i) + '.npy'), mfcc_delta)
        np.save(os.path.join(d, 'mfcc_delta2_' + str(i) + '.npy'), mfcc_delta_2)
        np.save(os.path.join(d, 'mfcc40_' + str(i) + '.npy'), mfcc40)
        np.save(os.path.join(d, 'spectral' + str(i) + '.npy'), spectral)
        """

        # print feature dimension information
        print("MFCC40:")
        print(mfcc40.shape)
        print("Spectral:")
        print(spectral.shape)


