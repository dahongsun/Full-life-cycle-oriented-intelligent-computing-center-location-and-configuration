import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib
from matplotlib import rcParams

# ==========================================
# 1. Global Settings
# ==========================================
# Attempt to set a font that supports Chinese characters.
# In this environment, we check available fonts or fallback.
# Ideally, 'SimHei' or similar is needed.
rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

# ==========================================
# 2. Data Preparation
# ==========================================
# Replacing the template data with the user's provided data
data = {
    "Scenario": [
        "基准情景",
        "东部绿电+1%",
        "中部绿电+1%",
        "西部绿电+1%"
    ],
    "East_Racks":    [243000, 240000, 243000, 243000],
    "Central_Racks": [503000, 503000, 503000, 503000],
    "West_Racks":    [898000, 901000, 898000, 898000],
    # Using full numbers for accuracy, script calculates percentage change anyway
    "Total_Cost":    [6611518232589, 6617866770219, 6615714920125, 6613824692812],
    "Carbon_Cost":   [1008213804916, 1014021799131, 1010357028098, 1010470801121],
    "GDP_Growth":    [0.3546, 0.3545, 0.3547, 0.3546]
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
# Adjusting ylim to fit the new data range. The changes might be small, so auto-scaling or a tighter range might be better.
# Given the data, changes are small (<1%). Let's keep a reasonable range or auto.
# Let's check the data range first.
# Calculation check: (6.617 - 6.611)/6.611 is small.
# Let's set a smaller limit for visibility if needed, or just let it auto scale if the user code had fixed -10, 10.
# The previous code had -10, 10. This data has much smaller variance. I will adjust the limits to make points visible.
data_max = max(df[["Total_Cost_Change", "Carbon_Cost_Change", "GDP_Change"]].max().max(), 0.5)
data_min = min(df[["Total_Cost_Change", "Carbon_Cost_Change", "GDP_Change"]].min().min(), -0.5)
margin = (data_max - data_min) * 0.2
ax_lines.set_ylim(data_min - margin, data_max + margin)


# Zero line
ax_lines.axhline(0, color='black', linewidth=1, linestyle='-', alpha=0.5)

# X Axis
ax_lines.set_xticks(x)
ax_lines.set_xticklabels(df["Scenario"], rotation=0, fontsize=11) # Rotation 0 is fine for short names

# --- Combined Legend ---
lines = [p1, p2, p3, l1, l2, l3]
labels = [l.get_label() for l in lines]
ax_lines.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=6, fontsize=10)

plt.title('省份供电结构变化敏感性分析：结构与指标变动', fontsize=16, pad=20)
plt.tight_layout()
plt.savefig('Figure_Sensitivity_Scatter_GreenPower123.svg', dpi=300, format='svg')
plt.savefig('Figure_Sensitivity_Scatter_GreenPower123.svg', dpi=300,format='svg')

plt.show()