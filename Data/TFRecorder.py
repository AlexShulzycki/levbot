import os
import tensorflow as tf
import numpy as np
import pandas as pd
import temporian as tp
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



def _float_feature(value):
  """Returns a float_list from a float / double."""
  return tf.train.Feature(float_list=tf.train.FloatList(value=value))

def _int64_feature(value):
  """Returns an int64_list from a bool / enum / int / uint."""
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))

def _bytes_feature(value):
  """Returns an int64_list from a bool / enum / int / uint."""
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))



class coinRecordGenerator:

    minimum_timestamp = 1597132100
    """The minimum time, to cut off noise at the start"""

    def __init__(self, coin: str, datalocation: str = "raw", savelocation: str = "tfrecords", savename ="test.tfrecord"):
        """
        Handles the saving of each coin to tfrecords, DONT COMBINE TIMEFRAMES
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

        self.evset = None

    def addToEvset(self, evset: tp.event_set):
        """
        Adds to the self.evset if it exists, otherwise self.evset = evset. Must have Timeframe as index and a timestamp.
        :param evset: evset to add to the main evset
        :return: nothing :)
        """
        if self.evset is None:
            self.evset = evset
            return

        # Check if features exists already
        for feature in evset.schema.features:
            if feature in self.evset.schema.features:
                self.evset = tp.combine(self.evset, evset)
                return

        # Otherwise, join
        self.evset = self.evset.join(evset)

    def loadData(self, datatype: str, timeframe: str) -> tp.event_set:
        """
        Loads in csv data pertaining to datatype and timeframe
        :param datatype: klines
        :param timeframe: 1m
        :return: eventset
        """

        folder = f"{self.datalocation}{self.coin}/{datatype}/{timeframe}/csv/"
        """CSV file(s) location"""

        evsets = []

        for file in tqdm(os.listdir(folder)):

            # Try to read in the file
            if file.endswith(".csv"):
                df = pd.read_csv(folder + file)
            else:
                continue

            # Label / drop axes depending on datatype
            match datatype:
                case 'klines':
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
        combined = tp.combine(*evsets)
        self.addToEvset(combined)
        return combined

    def engineerFeatures(self):
        # do something to self.evset
        pass

    def save(self):
        """Generate location, save to location"""

        try:
            os.makedirs(f"{self.savelocation}{self.coin}/")
        except OSError:
            pass

        location = f"{self.savelocation}{self.coin}/{self.savename}"

        # Create the schema from our evset
        features = {}

        df = tp.to_pandas(self.evset.after(self.minimum_timestamp)) # After the min time

        # calculate unix datetime for timestamp in seconds
        df["timestamp"] = (df["timestamp"] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

        for column in df:

            # Ignore timeframe, handle edge cases, otherwise it's a float
            match column:
                case "Timeframe":
                    features[column] = _bytes_feature([df[column].tolist()[0].encode()])
                case "timestamp":
                    features[column] = _int64_feature(df[column].tolist())
                case _:
                    features[column] = _float_feature(df[column].tolist())



        example = tf.train.Example(features=tf.train.Features(feature=features))
        serialized = example.SerializeToString()

        writer = tf.io.TFRecordWriter(location)
        writer.write(serialized)
        writer.close()

