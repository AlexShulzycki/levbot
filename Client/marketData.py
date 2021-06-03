import requests
import pandas
import json


def api(url, payload):
    response = requests.get("http://fapi.binance.com" + url, params=payload)
    df = pandas.DataFrame(json.loads(response.text))

    return df


def getPrices(ticker, interval, limit):
    payload = {"pair": ticker, "interval": interval, "contractType":"PERPETUAL", "limit": limit}
    df = api("/fapi/v1/continuousKlines", payload)

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

def getHistorical(ticker, interval, start, end):
    payload = {"pair": ticker, "startTime": start, "endTime":end, "contractType": "PERPETUAL", "interval": interval}
    df = api("/fapi/v1/continuousKlines", payload)

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
    df = api("/fapi/v1/depth", payload)

    return df


