

#########################################################
## Get data from bigdata time series database InfluxDb ##
#########################################################


import traceback
import pandas as pd
from influxdb import InfluxDBClient
import time


#influxdb param using HTTP
influxdb_params = ('localhost', 8086, 'USER', 'USER', 'DATABASE', False, False)

clientInfluxdb = None


class InfluxdbRetriveData:


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
    
    ############################## retrive data from InfluxDB (trade_time, amount, price)
    def get_trades_data(self, exchange, symbol, look_back_timeperiod, size_dataset_train, size_dataset_test):
        global clientInfluxdb
        points = None
        dataset_train = None
        dataset_test = None
        
        try:       
            if (clientInfluxdb is None):
                clientInfluxdb = self.connectInfluxdb()
            
            if (clientInfluxdb):
                try:
                    
                    if ((size_dataset_train + size_dataset_test) != 100):
                        raise print('!! ERROR in class InfluxdbRetriveData get_trades_data size_dataset_train + size_dataset_test different from 100%')
                    
                    query = f'SELECT bitfinex_trade_time, amount, price  FROM TRADES WHERE exchange=\'{exchange}\' AND symbol=\'{symbol}\' AND time >= now() - {look_back_timeperiod} GROUP BY exchange, symbol'

                    results = clientInfluxdb.query(query)
                        
                    points = list(results.get_points(measurement='TRADES', tags={'symbol': symbol}))
                    
                    points = pd.DataFrame(points)
                    
                    if len(points.index.values) != 0: #check if points is not empty 
                        points = points.dropna(subset=['bitfinex_trade_time', 'amount', 'price'])
                        points = pd.concat((points['bitfinex_trade_time'], points['amount'], points['price']), axis=1)
                        index_dataset_train = int((points.shape[0]*size_dataset_train)/100)
                        dataset_train = points.iloc[:index_dataset_train]
                        dataset_test = points.iloc[index_dataset_train:]
                        dataset_train.to_csv(path_or_buf='dataset_train.csv', index_label = False)
                        dataset_test.to_csv(path_or_buf='dataset_test.csv', index_label = False)
                except Exception as writeInfluxdb:
                    traceback.print_tb(writeInfluxdb.__traceback__)
                    self.disconnectInfluxdb(clientInfluxdb)
                    raise print('!! ERROR in class InfluxdbRetriveData when using get_trades_data().')
        except Exception as e:
            print('Could not connect to InfluxDB.')
            traceback.print_tb(e.__traceback__)
            clientInfluxdb = None
            raise e.__traceback__
            
        else:            
            return dataset_train, dataset_test
    
     
