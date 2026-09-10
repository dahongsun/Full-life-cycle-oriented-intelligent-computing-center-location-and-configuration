import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib
from matplotlib import rcParams

# ==========================================
# 1. 全局设置：字体与负号
# ==========================================
rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

# ========================= 1. 全局设置 =========================
config = {
    "font.family": "serif",
    "font.serif": ["Times New Roman", "SimSun", "SimHei"],
    "font.sans-serif": ["SimHei"],
    "axes.unicode_minus": False,
    "mathtext.fontset": "stix",
}
plt.rcParams.update(config)
# ==========================================
# 2. 数据准备
# ==========================================
# 省份名称 (代码顺序)
provinces = [
    "北京", "天津", "河北", "山西", "辽宁", "吉林",
    "黑龙江", "上海", "江苏", "浙江", "安徽", "福建",
    "江西", "山东", "河南", "湖北", "湖南", "广东",
    "广西", "海南", "重庆", "四川", "贵州", "云南",
    "陕西", "甘肃", "青海", "宁夏", "新疆", "内蒙古"
]

# 绿电占比 (1 - alpha_coal)
alpha_coal = np.array([
    0.9593, 0.9797, 0.8645, 0.9049, 0.8670, 0.7740, 0.8545, 0.9769, 0.9512, 0.8967,
    0.9352, 0.6999, 0.8161, 0.9494, 0.9356, 0.4064, 0.5866, 0.8918, 0.4721, 0.8478,
    0.6422, 0.0992, 0.6014, 0.0811, 0.8902, 0.5268, 0.2484, 0.8242, 0.7752, 0.8445
])
green_ratio = 1 - alpha_coal

# 设备乘数 (m_equip)
multipliers = np.array([
    5.0137, 4.5163, 2.9711, 3.2173, 2.6048, 3.2688,
    2.7142, 4.7486, 3.5741, 3.5371, 4.0347, 3.9770,
    3.9915, 4.2853, 4.3810, 3.5774, 2.9689, 4.0483,
    3.4172, 3.1172, 4.4020, 3.6096, 3.1799, 3.1641,
    2.9335, 3.1390, 3.4739, 2.0000, 3.5467, 3.1412
])

# 建设规模 (Capacity Built)
capacity_per_scale = np.array([3000, 10000, 20000])
x_sol = np.array([
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
    [0, 1, 2],
    [0, 0, 6],
    [0, 0, 0],
    [0, 1, 3],
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
    [1, 0, 6],
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
    [1, 0, 19],
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
    [1, 1, 18],
    [0, 0, 0],
    [2, 0, 12],
    [0, 0, 0],
    [2, 1, 1],
    [0, 0, 1],
    [0, 1, 2],
    [1, 0, 1],
    [0, 1, 7]
])
capacity_built = np.dot(x_sol, capacity_per_scale)
capacity_built =[ 64306.,  25957.,  63118.,  30997.,  45667.,  21859.,  24954.,
        69950., 181048., 112666.,  66063.,  75148.,  44125., 129460.,
        96996.,  81625.,  70568., 194135.,  38125.,   9538.,  41934.,
        83334.,  29823.,  40559.,  46505.,  15742.,   5337.,   6819.,
        24881.,  31352.]
df_het = pd.DataFrame({
    'Province': provinces,
    'Green_Ratio': green_ratio,
    'Multiplier': multipliers,
    'Capacity': capacity_built
})

# ==========================================
# 3. 绘制异质性散点图
# ==========================================
plt.figure(figsize=(14, 9))  # 稍微加大画布尺寸以容纳所有标签

# 气泡大小
sizes = df_het['Capacity'] / 80
sizes = np.maximum(sizes, 50)  # 调大一点最小气泡，让每个省都能看到点

# 散点图
scatter = plt.scatter(
    df_het['Green_Ratio'],
    df_het['Multiplier'],
    s=sizes,
    c=df_het['Green_Ratio'],
    cmap='viridis_r',
    alpha=0.7,
    edgecolors='black',
    linewidth=0.5
)

# 标签 (标注所有省份)
# 为了防止重叠，我们可以手动设置一些偏移，或者简单地全部标注
# 这里采用全部标注，并对已知密集的点做一点微调
for i, row in df_het.iterrows():
    offset = (0, 8)  # 默认在点上方

    # 手动微调密集区域或边缘省份的标签位置
    if row['Province'] == '北京':
        offset = (0, -15)
    elif row['Province'] == '上海':
        offset = (0, -15)
    elif row['Province'] == '天津':
        offset = (15, 0)
    elif row['Province'] == '河北':
        offset = (-15, 0)
    elif row['Province'] == '宁夏':
        offset = (0, -18)
    elif row['Province'] == '山东':
        offset = (-20, 0)
    elif row['Province'] == '江苏':
        offset = (20, 0)

    plt.annotate(
        row['Province'],
        (row['Green_Ratio'], row['Multiplier']),
        xytext=offset, textcoords='offset points',
        fontsize=9, ha='center', fontweight='normal'  # 字体稍微改小一点，避免拥挤
    )

# 重新划分象限线
plt.axvline(x=0.4, color='gray', linestyle='--', alpha=0.6)
plt.axhline(y=3.5, color='gray', linestyle='--', alpha=0.6)

# 区域标注
plt.text(0.8, 4.5, '理想区域 (High Green, High Econ)\n(湖北、四川)', fontsize=12, color='green', ha='center',
         fontweight='bold', bbox=dict(facecolor='white', alpha=0.6))
plt.text(0.2, 4.5, '经济引擎区 (High Econ)\n(北京、上海、天津)', fontsize=12, color='#d62728', ha='center', fontweight='bold',
         bbox=dict(facecolor='white', alpha=0.6))
plt.text(0.8, 2.5, '资源输出区 (High Green)\n(贵州、甘肃、云南)', fontsize=12, color='#1f77b4', ha='center', fontweight='bold',
         bbox=dict(facecolor='white', alpha=0.6))
plt.text(0.2, 2.2, '低效/潜力区域\n(内蒙古、山西、辽宁)', fontsize=12, color='gray', ha='center', fontweight='bold',
         bbox=dict(facecolor='white', alpha=0.6))

# 标签
plt.xlabel('清洁能源占比 (Green Power Ratio, 1-$\\alpha$)', fontsize=14, fontweight='bold')
plt.ylabel('产业经济乘数 (Economic Multiplier)', fontsize=14, fontweight='bold')
plt.title('省域资源-经济异质性与智算中心选址分布', fontsize=16, pad=20)

# Colorbar
cbar = plt.colorbar(scatter)
cbar.set_label('清洁能源占比', fontsize=12)

plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('Figure7_Heterogeneity_Scatter_AllLabels.svg', dpi=300,format='svg')
plt.show()