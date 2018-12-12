import librosa
import numpy as np
import os
import scipy
import scipy.io.wavfile as wavfile
import sys

# should use max or abs(min) because min is negative
def read_a_wavfile(filename):
    fs, s = wavfile.read(filename)
    print("deebug", fs, s, s.dtype, np.iinfo(np.dtype('int16')).min, np.iinfo(np.dtype('int16')).max, len(s))
    if s.dtype == np.dtype('int16'):
        s = s.astype('float32') / np.iinfo(np.dtype('int16')).max
    a = [x for x in s if x > 0]
    print("deebug: s=", s)
    print("deebug: a=", len(a))
    return fs,s

def extract_mfcc(s,sr, win_len, hop_len):
    print("deebug: extract_mfcc", len(s), sr, win_len, hop_len)
    print("deebug: samples: ")
    for i in range(0, 4):
        print(s[i], end=" ")
    print(" ")
    mfcc = librosa.feature.mfcc(y=s, sr=sr, n_fft=win_len, hop_length=hop_len, n_mfcc = 13)
    mfcc_delta = librosa.feature.delta(mfcc)
    mfcc_delta_2 = librosa.feature.delta(mfcc, order = 2)
    mfcc40 = librosa.feature.mfcc(y=s, sr=sr, n_fft =win_len, hop_length=hop_len, n_mfcc=40)
    print("deebug: mfcc40.shape", mfcc40.shape)
    for j in range(0, 10):
        for i in range(0, 3):
            print(j, i, mfcc40[i][j], end=", ")
        print()
    return mfcc, mfcc_delta, mfcc_delta_2, mfcc40

def extract_spectral(s, sr, win_len, hop_len):
    spectral_complex = librosa.stft(y=s, n_fft=win_len, hop_length=hop_len)
    spectral = np.abs(spectral_complex)
    spectral = spectral / np.sum(spectral, axis=0)  # normalize using "sum-to-one"
    return spectral

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Usage: {:s} wav_file".format(sys.argv[0]))
        sys.exit(1)
    win_len = 0.04
    hop_len = 0.02

    # extract feature
    filename = sys.argv[1]
    fs, s = read_a_wavfile(filename)
    mfcc, mfcc_delta, mfcc_delta_2, mfcc40 = extract_mfcc(s,fs,int(win_len*fs), int(hop_len*fs))
    spectral = extract_spectral(s, fs, int(win_len*fs), int(hop_len*fs))

    # print feature dimension information
    print("MFCC40:")
    print(mfcc40.shape)
    print("Spectral:")
    print(spectral.shape)
