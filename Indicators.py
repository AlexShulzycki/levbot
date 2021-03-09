import pandas
import talib
import numpy as np

#Stochastic needs 8 candles to calculate
def Stochastic (df: pandas.DataFrame):
    slowk, slowd = talib.STOCH(np.array(df['High']),np.array(df["Low"]), np.array(df["Close"]))
    df.insert(len(df.columns), "K", slowk)
    df.insert(len(df.columns), "D", slowd)

    return df

#ADX needs 27 candles to calculate
def ADX (df: pandas.DataFrame):
    ADX = talib.ADX(np.array(df['High']),np.array(df["Low"]), np.array(df["Close"]))
    df.insert(len(df.columns), "ADX", ADX)

    return df
