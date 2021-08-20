
#################################################################################################################
## Scraping Real Time Data (trades) from an Exchange and insert them in big data time series database InfluxDB ##
#################################################################################################################

import asyncio
import websockets
import traceback
import json
import time
import logging, logging.config
from copy import deepcopy
from influxdb import InfluxDBClient

symbol = 'tBTCUSD'
exchange = 'BITFINEX'

websocket_timeout = 30
asyncio_sleep = 0.01 

#influxdb param using HTTP
influxdb_params = ('localhost', 8086, 'USER', 'USER', 'DATABASE', False, False)

SUB_MESG_TRADES = {
        'event': 'subscribe',
        'channel': 'trades',
        'symbol': symbol
    }

# Logger creation
logging_config = logging.config.fileConfig('/logger/config_v1.0.ini')
logger = logging.getLogger(logging_config)

############################## Creat the data model and insert scrapped tardes within the memory queue (data producer)
async def build_trades_bids_asks(trade, queue):        
    trade_side = None
       
    trade = json.loads(trade)
    
    if trade:
        if isinstance(trade, list):
            if not isinstance(trade[1], list):             
                if trade[1] == 'te':                      
                    if (float(trade[2][2]) >= 0): # means buy trade
                        trade_side = 'buy'
                    else: # means sell trade
                        trade_side = 'sell'
                        
                    fetched_trade = [
                                {
                                    'measurement': 'TRADES',
                                    'tags': {
                                        'symbol': symbol,
                                        'exchange': exchange,
                                        'trade_side': trade_side
                                    },
                                    'fields': {
                                        'id': int(trade[2][0]),
                                        'bitfinex_trade_time': int(trade[2][1]),
                                        'amount': float(trade[2][2]),
                                        'price': float(trade[2][3])
                                    }
                                }
                            ]

                    await queue.put(fetched_trade)
 
    await asyncio.sleep(asyncio_sleep)
    
############################## Scrap data from exchange
async def get_trades(queue):
    symbol_dict = deepcopy(SUB_MESG_TRADES)
    async with websockets.connect('wss://api.bitfinex.com/ws/2') as websocket_get_trades:
        await websocket_get_trades.send(json.dumps(symbol_dict))
        
        while True:           
            try:
                res = await asyncio.wait_for(websocket_get_trades.recv(), timeout = websocket_timeout)
            except asyncio.TimeoutError:
                print('{0} -> In get_trades() Waited {1}s, still to wait {2}s before disconnect'.format(symbol, websocket_timeout, websocket_timeout))
                try:
                    pong_waiter = await websocket_get_trades.ping()
                    await asyncio.wait_for(pong_waiter, timeout = websocket_timeout)
                except asyncio.TimeoutError:
                    print('{0} -> CONNECTION CLOSED raised exception in get_trades() -> TRYING TO RECONNECT !!!'.format(symbol))
                    raise websockets.ConnectionClosed('ConnectionClosed ---> in get_trades()')
                    Exception
                    break
            else:
                await build_trades_bids_asks(res, queue)
                await asyncio.sleep(asyncio_sleep)

############################## Connect to InfluxDB                
def connectInfluxdb():
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
  
############################## Disconnect from InfluxDB                
def disconnectInfluxdb(clientInfluxdb):
    if clientInfluxdb is not None:
        clientInfluxdb.close()
        print('Connection to InfluxDB properly closed.')
        time.sleep(3)
    else:
        print('!! Could not close connection to InfluxDB.')          
 
############################## Insert within Influxdb scrapped tardes consumed from the memory queue (data consumer)
async def save_real_time_market_data(queue):

    try:       
        clientInfluxdb = connectInfluxdb()
        
        while True:
            if (clientInfluxdb):
                try:
                    if (queue.qsize() != 0):
                        # wait for a fetched_trade from the producer
                        fetched_value =  await queue.get()
                        
                        clientInfluxdb.write_points(fetched_value) 

                    await asyncio.sleep(asyncio_sleep)
                
                except Exception as writeInfluxdb:
                    traceback.print_tb(writeInfluxdb.__traceback__)
                    disconnectInfluxdb(clientInfluxdb)
                    raise print('!! Could not write to InfluxDB.')
                    break
    except Exception as e:
        print('Could not connect to InfluxDB.')
        traceback.print_tb(e.__traceback__)
        clientInfluxdb = None
        raise e.__traceback__


loop = asyncio.get_event_loop()
queue = asyncio.LifoQueue(loop=loop)
tasks = [get_trades(queue), save_real_time_market_data(queue)]
loop.run_until_complete(asyncio.gather(*tasks))
 
