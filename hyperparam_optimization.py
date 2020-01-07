#################################
## Tuning LSTM hyperparameters ##
#################################

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.model_selection import GridSearchCV

from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout


#LSTM config
timesteps = 65
LSTM_units = 30
dropout = 0.2
epochs = 100
batch_size = 35

# Importing the training set
dataset_train = pd.read_csv('dataset_train.csv')
training_set_x = dataset_train.iloc[:, :].values
training_set_y = dataset_train.iloc[:, -1:].values

# Feature Scaling
sc_x = MinMaxScaler(feature_range = (0, 1))
sc_y = MinMaxScaler(feature_range = (0, 1))
training_set_scaled_x = sc_x.fit_transform(training_set_x)
training_set_scaled_y = sc_y.fit_transform(training_set_y)

# Building training set
X_train = []
y_train = []
for i in range(timesteps, training_set_scaled_x.shape[0]):
    X_train.append(training_set_scaled_x[i-timesteps:i, :])
    
for i in range(timesteps, training_set_scaled_y.shape[0]):
    y_train.append(training_set_scaled_y[i, 0])
    
    
X_train, y_train = np.array(X_train), np.array(y_train)

# Reshaping
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], training_set_scaled_x.shape[1]))



def build_regressor(optimizer):
    # Building LSTM
    # Initialising LSTM
    regressor = Sequential()
    
    # Adding the first LSTM layer and Dropout regularisation
    regressor.add(LSTM(units = LSTM_units, return_sequences = True, input_shape = (X_train.shape[1], 3)))
    regressor.add(Dropout(dropout))
    
    # Adding a second LSTM layer and Dropout regularisation
    regressor.add(LSTM(units = LSTM_units, return_sequences = True))
    regressor.add(Dropout(dropout))
    
    # Adding a third LSTM layer and Dropout regularisation
    regressor.add(LSTM(units = LSTM_units))
    regressor.add(Dropout(dropout))
    
    # Adding the output layer
    regressor.add(Dense(units = 1))
    
    # Compiling LSTM
    regressor.compile(optimizer = optimizer, loss = 'mean_squared_error')
    return regressor

regressor = KerasRegressor(build_fn = build_regressor)

param_grid = {'optimizer': ['adam', 'rmsprop', 'sgd']}

grid_search = GridSearchCV(estimator = regressor, param_grid = param_grid, scoring = 'neg_mean_squared_error', cv = 3)

grid_search = grid_search.fit(X_train, y_train)

print('Best parameters found:')
print(grid_search.best_params_)
print('Best score found:')
print(grid_search.best_score_)


