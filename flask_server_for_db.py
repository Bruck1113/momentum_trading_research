import sys

sys.path.append("C:\\Users\\tszki\\AppData\\Local\\Programs\\Python\\Python310\\Lib\\site-packages")
import flask
from flask import Flask
import csv
import json
import pandas
import eikon as ek
import requests
import datetime
import numpy as np

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





#http://127.0.0.1:8001/options
info_server.run(host="127.0.0.1", port=8001, threaded=True)