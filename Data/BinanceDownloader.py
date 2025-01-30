import shutil
from tabnanny import verbose

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


class Downloader:

    def __init__(self, onlinedirectoryurl: str, savefolder: str):
        """

        :param onlinedirectoryurl: https(...)/markPriceKlines/AAVEUSD_PERP/1d/
        :param savefolder: folder where to save the files
        """
        """Folder of the online URL, contains / at the end"""
        self.urlfolder = onlinedirectoryurl
        """Local save folder location, contains / at the end"""
        self.savefolder = savefolder

        # make sure the savefolder has a final slash
        if self.savefolder[-1] != '/':
            self.savefolder += "/"
        # make sure the onlinedirectory has a final slash
        if self.urlfolder[-1] != '/':
            self.urlfolder += "/"

        # Extract info from URL
        urlsplit = self.urlfolder.split("/")
        self.coin = urlsplit[-3]
        self.datatype = urlsplit[-4]
        self.timeframe = urlsplit[-2]

        # If save folder does not exist, make it
        try:
            os.makedirs(self.savefolder+"zipped/")
            os.makedirs(self.savefolder + "csv/")
        except FileExistsError:
            # directory already exists, nothing to do
            pass

        # Run the magic
        #self.Download(self.getAvailable())

    def Download(self, urls):
        pbar = tqdm(total=len(urls), desc=f"Downloading {len(urls)} files from {self.urlfolder}", leave=False)
        with ThreadPoolExecutor() as executor:
            for url in urls:
                executor.submit(self.downloadAndUnzip, url, pbar)
        pbar.close()

    def getAvailable(self, verbose = False) -> list:
        """
         Get filenames that can be downloaded, by counting down chronologically from the current time

        """
        month = int(datetime.datetime.now().strftime("%m"))
        year = int(datetime.datetime.now().strftime("%Y"))

        fileprefix = f"{self.urlfolder}{self.coin}-{self.timeframe}"

        if verbose:
            pbar = tqdm(desc=f"Checking for files in {self.urlfolder}", leave=False)
            pbar.update(0)
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

            if verbose:
                pbar.set_description(f"{year} - {month}, response {res.status_code}")
                pbar.refresh()

            # Check if it exists
            if res.status_code != 200:
                # Does not exist, no more data, return what we have
                if verbose:
                    pbar.close()
                return result
            else:
                if verbose:
                    pbar.update(1)
                # Append to results
                result.append(fileurl)


    def downloadAndUnzip(self, fileurl, pbar = None):
        """

        :param fileurl: complete file url to download, file extension included
        :param pbar: TQDM progress bar, will call update() on completion
        :return: nothing :)
        """
        # Generate filename from file url
        filename = fileurl.split("/")[-1]

        # request!
        response = requests.get(fileurl)

        if response.status_code != 200:
            print("Error downloading " + "filename")

        # Download the file and unzip it
        try:
            ziplocation = self.savefolder + "zipped/" +filename
            with open(ziplocation, mode="wb") as file:
                file.write(response.content)
                file.close()
            shutil.unpack_archive(ziplocation, self.savefolder + "csv/")
            print("saved "+filename)
        except Exception as e:
            print(e)

        # Update progress bar if we got one
        if pbar is not None:
            pbar.update(1)



def bulkDataTypeCoinTimeframes(baseurl: str, datatypes: list, coins: list, timeframes: list, savedirectory:str):
    """
    TODO: Non functional, fix in the future sometime, threadpool executor more than one, write another class:)
    Download timeframes from this url
    :param baseurl: base url, i.e. https:/(...)/cm/monthly/
    :param datatypes: list of datatypes, i.e. klines, whatever
    :param coins: BTCUSD_PERP, AAVEUSD_PERP
    :param timeframes: 1m, 5m, etc
    :param savedirectory: folder where to save the files
    :return: nothing
    """
    # make sure the url and folder has a final slash
    if baseurl[-1] != '/':
        baseurl += "/"
    if savedirectory[-1] != '/':
        savedirectory += "/"


    with ThreadPoolExecutor() as executor:
        for datatype in datatypes:
            for coin in tqdm(coins):
                coinurl = f"{baseurl}{datatype}/{coin}/"
                for timeframe in timeframes:
                    coinurl = f"{coinurl}{timeframe}/"
                    dwnld = Downloader(coinurl, f"{savedirectory}{coin}/{datatype}/{timeframe}/")
                    available = dwnld.getAvailable(verbose = True)

                    pbarinner = tqdm(total=len(available), desc=f"{datatype} {timeframe}", leave=False)
                    pbarinnerplural = []
                    for av in available:
                        pbarinnerplural.append(pbarinner)
                    executor.map(dwnld.Download, available, pbarinnerplural)