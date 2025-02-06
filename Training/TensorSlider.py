import numpy as np
import tensorflow as tf
import numba as nb
from numba.experimental import jitclass


class WindowSlider:

    #TODO Test raise StopIterations
    features:list = ["timestamp", "Open", "High", "Low", "Close", "Volume"]

    inMinutes:dict = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "6h": 60 * 6,
        "12h": 60 * 12,
        "1d": 60 * 24
    }

    def __init__(self, datasets:dict, windowsize:int = 100, lookforward:int = 5, batchsize:int = 1):
        """
        Create a window slider that slides over datasets
        :param windowsize: How "wide" the data is
        :param lookforward: How far forward we should look for
        :param datasets: Dict of datasets, {"5m": dataset, "15m": dataset}
        """
        # Set up variables
        self.windowsize = windowsize
        self.lookforward = lookforward
        self.batchsize = batchsize

        # We need to transform the datasets from a dict into a numpy array we can feed to the speedslider

        sortedtimeframes = sorted(datasets.keys(), key=lambda x: self.inMinutes[x])
        data = []
        """Timeframe, Feature, Entry"""
        # Call iter on each dataset and extract data
        for key in sortedtimeframes:
            data.append(datasets[key].__iter__().__next__())

        # array to fill
        processed = np.zeros((len(data), len(self.features), len(data[0]["timestamp"])), dtype="float32")
        # length of the data is the base timeframe length

        for i, timeframe in enumerate(data):
            for j, key in enumerate(self.features):
                featurelength = len(timeframe[key])
                processed[i, j, 0:featurelength] = timeframe[key].numpy()
                # if the data is shorter than the base timeframe, the rest is padded with zeros.


        # Set up speed slider
        self.speedslider = SpeedSlider(processed, batchsize, windowsize, lookforward)


    def __iter__(self):
        """
        Called when an iteration is started.
        """
        self.speedslider.init_from_zero()
        return self

    def __next__(self):
        """
        Called after iteration started, returns next value
        """
        try:
            return self.speedslider.next()

        except IndexError:
            raise StopIteration


class MultiSlideManager:
    """
    This class handles interleaving and loading/unloading of window sliders
    Makes use of tf.data interleaving
    Randomly slides the window sliders at intervals
    Decides when each window slider is done
    """

    def __init__(self, windowsize, lookforward, coins, timeframes, percent_slice):
        """
        Initialize
        :param windowsize: length of each window
        :param lookforward:
        :param coins:
        :param timeframes:
        :param percent_slice: percent of data you want it to use cointing from start, negative numbers count from end
        """
        pass

    def __iter__(self):
        pass

    def __next__(self):
        pass



spec = [
    ("batchsize", nb.int32),
    ("windowsize", nb.int32),
    ("lookforward", nb.int32),
    ("indexes", nb.int32[:]),
    # indexes where the pointers are
    ("tensors", nb.float32[:,:,:]),
    # data from tfdata, [timeframe, feature, entries]
    ("lookforwardoutput", nb.float32[:,:,:,:]),
    # lookforwardoutput, [batch, current + lookforward, labels]
    ("dataoutput", nb.float32[:,:,:,:]),
    # data output, [batch, timeframe, feature, entries]
    ("deltas", nb.float32[:]),
    # approximate time deltas for each timeframe
    ("currenttimes", nb.int32[:]),
]

# Features are as follows: [timeframe, open, high, low, close, volume]

@jitclass(spec)
class SpeedSlider:
    def __init__(self, tensors, batchsize, windowsize, lookforward):
        self.tensors = tensors
        """Indexed by increasing timeframe, base is at index 0 -> [timeframe, feature, entry]"""
        self.batchsize = batchsize
        self.windowsize = windowsize
        self.lookforward = lookforward
        self.indexes = np.zeros(shape=(tensors.shape[0]), dtype=np.int32)
        """Indexed by increasing timeframe, base is at index 0"""

        # Set up output buffers
        self.lookforwardoutput = np.zeros(shape=(self.batchsize, tensors.shape[0], tensors.shape[1]-1, self.lookforward +1), dtype=np.float32)
        self.dataoutput = np.zeros(shape=(self.batchsize, tensors.shape[0], tensors.shape[1]-1, self.windowsize), dtype=np.float32)
        """ [Batch, timeframe, feature, entry], feature -1 because we dont include the timestamp"""
        # Compute time variables
        self.deltas = np.zeros(shape=(tensors.shape[0]), dtype=np.float32)
        """Approximate delta t between timeframe entries"""
        self.currenttimes = np.zeros(shape=(tensors.shape[0]), dtype=np.int32)
        """Timestamp at the indexes for each timeframe"""

        # Update timestamps
        self.updateCurrentTimestamps()

        # Compute deltas
        for i in range(tensors.shape[0]):
            self.deltas[i] = self.tensors[i,0,1] - self.tensors[i,0,1] # get delta


    def updateCurrentTimestamps(self):
        for i in range(self.currenttimes.shape[0]):
            self.currenttimes[i] = self.tensors[i,0,self.indexes[i]] # get timestamp

    def getLatestTime(self) -> np.float32:

        self.updateCurrentTimestamps()

        latest = 0
        for timestamp in self.currenttimes:
            thislatest = timestamp
            if thislatest > latest:
                latest = thislatest

        return latest

    def stepToPresent(self, timestamp = None):

        if timestamp is None:
            self.updateCurrentTimestamps()
            timestamp = self.currenttimes[0]

        for timeframe, timeframetensor in enumerate(self.tensors):
            while timestamp > timeframetensor[0, self.indexes[timeframe] - self.lookforward]:
                self.indexes[timeframe] += 1

    def init_from_zero(self):
        # Slide all indexes to the minimum window size
        self.indexes[:] = self.windowsize + self.lookforward

        latest = self.getLatestTime()
        self.stepToPresent(latest)

    def fillresponsearrays(self, batchindex):

        # iterate over each timeframe
        for timeframe, timeframetensor in enumerate(self.tensors):
            # We are skipping the timestamp at index 0
            # We are only selecting the window size
            windowstart = self.indexes[timeframe] - self.lookforward - self.windowsize
            windowend = self.indexes[timeframe] - self.lookforward

            # fill data output
            self.dataoutput[batchindex][timeframe] = timeframetensor[1:, windowstart: windowend]

            # fill lookforward
            self.lookforwardoutput[batchindex][timeframe] = timeframetensor[1:, windowend: self.indexes[timeframe]+1]


    def next(self):

        # fill up batches
        for i in range(self.batchsize):

            # Step up
            self.indexes[0] += 1
            self.updateCurrentTimestamps()
            self.stepToPresent(self.currenttimes[0])
            # Fill
            self.fillresponsearrays(i)

        return self.dataoutput, self.lookforwardoutput
