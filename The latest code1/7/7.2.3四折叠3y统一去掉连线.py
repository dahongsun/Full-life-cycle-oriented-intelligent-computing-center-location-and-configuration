import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib
from matplotlib import rcParams

# ==========================================
# 1. Global Settings
# ==========================================
rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

# ==========================================
# 2. Data Preparation
# ==========================================
data = {
    # Reordered Scenarios: Baseline -> East -> Central -> West
    "Scenario": [
        "基准情景",
        "东部火电+1%", "东部绿电-1%",
        "中部火电+1%", "中部绿电-1%",
        "西部火电+1%", "西部绿电-1%"
    ],
    # Reordered Racks (East)
    "East_Racks": [243000, 0, 430000, 260000, 0, 243000, 120000],
    # Reordered Racks (Central)
    "Central_Racks": [503000, 599000, 290000, 280000, 832000, 513000, 320000],
    # Reordered Racks (West)
    "West_Racks": [898000, 1048000, 898000, 1105000, 805000, 885000, 1211000],
    # Reordered Total Cost
    "Total_Cost": [6.61e12, 7.08e12, 6.09e12, 6.77e12, 6.40e12, 6.74e12, 6.44e12],
    # Reordered Carbon Cost
    "Carbon_Cost": [1.008e12, 1.006e12, 1.032e12, 1.020e12, 1.033e12, 1.004e12, 1.064e12],
    # Reordered GDP Growth
    "GDP_Growth": [0.3546, 0.3816, 0.3216, 0.3620, 0.3392, 0.3625, 0.3375]
}

df = pd.DataFrame(data)

# Calculate Ratios
df["Total_Racks"] = df["East_Racks"] + df["Central_Racks"] + df["West_Racks"]
df["East_Ratio"] = df["East_Racks"] / df["Total_Racks"]
df["Central_Ratio"] = df["Central_Racks"] / df["Total_Racks"]
df["West_Ratio"] = df["West_Racks"] / df["Total_Racks"]

# Calculate Percentage Changes vs Baseline (Index 0)
base_total = df.loc[0, "Total_Cost"]
base_carbon = df.loc[0, "Carbon_Cost"]
base_gdp = df.loc[0, "GDP_Growth"]

df["Total_Cost_Change"] = (df["Total_Cost"] - base_total) / base_total * 100
df["Carbon_Cost_Change"] = (df["Carbon_Cost"] - base_carbon) / base_carbon * 100
df["GDP_Change"] = (df["GDP_Growth"] - base_gdp) / base_gdp * 100

# ==========================================
# 3. Plotting
# ==========================================
fig, ax_lines = plt.subplots(figsize=(14, 8))

# Twin axis for background bars
ax_bars = ax_lines.twinx()

# Turn off grids
ax_lines.grid(False)
ax_bars.grid(False)

# --- Plot Stacked Bars (Background) ---
x = np.arange(len(df))
bar_width = 0.5

# Low alpha for background effect
p1 = ax_bars.bar(x, df["East_Racks"], width=bar_width, label='东部机架占比', color='#4e79a7', alpha=0.3)
p2 = ax_bars.bar(x, df["Central_Racks"], width=bar_width, bottom=df["East_Racks"], label='中部机架占比', color='#f28e2b', alpha=0.3)
p3 = ax_bars.bar(x, df["West_Racks"], width=bar_width, bottom=df["East_Racks"]+df["Central_Racks"], label='西部机架占比', color='#59a14f', alpha=0.3)

# Add ratio text on bars
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

# Hide right Y-axis
ax_bars.set_yticks([])

# --- Plot Scatter Points (Foreground) ---
# Markers only, no lines (linestyle='none')
# Carbon Cost (Red Circle)
l1, = ax_lines.plot(x, df["Carbon_Cost_Change"], color='#d62728',
                    marker='o', linestyle='none', markersize=12,
                    label='碳成本变动 (%)', zorder=10)
# Total Cost (Blue Square)
l2, = ax_lines.plot(x, df["Total_Cost_Change"], color='#1f77b4',
                    marker='s', linestyle='none', markersize=12,
                    label='总成本变动 (%)', zorder=10)
# GDP Growth (Purple Triangle)
l3, = ax_lines.plot(x, df["GDP_Change"], color='#9467bd',
                    marker='^', linestyle='none', markersize=12,
                    label='GDP增幅变动 (%)', zorder=10)

# --- Axis Settings ---
ax_lines.set_ylabel('变动 (%)', color='black', fontsize=12, fontweight='bold')
ax_lines.set_ylim(-10, 10)  # Fixed range
# Zero line
ax_lines.axhline(0, color='black', linewidth=1, linestyle='-', alpha=0.5)

# X Axis
ax_lines.set_xticks(x)
ax_lines.set_xticklabels(df["Scenario"], rotation=15, fontsize=11)

# --- Combined Legend ---
lines = [p1, p2, p3, l1, l2, l3]
labels = [l.get_label() for l in lines]
ax_lines.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=6, fontsize=10)

plt.title('多情景敏感性分析：结构与指标变动', fontsize=16, pad=20)
plt.tight_layout()
plt.savefig('Figure_Sensitivity_Scatter_Reordered.png', dpi=3000)
plt.show()