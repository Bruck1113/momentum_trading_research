import sys


sys.path.append("C:\\Users\\tszki\\AppData\\Local\\Programs\\Python\\Python310\\Lib\\site-packages")


import csv
import json
import pandas
import eikon as ek
import requests
import datetime
import numpy as np
import streamlit as st

x = st.slider("Select a value")
st.write(x, "squared is", x * x)

