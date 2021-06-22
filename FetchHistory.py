import math

if __name__ == "__main__":
    import time
    import numpy
    import Client.Indicators as Indicators
    import Client.marketData as marketData

    #How far back you want to go
    amount = 500

    # Training target
    pair = "ATOMUSDT"


    def fetch(timeframe, amount):

        # Time to nanoseconds
        current = time.time() * 1000
        current = round(current)

        # Time step for requests
        block = 500 * 60 * 1000
        current -= block

        # Populating latest
        df = marketData.getPrices(pair, timeframe, 500)
        for i in range(0, amount):
            print(str(str(i) + "/"+ str(amount)))
            df = df.append(marketData.getHistorical(pair, timeframe, current - block, current))
            current -= block

        df = df.sort_index()
        print("Done fetching")

        df = Indicators.Stochastic(df)
        df = Indicators.ADX(df)

        # Truncate unusable data
        df = df.iloc[27:]

        print("Indicators added")

        # Set datetime to millis
        df = df.reset_index() # we have to unset, modify, and then reset the index column.
        df["Time"] = df["Time"].astype(numpy.int64) / int(1e6)
        df.set_index("Time", inplace=True)


        # Save fetched data
        df.to_csv("Data/" + pair +"/"+ timeframe + "history.csv")

    # Get 1m
    fetch("1m", amount)
    fetch("1h", amount+50)

    print("History data saved")


