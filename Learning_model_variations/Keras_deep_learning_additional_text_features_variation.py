# Import required libraries
import numpy as np
import pandas as pd
import re
import pickle

# Load any variation of tweet embeddings created from Spacy, BERT and ELMo the state-of-the-art NLP models
# and assign it to X
pickle_in = open("Spacy_train.pickle","rb")                 # May use other variants of embeddings
df_array = pickle.load(pickle_in)
print(df_array.shape)

# Load train dataset which includes 'tweet_len' and 'punct_len' as additional columns
# vectors representing additional text_features which may improve the model performance
df = pd.read_csv('train_more_features.csv')
print(df.head())

# Check the distribution of target variable for binary classification with '0' being positive and '1' being negative tweet
print(df['label'].value_counts())

# Normalize the additional text features using MinMaxScaler
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range=(-1,1))

tweet_len_arr = np.array(df['tweet_len'])
tweet_punct_arr = np.array(df['punct_len'])
print(tweet_len_arr.shape, tweet_punct_arr.shape)

tweet_len_norm = scaler.fit_transform(tweet_len_arr.reshape(-1, 1))
tweet_punct_norm = scaler.fit_transform(tweet_punct_arr.reshape(-1, 1))
print(tweet_len_norm.shape, tweet_punct_norm.shape)

# Join the Spacy or any other combination of embeddings with newly created text features and assign X
X = np.hstack((df_array, tweet_len_norm, tweet_punct_norm))
print(X.shape)

# Prepare the target variable for keras model
from keras.utils import to_categorical
y = df['label']
y = to_categorical(y)
print(y.shape)


# Split the dataset into train and test subsets
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=21)

## If using Conv1D layer, reshape the data from 2-dim to 3-dim to feed as an input
## If not using Conv1D, might just comment out this section and the Conv1D layers during model building
X_train = np.reshape(X_train, X_train.shape + (1,))
X_test = np.reshape(X_test, X_test.shape + (1,))

print(X_train.shape, X_test.shape)
print(y_train.shape, y_test.shape)


### Build Keras Deep Learning model

# Import the layers that you want to use to build model and visualize key metrics
from keras.models import Sequential
from keras.layers import Dense, Conv1D, Flatten, BatchNormalization, Dropout # LeakyReLU
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau   #Use callbacks to fine-tune the model
from keras import optimizers
from matplotlib import pyplot


## Try different combinations of layers and their respective hyperparameters
## Comment out the layers which are not desired. Also, keep an eye on batch_input_shape parameter for Conv1D    

model = Sequential()
model.add(Dropout((0.2), batch_input_shape=(None,302,1)))
model.add(Conv1D(64, 8, use_bias=True, activation='relu', bias_initializer='zeros', batch_input_shape=(None,302,1)))
#model.add(LeakyReLU(alpha=0.3))
#model.add(Dropout(0.2))
model.add(Conv1D(32, 4, use_bias=True, activation='relu', bias_initializer='zeros', batch_input_shape=(None,302,1)))
#model.add(LeakyReLU(alpha=0.3))
model.add(BatchNormalization(momentum=0.99, epsilon=0.0005))
model.add(Flatten())
model.add(Dropout(0.2))
model.add(Dense(64, activation='relu'))                # may use input_dim=(X,) if want to
#model.add(Dropout(0.2))
model.add(Dense(32, activation='relu'))
model.add(Dense(2, activation='sigmoid'))
sgd = optimizers.SGD(lr=0.02, momentum=0.9, nesterov=True)
model.compile(loss='mean_squared_error', optimizer=sgd, metrics=['accuracy'])

# Use callbacks to optimize and control the learning process
es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=20)
ch = ModelCheckpoint('spacymf_bestmodel.hdf5', monitor='val_acc', verbose=1, save_best_only=True, mode='max',period=1)
relr = ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=6, min_lr=0.0001, mode='min', verbose=1, min_delta=1E-5)
callbacks_list = [es,ch,relr]

# Train model on the traning dataset
history = model.fit(X_train,y_train,epochs=100, verbose=2, shuffle=True, batch_size=32, validation_split=0.1, callbacks=callbacks_list)

# Plot Training Accuracy Vs Validation accuracy and Training Loss Vs Validation loss charts
print('\nPerformance Charts\n')
pyplot.plot(history.history['acc'], label='training_accuracy')
pyplot.plot(history.history['val_acc'], label='validation_accuracy')
pyplot.show()
pyplot.plot(history.history['loss'], label='training_loss')    
pyplot.plot(history.history['val_loss'], label='validation_loss')
pyplot.show() 
        
print('------------------------------------------------------------------------')

# Saving the final trained model
print('Saving final model Final.hdf5')
model.save("Comb_final.hdf5")

# Evaluate the model using loss and accuracy metrics
model.evaluate(x=X_test,y=y_test)

# Make predictions on X_test using latest updated trained model
predictions = model.predict_classes(X_test)
print(predictions)

print(y_test.argmax(axis=1))

# Import metrics from sklearn
from sklearn import metrics

# Print a confusion matrix
print(metrics.confusion_matrix(y_test.argmax(axis=1),predictions))

# Print a classification report
print(metrics.classification_report(y_test.argmax(axis=1),predictions))

# Print the overall accuracy
print(metrics.accuracy_score(y_test.argmax(axis=1),predictions))

# Load test dataset with additional text_features for making final predictions using the latest updated instance of trained model
df1 = pd.read_csv('test_more_features.csv')
print(df1.head())

# Load corresponding tweet embeddings for test dataset same as that was loaded for training dataset
pickle_in = open("Spacy_test.pickle","rb")
test_array = pickle.load(pickle_in)
print(test_array.shape)

# Preparing test dataset for predictions by adding text features to the tweet embeddings data as it was done for training dataset 
tweet_len_arr_test = np.array(df1['tweet_len'])
tweet_punct_arr_test = np.array(df1['punct_len'])
print(tweet_len_arr_test.shape, tweet_punct_arr_test.shape)

tweet_len_norm_test = scaler.fit_transform(tweet_len_arr_test.reshape(-1, 1))
tweet_punct_norm_test = scaler.fit_transform(tweet_punct_arr_test.reshape(-1, 1))
print(tweet_len_norm_test.shape, tweet_punct_norm_test.shape)

test_X = np.hstack((test_array, tweet_len_norm_test, tweet_punct_norm_test))
print(test_X.shape)


# You may have to reshape the test tweet embeddings dataset in order to feed into ConV1D layer of the model
# However comment out this step if not using Convolution Neural Network layer in the model
test_X = np.reshape(test_X, test_X.shape + (1,))
print(test_X.shape)

# Make prediction on the test dataset for final submission
test_predictions = model.predict_classes(test_X)
print(test_predictions)
df1['label'] = test_predictions
df1 = df1.drop(['tweet','tweet_len','punct_len'],axis=1)
print(df1.head())

# Saving the final predictions to csv file
df1.to_csv('spacymf_final.csv', index=False)


# Now loading the best model that got saved using ModelCheckpoint Callback and its hyperparameters
from keras.models import load_model
model1 = load_model('spacymf_bestmodel.hdf5')

# Making predictions on test dataset using the best saved model
best_predictions = model1.predict_classes(test_X)
print(best_predictions)

# Making a copy of dataframe to store newly predicted sentiment values
df2 = df1
df2['label'] = best_predictions
print(df2.head())

# Saving the best predicted version of test dataset
df2.to_csv('spacymf_best_final.csv')