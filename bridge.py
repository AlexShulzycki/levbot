import requests
import hmac
import hashlib
import time
import json

class bridge():

    def tick(self):
        # Check if take profit or stop loss is complete, if so, cancel other order
        print(self.orders)
        return

    def takePosition(self, side, tp, sl, quantity):

        if(len(self.orders) != 0):
            print("Already have position, skipping for now")
            return

        headers = {"Content-type": "application/x-www-form-urlencoded", "X-MBX-APIKEY": self.api_key}

        def send(querystring):

            # Add timestamp
            querystring += "&timestamp=" + str(time.time() * 1000)[0:13]
            querystring += "&signature=" + str(
                hmac.new(bytes(self.api_secret, "utf-8"), bytes(querystring, "utf-8"), hashlib.sha256).hexdigest())

            # Send request
            return requests.post(self.url + "/fapi/v1/order", headers=headers, data=querystring).text

        # Market order
        querystring = "symbol=BTCUSDT&side=" + side + "&type=MARKET&quantity=" + quantity
        send(querystring)

        # Flip buy to sell and vice versa
        if (side == "BUY"):
            side = "SELL"
        else:
            side = "BUY"

        # Take profit
        querystring = "symbol=BTCUSDT&side=" + side + "&type=TRAILING_STOP_MARKET&callbackRate=0.05&quantity=" + quantity + "&activationPrice=" + tp
        self.orders.append(json.loads(send(querystring)))

        # Stop loss
        querystring = "symbol=BTCUSDT&side=" + side + "&type=STOP_MARKET&quantity=" + quantity + "&stopPrice=" + sl
        self.orders.append(json.loads(send(querystring)))

        return

    def __init__(self, url):
        self.url = url
        self.lastprice = 0

        # Import API keys
        f = open("Data/API.txt", "r")
        self.api_key = f.readline().rstrip()
        self.api_secret = f.readline().rstrip()
        f.close()

        self.orders = []

