const express = require('express')
const app = express()
const port = 9000
const WebSockets = require("ws")
require('typescript-require');

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

    // handle debug ping
    if (message == "ping!"){
        obj = {"blocks": []}

        for(i = 0; i < 3; i++){
            obj.blocks.push({"blockid": i, "time": new Date()})
        }
        ws.send(JSON.stringify(obj))
    }

    //otherwise do something else
    try{
        let jason = JSON.parse(message)
        console.log(jason)
    }catch (e){
        console.log("could not jsonify "+ message)
    }
    //ws.send("Got your message: "+message)
}

function respondPing(ws){

}


const marketfetcher = require("./marketfetcher.ts")
marketfetcher.getPair("BTCUSD")
// Fetch all apis, then do something : Promise.all([promise1, promise2, promise3]).then((values) => {
//   console.log(values);
// });

// cronjob scheduling with node-schedule
//https://www.npmjs.com/package/node-schedule