# plot_demo

本项目采用 `conda` 作为包管理工具


### 配置 conda 国内源

```shell script
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --set show_channel_urls yes
```

### 切换 python 版本

wrf-python不支持3.11以上版本的python，因此不要使用太高版本的python 

```shell script
conda install -c conda-forge python=3.11
```

### 安装依赖的第三方包

```shell script
conda install -c conda-forge netCDF4 
conda install -c conda-forge cartopy
conda install -c conda-forge wrf-python
conda install -c conda-forge cmaps
```


### conda 运行本项目

  * Air Temperature Chart

    - 通过第三方接口获取城市气温
    - 以日期为X轴, 日最高/低温度为Y轴的图表

      ```shell script
      conda run air_temp_plot.py
      ```

      ![Air Temperature Chart](/assets/air_temp_plot.png)
    
    
  * Vertical Section Chart
     
    - 代码参考自 https://zhuanlan.zhihu.com/p/380626604

      ```shell script
      conda run vertical_plot.py
      ```
    
      ![Vertical Section Chart](/assets/vertical_plot.png)