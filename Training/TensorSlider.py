import random
import numpy as np
import tensorflow as tf
import numba as nb
from numba.experimental import jitclass



class WindowSlider:

    #TODO Test raise StopIterations
    features:list = ["timestamp", "Open", "High", "Low", "Close", "Volume"]

    inMinutes:dict = {
        "1m": 1,
        "3m": 3,
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

        # Create processed data variable
        self.processed = processed
        # Create speedslider variable
        self.speedslider = None


    def __iter__(self):
        """
        Called when an iteration is started.
        """
        self.speedslider.iter()
        return self

    def __next__(self):
        """
        Called after iteration started, returns next value
        """
        try:
            return self.speedslider.next()

        except IndexError:
            raise StopIteration

class ForwardWindowSlider(WindowSlider):
    def __init__(self, datasets: dict, windowsize: int = 100, lookforward: int = 5, batchsize: int = 1):
        super().__init__(datasets, windowsize, lookforward, batchsize)

        # Initialize the forward speedslider
        self.speedslider = ForwardSpeedSlider(self.processed, self.batchsize, self.windowsize, self.lookforward)



class RandomWindowSlider(WindowSlider):
    def __init__(self, datasets: dict, windowsize: int = 100, lookforward: int = 5, batchsize: int = 1):
        super().__init__(datasets, windowsize, lookforward, batchsize)

        # Initialize the random
        self.speedslider = RandomSpeedSlider(self.processed, self.batchsize, self.windowsize, self.lookforward)



specForward = [
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

@jitclass(specForward)
class ForwardSpeedSlider:
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

    def updateIndex(self, index:int, updateTo):
        tlength = self.tensors.shape[2]
        if updateTo >= tlength or updateTo < 0:
            print(f"Index maxxed, index: {index}, updateTo: {updateTo}")
            raise IndexError
        else:
            self.indexes[index] = updateTo


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
                currentindex = self.indexes[timeframe]
                self.updateIndex(timeframe, currentindex + 1)

    def iter(self):
        # Slide all indexes to the minimum window size
        self.indexes[:] = self.windowsize + self.lookforward # we will allow this bypassing updateindex

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
            nextindex = self.indexes[0] +1
            self.updateIndex(0, nextindex)
            self.updateCurrentTimestamps()
            self.stepToPresent(self.currenttimes[0])
            # Fill
            self.fillresponsearrays(i)

        return self.dataoutput, self.lookforwardoutput


specRandom = [
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
    ("iterationcount", nb.int32)
]

@jitclass(specRandom)
class RandomSpeedSlider:
    def __init__(self, tensors, batchsize, windowsize, lookforward):
        self.tensors = tensors
        """Indexed by increasing timeframe, base is at index 0 -> [timeframe, feature, entry]"""
        self.batchsize = batchsize
        self.windowsize = windowsize
        self.lookforward = lookforward
        self.indexes = np.zeros(shape=(tensors.shape[0]), dtype=np.int32)
        """Indexed by increasing timeframe, base is at index 0. Points to current time"""

        # Set up output buffers
        self.lookforwardoutput = np.zeros(shape=(self.batchsize, tensors.shape[0], tensors.shape[1]-1, self.lookforward +1), dtype=np.float32)
        self.dataoutput = np.zeros(shape=(self.batchsize, tensors.shape[0], tensors.shape[1]-1, self.windowsize), dtype=np.float32)
        """ [Batch, timeframe, feature, entry], feature -1 because we dont include the timestamp"""
        # Compute time variables
        self.deltas = np.zeros(shape=(tensors.shape[0]), dtype=np.float32)
        """Approximate delta t between timeframe entries"""
        self.currenttimes = np.zeros(shape=(tensors.shape[0]), dtype=np.int32)
        """Timestamp at the current time index for each timestamp (index-lookforward)"""

        self.iterationcount = 0
        """How many times we have returned next() since iter was called"""

        # Compute deltas
        for i in range(tensors.shape[0]):
            self.deltas[i] = (self.tensors[i,0,100] - self.tensors[i,0,1])/100 # get delta

    def updateIndex(self, index:int, updateTo):
        tlength = self.tensors.shape[2]
        if updateTo >= tlength or updateTo < 0:
            raise IndexError
        else:
            self.indexes[index] = updateTo


    def updateCurrentTimestamps(self):
        """
        Updates the timestamp array with timestamps pointed to by the indexes
        """
        for i in range(self.currenttimes.shape[0]):
            self.currenttimes[i] = self.tensors[i,0,self.indexes[i]] # get timestamp


    def creepToTimestamp(self, timeframe:int, initialguess:int, timestamp:int) ->bool:
        """
        Creeps timeframe index to a given timestamp.
        :param timeframe: index of timeframe
        :param guess: initial index guess
        :param timestamp: timestamp to creep to
        :return: True if successful, False otherwise
        """
        # Check if initial guess is in range
        guess = initialguess
        if not self.validIndex(timeframe, guess):
            return False

        # We are in business, check if we are over or undershooting
        # Tensor is timeframe, feature(timestamp is feature 0), entry
        overshooting = np.greater(self.tensors[timeframe, 0, guess], timestamp)
        if not self.tensors[timeframe, 0, guess]>0:
            return False# We have hit a padding 0, not valid!
        if overshooting:
            # We creep downwards
            while overshooting:
                guess -= 1 # move down
                if not self.validIndex(timeframe, guess):
                    return False # check if we can indeed move down
                # we can move down, lets check if this timestamp is below the target
                overshooting = self.tensors[timeframe, 0, guess] > timestamp

            # We want the real guess to be pointing to the first overshoot value
            guess += 1
        else:
            while not overshooting:
                guess += 1
                if not self.validIndex(timeframe, guess):
                    return False
                # We can move up, lets check if this timestamp is above the target
                overshooting = self.tensors[timeframe, 0, guess] > timestamp

        # Our guess points to the first entry after the window, lets calculate the index ranges we will be reading
        start = guess - self.windowsize
        end = guess + self.lookforward +self.batchsize +1 # plus one since we include the current latest timestamp

        if self.validIndex(timeframe, start) and self.validIndex(timeframe, end):
            # all good, lets update the indexes
            self.indexes[timeframe] = guess # set the index
            self.updateCurrentTimestamps() # update timestamps
            return True
        else:
            return False



    def synchronizeIndexesToTimestamp(self, timestamp:int) -> bool:
        """
        Synchronizes indexes to the timestamp. Returns True if possible, False if out of range
        :param timestamp: Timestamp to slide to
        """
        self.updateCurrentTimestamps()

        # calculate approximate deltas from current position
        timestampdeltas = timestamp - self.currenttimes

        # Calculate index deltas and turn all infs to zeros
        indexdeltas = np.divide(timestampdeltas,self.deltas)
        indexdeltas[np.isinf(indexdeltas)] = 0

        # We need to make sure that we round down so we don't leak the future, better to have a lower index than see the future.
        indexdeltas = np.floor(indexdeltas)
        # This is a very coarse approximation, since the timestamp at the index is at the lookahead position

        # Synchronize the index pointers
        for i, indexdelta in enumerate(indexdeltas):
            if indexdelta == 0: continue
            valid = self.creepToTimestamp(i, int(self.indexes[i] + indexdelta), timestamp)
            # Creep to timestamp
            if not valid:
                # out of range!
                return False

        # All good!
        return True

    def iter(self):
        # Reset counter to zero
        self.iterationcount = 0

    def fillresponsearrays(self, batchindex):

        # iterate over each timeframe
        for timeframe, timeframetensor in enumerate(self.tensors):
            # We are skipping the timestamp at index 0
            # We are only selecting the window size
            windowstart = self.indexes[timeframe] - self.windowsize
            windowend = self.indexes[timeframe]
            lookforwardend = windowend + self.lookforward + 1 # plus one for slicing

            # fill data output
            self.dataoutput[batchindex][timeframe] = timeframetensor[1:, windowstart: windowend]

            # fill lookforward
            self.lookforwardoutput[batchindex][timeframe] = timeframetensor[1:, windowend: lookforwardend]

    def validIndex(self, timeframe, index) -> bool:
        """
        Returns if this index exists, and thus is usable.
        :param timeframe: timeframe of the index.
        :param index: Index number to check
        :return: True if valid, False if out of range
        """
        timeframelength = self.tensors[timeframe].shape[1]

        if (index >= timeframelength - 1) or (index < 0):
            return False
        else:
            return True

    def next(self):
        """
        Selects random index in base timeframe, slides all timeframes to just before its approximate location,
        slides forward to synchronize, and steps forward base timeframe by base timeframe until the output buffers are
        filled.
        :return: Filled output buffers
        """
        basetimeframelength = self.tensors.shape[2]
        # Check if we are done iterating
        if self.iterationcount > basetimeframelength: # we are iterating for the size of the base timeframe
            raise IndexError

        # Still iterating, lets select a random index until we find one that is valid
        valid = False
        while not valid:
            randindex = random.randint(self.windowsize, basetimeframelength -1) # -1 since we want the index
            valid = self.synchronizeIndexesToTimestamp(self.tensors[0, 0, randindex])


        # fill up batches
        for i in range(self.batchsize):
            # Fill
            self.fillresponsearrays(i)
            # Increment target timestamp by the delta of the base timeframe, +1 to double make sure
            # This is why we don't update the current times
            # IF this does not succeed we have a big problem
            if not self.synchronizeIndexesToTimestamp(int(self.currenttimes[0] + self.deltas[0] + 1)): raise Exception

        return self.dataoutput, self.lookforwardoutput