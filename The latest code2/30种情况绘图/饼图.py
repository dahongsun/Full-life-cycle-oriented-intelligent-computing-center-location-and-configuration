import matplotlib.pyplot as plt
import numpy as np

# Data
data = {
    r'Scenario 1 ($\psi$=1)': {
        'Initial Cost': 203089296000,
        'Energy Cost': 4030418164243,
        'Equipment Maintenance Cost': 263236093058,
        'Terminal Cost': 5015269143,
        'Total Social Cost of Carbon': 1387782401179
    },
    r'Scenario 2 ($\psi$=1.1)': {
        'Initial Cost': 206710925700,
        'Energy Cost': 4120357374387,
        'Equipment Maintenance Cost': 177021101874,
        'Terminal Cost': 5015269143,
        'Total Social Cost of Carbon': 1422706283240
    },
    r'Scenario 3 ($\psi$=1.2)': {
        'Initial Cost': 213248399700,
        'Energy Cost': 4236915414610,
        'Equipment Maintenance Cost': 127625456784,
        'Terminal Cost': 5015269143,
        'Total Social Cost of Carbon': 1443999579455
    },
    r'Scenario 4 ($\psi$=1.3)': {
        'Initial Cost': 220458193200,
        'Energy Cost': 4365279106853,
        'Equipment Maintenance Cost': 155092141798,
        'Terminal Cost': 5015269143,
        'Total Social Cost of Carbon': 1461852144582
    }
}

labels = [
    'Initial Cost',
    'Energy Cost',
    'Equipment Maintenance Cost',
    'Terminal Cost',
    'Total Social Cost of Carbon'
]

# 5个分类的蓝色系配色方案
category_colors = {
    'Energy Cost': '#08519c',  # 最深蓝
    'Total Social Cost of Carbon': '#3182bd',  # 强蓝
    'Initial Cost': '#6baed6',  # 中蓝
    'Equipment Maintenance Cost': '#bdd7e7',  # 浅蓝
    'Terminal Cost': '#eff3ff'  # 最浅蓝
}

color_list = [category_colors[l] for l in labels]

# 保持宽幅，确保5个图例能在一行放得下
fig, axes = plt.subplots(1, 4, figsize=(22, 6))

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']

for i, (scenario_name, costs) in enumerate(data.items()):

    ax = axes[i]

    values = [costs[l] for l in labels]
    total = sum(values)
    percentages = [v / total * 100 for v in values]

    # Plot pie
    wedges, _ = ax.pie(
        values,
        startangle=90,
        colors=color_list,
        radius=1.0
    )

    # Add annotations with lines
    for j, w in enumerate(wedges):

        ang = (w.theta2 - w.theta1) / 2. + w.theta1

        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))

        # Connection point on the wedge
        p_wedge = (x, y)

        horizontalalignment = {
            -1: "right",
            1: "left"
        }[int(np.sign(x))]

        # ==================================================
        # 仅调整 Equipment Maintenance Cost 和 Terminal Cost
        # 保证上下顺序与饼图扇区一致，避免引导线交叉
        # ==================================================

        if labels[j] == 'Equipment Maintenance Cost':

            # Equipment Maintenance Cost 位于 Terminal Cost 下方
            # 因此文字位置也放在下方
            xytext = (
                1.45 * np.sign(x),
                1.20 * y - 0.22
            )

        elif labels[j] == 'Terminal Cost':

            # Terminal Cost 位于 Equipment Maintenance Cost 上方
            # 因此文字位置放在上方
            xytext = (
                1.45 * np.sign(x),
                1.20 * y + 0.22
            )

        elif percentages[j] < 1.0:

            y_offset = 0.25 if j % 2 == 0 else -0.25

            xytext = (
                1.45 * np.sign(x),
                1.20 * y + y_offset
            )

        else:

            xytext = (
                1.35 * np.sign(x),
                1.35 * y
            )

        pct_text = f"{percentages[j]:.2f}%"

        ax.annotate(
            pct_text,
            xy=p_wedge,
            xytext=xytext,
            horizontalalignment=horizontalalignment,
            arrowprops=dict(
                arrowstyle="-",
                color='gray',
                linewidth=1.5
            ),
            fontsize=16,
            fontweight='bold'
        )

    ax.set_title(
        scenario_name,
        fontsize=18,
        fontweight='bold',
        y=1.1
    )


# ncol=5 强制一行
fig.legend(
    wedges,
    labels,
    loc='lower center',
    ncol=5,
    bbox_to_anchor=(0.5, 0.05),
    fontsize=18,
    frameon=False,
    handletextpad=0.5,
    columnspacing=1.5
)

plt.suptitle(
    'Analysis of LCSC Structures Under Different Constraints ($\psi$)',
    fontsize=20,
    y=0.98
)

# 减少无用留白
plt.subplots_adjust(
    bottom=0.12,
    top=0.85,
    wspace=0.4
)

plt.savefig(
    'cost_breakdown_pie_charts_english_lines.png',
    bbox_inches='tight',
    dpi=600
)

plt.show()