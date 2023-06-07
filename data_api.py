import requests
import pandas as pd
import os
import csv
import matplotlib
import mplfinance as mpf
from matplotlib import pyplot as plt
# from matplotlib.dates import mpl_dates
import datetime
import time
import json
from json.decoder import JSONDecodeError
import numpy as np
from statsmodels.tsa.stattools import coint
import seaborn

from urllib.request import urlopen
from bs4 import BeautifulSoup


class API_connection:
    # 5 requests per minute and 500 per day

    def __init__(self) -> None:
        self.Credentials = {"Stock_API_Key": "FQ4QXSG40SMEWLCB", "Crypto_API_Key": "2Ckxb2FUjt1ml5J90Pl2uo9Bf8r"}
        self.stock_url = ['https://www.alphavantage.co/query?function=', "&symbol=", "&interval=",
                          "&apikey=" + self.Credentials["Stock_API_Key"], "&outputsize=full", "&from_currency=",
                          "&to_currency=", "&from_symbol=", "&to_symbol="]
        self.glassnode_url = 'https://api.glassnode.com/v1/metrics/'
        self.writing_csv_file = ""
        self.own_path = "testing.csv"
        self.Token = ['BTC', 'ETH', 'LTC', 'AAVE', 'ABT', 'AMPL', 'ANT', 'ARMOR', 'BADGER', 'BAL',
                      'BAND', 'BAT', 'BIX', 'BNT', 'BOND', 'BRD', 'BUSD', 'BZRX', 'CELR', 'CHSB',
                      'CND', 'COMP', 'CREAM', 'CRO', 'CRV', 'CVC', 'CVP', 'DAI', 'DDX', 'DENT',
                      'DGX', 'DHT', 'DMG', 'DODO', 'DOUGH', 'DRGN', 'ELF', 'ENG', 'ENJ', 'EURS',
                      'FET', 'FTT', 'FUN', 'GNO', 'GUSD', 'HEGIC', 'HOT', 'HPT', 'HT', 'HUSD',
                      'INDEX', 'KCS', 'LAMB', 'LBA', 'LDO', 'LEO', 'LINK', 'LOOM', 'LRC', 'MANA',
                      'MATIC', 'MCB', 'MCO', 'MFT', 'MIR', 'MKR', 'MLN', 'MTA', 'MTL', 'MX', 'NDX',
                      'NEXO', 'NFTX', 'NMR', 'Nsure', 'OCEAN', 'OKB', 'OMG', 'PAY', 'PERP',
                      'PICKLE', 'PNK', 'PNT', 'POLY', 'POWR', 'PPT', 'QASH', 'QKC', 'QNT', 'RDN',
                      'REN', 'REP', 'RLC', 'ROOK', 'RPL', 'RSR', 'SAI', 'SAN', 'SNT', 'SNX', 'STAKE',
                      'STORJ', 'sUSD', 'SUSHI', 'TEL', 'TOP', 'UBT', 'UMA', 'UNI', 'USDC', 'USDK',
                      'USDP', 'USDT', 'UTK', 'VERI', 'WaBi', 'WAX', 'WBTC', 'WETH', 'wNXM', 'WTC',
                      'YAM', 'YFI', 'ZRX']

    def return_interval(self, interval, type):
        if type == "stock":
            switcher = {
                "weekly": "TIME_SERIES_WEEKLY",
                "daily": "TIME_SERIES_DAILY_ADJUSTED",
                "intraday": "TIME_SERIES_INTRADAY",
                "monthly": "TIME_SERIES_MONTHLY",
            }
        else:
            switcher = {
                "weekly": "FX_WEEKLY",
                "daily": "FX_DAILY",
                "intraday": "FX_INTRADAY",
                "monthly": "FX_MONTHLY",
            }
        return switcher.get(interval, "NA")

    def transferring_normal_datetime_into_unix(self, date):
        day_list = date.split('-')
        unix_time = str(int(datetime.datetime(int(day_list[0]), int(day_list[1]), int(day_list[2]), 0, 0).timestamp()))
        return unix_time

    def transferring_unix_into_datetime(self, unix):
        return datetime.datetime.fromtimestamp(int(unix)).strftime('%Y-%m-%d %H:%M:%S')

    # OHLC data is imported
    def get_stock_data(self, function, symbol, interval, datatype, own_path) -> pd.DataFrame:
        json_dict = {"weekly": "Weekly Time Series",
                     "daily": "Time Series (Daily)",
                     "1min": "Time Series (1min)",
                     "5min": "Time Series (5min)",
                     "15min": "Time Series (15min)",
                     "30min": "Time Series (30min)",
                     "60min": "Time Series (60min)",
                     "monthly": "Monthly Time Series",
                     }
        intv = self.return_interval(function, "stock")
        print(intv)
        url = self.stock_url[0] + intv + self.stock_url[1] + symbol
        if (function == "Intraday"):
            url = url + self.stock_url[2] + interval
        print(url)
        r = requests.get(url)
        try:
            r_json = json.loads(r.text)
        except (JSONDecodeError):  # no result returned
            pass

        try:
            if (function == "intraday"):
                function = interval
            r_price_series = r_json[json_dict[function]]
            # Need to address different returning dictionary regarding different returning data
        except (KeyError):
            # print(r_json)
            pass

        price_list = []
        for items in r_price_series.values():
            # print(items)
            price_list.append(float(items['4. close']))
        df_internal = pd.DataFrame(price_list, index=r_price_series.keys())
        # print(df_internal)
        return df_internal

    def backtester_data_usage(self, function, symbol, interval) -> pd.DataFrame:
        json_dict = {"weekly": "Weekly Time Series",
                     "daily": "Time Series (Daily)",
                     "1min": "Time Series (1min)",
                     "5min": "Time Series (5min)",
                     "15min": "Time Series (15min)",
                     "30min": "Time Series (30min)",
                     "60min": "Time Series (60min)",
                     "monthly": "Monthly Time Series",
                     }
        intv = self.return_interval(function, "stock")
        print(intv)
        url = self.stock_url[0] + intv + self.stock_url[1] + symbol
        if (function == "intraday"):
            url = url + self.stock_url[2] + interval
        url = url + "&outputsize=full" + self.stock_url[3]

        print(url)
        r = requests.get(url)
        try:
            r_json = json.loads(r.text)
        except (JSONDecodeError):  # no result returned
            pass

        try:
            if (function == "intraday"):
                function = interval
            r_price_series = r_json[json_dict[function]]
            # Need to address different returning dictionary regarding different returning data
        except (KeyError):
            # print(r_json)
            pass

        df_internal = pd.DataFrame()
        Open_list = ['Open']
        High_list = ['High']
        Low_list = ['Low']
        Close_list = ['Close']
        volume_list = ['Volume']
        date = ["Datetime"]
        days = [key for key in r_price_series]
        days.reverse()
        for key in days:
            date.append(key)

        data = [key for key in r_price_series.values()]
        data.reverse()
        for items in data:
            # print(items)
            Open_list.append(float(items['1. open']))
            High_list.append(float(items['2. high']))
            Low_list.append(float(items['3. low']))
            Close_list.append(float(items['4. close']))
            volume_list.append(float(items['5. volume']))

        list = [date, Open_list, High_list, Low_list, Close_list, volume_list]
        for items in list:
            df_internal[items[0]] = items[1:]
        # print(df_internal)
        # df_internal = df_internal[::-1]
        return df_internal

    def df_to_csv(self, df, filename) -> None:
        df.to_csv(filename)

    def get_real_time_currency_exchange_rate(self, from_currency, to_currency) -> pd.DataFrame:
        url = self.stock_url[0] + "CURRENCY_EXCHANGE_RATE" + self.stock_url[5] + from_currency + self.stock_url[
            6] + to_currency
        r = requests.get(url)
        data = r.json()
        df = pd.DataFrame(data)
        return df

    def get_periodic_currency_exchange_rate(self, from_currency, to_currency, interval) -> pd.DataFrame:
        intv = self.return_interval(interval, "FX")
        url = self.stock_url[0] + intv + self.stock_url[7] + from_currency + self.stock_url[8] + to_currency
        r = requests.get(url)
        data = r.json()
        df = pd.DataFrame(data)
        return df

    def candle_stick_chart_generation(data) -> None:
        df = pd.read_csv(data, parse_dates=True)
        df.index = pd.to_datetime(df['timestamp'])
        ohlc = df.loc[:, ['timestamp', 'open', 'high', 'low', 'close']]
        ohlc['timestamp'] = pd.to_datetime(ohlc['timestamp'])
        mpf.plot(ohlc, type="candle")
        plt.show()

    def get_crypto_market_metrics(self, type, data, since, until, freq, format, timestamp) -> pd.DataFrame:
        #    , since, until, freq, format, timestamp
        local_params = {"a": data, 's': since, 'u': until, 'i': freq, 'f': format, 'timestamp_format': timestamp,
                        "api_key": self.Credentials["Crypto_API_Key"]}
        url = self.glassnode_url + "market/" + type
        print("url = " + url)

        df = pd.DataFrame()
        if data not in self.Token:
            print("This token is not available in glassnode api, plz seek for help")
            return df

        if type == "price_usd_close":
            # print("Hit")
            r = requests.get(url, params={'a': data, 'api_key': self.Credentials['Crypto_API_Key']})
        elif type == "price_usd_ohlc":
            r = requests.get(url, params={'a': data, 's': since, 'u': until, 'i': freq,
                                          'api_key': self.Credentials['Crypto_API_Key']})
        # print(r.text)
        r_json = json.loads(r.text)
        print(r_json)
        length = len(r_json)
        open = []
        high = []
        low = []
        close = []
        date = []
        for i in range(length):
            open.append(float(r_json[i]['o']['o']))
            high.append(float(r_json[i]['o']['h']))
            low.append(float(r_json[i]['o']['l']))
            close.append(float(r_json[i]['o']['c']))
            date.append(self.transferring_unix_into_datetime(int(r_json[i]['t'])))

        df["Date"] = date
        df['Open'] = open
        df['high'] = high
        df['low'] = low
        df['close'] = close

        return df
        # if the requested datatype is csv
        # return df

    def transferring_normal_datetime_into_unix(date):
        day_list = date.split('-')
        unix_time = str(int(datetime.datetime(int(day_list[0]), int(day_list[1]), int(day_list[2]), 0, 0).timestamp()))
        return unix_time

    def check_symbol_exists(self, symbol):
        # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
        # url = 'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=tesco&apikey=demo'
        url = self.stock_url[0] + "SYMBOL_SEARCH&keywords=tesco&apikey=demo"
        r = requests.get(url)
        data = r.json()
        print(data)

    def get_datalist_in_csv(self, function, symbol, interval) -> pd.DataFrame:
        df = pd.DataFrame()
        for i in symbol:
            url = self.stock_url[0] + function + self.stock_url[1] + i + self.stock_url[3]
            print(url)
            r = requests.get(url, stream=True)
            try:
                r_json = json.loads(r.text)
            except (JSONDecodeError):  # no result returned
                continue

            # print(r_json)
            # break
            try:
                r_price_series = r_json["Weekly Time Series"]
            except (KeyError):
                print(r_json)
            # print(r_csv)
            price_list = []
            for items in r_price_series.values():
                # print(items)
                price_list.append(float(items['4. close']))
            df_internal = pd.DataFrame(price_list, index=r_price_series.keys())
            # print(df_internal)
            df[i] = df_internal
            df.dropna(inplace=True)
            df = df[::-1]
        return df

    # def get_data_in_list(self, function, symbol, interval, own_path)->pd.DataFrame:
    #     df = pd.DataFrame()
    #     for i in symbol:
    #         #print("Running data extraction for" + i)
    #         df_internal = self.get_stock_data(function, i, interval, "JSON", "NA")
    #         #print(df_internal)
    #         df[i] = df_internal
    #         df.dropna(inplace=True)
    #         df = df[::-1]
    #         #print("RAN")
    #     return df

    def get_data_in_list(self, function, symbol, interval) -> pd.DataFrame:
        df = pd.DataFrame()
        for i in symbol:
            print("Running data extraction for" + i)
            df_internal = self.get_stock_data(function, i, interval, "JSON", "NA")
            print(df_internal)
            # For 2 or more rows
            print(i)
            if (i != symbol[0]):
                df[i] = df_internal
            else:
                df = df_internal.copy()
                df.dropna(inplace=True)
            df = df[::-1]
            print("RAN")
        return df

    def get_economic_indicator(self, function, interval) -> pd.DataFrame:
        url = self.stock_url[0] + function + self.stock_url[2] + interval + self.stock_url[3]
        r = requests.get(url, stream=True)
        try:
            r_json = json.loads(r.text)
        except (JSONDecodeError):  # no result returned
            pass
        price_list = []
        date_list = []
        for items in r_json['data']:
            date_list.append(items['date'])
            price_list.append(float(items['value']))
        df = pd.DataFrame(price_list, index=date_list)
        df.dropna(inplace=True)
        df = df[::-1]
        return df

    def find_cointegrated_pairs(self, data) -> pd.DataFrame:
        n = data.shape[1]
        print("n=" + str(n))
        score_matrix = np.zeros((n, n))
        pvalue_matrix = np.ones((n, n))
        # create two matrix by initiating two 2d array
        keys = data.keys()
        print(keys)
        # return the column name
        pairs = []
        for i in range(n):  # To pick one of the securities
            for j in range(i + 1, n):  # To pick the securities after the pre-chosen security
                print("i= " + str(i) + ", j= " + str(j))
                S1 = data[keys[i]]
                S2 = data[keys[j]]
                result = coint(S1, S2)  # S1. S2 are array-like
                # coint() is a function in statsmodel which is for testing no_cointegration of a univariate equation
                # FYI, https://www.statsmodels.org/dev/generated/statsmodels.tsa.stattools.coint.html
                score = result[0]
                pvalue = result[1]
                score_matrix[i, j] = score
                pvalue_matrix[i, j] = pvalue
                if pvalue < 0.02:
                    pairs.append((keys[i], keys[j]))
        return score_matrix, pvalue_matrix, pairs

    def trade(self, S1, S2, window1, window2):

        # If window length is 0, algorithm doesn't make sense, so exit
        window1 = int(window1)
        window2 = int(window2)
        if (window1 == 0) or (window2 == 0):
            return 0

        # Compute rolling mean and rolling standard deviation
        ratios = S1 / S2
        ma1 = ratios.rolling(window=window1,
                             center=False).mean()
        ma2 = ratios.rolling(window=window2,
                             center=False).mean()
        std = ratios.rolling(window=window2,
                             center=False).std()
        zscore = (ma1 - ma2) / std

        # Simulate trading
        # Start with no money and no positions
        money = 0
        countS1 = 0
        countS2 = 0
        for i in range(len(ratios)):
            # Sell short if the z-score is > 1
            if zscore[i] > 1:
                money += S1[i] - S2[i] * ratios[i]
                countS1 -= 1
                countS2 += ratios[i]
                print('Selling Ratio %s %s %s %s' % (money, ratios[i], countS1, countS2))
            # Buy long if the z-score is < 1
            elif zscore[i] < -1:
                money -= S1[i] - S2[i] * ratios[i]
                countS1 += 1
                countS2 -= ratios[i]
                print('Buying Ratio %s %s %s %s' % (money, ratios[i], countS1, countS2))
            # Clear positions if the z-score between -.5 and .5
            elif abs(zscore[i]) < 0.75:
                money += S1[i] * countS1 + S2[i] * countS2
                countS1 = 0
                countS2 = 0
                print('Exit pos %s %s %s %s' % (money, ratios[i], countS1, countS2))

        return money

    def pair_trading_analysis(self, equities, function, interval) -> None:
        df = self.get_data_in_list(function=function, symbol=equities, interval=interval,
                                   own_path="NA")  # get data in list
        # Please change the file_path here if u want to specify a place to store the data
        df_coin = self.find_cointegrated_pairs(df)
        scores, pvalues, pairs = df_coin

        # The first printing result:The correlation heatmap
        seaborn.heatmap(pvalues, xticklabels=equities,
                        yticklabels=equities, cmap='RdYlGn_r',
                        mask=(pvalues >= 0.98))
        plt.show()

        while (True):
            # Will need to use two of the them to do the training dataset
            first_equity = input("Please enter the first equity u wanna check?")
            second_equity = input("Please enter the second equity u wanna check?")
            if first_equity == "NA" or second_equity == "NA":
                break
            ratios = df[first_equity][::-1] / df[second_equity][::-1]
            train_ratio = int(len(ratios) * 0.7)
            train = ratios[:train_ratio]
            test = ratios[train_ratio:]

            # Displaying MA ratio of the two equities
            short_window = input("Please enter the duration of short window")
            long_window = input("Please enter the duration of long window")
            ratios_mavg_short = train.rolling(window=int(short_window),
                                              center=False).mean()
            # The moving average of closing price in a month
            ratios_mavg_long = train.rolling(window=int(long_window),
                                             center=False).mean()
            # The moving average of closing price in 3 months
            std_12 = train.rolling(window=48,
                                   center=False).std()
            # For weekly, there are 48 weeks
            zscore_60_5 = (ratios_mavg_short - ratios_mavg_long) / std_12
            plt.figure(figsize=(15, 7))
            plt.plot(train.index, train.values)
            plt.plot(ratios_mavg_short.index, ratios_mavg_short.values)
            plt.plot(ratios_mavg_long.index, ratios_mavg_long.values)
            plt.legend(['Ratio', '1 month Ratio MA', '3 month Ratio MA'])
            plt.ylabel('Ratio')
            plt.show()

            # To show the zscore of the two equities
            plt.figure(figsize=(15, 7))
            zscore_60_5.plot()
            plt.axhline(0, color='black')
            plt.axhline(1.0, color='red', linestyle='--')
            plt.axhline(-1.0, color='green', linestyle='--')
            plt.legend(['Rolling Ratio z-Score', 'Mean', '+1', '-1'])
            plt.show()

            # Showing the position of buy and sell signal at different dates
            plt.figure(figsize=(15, 7))
            train[60:].plot()
            buy = train.copy()
            sell = train.copy()
            buy[zscore_60_5 > -1] = 0
            sell[zscore_60_5 < 1] = 0
            buy[60:].plot(color='g', linestyle='None', marker='^')
            sell[60:].plot(color='r', linestyle='None', marker='^')
            x1, x2, y1, y2 = plt.axis()
            plt.axis((x1, x2, ratios.min(), ratios.max()))
            plt.legend(['Ratio', 'Buy Signal', 'Sell Signal'])
            plt.show()

            # Plot the prices and buy and sell signals from z score
            plt.figure(figsize=(18, 9))
            S1 = df[first_equity][::-1].iloc[:train_ratio]  # Plot the prices and buy and sell signals from z score
            S2 = df[second_equity][::-1].iloc[:train_ratio]

            S1[60:].plot(color='b')
            S2[60:].plot(color='c')
            buyR = 0 * S1.copy()
            sellR = 0 * S1.copy()
            # When buying the ratio, buy S1 and sell S2
            buyR[buy != 0] = S1[buy != 0]
            sellR[buy != 0] = S2[buy != 0]
            # When selling the ratio, sell S1 and buy S2
            buyR[sell != 0] = S2[sell != 0]
            sellR[sell != 0] = S1[sell != 0]
            buyR[60:].plot(color='g', linestyle='None', marker='^')
            sellR[60:].plot(color='r', linestyle='None', marker='^')
            x1, x2, y1, y2 = plt.axis()
            plt.axis((x1, x2, min(S1.min(), S2.min()), max(S1.max(), S2.max())))
            plt.legend([first_equity, second_equity, 'Buy Signal', 'Sell Signal'])
            plt.show()

            # Applying the data into trades
            money = self.trade(df[first_equity][::-1].iloc[:train_ratio], df[second_equity][::-1].iloc[:train_ratio],
                               short_window, long_window)

            print("""The result cash in the account will be: """ + str(money)
                  + """ The long frequency: """ + str(buy[zscore_60_5 > -1].count())
                  + """ The short frequency: """ + str(sell[zscore_60_5 < 1].count())
                  + """ Sharpe ratio: """)

        return None

    def get_start_and_end_date(self, df):
        return [str(df["Datetime"][0]), str(df["Datetime"][len(df["Datetime"]) - 1])]

    def Chin_commo_data(self, website):
        html = urlopen(website)
        bs = BeautifulSoup(html, "html.parser")
        # print(bs.prettify())  # print the parsed data of html

        # for link in bs.find_all("a"):
        #     print("Inner Text: {}".format(link.text))
        #     print("Title: {}".format(link.get("title")))
        #     print("href: {}".format(link.get("href")))

        gdp_table = bs.find_all("div")
        gdp_table_data = gdp_table.tbody.find_all("tr")  # contains 2 rows

        # Get all the headings of Lists
        headings = []
        for td in gdp_table_data[0].find_all("td"):
            # remove any newlines and extra spaces from left and right
            headings.append(td.b.text.replace('\n', ' ').strip())

        print(headings)

def main():
    conn = API_connection()
    time.sleep(10)