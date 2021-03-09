# To be run by scheduler
# Get market data
# Compute indicators
# Truncate data
# Preprocess data
# Feed data to model
# Return buy, sell, or neutral signal
import tensorflow as tf
import numpy as np
import marketData
import Indicators
import Preprocess

def tick(ticker):

    # Fetch data
    df = marketData.getPrices("BTCUSDT", "1m", 77)

    # Calculate indicators
    df = Indicators.Stochastic(df)
    df = Indicators.ADX(df)

    #Truncate unusable data
    df = df.iloc[27:]

    # Preprocess data into a numpy array
    inputs = np.array(Preprocess.prepare(df))
    # Reshape array for tensor input
    inputs = inputs.reshape(1,400)

    # Load TF Model
    model = tf.keras.models.load_model("model")

    # 0 for none, 1 for short, 2 for long.
    prediction = model.predict(inputs)[0]

    prediction = prediction.tolist()

    print("Neutral: "+str(prediction[0])+" Long: "+str(prediction[1]) +" Short: "+str(prediction[2]))

