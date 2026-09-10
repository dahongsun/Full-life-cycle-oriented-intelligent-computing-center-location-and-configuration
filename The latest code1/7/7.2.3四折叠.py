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
    "GDP_Growth": [0.3546, 0.3620, 0.3392, 0.3816, 0.3216, 0.3625, 0.3375] # 新增 GDP 数据
}

df = pd.DataFrame(data)

# 2. 计算比率与变动幅度
df["Total_Racks"] = df["East_Racks"] + df["Central_Racks"] + df["West_Racks"]
df["East_Ratio"] = df["East_Racks"] / df["Total_Racks"]
df["Central_Ratio"] = df["Central_Racks"] / df["Total_Racks"]
df["West_Ratio"] = df["West_Racks"] / df["Total_Racks"]

# 计算相对于基准情景 (索引0) 的变动百分比
base_total = df.loc[0, "Total_Cost"]
base_carbon = df.loc[0, "Carbon_Cost"]
base_gdp = df.loc[0, "GDP_Growth"]

df["Total_Cost_Change"] = (df["Total_Cost"] - base_total) / base_total * 100
df["Carbon_Cost_Change"] = (df["Carbon_Cost"] - base_carbon) / base_carbon * 100
df["GDP_Change"] = (df["GDP_Growth"] - base_gdp) / base_gdp * 100 # GDP变动百分比

# 3. 绘图
fig, ax_bars = plt.subplots(figsize=(15, 8)) #稍微加宽一点，给右侧两个轴留空间

# 关闭网格线 (如您要求)
ax_bars.grid(False)

# --- 绘制堆叠柱状图 (背景) ---
x = np.arange(len(df))
bar_width = 0.5
p1 = ax_bars.bar(x, df["East_Racks"], width=bar_width, label='东部机架占比', color='#4e79a7', alpha=0.4)
p2 = ax_bars.bar(x, df["Central_Racks"], width=bar_width, bottom=df["East_Racks"], label='中部机架占比', color='#f28e2b', alpha=0.4)
p3 = ax_bars.bar(x, df["West_Racks"], width=bar_width, bottom=df["East_Racks"]+df["Central_Racks"], label='西部机架占比', color='#59a14f', alpha=0.4)

# 在柱子上添加比率文字
for i in range(len(df)):
    if df.loc[i, "East_Racks"] > 0:
        ax_bars.text(i, df.loc[i, "East_Racks"]/2, f'{df.loc[i, "East_Ratio"]:.1%}',
                     ha='center', va='center', fontsize=9, color='black', fontweight='bold')
    if df.loc[i, "Central_Racks"] > 0:
        y_pos = df.loc[i, "East_Racks"] + df.loc[i, "Central_Racks"]/2
        ax_bars.text(i, y_pos, f'{df.loc[i, "Central_Ratio"]:.1%}',
                     ha='center', va='center', fontsize=9, color='black', fontweight='bold')
    if df.loc[i, "West_Racks"] > 0:
        y_pos = df.loc[i, "East_Racks"] + df.loc[i, "Central_Racks"] + df.loc[i, "West_Racks"]/2
        ax_bars.text(i, y_pos, f'{df.loc[i, "West_Ratio"]:.1%}',
                     ha='center', va='center', fontsize=9, color='black', fontweight='bold')

# 隐藏柱状图的Y轴
ax_bars.set_yticks([])

# --- 配置多Y轴折线图 ---
ax_carbon = ax_bars.twinx()  # 左轴
ax_total = ax_bars.twinx()   # 右轴1
ax_gdp = ax_bars.twinx()     # 右轴2 (需要偏移)

# 1. 设置碳成本轴 (左侧)
ax_carbon.yaxis.tick_left()
ax_carbon.yaxis.set_label_position("left")
ax_carbon.spines["left"].set_position(("axes", 0))
ax_carbon.set_frame_on(True)
ax_carbon.patch.set_visible(False)

# 2. 设置总成本轴 (右侧内) - 默认位置

# 3. 设置GDP轴 (右侧外 - 偏移)
ax_gdp.spines["right"].set_position(("axes", 1.08)) # 向右偏移 8% 的距离
ax_gdp.set_frame_on(True)
ax_gdp.patch.set_visible(False)

# --- 绘制三条折线 ---
# 碳成本 (红)
l1, = ax_carbon.plot(x, df["Carbon_Cost_Change"], color='#d62728', marker='o', linewidth=2.5, label='碳成本变动 (%)', zorder=10)
# 总成本 (蓝)
l2, = ax_total.plot(x, df["Total_Cost_Change"], color='#1f77b4', marker='s', linewidth=2.5, linestyle='--', label='总成本变动 (%)', zorder=10)
# GDP (紫)
l3, = ax_gdp.plot(x, df["GDP_Change"], color='#9467bd', marker='^', linewidth=2.5, linestyle='-.', label='GDP增幅变动 (%)', zorder=10)

# --- 设置轴标签和颜色 ---
# 碳成本
ax_carbon.set_ylabel('碳成本变动 (%)', color='#d62728', fontsize=12, fontweight='bold')
ax_carbon.tick_params(axis='y', labelcolor='#d62728')
ax_carbon.set_ylim(-5, 8)

# 总成本
ax_total.set_ylabel('总成本变动 (%)', color='#1f77b4', fontsize=12, fontweight='bold')
ax_total.tick_params(axis='y', labelcolor='#1f77b4')
ax_total.set_ylim(-12, 10)

# GDP
ax_gdp.set_ylabel('GDP增幅变动 (%)', color='#9467bd', fontsize=12, fontweight='bold')
ax_gdp.tick_params(axis='y', labelcolor='#9467bd')
# 为了不让线挤在一起，可以微调 ylim
ax_gdp.set_ylim(-10, 10)

# 添加0刻度参考线 (基于左轴)
ax_carbon.axhline(0, color='gray', linewidth=1, linestyle=':', alpha=0.5)

# 设置X轴
ax_bars.set_xticks(x)
ax_bars.set_xticklabels(df["Scenario"], rotation=15, fontsize=11)

# --- 合并图例 (6个元素) ---
lines = [p1, p2, p3, l1, l2, l3]
labels = [l.get_label() for l in lines]
# 图例放到底部
ax_bars.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=10)

plt.title('多情景敏感性分析：布局结构 vs 成本效益 vs 经济增长', fontsize=16, pad=20)
plt.tight_layout()
plt.show()