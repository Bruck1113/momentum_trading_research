import requests
from binance.spot import Spot
import configparser
import pandas as pd
import logging
import time
#from binance.websocket.spot.websocket_api import SpotWebsocketAPIClient


#For regular price extraction, regualr client is enough
client = Spot()
config = configparser.ConfigParser()
config.read("config.ini")

#For user information extraction, use user_client
user_client = Spot(api_key=config["keys"]["api_key"], api_secret=config["keys"]["api_secret"])

def tick_data_storage(token):
    par = token + "USDT"
    data = client.klines(par, "1m")
    return pd.DataFrame(data, columns=["Open time", "Open", "High", "Low", "Close", "Volume", "Close time", "Quote asset volume", "Number of trades", "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"])

def get_ticker(pair=None):
    default_url = "https://www.binance.com/api/v3/ticker/price?symbol="
    all_tickers_info = "https://www.binance.com/api/v3/ticker/price"

    if pair == None:
        url = all_tickers_info

    else:
        url = default_url + pair

    obj = requests.get(url)
    return obj.json()


def on_close(_):
    logging.info("Do custom stuff when connection is closed")

def message_handler(_, message):
    logging.info(message)


# Get server timestamp
print(client.time())
# Get klines of BTCUSDT at 1m interval
print(client.klines("BTCUSDT", "1m"))
# Get last 10 klines of BNBUSDT at 1h interval
print(client.klines("BNBUSDT", "1h", limit=10))

df = tick_data_storage("ETH")

time.sleep(2)
my_client.ticker(symbols=["BNBBUSD", "BTCUSDT"], type="MINI", windowSize="2h")
time.sleep(2)

# API key/secret are required for user data endpoints
client = Spot(api_key=config["keys"]["api_key"], api_secret=config["keys"]["api_secret"])

# Get account and balance information
print(client.account())

# Post a new order
# params = {
#     'symbol': 'BTCUSDT',
#     'side': 'SELL',
#     'type': 'LIMIT',
#     'timeInForce': 'GTC',
#     'quantity': 0.002,
#     'price': 9500
# }


