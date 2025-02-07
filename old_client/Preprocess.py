import pandas as pd


def prepare(df:pd.DataFrame):
    count = len(df.index)
    data = []
    row = pd.Series([])

    # Reset index for dataframe
    df = df.reset_index()
    latest = df.iloc[49]

    for i in range(0,50):
        data.extend(preprocess(df.iloc[i], latest))

    return data

def preprocess(current:pd.DataFrame, latest: pd.DataFrame):
    data = []
    buffer = None
    # Open
    buffer = current["Open"]/ latest["Open"]
    data.append((1 - buffer) * 10)
    # High
    buffer = current["High"] / latest["High"]
    data.append((1 - buffer) * 10)
    # Low
    buffer = current["Low"] / latest["Low"]
    data.append((1 - buffer) * 10)
    # Close
    buffer = current["Close"] / latest["Close"]
    data.append((1 - buffer) * 10)


    # Volume
    if((current["Volume"] == 0) or (latest["Volume"] == 0)):
        buffer = 0
    else:
        buffer = current["Volume"] / latest["Volume"]

    data.append((1 - buffer) / 10)


    # K
    buffer = current["K"] / latest["K"]
    data.append((buffer-50) / 100)
    # D
    buffer = current["D"] / latest["D"]
    data.append((buffer - 50) / 100)
    # ADX
    buffer = current["ADX"] / latest["ADX"]
    data.append((buffer - 50) / 100)


    return data