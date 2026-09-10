import matplotlib.pyplot as plt
import pandas as pd
import re
import numpy as np
# 解决中文显示问题
# 设置字体列表：优先尝试 Times New Roman，如果找不到字符（如汉字），则使用 SimHei（黑体）
plt.rcParams['font.sans-serif'] = ['Times New Roman', 'SimHei']

# 或者使用微软的一套字体方案，效果通常更好：
# plt.rcParams['font.sans-serif'] = ['Times New Roman', 'Microsoft YaHei']

# 解决负号 '-' 显示为方块的问题
plt.rcParams['axes.unicode_minus'] = False

# 1. 数据解析 (Same as before)
raw_data = """
\\tau=1ms, \\alpha_i=0: 全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.4038%,总成本（元）: 5,749,164,820,866
  ├─ 建设CAPEX（元）: 92,895,487,250
  ├─ 电费（元, 生命周期）: 5,640,889,464,186
  ├─ 碳社会成本（元, 生命周期）: 0
  └─ 传输费（元）: 15,379,869,430 
\\tau=1ms, \\alpha_i=0.25：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.4185%，总成本（元）: 6,312,598,791,822
  ├─ 建设CAPEX（元）: 93,423,470,600
  ├─ 电费（元, 生命周期）: 5,821,435,740,315
  ├─ 碳社会成本（元, 生命周期）: 383,371,642,001
  └─ 传输费（元）: 14,367,938,907
\\tau=1ms, \\alpha_i=0.5：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.4293%，总成本（元）: 6,864,865,079,680
  ├─ 建设CAPEX（元）: 93,473,093,150
  ├─ 电费（元, 生命周期）: 6,004,126,011,980
  ├─ 碳社会成本（元, 生命周期）: 767,186,672,804
  └─ 传输费（元）: 79,301,746
\\tau=1ms, \\alpha_i=0.75，全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.4391%，总成本（元）: 7,409,623,391,215
  ├─ 建设CAPEX（元）: 93,231,960,200
  ├─ 电费（元, 生命周期）: 6,160,853,285,802
  ├─ 碳社会成本（元, 生命周期）: 1,150,886,808,292
  └─ 传输费（元）: 4,651,336,921
\\tau=1ms, \\alpha_i=1: 全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.4436%,总成本（元）: 7,934,757,756,040
  ├─ 建设CAPEX（元）: 97,126,743,250
  ├─ 电费（元, 生命周期）: 6,297,692,188,079
  ├─ 碳社会成本（元, 生命周期）: 1,534,962,389,445
  └─ 传输费（元）: 4,976,435,265

\\tau=3ms，\\alpha_i=0：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3401%，总成本（元）: 5,249,133,957,615
  ├─ 建设CAPEX（元）: 90,426,610,250
  ├─ 电费（元, 生命周期）: 4,934,746,510,602
  ├─ 碳社会成本（元, 生命周期）: 0
  └─ 传输费（元）: 223,960,836,763
\\tau=3ms, \\alpha_i=0.25：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3716%，总成本（元）: 5,919,745,696,257
  ├─ 建设CAPEX（元）: 89,533,409,950
  ├─ 电费（元, 生命周期）: 5,400,028,302,857
  ├─ 碳社会成本（元, 生命周期）: 386,085,082,734
  └─ 传输费（元）: 44,098,900,716
\\tau=3ms, \\alpha_i=0.5：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3927%，总成本（元）: 6,557,493,881,422
  ├─ 建设CAPEX（元）: 89,353,390,500
  ├─ 电费（元, 生命周期）: 5,689,280,144,545
  ├─ 碳社会成本（元, 生命周期）: 772,454,570,049
  └─ 传输费（元）: 6,405,776,328
\\tau=3ms, \\alpha_i=0.75：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.4006%，总成本（元）: 7,153,736,471,247
  ├─ 建设CAPEX（元）: 89,057,517,600
  ├─ 电费（元, 生命周期）: 5,831,156,476,925
  ├─ 碳社会成本（元, 生命周期）: 1,156,370,331,255
  └─ 传输费（元）: 77,152,145,467
\\tau=3ms, \\alpha_i=1：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.4023%，总成本（元）: 7,652,054,985,931
  ├─ 建设CAPEX（元）: 87,402,147,350
  ├─ 电费（元, 生命周期）: 5,909,434,991,355
  ├─ 碳社会成本（元, 生命周期）: 1,537,432,693,858
  └─ 传输费（元）: 117,785,153,368

\\tau=5ms, \\alpha_i=0：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3442%，总成本（元）: 5,149,555,840,118
  ├─ 建设CAPEX（元）: 91,593,466,450
  ├─ 电费（元, 生命周期）: 4,956,563,250,663
  ├─ 碳社会成本（元, 生命周期）: 0
  └─ 传输费（元）: 101,399,123,005
\\tau=5ms, \\alpha_i=0.25：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3644%，总成本（元）: 5,838,668,730,778
  ├─ 建设CAPEX（元）: 89,720,180,300
  ├─ 电费（元, 生命周期）: 5,326,698,291,611
  ├─ 碳社会成本（元, 生命周期）: 386,656,046,878
  └─ 传输费（元）: 35,594,211,990
\\tau=5ms, \\alpha_i=0.5：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3830%，总成本（元）: 6,467,756,717,985
  ├─ 建设CAPEX（元）: 90,027,050,050
  ├─ 电费（元, 生命周期）: 5,604,301,460,662
  ├─ 碳社会成本（元, 生命周期）: 773,348,905,527
  └─ 传输费（元）: 79,301,746
\\tau=5ms, \\alpha_i=0.75：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3900%，总成本（元）: 7,051,578,588,761
  ├─ 建设CAPEX（元）: 89,751,384,950
  ├─ 电费（元, 生命周期）: 5,756,160,905,825
  ├─ 碳社会成本（元, 生命周期）: 1,155,448,142,168
  └─ 传输费（元）: 50,218,155,818
\\tau=5ms, \\alpha_i=1：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3828%，总成本（元）: 7,546,300,860,687
  ├─ 建设CAPEX（元）: 87,693,798,100
  ├─ 电费（元, 生命周期）: 5,714,747,337,842
  ├─ 碳社会成本（元, 生命周期）: 1,538,205,782,963
  └─ 传输费（元）: 205,653,941,782

\\tau=7ms, \\alpha_i=0：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3503%，总成本（元）: 5,073,833,132,930
  ├─ 建设CAPEX（元）: 95,887,048,350
  ├─ 电费（元, 生命周期）: 4,956,227,486,649
  ├─ 碳社会成本（元, 生命周期）: 0
  └─ 传输费（元）: 21,718,597,931
\\tau=7ms, \\alpha_i=0.25：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3702%，总成本（元）: 5,817,068,907,808
  ├─ 建设CAPEX（元）: 91,832,878,000
  ├─ 电费（元, 生命周期）: 5,335,940,671,684
  ├─ 碳社会成本（元, 生命周期）: 388,753,405,158
  └─ 传输费（元）: 541,952,966
\\tau=7ms, \\alpha_i=0.5：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3819%，总成本（元）: 6,462,770,830,287
  ├─ 建设CAPEX（元）: 90,016,282,550
  ├─ 电费（元, 生命周期）: 5,599,777,043,419
  ├─ 碳社会成本（元, 生命周期）: 772,898,202,573
  └─ 传输费（元）: 79,301,746
\\tau=7ms, \\alpha_i=0.75：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3893%，总成本（元）: 7,047,050,020,941
  ├─ 建设CAPEX（元）: 89,260,189,450
  ├─ 电费（元, 生命周期）: 5,751,430,405,756
  ├─ 碳社会成本（元, 生命周期）: 1,154,584,712,790
  └─ 传输费（元）: 51,774,712,945
\\tau=7ms, \\alpha_i=1：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3824%，总成本（元）: 7,543,910,164,695
  ├─ 建设CAPEX（元）: 87,594,644,500
  ├─ 电费（元, 生命周期）: 5,703,988,298,255
  ├─ 碳社会成本（元, 生命周期）: 1,536,506,234,026
  └─ 传输费（元）: 215,820,987,915

\\tau=9ms, \\alpha_i=0：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3494%，总成本（元）: 5,072,924,813,128
  ├─ 建设CAPEX（元）: 95,668,098,600
  ├─ 电费（元, 生命周期）: 4,951,921,115,390
  ├─ 碳社会成本（元, 生命周期）: 0
  └─ 传输费（元）: 25,335,599,137
\\tau=9ms, \\alpha_i=0.25：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3692%，总成本（元）: 5,810,658,185,828
  ├─ 建设CAPEX（元）: 91,654,404,250
  ├─ 电费（元, 生命周期）: 5,329,947,435,510
  ├─ 碳社会成本（元, 生命周期）: 388,439,011,450
  └─ 传输费（元）: 617,334,618
\\tau=9ms, \\alpha_i=0.5：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3814%，总成本（元）: 6,455,023,002,715
  ├─ 建设CAPEX（元）: 90,171,902,450
  ├─ 电费（元, 生命周期）: 5,592,045,236,937
  ├─ 碳社会成本（元, 生命周期）: 772,726,561,582
  └─ 传输费（元）: 79,301,746
\\tau=9ms, \\alpha_i=0.75：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3888%，总成本（元）: 7,040,265,009,972
  ├─ 建设CAPEX（元）: 89,189,418,250
  ├─ 电费（元, 生命周期）: 5,744,970,248,333
  ├─ 碳社会成本（元, 生命周期）: 1,154,373,322,790
  └─ 传输费（元）: 51,732,020,599
\\tau=9ms, \\alpha_i=1：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3819%，总成本（元）: 7,534,768,219,708
  ├─ 建设CAPEX（元）: 87,670,596,700
  ├─ 电费（元, 生命周期）: 5,694,551,948,898
  ├─ 碳社会成本（元, 生命周期）: 1,536,724,686,195
  └─ 传输费（元）: 215,820,987,915

\\tau=11ms, \\alpha_i=0：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3494%，总成本（元）: 5,072,924,813,128
  ├─ 建设CAPEX（元）: 95,668,098,600
  ├─ 电费（元, 生命周期）: 4,951,921,115,390
  ├─ 碳社会成本（元, 生命周期）: 0
  └─ 传输费（元）: 25,335,599,137
\\tau=11ms, \\alpha_i=0.25：全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3692%,总成本（元）: 5,810,658,185,828
  ├─ 建设CAPEX（元）: 91,654,404,250
  ├─ 电费（元, 生命周期）: 5,329,947,435,510
  ├─ 碳社会成本（元, 生命周期）: 388,439,011,450
  └─ 传输费（元）: 617,334,618
\\tau=11ms, \\alpha_i=0.5:全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3814%,总成本（元）: 6,454,972,930,599
  ├─ 建设CAPEX（元）: 90,171,902,450
  ├─ 电费（元, 生命周期）: 5,591,994,473,049
  ├─ 碳社会成本（元, 生命周期）: 772,727,253,353
  └─ 传输费（元）: 79,301,746
\\tau=11ms,\\alpha_i=0.75: 全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3887%,总成本（元）: 7,036,137,217,705
  ├─ 建设CAPEX（元）: 89,581,564,150
  ├─ 电费（元, 生命周期）: 5,740,397,895,488
  ├─ 碳社会成本（元, 生命周期）: 1,154,054,883,958
  └─ 传输费（元）: 52,102,874,110
\\tau=11ms, \\alpha_i=1: 全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：0.3815%,总成本（元）: 7,526,448,302,267
  ├─ 建设CAPEX（元）: 87,870,300,700
  ├─ 电费（元, 生命周期）: 5,686,932,138,534
  ├─ 碳社会成本（元, 生命周期）: 1,535,773,722,434
  └─ 传输费（元）: 215,872,140,599
"""

# Data Cleaning and Structuring
records = []
sections = raw_data.split('\\tau=')
for sec in sections:
    if not sec.strip(): continue

    # Extract tau
    tau_match = re.search(r'(\d+)ms', sec)
    if not tau_match: continue
    tau = int(tau_match.group(1))

    # Extract alpha_i, GDP, total_cost
    alpha_match = re.search(r'alpha_i=([\d\.]+).*?GDP.*?[：:]\s*([\d\.]+)%.*?总成本.*?[：:]\s*([\d,]+)', sec, re.DOTALL)
    if not alpha_match: continue
    alpha = float(alpha_match.group(1))
    gdp_growth = float(alpha_match.group(2))
    total_cost = float(alpha_match.group(3).replace(',', ''))

    # Extract cost components
    capex = float(re.search(r'建设CAPEX.*?[：:]\s*([\d,]+)', sec).group(1).replace(',', ''))
    elec = float(re.search(r'电费.*?[：:]\s*([\d,]+)', sec).group(1).replace(',', ''))
    carbon = float(re.search(r'碳社会成本.*?[：:]\s*([\d,]+)', sec).group(1).replace(',', ''))
    trans = float(re.search(r'传输费.*?[：:]\s*([\d,]+)', sec).group(1).replace(',', ''))

    records.append({
        'tau': tau,
        'alpha': alpha,
        'gdp_growth': gdp_growth,
        'total_cost': total_cost,
        'capex': capex,
        'elec': elec,
        'carbon': carbon,
        'trans': trans
    })

df = pd.DataFrame(records)
# Sort
df = df.sort_values(by=['tau', 'alpha'])

# 2. Plotting Settings
# Use standard fonts to avoid glyph issues, assuming the user can set Chinese fonts locally if needed,
# but here using standard sans-serif which usually falls back correctly or English labels if necessary.
# However, user provided Chinese labels. I will use a font property.
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'sans-serif']  # Try SimHei first for Chinese
plt.rcParams['axes.unicode_minus'] = False

# Create 2x3 subplots
fig, axes = plt.subplots(2, 3, figsize=(20, 12), constrained_layout=True)
axes = axes.flatten()

# Colors and Markers for lines
cost_styles = {
    'capex': {'color': '#4e79a7', 'marker': 'o', 'label': '建设CAPEX'},
    'elec': {'color': '#f28e2b', 'marker': 's', 'label': '电费(生命周期)'},
    'carbon': {'color': '#e15759', 'marker': '^', 'label': '碳社会成本'},
    'trans': {'color': '#76b7b2', 'marker': 'D', 'label': '传输费'},
    'total': {'color': '#595959', 'marker': 'x', 'label': '总成本', 'linewidth': 2.5, 'linestyle': '--'}
    # Distinct style for Total
}

# Unit scaling: Yuan -> 100 Million Yuan (亿元)
unit_scale = 1e8

for i, tau in enumerate(df['tau'].unique()):
    ax1 = axes[i]
    sub_df = df[df['tau'] == tau]

    x = sub_df['alpha']

    # Data for Left Axis (Costs)
    y_capex = sub_df['capex'] / unit_scale
    y_elec = sub_df['elec'] / unit_scale
    y_carbon = sub_df['carbon'] / unit_scale
    y_trans = sub_df['trans'] / unit_scale
    y_total = sub_df['total_cost'] / unit_scale

    # Plot Costs on Left Axis
    l1 = ax1.plot(x, y_capex, **cost_styles['capex'])
    l2 = ax1.plot(x, y_elec, **cost_styles['elec'])
    l3 = ax1.plot(x, y_carbon, **cost_styles['carbon'])
    l4 = ax1.plot(x, y_trans, **cost_styles['trans'])
    l5 = ax1.plot(x, y_total, **cost_styles['total'])

    ax1.set_ylabel('成本 (亿元)', fontsize=10)
    ax1.set_xlabel('能源结构 ($\\alpha$)', fontsize=10)
    ax1.set_title(f'时延 $\\tau$ = {tau}ms', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.grid(True, linestyle=':', alpha=0.6)

    # Plot GDP on Right Axis
    ax2 = ax1.twinx()
    y_gdp = sub_df['gdp_growth']
    l_gdp = ax2.plot(x, y_gdp, color='#59a14f', marker='*', linewidth=2, linestyle='-', label='GDP增幅(%)')

    ax2.set_ylabel('GDP增幅值 (%)', color='#2e5f35', fontsize=10)
    ax2.tick_params(axis='y', labelcolor='#2e5f35')

    # Adjust Y-axis limits slightly to make room for markers
    # Costs
    cost_max = y_total.max()
    ax1.set_ylim(-cost_max * 0.05, cost_max * 1.1)
    # GDP
    gdp_min, gdp_max = y_gdp.min(), y_gdp.max()
    ax2.set_ylim(gdp_min - (gdp_max - gdp_min) * 0.1, gdp_max + (gdp_max - gdp_min) * 0.1)

# Global Legend
lines = [l1[0], l2[0], l3[0], l4[0], l5[0], l_gdp[0]]
labels = [l.get_label() for l in lines]
fig.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, 1.02), ncol=6, fontsize=12)

plt.suptitle("不同时延($\\tau$)与能源结构($\\alpha$)下的智算中心成本及GDP效益趋势", y=1.05, fontsize=18)
plt.savefig('cost_gdp_line_analysis.png', dpi=300, bbox_inches='tight')
plt.show()