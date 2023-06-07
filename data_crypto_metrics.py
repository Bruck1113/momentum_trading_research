import requests
from binance.spot import Spot
import configparser
import pandas as pd
import logging
import time
from ccxt import binance, deribit

exchange = deribit()
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

# def get_active_user_eth():
#     # Connect to the Ethereum network
#     w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR-PROJECT-ID'))
#
#     # Get the number of active accounts
#     num_active_accounts = w3.eth.accounts.count()
#
#     print("Number of active accounts:", num_active_accounts)

def _get_book_summary_by_instrument(instrument_name : str):
    params = {
        'instrument_name' : instrument_name
    }
    return exchange.public_get_get_book_summary_by_instrument( params = params )

def get_deribit_put_call_open_interest(token):
    # Deribit API endpoint for retrieving options open interest
    url = 'https://www.deribit.com/api/v2/public/get_open_interest'

    # Parameters for retrieving Bitcoin options open interest
    params = {
        'currency': token,
        'kind': 'option',
        'expired': False
    }

    # Send the API request and retrieve the response
    response = requests.get(url, params=params).json()

    # Initialize an empty dictionary to store the open interest by expiry date
    open_interest_by_expiry = {}

    # Loop through each option contract in the response
    for contract in response['result']:
        # Extract the expiry date from the contract name
        expiry_date = contract['instrument_name'].split('-')[-1]

        # Extract the put/call open interest from the contract data
        put_open_interest = contract['open_interest_puts']
        call_open_interest = contract['open_interest_calls']

        # If this is the first contract for this expiry date, create a new dictionary entry
        if expiry_date not in open_interest_by_expiry:
            open_interest_by_expiry[expiry_date] = {}

        # Add the put/call open interest to the dictionary for this expiry date
        open_interest_by_expiry[expiry_date]['put'] = put_open_interest
        open_interest_by_expiry[expiry_date]['call'] = call_open_interest

    return open_interest_by_expiry



# Get server timestamp
print(client.time())
dic = get_deribit_put_call_open_interest("BTC")
# Get klines of BTCUSDT at 1m interval
print(client.klines("BTCUSDT", "1m"))
# Get last 10 klines of BNBUSDT at 1h interval
print(client.klines("BNBUSDT", "1h", limit=10))

df = tick_data_storage("ETH")

time.sleep(2)
# my_client.ticker(symbols=["BNBBUSD", "BTCUSDT"], type="MINI", windowSize="2h")
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


