import tensorflow as tf
import collections

class WindowSlider:

    #TODO Implement raise StopIterations

    features = ("Open", "High", "Low", "Close", "Volume")

    def __init__(self, windowsize, lookforward, baseTimeframeDataset, otherdatasets:dict = {}):
        """
        Create a window slider that slides over datasets
        :param windowsize: How "wide" the data is
        :param lookforward: How far forward we should look for
        :param baseTimeframeDataset: Lowest timeframe dataset
        :param otherdatasets: Dict of other timeframe datasets, {"5m": dataset, "15m": dataset}
        """
        # Set up variables
        self.windowsize = windowsize
        self.lookforward = lookforward

        self.base = baseTimeframeDataset
        """base timeframe dataset"""
        self.baseTensor = None
        """base Tensor dict"""
        self.others = otherdatasets
        """TODO dict of datasets"""
        self.otherTensors = {}
        """Tensor dict of what the datasets contain"""


        # The +1 is handled by the fact that the index is 1 less than the total amount
        self.baseindex = self.windowsize + self.lookforward
        """Index where the most forward portion of the buffer is"""

        self.otherindexes = {}
        """Dict of indexes where the most forward portion of the buffer is"""

    def stepToPresent(self, timestamp = None):

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


    def __iter__(self):
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

    def __next__(self):

        response = {}
        response["basetimestamp"] = self.baseTensor["timestamp"][self.baseindex - self.lookforward]


        # Move forward, synchronize all indexes
        self.baseindex += 1
        self.stepToPresent()

        return response
