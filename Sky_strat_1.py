import datetime  # For datetime objects
import os.path
from sqlite3 import connect  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
import backtrader.feeds as btfeeds
import data_api
# Also, you can just use this script and paste it into your browsers to grab quick market cvs data from yahoo.
# http://ichart.finance.yahoo.com/table.csv?s=ENTERSTOCKHERE
import quantstats
import yfinance as yf
import pandas_ta as pt

testing_symbols = ["BA", "VWAGY", 'TSLA', 'BABA', 'OXY', 'BTC-USD', 'NQ=F', '^VIX', 'GC=F', 'ETH-USD', 'MMM', 'AAPL', 'NVDA', 'SOFI', 'NIO']
# Create a Stratey

agri_tickers = ["ALSN", "AXL"]
class TestStrategy(bt.Strategy):
    params = (('BBandsperiod', 20),)

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.redline = None
        self.blueline = None

        # Add a BBand indicator
        #self.bband = bt.indicators.BBands(self.datas[0], period=self.params.BBandsperiod)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enougth cash
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        if self.dataclose < self.bband.lines.bot and not self.position:
            self.redline = True

        if self.dataclose > self.bband.lines.top and self.position:
            self.blueline = True

        if self.dataclose > self.bband.lines.mid and not self.position and self.redline:
            # BUY, BUY, BUY!!! (with all possible default parameters)
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            # Keep track of the created order to avoid a 2nd order
            self.order = self.buy()

        if self.dataclose > self.bband.lines.top and not self.position:
            # BUY, BUY, BUY!!! (with all possible default parameters)
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            # Keep track of the created order to avoid a 2nd order
            self.order = self.buy()

        if self.dataclose < self.bband.lines.mid and self.position and self.blueline:
            # SELL, SELL, SELL!!! (with all possible default parameters)
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.blueline = False
            self.redline = False
            # Keep track of the created order to avoid a 2nd order
            self.order = self.sell()

class SmaStrategy(bt.Strategy):
    params = dict(
        pfast=11,  # period for the fast moving average
        pslow=33   # period for the slow moving average
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

    def next(self):
        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.buy()  # enter long

        elif self.crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position

if __name__ == '__main__':
# Create a cerebro entity
    cerebro = bt.Cerebro()

# Add a strategy
    cerebro.addstrategy(SmaStrategy)
connection = data_api.API_connection()
df = connection.backtester_data_usage("daily", agri_tickers[0], "NA")
endpoints = connection.get_start_and_end_date(df)
df.to_csv("data.csv")


# data
data = btfeeds.GenericCSVData(
        dataname='data.csv',

        fromdate=datetime.datetime.strptime(endpoints[0], "%Y-%m-%d"),
        todate=datetime.datetime.strptime(endpoints[1], "%Y-%m-%d"),

        nullvalue=0.0,  # missing values to be replaced with 0

        dtformat=('%Y-%m-%d'),
        datetime=1,
        open=2,
        high=3,
        low=4,
        close=5,
        volume=6,

)


# Add the Data Feed to Cerebro
cerebro.adddata(data)

# Set our desired cash start
cerebro.broker.setcash(10000.0)

# Add a FixedSize sizer according to the stake
cerebro.addsizer(bt.sizers.FixedSize, stake=5)

#Add analyzers
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')


# Set the commission
cerebro.broker.setcommission(commission=0.002)

# Print out the starting conditions
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Run over everything
results = cerebro.run()
strats = results[0]

portfolio_stats = strats.analyzers.getbyname('PyFolio')
returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
returns.index = returns.index.tz_convert(None)
quantstats.reports.html(returns, output='stats.html', title='BTC Sentiment')
# Print out the final result
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Plot the result
cerebro.plot(iplot=False)
