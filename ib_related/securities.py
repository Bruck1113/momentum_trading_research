#create different classes for creating contract later
class stock_obj():

    def __init__(self, symbol, exchange, currency):
        self.name = symbol
        self.exchange = exchange
        self.currency = currency
        self.intraday = {
            "Bid": [],
            "Mid": [],
            "Ask": []
        }

    

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
