import tensorflow as tf
import collections

class WindowSlider:

    features = ("Open", "High", "Low", "Close", "Volume")

    def __init__(self, windowsize, lookforward, baseTimeframeDataset, otherdatasets):

        # Set up variables
        self.windowsize = windowsize
        self.lookforward = lookforward

        self.base = baseTimeframeDataset
        """Tensor dict"""
        self.others = otherdatasets
        """List of tensor dicts"""


        # The +1 is handled by the fact that the index is 1 less than the total amount
        self.baseindex = self.windowsize + self.lookforward
        """Index where the most forward portion of the buffer is"""
        self.otherindexes = [self.windowsize] * len(self.others)
        """List of indexes where the most forward portion of the buffer is"""

    def stepToPresent(self, timestamp = None):

        # Set current time
        if timestamp is None:
            ct = self.base["timestamp"][-(self.lookforward + 1)]
        else:
            ct = timestamp

        for i, ds in enumerate(self.others):
            # Check whether margin is before the current time
            while ct > ds["timestamp"][self.otherindexes[i]]:
                # We are not there yet, increase the index
                self.otherindexes[i] += 1

    def getLatestTime(self):
        """
        Returns the latest timestamp of the other timeframes
        """
        time = self.base["timestamp"][self.baseindex]

        for i, index in enumerate(self.otherindexes):
            latest = self.others[i]["timestamp"][index].value -1 # Remove one seconds to prevent fuckups wrt exact timing
            if latest > time:
                time = latest

        return time

    def __iter__(self):
        """
        Initializes the window slider from beginning
        """

        # Call iter on each dataset
        self.base = self.base.__iter__().__next__()
        for i, o in enumerate(self.others):
            self.others[i] = o.__iter__().__next__()

        # Reset indexes
        # The +1 is handled by the fact that the index is 1 less than the total amount
        self.baseindex = self.windowsize + self.lookforward
        self.otherindexes = [self.windowsize] * len(self.others)

        # Get latest time and step everyone to it
        latest = self.getLatestTime()
        self.stepToPresent(latest)

        return self

    def __next__(self):
        response = {}
        return self.base["timestamp"][self.baseindex - self.lookforward]

