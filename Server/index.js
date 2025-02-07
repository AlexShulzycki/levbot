const express = require('express')
const app = express()
const port = 9000
const WebSockets = require("ws")

app.use(express.static("www"))
app.get('/', (req, res) =>{
    res.send("whats good lmao")
} )

app.listen(port)

const wss = new WebSockets.WebSocketServer({port: 8080}) //websocket server

wss.on("connection", (ws)=> {
    console.log("New client wants to connect lmao")
    ws.send("Whats good")
    ws.on("message", (message)=>{receive(ws, message)})
});



function receive(ws, message){
    console.log("received message: "+message)
    try{
        let jason = JSON.parse(message)
        console.log(jason.boner)
    }catch (e){
        console.log("could not jsonify "+ message)
    }
    ws.send("Got your message: "+message)
}

// Fetch all apis, then do something : Promise.all([promise1, promise2, promise3]).then((values) => {
//   console.log(values);
// });

// Now we have to figure out some kind of cronjob scheduling