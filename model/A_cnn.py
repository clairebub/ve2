from keras.models import Model
from keras.layers import Input, Dense, Conv1D, MaxPooling1D, Flatten, Reshape
from keras.optimizers import Adam
from keras.models import model_from_json, Sequential
from keras import regularizers

from sklearn.model_selection import train_test_split
import os
import numpy as np
import timeit

if __name__ == "__main__":
    # parameter configurations
    model_number = 2

    d = '../'

    temp_dest = os.path.join(d, 'RESULTS')
    if not os.path.isdir(temp_dest):
        os.mkdir(temp_dest)
    temp_dest = os.path.join(temp_dest,'All_Target')
    if not os.path.isdir(temp_dest):
        os.mkdir(temp_dest)
    dest = os.path.join(temp_dest, "target(1)_basic_tanh")
    if not os.path.isdir(dest):
        os.mkdir(dest)

    spectral_file = os.path.join(d, 'spectral_contextWin2.npy')
    label_file = os.path.join(d, 'label_contextWin2.npy')
    target = [0,1, 2]

    # load data
    print("loading data ...")
    all_fea = np.load(spectral_file)
    all_label = np.load(label_file)
    all_label = all_label[:,target] # only target labels
    print(["all_label.shape:", all_label.shape])
    print(["all_fea.shape:", all_fea.shape])

    # data re-formating
    all_fea = all_fea[:, 0:all_fea.shape[1]:3]
    all_fea = all_fea.reshape(all_fea.shape[0],all_fea.shape[1], 1)
    print(["all_fea.shape:", all_fea.shape])

    # split into train and test
    print("spliting data...")
    X_train, X_test, y_train, y_test = train_test_split(all_fea, all_label, test_size=0.3, shuffle=False)


    # Model Training
    if not os.path.isfile(os.path.join(dest,"model_target({}).json".format(model_number))):
        # configure model
        cnn = Sequential()
        cnn.add(Conv1D(4, kernel_size=20, strides=4, activation='tanh', kernel_initializer='he_normal',
                       bias_initializer='he_normal', input_shape=(all_fea.shape[1],1,)))
        cnn.add(MaxPooling1D(pool_size=4, padding='valid'))
        cnn.add(Conv1D(2, kernel_size=10, strides=4, activation='tanh', kernel_initializer='he_normal',
                       bias_initializer='he_normal'))
        cnn.add(MaxPooling1D(pool_size=4, padding='valid'))
        cnn.add(Flatten())
        cnn.add(Dense(256, activation='tanh', kernel_initializer='he_normal', bias_initializer='he_normal'))
        cnn.add(Dense(all_label.shape[1], activation="sigmoid", activity_regularizer=regularizers.l2(10e-7),
                      kernel_initializer='he_normal', bias_initializer='he_normal'))
        cnn.summary()

        # compile model
        cnn.compile(optimizer= Adam(lr=0.0001), loss = 'binary_crossentropy', metrics=['accuracy'])  # decay=0.014 lr=0.001

        # train model
        cnn.fit(X_train, y_train, epochs=20, batch_size=512, shuffle=True)

        # evaluate model
        score = cnn.evaluate(X_train, y_train, batch_size = 512)
        print(["train score",score])

        # serialize model to JSON
        model_json = cnn.to_json()
        if not os.path.isdir(dest):
            os.mkdir(dest)
        with open(os.path.join(dest, "model_target({}).json".format(model_number)), 'w') as json_file:
            json_file.write(model_json)
        # serialize model to HDF5
        cnn.save_weights(os.path.join(dest, "model_target({}).h5".format(model_number)))
        print("Saved model to disk")

    # load json and create model
    json_file = open(os.path.join(dest, "model_target({}).json".format(model_number)),'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights(os.path.join(dest, "model_target({}).h5".format(model_number)))
    print("Loaded model from disk")

    # evaluate and predict
    loaded_model.compile(optimizer= Adam(lr=0.0001), loss='binary_crossentropy', metrics=['accuracy'])
    score = loaded_model.evaluate(X_test, y_test, batch_size=512)
    print(["test score", score])

    start_time = timeit.default_timer()
    predictions_probs_test = loaded_model.predict(X_test)
    stop_time = timeit.default_timer()
    print("Time to predict testing data:", stop_time - start_time)
    predictions = np.empty(predictions_probs_test.shape)
    predictions[predictions_probs_test >= 0.5] = int(1)
    predictions[predictions_probs_test < 0.5] = int(0)
    np.savetxt(os.path.join(dest, 'cnn_predictionProbs_test.txt'), predictions_probs_test, delimiter=',')
    np.savetxt(os.path.join(dest, 'cnn_ytest.txt'), y_test, delimiter=',')
    np.savetxt(os.path.join(dest, 'cnn_predictions_test.txt'),predictions, delimiter=',')

