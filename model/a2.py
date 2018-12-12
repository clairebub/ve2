import librosa
import scipy.io.wavfile as wavfile
import numpy as np
from keras.optimizers import Adam
from keras.models import model_from_json
import datetime
import os


def extract_mfcc(s,sr, win_len, hop_len):
    mfcc40 = librosa.feature.mfcc(y=s, sr=sr, n_fft =win_len, hop_length=hop_len, n_mfcc=40)
    return mfcc40


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


def extract_spectral(s, win_len, hop_len):
    spectral_complex = librosa.stft(y=s, n_fft=win_len, hop_length=hop_len)
    spectral = np.abs(spectral_complex)
    spectral = spectral / np.sum(spectral, axis=0)  # normalize using "sum-to-one"
    return spectral


def contextWin(fea_orig, n_contextWin = 2):
    # Feature processing
    fea_orig = fea_orig[:, :-1]
    n_dims, n_feas = fea_orig.shape

    # construct feaMat
    new_fea = np.empty((n_feas, n_dims * (1 + 2 * n_contextWin)))
    for i in range(n_feas):
        if (i - n_contextWin) >= 0 and (i + n_contextWin) < n_feas:
            row = fea_orig[:, i - n_contextWin:i + n_contextWin + 1].flatten()
        else:
            row = np.zeros(new_fea[0].shape)
            for w in range(i - n_contextWin, i + n_contextWin + 1):
                if n_feas > w >= 0:
                    k = w - (i - n_contextWin)
                    row[k * n_dims:(k + 1) * n_dims] = fea_orig[:, w]
        new_fea[i] = row

    # save new feature matrix
    return new_fea


def confidence_ensemble(probs_1,probs_2):
    l1 = abs(probs_1 - 0.5) > abs(probs_2-0.5)
    l2 = ~l1
    ensemble_probs = l1 * probs_1 + l2 * probs_2
    return ensemble_probs


def compress_label(labelMat, threshold = 0.5):
    """
    input: labelMat is a (n_wins,n_dims) matrix.
    output: ret, a row vector of size (1, n_dims)
    Compress "labelMat" from a matrix to a row vector "ret", where ret[i] = 1 if any(labelMat[:,i] == 1), otherwise 0
    """
    label_dims = labelMat.shape[1]
    ret = np.empty(labelMat[0,:].shape)
    for i in range(label_dims):
        ret[i] = 1 if any(labelMat[:,i]>=threshold) else 0
    return ret


if __name__ == "__main__":
    # parameter configurations: define stream chunk size
    fs = 44100
    chunkSize_in_sec = 1
    chunk_size = fs * chunkSize_in_sec
    win_len = int(fs * 0.04)
    hop_len = int(fs * 0.02)
    context_chunk_size = win_len   # add context of 1 second before and after current chunk
    audio_file = "../combined_01.wav"
    dir_classifier = '../target(1)_basic_tanh'
    label_gt_file = "../all_label.npy"

    # load ground truth label
    label_gt = np.load(label_gt_file)
    label_gt = label_gt[:, [0,1,2]]
    class_label = ['smokeAlarm', 'dogbarking','doorbell']

    # load the raw audio stream
    fs, data_stream = wavfile.read(audio_file)
    if data_stream.dtype == np.dtype('int16'):
        data_stream = data_stream.astype('float32') / np.iinfo(np.dtype('int16')).min

    # load mfcc model
    json_file_mfcc = open(os.path.join(dir_classifier, "model_target(1).json"), 'r')
    model_json_mfcc = json_file_mfcc.read()
    json_file_mfcc.close()
    mfcc_model = model_from_json(model_json_mfcc)
    # load weights into new model
    mfcc_model.load_weights(os.path.join(dir_classifier, "model_target(1).h5"))
    print("Loaded mfcc model from disk")
    # compile model
    mfcc_model.compile(optimizer=Adam(lr=0.00001), loss='binary_crossentropy', metrics=['accuracy'])

    # load spectral model
    json_file_spectral = open(os.path.join(dir_classifier, "model_target(2).json"), 'r')
    model_json_spectral = json_file_spectral.read()
    json_file_spectral.close()
    spectral_model = model_from_json(model_json_spectral)
    # load weights into new model
    spectral_model.load_weights(os.path.join(dir_classifier, "model_target(2).h5"))
    print("Loaded spectral model from disk")
    # compile model
    spectral_model.compile(optimizer=Adam(lr=0.0001), loss='binary_crossentropy', metrics=['accuracy'])

    # wait for audio to play in local machine
    raw_input("Waiting for audio playing in local machine.\nPress enter to start running: ")
    print("Sound event detection starts.....")

    # read data chunk by chunk from the audio stream; process each chunk, including playing the chunk and classification
    t = 0   # time stamp

    for i in range(chunk_size,len(data_stream), chunk_size):

        # read the data chunk
        start_time = datetime.datetime.now()
        data_chunk = data_stream[i - context_chunk_size : min(i+chunk_size+context_chunk_size, len(data_stream))]

        # extract the spectral features
        mfcc40 = extract_mfcc(data_chunk, fs, win_len, hop_len)
        mfcc40 = contextWin(mfcc40)
        spectral = extract_spectral(data_chunk, win_len, hop_len)
        spectral = contextWin(spectral)
        spectral = spectral[:,0:spectral.shape[1]:3]
        spectral = spectral.reshape((spectral.shape[0],spectral.shape[1], 1))

        # classification
        probs_mfcc = mfcc_model.predict(mfcc40)
        preds_mfcc = compress_label(probs_mfcc[context_chunk_size/hop_len : -context_chunk_size/hop_len,:])
        probs_spectral = spectral_model.predict(spectral)
        preds_spectral = compress_label(probs_spectral[context_chunk_size / hop_len :
                                                             -context_chunk_size / hop_len, :])
        probs = confidence_ensemble(probs_mfcc, probs_spectral)
        predictions = compress_label(probs[context_chunk_size/hop_len : -context_chunk_size/hop_len,:])

        # construct strings to show the detection results
        t = t + 1  # current time stamp: (offset from beginning) + 1
        print_str = ""  # classification result string
        for j, preds in enumerate(predictions):
            if preds > 0:
                print_str += class_label[j] + ",    "
        print_str = print_str[:-len(",    ")]
        if not print_str:
            print_str = "None"
        gt_string = ""  # ground truth string
        gt = compress_label(label_gt[t: t + chunkSize_in_sec,:])
        for j, label in enumerate(gt):
            if label > 0:
                gt_string += class_label[j] + ",    "
        if gt_string:
            gt_string = gt_string[:-len(",    ")]

        """
        # wait for the time
        delta = datetime.datetime.now()-start_time
        while delta.microseconds < (chunkSize_in_sec*1000000-200):
            delta = datetime.datetime.now() - start_time
        """

        # print the result strings
        print('\r\n')
        print("The {}th second:".format(t-1))
        print(print_str)
        print("({})".format(gt_string))





