
##################################################
## Technical Indicator Examples (RSI, ATR, ADX) ##
##################################################

import traceback
import numpy as np
import pandas as pd
from influxdb import InfluxDBClient
import talib
import time


exchange = 'BITFINEX'

data_timeperiod_1m = '1m'
data_timeperiod_5m = '5m'
data_timeperiod_15m = '15m'
data_timeperiod_30m = '30m'
data_timeperiod_1h = '1h'
data_timeperiod_6h = '6h'
data_timeperiod_12h = '12h'
data_timeperiod_1d = '1d'
data_timeperiod_1w = '1w'

#influxdb param using HTTP
influxdb_params = ('yourhost', 8086, 'youruser', 'yourpwd', 'yourdatabase', False, False)

indicator_timeperiod = 14
clientInfluxdb = None


class Indicator:


    ############################## Connect to InfluxDB                
    def connectInfluxdb(self):
        host = influxdb_params[0]
        port = influxdb_params[1]
        username = influxdb_params[2]
        password = influxdb_params[3]
        database = influxdb_params[4]
        ssl = influxdb_params[5]
        verify_ssl = influxdb_params[6]
    
        try:
            print('Connection to InfluxDB...')        
            clientInfluxdb =  InfluxDBClient(host = host, port = port, username = username, password = password, database = database, ssl = ssl, verify_ssl = verify_ssl)        
            print('Connection to InfluxDB successfully established')
        except Exception as e:
            print('Could not connect to InfluxDB.')
            traceback.print_tb(e.__traceback__)
            clientInfluxdb = None
                   
        return clientInfluxdb
    
    ############################## disconnect from InfluxDB                
    def disconnectInfluxdb(self, clientInfluxdb):
        if clientInfluxdb is not None:
            clientInfluxdb.close()
            print('Connection to InfluxDB properly closed.')
            time.sleep(3)
        else:
            print('!! Could not close connection to InfluxDB.')          
    
    ############################## get_data_trades from influxdb
    def get_data_trades(self, symbol, group_by_timeperiod , look_back_timeperiod):
        global clientInfluxdb
        points = None
        
        try:       
            if (clientInfluxdb is None):
                clientInfluxdb = self.connectInfluxdb()
            
            if (clientInfluxdb):
                try:

                    query = f'SELECT first(price) AS open, last(price) AS close, max(price) AS high, min(price) AS low, sum(amount) AS volume, first(bitfinex_trade_time) AS trade_time_period FROM TRADES WHERE exchange=\'{exchange}\' AND symbol=\'{symbol}\'  AND time >= now() - {look_back_timeperiod} GROUP BY time({group_by_timeperiod}), symbol, exchange'
                    
                    results = clientInfluxdb.query(query)
                    
                    points = list(results.get_points(measurement='TRADES', tags={'symbol': symbol}))
                    
                    points = pd.DataFrame(points)
                    
                    if len(points.index.values) != 0: #check if points is not empty 
                        points = points.dropna(subset=['open', 'close', 'high', 'low', 'volume', 'trade_time_period'])
                               
                except Exception as writeInfluxdb:
                    traceback.print_tb(writeInfluxdb.__traceback__)
                    self.disconnectInfluxdb(clientInfluxdb)
                    raise print('!! ERROR in class Indicator when using get_data_trades().')
                    #break
        except Exception as e:
            print('Could not connect to InfluxDB.')
            traceback.print_tb(e.__traceback__)
            clientInfluxdb = None
            raise e.__traceback__
            
        else:
            
            return points
    
    ############################## compute_RSI from influxdb
    def compute_RSI(self, points = None, indicator_calculation_period = 14):
        values = None
        cleaned_RSI_values = []
        
        if (points is not  None):
            RSI = talib.RSI(points['close'].values, timeperiod = indicator_calculation_period)
            
            values = [[x, y] for x, y in zip(RSI, points['trade_time_period'].values)]
            
        #remove nan values
        for value in values:                           
            if np.logical_not(np.isnan(value[0])):
                cleaned_RSI_values.insert(0, value) # add the newest value on left of the list, oldest one is on the right
                
        return cleaned_RSI_values         
    
    ############################## compute_ADX from influxdb
    def compute_ADX(self, points = None, indicator_calculation_period = 14):
        values = None
        cleaned_ADX_values = []
        
        if (points is not  None):
            ADX = talib.ADX(points['high'].values, points['low'].values, points['close'].values, timeperiod = indicator_calculation_period)
            
            values = [[x, y] for x, y in zip(ADX, points['trade_time_period'].values)]
            
        #remove nan values
        for value in values:                           
            if np.logical_not(np.isnan(value[0])):
                cleaned_ADX_values.insert(0, value) # add the newest value on left of the list, oldest one is on the right
            
        return cleaned_ADX_values
        
    ############################## compute_ATR from influxdb
    def compute_ATR(self, points = None, indicator_calculation_period = 14):
        values = None
        cleaned_ATR_values = []
        
        if (points is not  None):
            ATR = talib.ATR(points['high'].values, points['low'].values, points['close'].values, indicator_calculation_period)
    
            values = [[x, y] for x, y in zip(ATR, points['trade_time_period'].values)]
                    
        #remove nan values
        for value in values:                           
            if np.logical_not(np.isnan(value[0])):
                cleaned_ATR_values.insert(0, value) # add the newest value on left of the list, oldest one is on the right        
        
        return cleaned_ATR_values
    
    ############################## retrive needed indicator
    def get_indicator(self, symbol, used_indicator, group_by_timeperiod, indicator_calculation_period, look_back_timeperiod):
        values = None
               
        points = self.get_data_trades(symbol, group_by_timeperiod, look_back_timeperiod)
        if (used_indicator == 'RSI'):
            values = self.compute_RSI(points, indicator_calculation_period)
        elif (used_indicator == 'ADX'):
            values = self.compute_ADX(points, indicator_calculation_period)
        elif (used_indicator == 'ATR'):
            values = self.compute_ATR(points)
        else:
            values = None
            
        return values

