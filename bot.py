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
import hmac
import hashlib
import requests

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

    #Send to API
    def takePosition(self, side, tp, sl, quantity):
        headers = {"Content-type":"application/x-www-form-urlencoded" , "X-MBX-APIKEY": self.api_key}

        def send(querystring):

            # Add timestamp
            querystring += "&timestamp="+ str(time.time()*1000)[0:13]
            querystring += "&signature="+ str(hmac.new(bytes(self.api_secret, "utf-8"), bytes(querystring,"utf-8"), hashlib.sha256).hexdigest())

            # Send request
            print (requests.post(self.url + "/fapi/v1/order", headers=headers, data=querystring).text)


        # Market order
        querystring = "symbol=BTCUSDT&side="+side+"&type=MARKET&quantity="+quantity
        send(querystring)

        # Flip buy to sell and vice versa
        if(side == "BUY"):
            side = "SELL"
        else:
            side = "BUY"

        # Take profit
        querystring = "symbol=BTCUSDT&side="+side+"&type=TRAILING_STOP_MARKET&callbackRate=0.05&quantity="+quantity+"&activationPrice="+tp
        send(querystring)

        # Stop loss
        querystring = "symbol=BTCUSDT&side="+side+"&type=STOP_MARKET&quantity="+quantity+"&stopPrice="+sl
        send(querystring)

        # Reset cooldown
        self.cooldown = 5
        return

    #Runs every minute on a fresh candle
    # Take profit is 0.35 %, stop loss is 0.2 %
    def tick(self):
        print(datetime.now())
        prediction = self.predict()

        amount = 2/self.lastprice.item()
        amount = "{:f}".format(amount)

        if(self.cooldown > 0):
            self.cooldown -= 1
            print("Cooldown in effect: "+ str(self.cooldown))
            return

        if(prediction == 0):
            return
        # Long
        if(prediction == 1):
            print(self.lastprice*1.003)
            self.takePosition("BUY", str(self.lastprice*1.003)[0:8], str(self.lastprice*0.998)[0:8], amount)
            return

        # Short
        if(prediction ==2):
            print(self.lastprice * 1.003)
            self.takePosition("SELL", str(self.lastprice * 0.997)[0:8], str(self.lastprice * 0.1002)[0:8], amount)
            return
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

        # Start bot
        self.schedule(runsFor)

