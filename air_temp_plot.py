#!/usr/bin/env python
# encoding: utf-8
from typing import List
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from weather_api import WeatherApi

font_prop = FontProperties(fname="./fonts/simsun.ttc")


def plot(date_list: List, high_list: List, low_list: List):
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

    ax.set_title('Air Temperature Chart (南京)', fontproperties=font_prop, fontsize=20)
    ax.set_xlabel('日期', fontproperties=font_prop, fontsize=15)
    ax.set_ylabel('高温/低温 (℃)', fontproperties=font_prop, fontsize=15)
    ax.grid(True)
    ax.plot(date_list, high_list, date_list, low_list)

    # fig.savefig("assets/air_temp_plot.png", dpi=300)
    plt.show()


def main():
    wApi = WeatherApi()
    r = wApi.get_by_city_name("南京")
    date_list, high_list, low_list = WeatherApi.parse_forecast_list(r)

    plot(date_list, high_list, low_list)


if __name__ == "__main__":
    main()
