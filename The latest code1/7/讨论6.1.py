import matplotlib.pyplot as plt

# --- 1. 字体与全局设置 ---
# 设置字体为 Times New Roman
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
# 数学公式字体设置为 stix
plt.rcParams['mathtext.fontset'] = 'stix'
# 全局调大字号
plt.rcParams.update({'font.size': 16})

# --- 2. 准备数据 ---
data_source = {
    '1ms': {
        'psi': [1, 1.1, 1.2, 1.3],
        'cost': [6432596201941, 6432596201941, 6432596201941, 6704560757167],
        'gdp': [0.295069, 0.295069, 0.295069, 0.31564]
    },
    '3ms': {
        'psi': [1, 1.1, 1.2, 1.3],
        'cost': [6034240518574, 6041836687008, 6096086269115, 6250975564686],
        'gdp': [0.254992, 0.26708, 0.29136, 0.31564]
    },
    '5ms': {
        'psi': [1, 1.1, 1.2, 1.3],
        'cost': [5889541223624, 5931810954343, 6026804170798, 6207696701097],
        'gdp': [0.247161, 0.26708, 0.29136, 0.31564]
    },
    '7ms': {
        'psi': [1, 1.1, 1.2, 1.3],
        'cost': [5875295467501, 5922988083691, 6025318686003, 6207411182355],
        'gdp': [0.2428, 0.26708, 0.29136, 0.31564]
    },
    '9ms': {
        'psi': [1, 1.1, 1.2, 1.3],
        'cost': [5870450570601, 5918509820417, 6021200179083, 6204846060771],
        'gdp': [0.2428, 0.26708, 0.29136, 0.31564]
    },
    '11ms': {
        'psi': [1, 1.1, 1.2, 1.3],
        'cost': [5867690775722, 5915391424538, 6019902240373, 6204787528385],
        'gdp': [0.242809, 0.26708, 0.29136, 0.31564]
    }
}
# 转换成本单位为 亿元 (10^8)
for k, v in data_source.items():
    v['cost'] = [x / 100000000 for x in v['cost']]

delays = ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms']
titles = [
    '(a) Propagation delay ≤1ms',
    '(b) Propagation delay ≤3ms',
    '(c) Propagation delay ≤5ms',
    '(d) Propagation delay ≤7ms',
    '(e) Propagation delay ≤9ms',
    '(f) Propagation delay ≤11ms'
]

# --- 3. 绘图 ---
fig, axes = plt.subplots(3, 2, figsize=(22, 18))
axes = axes.flatten()

color_cost = '#4472C4'  # 蓝
color_gdp = '#ED7D31'  # 橙
color_dash = '#FFC000'  # 黄色虚线 (背景网格/投影)
color_annot = '#C00000'  # 红色虚线和文字 (变动幅度)

lines_labels = []

for i, delay in enumerate(delays):
    ax1 = axes[i]
    data = data_source[delay]
    psi_vals = data['psi']
    costs = data['cost']
    gdps = data['gdp']

    # --- 左轴：总成本 ---
    l1, = ax1.plot(psi_vals, costs, color=color_cost, marker='o', markersize=7, linewidth=2.5, label='Total costs')

    ax1.set_ylabel('Life Cycle Socio-Economic Cost ($10^8$ CNY)', color='black', fontsize=19)
    ax1.tick_params(axis='y', labelcolor='black', labelsize=16)
    ax1.tick_params(axis='x', labelsize=16)

    # 左轴 Y 范围设置
    min_c, max_c = min(costs), max(costs)
    margin_c = (max_c - min_c) * 0.4 if max_c != min_c else max_c * 0.2
    ax1.set_ylim(min_c - margin_c, max_c + margin_c)

    # --- 绘制黄色水平基准线 (Baseline) ---
    baseline_y = costs[0]
    ax1.hlines(y=baseline_y, xmin=min(psi_vals), xmax=max(psi_vals),
               colors=color_dash, linestyles='--', linewidth=2, alpha=0.8)

    # --- 右轴：GDP增幅 ---
    ax2 = ax1.twinx()
    l2, = ax2.plot(psi_vals, gdps, color=color_gdp, marker='o', markersize=7, linewidth=2.5,
                   label='National Total GDP Increase')

    ax2.set_ylabel('Gross output value contribution share (%)', color='black', fontsize=19)
    ax2.tick_params(axis='y', labelcolor='black', labelsize=16)

    # 右轴 Y 范围设置
    min_g, max_g = min(gdps), max(gdps)
    margin_g = (max_g - min_g) * 0.3 if max_g != min_g else max_g * 0.1
    ax2.set_ylim(min_g - margin_g, max_g + margin_g * 0.2)

    # --- X轴设置 ---
    ax1.set_xticks(psi_vals)
    ax1.set_xticklabels([r'$\psi$=' + str(x) for x in psi_vals], fontsize=16)
    ax1.set_title(titles[i], y=-0.28, fontsize=20)

    # 显式扩大 X 轴范围
    x_padding = 0.03
    ax1.set_xlim(min(psi_vals) - x_padding, max(psi_vals) + x_padding)

    # --- 标注绘制 ---
    ymin_cost, ymax_cost = ax1.get_ylim()
    ymin_gdp, ymax_gdp = ax2.get_ylim()

    # 提前计算 GDP 轴的总跨度，用于计算 offset
    y_range_gdp = ymax_gdp - ymin_gdp

    for j, psi in enumerate(psi_vals):
        c_val = costs[j]
        g_val = gdps[j]

        # 1. 黄色垂直虚线
        ax1.vlines(x=psi, ymin=ymin_cost, ymax=c_val, colors=color_dash, linestyles='dashed', alpha=0.6, linewidth=1.5)

        # 2. 数值标注
        # 成本数值 (保持原样，在上方)
        ax1.text(psi, c_val + (ymax_cost - ymin_cost) * 0.02, f'{int(c_val)}',
                 ha='center', va='bottom', color=color_cost, fontsize=15, fontweight='bold')

        # GDP数值逻辑修改：
        # 如果是 3ms-11ms 图 (i > 0) 且是 第2个点 (j == 1)，则放在上面
        # 否则 (包括 1ms 图的所有点，以及其他图的其他点)，保持原样放在下面
        if i > 0 and j == 1:
            # 放在上方 (正偏移，va='bottom')
            ax2.text(psi, g_val + y_range_gdp * 0.02, f'{g_val:.4f}%',
                     ha='center', va='bottom', color=color_gdp, fontsize=15, fontweight='bold')
        else:
            # 放在下方 (负偏移，va='top') - 这是您提供的原始代码逻辑
            ax2.text(psi, g_val - y_range_gdp * 0.05, f'{g_val:.4f}%',
                     ha='center', va='top', color=color_gdp, fontsize=15, fontweight='bold')

        # --- 红色垂直虚线 (点到直线) ---
        if j > 0:
            diff_pct = (c_val - baseline_y) / baseline_y * 100

            # 绘制红色虚线 (无偏移)
            ax1.plot([psi, psi], [baseline_y, c_val], color=color_annot, linestyle='--', linewidth=2.5)

            # 标注百分比文字 (在虚线右侧)
            mid_y = (baseline_y + c_val) / 2

            # 文本向右偏移 0.005
            ax1.text(psi + 0.005, mid_y, f'{diff_pct:.2f}%',
                     ha='left', va='center', color=color_annot, fontsize=14, fontweight='bold')

    if i == 0:
        lines_labels = [l1, l2]

plt.tight_layout()
plt.subplots_adjust(bottom=0.12)

# 图例
fig.legend(lines_labels, ['Life Cycle Socio-Economic Cost ', 'Gross output value contribution share'],
           loc='lower center', ncol=2, frameon=False, fontsize=26)
# --- 保存为 SVG 格式 ---
plt.savefig('chart_output1.svg', format='svg', bbox_inches='tight')
plt.show()