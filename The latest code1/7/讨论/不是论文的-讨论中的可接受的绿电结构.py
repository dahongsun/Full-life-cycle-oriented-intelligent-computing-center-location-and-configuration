import matplotlib.pyplot as plt
import numpy as np

# --- 1. 全局设置 ---
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['mathtext.fontset'] = 'stix'
# 全局字号保持 18
plt.rcParams.update({'font.size': 18})

# --- 2. 数据准备 ---
raw_data = {
    '1': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [
            4109156303780, 4329404072518, 4513882566091,
            4675124198108, 4792228082163
        ],
        'carbon': [
            1580905159, 381872233965, 762235827812,
            1139042865609, 1497863701023
        ],
        'gdp': [
            0.262989, 0.275712, 0.284625,
            0.294027, 0.310594
        ],
        'socio_cost': [
            4110737208940, 4711276306484, 5276118393903,
            5814167063717, 6290091783186
        ]
    },
    '1.02': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [
            4120472989731, 4329404072518, 4513882566091,
            4675124198108, 4792228082163
        ],
        'carbon': [
            1565365285, 381872233965, 762235827812,
            1139042865609, 1497863701023
        ],
        'gdp': [
            0.266730, 0.275712, 0.284625,
            0.294027, 0.310594
        ],
        'socio_cost': [
            4122038355016, 4711276306484, 5276118393903,
            5814167063717, 6290091783186
        ]
    },
    '1.04': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [
            4144835932066, 4329404072518, 4513882566091,
            4675124198108, 4792228082163
        ],
        'carbon': [
            1568564041, 381872233965, 762235827812,
            1139042865609, 1497863701023
        ],
        'gdp': [
            0.271960, 0.275712, 0.284625,
            0.294027, 0.310594
        ],
        'socio_cost': [
            4146404496107, 4711276306484, 5276118393903,
            5814167063717, 6290091783186
        ]
    },
    '1.06': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [
            4169336382202, 4331505163180, 4513882566091,
            4675124198108, 4792228082163
        ],
        'carbon': [
            1572222056, 381737264537, 762235827812,
            1139042865609, 1497863701023
        ],
        'gdp': [
            0.277190, 0.277190, 0.284625,
            0.294027, 0.310594
        ],
        'socio_cost': [
            4170908604258, 4713242427717, 5276118393903,
            5814167063717, 6290091783186
        ]
    },
    '1.08': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [
            4194386553977, 4351048887311, 4513882566091,
            4675124198108, 4792228082163
        ],
        'carbon': [
            1579068124, 381447817816, 762235827812,
            1139042865609, 1497863701023
        ],
        'gdp': [
            0.282420, 0.282420, 0.284625,
            0.294027, 0.310594
        ],
        'socio_cost': [
            4195965622101, 4732496705128, 5276118393903,
            5814167063717, 6290091783186
        ]
    },
    '1.1': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [
            4220508089694, 4375136814168, 4520246470308,
            4675124198108, 4792228082163
        ],
        'carbon': [
            1575415461, 380725888332, 760780434350,
            1139042865609, 1497863701023
        ],
        'gdp': [
            0.287650, 0.287650, 0.287650,
            0.294027, 0.310594
        ],
        'socio_cost': [
            4222083505155, 4755862702500, 5281026904658,
            5814167063717, 6290091783186
        ]
    }
}

titles = [
    r'(a) $\psi=1$',
    r'(b) $\psi=1.02$',
    r'(c) $\psi=1.04$',
    r'(d) $\psi=1.06$',
    r'(e) $\psi=1.08$',
    r'(f) $\psi=1.1$'
]

keys = ['1', '1.02', '1.04', '1.06', '1.08', '1.1']

# --- 3. 绘图 ---
fig, axes = plt.subplots(3, 2, figsize=(22, 18))
axes = axes.flatten()

# 颜色定义
color_socio = '#7030A0'  # 紫色
color_cost = '#4472C4'  # 蓝色
color_carbon = '#548235'  # 绿色
color_gdp = '#ED7D31'  # 橙色
color_drop = '#C00000'  # 红色虚线

# 为了数据可读性，将货币数值单位设为 10^8（亿元）
unit = 1e8
lines_labels_list = []

for i, key in enumerate(keys):
    ax1 = axes[i]
    data = raw_data[key]

    alpha_x = range(len(data['alpha']))

    # 提取绝对数值并缩放
    socio_costs = [x / unit for x in data['socio_cost']]
    costs = [x / unit for x in data['cost']]
    carbons = [x / unit for x in data['carbon']]
    gdps = data['gdp']

    # --- 左轴: Absolute Socio, Cost & Carbon ---
    l4, = ax1.plot(alpha_x, socio_costs, color=color_socio, marker='D', markersize=8,
                   linewidth=3, label='Life Cycle Socio-Economic Cost')

    l1, = ax1.plot(alpha_x, costs, color=color_cost, marker='o', markersize=8,
                   linewidth=3, label='Total lifecycle cost')

    l2, = ax1.plot(alpha_x, carbons, color=color_carbon, marker='s', markersize=8,
                   linewidth=3.5, linestyle='--', label='Total Social Cost of Carbon')

    ax1.set_ylabel(r'Cost ($10^8$ CNY)', color='black', fontsize=20)
    ax1.tick_params(axis='y', labelcolor='black', labelsize=18)
    ax1.tick_params(axis='x', labelsize=18)

    # 动态调高Y轴上下限
    all_costs = socio_costs + costs + carbons
    min_c, max_c = min(all_costs), max(all_costs)
    margin_c = (max_c - min_c) * 0.15
    ax1.set_ylim(min_c - margin_c, max_c + margin_c * 1.5)

    # --- 右轴: GDP ---
    ax2 = ax1.twinx()
    l3, = ax2.plot(alpha_x, gdps, color=color_gdp, marker='^', markersize=9,
                   linewidth=3, label='Gross output value contribution share (%)')

    ax2.set_ylabel('Gross output value contribution share (%)', color='black', fontsize=20)
    ax2.tick_params(axis='y', labelcolor='black', labelsize=18)

    min_g, max_g = min(gdps), max(gdps)
    margin_g = (max_g - min_g) * 2 if max_g != min_g else max_g * 0.5
    ax2.set_ylim(min_g - margin_g, max_g + margin_g)

    # --- X轴设置 ---
    ax1.set_xticks(alpha_x)
    ax1.set_xticklabels(data['alpha'])
    ax1.set_title(titles[i], y=-0.20, fontsize=22)

    # --- 绘制和标注 ---
    ylim_cost = ax1.get_ylim()
    y_span_cost = ylim_cost[1] - ylim_cost[0]

    ylim_gdp = ax2.get_ylim()
    y_span_gdp = ylim_gdp[1] - ylim_gdp[0]

    for j, _ in enumerate(alpha_x):
        socio_val = socio_costs[j]
        c_val = costs[j]
        carb_val = carbons[j]
        g_val = gdps[j]

        # 投影线 (起始点设为 Y轴底端)
        ax1.vlines(x=j, ymin=ylim_cost[0], ymax=socio_val, colors=color_drop, linestyles='--', alpha=0.6, linewidth=1.5)

        # 1. Socio Cost 标注 - 紫色 (放在最上方)
        ax1.text(j, socio_val + y_span_cost * 0.03, f'{socio_val:.0f}',
                 ha='center', va='bottom', color=color_socio, fontsize=15, fontweight='bold')

        # 2. Cost 标注 (Total Costs) - 蓝色
        # 如果 Cost 和 Socio 靠得太近（比如 alpha=0 时），将 Cost 的标注移到下方防止重叠
        if abs(socio_val - c_val) < y_span_cost * 0.08:
            ax1.text(j, c_val - y_span_cost * 0.03, f'{c_val:.0f}',
                     ha='center', va='top', color=color_cost, fontsize=15, fontweight='bold')
        else:
            ax1.text(j, c_val + y_span_cost * 0.03, f'{c_val:.0f}',
                     ha='center', va='bottom', color=color_cost, fontsize=15, fontweight='bold')

        # 3. Carbon 标注 - 绿色
        # 如果 Carbon 和 Cost 太近，将其水平便宜避免遮挡
        if abs(c_val - carb_val) < y_span_cost * 0.08:
            ax1.text(j + 0.15, carb_val, f'{carb_val:.0f}',
                     ha='left', va='center', color=color_carbon, fontsize=15, fontweight='bold')
        else:
            ax1.text(j, carb_val + y_span_cost * 0.03, f'{carb_val:.0f}',
                     ha='center', va='bottom', color=color_carbon, fontsize=15, fontweight='bold')

        # 4. GDP 标注 - 橙色
        ax2.text(j, g_val - y_span_gdp * 0.05, f'{g_val:.4f}%',
                 ha='center', va='top', color=color_gdp, fontsize=15, fontweight='bold')

    if i == 0:
        lines_labels_list = [l4, l1, l2, l3]

plt.tight_layout()

# 调整底部留白
plt.subplots_adjust(bottom=0.11)

# 将图例名称的 "Normalized" 去掉，且按照您要求的排为 2 行 (ncol=2)
fig.legend(lines_labels_list,
           ['Life Cycle Socio-Economic Cost', 'Total lifecycle cost',
            'Total Social Cost of Carbon', 'Gross output value contribution share'],
           loc='lower center', ncol=2, frameon=False, fontsize=20)

plt.savefig('chart_alpha_absolute_fixed_labels.svg', format='svg', bbox_inches='tight')
plt.show()