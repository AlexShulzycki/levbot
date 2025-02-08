import tensorflow as tf
import TensorSlider as ts

def createLabelsBatch(data, lookforward):
    """
    create input labels from the lookahead data
    """

    shape = lookforward.shape

    dividepricesby = tf.reshape(lookforward[:, 0, 0, 0], (shape[0], 1, 1, 1))
    prices = tf.divide(lookforward[:, :, 0:4], dividepricesby)  # divide by latest base timeframe close
    prices -= 1  # zero out
    prices *= 10  # convert to 1/10 percentage, so 1 = 10 percent

    low = tf.reduce_min(prices[:, 0, 2], 1)
    high = tf.reduce_max(prices[:, 0, 1], 1)

    label = tf.stack([low, high], axis=1)

    shape = data.shape
    # data processing, format: batch, timeframe, feature(ohlcv), window (ascending time)
    # prices
    dividepricesby = tf.reshape(data[:, 0, 3, -1], (shape[0], 1, 1, 1))
    prices = tf.divide(data[:, :, 0:4], dividepricesby)  # divide by latest base timeframe close
    prices -= 1  # zero out
    prices *= 10  # convert to 1/10 percentage, so 1 = 10 percent

    volumes = tf.reshape(data[:, :, 4], (shape[0], shape[1], 1, shape[3]))
    dividebyvolume = tf.reshape(data[:, :, 4, -1], (shape[0], shape[1], 1, 1))
    volume = tf.divide(volumes, dividebyvolume)  # divide by latest volume (of each timeframe)
    volume -= 1
    volume *= 10  # convert to 1/10 percentage, so 1 = 10 percent

    data = tf.clip_by_value(tf.concat([prices, volume], axis=2), -2, 2)
    # remove nans
    data, label = tf.keras.ops.nan_to_num(data), tf.keras.ops.nan_to_num(label)

    return data, label


def decode(record_bytes):
    # Function for parsing each record in the tf files
    example = tf.io.parse_single_example(
        # Data
        record_bytes,

        # Schema
        {
            'Timeframe': tf.io.FixedLenFeature([], tf.string),
            'timestamp': tf.io.RaggedFeature(dtype=tf.int64),
            'Open': tf.io.RaggedFeature(dtype=tf.float32),
            'High': tf.io.RaggedFeature(dtype=tf.float32),
            'Low': tf.io.RaggedFeature(dtype=tf.float32),
            'Close': tf.io.RaggedFeature(dtype=tf.float32),
            'Volume': tf.io.RaggedFeature(dtype=tf.float32),
        }
    )

    return example


def getDataset(path):
    ds = tf.data.TFRecordDataset(path, num_parallel_reads=tf.data.AUTOTUNE)
    ds = ds.map(decode, num_parallel_calls=tf.data.AUTOTUNE)
    return ds


def getRandomSlider(coin, window_size, lookahead, batch_size, tfrecordpath ="../Data/tfrecords/"):
    path = tfrecordpath + coin+"/{tframe}.tfrecord"
    datasets = {"1m" : getDataset(path.format(tframe="1m")),
                "3m" : getDataset(path.format(tframe="3m")),
                "5m":  getDataset(path.format(tframe="5m")),
                "15m":  getDataset(path.format(tframe="15m")),
                "30m":  getDataset(path.format(tframe="30m")),
                "1h":  getDataset(path.format(tframe="1h"))}
    return ts.RandomWindowSlider(datasets, window_size, lookahead, batch_size)

def getAllSliders(coins, window_size, lookahead, batch_size, tfrecordpath ="../Data/tfrecords/"):
    """Gets random sliders for the given coins. Lookahead and window_size must match model"""
    datasets = []
    for coin in coins:
        datasets.append(tf.data.Dataset.from_generator(lambda: getRandomSlider(coin, window_size, lookahead, batch_size, tfrecordpath),
                                                       output_signature=(
                tf.TensorSpec((batch_size, 6, 5, window_size), dtype=tf.float32),
                tf.TensorSpec((batch_size,6,5, lookahead+1), dtype=tf.float32))
                                                       ))#.prefetch(tf.data.AUTOTUNE))
    return datasets