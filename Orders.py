import marketData
import pandas


def OrderBook(ticker):
    df = marketData.getOrderBook(ticker, 1000)
    # Expand tuples
    dfb = pandas.DataFrame(df["asks"].tolist(), index=df.index)
    dfa = pandas.DataFrame(df["bids"].tolist(), index=df.index)

    # convert to floats
    dfb = dfb.apply(pandas.to_numeric)
    dfa = dfa.apply(pandas.to_numeric)

    dfb.columns = ["Price", "Volume"]
    dfa.columns = ["Price", "Volume"]
    return [dfb, dfa]


#TODO squash function
def Squash(df: pandas.DataFrame, group: int):
    newFrame = pandas.DataFrame()





