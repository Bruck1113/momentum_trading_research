import ib_insync
from ib_insync import *
import ibapi
from ibapi.client import *
from ibapi.wrapper import *
from ibapi.contract import Contract
import threading
import time
import yfinance as yf
import datetime as dt
import pandas as pd
import threading
from const import STOCKS
from decimal import *

from ibapi.client import *
from ibapi.wrapper import *
from ibapi.contract import Contract
import threading
import time

class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 
        self.reqMarketDataType(3)
        self.res = {}
    # def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
    #     print("TickGeneric. TickerId:", reqId, "TickType:", tickType, "Value:", floatMaxString(value))

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        print(reqId, tickType, price, attrib)
        self.res[reqId] = price  # Store price in the dictionary

    def getPrices(self):
        return self.res
    # def tickSize(self, reqId: TickerId, tickType: TickType, size: Decimal):
    #     print("TickSize. TickerId:", reqId, "TickType:", tickType, "Size: ", decimalMaxString(size))

    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        print("TickString. TickerId:", reqId, "Type:", tickType, "Value:", value)

    # def tickReqParams(self, tickerId:int, minTick:float, bboExchange:str, snapshotPermissions:int):
    #     print("TickReqParams. TickerId:", tickerId, "MinTick:", floatMaxString(minTick), "BboExchange:", bboExchange, "SnapshotPermissions:", intMaxString(snapshotPermissions))

    def rerouteMktDataReq(self, reqId: int, conId: int, exchange: str):
        print("Re-route market data request. ReqId:", reqId, "ConId:", conId, "Exchange:", exchange)


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

class data:
    def __init__(self, type, security) -> None:
        self.type =  type # For verifying if user is requesting historical or tick data
        self.security = security # Contract type object
        self.value = []

    def request(self, tradeApp):
        

class tools:
    def __init__(self, ibClient) -> None:
        self.core = ibClient
        self.wrapper = EWrapper()
        self.client = EClient(self.wrapper)
        self.client.reqMarketDataType(3)
        self.tickers = []
        for symbol in STOCKS:
            contract = Contract()
            contract.symbol = symbol
            contract.secType = 'STK'
            contract.exchange = 'SMART'
            contract.currency = 'USD'
            self.tickers.append(contract)
        self.numRequests = 0

    def tickers_to_contract(self, tickers):
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
        return contract_lst

    def update_num_to_df(self, key, contract, df_dico):
        ticker = self.core.reqMktData(contract)
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

    def hist_data_feed(self, key, contract, ticker_lst):
        ticker = self.core.reqHistoricalData(
            contract,
            endDateTime="20230503 15:59:00 US/Eastern",
            durationStr='10 D',
            barSizeSetting='1 min',
            whatToShow='MIDPOINT',
            useRTH=True,
            formatDate=1)
        ticker_lst.append(ticker)

        return ticker

    def totalmarket_data_needed(self, tickers, df_dico)->dict:
        threads = []
        contracts = self.tickers_to_contract(tickers)
        for i in contracts:
            thrd = threading.Thread(target=self.update_num_to_df(i.symbol, i, df_dico))
            threads.append(thrd)

        for j in threads:
            j.start()

        for j in threads:
            j.join()

        return df_dico

    def hist_data(self, tickers, ticker_lst):
        threads = []
        contracts = self.tickers_to_contract(tickers)
        for i in contracts:
            thrd = threading.Thread(target=self.hist_data_feed(i.symbol, i, ticker_lst))
            threads.append(thrd)

        for j in threads:
            j.start()

        for j in threads:
            j.join()

        return ticker_lst

    def get_Quotes(self):
        res = {}
        tradeApp = TradeApp()
        tradeApp.connect("127.0.0.1", 7497, 1000)

        time.sleep(10)
        tradeApp.reqMarketDataType(3)
        # con_thread = threading.Thread(target=websocket_con, daemon=True)
        # con_thread.start()
        for contract in self.tickers:
            # curRequestSize = len(self.requests)
            # tradeApp.reqMktDataType(1) #Choose getting Live Data
            tradeApp.reqMktData(self.numRequests, contract, "", False, False, [])
            # self.reqRealTimeBars(3001, contract, 5, "MIDPOINT", 0, [])
            self.numRequests += 1

        tradeApp.run()
        tradeApp.disconnect()
        res = tradeApp.getPrices()
        return res


    # Defining a function to retrieve the stocks that the program is watching
    def get_top_50_stocks():
        sp500_tickers = yf.Tickers('^GSPC')  # Fetch S&P 500 tickers
        sp500_df = sp500_tickers.tickers['^GSPC'].history(period='1d')  # Get historical data for S&P 500
        sp500_df = sp500_df.sort_values('Volume', ascending=False).head(50)  # Sort by volume and get top 50 stocks

        stock_dict = {}
        for symbol in sp500_df.index:
            stock = stock_obj(symbol, "SMART", "USD")  # Replace 'Exchange' and 'Currency' with actual values
            stock_dict[symbol] = stock

        return stock_dict


class equityStrategy:

    def __init__(self, watching_stocks) -> None:
        self.watching_stocks = {}
        for symbol in watching_stocks:
            stock = stock_obj(symbol, "SMART", "USD")  # Replace 'Exchange' and 'Currency' with actual values
            self.watching_stocks[symbol] = stock


    def placing_order(self, direction, quantity):
        order = ibapi.Order()
        order.action = direction
        order.orderType = "MKT"
        order.totalQuantity = quantity
    
# class allocation_strategy:

#     def __init__(self, watching_stocks) -> None:
#         self.core = equityStrategy(watching_stocks)

#     def listen(self, updatedPrices):
        