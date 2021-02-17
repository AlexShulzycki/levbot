import matplotlib.pyplot as plt
import mplfinance as mpf


def plotCandles(data):
    mpf.plot(data, type="candle")
