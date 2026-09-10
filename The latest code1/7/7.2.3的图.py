import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 设置中文字体 (请根据您的系统调整，如 Mac 可用 'Arial Unicode MS')
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
    "Carbon_Cost": [1.008e12, 1.020e12, 1.033e12, 1.006e12, 1.032e12, 1.004e12, 1.064e12]
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
df["Total_Cost_Change"] = (df["Total_Cost"] - base_total) / base_total * 100
df["Carbon_Cost_Change"] = (df["Carbon_Cost"] - base_carbon) / base_carbon * 100

# 3. 绘图
fig, ax_bars = plt.subplots(figsize=(14, 8))
ax_bars.grid(False)  # <--- 核心修改：这会关闭背景里所有的白色横线
#ax_bars.grid(False)  # <--- 新增这行：删除横向网格线
#ax_bars.grid(True, axis='y', alpha=1) # 开启Y轴网格，设置透明度
#ax_bars.set_axisbelow(True)             # <--- 关键：将网格线放在柱状图图层下方
# --- 绘制堆叠柱状图 (背景) ---
x = np.arange(len(df))
bar_width = 0.5
p1 = ax_bars.bar(x, df["East_Racks"], width=bar_width, label='东部机架占比', color='#4e79a7', alpha=0.5)
p2 = ax_bars.bar(x, df["Central_Racks"], width=bar_width, bottom=df["East_Racks"], label='中部机架占比', color='#f28e2b', alpha=0.5)
p3 = ax_bars.bar(x, df["West_Racks"], width=bar_width, bottom=df["East_Racks"]+df["Central_Racks"], label='西部机架占比', color='#59a14f', alpha=0.5)

# 在柱子上添加比率文字
for i in range(len(df)):
    # 东部文字
    if df.loc[i, "East_Racks"] > 0:
        ax_bars.text(i, df.loc[i, "East_Racks"]/2, f'{df.loc[i, "East_Ratio"]:.1%}',
                     ha='center', va='center', fontsize=9, color='black', fontweight='bold')
    # 中部文字
    if df.loc[i, "Central_Racks"] > 0:
        y_pos = df.loc[i, "East_Racks"] + df.loc[i, "Central_Racks"]/2
        ax_bars.text(i, y_pos, f'{df.loc[i, "Central_Ratio"]:.1%}',
                     ha='center', va='center', fontsize=9, color='black', fontweight='bold')
    # 西部文字
    if df.loc[i, "West_Racks"] > 0:
        y_pos = df.loc[i, "East_Racks"] + df.loc[i, "Central_Racks"] + df.loc[i, "West_Racks"]/2
        ax_bars.text(i, y_pos, f'{df.loc[i, "West_Ratio"]:.1%}',
                     ha='center', va='center', fontsize=9, color='black', fontweight='bold')

# 隐藏柱状图的Y轴刻度
ax_bars.set_yticks([])

# --- 绘制双Y轴折线图 ---
ax_carbon = ax_bars.twinx()  # 创建共享X轴的新轴
ax_total = ax_bars.twinx()   # 再创建一个

# 调整轴的位置：将 ax_carbon 移到左侧
ax_carbon.yaxis.tick_left()
ax_carbon.yaxis.set_label_position("left")
ax_carbon.spines["left"].set_position(("axes", 0))
ax_carbon.set_frame_on(True)
ax_carbon.patch.set_visible(False)

# ax_total 默认在右侧，无需移动

# 绘制折线
l1, = ax_carbon.plot(x, df["Carbon_Cost_Change"], color='#d62728', marker='o', linewidth=2.5, label='碳社会成本变动 (%)', zorder=10)
l2, = ax_total.plot(x, df["Total_Cost_Change"], color='#1f77b4', marker='s', linewidth=2.5, linestyle='--', label='总成本变动 (%)', zorder=10)

# 设置Y轴标签和颜色
ax_carbon.set_ylabel('碳社会成本变动幅度 (%)', color='#d62728', fontsize=12, fontweight='bold')
ax_carbon.tick_params(axis='y', labelcolor='#d62728')
ax_carbon.set_ylim(-2, 7) # 根据数据微调范围，避免遮挡

ax_total.set_ylabel('总成本变动幅度 (%)', color='#1f77b4', fontsize=12, fontweight='bold')
ax_total.tick_params(axis='y', labelcolor='#1f77b4')
ax_total.set_ylim(-10, 8)

# 添加0刻度参考线
ax_carbon.axhline(0, color='gray', linewidth=1, linestyle=':', alpha=0.7)

# 设置X轴标签
ax_bars.set_xticks(x)
ax_bars.set_xticklabels(df["Scenario"], rotation=15, fontsize=11)

# 合并图例
lines = [p1, p2, p3, l1, l2]
labels = [l.get_label() for l in lines]
ax_bars.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=5, fontsize=10)

plt.title('算力布局结构与成本效益敏感性综合分析', fontsize=15, pad=20)
plt.tight_layout()
plt.show()