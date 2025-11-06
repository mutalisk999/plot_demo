#!/usr/bin/env python
# encoding: utf-8
import netCDF4 as nc
from wrf import to_np, getvar, CoordPair, vertcross, interplevel
import cartopy.crs as ccrs
import cartopy.feature as cfeat
import matplotlib.pyplot as plt
import cmaps
import matplotlib as mpl
import matplotlib.ticker as mticker
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from matplotlib.font_manager import FontProperties
import numpy as np

Simsun = FontProperties(fname="./fonts/simsun.ttc")
Times = FontProperties(fname="./fonts/times.ttf")
mpl.rcParams['axes.unicode_minus'] = False
config = {
    "mathtext.fontset": 'stix',
}
mpl.rcParams.update(config)

# 初始数据
big_p, small_p, interval_p = 1000, 700, 50
start_lon, end_lon, interval_lon = 120.2, 121.2, 0.2
start_lat, end_lat = 22, 23
# 插值初始点与末点的坐标数据
startpoint = CoordPair(lat=start_lat, lon=start_lon)
endpoint = CoordPair(lat=end_lat, lon=end_lon)
ncfile = nc.Dataset('./wrfout/wrfout_d01_2016-07-12_00_00_00')
# 读取及初步处理数据
tc = getvar(ncfile, 'tc', timeidx=0)
lat = getvar(ncfile, 'lat')
lon = getvar(ncfile, 'lon')
height = getvar(ncfile, 'height')
hgt = getvar(ncfile, 'HGT')
height2earth = height - hgt
ua = getvar(ncfile, 'ua', timeidx=0)
va = getvar(ncfile, 'va', timeidx=0)
wa = getvar(ncfile, 'wa', timeidx=0)
wa = wa * 200
p = getvar(ncfile, 'pressure', timeidx=0)
# 插值数据
tc_vert = vertcross(tc, p, wrfin=ncfile, start_point=startpoint, end_point=endpoint, latlon=True)
ua_vert = vertcross(ua, p, wrfin=ncfile, start_point=startpoint, end_point=endpoint, latlon=True)
va_vert = vertcross(va, p, wrfin=ncfile, start_point=startpoint, end_point=endpoint, latlon=True)
wa_vert = vertcross(wa, p, wrfin=ncfile, start_point=startpoint, end_point=endpoint, latlon=True)
# 计算风速
ws_vert = np.sqrt(ua_vert ** 2 + va_vert ** 2)
# 计算风向夹角
wdir_vert = np.arctan2(va_vert, ua_vert) * 180 / np.pi
line_angel = np.arctan2(end_lat - start_lat, end_lon - start_lon) * 180 / np.pi
vl_angel = wdir_vert - line_angel
# vl_angel = np.cos(vl_angel / 180 * np.pi)
vl_angel = np.cos(np.deg2rad(vl_angel))
ws_vert = ws_vert * vl_angel

lonlist, latlist, hlist = [], [], []
plist = to_np(va_vert.coords['vertical'])
# 生成插值数据的经纬度列表
for i in range(len(ua_vert.coords['xy_loc'])):
    s = str(ua_vert.coords['xy_loc'][i].values)
    lonlist.append(float(s[s.find('lon=') + 4:s.find('lon=') + 11]))
    latlist.append(float(s[s.find('lat=') + 4:s.find('lat=') + 11]))
# 插值数据对应气压的离地高度
for i in range(big_p, small_p - interval_p, -interval_p):
    hlist.append(float(np.max(interplevel(height2earth, p, i)).values))
hlist = np.array([int(i) for i in hlist])  # 简单地取整
str_lonlist, float_lonlist = [], []
a = np.mgrid[
    0:len(lonlist) - 1:complex(str(int(round((end_lon + interval_lon - start_lon) / interval_lon))) + 'j')]  # 生成位置列表
a = np.around(a, decimals=0)  # 四舍五入取整
# 处理插入x轴的刻度标签
for i in range(int((end_lon + interval_lon - start_lon) / interval_lon)):
    float_lonlist.append(lonlist[int(a[i])])
    lo, la = round(lonlist[int(a[i])], 2), round(latlist[int(a[i])], 2)
    str_lonlist.append(str(lo) + '°E' + "\n" + str(la) + '°N')

fig = plt.figure(figsize=(5, 5), dpi=150)
axe = plt.subplot(1, 1, 1)
axe.set_title('垂直剖面图，臭氧浓度与风向', fontproperties=Simsun, fontsize=12, y=1.05)
axe.set_xlim(start_lon, end_lon)
axe.set_ylim(small_p, big_p)
axe.invert_yaxis()  # 翻转纵坐标
axe.grid(color='gray', linestyle=':', linewidth=0.7, axis='y')
plt.xticks(float_lonlist, str_lonlist, fontsize=8, color='k')
axe.set_xlabel('经纬度坐标', fontproperties=Simsun, fontsize=12)
axe.get_xaxis().set_visible('True')
plt.yticks(fontsize=8, color='k')
axe.get_yaxis().set_visible('True')
axe.set_yticks(np.arange(small_p, big_p, interval_p))
axe.set_ylabel('气压$\mathrm{(hPa))}$', fontproperties=Simsun, fontsize=12)
axe.tick_params(length=2)
labels = axe.get_xticklabels() + axe.get_yticklabels()
[label.set_fontproperties(FontProperties(fname="./fonts/times.ttf", size=8)) for label in labels]

axe.grid(color='gray', linestyle=":", linewidth=0.7, axis='y')

tc_level = np.arange(10, 40, 3)
contourf = axe.contourf(lonlist, plist, tc_vert, levels=tc_level, cmap=cmaps.NCV_jaisnd, extend='neither')
axe.quiver(lonlist, plist, ws_vert, wa_vert, pivot='mid',
           width=0.001, scale=120, color='k', headwidth=4,
           alpha=1)

fig.subplots_adjust(right=0.78)
rect = [0.95, 0.07, 0.01, 0.57]  # 分别代表，水平位置，垂直位置，水平宽度，垂直宽度
cbar_ax = fig.add_axes(rect)
cb = fig.colorbar(contourf, drawedges=True, ticks=tc_level, cax=cbar_ax, orientation='vertical', spacing='uniform')
cb.set_label('温度（$\mathrm{^oC}$）', fontproperties=Simsun, fontsize=12)
cb.ax.tick_params(length=0)
labels = cb.ax.get_xticklabels() + cb.ax.get_yticklabels()
[label.set_fontproperties(FontProperties(fname="./fonts/times.ttf", size=10)) for label in labels]

axe1 = fig.add_axes([0.9, 0.69, 0.2, 0.2], projection=ccrs.PlateCarree())
axe1.add_feature(cfeat.COASTLINE.with_scale("50m"), linewidth=0.7, color='k')
axe1.add_feature(cfeat.RIVERS.with_scale("50m"))
axe1.add_feature(cfeat.OCEAN.with_scale("50m"))
axe1.add_feature(cfeat.LAKES.with_scale("50m"))
axe1.set_extent([118, 128, 20, 30], crs=ccrs.PlateCarree())

gl = axe1.gridlines(crs=ccrs.PlateCarree(), draw_labels=False, linewidth=0.5, color='gray', linestyle=':')
gl.xlocator = mticker.FixedLocator(np.arange(118, 128, 2))
gl.ylocator = mticker.FixedLocator(np.arange(20, 30, 2))
axe1.set_xticks(np.arange(118, 128 + 2, 2), crs=ccrs.PlateCarree())
axe1.set_yticks(np.arange(20, 30 + 2, 2), crs=ccrs.PlateCarree())
plt.tick_params(top=True, bottom=True, left=True, right=True)  # tick刻度显示
plt.tick_params(labeltop=True, labelleft=True, labelright=True, labelbottom=True)  # tick标签显示
axe1.xaxis.set_major_formatter(LongitudeFormatter())
axe1.yaxis.set_major_formatter(LatitudeFormatter())
labels = axe1.get_xticklabels() + axe1.get_yticklabels()
[label.set_fontproperties(FontProperties(fname="./fonts/times.ttf", size=6)) for label in labels]

axe1.plot([lonlist[0], lonlist[-1]], [latlist[0], latlist[-1]], color='red', linewidth=1.5, linestyle='-')
axe1.plot(lonlist[0], latlist[0], marker='o', color='red', markersize=2.5)
axe1.plot(lonlist[-1], latlist[-1], marker='o', color='red', markersize=2.5)
axe1.text(lonlist[0], latlist[0], 'A', fontproperties=FontProperties(fname="./fonts/times.ttf", size=8))
axe1.text(lonlist[-1], latlist[-1], 'A' + "'",
          fontproperties=FontProperties(fname="./fonts/times.ttf", size=8))

axe_sub = axe.twinx()
axe_sub.set_ylim(hlist[0], hlist[-1])
axe_sub.set_yticks(np.mgrid[hlist[0]:hlist[-1]:complex(str(int(hlist.shape[0])) + 'j')])
round_hlist = np.around(hlist, -1)
axe_sub.set_yticklabels(round_hlist)
axe_sub.set_ylabel('离地高度$\mathrm{(m))}$', fontproperties=Simsun, fontsize=12)
axe_sub.tick_params(labelcolor='black', length=3)
labels = axe_sub.get_xticklabels() + axe_sub.get_yticklabels()
[label.set_fontproperties(FontProperties(fname="./fonts/times.ttf", size=8)) for label in labels]

plt.show()
