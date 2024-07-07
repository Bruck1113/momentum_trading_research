import ib_insync
import ibapi
import numpy as np
import pandas as pd
import csv
import json
import flask
import threading
import time
import schedule
# import time
import datetime as dt
from ib_insync import *
import yfinance as yf
import logging
import paper_trading_strategies as tools
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from const import TRADING_STOCKS

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=5)
toolsPack = tools.tools(ib)

def logTemplate(df):
    print("The quote prices at time " + str(dt.datetime.now()))
    for i in df.keys():
        print(str(i.symbol) + ": " + str(df[i]))

# top_50_stocks_dict = tools.get_top_50_stocks()
# ticker_lst  = top_50_stocks_dict
tick = []
# while(count < 1):
#Making a ticker list to extract data
def initiate():
    trading_stocks = TRADING_STOCKS
    
def listen():
    prev_time = dt.datetime.now()
    # df_dico = toolsPack.get_Quotes()
    # logTemplate(df_dico)


def main():
    print("Setting up trading environment")
    initiate()
    print("Listening started ")
    listen()
    

main()


#Create contract object
# apple_contract = Contract()
# apple_contract.symbol = 'AAPL'
# apple_contract.secType = 'STK'
# apple_contract.exchange = 'SMART'
# apple_contract.currency = 'USD'
#


#Request Market Data
# app.reqMktData(1, apple_contract, '', False, False, [])

# time.sleep(10) #Sleep interval to allow time for incoming price data
# app.disconnect()
# app.run()

'''
#Uncomment this section if unable to connect
#and to prevent errors on a reconnect
# import time
# time.sleep(2)
# app.disconnect()
'''

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

#Start the socket in a thread
# api_thread = threading.Thread(target=run_loop, daemon=True)
# api_thread.start()