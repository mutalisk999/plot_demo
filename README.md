# plot_demo

本项目采用pipenv作为包依赖管理

### pipenv 安装
```shell script
pip install pipenv
```

### pipenv 依赖库安装
```shell script
pipenv lock
pipenv install
```


### pipenv 运行本项目


* Air Temperature Chart

    - 通过第三方接口获取城市气温
    - 以日期为X轴, 日最高/低温度为Y轴的图表

    ```shell script
    pipenv run python air_temp_plot.py
    ```

    ![Air Temperature Chart](/assets/air_temp_plot.png)