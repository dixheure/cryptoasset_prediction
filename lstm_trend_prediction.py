

########################################################################
## Making CryptoAsset Prediction Using Recurrent Neural Network (RNN) ## 
########################################################################

# Importing libraries
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
# Retrive data from time series database (influxdb)
from influxdb_retrive_data import InfluxdbRetriveData
# Used to process data
from sklearn.preprocessing import MinMaxScaler
# Construct the RNN (LSTM will be used in this example)
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout


#DataSet definition
exchange = 'BITFINEX' # exchange
symbol = 'tBTCUSD' # cryptoasset
look_back_timeperiod = '5d' # data extraction point, in this example now - 5 days
size_dataset_train = 80 # in percentage
size_dataset_test = 20 # in percentage

#LSTM config
timesteps = 65
LSTM_units = 30
dropout = 0.2
epochs = 100
batch_size = 35


# Extracting data from InfluxDB and load it within CSV files
influxdbRetriveData = InfluxdbRetriveData()
influxdbRetriveData.get_trades_data(exchange, symbol, look_back_timeperiod, size_dataset_train, size_dataset_test)


# Importing training set
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
regressor.compile(optimizer = 'adam', loss = 'mean_squared_error')

# Fitting LSTM to training set
regressor.fit(X_train, y_train, epochs = epochs, batch_size = batch_size)


# Making the predictions and visualising the results

# Getting real price 
dataset_test = pd.read_csv('dataset_test.csv')
real_stock_price = dataset_test['price'].values

# Getting the predicted price
dataset_total = pd.concat((dataset_train, dataset_test), axis = 0)

inputs = dataset_total[len(dataset_total) - len(dataset_test) - timesteps:].values
inputs = sc_x.transform(inputs)

X_test = []
for i in range(timesteps, inputs.shape[0]):
    X_test.append(inputs[i-timesteps:i, :])

X_test = np.array(X_test)
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], inputs.shape[1]))

predicted_stock_price = regressor.predict(X_test)
predicted_stock_price = sc_y.inverse_transform(predicted_stock_price)

# Visualising results
plt.plot(real_stock_price, color = 'blue', label = 'Real CryptoAsset Price')
plt.plot(predicted_stock_price, color = 'green', label = 'Predicted CryptoAsset Price')
plt.title('CryptoAsset Price Prediction')
plt.xlabel('Time')
plt.ylabel('CryptoAsset Price')
plt.legend()
plt.show()

# Publish the trained LSTM Model
regressor.save('LSTM_v1.0.h5')


