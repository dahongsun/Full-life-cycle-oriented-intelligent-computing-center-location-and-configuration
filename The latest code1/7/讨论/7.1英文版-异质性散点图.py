import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib
from matplotlib import rcParams

# ==========================================
# 1. Global Settings
# ==========================================
# Switch to Times New Roman for English academic style
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman']
rcParams['axes.unicode_minus'] = False

# ==========================================
# 2. Data Preparation
# ==========================================
# Provinces (Translated to English)
provinces = [
    "Beijing", "Tianjin", "Hebei", "Shanxi", "Liaoning", "Jilin",
    "Heilongjiang", "Shanghai", "Jiangsu", "Zhejiang", "Anhui", "Fujian",
    "Jiangxi", "Shandong", "Henan", "Hubei", "Hunan", "Guangdong",
    "Guangxi", "Hainan", "Chongqing", "Sichuan", "Guizhou", "Yunnan",
    "Shaanxi", "Gansu", "Qinghai", "Ningxia", "Xinjiang", "Inner Mongolia"
]

# Green Power Ratio (1 - alpha_coal)
alpha_coal = np.array([
    0.9593, 0.9797, 0.8645, 0.9049, 0.8670, 0.7740, 0.8545, 0.9769, 0.9512, 0.8967,
    0.9352, 0.6999, 0.8161, 0.9494, 0.9356, 0.4064, 0.5866, 0.8918, 0.4721, 0.8478,
    0.6422, 0.0992, 0.6014, 0.0811, 0.8902, 0.5268, 0.2484, 0.8242, 0.7752, 0.8445
])
green_ratio = 1 - alpha_coal

# Economic Multipliers
multipliers = np.array([
    5.0137, 4.5163, 2.9711, 3.2173, 2.6048, 3.2688,
    2.7142, 4.7486, 3.5741, 3.5371, 4.0347, 3.9770,
    3.9915, 4.2853, 4.3810, 3.5774, 2.9689, 4.0483,
    3.4172, 3.1172, 4.4020, 3.6096, 3.1799, 3.1641,
    2.9335, 3.1390, 3.4739, 2.0000, 3.5467, 3.1412
])
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
# Capacity Data
#capacity_built =[ 64306.,  25957.,  63118.,  30997.,  45667.,  21859.,  24954.,
#       69950., 181048., 112666.,  66063.,  75148.,  44125., 129460.,
#        96996.,  81625.,  70568., 194135.,  38125.,   9538.,  41934.,
#        83334.,  29823.,  40559.,  46505.,  15742.,   5337.,   6819.,
#        24881.,  31352.]
capacity_built = [
    0,        # 北京
    0,        # 天津
    0,        # 河北
    63000,    # 山西
    120000,   # 辽宁
    0,        # 吉林
    70000,    # 黑龙江
    0,        # 上海
    0,        # 江苏
    0,        # 浙江
    0,        # 安徽
    0,        # 福建
    0,        # 江西
    0,        # 山东
    0,        # 河南
    460000,   # 湖北
    0,        # 湖南
    0,        # 广东
    0,        # 广西
    0,        # 海南
    0,        # 重庆
    266000,   # 四川
    0,        # 贵州
    263000,   # 云南
    110000,   # 陕西
    36000,    # 甘肃
    20000,    # 青海
    46000,    # 宁夏
    23000,    # 新疆
    150000    # 内蒙古
]
df_het = pd.DataFrame({
    'Province': provinces,
    'Green_Ratio': green_ratio,
    'Multiplier': multipliers,
    'Capacity': capacity_built
})

# ==========================================
# 3. Plotting
# ==========================================
plt.figure(figsize=(14, 9))

# Adjust Bubble Size (Increased)
# Changed divisor from 80 to 40, minimum from 50 to 100
sizes = df_het['Capacity'] / 70
sizes = np.maximum(sizes, 100)

# Scatter Plot
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

# Labels (Translated + Larger Font)
for i, row in df_het.iterrows():
    offset = (0, 8)

    # Fine-tuning for specific English labels to avoid overlap
    if row['Province'] == 'Beijing':
        offset = (0, -18)
    elif row['Province'] == 'Shanghai':
        offset = (0, -18)
    elif row['Province'] == 'Tianjin':
        offset = (18, 0)
    elif row['Province'] == 'Hebei':
        offset = (-18, 0)
    elif row['Province'] == 'Ningxia':
        offset = (0, -22)
    elif row['Province'] == 'Shandong':
        offset = (-25, 0)
    elif row['Province'] == 'Jiangsu':
        offset = (25, 0)

    plt.annotate(
        row['Province'],
        (row['Green_Ratio'], row['Multiplier']),
        xytext=offset, textcoords='offset points',
        fontsize=11, ha='center', fontweight='normal'  # Font size 9 -> 11
    )

# Quadrant Lines
plt.axvline(x=0.4, color='gray', linestyle='--', alpha=0.6)
plt.axhline(y=3.5, color='gray', linestyle='--', alpha=0.6)

# Region Annotations (Translated + Larger Font)
# Font size 12 -> 14/15
plt.text(0.8, 4.5, 'Ideal Region (High Green, High Econ)\n(Hubei, Sichuan)',
         fontsize=15, color='green', ha='center',
         fontweight='bold', bbox=dict(facecolor='white', alpha=0.6))

plt.text(0.2, 4.5, 'Economic Engine (High Econ)\n(Beijing, Shanghai, Tianjin)',
         fontsize=15, color='#d62728', ha='center', fontweight='bold',
         bbox=dict(facecolor='white', alpha=0.6))

plt.text(0.8, 2.5, 'Resource Exporter (High Green)\n(Guizhou, Gansu, Yunnan)',
         fontsize=15, color='#1f77b4', ha='center', fontweight='bold',
         bbox=dict(facecolor='white', alpha=0.6))

plt.text(0.2, 2.2, 'Potential Region\n(Inner Mongolia, Shanxi, Liaoning)',
         fontsize=15, color='gray', ha='center', fontweight='bold',
         bbox=dict(facecolor='white', alpha=0.6))

# Axis Labels and Title (Translated + Larger Font)
# Font size 14 -> 17, 16 -> 20
plt.xlabel('Green Power Ratio (1-$\\alpha$)', fontsize=17, fontweight='bold')
plt.ylabel('Input-output multiplier', fontsize=17, fontweight='bold')
#plt.title('', fontsize=20, pad=20)

# Colorbar (Translated + Larger Font)
cbar = plt.colorbar(scatter)
cbar.set_label('Green Power Ratio', fontsize=15) # Font size 12 -> 15
cbar.ax.tick_params(labelsize=13)

plt.tick_params(axis='both', which='major', labelsize=13) # Axis ticks larger
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('Figure7_Heterogeneity_Scatter_English_Large.svg', dpi=300, format='svg')
plt.show()