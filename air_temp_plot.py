#!/usr/bin/env python
# encoding: utf-8
from typing import List
import matplotlib.pyplot as plt

from weather_api import WeatherApi


def plot(date_list: List, high_list: List, low_list: List):
    fig, ax = plt.subplots()
    ax.plot(date_list, high_list, date_list, low_list)
    ax.set_title('nanjing')
    ax.set_xlabel('date')
    ax.set_ylabel('high/low temp ℃')
    ax.grid(True)
    # fig.savefig("assets/air_temp_plot.png", dpi=300)
    plt.show()


def main():
    wApi = WeatherApi()
    r = wApi.get_by_city_name("南京")
    date_list, high_list, low_list = WeatherApi.parse_forecast_list(r)

    # date_list = ['2025-09-15', '2025-09-16', '2025-09-17', '2025-09-18', '2025-09-19', '2025-09-20', '2025-09-21',
    #              '2025-09-22',
    #              '2025-09-23', '2025-09-24', '2025-09-25', '2025-09-26', '2025-09-27', '2025-09-28', '2025-09-29']
    # high_list = [32, 34, 30, 27, 28, 28, 29, 34, 34, 32, 26, 26, 26, 27, 30]
    # low_list = [25, 25, 24, 22, 22, 22, 22, 25, 25, 25, 22, 19, 16, 16, 20]

    plot(date_list, high_list, low_list)


if __name__ == "__main__":
    main()
