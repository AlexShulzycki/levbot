import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas


def plotCandles(data):
    mpf.plot(data, type="candle")

def plotSR(dfs, dfr):

    plt.plot(dfs["Price"], dfs["Volume"], color= "green")
    plt.plot(dfr["Price"], dfr["Volume"], color="red")
    plt.show()
