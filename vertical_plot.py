#!/usr/bin/env python
# encoding: utf-8

import os
import sys

import numpy as np
import netCDF4
import matplotlib.pyplot as plt
import matplotlib.ticker as mp_ticker
from matplotlib.font_manager import FontProperties
from wrf import to_np, getvar, CoordPair, vertcross, interplevel
import cartopy.crs as cartopy_crs
import cartopy.feature as cartopy_feat
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import cmaps
import matplotlib as mpl

# ==============================================================================
# 1. 配置参数 (Configuration Parameters) - 所有可调整的参数都集中在这里
# ==============================================================================
# 文件路径
WRF_FILE_PATH = './wrfout/wrfout_d01_2016-07-12_00_00_00'
OUTPUT_IMAGE_PATH = "assets/vertical_plot.png"
FONT_PATH_SIMSUN = "./fonts/simsun.ttc"
FONT_PATH_TIMES = "./fonts/times.ttf"

# 剖面定义
START_LON, END_LON = 120.2, 121.2
START_LAT, END_LAT = 22.0, 23.0
INTERVAL_LON_FOR_TICKS = 0.2  # X轴刻度的经度间隔

# 气压层定义
BIG_P, SMALL_P, INTERVAL_P = 1000, 700, 50  # 用于Y轴刻度和高度估算

# 绘图参数
FIG_SIZE = (6, 6)  # 调整为更宽一点，给小地图更多空间
DPI = 150
TITLE = '垂直剖面图（温度与风场）'
TEMP_LEVELS = np.arange(10, 40, 2)  # 温度等值线级别，间隔调小一点使 contour 更平滑
QUIVER_SCALE = 120  # 风矢量箭头比例
CBAR_ORIENTATION = 'vertical'

# 小地图(Insets)参数
MAP_EXTENT = [118, 128, 20, 30]
MAP_TICK_INTERVAL = 2


# ==============================================================================
# 2. 初始化和字体设置 (Initialization & Font Settings)
# ==============================================================================
def check_file_exists(filepath):
    """检查文件是否存在"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"错误：文件未找到 -> {filepath}")


# 检查关键文件是否存在
check_file_exists(WRF_FILE_PATH)
check_file_exists(FONT_PATH_SIMSUN)
check_file_exists(FONT_PATH_TIMES)

# 配置字体
Simsun = FontProperties(fname=FONT_PATH_SIMSUN)
Times = FontProperties(fname=FONT_PATH_TIMES)

# 解决负号显示问题和数学公式字体
mpl.rcParams['axes.unicode_minus'] = False
mpl.rcParams['mathtext.fontset'] = 'stix'


# ==============================================================================
# 3. 数据读取和处理 (Data Loading & Processing)
# ==============================================================================
def load_and_process_data(ncfile_path):
    """
    从NetCDF文件读取数据并进行垂直剖面计算。
    """
    print(f"正在读取文件: {ncfile_path}")
    ncfile = netCDF4.Dataset(ncfile_path)

    # 读取基础变量
    tc = getvar(ncfile, 'tc', timeidx=0)
    lat = getvar(ncfile, 'lat')
    lon = getvar(ncfile, 'lon')
    height = getvar(ncfile, 'height')
    hgt = getvar(ncfile, 'HGT')
    ua = getvar(ncfile, 'ua', timeidx=0)
    va = getvar(ncfile, 'va', timeidx=0)
    wa = getvar(ncfile, 'wa', timeidx=0)
    p = getvar(ncfile, 'pressure', timeidx=0)

    # 数据预处理
    height2earth = height - hgt  # 计算离地高度
    wa = wa * 200  # 放大垂直运动信号

    # 定义剖面起点和终点
    startpoint = CoordPair(lat=START_LAT, lon=START_LON)
    endpoint = CoordPair(lat=END_LAT, lon=END_LON)

    # 计算垂直剖面
    print("正在计算垂直剖面...")
    tc_vert = vertcross(tc, p, wrfin=ncfile, start_point=startpoint, end_point=endpoint, latlon=True)
    ua_vert = vertcross(ua, p, wrfin=ncfile, start_point=startpoint, end_point=endpoint, latlon=True)
    va_vert = vertcross(va, p, wrfin=ncfile, start_point=startpoint, end_point=endpoint, latlon=True)
    wa_vert = vertcross(wa, p, wrfin=ncfile, start_point=startpoint, end_point=endpoint, latlon=True)

    ncfile.close()
    return tc_vert, ua_vert, va_vert, wa_vert, height2earth, p


# ==============================================================================
# 4. 风场分量计算和坐标准备 (Wind Component Calculation & Coordinate Prep)
# ==============================================================================
def prepare_plot_data(tc_vert, ua_vert, va_vert, wa_vert, height2earth, p):
    """
    计算沿剖面的风场分量，并准备绘图所需的坐标和标签。
    """
    # 转换为numpy数组
    tc_vert_np = to_np(tc_vert)
    ua_vert_np = to_np(ua_vert)
    va_vert_np = to_np(va_vert)
    wa_vert_np = to_np(wa_vert)
    plist_np = to_np(tc_vert.coords['vertical'])

    # 计算水平风速
    ws_vert = np.sqrt(ua_vert_np ** 2 + va_vert_np ** 2)

    # 计算风向与剖面夹角，并得到沿剖面的切向分量
    wdir_vert = np.arctan2(va_vert_np, ua_vert_np) * 180 / np.pi
    line_angle = np.arctan2(END_LAT - START_LAT, END_LON - START_LON) * 180 / np.pi
    relative_angle = wdir_vert - line_angle
    ws_along_profile = ws_vert * np.cos(np.deg2rad(relative_angle))

    # 提取剖面线上的经纬度坐标
    lonlist, latlist = [], []
    for loc in ua_vert.coords['xy_loc']:
        s = str(loc.values)
        # 使用split方法更健壮
        s = s.split("(")[1].split(")")[0]
        parts = s.split(',')
        lon = float(parts[3].strip().split('=')[1])
        lat = float(parts[2].strip().split('=')[1])
        lonlist.append(lon)
        latlist.append(lat)

    # --- 高度坐标处理 ---
    # 方法A: 沿用你原有的逻辑，取每个气压层的最大离地高度
    hlist = []
    for i in range(BIG_P, SMALL_P - INTERVAL_P, -INTERVAL_P):
        # interplevel会返回一个和height2earth水平维度相同的场
        # np.max取这个气压层上的最大高度，作为该层的代表性高度
        h = np.max(interplevel(height2earth, p, i)).values
        hlist.append(float(h))
    hlist = np.array([int(round(h)) for h in hlist])

    # 方法B: (推荐) 计算沿剖面线各点在指定气压层的高度，然后取平均
    # 这更符合垂直剖面的常规做法
    # h_levels = []
    # for i in range(BIG_P, SMALL_P - INTERVAL_P, -INTERVAL_P):
    #     h_field = interplevel(height2earth, p, i)
    #     h_vert = vertcross(h_field, p, wrfin=ncfile, start_point=startpoint, end_point=endpoint, latlon=True)
    #     h_levels.append(np.mean(to_np(h_vert)))
    # hlist = np.array([int(round(h)) for h in h_levels])

    # 准备X轴刻度标签
    num_ticks = int(round((END_LON - START_LON) / INTERVAL_LON_FOR_TICKS)) + 1
    tick_indices = np.linspace(0, len(lonlist) - 1, num_ticks, dtype=int)

    float_lonlist = [lonlist[i] for i in tick_indices]
    str_lonlist = [f"{round(lonlist[i], 2)}°E\n{round(latlist[i], 2)}°N" for i in tick_indices]

    return {
        'x': lonlist, 'y_pressure': plist_np, 'data_temp': tc_vert_np,
        'u_wind': ws_along_profile, 'v_wind': wa_vert_np,
        'height_m': hlist,
        'xticks_vals': float_lonlist, 'xticks_labels': str_lonlist
    }


# ==============================================================================
# 5. 主绘图函数 (Main Plotting Function)
# ==============================================================================
def create_vertical_cross_section_plot(plot_data):
    """
    根据处理好的数据创建并保存垂直剖面图。
    """
    print("正在绘制图形...")
    fig = plt.figure(figsize=FIG_SIZE, dpi=DPI)

    # --- 主 axes (左侧大图) ---
    ax_main = plt.subplot(1, 1, 1)
    ax_main.set_title(TITLE, fontproperties=Simsun, fontsize=14, y=1.02)

    # 绘制温度等值线填充
    contourf = ax_main.contourf(plot_data['x'], plot_data['y_pressure'], plot_data['data_temp'],
                                levels=TEMP_LEVELS, cmap=cmaps.NCV_jaisnd, extend='both')

    # 绘制风矢量箭头 (水平分量沿剖面，垂直分量为wa)
    ax_main.quiver(plot_data['x'], plot_data['y_pressure'],
                   plot_data['u_wind'], plot_data['v_wind'],
                   pivot='mid', width=0.0015, scale=QUIVER_SCALE, color='k', headwidth=4, alpha=0.8)

    # 设置主坐标轴 (气压)
    ax_main.set_xlim(START_LON, END_LON)
    ax_main.set_ylim(SMALL_P, BIG_P)
    ax_main.invert_yaxis()  # 气压值从上到下增大
    ax_main.set_yticks(np.arange(SMALL_P, BIG_P + INTERVAL_P, INTERVAL_P))
    ax_main.set_ylabel('气压 (hPa)', fontproperties=Simsun, fontsize=12)
    ax_main.grid(color='gray', linestyle=':', linewidth=0.7, axis='y')

    # 设置X轴
    ax_main.set_xticks(plot_data['xticks_vals'])
    ax_main.set_xticklabels(plot_data['xticks_labels'], fontproperties=Times, fontsize=9)
    ax_main.set_xlabel('经纬度坐标', fontproperties=Simsun, fontsize=12)

    # --- 右侧副坐标轴 (离地高度) ---
    ax_height = ax_main.twinx()
    # 修正：直接使用我们计算好的气压层和对应的高度来设置刻度
    pressure_levels_for_height = np.arange(BIG_P, SMALL_P - INTERVAL_P, -INTERVAL_P)
    ax_height.set_yticks(pressure_levels_for_height)
    ax_height.set_yticklabels(plot_data['height_m'], fontproperties=Times, fontsize=9)
    ax_height.set_ylabel('离地高度 (m)', fontproperties=Simsun, fontsize=12)
    ax_height.tick_params(axis='y', colors='darkred', length=3)
    # 确保高度轴的范围和气压轴一致
    ax_height.set_ylim(SMALL_P, BIG_P)
    ax_height.invert_yaxis()

    # --- 颜色条 (Colorbar) ---
    cbar_ax = fig.add_axes([0.9, 0.1, 0.02, 0.6])  # 位置微调

    cb = fig.colorbar(contourf, cax=cbar_ax, orientation=CBAR_ORIENTATION, ticks=TEMP_LEVELS[::2])
    cb.set_label('温度 ($^\circ$C)', fontproperties=Simsun, fontsize=12)
    cb.ax.tick_params(labelsize=10)
    for label in cb.ax.get_yticklabels():
        label.set_fontproperties(Times)

    # --- 小地图 (Inset Map) ---
    ax_map = fig.add_axes([0.83, 0.80, 0.18, 0.18], projection=cartopy_crs.PlateCarree())
    ax_map.add_feature(cartopy_feat.COASTLINE.with_scale("50m"), linewidth=0.7)
    ax_map.add_feature(cartopy_feat.LAND, facecolor='lightgray', alpha=0.5)
    ax_map.set_extent(MAP_EXTENT, crs=cartopy_crs.PlateCarree())

    # 绘制剖面线
    ax_map.plot([START_LON, END_LON], [START_LAT, END_LAT], color='red', linewidth=2)
    ax_map.plot(START_LON, START_LAT, marker='o', color='red', markersize=4)
    ax_map.plot(END_LON, END_LAT, marker='s', color='red', markersize=4)
    ax_map.text(START_LON, START_LAT, 'A', fontproperties=Times, fontsize=10, ha='right')
    ax_map.text(END_LON, END_LAT, "A'", fontproperties=Times, fontsize=10, ha='left')

    # 小地图刻度
    gl = ax_map.gridlines(crs=cartopy_crs.PlateCarree(), draw_labels=True,
                          linewidth=0.5, color='gray', linestyle=':', alpha=0.6)
    gl.xlocator = mp_ticker.FixedLocator(np.arange(MAP_EXTENT[0], MAP_EXTENT[1] + 1, MAP_TICK_INTERVAL))
    gl.ylocator = mp_ticker.FixedLocator(np.arange(MAP_EXTENT[2], MAP_EXTENT[3] + 1, MAP_TICK_INTERVAL))
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 6, 'fontproperties': Times}
    gl.ylabel_style = {'size': 6, 'fontproperties': Times}

    # 调整布局并保存
    plt.tight_layout()
    # 手动微调，防止小地图和颜色条重叠
    plt.subplots_adjust(top=0.78, right=0.80)

    # 确保输出目录存在
    # os.makedirs(os.path.dirname(OUTPUT_IMAGE_PATH), exist_ok=True)
    # plt.savefig(OUTPUT_IMAGE_PATH, dpi=300, bbox_inches='tight')
    # print(f"图像已保存至: {OUTPUT_IMAGE_PATH}")
    plt.show()


# ==============================================================================
# 6. 主执行流程 (Main Execution Flow)
# ==============================================================================
if __name__ == "__main__":
    try:
        # 步骤1: 加载和处理数据
        vert_data = load_and_process_data(WRF_FILE_PATH)

        # 步骤2: 准备绘图数据
        plot_ready_data = prepare_plot_data(*vert_data)

        # 步骤3: 绘图
        create_vertical_cross_section_plot(plot_ready_data)

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"程序运行出错: {e}")
