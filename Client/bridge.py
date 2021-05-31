import requests
import hmac
import hashlib
import time
import json

class bridge():

    def orderStatus(self, order_id):

        # Headers and query
        headers = {"Content-type": "application/x-www-form-urlencoded", "X-MBX-APIKEY": self.api_key}
        querystring = "symbol=" + self.ticker +"&orderId="+ str(order_id)

        # Add timestamp
        querystring += "&timestamp=" + str(time.time() * 1000)[0:13]
        querystring += "&signature=" + str(
            hmac.new(bytes(self.api_secret, "utf-8"), bytes(querystring, "utf-8"), hashlib.sha256).hexdigest())

        # Send request and return status
        return json.loads(requests.get(self.url + "/fapi/v1/order", headers=headers, params=querystring).text)["status"]


    def cancelAll(self):

        # Headers and query
        headers = {"Content-type": "application/x-www-form-urlencoded", "X-MBX-APIKEY": self.api_key}
        querystring = "symbol="+self.ticker

        # Add timestamp
        querystring += "&timestamp=" + str(time.time() * 1000)[0:13]
        querystring += "&signature=" + str(
            hmac.new(bytes(self.api_secret, "utf-8"), bytes(querystring, "utf-8"), hashlib.sha256).hexdigest())

        # Send request
        print(requests.delete(self.url + "/fapi/v1/allOpenOrders", headers=headers, data=querystring).text)

    def tick(self):
        # Check if take profit or stop loss is complete, if so, cancel other order
        if(len(self.orders) == 0):
            # Return if we got no positions
            return
        # TP
        if(self.orderStatus(self.orders[0]) == "FILLED"):
            print("Take profit filled")
            self.good += 1
            self.cancelAll()
            self.orders = []
            return

        # SL
        if (self.orderStatus(self.orders[1]) == "FILLED"):
            print("Stop Loss Filled")
            self.bad += 1
            self.cancelAll()
            self.orders = []
            return


    def takePosition(self, side, tp, sl, quantity):

        if(len(self.orders) != 0):
            print("Already have position, skipping for now")
            return

        headers = {"Content-type": "application/x-www-form-urlencoded", "X-MBX-APIKEY": self.api_key}

        # Format all prices to 3 decimal precision
        quantity = ("{:."+str(self.amntprec)+"f}").format(quantity)
        tp = ("{:."+str(self.prcprec)+"f}").format(tp)
        sl = ("{:."+str(self.prcprec)+"f}").format(sl)

        # Debug
        print(self.ticker, side, quantity)

        def send(querystring):

            # Add timestamp
            querystring += "&timestamp=" + str(time.time() * 1000)[0:13]
            querystring += "&signature=" + str(
                hmac.new(bytes(self.api_secret, "utf-8"), bytes(querystring, "utf-8"), hashlib.sha256).hexdigest())

            # Send request
            return requests.post(self.url + "/fapi/v1/order", headers=headers, data=querystring).text

        # Market order
        querystring = "symbol="+self.ticker+"&side=" + side + "&type=MARKET&quantity=" + quantity
        send(querystring)

        # Flip buy to sell and vice versa
        if (side == "BUY"):
            side = "SELL"
        else:
            side = "BUY"

        # Take profit
        querystring = "symbol="+self.ticker+"&side=" + side + "&reduceOnly=true&type=TRAILING_STOP_MARKET&quantity=" + quantity + "&activationPrice=" + tp+"&callbackRate="+ str(0.1)
        res = json.loads(send(querystring))
        print(res)
        self.orders.append(res["orderId"])

        # Stop loss
        querystring = "symbol="+self.ticker+"&side=" + side + "&reduceOnly=true&type=STOP_MARKET&quantity=" + quantity + "&stopPrice=" + sl
        res = json.loads(send(querystring))
        print(res)
        self.orders.append(res["orderId"])

        return

    def __init__(self, url, ticker, prcprec, amntprec):
        self.url = url
        self.lastprice = 0
        self.ticker = ticker
        self.prcprec = prcprec
        self.amntprec = amntprec

        # Import API keys
        f = open("API.txt", "r")
        self.api_key = f.readline().rstrip()
        self.api_secret = f.readline().rstrip()
        f.close()

        self.orders = []

        self.good = 0
        self.bad = 0

