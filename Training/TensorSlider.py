import numpy as np
import tensorflow as tf

class WindowSlider:

    #TODO Test raise StopIterations

    features = ("Open", "High", "Low", "Close", "Volume")

    inMinutes = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "6h": 60 * 6,
        "12h": 60 * 12,
        "1d": 60 * 24
    }

    def __init__(self, datasets:dict, windowsize = 100, lookforward = 5, batchsize = 1):
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

        # pop the lowest timeframe (base timeframe)
        self.base = datasets.pop(sorted(datasets.keys(), key=lambda x: self.inMinutes[x])[0])
        """base timeframe dataset"""
        self.baseTensor = None
        """base Tensor dict"""
        self.others = datasets
        """TODO dict of datasets"""
        self.otherTensors = {}
        """Tensor dict of what the datasets contain"""


        # The +1 is handled by the fact that the index is 1 less than the total amount
        self.baseindex = self.windowsize + self.lookforward
        """Index where the most forward portion of the buffer is"""

        self.otherindexes = {}
        """Dict of indexes where the most forward portion of the buffer is"""

        self.returndatanumpy = np.zeros((self.batchsize, 1 + len(self.others), len(self.features),  self.windowsize))
        """Array for data return values, timeframe, feature, window"""
        self.returnlookaheadnumpy = np.zeros((self.batchsize,self.lookforward+1, len(self.features)))
        """Array for lookahead return values, lookforward + current, features"""

    def stepToPresent(self, timestamp = None):
        """
        Slides forward timeframes to the timestamp of the base timeframe
        :param timestamp: timestamp to slide to, if none then current time of base timeframe
        :return:
        """
        # Set current time
        if timestamp is None:
            ct = self.baseTensor["timestamp"][self.baseindex - self.lookforward]
        else:
            ct = timestamp
            while ct > self.baseTensor["timestamp"][self.baseindex - self.lookforward]:
                # We are not there yet, increase the index
                self.baseindex += 1

        for key, tensor in self.otherTensors.items():
            # Check whether margin is before the current time
            while ct > tensor["timestamp"][self.otherindexes[key]]:
                # We are not there yet, increase the index
                self.otherindexes[key] += 1

    def moveToTime(self, timestamp: int):
        """
        Move all pointers to the specified time

        :param timestamp: timestamp to move to
        """

        for key, index in self.otherindexes.items():
            # get current time at pointer
            ct = self.otherTensors[key]["timestamp"][index]
            # compute delta
            dt = ct - timestamp
            # estimate delta then call steptopresent

    def getLatestTime(self):
        """
        Returns the latest timestamp of the other timeframes
        """
        # get current time as given by the base timeframe
        time = self.baseTensor["timestamp"][self.baseindex - self.lookforward]

        for key, index in self.otherindexes.items():
            latest = self.otherTensors[key]["timestamp"][index]
            if latest > time:
                time = latest

        return time

    def getFeaturesAtKey(self, key):
        pass


    def init_from_zero(self):
        """
        Initializes the window slider from beginning
        """

        # Call iter on each dataset
        self.baseTensor = self.base.__iter__().__next__()
        for key, dataset in self.others.items():
            self.otherTensors[key] = dataset.__iter__().__next__()

        # Reset indexes
        # The +1 is handled by the fact that the index is 1 less than the total amount
        self.baseindex = self.windowsize + self.lookforward

        for key, dataset in self.others.items():
            self.otherindexes[key] = self.windowsize

        # Get latest time and step everyone to it
        latest = self.getLatestTime()
        self.stepToPresent(latest)

        return self

    def fillresponsearrays(self):
        """
        Fills the response numpy arrays with data
        TODO test batch functionality
        """

        for bindex in range(self.batchsize):
            # Fill in with base timeframe
            for j, feature in enumerate(self.features):
                # Get the indexes
                start = self.baseindex - self.windowsize -self.lookforward + bindex
                end = self.baseindex - self.lookforward + bindex
                # Assign the values
                self.returndatanumpy[bindex][0][j] = self.baseTensor[feature][start:end]

            # Timeframe
            for i, (key, tensor) in enumerate(self.otherTensors.items()):
                # Feature
                for j, feature in enumerate(self.features):
                    # Get the indexes
                    start = self.otherindexes[key] - self.windowsize + bindex
                    end = self.otherindexes[key] + bindex
                    # Assign the values
                    self.returndatanumpy[bindex][i+1][j] = tensor[feature][start:end] # plus 1 since 0 is the base timeframe

            # Fill up future price response array (base timeframe only)
            for i, feature in enumerate(self.features):
                start = self.baseindex - self.lookforward + bindex
                end = self.baseindex + 1 + bindex
                self.returnlookaheadnumpy[bindex][:,i] = self.baseTensor[feature][start:end]

    def slideTo(self, timestamp: int):
        """
        Slides the window to the given timestamp
        :param timestamp: unix time to slide to (in seconds)
        """

        currenttime = self.baseTensor["timestamp"][self.baseindex - self.lookforward]
        """Current timestamp as is pointed to by the base timeframe"""
        delta = timestamp - currenttime
        """By how much we need to move"""

        # Calculate step deltas for each timeframe to speed up moving

        pass

    def __iter__(self):
        return self.init_from_zero()

    def __next__(self):

        try:

            # Synchronize all indexes
            self.baseindex += self.batchsize
            self.stepToPresent()

            # fill up data response arrays
            self.fillresponsearrays()

            return tf.convert_to_tensor(self.returndatanumpy), tf.convert_to_tensor(self.returnlookaheadnumpy)

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
