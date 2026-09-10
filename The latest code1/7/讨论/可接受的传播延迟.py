# -*- coding: utf-8 -*-
import math
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, MaxNLocator, FormatStrFormatter

# --- 1. 全局设置 ---
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams.update({'font.size': 18})

# --- 2. 数据准备 ---
raw_data = {
    '1': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761651477040, 4594690154581, 4501758822445,
            4510698782058, 4506084708564, 4492655261104
        ],
        'carbon': [
            1670944724901, 1439550363992, 1387782401179,
            1364596685443, 1364365862037, 1375035514618
        ],
        'gdp': [
            0.295069, 0.254992, 0.247161,
            0.242800, 0.242800, 0.242809
        ],
        'socio_cost': [
            6432596201941, 6034240518574, 5889541223624,
            5875295467501, 5870450570601, 5867690775722
        ]
    },
    '1.02': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761651477040, 4594690154581, 4502108241491,
            4501674037736, 4499101382371, 4483901657796
        ],
        'carbon': [
            1670944724901, 1439550363992, 1387455851385,
            1377920986948, 1375791262058, 1388070956170
        ],
        'gdp': [
            0.295069, 0.254992, 0.247656,
            0.247656, 0.247656, 0.247656
        ],
        'socio_cost': [
            6432596201941, 6034240518574, 5889564092876,
            5879595024684, 5874892644428, 5871972613966
        ]
    },
    '1.04': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761651477040, 4594690154581, 4503473611288,
            4493515147743, 4490117473526, 4475508636517
        ],
        'carbon': [
            1670944724901, 1439550363992, 1395215265706,
            1394450734413, 1393304789858, 1404861093991
        ],
        'gdp': [
            0.295069, 0.254992, 0.252512,
            0.252512, 0.252512, 0.252512
        ],
        'socio_cost': [
            6432596201941, 6034240518574, 5898688876994,
            5887965882156, 5883422263383, 5880369730508
        ]
    },
    '1.06': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761651477040, 4588525615800, 4509075225129,
            4492138330138, 4485467527546, 4487100383438
        ],
        'carbon': [
            1670944724901, 1447001094305, 1400378868341,
            1407034960020, 1409242560834, 1404447165572
        ],
        'gdp': [
            0.295069, 0.257533, 0.257368,
            0.257368, 0.257368, 0.257368
        ],
        'socio_cost': [
            6432596201941, 6035526710105, 5909454093471,
            5899173290158, 5894710088380, 5891547549010
        ]
    },
    '1.08': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761651477040, 4583983328813, 4515787804617,
            4497626457779, 4502000706998, 4479924912186
        ],
        'carbon': [
            1670944724901, 1454695591365, 1404515873296,
            1413278376652, 1404429054533, 1423372978452
        ],
        'gdp': [
            0.295069, 0.262224, 0.262224,
            0.262224, 0.262224, 0.262224
        ],
        'socio_cost': [
            6432596201941, 6038678920177, 5920303677913,
            5910904834431, 5906429761532, 5903297890638
        ]
    },
    '1.1': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761651477040, 4579648548197, 4509104671103,
            4518644200678, 4513149798827, 4502474215689
        ],
        'carbon': [
            1670944724901, 1462188138810, 1422706283240,
            1404343883013, 1405360021591, 1412917208848
        ],
        'gdp': [
            0.295069, 0.267080, 0.267080,
            0.267080, 0.267080, 0.267080
        ],
        'socio_cost': [
            6432596201941, 6041836687008, 5931810954343,
            5922988083691, 5918509820417, 5915391424538
        ]
    }
}

# --- 归一化处理 ---
for k, v in raw_data.items():
    base_cost = v['cost'][0]
    base_carbon = v['carbon'][0]
    base_socio = v['socio_cost'][0]

    v['cost'] = [x / base_cost * 100 for x in v['cost']]
    v['carbon'] = [x / base_carbon * 100 for x in v['carbon']]
    v['socio_cost'] = [x / base_socio * 100 for x in v['socio_cost']]

all_normalized_values = []
for v in raw_data.values():
    all_normalized_values.extend(v['cost'])
    all_normalized_values.extend(v['carbon'])
    all_normalized_values.extend(v['socio_cost'])

left_axis_lower = float(math.floor(min(all_normalized_values) - 1.0))
left_axis_upper = 101.5
left_start_ratio = (100.0 - left_axis_lower) / (left_axis_upper - left_axis_lower)
left_axis_ticks = list(range(int(left_axis_lower), 101, 4))

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

color_socio = '#7030A0'
color_cost = '#4472C4'
color_carbon = '#548235'
color_gdp = '#ED7D31'
color_drop = '#C00000'

lines_labels_list = []

for i, key in enumerate(keys):
    ax1 = axes[i]
    data = raw_data[key]

    delays_x = list(range(len(data['delays'])))
    carbon_x = [x if x == 0 else x - 0.035 for x in delays_x]
    gdp_x = [x if x == 0 else x + 0.035 for x in delays_x]
    socio_costs = data['socio_cost']
    costs = data['cost']
    carbons = data['carbon']
    gdps = data['gdp']

    l4, = ax1.plot(
        delays_x, socio_costs,
        color=color_socio, marker='D', markersize=8,
        linewidth=3, label='Normalized Socio-Economic Cost',
        zorder=3
    )

    l1, = ax1.plot(
        delays_x, costs,
        color=color_cost, marker='o', markersize=8,
        linewidth=3, label='Normalized Total Costs',
        zorder=3
    )

    l2, = ax1.plot(
        carbon_x, carbons,
        color=color_carbon, marker='s', markersize=8,
        linewidth=3.5, linestyle='--',
        label='Normalized Total Social Cost of Carbon',
        zorder=2
    )

    # 修改1：轴名称保持你的原文不变
    ax1.set_ylabel('Normalized Value (% of 1ms)', color='black', fontsize=20)

    # 修改2：左轴范围收紧，使曲线变化更清楚
    ax1.set_ylim(left_axis_lower, left_axis_upper)
    ax1.set_yticks(left_axis_ticks)

    # 修改3：补齐上边框、上刻度和次刻度
    ax1.spines['top'].set_visible(True)
    ax1.spines['bottom'].set_visible(True)
    ax1.spines['left'].set_visible(True)
    ax1.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax1.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax1.tick_params(
        axis='x', which='major',
        top=True, bottom=True, labeltop=False,
        direction='in', length=6, width=1.1,
        labelsize=18
    )
    ax1.tick_params(
        axis='x', which='minor',
        top=True, bottom=True,
        direction='in', length=3, width=0.8
    )
    ax1.tick_params(
        axis='y', which='major',
        left=True, direction='in',
        length=6, width=1.1,
        labelcolor='black', labelsize=18
    )
    ax1.tick_params(
        axis='y', which='minor',
        left=True, direction='in',
        length=3, width=0.8
    )

    # --- 右轴: 总产值贡献份额 ---
    ax2 = ax1.twinx()
    l3, = ax2.plot(
        gdp_x, gdps,
        color=color_gdp, marker='^', markersize=9,
        linewidth=3, label='GDP Increase',
        zorder=4
    )

    # 轴名称保持你的原文不变
    ax2.set_ylabel(
        'Gross output value contribution share (%)',
        color='black', fontsize=20
    )

    min_g, max_g = min(gdps), max(gdps)
    right_axis_lower = max(0.0, min_g - 0.020)
    right_axis_upper = right_axis_lower + (gdps[0] - right_axis_lower) / left_start_ratio
    right_axis_upper = max(right_axis_upper, max_g + 0.004)
    ax2.set_ylim(right_axis_lower, right_axis_upper)
    ax2.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax2.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

    # 修改4：补齐右边框、右刻度和次刻度
    ax2.spines['right'].set_visible(True)
    ax2.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax2.tick_params(
        axis='y', which='major',
        right=True, direction='in',
        length=6, width=1.1,
        labelcolor='black', labelsize=18
    )
    ax2.tick_params(
        axis='y', which='minor',
        right=True, direction='in',
        length=3, width=0.8
    )

    # --- X轴设置 ---
    ax1.set_xticks(delays_x)
    ax1.set_xticklabels(data['delays'])
    ax1.set_xlim(-0.25, 5.35)
    ax1.set_title(titles[i], y=-0.20, fontsize=22)

    # --- 绘制投影线 ---
    for j, _ in enumerate(delays_x):
        ax1.vlines(
            x=j, ymin=left_axis_lower, ymax=socio_costs[j],
            colors=color_drop, linestyles='--',
            alpha=0.35, linewidth=1.2
        )

    label_box = dict(facecolor='white', edgecolor='none', alpha=0.82, pad=0.25)

    # --- 修改5：给所有点标数值，并错开标签 ---
    for j, _ in enumerate(delays_x):
        socio_val = socio_costs[j]
        c_val = costs[j]
        carb_val = carbons[j]
        g_val = gdps[j]

        # 1ms只标注总产值贡献份额
        if j != 0:
            # 紫色LCSC放在线的下方
            x_socio = j - 0.05 if j == 5 else j
            ha_socio = 'right' if j == 5 else 'center'
            ax1.text(
                x_socio, socio_val - 0.65,
                f'{socio_val:.1f}%',
                ha=ha_socio, va='top',
                color=color_socio,
                fontsize=14, fontweight='bold',
                bbox=label_box,
                zorder=10
            )

            # 蓝色LCC放在线的上方
            x_cost = j - 0.02 if j == 5 else j
            ha_cost = 'right' if j == 5 else 'center'
            ax1.text(
                x_cost, c_val + 0.45,
                f'{c_val:.1f}%',
                ha=ha_cost, va='bottom',
                color=color_cost,
                fontsize=14, fontweight='bold',
                bbox=label_box,
                zorder=10
            )

            # 绿色TSCC放在线的上方；3ms额外向上移动
            carbon_offset = 1.00 if j == 1 else 0.70
            x_carbon = carbon_x[j] - 0.08 if j >= 2 else carbon_x[j] - 0.04
            ha_carbon = 'right'
            y_carbon = max(carb_val - carbon_offset, ax1.get_ylim()[0] + 0.90)
            ax1.text(
                x_carbon, y_carbon,
                f'{carb_val:.1f}%',
                ha=ha_carbon, va='top',
                color=color_carbon,
                fontsize=14, fontweight='bold',
                bbox=label_box,
                zorder=10
            )

        # 橙色总产值贡献份额放在线的下方
        x_gdp = gdp_x[j] + 0.04 if j >= 2 else gdp_x[j]
        ha_gdp = 'left' if j >= 2 else 'center'
        gdp_offset = (max_g - min_g) * 0.035 if max_g != min_g else 0.00055

        # 橙色总产值贡献份额放在线的下方
        if j == 0:  # 只移动 1ms 的产值贡献份额
            x_gdp = gdp_x[j] + 0.55  # 向右移动；想向左就改成 j - 0.15
            y_gdp = g_val - gdp_offset * 0  # 向下移动；想向上就减小倍数
            ha_gdp = 'center'
            va_gdp = 'bottom'
        elif j == 1:
            x_gdp = gdp_x[j] + 0.12
            y_gdp = g_val + gdp_offset
            ha_gdp = 'left'
            va_gdp = 'bottom'
        elif j == 5:
            x_gdp = gdp_x[j] + 0.2
            y_gdp = g_val + gdp_offset
            ha_gdp = 'right'
            va_gdp = 'bottom'
        else:
            x_gdp = gdp_x[j] + 0.04 if j >= 2 else gdp_x[j] + 0.04
            y_gdp = g_val + gdp_offset
            ha_gdp = 'left'
            va_gdp = 'bottom'
        y_gdp = min(y_gdp, ax2.get_ylim()[1] - 0.004)
        ax2.text(
            x_gdp, y_gdp,
            f'{g_val:.4f}%',
            ha=ha_gdp, va=va_gdp,
            color=color_gdp,
            fontsize=14, fontweight='bold',
            bbox=label_box,
            zorder=10
        )

    if i == 0:
        lines_labels_list = [l4, l1, l2, l3]

plt.tight_layout()
plt.subplots_adjust(bottom=0.11)

fig.legend(
    lines_labels_list,
    [
        'Normalized Life Cycle Socio-Economic Cost',
        'Normalized Total lifecycle cost',
        'Normalized Total Carbon social cost',
        'Gross output value contribution share'
    ],
    loc='lower center',
    ncol=2,
    frameon=False,
    fontsize=20
)

# --- 4. 保存图片 ---
plt.savefig(
    'Figure15_按照你的原代码修改版.svg',
    format='svg',
    bbox_inches='tight'
)
plt.savefig(
    'Figure15_按照你的原代码修改版.png',
    dpi=600,
    bbox_inches='tight'
)
plt.show()
