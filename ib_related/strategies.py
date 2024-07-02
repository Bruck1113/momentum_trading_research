from securities import *
from const import allocation_strategy_boosted
from portfolios import allocation_strategy_allocation
import pandas as pd


def setDefaultAllocation(stocks):
    res = {}
    for s in stocks:
        res[s] = 1/len(stocks)
    return res

class equityStrategy:

    def __init__(self, watching_stocks, ibClient) -> None:
        self.watching_stocks = {}
        for symbol in watching_stocks:
            stock = stock_obj(symbol, "SMART", "USD")  # Replace 'Exchange' and 'Currency' with actual values
            self.watching_stocks[symbol] = stock
        self.tradingApp = ibClient
        
    def placing_order(self, direction, quantity):
        order = self.tradingApp.Order()
        order.action = direction
        order.orderType = "MKT"
        order.totalQuantity = quantity

class allocationStrategy(equityStrategy):

    def __init__(self, watching_stocks, ibClient) -> None:
        super().__init__(watching_stocks, ibClient)
        if allocation_strategy_boosted:
            self.allocation = setDefaultAllocation(watching_stocks)
        else:
            self.allocation = allocation_strategy_allocation
        self.tradingStocks = [stock_obj(i, 'SMART', 'USD') for i in watching_stocks]
        self.data = pd.read_csv("Table 1.csv") # Dataframe
        self.signals = 

    def logic(self):
        for stock in self.tradingStocks:
            if stock.getCurrentReturn() < self.signal:
                self.placing_order(1, 1)
            elif stock.getCurrentReturn() > self.signal2:
                self.placing_order(-1, 1)


    # Different strategies will listen to different things
    def listen(self, priceUpdate):
        # priceUpdate will be a dictionary appended to the prices 

        