if __name__ == "__main__":
    import time
    import Client.Indicators as Indicators
    import Client.marketData as marketData

    # Training target
    pair = "LINKUSDT"

    # Time to nanoseconds
    timeframe = "1m"
    current = time.time() * 1000
    current = round(current)

    # Time step for requests
    block = 500 * 60 * 1000
    current -= block
    amount = 500

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

    # Save fetched data
    df.to_csv("Data/" + pair +"/"+ "history.csv")

    print("History data saved")


