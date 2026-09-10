import matplotlib.pyplot as plt
import numpy as np

# --- 1. 全局学术样式设置 ---
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 14
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'

# --- 2. 数据准备 ---


raw_data = {
    '1': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [4109156303780, 4329404072518, 4513882566091, 4675345896644, 4792858147378],
        'carbon': [1580905159, 532185240597, 1062764611665, 1587594254261, 2084716341262],
        'gdp': [0.246876, 0.263313, 0.275008, 0.283976, 0.292161],
        'socio_cost': [4110737208940, 4861589313116, 5576647177756, 6262940150905, 6877574488639],
    },
    '1.02': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [4110613449656, 4329404072518, 4513882566091, 4675345896644, 4792857479913],
        'carbon': [1581823677, 532185240597, 1062764611665, 1587594254261, 2084716341262],
        'gdp': [0.247656, 0.264093, 0.275008, 0.283976, 0.292161],
        'socio_cost': [4112195273333, 4861589313116, 5576647177756, 6262940150905, 6877573821175],
    },
    '1.04': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [4130405782121, 4329404072518, 4513882566091, 4675345896644, 4792857479913],
        'carbon': [1572681315, 532185240597, 1062764611665, 1587594254261, 2084716341262],
        'gdp': [0.252512, 0.268949, 0.277917, 0.286102, 0.292161],
        'socio_cost': [4131978463435, 4861589313116, 5576647177756, 6262940150905, 6877573821175],
    },
    '1.06': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [4153463983834, 4329404072518, 4513882566091, 4675345896644, 4792857479913],
        'carbon': [1569023300, 532185240597, 1062764611665, 1587594254261, 2084716341262],
        'gdp': [0.257368, 0.273805, 0.282773, 0.290958, 0.292161],
        'socio_cost': [4155033007133, 4861589313116, 5576647177756, 6262940150905, 6877573821175],
    },
    '1.08': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [4176639118426, 4337416149765, 4513882566091, 4675345896644, 4792857479913],
        'carbon': [1572681315, 532537335579, 1062764611665, 1587594254261, 2084716341262],
        'gdp': [0.262224, 0.278661, 0.287629, 0.292161, 0.292161],
        'socio_cost': [4178211799741, 4869953485344, 5576647177756, 6262940150905, 6877573821175],
    },
    '1.1': {
        'alpha': ['0', '0.25', '0.5', '0.75', '1'],
        'cost': [4200804348500, 4360165609461, 4514383410573, 4675345896644, 4792857479913],
        'carbon': [1575426164, 531261981256, 1062586817436, 1587594254261, 2084716341262],
        'gdp': [0.26708, 0.283517, 0.292161, 0.292161, 0.292161],
        'socio_cost': [4202379774664, 4891427590717, 5576970228009, 6262940150905, 6877573821175],
    },
}
# --- 3. 绘图配置 ---
fig, axes = plt.subplots(3, 2, figsize=(18, 16))
axes = axes.flatten()

psi_keys = ['1', '1.02', '1.04', '1.06', '1.08', '1.1']
titles = [
    r'(a) $\psi=1$',
    r'(b) $\psi=1.02$',
    r'(c) $\psi=1.04$',
    r'(d) $\psi=1.06$',
    r'(e) $\psi=1.08$',
    r'(f) $\psi=1.1$'
]

x_vals = [0, 0.25, 0.5, 0.75, 1.0]
x_labels = [r'$\alpha=0$', r'$\alpha=0.25$', r'$\alpha=0.5$', r'$\alpha=0.75$', r'$\alpha=1$']

# 颜色
color_cost = '#1f77b4'
color_carbon = '#006400'
color_socio = '#7030A0'
color_gdp = '#ff7f0e'
# ==========================================
# 调整区：数值越大，标注越往下移动
# 分别对应 alpha = 0, 0.25, 0.5, 0.75, 1.0
gdp_v_offsets = [0.11, 0.09, 0.1, 0.05, 0.05]
# ==========================================
unit = 1e8
lines_legend = []

# --- 4. 逐张子图绘制 ---
for i, key in enumerate(psi_keys):
    ax1 = axes[i]
    data = raw_data[key]

    cost = np.array(data['cost']) / unit
    carbon = np.array(data['carbon']) / unit
    socio = np.array(data['socio_cost']) / unit
    gdp = np.array(data['gdp'])

    # --- 左轴设置 (成本系) ---
    ax1.set_xticks(x_vals)
    ax1.set_xticklabels(x_labels)
    ax1.set_xlim(-0.1, 1.1)

    l1, = ax1.plot(x_vals, cost, marker='o', linewidth=2.5, markersize=7, color=color_cost,
                   label='Total lifecycle cost')
    l2, = ax1.plot(x_vals, carbon, marker='^', linestyle='--', linewidth=2.5, markersize=7, color=color_carbon,
                   label='Social Cost of Carbon')
    l3, = ax1.plot(x_vals, socio, marker='D', linewidth=2.5, markersize=7, color=color_socio,
                   label='Life Cycle Socio-Economic Cost')

    ax1.set_ylabel(r'Cost ($10^8$ CNY)', fontsize=15)
    ax1.grid(True, linestyle=':', alpha=0.4)

    # 动态获取左轴的数据范围
    all_costs = np.concatenate([cost, carbon, socio])
    min_c, max_c = min(all_costs), max(all_costs)
    range_c = max_c - min_c
    ax1.set_ylim(min_c - range_c * 0.15, max_c + range_c * 0.25)

    # --- 右轴设置 (GDP) ---
    ax2 = ax1.twinx()
    l4, = ax2.plot(x_vals, gdp, marker='s', linewidth=2.5, markersize=7, color=color_gdp,
                   label='Gross output value contribution share (%)')
    ax2.set_ylabel('Gross output value contribution share (%)', fontsize=15)

    # 动态预留右轴空间
    min_g, max_g = min(gdp), max(gdp)
    range_g = max_g - min_g if max_g != min_g else min_g * 0.1
    ax2.set_ylim(min_g - range_g * 0.2, max_g + range_g * 0.3)

    # --- 动态比例的数值标注 ---
    for j, x in enumerate(x_vals):
        # 1. 紫色 socio_cost
        if key in ['1.06', '1.08', '1.1'] and j == 3:
            socio_y = socio[j] - range_c * 0.035
            socio_va = 'top'
        else:
            socio_y = socio[j] + range_c * 0.03
            socio_va = 'bottom'
        ax1.text(x, socio_y, f'{socio[j]:.0f}',
                 ha='center', va=socio_va, fontsize=11, color=color_socio, fontweight='bold')

        # 2. 蓝色 cost (全生命周期成本)
        # 修改点：在 alpha=0.5 (j=2) 时，将数字向右移动并左对齐，避开 GDP 数值
        if j == 2:
            ax1.text(x + 0.04, cost[j] - range_c * 0.03, f'{cost[j]:.0f}',
                     ha='left', va='top', fontsize=11, color=color_cost, fontweight='bold')
        elif key == '1.08' and j == 1:
            ax1.text(x - 0.025, cost[j] - range_c * 0.03, f'{cost[j]:.0f}',
                     ha='center', va='top', fontsize=11, color=color_cost, fontweight='bold')
        elif key == '1.1' and j == 1:
            ax1.text(x + 0.045, cost[j] - range_c * 0.03, f'{cost[j]:.0f}',
                     ha='center', va='top', fontsize=11, color=color_cost, fontweight='bold')
        else:
            ax1.text(x, cost[j] - range_c * 0.03, f'{cost[j]:.0f}',
                     ha='center', va='top', fontsize=11, color=color_cost, fontweight='bold')

        # 3. 绿色 carbon (碳社会成本)
        # 修改点：在 alpha=0 (j=0) 时，向上大幅移动数值偏移量
        carbon_offset = 0.08 if j == 0 else 0.03
        carb_txt = f'{carbon[j]:.1f}' if carbon[j] < 100 else f'{carbon[j]:.0f}'
        ax1.text(x, carbon[j] + range_c * carbon_offset, carb_txt,
                 ha='center', va='bottom', fontsize=11, color=color_carbon)

        # 4. 橙色 GDP
        # 使用自定义的偏移系数列表 gdp_v_offsets
        v_offset = gdp_v_offsets[j]
        # alpha=0.5 (j=2) 时数字移到左边
        gdp_x = x + 0.03 if j == 2 else x
        gdp_ha = 'right' if j == 2 else 'center'
        if key in ['1.08', '1.1'] and j == 1:
            gdp_x = x + 0.060 if key == '1.1' else x + 0.035
            gdp_ha = 'center'
        if key == '1.1' and j == 1:
            v_offset += 0.035
        if (key in ['1.06', '1.08'] and j == 3) or (key == '1.1' and j in [2, 3]):
            gdp_y = gdp[j] + range_g * 0.055
            gdp_va = 'bottom'
        else:
            gdp_y = gdp[j] - range_g * v_offset
            gdp_va = 'top'
        ax2.text(gdp_x, gdp_y, f'{gdp[j]:.4f}%', ha=gdp_ha, va=gdp_va, fontsize=12,
                 color=color_gdp, fontweight='bold')
    # 标题位置
    ax1.set_title(titles[i], y=-0.18, fontsize=17)

    if i == 0:
        lines_legend = [l1, l2, l3, l4]

# --- 5. 全局布局与图例设置 ---
plt.subplots_adjust(left=0.06, right=0.94, top=0.98, bottom=0.08, wspace=0.25, hspace=0.25)

fig.legend(lines_legend, [l.get_label() for l in lines_legend],
           loc='lower center', bbox_to_anchor=(0.5, 0.0001), ncol=4, frameon=False, fontsize=16)

plt.savefig('alpha_psi_subplots_optimized_v2.png', dpi=300, bbox_inches='tight')
# 保存为 SVG (矢量图，学术排版推荐)
plt.savefig('alpha_psi_subplots_optimized_v2.svg', format='svg', bbox_inches='tight')
plt.show()
