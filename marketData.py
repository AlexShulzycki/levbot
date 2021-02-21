import requests
import pandas
import json
from talib.abstract import *


def api(url, payload):
    response = requests.get("http://api.binance.com" + url, params=payload)
    df = pandas.DataFrame(json.loads(response.text))

    return df


def getPrices(ticker, interval, limit):
    payload = {"symbol": ticker, "interval": interval, "limit": limit}
    df = api("/api/v3/klines", payload)

    # select relevant columns
    df = df.iloc[:, 0:6]

    # convert to floats
    df = df.apply(pandas.to_numeric)

    # label the columns
    df.columns = ["Time", "Open", "High", "Low", "Close", "Volume"]

    # Set the datetime
    df["Time"] = pandas.to_datetime(df["Time"], unit='ms')
    df.set_index("Time", inplace=True)

    return df


def getOrderBook(ticker, limit):
    payload = {"symbol": ticker, "limit": limit}
    df = api("/api/v3/depth", payload)

    return df


def indicators(df):
    return True
