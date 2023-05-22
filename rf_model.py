import seaborn

import yfinance as yf
import pandas as pd
import openpyxl
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import statsmodels
import seaborn as sns
import scipy
from scipy import stats
from statistics import mean


import statsmodels.tsa.api as tsa
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import acf, q_stat, adfuller
from scipy.stats import probplot, moment
import requests

import graphviz
import pydotplus

import eikon as ek  # the Eikon Python wrapper package
import configparser as cp

import sklearn
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
# Load libraries
from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, ConfusionMatrixDisplay
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from scipy.stats import randint

from sklearn.tree import export_graphviz
from six import StringIO
from IPython.display import Image
import pydotplus

class model:

    def __init__(self, bt_data, price_data):
        self.df = pd.read_csv(bt_data)
        self.df = self.df.dropna()
        self.prices = pd.read_csv(price_data)
        self.prices = self.prices["Close"]
        self.models = []

    def pct_change(self, lst):
        changes = []
        for i in range(len(lst)):
            if i > 0:
                changes.append((lst[i] - lst[i - 1]) / lst[i - 1])
            else:
                changes.append(0)

        df = pd.DataFrame(changes, index=None)
        return df

    def turn_trend_into_bin(self, lst):
        lst = list(lst)
        bin = []
        for i in lst:
            if i > 0:
                bin.append(1)
            else:
                bin.append(-1)

        return bin

    def range_interval(self, lst, high, low):
        # lst = list(lst)
        #To classify the data into three category
        #Inside the channel, higher than the ceiling of the channel, lower than
        ter = []
        for i in lst:
            if i >= high:
                ter.append(1)
            elif i > low:
                ter.append(0)
            else:
                ter.append(-1)

        return ter

    def visualize_tree(self, tree, feature_cols, image_address):
        dot_data = StringIO()
        export_graphviz(tree, out_file=dot_data,
                        filled=True, rounded=True,
                        special_characters=True, feature_names=feature_cols, class_names=None)
        graph = pydotplus.graph_from_dot_data(dot_data.getvalue())
        graph.write_png(image_address)
        Image(graph.create_png())

    def trim_df(self):
        short_window = 3
        long_window = 4

        self.df["Closing price"] = self.prices
        self.df["Short_window"] = self.df["Closing price"].rolling(3).mean
        self.df["Short_window"] = self.df["Closing price"].rolling(3).mean

        self.df["Short_window"] = self.pct_change(list(self.df["Closing price"])).rolling(short_window).mean()
        self.df["Long_window"] = self.pct_change(list(self.df["Closing price"])).rolling(long_window).mean()
        # df["RSI_pct_change"] = pct_change(list(df["RSI"]))

        self.df["RSI_range"] = self.range_interval(self.df["RSI"], 65, 38)
        self.df["WMV_pct_change"] = self.pct_change(list(self.df['WeightedMovingAverage']))

        self.df["Short window bin"] = self.turn_trend_into_bin(self.df["Short_window"])
        self.df["Long window bin"] = self.turn_trend_into_bin(self.df["Long_window"])
        # df["RSI_bin"] = turn_trend_into_bin(df["RSI_pct_change"])
        self.df["WMV_bin"] = self.turn_trend_into_bin(self.df["WMV_pct_change"])

        self.df = self.df.fillna(method="ffill")
        return None

    def random_forest_train(self, features_cols, output_cols):
        using = ["RSI_range", "WMV_bin"]
        X = self.df[features_cols].values  # Features
        y = self.df[output_cols].values  # Target variable

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

        rf =RandomForestClassifier()
        rf.fit(X_train, y_train)

        self.models.append(rf)
        return rf
        # y_pred = rf.predict(X_test)
        # accuracy = accuracy_score(y_test, y_pred)
        # print("Accuracy:", accuracy)