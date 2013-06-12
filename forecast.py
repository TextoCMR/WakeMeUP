# coding=utf-8

import os
import sys
import json
import requests
from datetime import datetime


class ForecastClient(object):
    """
        A simple client for Forecast.io's API
    """
    def __init__(self, time_zone):
        super(ForecastClient, self).__init__()

        self.API_KEY = os.environ["FORECAST_API_KEY"]
        self.desired_time_zone = time_zone

    def get_forecast(self, latitude, longitude):

        endpoint = "https://api.forecast.io/forecast/{api_key}/{lat},{lon}".format(api_key=self.API_KEY, lat=latitude, lon=longitude)
        r = requests.get(endpoint)
        j = json.loads(r.text)
        self.forecast_offset = j.get("offset")
        return self.interpret_forecast(j)

    def interpret_forecast(self, forecast):

        overall_summary = ""

        # start with daily summary
        daily_summary = forecast.get("hourly", {}).get("summary", "")
        overall_summary = daily_summary

        if len(overall_summary) > 135:
            return overall_summary  # no room for high temp info

        # add high temp information
        daily_high_temp = -1000
        daily_high_time = None
        for hour in forecast.get("hourly", {}).get("data", [])[:24]:
            hour_temp = hour.get("temperature") or -1000
            if hour_temp > daily_high_temp:
                daily_high_temp = hour_temp
                if hour.get("time"):
                    daily_high_time = datetime.fromtimestamp(hour.get("time"))

        # pretty print the hour of the high temp
        daily_high_hour = self.convert_hour_to_local(daily_high_time.hour)
        if daily_high_hour == 0:
            hour_str = "midnight"
        elif daily_high_hour == 12:
            hour_str = "noon"
        elif daily_high_hour > 12:
            daily_high_hour = daily_high_hour - 12
            hour_str = "{hour}pm".format(hour=daily_high_hour)
        else:
            hour_str = "{hour}am".format(hour=daily_high_hour)

        temp_summary = "High of {temp} at {hour_str}.".format(
            temp=self.format_temperature(daily_high_temp),
            hour_str=hour_str
        )

        overall_summary = overall_summary + " " + temp_summary

        # add current conditions info
        current_temp = forecast.get("currently", {}).get("temperature", None)
        current_summary = forecast.get("minutely", {}).get("summary", "")

        if current_summary and current_temp and len(overall_summary) < 100:
            overall_summary = "Currently {temp}, {summary} {the_rest}".format(
                temp=self.format_temperature(current_temp),
                summary=current_summary.lower(),
                the_rest=overall_summary
            )
        elif current_temp and len(overall_summary) < 145:
            overall_summary = "Currently {temp}. {the_rest}".format(
                temp=self.format_temperature(current_temp),
                the_rest=overall_summary
            )

        return overall_summary

    def convert_hour_to_local(self, hour):
        diff = int(self.desired_time_zone) - self.forecast_offset
        return hour + diff

    @staticmethod
    def format_temperature(temp):
        return u"{temp}".format(temp=int(round(temp)))
        # return u"{temp}°".format(temp=int(round(temp)))


if __name__ == "__main__":
    f = ForecastClient("-4")
    print f.get_forecast(42.36, -71.10)
