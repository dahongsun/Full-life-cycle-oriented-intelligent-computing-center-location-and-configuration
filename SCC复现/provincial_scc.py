# -*- coding: utf-8 -*-
"""
国家 + 各省 SCC 轨迹（2026-2050）。

方法：省级 SCC = 全国 SCC × 各省 GDP 份额。
依据：Ricke/DJO 损害 ∝ δ·ΔT·GDP；全国统一温升、各省人均GDP均≫阈值$2449（统一 δ=-0.191）
      → 损害按 GDP 份额在各省间分配，各省 SCC 之和 = 全国 SCC（损害归宿分解，与 Wang 省级口径一致）。
输入：
  out/scc_china_trajectory_MAIN_jiang.csv  全国 SCC（姜彤主，Ramsey 等各档）
  data/1_省级SSP2_GDP人口.csv               各省逐年 人均GDP(CNY) + 人口 → GDP_p = 人均×人口
输出：
  out/scc_provincial_trajectory.csv         全国 + 31 省 逐年 SCC（USD2010/tCO2，Ramsey 主口径）
  out/scc_provincial_share.csv              各省 GDP 份额（%）
  out/fig_scc_provincial_stacked.png        堆叠面积图（各省叠加 = 全国总高）
  out/fig_scc_provincial_lines.png          主要省份折线 + 全国
"""
import os, csv
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

USDCNY = 6.77
YEARS = list(range(2025, 2101))
EN = {'广东':'Guangdong','江苏':'Jiangsu','山东':'Shandong','浙江':'Zhejiang','河南':'Henan',
      '四川':'Sichuan','福建':'Fujian','湖北':'Hubei','湖南':'Hunan','上海':'Shanghai',
      '安徽':'Anhui','河北':'Hebei','北京':'Beijing','陕西':'Shaanxi','江西':'Jiangxi',
      '重庆':'Chongqing','辽宁':'Liaoning','云南':'Yunnan','广西':'Guangxi','山西':'Shanxi',
      '内蒙古':'Inner Mongolia','贵州':'Guizhou','天津':'Tianjin','黑龙江':'Heilongjiang',
      '新疆':'Xinjiang','吉林':'Jilin','甘肃':'Gansu','海南':'Hainan','宁夏':'Ningxia',
      '青海':'Qinghai','西藏':'Tibet'}

# ---------- 全国 SCC（Ramsey 主口径）----------
rows = list(csv.reader(open('out/scc_china_trajectory_MAIN_jiang.csv', encoding='utf-8-sig')))
hdr = rows[0]; ci = hdr.index('Ramsey(ρ0.692,η1.07)')
nat = {int(r[0]): float(r[ci]) for r in rows[1:]}   # year -> 全国 SCC USD2010/tCO2

# ---------- 各省 GDP（= 人均×人口）----------
gdp = {}            # (province, year) -> GDP (任意一致单位)
provs = []
for r in csv.reader(open('data/1_省级SSP2_GDP人口.csv', encoding='utf-8-sig')):
    if not r or r[0] == 'province' or r[1] == 'year': continue
    p, y = r[0], int(r[1])
    if y in YEARS:
        gdp[(p, y)] = float(r[2]) * float(r[3])
        if p not in provs: provs.append(p)

# ---------- 份额 + 省级 SCC ----------
share = {}          # (p, y) -> 份额
pscc = {}           # (p, y) -> 省级 SCC USD2010/tCO2
for y in YEARS:
    tot = sum(gdp[(p, y)] for p in provs)
    for p in provs:
        s = gdp[(p, y)] / tot
        share[(p, y)] = s
        pscc[(p, y)] = nat[y] * s

# 校验：各省之和 = 全国
chk = max(abs(sum(pscc[(p, y)] for p in provs) - nat[y]) for y in YEARS)
print(f"校验 Σ省 = 全国，最大残差 {chk:.2e}（应≈0）")

# 按平均份额排序，取前 8 高亮，其余并为 Others
order = sorted(provs, key=lambda p: -np.mean([share[(p, y)] for y in YEARS]))
TOP = order[:8]; OTH = order[8:]

# ---------- 输出 CSV（全国 + 31 省，USD2010/tCO2）----------
with open('out/scc_provincial_trajectory.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['排放年', '全国'] + order + ['全国_CNY@6.77'])
    for y in YEARS:
        w.writerow([y, round(nat[y], 2)] + [round(pscc[(p, y)], 3) for p in order] + [round(nat[y]*USDCNY, 1)])
with open('out/scc_provincial_share.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['排放年'] + order)
    for y in YEARS:
        w.writerow([y] + [round(share[(p, y)]*100, 2) for p in order])

# ---------- 图1：堆叠面积（= 全国）----------
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']; plt.rcParams['axes.unicode_minus'] = False
fig, ax = plt.subplots(figsize=(8.4, 5.4))
bands = [[pscc[(p, y)] for y in YEARS] for p in TOP]
others = [sum(pscc[(p, y)] for p in OTH) for y in YEARS]
labels = [EN[p] for p in TOP] + ['Others (%d provinces)' % len(OTH)]
cmap = plt.cm.tab20(np.linspace(0, 1, len(TOP)+1))
ax.stackplot(YEARS, *bands, others, labels=labels, colors=cmap, alpha=0.9)
ax.plot(YEARS, [nat[y] for y in YEARS], 'k-', lw=2.2, label='National total')
ax.set_xlim(2025, 2100); ax.set_xlabel('Emission year'); ax.set_ylabel('SCC (USD2010 / tCO$_2$)')
ax.set_title('Provincial decomposition of China SCC, 2025–2100\n(stacked bands sum to the national SCC; Ramsey ρ=0.692%, η=1.07)')
ax.legend(fontsize=7.5, loc='upper left', ncol=2, framealpha=0.9); ax.grid(alpha=0.2)
fig.tight_layout(); fig.savefig('out/fig_scc_provincial_stacked.png', dpi=170)

# ---------- 图2：主要省份折线 ----------
fig, ax = plt.subplots(figsize=(8.4, 5.4))
for i, p in enumerate(TOP):
    ax.plot(YEARS, [pscc[(p, y)] for y in YEARS], lw=2, color=plt.cm.tab10(i % 10), label=EN[p])
for p in OTH:
    ax.plot(YEARS, [pscc[(p, y)] for y in YEARS], lw=0.7, color='#cccccc', zorder=0)
ax.set_xlim(2025, 2100); ax.set_xlabel('Emission year'); ax.set_ylabel('Provincial SCC (USD2010 / tCO$_2$)')
ax.set_title('Provincial SCC trajectories, 2025–2100 (top 8 labelled; grey = other provinces)')
ax.legend(fontsize=8, loc='upper left', ncol=2, framealpha=0.9); ax.grid(alpha=0.2)
fig.tight_layout(); fig.savefig('out/fig_scc_provincial_lines.png', dpi=170)

print('[输出] out/scc_provincial_trajectory.csv, out/scc_provincial_share.csv')
print('[输出] out/fig_scc_provincial_stacked.png, out/fig_scc_provincial_lines.png')
print(f"\n前8省（2026 SCC USD2010/tCO2 与份额）：")
for p in TOP:
    print(f"  {EN[p]:<16}{p:<5} 2026={pscc[(p,2026)]:6.2f}  2050={pscc[(p,2050)]:6.2f}  份额{share[(p,2026)]*100:4.1f}%")
print(f"  Others({len(OTH)}省)        2026={others[0]:6.2f}  2050={others[-1]:6.2f}")
print(f"  全国 National          2026={nat[2026]:6.2f}  2050={nat[2050]:6.2f}")
