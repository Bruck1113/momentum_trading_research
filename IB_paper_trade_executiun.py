import ib_insync
import ibapi
import numpy as np
import pandas as pd
import csv
import json
import flask
import threading
import time
import datetime as dt
from ib_insync import *

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

#create different classes for creating contract later
class stock_obj():

    def __init__(self, symbol, exchange, currency):
        self.name = symbol
        self.exchange = exchange
        self.currency = currency

class Forex():

    def __init__(self, pair):
        self.pair = pair

class Future():

    def __init__(self, underlying, last_trading_date, exchange):
        self.underlying = underlying
        self.last_trading_date = last_trading_date
        self.exchange = exchange

class Option():

    def __init__(self, pair, lasttradedate, strike, right, exchange):
        self.pair = pair
        self.last_trade_date = lasttradedate
        self.strike = strike
        self.right = right
        self.exchange = exchange


ib = IB()
ib.connect('127.0.0.1', 7497, clientId=5)
# Contract(conId=270639)
# Stock('AMD', 'SMART', 'USD')
# Stock('INTC', 'SMART', 'USD', primaryExchange='NASDAQ')
# Forex('EURUSD')
# CFD('IBUS30')
# Future('ES', '20180921', 'GLOBEX')
# Option('SPY', '20170721', 240, 'C', 'SMART')
# Bond(secIdType='ISIN', secId='US03076KAA60')
# Crypto('BTC', 'PAXOS', 'USD')


# app.connect('127.0.0.1', 7497, 123 )
def tickers_to_contract(tickers):
    contract_lst = []
    # funcdict = {"Stock":Stock, "Forex":Forex, "Future":Future, "Option":Option}
    # This is for ib_insync contract object
    for i in tickers:
        if type(i) == stock_obj:
            contract = Stock(i.name, i.exchange, i.currency)
        elif type(i) == "Forex":
            contract = Forex(i.pair)
        elif type(i) == "Future":
            contract = Future(i.underlying, i.last_trading_date, i.exchange)
        else:
            contract = Option(i.pair, i.last_trading_date, i.strike, i.right, i.exchange)

        contract_lst.append(contract)
        # contract = Contract()
        # contract.symbol = i
        # contract.secType = 'STK'
        # contract.exchange = 'SMART'
        # contract.currency = 'USD'
        # contract_lst.append(contract)
    return contract_lst

def update_num_to_df(key, contract, df_dico):
    ticker = ib.reqMktData(contract)
    value = ticker.marketPrice()
    print(str(value))
    if len(df_dico[key]) == 0:
        print("first condition")
        data = {"time": dt.datetime.now(), "Price": str(value)}
        df_dico[key] = pd.DataFrame(data, index=[0])
        df_dico[key].columns = ["time", "Price"]
    else:
        print("second condition")
        data = {"time": dt.datetime.now(), "Price": value}
        df_dico[key] = df_dico[key].append(data, ignore_index=True)

def hist_data_feed(key, contract, ticker_lst):
    ticker = ib.reqHistoricalData(
        contract,
        endDateTime="20230503 15:59:00 US/Eastern",
        durationStr='10 D',
        barSizeSetting='1 min',
        whatToShow='MIDPOINT',
        useRTH=True,
        formatDate=1)
    ticker_lst.append(ticker)

    return ticker
def totalmarket_data_needed(tickers, df_dico)->dict:
    threads = []
    contracts = tickers_to_contract(tickers)
    for i in contracts:
        thrd = threading.Thread(target=update_num_to_df(i.symbol, i, df_dico))
        threads.append(thrd)

    for j in threads:
        j.start()

    for j in threads:
        j.join()

    return df_dico

def hist_data(tickers, ticker_lst):
    threads = []
    contracts = tickers_to_contract(tickers)
    for i in contracts:
        thrd = threading.Thread(target=hist_data_feed(i.symbol, i, ticker_lst))
        threads.append(thrd)

    for j in threads:
        j.start()

    for j in threads:
        j.join()

    return ticker_lst
#Start the socket in a thread
# api_thread = threading.Thread(target=run_loop, daemon=True)
# api_thread.start()


#Making a ticker list to extract data
ticker_lst  = [stock_obj("TSLA", "SMART", "USD"), stock_obj("AAPL", "SMART", "USD")]
df_dico = {}
for i in ticker_lst:
    df_dico[i.name] = pd.DataFrame()

tick = []
count = 0
while(count < 1):
    prev_time = dt.datetime.now()
    df_dico = hist_data(ticker_lst, tick)
    print(dt.datetime.now() - prev_time)
    time.sleep(2)
    count += 1




#Create contract object
# apple_contract = Contract()
# apple_contract.symbol = 'AAPL'
# apple_contract.secType = 'STK'
# apple_contract.exchange = 'SMART'
# apple_contract.currency = 'USD'
#


#Request Market Data
# app.reqMktData(1, apple_contract, '', False, False, [])

time.sleep(10) #Sleep interval to allow time for incoming price data
# app.disconnect()
# app.run()

'''
#Uncomment this section if unable to connect
#and to prevent errors on a reconnect
# import time
# time.sleep(2)
# app.disconnect()
'''
