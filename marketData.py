import requests
import pandas
import json
from talib.abstract import *

def getData(ticker, interval, limit):

    payload = {"symbol": ticker, "interval": interval, "limit":limit}
    response = requests.get("http://api.binance.com/api/v3/klines", params=payload)

    df = pandas.DataFrame(json.loads(response.text))
    # select relevant columns
    df = df.iloc[:,0:6]

    # convert to floats
    df = df.apply(pandas.to_numeric)

    # label the columns
    df.columns = ["Time", "Open", "High", "Low", "Close", "Volume"]

    # Set the datetime
    df["Time"] = pandas.to_datetime(df["Time"], unit='ms')
    df.set_index("Time", inplace=True)


    return df

def indicators(df):
    return True