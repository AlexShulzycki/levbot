import threading
import time
from datetime import datetime

import numpy as np
import tflite_runtime.interpreter as tflite

import marketData, Indicators, bridge, Preprocess


class bot():

    def predict(self):

        # Fetch data
        df = marketData.getPrices(self.ticker, "1m", 77)

        # Calculate indicators
        df = Indicators.Stochastic(df)
        df = Indicators.ADX(df)

        # Truncate unusable data
        df = df.iloc[27:]

        # Set last price
        self.lastprice = df["Close"][49].item() # .item() turns numpy64 to a regular float


        # Preprocess data into a numpy array
        inputs = np.array(Preprocess.prepare(df))
        # Reshape array for tensor input
        inputs = inputs.reshape(1, 400).astype("float32")

        # Get input/output tensors
        in_det = self.interpreter.get_input_details()
        out_det = self.interpreter.get_output_details()

        # Set input tensor
        self.interpreter.set_tensor(in_det[0]["index"], inputs)

        # Do the magic
        self.interpreter.invoke()

        # Retrieve prediction and turn it into a regular list
        prediction = self.interpreter.get_tensor(out_det[0]["index"])
        prediction = prediction[0].tolist()

        # 0 for none, 1 for short, 2 for long.
        print("Neutral: " + str(prediction[0]) + " Long: " + str(prediction[1]) + " Short: " + str(prediction[2]))

        # Return prediction
        return prediction.index(max(prediction))

    # Runs every minute on a fresh candle

    def tick(self):
        self.bridge.tick()
        print(datetime.now())
        prediction = self.predict()  # The last price is updated inside

        # Calculate size of potential position (two bucks for now) TODO Implement position sizing
        amount = (2 * self.lev) / self.lastprice  # Dollar amount * Leverage / Last price
        print(self.bridge.ticker, self.lastprice, self.lev, amount)

        if (self.cooldown > 0):
            self.cooldown -= 1
            print("Cooldown in effect: " + str(self.cooldown))
            return

        if (prediction == 0):
            return

        # Long
        if (prediction == 1):
            tp = 1 + self.tp
            sl = 1 - self.sl

            self.bridge.takePosition("BUY", float(self.lastprice * tp), float(self.lastprice * sl), amount)
            # Reset cooldown
            self.cooldown = 5
            return

        # Short
        if (prediction == 2):
            tp = 1 - self.tp
            sl = 1 + self.sl

            self.bridge.takePosition("SELL", float(self.lastprice * tp), float(self.lastprice * sl), amount)
            # Reset cooldown
            self.cooldown = 5
            return

    # Schedules ticks to happen on the minute TODO Find a better way for scheduling than blindly adding 1 minute to the clock
    def schedule(self):
        print("Thread Started")

        while self.Running:

            x = datetime.now()
            if (x.minute == 59):
                y = x.replace(hour=x.hour + 1, minute=0, second=1, microsecond=0)
            else:
                y = x.replace(minute=x.minute + 1, second=1, microsecond=0)

            waitTime = y - x

            time.sleep(waitTime.seconds)
            self.tick()
        print(self.ticker+" bot stopped.")

    # Start bot schedule thread
    def start(self):
        if (self.Running):
            # Skip if already running
            return
        self.Running = True
        self.thread = threading.Thread(target=self.schedule)
        self.thread.start()

    # Stop bot schedule
    def stop(self):
        # Set flag to false
        self.Running = False

    # Init
    def __init__(self, ticker, tp, sl, leverage, prce_prec, amnt_prec):
        print(ticker+" Bot Created")

        # Take profit, stop loss, leverage
        self.tp = tp
        self.sl = sl
        self.lev = leverage

        # Import API keys
        f = open("API.txt", "r")
        self.api_key = f.readline().rstrip()
        self.api_secret = f.readline().rstrip()
        f.close()
        # self.url = "http://testnet.binancefuture.com"
        self.url = "http://fapi.binance.com"

        # Init last price var
        self.lastprice = 0
        self.cooldown = 0

        self.ticker = ticker
        # Load TF Model
        self.interpreter = tflite.Interpreter(model_path="models/" + ticker + ".tflite")
        self.interpreter.allocate_tensors()

        # Create bridge
        self.bridge = bridge.bridge(self.url, self.ticker, int(prce_prec), int(amnt_prec))

        # Bot is not running yet
        self.Running = False
        # Start the bot immediately
        self.start()
