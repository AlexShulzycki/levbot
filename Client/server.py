# Python 3 server

from http.server import BaseHTTPRequestHandler, HTTPServer

from Client import bot

hostName = "localhost"
serverPort = 8080
bots = []


def printBots():
    string = ""
    i = 0
    for bot in bots:
        running = bot.Running
        button = ""
        if (running):
            running = "running"
            button = "Stop"
        else:
            running = "stopped"
            button = "Start"

        good = bot.bridge.good
        bad = bot.bridge.bad

        # Open div, add title
        string += "<div class= 'bot'><h1 class = '" + running + "'> " + bot.ticker + " </h1>"

        # Start/Stop
        string += "<h4>" + bot.url + "</h4><a class='" + button + "' href='bot" + str(
            i) + button + "'>" + button + "</a>"

        # Trades
        string += "<div class= trades><h4>Good Trades</h4><p>" + str(good) + "</p></div>"
        string += "<div class= trades><h4>Bad Trades</h4><p>" + str(bad) + "</p></div>"

        # Close Div
        string += "</div>"
        i += 1
    return string


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        # Send CSS
        if (self.path == "/style.css"):
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            self.wfile.write(bytes(open("style.css").read(), "utf-8"))
            return

        # bot commands
        if (self.path[1:4] == "bot"):
            id = int(self.path[4:5])

            if (self.path[5:] == "Start"):
                bots[id].start()
                #self.wfile.write(bytes("Bot Started", "utf-8"))

            elif (self.path[5:] == "Stop"):
                bots[id].stop()
                #self.wfile.write(bytes("Bot Stopped", "utf-8"))

            # All done

        # Continue if not CSS
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # Header tags, including stylesheet
        self.wfile.write(
            bytes("<html><head><title>levbot</title><link rel='stylesheet' href='style.css'></head>", "utf-8"))
        # Debug
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        # Open body tags
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<h1>Alex's Shitty Trading Bot</h1>", "utf-8"))

        self.wfile.write(bytes(printBots(), "utf-8"))

        # Close body and html tags
        self.wfile.write(bytes("</body></html>", "utf-8"))

def initializeBots():

    # Read data from config file
    import csv
    with open("config.csv") as csvfile:
        data = list(csv.reader(csvfile))

    # Remove the first row containing column headers
    data.pop(0)

    # Now that we have the configuration data, we can initialize the bots
    models = os.listdir("models")
    for x in data:
        # Check if tflite model exists in the models folder
        if x[0]+".tflite" in models:
            # Model exists, initialize the bot
            bots.append(bot.bot(x[0], float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])))
        else:
            print(x[0]+" does not have a .tflite model, skipping.")


if __name__ == "__main__":

    # Detect models we can use
    import os
    initializeBots()


    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
