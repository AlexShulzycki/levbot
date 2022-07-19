# levbot
Utterly useless trading bot that tries to throw TensorFlow at the complexities of cryptocurrency prices with predictable results.

## What is the idea?
The name stems from leverage bot, as Binance futures allows you to trade with 125x leverage on some cryptos. The idea is to just predict whether the price will go
up or down within the next few minutes, and 125x leverage a few bucks ando get filthy rich over time. That obviously does not work, but it was fun to build.

## How it rougly works
The TensorFlow model is trained on historical data using both 15 and 1 minute timeframes. The data is fetched from Binance, reformatted, and then Java is used
to efficiently go over the data and decide at each point in time whether taking a trade is favorable or not. A model is then trained on that data.

## How it runs
The bot is actually several bots operating on a different currency pair. When server.py (in /Client) is run, a http server is started which initializes all the 
bots (class /Client/bot.py) with their respective settings and currency pair TensorFlow Lite models. Then every minute new price data is pulled, from which 
a decision is made by each model whether or not a trade could be made. If a trade should be made, the trade is made via the Binance API (via /Client/bridge.py).

It is possible to run this on a Raspberry Pi.

## Will it make me money?
No.
