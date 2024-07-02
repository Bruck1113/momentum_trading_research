import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
yf.pdr_override()

STOCKS = [
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "NVDA",
    "JPM"
]

prices = pdr.get_data_yahoo(STOCKS, start="2024-04-01", end="2024-06-28")['Adj Close']
prices = prices.dropna(axis = 1)

prices.to_csv("Table 1.csv")
