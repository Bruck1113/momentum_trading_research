import requests
from binance.spot import Spot
import configparser
import pandas as pd
import logging
import time
# import ccxt
# from ccxt import binance, deribit
from datetime import datetime, timedelta
import pytz
import arrow
from typing import Dict
# import pandas as pd
from ccxt import deribit, binance




exchange = deribit()
spot_exchange = binance()
binance_spot_testnet_api = "VUdQSkMwfad4OIM3rd3oHyVZ3agVrcuUsG1PT8ai6GlfR4d9M7IxKpKHg9AEKbbA"
binance_spot_testnet_secret = "VFkJ0L4drBKZ7Xmf8bILROxYbj86CcOeaZsHxuHMzMjXbl2fS0Ne22dRyxsEVKfo"
btc_usdt_ob = spot_exchange.fetch_order_book('BTC/USDT')
best_ask = min([x[0] for x in btc_usdt_ob['asks']])
best_bid = max([x[0] for x in btc_usdt_ob['bids']])
mid = (best_ask + best_bid) / 2
target_expiry : datetime = datetime.utcnow() + timedelta(days=3)
target_expiry = target_expiry.replace(tzinfo=pytz.UTC)

exchange = deribit()
markets = exchange.load_markets()



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


def _extract_from_market(market : Dict) -> Dict:
    print("hello world")
    is_option : bool = market['option']
    option_type : str = market['optionType'] if 'optionType' in market else '---'
    symbol : str = market['symbol']
    expiry : datetime = arrow.get(market['expiryDatetime']).datetime
    strike : float = market['strike']
    return {
        'symbol' : symbol,
        'is_option' : is_option,
        'option_type' : option_type,
        'expiry' : expiry,
        'strike' : strike
    }

def _btc_options_market_filter(market : Dict, mid : float, target_expiry : datetime, strike_range_pct : float = 10, target_ccy : str = 'BTC') -> bool:
    market_extract = _extract_from_market(market)
    is_option = market_extract['is_option']
    option_type = market_extract['option_type']
    symbol = market_extract['symbol']
    expiry = market_extract['expiry']

    #Strike doesn't exist
    strike = market_extract['strike']

    lower_strike_limit = mid * (1-strike_range_pct/100)
    higher_strike_limit = mid * (1+strike_range_pct/100)
    if strike == None:
        strike = 0


    if is_option and target_ccy in symbol and expiry.year == target_expiry.year and expiry.month == target_expiry.month and expiry.day<=target_expiry.day and strike > lower_strike_limit and strike < higher_strike_limit:
        return True
    else:
        return False
'''
We calling Deribit's API "get_book_summary_by_instrument":
    https://docs.deribit.com/#public-get_book_summary_by_instrument
But we do so via ccxt "Implicit Methods"
    https://github.com/ccxt/ccxt/wiki/Manual
'''


marks = [markets[i] for i in markets.keys()]
btc_markets = sorted([mark for mark in marks if _btc_options_market_filter(mark, mid, target_expiry)], key=lambda mark : mark['strike'])

def _get_book_summary_by_instrument(instrument_name : str):
    params = {
        'instrument_name' : instrument_name
    }
    return exchange.public_get_get_book_summary_by_instrument( params = params )

def reorganize_dataframe(btc_markets):

    print(f"overall start: {datetime.now()}")
    columns = ['symbol', 'option_type', 'expiry', 'strike', 'open_interest']
    summaries = pd.DataFrame(columns=columns)
    i = 0
    for market in btc_markets:
        market_extract = _extract_from_market(market)
        summary = _get_book_summary_by_instrument(instrument_name=market['id'])
        summaries.loc[i] = [ market_extract['symbol'], market_extract['option_type'], market_extract['expiry'], market_extract['strike'], summary['result'][0]['open_interest'] ]
        i = i + 1

    summaries.sort_values(by=['expiry', 'strike', 'option_type'], ascending=[True, True, False], inplace=True)
    return summaries

def compute_put_call_ratio(dt: pd.DataFrame):
    data = dt.copy()
    ratios = {}
    for i in list(data["strike"]):
        ratios[i] = {"put":data[ (data["option_type"] == "put") & (data["strike"] == i)]["open_interest"],
                     "call":data[ (data["option_type"] == "call") & (data["strike"] == i)]["open_interest"]}
        # ratios[i]["p/c"] = float(ratios[i]["put"] / ratios[i]["call"])

    ratios["p/c"] = ratios["put"] / ratios["call"]
    return ratios

df = reorganize_dataframe(btc_markets)
ratios = compute_put_call_ratio(df)
print(f"overall finish: {datetime.now()}")



# Get server timestamp
# print(client.time())
# dic = get_deribit_put_call_open_interest("BTC")
# # Get klines of BTCUSDT at 1m interval
# print(client.klines("BTCUSDT", "1m"))
# # Get last 10 klines of BNBUSDT at 1h interval
# print(client.klines("BNBUSDT", "1h", limit=10))

# dico = get_deribit_btc_futures_open_interest()
# df = tick_data_storage("ETH")
#
# time.sleep(2)
# # my_client.ticker(symbols=["BNBBUSD", "BTCUSDT"], type="MINI", windowSize="2h")
# time.sleep(2)
#
# # API key/secret are required for user data endpoints
# client = Spot(api_key=config["keys"]["api_key"], api_secret=config["keys"]["api_secret"])
#
# # Get account and balance information
# print(client.account())

# Post a new order
# params = {
#     'symbol': 'BTCUSDT',
#     'side': 'SELL',
#     'type': 'LIMIT',
#     'timeInForce': 'GTC',
#     'quantity': 0.002,
#     'price': 9500
# }


