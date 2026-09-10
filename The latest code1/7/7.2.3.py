import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Data Preparation
data = {
    "Scenario": [
        "Baseline",
        "Mid Coal +20%",
        "Mid Green -20%",
        "East Coal +20%",
        "East Green -20%",
        "West Coal +20%",
        "West Green -20%"
    ],
    "East_Racks": [243000, 260000, 0, 0, 430000, 243000, 120000],
    "Central_Racks": [503000, 280000, 832000, 599000, 290000, 513000, 320000],
    "West_Racks": [898000, 1105000, 805000, 1048000, 898000, 885000, 1211000],
    "GDP_Growth": [0.3546, 0.3620, 0.3392, 0.3816, 0.3216, 0.3625, 0.3375],
    "Total_Cost": [6.61e12, 6.77e12, 6.40e12, 7.08e12, 6.09e12, 6.74e12, 6.44e12],
    "Carbon_Cost": [1.008e12, 1.020e12, 1.033e12, 1.006e12, 1.032e12, 1.004e12, 1.064e12]
}

df = pd.DataFrame(data)

# Normalize Units for Plotting
# Racks in 10k
df["East_Racks_10k"] = df["East_Racks"] / 10000
df["Central_Racks_10k"] = df["Central_Racks"] / 10000
df["West_Racks_10k"] = df["West_Racks"] / 10000
# Cost in Trillion (Wan Yi)
df["Total_Cost_Trillion"] = df["Total_Cost"] / 1e12
df["Carbon_Cost_Trillion"] = df["Carbon_Cost"] / 1e12

# Set plot style
plt.style.use('seaborn-v0_8-whitegrid')
fig_size = (10, 6)

# 1. Stacked Bar Chart: Spatial Distribution
fig1, ax1 = plt.subplots(figsize=fig_size)
scenarios = df["Scenario"]
bar_width = 0.6

p1 = ax1.bar(scenarios, df["East_Racks_10k"], width=bar_width, label='East', color='#4e79a7')
p2 = ax1.bar(scenarios, df["Central_Racks_10k"], width=bar_width, bottom=df["East_Racks_10k"], label='Central', color='#f28e2b')
p3 = ax1.bar(scenarios, df["West_Racks_10k"], width=bar_width, bottom=df["East_Racks_10k"]+df["Central_Racks_10k"], label='West', color='#59a14f')

ax1.set_ylabel('New Racks (10k Units)')
ax1.set_title('Spatial Distribution of New Computing Power by Scenario')
ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
plt.xticks(rotation=15)
plt.tight_layout()
fig1.savefig('spatial_distribution.png')

# 2. Scatter Plot: Cost vs GDP
fig2, ax2 = plt.subplots(figsize=fig_size)

# Baseline reference lines
base_gdp = df.loc[0, "GDP_Growth"]
base_cost = df.loc[0, "Total_Cost_Trillion"]

ax2.axhline(y=base_gdp, color='gray', linestyle='--', alpha=0.5)
ax2.axvline(x=base_cost, color='gray', linestyle='--', alpha=0.5)

colors = plt.cm.tab10(np.linspace(0, 1, len(df)))

for i, row in df.iterrows():
    ax2.scatter(row["Total_Cost_Trillion"], row["GDP_Growth"], s=150, color=colors[i], label=row["Scenario"], edgecolors='w')
    # Annotate points
    ax2.text(row["Total_Cost_Trillion"]+0.02, row["GDP_Growth"]+0.001, row["Scenario"], fontsize=9)

ax2.set_xlabel('Total Cost (Trillion RMB)')
ax2.set_ylabel('GDP Growth Rate (%)')
ax2.set_title('Trade-off Analysis: Economic Benefit vs. Cost')
# ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True)
plt.tight_layout()
fig2.savefig('cost_benefit_scatter.png')

# 3. Tornado Plot: Sensitivity of Carbon Cost (Difference from Baseline)
fig3, ax3 = plt.subplots(figsize=(10, 6))

df_sens = df[df["Scenario"] != "Baseline"].copy()
df_sens["Carbon_Diff"] = (df_sens["Carbon_Cost_Trillion"] - df.loc[0, "Carbon_Cost_Trillion"]) / df.loc[0, "Carbon_Cost_Trillion"] * 100

# Sort by impact
df_sens = df_sens.sort_values("Carbon_Diff", ascending=True)

colors_tornado = ['green' if x < 0 else 'red' for x in df_sens["Carbon_Diff"]]
bars = ax3.barh(df_sens["Scenario"], df_sens["Carbon_Diff"], color=colors_tornado)

ax3.axvline(0, color='black', linewidth=0.8)
ax3.set_xlabel('Change in Carbon Cost vs Baseline (%)')
ax3.set_title('Sensitivity Analysis: Impact on Carbon Cost')

# Add value labels
for bar in bars:
    width = bar.get_width()
    label_x_pos = width + 0.5 if width > 0 else width - 2.5
    ax3.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:.2f}%', va='center')

plt.tight_layout()
fig3.savefig('tornado_carbon.png')

# 4. Tornado Plot: Sensitivity of Total Cost
fig4, ax4 = plt.subplots(figsize=(10, 6))

df_sens["Cost_Diff"] = (df_sens["Total_Cost_Trillion"] - df.loc[0, "Total_Cost_Trillion"]) / df.loc[0, "Total_Cost_Trillion"] * 100
df_sens = df_sens.sort_values("Cost_Diff", ascending=True)

colors_tornado_cost = ['green' if x < 0 else 'red' for x in df_sens["Cost_Diff"]]
bars4 = ax4.barh(df_sens["Scenario"], df_sens["Cost_Diff"], color=colors_tornado_cost)

ax4.axvline(0, color='black', linewidth=0.8)
ax4.set_xlabel('Change in Total Cost vs Baseline (%)')
ax4.set_title('Sensitivity Analysis: Impact on Total Cost')

for bar in bars4:
    width = bar.get_width()
    label_x_pos = width + 0.5 if width > 0 else width - 2.5
    ax4.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:.2f}%', va='center')

plt.tight_layout()
fig4.savefig('tornado_total_cost.png')
plt.show()