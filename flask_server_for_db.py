import flask
from flask import Flask
import pandas as pd
import csv
import json

info_server = Flask("Server")

@info_server.route('/update/<string:tickers>', methods=['GET', 'POST'])





info_server.run(host="127:0.0.1", port=8001, threaded=True)