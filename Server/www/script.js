const ws = new WebSocket('ws://localhost:8080');

    ws.onopen = () => {
      console.log('Connected to server');
      ws.send("henlou :DDDDDD")
      ws.send(JSON.stringify({boner: true}));
    };

    ws.onmessage = (event) => {
      console.log(`Message from server: ${event.data}`);
    };

    ws.onclose = () => {
      console.log('Connection closed');
    };