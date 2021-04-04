# Python 3 server

from http.server import BaseHTTPRequestHandler, HTTPServer
import bot

hostName = "localhost"
serverPort = 8080
bots = [bot.bot("BTCUSDT", "model")]

def printBots():
    string = ""
    i = 0
    for bot in bots:
        running = bot.Running
        button = ""
        if(running):
            running = "running"
            button = "Stop"
        else:
            running = "stopped"
            button = "Start"

        good = bot.bridge.good
        bad = bot.bridge.bad

        # Open div, add title
        string+= "<div class= 'bot'><h1 class = '"+running+"'> "+bot.ticker+" </h1>"

        # Start/Stop
        string+= "<h4>"+bot.url+"</h4><a class='"+button+"' href='bot"+str(i)+button+"'>"+button+"</a>"

        # Trades
        string+= "<div class= trades><h4>Good Trades</h4><p>" +str(good)+ "</p></div>"
        string+= "<div class= trades><h4>Bad Trades</h4><p>" + str(bad) + "</p></div>"

        # Close Div
        string+= "</div>"
        i+=1
    return string

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        # Send CSS
        if(self.path == "/style.css"):
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            self.wfile.write(bytes(open("style.css").read(), "utf-8"))
            return

        #bot commands
        if(self.path[1:4] == "bot"):
            print(self.path[1:4])
            id = int(self.path[4:5])
            if(self.path[5:] == "Start"):
                bots[id].start()
            elif(self.path[5:] == "Stop"):
                bots[id].stop()

            # All done

        # Continue if not CSS
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # Header tags, including stylesheet
        self.wfile.write(bytes("<html><head><title>levbot</title><link rel='stylesheet' href='style.css'></head>", "utf-8"))
        # Debug
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        # Open body tags
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<h1>Alex's Shitty Trading Bot</h1>", "utf-8"))

        self.wfile.write(bytes(printBots(), "utf-8"))

        # Close body and html tags
        self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")