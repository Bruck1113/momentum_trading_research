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

agri_tickers = ["ALSN", "AXL"]
class HANS123(bt.Strategy):

    params = dict(
        pfast=11,  # period for the fast moving average
        pslow=33,   # period for the slow moving average
        # last_trading_date = datetime.now()
        total_commision = 0,
        num_trade = 0,
        stop_loss = 0.01,
        each_day_high_low = {"High":None, "Low":None, "Trading day":None},
        trade = {"time": [], "amount": []},
        next_called_time = 0,
        detecting_time = 30,
        pos_posted = False
        #甄別時間
    )
    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.rsi_sma = bt.ind.RSI_SMA()
        self.rsi_ema = bt.ind.RSI_EMA()
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal
        # self.dt_time = bt.datas
        self.dataclose = self.datas[0].close
        self.dates = self.datas[0].datetime

        # Add ExpMA, WtgMA, StocSlow, MACD, ATR, RSI indicators for plotting.
        # self.ind1 = bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # self.ind2 = bt.indicators.WeightedMovingAverage(self.datas[0], period=25,subplot = True)
        # self.ind3 = bt.indicators.StochasticSlow(self.datas[0])
        # self.ind4 = bt.indicators.MACDHisto(self.datas[0])
        # self.ind5 = rsi = bt.indicators.RSI(self.datas[0])
        # self.ind6 = bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # self.ind7 = bt.indicators.ATR(self.datas[0], plot = False)

        self.long_pos = None
        self.short_pos = None
        # self.data_short = self.datas[1]

        # self.detecting_time = 60
        #We are giving the strategy 60 bars(i.e. 60 mins to find the high and low

    def next(self):
        curdt = self.datetime[0]  # float
        curdtime = self.datetime.datetime(ago=0)  # 0 is the default
        curdate = self.datetime.date(ago=0)  # 0 is the default
        curtime = self.datetime.time(ago=0)  # 0 is the default ago

        print(self.datas[0].datetime.time(0))
        pos_size = 5
        #Assuming we are doing a trade for 5 shares of one equity per day
        # print([curdt, curdtime, curdate, curtime])
        #Check if the high and low is established or not
        dt1 = self.p.each_day_high_low["Trading day"]
        dt2 = curdtime

        current_datetime = self.datas[0].datetime.datetime(0)

        # Convert the datetime object to a string in the format "hh:mm:ss"
        current_time_string = current_datetime.strftime("%H:%M:%S")

        # Extract the time component of the string
        current_time = current_time_string[:8]

        # # Check if the current time is equal to "16:00:00"
        # if current_time == "16:00:00":
        #     print("Market closed")
        #
        #     if self.long_pos and self.long_pos.completed:
        #         self.close(self.long_pos)
        #     if self.short_pos and self.short_pos.completed:
        #         self.close(self.short_pos)
        #     self.p.pos_posted = False
        # # Do something at 4:00 PM

        if dt1 and (not dt1.day == dt2.day) :
            #We are already at a different day
            print("another day detected")
            self.p.detecting_time = 30
            self.p.pos_posted = False
            #To update the detecting time so that the strategy can update the high and low accordingly

        if self.p.detecting_time > 0:
            print(current_datetime)
            #We need to carry on the detecting process
            if self.params.each_day_high_low["High"] == None or self.data.high[0] > self.params.each_day_high_low["High"]:
                #We have to replace the highest in the day with this bar's high
                self.params.each_day_high_low["High"] = self.data.high[0]
            if self.params.each_day_high_low["Low"] == None or self.data.low[0] < self.params.each_day_high_low["Low"]:
                self.params.each_day_high_low["Low"] = self.data.low[0]

            self.p.each_day_high_low["Trading day"] = current_datetime
            self.p.detecting_time -= 1

        elif not self.p.pos_posted:
            #Ww have already chosen the high and low during the hans time
            #Now we are going to set up the high low position for the intraday trade
            #We do not have position posted in the strategy environment
            print("Create buy and sell order")
            self.long_pos = self.buy(exectype = bt.Order.Limit,
                                     price = self.params.each_day_high_low["High"],
                                     size = pos_size,
                                     valid=datetime.datetime.now() + datetime.timedelta(days=200))

            self.short_pos = self.sell(exectype=bt.Order.Limit,
                                       price = self.params.each_day_high_low["Low"],
                                       size = pos_size,
                                       valid=datetime.datetime.now() + datetime.timedelta(days=200))
            print("High price is " + str(self.params.each_day_high_low["High"]) + " and the low price is " + str(self.params.each_day_high_low["Low"]))
            self.p.pos_posted = True



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


if __name__ == '__main__':
# Create a cerebro entity
    cerebro = bt.Cerebro()
# Add a strategy
#     cerebro.addstrategy(SmaStrategy)
#     strat = rf_agric_strat()
    temp_df = pd.read_csv("data.csv")

    cerebro.addstrategy(HANS123)
    cerebro.addobserver(bt.observers.Broker)
    connection = data_api.API_connection()
    df = connection.backtester_data_usage("intraday", agri_tickers[0], "1min")
    TIME = df["Datetime"]

    endpoints = connection.get_start_and_end_date(df)
    df.to_csv("data.csv")


    # data
    data = btfeeds.GenericCSVData(
            dataname='data.csv',

            fromdate=datetime.datetime.strptime(endpoints[0],  "%Y-%m-%d %H:%M:%S"),
            todate=datetime.datetime.strptime(endpoints[1],  "%Y-%m-%d %H:%M:%S"),
            timeframe=bt.TimeFrame.Minutes,

            nullvalue=0.0,  # missing values to be replaced with 0

            dtformat=("%Y-%m-%d %H:%M:%S"),
            datetime=1,
            open=2,
            high=3,
            low=4,
            close=5,
            volume=6,

    )
    # cerebro.resampledata(data,timeframe=bt.TimeFrame.Minutes)

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
    # strats.p.record["ExponentialMovingAverage"] = strats.ind1.array
    # strats.p.record["WeightedMovingAverage"] = strats.ind2.array
    # strats.p.record["StochasticSlow"] = strats.ind3.array
    # strats.p.record["MACDHisto"] = strats.ind4.array
    # strats.p.record["RSI"] = strats.ind5.array
    # strats.p.record["SmoothedMovingAverage"] = strats.ind6.array
    # strats.p.record["ATR"] = strats.ind7.array
    # strats.p.record["AO"] = strats.ind8.array
    # strats.p.record["WilliamR"] = strats.ind9.array
    #
    # strats.p.record["time"] = TIME[:-1]
    # strats.p.record["value"] = strats.observers.broker.array[:len(strats.p.record["ATR"])]
    # print([len(item) for item in strats.p.record.values()])
    # df = pd.DataFrame(strats.p.record)
    #
    # trade_rec = pd.DataFrame(strats.p.trade)
    # # trade_rec.to_csv("trade_record.csv")
    # df.to_csv("evaluation.csv")

    # new_dict = strats.p.result["Time", "Model signal", "Profit/loss"]
    # # vol_df = pd.DataFrame(strats.p.vol_rec)
    # Signals = []
    # for i in strats.p.result["Time"]:
    #     ind = strats.p.vol_rec["Time"].index(i)
    #     Signals.append(strats.p.vol_rec["Signal"][ind])
    #
    # pnl_rec = pd.DataFrame(strats.p.result)
    # pnl_rec["vol_signal"] = Signals
    # pnl_rec.to_csv("pnl.csv")

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # print('Commision expenses: %.2f' % strats.p.total_commision)
    # print('Number of trades carried out: %.2f' % strats.p.num_trade)
    # print(trade_profit_record(transactions.T.T["value"]))
    # Plot the result
    cerebro.plot(style='candlestick',loc='grey', grid=False, iplot=False)