import matplotlib.pyplot as plt

# --- 1. 全局设置 ---
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['mathtext.fontset'] = 'stix'
# 全局字号保持 18
plt.rcParams.update({'font.size': 18})

# --- 2. 数据准备 ---
raw_data = {
    '1': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761558297341, 4549887240126, 4463896118970,
            4466506404908, 4462475081407, 4459826548955
        ],
        'carbon': [
            1198960176614, 1066451156020, 1024419057761,
            1013864487183, 1013212965073, 1012179349707
        ],
        'gdp': [
            0.313879, 0.274506, 0.265720,
            0.261740, 0.261581, 0.261500
        ],
        'socio_cost': [
            5960518473955, 5616338396146, 5488315176731,
            5480370892091, 5475688046480, 5472005898662
        ]
    },
    '1.02': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761558297341, 4549887240126, 4462115799489,
            4455268225047, 4450958980371, 4447233589184
        ],
        'carbon': [
            1198960176614, 1066451156020, 1026329497191,
            1025516512065, 1025258646072, 1025299646435
        ],
        'gdp': [
            0.313879, 0.274506, 0.266738,
            0.266730, 0.266730, 0.266930
        ],
        'socio_cost': [
            5960518473955, 5616338396146, 5488445296679,
            5480784737112, 5476217626443, 5472533235619
        ]
    },
    '1.04': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761558297341, 4549887240126, 4451973187389,
            4439625306602, 4435998306993, 4432386624089
        ],
        'carbon': [
            1198960176614, 1066451156020, 1041462338718,
            1042678299489, 1041899681602, 1042092550757
        ],
        'gdp': [
            0.313879, 0.274506, 0.271961,
            0.271960, 0.271960, 0.271960
        ],
        'socio_cost': [
            5960518473955, 5616338396146, 5493435526107,
            5482303606091, 5477897988595, 5474479174847
        ]
    },
    '1.06': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761558297341, 4544803454405, 4455594526149,
            4446506525542, 4438455102497, 4436288394066
        ],
        'carbon': [
            1198960176614, 1071844685804, 1046820549859,
            1046633697735, 1050301482254, 1049295451159
        ],
        'gdp': [
            0.313879, 0.277327, 0.277190,
            0.277190, 0.277190, 0.277190
        ],
        'socio_cost': [
            5960518473955, 5616648140209, 5502415076008,
            5493140223276, 5488756584751, 5485583845225
        ]
    },
    '1.08': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761558297341, 4543295114712, 4465000595335,
            4456114381130, 4452693502563, 4449655326572
        ],
        'carbon': [
            1198960176614, 1075134036047, 1048625645512,
            1049145902597, 1048318965847, 1048275415538
        ],
        'gdp': [
            0.313879, 0.282420, 0.282420,
            0.282420, 0.282420, 0.282420
        ],
        'socio_cost': [
            5960518473955, 5618429150759, 5513626240847,
            5505260283728, 5501012468410, 5497930742110
        ]
    },
    '1.1': {
        'delays': ['1ms', '3ms', '5ms', '7ms', '9ms', '11ms'],
        'cost': [
            4761558297341, 4551525655426, 4470806925668,
            4469831676245, 4465339832032, 4464062823636
        ],
        'carbon': [
            1198960176614, 1070652472608, 1054700355738,
            1048524307982, 1048911249982, 1046941047917
        ],
        'gdp': [
            0.313879, 0.287681, 0.287650,
            0.287650, 0.287650, 0.287650
        ],
        'socio_cost': [
            5960518473955, 5622178128034, 5525507281406,
            5518355984227, 5514251082014, 5511003871554
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
# 颜色定义 (新增 socio_cost 颜色)
color_socio = '#7030A0'   # 紫色
color_cost = '#4472C4'    # 蓝色
color_carbon = '#548235'  # 绿色
color_gdp = '#ED7D31'     # 橙色
color_drop = '#C00000'    # 红色虚线

lines_labels_list = []

for i, key in enumerate(keys):
    ax1 = axes[i]
    data = raw_data[key]

    delays_x = range(len(data['delays']))
    socio_costs = data['socio_cost']
    costs = data['cost']
    carbons = data['carbon']
    gdps = data['gdp']

    # --- 左轴: Normalized Socio, Cost & Carbon ---
    # 先画最高的那条线 Socio-Economic Cost
    l4, = ax1.plot(delays_x, socio_costs, color=color_socio, marker='D', markersize=8,
                   linewidth=3, label='Normalized Socio-Economic Cost')

    l1, = ax1.plot(delays_x, costs, color=color_cost, marker='o', markersize=8,
                   linewidth=3, label='Normalized Total Costs')

    l2, = ax1.plot(delays_x, carbons, color=color_carbon, marker='s', markersize=8,
                   linewidth=3.5, linestyle='--', label='Normalized Total Social Cost of Carbon')

    ax1.set_ylabel('Normalized Value (% of 1ms)', color='black', fontsize=20)
    ax1.tick_params(axis='y', labelcolor='black', labelsize=18)
    ax1.tick_params(axis='x', labelsize=18)

    # 调高Y轴上限，为了容纳 125% 左右的 socio_cost
    ax1.set_ylim(0, 110)

    # --- 右轴: GDP ---
    ax2 = ax1.twinx()
    l3, = ax2.plot(delays_x, gdps, color=color_gdp, marker='^', markersize=9,
                   linewidth=3, label='GDP Increase')

    ax2.set_ylabel('Gross output value contribution share (%)', color='black', fontsize=20)
    ax2.tick_params(axis='y', labelcolor='black', labelsize=18)

    min_g, max_g = min(gdps), max(gdps)
    margin_g = (max_g - min_g) * 2 if max_g != min_g else max_g * 0.5
    ax2.set_ylim(min_g - margin_g, max_g + margin_g)

    # --- X轴设置 ---
    ax1.set_xticks(delays_x)
    ax1.set_xticklabels(data['delays'])
    ax1.set_title(titles[i], y=-0.20, fontsize=22)

    # --- 绘制和标注 ---
    ylim_cost = ax1.get_ylim()
    y_span_cost = ylim_cost[1] - ylim_cost[0]

    ylim_gdp = ax2.get_ylim()
    y_span_gdp = ylim_gdp[1] - ylim_gdp[0]

    for j, _ in enumerate(delays_x):
        socio_val = socio_costs[j]
        c_val = costs[j]
        carb_val = carbons[j]
        g_val = gdps[j]

        # 投影线 (高度提到 socio_val)
        ax1.vlines(x=j, ymin=0, ymax=socio_val, colors=color_drop, linestyles='--', alpha=0.6, linewidth=1.5)

        # 1. Socio Cost 标注 - 紫色 (放在最上方)
        ax1.text(j, socio_val + y_span_cost * 0.025, f'{socio_val:.1f}%',
                 ha='center', va='bottom', color=color_socio, fontsize=16, fontweight='bold')

        # 2. Cost 标注 (Total Costs) - 蓝色
        ax1.text(j, c_val + y_span_cost * 0.025, f'{c_val:.1f}%',
                 ha='center', va='bottom', color=color_cost, fontsize=16, fontweight='bold')

        # 3. Carbon 标注 (Carbon Costs) - 绿色
        offset_y_carb = y_span_cost * 0.025
        if abs(c_val - carb_val) < 2.0:
            ax1.text(j + 0.15, carb_val + offset_y_carb, f'{carb_val:.1f}%',
                     ha='left', va='bottom', color=color_carbon, fontsize=16, fontweight='bold')
        else:
            ax1.text(j, carb_val + offset_y_carb, f'{carb_val:.1f}%',
                     ha='center', va='bottom', color=color_carbon, fontsize=16, fontweight='bold')

        # 4. GDP 标注 - 橙色
        ax2.text(j, g_val - y_span_gdp * 0.05, f'{g_val:.4f}%',
                 ha='center', va='top', color=color_gdp, fontsize=16, fontweight='bold')

    if i == 0:
        # 按图例想要的顺序排列
        lines_labels_list = [l4, l1, l2, l3]

plt.tight_layout()

# 将底部留白加大，防止两行图例被切掉
plt.subplots_adjust(bottom=0.11)

# 图例修改为2排 (ncol=2)
fig.legend(lines_labels_list,
           ['Normalized Life Cycle Socio-Economic Cost', 'Normalized Total lifecycle cost',
            'Normalized Total Carbon social cost', 'Gross output value contribution share'],
           loc='lower center', ncol=2, frameon=False, fontsize=20)

plt.savefig('chart_psi_normalized_fixed_labels.svg', format='svg', bbox_inches='tight')
plt.show()