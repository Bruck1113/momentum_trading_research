import sys

sys.path.append("C:\\Users\\tszki\\AppData\\Local\\Programs\\Python\\Python310\\Lib\\site-packages")
import flask
from flask import Flask
import csv
import json
import pandas
import eikon as ek
import requests
import cx_Oracle
import pandas as pd
import datetime
import numpy as np
from data_crypto_metrics import reorganize_dataframe, compute_put_call_ratio

#c:\users\tszki\appdata\local\programs\python\python310\lib\site-packages
#We will use exchangerate.bot for the development of this tool
ek.set_app_key("b759357753f743e4b5c903da93b36640f32a4b32")

url = 'https://api.exchangerate.host/latest'
info_server = Flask("Server")
polygon_api_key = "yYLfEl900QtmLANvVP7nNC8zk_V20ZYb"
polygon_api_url = "https://api.polygon.io/v2"


@info_server.route('/update/<string:tickers>', methods=['GET', 'POST'])
def update_tickers(tickers):


    return None

@info_server.route('/FX', methods=['GET', 'POST'])
def update_fx_tri_arb():

    symbols=["AUD", "JPY", "CNY", "EUR", "GBP", "KRW", "INR", "TWD", "USD"]

    #Create a matrix of 2-D array by np
    store = {}
    prim_curr = "USD"
    output_curr = "GBP"

    for sym in symbols:
        url = 'https://api.exchangerate.host/latest?'
        base_curr = sym
        url = url + "base=" + base_curr + "&symbols="
        for i in symbols:
            if i != "USD":
                url = url + i + ","
            else:
                url = url + i

        print(url)
        response = requests.get(url)
        data = response.json()

        rates = data["rates"]
        store[sym] = rates


    print(store)
    new_rate = {}

    for i in store[prim_curr].keys():
        if i != prim_curr:
            for k in store[i].keys():
                #The rates here are the rates that are converted to 
                new_rate[i + "-" + k] = (store[prim_curr][i] * store[i][k])/store[prim_curr][k]

    return new_rate

@info_server.route('/correlation_table/<string:tickers_chain>', methods=['GET', 'POST'])
def update_corr_table(tickers_chain):
    #I expect that this can be used as a table to check correlation
    return None

@info_server.route('/company_financial data/<string:company_name>', methods=['GET', 'POST'])
def fin_result_feed(compay_name):
    return None

@info_server.route('/options', methods=['GET', 'POST'])
def options_feed():
    #trial
    ticker = '1200.HK'
    fields = ['PUTCALLIND', 'STRIKE_PRC', 'CF_CLOSE', 'IMP_VOLT']

    result = ek.get_data(ticker, fields=fields)[0]
    print(result)

    result = result.to_json()
    return result

def option_payoff_chart(strike_price, type, premium):
    price_series = [0, strike_price, strike_price * 2]
    if type == "call":
        for i in range(len(price_series)):
            if i < strike_price:
                price_series[i] = i - premium
            else:
                price_series[i] = strike_price - premium


@info_server.route('/collect', methods=['GET', 'POST'])
def daily_data_collection():
    # Set the database connection credentials
    username = 'USERNAME'
    password = 'PASSWORD'
    database = 'DATABASE_NAME'
    host = 'DATABASE_HOST'
    port = 1521
    service_name = 'SERVICE_NAME'

    # Create a connection to the database
    dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
    connection = cx_Oracle.connect(username, password, dsn)

    # Define the table name and the DataFrame to be inserted
    table_name = 'TABLE_NAME'
    data = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['John', 'Jane', 'Bob'],
        'age': [30, 25, 40]
    })

    # Create a cursor object to execute SQL statements
    cursor = connection.cursor()

    # Create a SQL INSERT statement with placeholders for the DataFrame columns
    sql = f"INSERT INTO {table_name} ({', '.join(data.columns)}) VALUES ({', '.join([':' + str(i + 1) for i in range(len(data.columns))])})"

    # Loop through the DataFrame rows and execute the INSERT statement for each row
    for row in data.itertuples(index=False):
        cursor.execute(sql, row)

    # Commit the changes to the database
    connection.commit()

    # Close the database connection
    connection.close()





#http://127.0.0.1:8001/options
info_server.run(host="127.0.0.1", port=8001, threaded=True)