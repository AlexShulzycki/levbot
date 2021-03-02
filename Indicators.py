import pandas
import talib
import numpy as np

def Stochastic (df: pandas.DataFrame):
    slowk, slowd = talib.STOCH(np.array(df['High']),np.array(df["Low"]), np.array(df["Close"]))

    print(slowk)


    df.insert(len(df.columns), "K", pandas.Series(slowk))
    df.insert(len(df.columns), "D", pandas.Series(slowd))

    return df

def ADX (df: pandas.DataFrame):
    ADX = talib.ADX(np.array(df['High']),np.array(df["Low"]), np.array(df["Close"]))

    df.insert(len(df.columns), "ADX", pandas.Series(ADX))

    return df
