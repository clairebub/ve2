import numpy as np
import os
import math

# parameter configuration
d = '../'
orig_mfcc_filename = 'mfcc40_1.npy'
new_mfcc_filename = 'mfcc40_1_contextWin2.npy'
orig_spectral_filename = 'spectral1.npy'
new_spectral_filename = 'spectral_contextWin2.npy'
orig_label_filename = 'all_label.npy'
new_label_filename = 'label_contextWin2.npy'
hop_len = 0.02
n_contextWin = 2


# MFCC Feature processing
# load original feature matrix
mfcc_orig = np.load(os.path.join(d, orig_mfcc_filename))
print("mfcc_orig.shape: {0}".format(mfcc_orig.shape))
mfcc_orig = mfcc_orig[:,:-1]
n_dims,n_feas = mfcc_orig.shape
# construct feaMat
feaMat = np.empty((n_feas, n_dims*(1+2*n_contextWin)))
for i in range(n_feas):
    if (i-n_contextWin) >= 0 and (i+n_contextWin) < n_feas:
        row = mfcc_orig[:,i-n_contextWin:i+n_contextWin+1].flatten()
    else:
        row = np.zeros(feaMat[0].shape)
        for w in range(i-n_contextWin, i+n_contextWin+1):
            if n_feas > w >= 0:
                k = w - (i-n_contextWin)
                row[k*n_dims:(k+1)*n_dims] = mfcc_orig[:,w]
    feaMat[i] = row
# save new feature matrix
print("new MFCC feaMat.shape:{0}".format(feaMat.shape))
np.save(os.path.join(d, new_mfcc_filename), feaMat)


# Spectral Feature processing
# load original feature matrix
spectral_orig = np.load(os.path.join(d, orig_spectral_filename))
print("spectral_orig.shape: {0}".format(spectral_orig.shape))
spectral_orig = spectral_orig[:,:-1]
n_dims,n_feas = spectral_orig.shape
# construct feaMat
feaMat = np.empty((n_feas, n_dims*(1+2*n_contextWin)))
for i in range(n_feas):
    if (i-n_contextWin) >= 0 and (i+n_contextWin) < n_feas:
        row = spectral_orig[:,i-n_contextWin:i+n_contextWin+1].flatten()
    else:
        row = np.zeros(feaMat[0].shape)
        for w in range(i-n_contextWin, i+n_contextWin+1):
            if n_feas > w >= 0:
                k = w - (i-n_contextWin)
                row[k*n_dims:(k+1)*n_dims] = spectral_orig[:,w]
    feaMat[i] = row
"""
# data re-formating (to have one channel) and downsampling by 3
feaMat = feaMat[:, 0:feaMat.shape[1]:3]
feaMat = feaMat.reshape(feaMat.shape[0],feaMat.shape[1], 1)
print(["all_fea.shape:", feaMat.shape])
"""
# save new feature matrix
print("new spectral feaMat.shape:{0}".format(feaMat.shape))
np.save(os.path.join(d, new_spectral_filename), feaMat)


# Label processing
label_orig = np.load(os.path.join(d,orig_label_filename))
print("label_orig.shape{0}:".format(label_orig.shape))

labelMat = np.empty((n_feas,label_orig.shape[1]))
for k in range(n_feas):
    start_time = int(math.floor(k*hop_len))

print("labelMat.shape:{0}".format(labelMat.shape))
np.save(os.path.join(d, new_label_filename), labelMat)










