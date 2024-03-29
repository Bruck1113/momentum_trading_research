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
import pandas as pd
import rf_model
import numpy as np
import stats

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
        pslow=33,   # period for the slow moving average
        # last_trading_date = datetime.now()
        total_commision = 0,
        num_trade = 0,
        stop_loss = 0.01,
        record = {"ExponentialMovingAverage":[],
                  "WeightedMovingAverage":[],
                  "StochasticSlow":[],
                  "MACDHisto":[],
                  "RSI":[],
                  "SmoothedMovingAverage":[],
                  "ATR":[],
                  "time":[],
                  "value":[]
                  },
        trade = {"time": [], "amount": []},
        next_called_time = 0
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.rsi_sma = bt.ind.RSI_SMA()
        self.rsi_ema = bt.ind.RSI_EMA()
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

        # Add ExpMA, WtgMA, StocSlow, MACD, ATR, RSI indicators for plotting.
        self.ind1 = bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        self.ind2 = bt.indicators.WeightedMovingAverage(self.datas[0], period=25,subplot = True)
        self.ind3 = bt.indicators.StochasticSlow(self.datas[0])
        self.ind4 = bt.indicators.MACDHisto(self.datas[0])
        self.ind5 = rsi = bt.indicators.RSI(self.datas[0])
        self.ind6 = bt.indicators.SmoothedMovingAverage(rsi, period=10)
        self.ind7 = bt.indicators.ATR(self.datas[0], plot = False)

    def next(self):
        self.p.next_called_time += 1
        #Current logic: We need to exit the current trade to enter into the next trade
        if self.position.size > 0:
            stop_price = self.data.close[0] * (1.0 - self.p.stop_loss)
            if self.data.close[0] < stop_price:
                #Need to stop loss
                self.sell(exectype=bt.Order.Stop, price=stop_price, size=self.position.size)
                self.p.num_trade += 1
                self.p.trade["amount"].append(-1)
                self.p.trade["time"].append(datetime.datetime.fromtimestamp(self.data.datetime[0]).strftime('%Y-%m-%d %H:%M:%S'))

            elif self.position and self.data.close[0] > self.position.price:
                self.sell(exectype=bt.Order.Limit, price=self.data.close[0], size = self.position.size)
                # self.p.total_commision += self.order.executed.comm
                self.p.num_trade += 1
                self.p.trade["amount"].append(-1)
                self.p.trade["time"].append(datetime.datetime.fromtimestamp(self.data.datetime[0]).strftime('%Y-%m-%d %H:%M:%S'))
            else:
                self.p.trade["amount"].append(0)
                self.p.trade["time"].append(datetime.datetime.fromtimestamp(self.data.datetime[0]).strftime('%Y-%m-%d %H:%M:%S'))

        else:
        # if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.buy(size=10000, exectype=bt.Order.Limit)  # enter long
                self.p.num_trade += 1
                self.p.trade["amount"].append(1)
                self.p.trade["time"].append(datetime.datetime.fromtimestamp(self.data.datetime[0]).strftime('%Y-%m-%d %H:%M:%S'))
            else:
                self.p.trade["amount"].append(0)
                self.p.trade["time"].append(datetime.datetime.fromtimestamp(self.data.datetime[0]).strftime('%Y-%m-%d %H:%M:%S'))

        # #For record
        # self.p.record["ExponentialMovingAverage"].append(bt.indicators.ema.ExponentialMovingAverage)
        # self.p.record["ExponentialMovingAverage"].append(list(bt.indicators.ema.ExponentialMovingAverage)[0])
        # self.p.record["WeightedMovingAverage"].append(list(bt.indicators.wma.WeightedMovingAverage)[0])
        # self.p.record["StochasticSlow"].append(list(bt.indicators.stochastic.StochasticSlow)[0])
        # self.p.record["MACDHisto"].append(list(bt.indicators.macd.MACDHisto)[0])
        # self.p.record["RSI"].append(list(bt.indicators.rsi.RSI)[0])
        # self.p.record["SmoothedMovingAverage"].append(list(bt.indicators.smma.SmoothedMovingAverage)[0])
        # self.p.record["SmoothedMovingAverage"].append(list(bt.indicators.atr.ATR)[0])


    # outputting information
    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))


    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.log(
                    "Executed BUY (Price: %.2f, Value: %.2f, Commission %.2f)" %
                    (order.executed.price, order.executed.value, order.executed.comm))


            else:
                self.log(
                    "Executed SELL (Price: %.2f, Value: %.2f, Commission %.2f)" %
                    (order.executed.price, order.executed.value, order.executed.comm))

            self.p.total_commision += order.executed.comm
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order was canceled/margin/rejected")
        self.order = None
        # elif self.crossover < 0:  # in the market & cross to the downside
        #     self.close()  # close long position

class rf_agric_strat(bt.Strategy):

    params = dict(
        pfast=11,  # period for the fast moving average
        pslow=33,   # period for the slow moving average
        # last_trading_date = datetime.now()
        total_commision = 0,
        num_trade = 0,
        stop_loss = 0.01,
        record = {"ExponentialMovingAverage":[],
                  "WeightedMovingAverage":[],
                  "StochasticSlow":[],
                  "MACDHisto":[],
                  "RSI":[],
                  "SmoothedMovingAverage":[],
                  "ATR":[],
                  "time":[],
                  "value":[],
                  "AO":[],
                  "WilliamR":[],
                  "Vol_signal": [0 for i in range(99)]
                  },
        trade = {"time": [], "amount":[]},
        next_called_time = 0,
        model_output = [],
        result = {"Time":[], "Model signal": [], "Profit/loss": []},
        vol_rec = {"Time":[], "Signal":[]}
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        AwesomeOscillator = bt.indicators.AwesomeOscillator()
        self.rsi_sma = bt.ind.RSI_SMA()
        self.rsi_ema = bt.ind.RSI_EMA()
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal
        self.exit_crossover = bt.ind.CrossOver(sma2, sma1)
        # self.ao_crossover = bt.ind.CrossOver(AwesomeOscillator)
        self.rsi = bt.ind.RSI()

        # Add ExpMA, WtgMA, StocSlow, MACD, ATR, RSI indicators for plotting.
        self.ind1 = bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        self.ind2 = bt.indicators.WeightedMovingAverage(self.datas[0], period=25,subplot = True)
        self.ind3 = bt.indicators.StochasticSlow(self.datas[0])
        self.ind4 = bt.indicators.MACDHisto(self.datas[0])
        self.ind5 = rsi = bt.indicators.RSI(self.datas[0])
        self.ind6 = bt.indicators.SmoothedMovingAverage(rsi, period=10)
        self.ind7 = bt.indicators.ATR(self.datas[0], plot = False)
        self.ind8 = bt.indicators.AwesomeOscillator(self.datas[0])
        self.ind9 = bt.indicators.WilliamsR(self.datas[0])


        self.long_std = bt.indicators.StandardDeviation(self.datas[0], period = 100)
        self.short_std = bt.indicators.StandardDeviation(self.datas[0], period = 10)


        # price_data = pd.read_csv("data.csv")
        self.estimators = [self.ind5, self.ind2]
        self.models = rf_model.model("evaluation.csv", "data.csv")
        # self.models = rf_model.svm_model("evaluation.csv", "data.csv")
        self.models.trim_df()
        # self.rf_model = self.models.random_forest_train(["RSI_range", "WMV_bin"], ["Short window bin"])
        using = ["RSI", "WilliamR"]
        self.svm_model = self.models.svm_model(using, ["Long window bin"])

    def next(self):
        self.p.next_called_time += 1
        #Current logic: We need to exit the current trade to enter into the next trade


        # input = pd.DataFrame({"RSI_range": self.models.range_interval([self.rsi[0]], 65, 38)[0],
        #                       "WNV_bin": self.models.turn_trend_into_bin([self.ind2.array[
        #                                                                   self.ind2.array.index(self.ind2[0])] -
        #                                                                   self.ind2.array[self.ind2.array.index(
        #                                                                   self.ind2[0]) - 1]])[0]}, index=[0])
        input = pd.DataFrame({"RSI": self.rsi[0],
                              "WilliamR": self.ind9[0]}, index = [0])
        model_output = self.svm_model.predict(input)
        self.p.model_output.append(model_output)
        # print("RSI: " + str(self.models.range_interval([self.rsi[0]], 65, 38)[0]) + "WMV_bin: " + str(self.models.turn_trend_into_bin([self.ind2.array[
        #                                                                   self.ind2.array.index(self.ind2[0])] -
        #                                                                   self.ind2.array[self.ind2.array.index(
        #                                                                   self.ind2[0]) - 1]])[0]))

        print("RSI: " +str( self.rsi[0]) + " WilliamR: " + str(self.ind9[0]))
        if model_output == 1:
            print("Model predicted should buy")
        else:
            print("Model predicted should sell")

        #Volitility consideration
        daily_stddev = stats.stdev([self.data.close[0], self.data.open[0], self.data.high[0], self.data.low[0]])
        daily_mean = stats.mean([self.data.close[0], self.data.open[0], self.data.high[0], self.data.low[0]])
        vol_signal = 1
        if self.long_std > self.short_std:
            diff = daily_mean - self.ind2
            if diff/self.long_std < 1 and diff/self.long_std > -1:
                vol_signal = 0
            elif diff/self.long_std < -1:
                vol_signal = -1
        else:
            vol_signal = 0

        self.p.record["Vol_signal"].append(vol_signal)
        self.p.vol_rec["Time"].append(self.datas[0].datetime.date(0))
        self.p.vol_rec["Signal"].append(vol_signal)

        pos_size = int(self.broker.get_cash() * 0.1 / self.data.close[0] / 2)
        if vol_signal == 1:
            pos_size = int(int(self.broker.get_cash() * 0.1 / self.data.close[0] / 2) * 1.1)
        elif vol_signal == -1:
            pos_size = int(int(self.broker.get_cash() * 0.1 / self.data.close[0] / 2) * 0.9)

        model_output = model_output[0]
        if self.position.size != 0:
            pos = self.position.size
            price = self.position.price

            #We define a window to measure the short term volatility
            # vol = np.std(self.self.data.close[])
            if pos > 0:
                # ML job
                #We have long position opening
                stop_price = price * (1.0 - self.p.stop_loss)
                # model_output = model_output[0]

                if self.exit_crossover > 0:
                    #Exit signal need to more confirmed
                    #Exit the long position
                    self.p.result["Time"].append(self.datas[0].datetime.date(0))
                    self.p.result["Model signal"].append(model_output)
                    self.p.result["Profit/loss"].append(self.data.close[0] - price)

                    self.close()


                elif  self.data.close[0] < self.position.price and model_output == 1:
                    # self.sell(exectype=bt.Order.Limit, price=self.data.close[0], size=self.position.size)
                    # self.p.total_commision += self.order.executed.comm
                    self.buy(exectype=bt.Order.Limit, price=self.data.close[0], size=pos_size)
                    # self.p.result["vol signal"].append(vol_signal)

                    # self.sell(exectype=bt.Order.Stop, price=stop_price, size=self.position.size)
                    self.p.num_trade += 1
                    self.p.trade["amount"].append(self.data.close[0])
                    # self.p.trade["long_price"].append(self.data.close[0])
                    self.p.trade["time"].append(
                        self.datas[0].datetime.date(0))
                    # datetime.datetime.fromtimestamp(self.data.datetime[0]).strftime('%Y-%m-%d'))

                elif self.data.close[0] < self.position.price and model_output == -1:

                    self.p.result["Time"].append(self.datas[0].datetime.date(0))
                    self.p.result["Model signal"].append(model_output)
                    self.p.result["Profit/loss"].append(self.data.close[0] - price)
                    self.close()
                    self.p.trade["amount"].append(-self.position.price)
                    # self.p.trade["short_price"].append(self.position.price)
                    self.p.trade["time"].append(
                        self.datas[0].datetime.date(0))

                elif self.data.close[0] < stop_price:
                    # Need to stop loss
                    self.p.result["Time"].append(self.datas[0].datetime.date(0))
                    self.p.result["Model signal"].append(model_output)
                    self.p.result["Profit/loss"].append(self.data.close[0] - price)
                    self.close()
                    self.p.num_trade += 1
                    self.p.trade["amount"].append(-self.position.price)
                    # self.p.trade["short_price"].append(self.position.price)
                    self.p.trade["time"].append(
                        self.datas[0].datetime.date(0))

            else:
                #We have short position opening
                stop_price = price * (1.0 + self.p.stop_loss)


                if self.crossover > 0:
                    self.p.result["Time"].append(self.datas[0].datetime.date(0))
                    self.p.result["Model signal"].append(model_output)
                    self.p.result["Profit/loss"].append(self.data.close[0] - price)
                    self.close()

                elif self.data.close[0] > self.position.price:
                    #If the closing price is higher than the price we entered into the short position
                    if  model_output == -1:
                        # self.sell(exectype=bt.Order.Limit, price=self.data.close[0], size=self.position.size)
                        # self.p.total_commision += self.order.executed.comm
                        # if vol_signal == 1:
                        #     pos_size = int(int(self.broker.get_cash() * 0.1 / self.data.close[0] / 2) * 1.1)
                        # elif vol_signal == -1:
                        #     pos_size = int(int(self.broker.get_cash() * 0.1 / self.data.close[0] / 2) * 0.9)
                        self.sell(exectype=bt.Order.Limit, price=self.data.close[0], size=pos_size)
                        # self.p.result["vol signal"].append(vol_signal)

                        # self.sell(exectype=bt.Order.Stop, price=stop_price, size=self.position.size)
                        self.p.num_trade += 1
                        self.p.trade["amount"].append(-self.data.close[0])
                        # self.p.trade["short_price"].append(self.data.close[0])
                        self.p.trade["time"].append(
                        self.datas[0].datetime.date(0))

                    elif model_output == 1:

                        self.p.result["Time"].append(self.datas[0].datetime.date(0))
                        self.p.result["Model signal"].append(model_output)
                        self.p.result["Profit/loss"].append(self.data.close[0] - price)
                        self.close()
                        self.p.trade["amount"].append(self.position.price)
                        # self.p.trade["long_price"].append(self.position.price)
                        self.p.trade["time"].append(
                            self.datas[0].datetime.date(0))

                elif self.data.close[0] > stop_price:
                    # Need to stop loss

                    self.p.result["Time"].append(self.datas[0].datetime.date(0))
                    self.p.result["Model signal"].append(model_output)
                    self.p.result["Profit/loss"].append(self.data.close[0] - price)
                    self.close()
                    self.p.num_trade += 1
                    # self.p.trade["long_price"].append(self.position.price)
                    self.p.trade["amount"].append(self.position.price)
                    self.p.trade["time"].append(
                        self.datas[0].datetime.date(0))

        else:
            print("there are no opening positions")
            # if not self.position:  # not in the market
            print("Available position size to enter: " + str(int(self.broker.get_cash() * 0.1)))
            if self.crossover > 0 or model_output == 1:  # if fast crosses slow to the upside
                self.buy(size=pos_size * 2, exectype=bt.Order.Limit)  # enter long
                # self.p.result["vol signal"].append(vol_signal)

                self.p.num_trade += 1
                # self.p.trade["long_price"].append(self.position.price)
                self.p.trade["amount"].append(self.position.price)
                self.p.trade["time"].append(
                    self.datas[0].datetime.date(0))

            elif model_output == -1:
                self.sell(size=pos_size * 2, exectype=bt.Order.Limit)  # enter long
                # self.p.result["vol signal"].append(vol_signal)

                self.p.num_trade += 1
                # self.p.trade["short_price"].append(self.position.price)
                self.p.trade["amount"].append(-self.position.price)
                self.p.trade["time"].append(
                    self.datas[0].datetime.date(0))

            else:
                # self.p.result["vol signal"].append(vol_signal)
                self.p.trade["amount"].append(0)
                self.p.trade["time"].append(
                    self.datas[0].datetime.date(0))



    # outputting information
    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))


    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.log(
                    "Executed BUY (Price: %.2f, Value: %.2f, Commission %.2f)" %
                    (order.executed.price, order.executed.value, order.executed.comm))


            else:
                self.log(
                    "Executed SELL (Price: %.2f, Value: %.2f, Commission %.2f)" %
                    (order.executed.price, order.executed.value, order.executed.comm))

            self.p.total_commision += order.executed.comm
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order was canceled/margin/rejected")
        self.order = None
        # elif self.crossover < 0:  # in the market & cross to the downside
        #     self.close()  # close long position



#Helper functions
def trade_profit_record(trade_value:list):
    profit_record = {"win":0, "lose":0}
    for i in range(len(trade_value)):
        if trade_value[i] > 0:
            if trade_value[i] > abs(trade_value[i - 1]):
                profit_record["win"] += 1
            else:
                profit_record["lose"] += 1

    return profit_record


if __name__ == '__main__':
# Create a cerebro entity
    cerebro = bt.Cerebro()
# Add a strategy
#     cerebro.addstrategy(SmaStrategy)
#     strat = rf_agric_strat()
    temp_df = pd.read_csv("data.csv")

    cerebro.addstrategy(rf_agric_strat)
    cerebro.addobserver(bt.observers.Broker)
    connection = data_api.API_connection()
    df = connection.backtester_data_usage("daily", agri_tickers[0], "NA")
    TIME = df["Datetime"]

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
    cerebro.broker.setcash(1000000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=5)
    # cerebro.addindicator()

    #Add analyzers
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(bt.observers.Value)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='time_return')

    # Set the commission
    cerebro.broker.setcommission(commission=0)

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
    strats.p.record["ExponentialMovingAverage"] = strats.ind1.array
    strats.p.record["WeightedMovingAverage"] = strats.ind2.array
    strats.p.record["StochasticSlow"] = strats.ind3.array
    strats.p.record["MACDHisto"] = strats.ind4.array
    strats.p.record["RSI"] = strats.ind5.array
    strats.p.record["SmoothedMovingAverage"] = strats.ind6.array
    strats.p.record["ATR"] = strats.ind7.array
    strats.p.record["AO"] = strats.ind8.array
    strats.p.record["WilliamR"] = strats.ind9.array

    strats.p.record["time"] = TIME[:-1]
    strats.p.record["value"] = strats.observers.broker.array[:len(strats.p.record["ATR"])]
    print([len(item) for item in strats.p.record.values()])
    df = pd.DataFrame(strats.p.record)

    trade_rec = pd.DataFrame(strats.p.trade)
    trade_rec.to_csv("trade_record.csv")
    df.to_csv("evaluation.csv")

    # new_dict = strats.p.result["Time", "Model signal", "Profit/loss"]
    # vol_df = pd.DataFrame(strats.p.vol_rec)
    Signals = []
    for i in strats.p.result["Time"]:
        ind = strats.p.vol_rec["Time"].index(i)
        Signals.append(strats.p.vol_rec["Signal"][ind])

    pnl_rec = pd.DataFrame(strats.p.result)
    pnl_rec["vol_signal"] = Signals
    pnl_rec.to_csv("pnl.csv")

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('Commision expenses: %.2f' % strats.p.total_commision)
    print('Number of trades carried out: %.2f' % strats.p.num_trade)
    print(trade_profit_record(transactions.T.T["value"]))
    # Plot the result
    cerebro.plot(style='candlestick',loc='grey', grid=False, iplot=False)





