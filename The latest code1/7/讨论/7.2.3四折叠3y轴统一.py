import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 1. 准备数据
data = {
    "Scenario": [
        "基准情景",
        "中部火电+20%",
        "中部绿电-20%",
        "东部火电+20%",
        "东部绿电-20%",
        "西部火电+20%",
        "西部绿电-20%"
    ],
    "East_Racks": [243000, 260000, 0, 0, 430000, 243000, 120000],
    "Central_Racks": [503000, 280000, 832000, 599000, 290000, 513000, 320000],
    "West_Racks": [898000, 1105000, 805000, 1048000, 898000, 885000, 1211000],
    "Total_Cost": [6.61e12, 6.77e12, 6.40e12, 7.08e12, 6.09e12, 6.74e12, 6.44e12],
    "Carbon_Cost": [1.008e12, 1.020e12, 1.033e12, 1.006e12, 1.032e12, 1.004e12, 1.064e12],
    "GDP_Growth": [0.3546, 0.3620, 0.3392, 0.3816, 0.3216, 0.3625, 0.3375]
}

df = pd.DataFrame(data)

# 2. 计算比率与变动幅度
df["Total_Racks"] = df["East_Racks"] + df["Central_Racks"] + df["West_Racks"]
df["East_Ratio"] = df["East_Racks"] / df["Total_Racks"]
df["Central_Ratio"] = df["Central_Racks"] / df["Total_Racks"]
df["West_Ratio"] = df["West_Racks"] / df["Total_Racks"]

# 计算变动百分比
base_total = df.loc[0, "Total_Cost"]
base_carbon = df.loc[0, "Carbon_Cost"]
base_gdp = df.loc[0, "GDP_Growth"]

df["Total_Cost_Change"] = (df["Total_Cost"] - base_total) / base_total * 100
df["Carbon_Cost_Change"] = (df["Carbon_Cost"] - base_carbon) / base_carbon * 100
df["GDP_Change"] = (df["GDP_Growth"] - base_gdp) / base_gdp * 100

# 3. 绘图
fig, ax_lines = plt.subplots(figsize=(14, 8))

# 创建一个共享X轴的副轴用于画背景柱状图
ax_bars = ax_lines.twinx()

# 关闭网格线
ax_lines.grid(False)
ax_bars.grid(False)

# --- 绘制堆叠柱状图 (背景：使用 ax_bars) ---
x = np.arange(len(df))
bar_width = 0.5

# 为了让柱状图不遮挡折线，设置较低的透明度和zorder
p1 = ax_bars.bar(x, df["East_Racks"], width=bar_width, label='东部机架占比', color='#4e79a7', alpha=0.3)
p2 = ax_bars.bar(x, df["Central_Racks"], width=bar_width, bottom=df["East_Racks"], label='中部机架占比', color='#f28e2b', alpha=0.3)
p3 = ax_bars.bar(x, df["West_Racks"], width=bar_width, bottom=df["East_Racks"]+df["Central_Racks"], label='西部机架占比', color='#59a14f', alpha=0.3)

# 在柱子上添加比率文字
for i in range(len(df)):
    if df.loc[i, "East_Racks"] > 0:
        ax_bars.text(i, df.loc[i, "East_Racks"]/2, f'{df.loc[i, "East_Ratio"]:.1%}',
                     ha='center', va='center', fontsize=9, color='black', alpha=0.6)
    if df.loc[i, "Central_Racks"] > 0:
        y_pos = df.loc[i, "East_Racks"] + df.loc[i, "Central_Racks"]/2
        ax_bars.text(i, y_pos, f'{df.loc[i, "Central_Ratio"]:.1%}',
                     ha='center', va='center', fontsize=9, color='black', alpha=0.6)
    if df.loc[i, "West_Racks"] > 0:
        y_pos = df.loc[i, "East_Racks"] + df.loc[i, "Central_Racks"] + df.loc[i, "West_Racks"]/2
        ax_bars.text(i, y_pos, f'{df.loc[i, "West_Ratio"]:.1%}',
                     ha='center', va='center', fontsize=9, color='black', alpha=0.6)

# 隐藏柱状图的Y轴 (右轴)
ax_bars.set_yticks([])

# --- 绘制折线图 (前景：使用 ax_lines) ---
# 碳成本 (红)
l1, = ax_lines.plot(x, df["Carbon_Cost_Change"], color='#d62728', marker='o', linewidth=3, label='碳成本变动 (%)', zorder=10)
# 总成本 (蓝)
l2, = ax_lines.plot(x, df["Total_Cost_Change"], color='#1f77b4', marker='s', linewidth=3, linestyle='--', label='总成本变动 (%)', zorder=10)
# GDP (紫)
l3, = ax_lines.plot(x, df["GDP_Change"], color='#9467bd', marker='^', linewidth=3, linestyle='-.', label='GDP增幅变动 (%)', zorder=10)

# --- 设置左侧唯一 Y 轴 ---
ax_lines.set_ylabel('变动 (%)', color='black', fontsize=12, fontweight='bold')
ax_lines.set_ylim(-10, 10)  # 设置固定范围
# 绘制 0 基准线
ax_lines.axhline(0, color='black', linewidth=1, linestyle='-', alpha=0.5)

# 设置 X 轴
ax_lines.set_xticks(x)
ax_lines.set_xticklabels(df["Scenario"], rotation=15, fontsize=11)

# --- 合并图例 ---
lines = [p1, p2, p3, l1, l2, l3]
labels = [l.get_label() for l in lines]
ax_lines.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)

plt.title('多情景敏感性分析：结构与指标变动', fontsize=16, pad=20)
plt.tight_layout()
plt.show()