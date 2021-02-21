import marketData
import pandas


def OrderBook(ticker):
    df = marketData.getOrderBook(ticker, 1000)
    # Expand tuples
    dfs = pandas.DataFrame(df["asks"].tolist(), index=df.index)
    dfr = pandas.DataFrame(df["bids"].tolist(), index=df.index)

    # convert to floats
    dfs = dfs.apply(pandas.to_numeric)
    dfr = dfr.apply(pandas.to_numeric)

    dfs.columns = ["Price", "Volume"]
    dfr.columns = ["Price", "Volume"]
    return [dfs, dfr]
