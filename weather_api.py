#!/usr/bin/env python
# encoding: utf-8


from typing import Optional, Dict, Tuple, List
import json
import requests


class WeatherApi(object):
    def __init__(self):
        self.url_tpl = "http://t.weather.itboy.net/api/weather/city/{}"
        self.session = requests.Session()
        self.session.trust_env = False

        obj = json.loads(open("city.json", "r", encoding="utf-8").read())
        self.city_map = dict()
        for province in obj.get("城市代码"):
            for city in province.get("市"):
                self.city_map[city.get("市名")] = city.get("编码")

    def get_by_city_key(self, city_key: str) -> Optional[Dict]:
        url = self.url_tpl.format(city_key)
        resp = self.session.get(url)
        return resp.json()

    def get_by_city_name(self, city_name: str) -> Optional[Dict]:
        city_key = self.city_map.get(city_name)
        if city_key is None:
            return None

        return self.get_by_city_key(city_key=city_key)

    @staticmethod
    def parse_forecast_list(resp_dict: Dict) -> Tuple[List, List, List]:
        forecast_list = resp_dict.get("data").get("forecast")
        date_list = list(map(lambda x: x.get("ymd").split("-", 1)[1].replace("-", "/"), forecast_list))
        high_list = list(map(lambda x: int(x.get("high").split()[1].rstrip("℃")), forecast_list))
        low_list = list(map(lambda x: int(x.get("low").split()[1].rstrip("℃")), forecast_list))
        return date_list, high_list, low_list


if __name__ == "__main__":
    wApi = WeatherApi()
    r = wApi.get_by_city_name("南京")
    print(r)

    l = WeatherApi.parse_forecast_list(r)
    print(l)
