from keras.models import load_model
from models import pickle_if_not_pickled, root_mse, reshape_for_conv2d, r2_coeff_determination
from sklearn.model_selection import KFold, train_test_split
# no GPU support for sklearn's cross_val_score
from create_dataset import done_beep
import matplotlib.pyplot as plt
from models import create_model
import numpy as np
from keras.callbacks import ModelCheckpoint

def k_fold_cv():
    """ Check the robustness of the model using K-Fold CV """
    cqt_segments, midi_segments = pickle_if_not_pickled()
    cqt_segments_reshaped, midi_segments_reshaped = reshape_for_conv2d(cqt_segments, midi_segments)
    k_folds = 5

    # The goal in this block is to set aside for testing a chunk of data which contains at least
    # one whole song the network will not have seen before.
    # Num data points to set aside for testing
    num_samples = len(cqt_segments_reshaped)
    num_testing = int(num_samples * .2)
    max_desired_test_start_index = num_samples - num_testing - 1 # - 1 is necessary bc of the way the remaining data gets sliced
    test_set_start_index = np.random.randint(0, max_desired_test_start_index)
    testing_end_index = test_set_start_index+num_testing
    cqt_test, midi_test = cqt_segments_reshaped[test_set_start_index:testing_end_index], \
                          midi_segments_reshaped[test_set_start_index:testing_end_index]

    # remaining data
    cqt_train_and_valid = np.concatenate(
        (cqt_segments_reshaped[:test_set_start_index], cqt_segments_reshaped[testing_end_index:]), axis=0)
    midi_train_and_valid = np.concatenate(
        (midi_segments_reshaped[:test_set_start_index], midi_segments_reshaped[testing_end_index:]), axis=0)

    # Generate a random order of elements
    # with np.random.permutation and index into the arrays data and classes with those elements

    # shuffle the remaining data:
    indices = np.random.permutation(len(cqt_train_and_valid))
    data, labels = cqt_train_and_valid[indices], midi_train_and_valid[indices]

    k_fold = KFold(n_splits=k_folds)  # Provides train/test indices to split data in train/test sets.
    for train_indices, valid_indices in k_fold.split(cqt_train_and_valid):
        print('Train: %s | valid: %s' % (train_indices, valid_indices))
    example_cqt_segment = cqt_train_and_valid[0]
    input_height, input_width, input_depth = example_cqt_segment.shape
    example_midi_segment = midi_train_and_valid[0]
    one_d_array_len = len(example_midi_segment)

    for i, (train, valid) in enumerate(k_fold.split(cqt_train_and_valid)):
        print("Running Fold", i + 1, "/", k_folds)

        model = create_model(input_height, input_width, one_d_array_len)
        # saving time (best models have reached best val_score before epoch 40)
        epochs = 50
        filepath = "model_checkpoints/weights-improvement-{epoch:02d}-{val_loss:.4f}.hdf5"
        checkpointer = ModelCheckpoint(filepath=filepath, monitor='val_loss',
                                       verbose=1, save_best_only=True, save_weights_only=False)
        history_for_plotting = model.fit(
            data[train], labels[train], epochs=epochs, verbose=2, validation_data=(data[valid], labels[valid]),
            callbacks=[checkpointer])
        test_score = model.evaluate(cqt_test, midi_test, verbose=0)
        print("test score:")
        print("[loss (rmse), root_mse, mae, r2_coeff_determination]")
        print(test_score)

        done_beep()

        # summarize history for loss
        # https://machinelearningmastery.com/display-deep-learning-model-training-history-in-keras/
        plt.plot(history_for_plotting.history['loss'])
        plt.plot(history_for_plotting.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['train rmse', 'validation rmse'], loc='upper right')
        plt.show()

def main():
    k_fold_cv()

if __name__ == '__main__':
    main()