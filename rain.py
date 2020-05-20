from pprint import pprint
import requests
from datetime import datetime


class Rain:

    BASEURL="https://api.openweathermap.org/data/2.5/onecall?lat={0}&lon={1}&exclude={2}&appid={3}&units=metric"

    def __init__(self, latitude=45.46, longitude=9.18):

        # read and store the API key for OpenWeather
        with open("OPENWEATHER_KEY") as fkey:
            self.APIKEY = fkey.read().strip()

        # define latitude and longitude (default are Milano lat&long)
        self.latitude = latitude
        self.longitude = longitude

        # string to query only interesting info
        self.exclude = "current,minutely,hourly"


    def getamount(self):

        # http request to get the data
        r = requests.get(self.BASEURL.format(
            self.latitude, self.longitude, self.exclude, self.APIKEY))
        data = r.json()

        # first get the string for the day for which the rain forecast will be extracted
        daystring = datetime.utcfromtimestamp(data["daily"][0]["dt"]).strftime("%d/%m/%Y")

        # extract the amount of rain, in mm
        try:
            rainamount = pprint(data["daily"][0]["rain"])
        except KeyError:
            rainamount = 0.

        return daystring, rainamount

