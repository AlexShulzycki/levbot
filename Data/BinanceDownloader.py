import requests
import datetime
import time
import os
from tqdm.auto import tqdm
from concurrent.futures import ThreadPoolExecutor

def coinDirURL(coin: str, timeframe: str) -> str:
    """
    Create director URL for the given coin and timeframe.
    :param coin: "BTC"
    :param timeframe: "1m"
    :return: url
    """
    baseurl = "https://data.binance.vision/data/futures/cm/monthly/klines/"
    return f"{baseurl + coin}USD_PERP/{timeframe}/"




def unzipall(coins):
    import shutil
    for coin in coins:
        for file in tqdm(os.listdir(coin + "/zipped")):
            finaldirectory = coin + "/csv/" + file.split("-")[0]
            print(finaldirectory)
            try:
                os.makedirs(finaldirectory)
            except FileExistsError:
                # directory already exists
                pass
            if file.endswith(".zip"):
                shutil.unpack_archive(coin + "/zipped/" + file, finaldirectory)


def downloadZipsForTimeframe(coin, timeframe):
    try:
        filenames = getAvailable(coin, timeframe)
        timeframes = []
        for filename in filenames:
            timeframes.append(timeframe)

        with ThreadPoolExecutor() as executor:
            executor.map(dwnld, filenames, timeframes)
    except Exception as e:
        print(e)


def downloadhistorical(coins, timeframes):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor() as executor:
        for coin in coins:
            # Create an equivalent array of just the coin for the map
            coinplural = []
            for timeframe in timeframes:
                coinplural.append(coin)
            executor.map(downloadZipsForTimeframe, coinplural, timeframes)
    unzipall(coins)


class Downloader:

    def __init__(self, onlinedirectoryurl: str, savefolder: str):
        """

        :param onlinedirectoryurl: https(...)/markPriceKlines/AAVEUSD_PERP/1d/
        :param savefolder: folder where to save the files
        """
        self.urlfolder = onlinedirectoryurl
        self.savefolder = savefolder

        # make sure the savefolder has a final slash
        if self.savefolder[-1] != '/':
            self.savefolder += "/"
        # make sure the onlinedirectory has a final slash
        if self.urlfolder[-1] != '/':
            self.urlfolder += "/"

        # Extract info from URL
        urlsplit = self.urlfolder.split("/")
        self.timeframe = urlsplit[-1]
        self.coin = urlsplit[-2]

        # If save folder does not exist, make it
        try:
            os.makedirs(self.savefolder)
        except FileExistsError:
            # directory already exists, nothing to do
            pass

    def getAvailable(self) -> list:
        """
         Get filenames that can be downloaded, by counting down chronologically from the current time

        """
        month = int(datetime.datetime.now().strftime("%m"))
        year = int(datetime.datetime.now().strftime("%Y"))

        fileprefix = f"{self.urlfolder}{self.coin}-{self.timeframe}"

        result = []
        while True:  # infinite loop until we break
            time.sleep(0.05)
            month -= 1
            # Loop back to december
            if month == 0:
                year -= 1
                month = 12

            # URL of the file we are checking, formatting month to have leading zeros
            fileurl = f"{fileprefix}-{year}-{format(month, '02d')}.zip"

            # Send the request
            res = requests.head(fileurl)
            print(f"{year} - {month}, response {res.status_code}")

            # Check if it exists
            if res.status_code != 200:
                # Does not exist, no more data, return what we have
                return result
            else:
                # Append to results
                result.append(fileurl)

    def downloadOneFile(self, fileurl, pbar):
        """

        :param fileurl: complete file url to download, file extension included
        :param pbar: TQDM progress bar, will call update() on completion
        :return: nothing :)
        """
        # Generate filename
        filename = fileurl.split("/")[-1]

        # request!
        response = requests.get(fileurl)

        if response.status_code != 200:
            print("Error downloading " + "filename")

        try:
            with open(self.savefolder + filename, mode="wb") as file:
                file.write(response.content)
                file.close()
        except Exception as e:
            print(e)

        pbar.update(1)



