import os
import tensorflow as tf
import numpy as np
import pandas as pd
import temporian as tp
from h5py._hl import datatype
from tqdm.auto import tqdm


def labelKlines(df: pd.DataFrame)-> tp.event_set:
    """
    kline processing
    """
    # Close time is the timestamp

    df = df.set_axis(
        ['Open time', "Open", "High", "Low", "Close", "Volume", "timestamp", "Quote asset volume",
         "Number of trades", "Taker buy asset volume", "Taker buy quote asset volume", "Ignore"], axis=1)
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.drop("Ignore", axis=1, inplace=True)
    df.drop("Open time", axis=1, inplace=True)

    return df


class coinRecordGenerator:
    def __init__(self, coin: str, datalocation: str = "Data/raw", savelocation: str = "Data/tfrecords", savename ="test"):
        """
        Handles the saving of each coin to tfrecords
        """
        self.coin = coin
        self.datalocation = datalocation
        self.savelocation = savelocation
        self.savename = savename

        # make sure the data locations have a final slash
        if self.datalocation[-1] != '/':
            self.datalocation += "/"
        if self.savelocation[-1] != '/':
            self.savelocation += "/"
        if self.savename[-1] != '/':
            self.savename += "/"

        self.evset = tp.event_set()

    def loadData(self, datatype: str, timeframe: str) -> tp.event_set:
        """
        Loads in csv data pertaining to datatype and timeframe
        :param datatype: klines
        :param timeframe: 1m
        :return: eventset
        """

        folder = f"{self.datalocation}{self.coin}/{datatype}/{timeframe}/"
        """CSV file(s) location"""

        evsets = []

        for file in tqdm(os.listdir(folder+"csv")):

            # Try to read in the file
            if file.endswith(".csv"):
                df = pd.read_csv(folder + file)
            else:
                continue

            # Label / drop axes depending on datatype
            match datatype:
                case 'kline':
                    df = labelKlines(df)
                case _:
                    raise Exception("UNKNOWN DATATYPE "+datatype)

            # Create a timeframe index to indicate which timeframe we are working with
            df["Timeframe"] = timeframe
            # Cast string to bytes so we are not operating with objects
            df["Timeframe"] = df["Timeframe"].astype(np.bytes_)

            # Append the file's eventset, remember to set the index
            evsets.append(tp.from_pandas(df, timestamps="timestamp", indexes=["Timeframe"]))

        # Return combined event set
        evset = tp.combine(*evsets)

    def engineerFeatures(self):
        # do something to self.evset
        pass

    def save(self):
        # Generate location, save with inbuilt function
        location = f"{self.savelocation}{self.coin}/{self.savename}"
        tp.to_tensorflow_record(self.evset, location)



class FeatureEngineer:
    """Engineers features for a given evset"""

    def __init__(self, evset: tp.event_set):
        self.evset = evset

    def addKlineFeatures(self):
        pass



