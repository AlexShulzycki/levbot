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
from datetime import datetime
import time
import bridge

class bot():

    def predict(self):

        # Fetch data
        df = marketData.getPrices(self.ticker, "1m", 77)

        # Calculate indicators
        df = Indicators.Stochastic(df)
        df = Indicators.ADX(df)

        #Truncate unusable data
        df = df.iloc[27:]

        # Set last price
        self.lastprice = df["Close"][49]

        # Preprocess data into a numpy array
        inputs = np.array(Preprocess.prepare(df))
        # Reshape array for tensor input
        inputs = inputs.reshape(1,400)

        # 0 for none, 1 for short, 2 for long.
        prediction = self.model.predict(inputs)[0].tolist()

        print("Neutral: "+str(prediction[0])+" Long: "+str(prediction[1]) +" Short: "+str(prediction[2]))

        # Return prediction
        return prediction.index(max(prediction))

    #Runs every minute on a fresh candle
    # Take profit is 0.35 %, stop loss is 0.2 %
    def tick(self):
        self.bridge.tick()
        print(datetime.now())
        prediction = self.predict()

        amount = 200/self.lastprice.item() # Dollar amount * Leverage

        if(self.cooldown > 0):
            self.cooldown -= 1
            print("Cooldown in effect: "+ str(self.cooldown))
            return

        if(prediction == 0):
            return
        # Long
        if(prediction == 1):
            tp = 1 + self.tp
            sl = 1- self.sl

            self.bridge.takePosition("BUY", str(self.lastprice*tp), str(self.lastprice*sl), amount)
            # Reset cooldown
            self.cooldown = 5
            return

        # Short
        if(prediction ==2):
            tp = 1 - self.tp
            sl = 1 + self.sl

            self.bridge.takePosition("SELL", str(self.lastprice * tp), str(self.lastprice * sl), amount)
            # Reset cooldown
            self.cooldown = 5
            return

    #Runs tick every minute on a fresh candle
    def schedule(self, runsFor):
        print("Bot scheduled for "+str(runsFor)+"m")

        for i in range(0, runsFor):

            x = datetime.now()
            if(x.minute == 59):
                y = x.replace(hour= x.hour +1,minute= 0, second= 1, microsecond= 0)
            else:
                y = x.replace(minute=x.minute + 1, second=1, microsecond=0)

            waitTime = y - x

            time.sleep(waitTime.seconds)
            self.tick()

        print("Schedule finished, exiting now.")


    # Init
    def __init__(self, ticker, model, runsFor):
        print("Bot started")

        # Take profit, stop loss
        self.tp = 0.25/100
        self.sl = 0.2/200

        # Import API keys
        f = open("Data/API.txt", "r")
        self.api_key = f.readline().rstrip()
        self.api_secret = f.readline().rstrip()
        f.close()
        self.url = "http://testnet.binancefuture.com"

        # Init last price var
        self.lastprice = 0
        self.cooldown = 0

        self.ticker = ticker
        # Load TF Model
        self.model = tf.keras.models.load_model(model)

        # Create bridge
        self.bridge = bridge.bridge(self.url, self.ticker)

        # Start bot
        self.schedule(runsFor)

