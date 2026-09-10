# -*- coding: utf-8 -*-
"""
目的: 针对《全生命周期导向下智算中心的扩建与配置》的完整模型
功能: 1. 考虑 LCC 与 SCC (含资金时间价值与隐含碳)
      2. 宏观经济 epsilon-约束法
      3. 自动遍历 psi 参数，寻找最优决策区间并绘制 Pareto 前沿
"""
import math
import numpy as np
import os
from openpyxl import load_workbook
import matplotlib.pyplot as plt  # 导入matplotlib绘图库，用于绘制帕累托前沿图
try:
    from gurobipy import Model, GRB, quicksum
except Exception as e:
    raise ImportError("无法导入 gurobipy。请确认 gurobi 与 gurobipy 已安装并可用。原始错误: " + str(e))

def status_name(code: int) -> str:
    mapping = {
        GRB.OPTIMAL: "OPTIMAL",
        GRB.TIME_LIMIT: "TIME_LIMIT",
        GRB.SUBOPTIMAL: "SUBOPTIMAL",
        GRB.INFEASIBLE: "INFEASIBLE",
        GRB.INF_OR_UNBD: "INF_OR_UNBD",
        GRB.UNBOUNDED: "UNBOUNDED",
        GRB.INTERRUPTED: "INTERRUPTED",
    }
    return mapping.get(code, str(code))

# =========================== 1. 宏观政策与容差开关 ===========================
# 若为True，则要求每个省的入流算力严格等于需求；False则允许在区间内波动
DEMAND_EQUAL_PER_PROV = False
ETA_MIN = 0.95                  # 需求满足的下界比例 (95%)
ETA_MAX = 1.05                  # 需求满足的上界比例 (105%)

# 全国总算力约束模式："none"无约束|"equal"严格等于|"interval"区间波动
NATIONAL_TOTAL_MODE = "interval"  # "none"|"equal"|"interval"
GAMMA_MIN = 0.95                  # 全国总供给下界比例
GAMMA_MAX = 1.05                  # 全国总供给上界比例

USE_MINCOST_Q  = True             # 是否对距离施加传输成本，True表示计算距离费用
LOCAL_FIRST_COEF = 0.0            # 本地优先系数，如果不为0，会变相惩罚跨省传输（本模型设为0）


# =========================== 2. 碳排放与经济折现核心参数 ===========================
#动态的碳社会成本
USD_TO_RMB = 6.69166666667  #当前美元兑人民币
SCC_INC_1 = 1.3 * USD_TO_RMB  # 前10年年均增量（元）
SCC_INC_2 = 1.5 * USD_TO_RMB  # 后10年年均增量（元）

CARBON_PRICE_PER_TON = 240.9      # 碳社会成本价格 (SCC)，单位：元/吨 CO2
EMISSION_FACTOR_D = 1.9           # 发电的折算因子参数 (配合后面的煤耗计算)

# Gurobi 参数
TIME_LIMIT = 3600                 # 求解时间上限：3600秒 (1小时)，防止极其复杂的模型卡死
MIP_GAP = 1e-6                    # 混合整数规划的容差(Gap)，1e-6表示解已经非常精确，接近绝对最优
THREADS = 0                       # 使用所有可用的CPU线程进行并行计算
OUTPUT_FLAG = 1                   # 1表示在控制台打印Gurobi求解过程的日志，0表示静默求解

# =========================== 3. 物理与工程常量 ===========================
# 时延与距离限制
TAU_MS =5                  # 容忍的最大传输时延 (ms)
L_0_MICROSEC_PER_KM = 5.1     # 光纤传输单位距离时延 (微秒/千米)
# 最大服务半径(公里) = (最大时延毫秒 * 1000 微秒/毫秒) / 单位公里微秒数
H0_KM = (TAU_MS * 1000.0) / L_0_MICROSEC_PER_KM
#新增：GDP增长约束开关与阈值
ENABLE_GDP_CONSTRAINT = True  # 是否开启GDP硬约束
# 目标：全国总增幅值（%）。例如 0.35 表示要求增幅达到 0.35%
TARGET_GDP_GROWTH_PERCENT = 0.2806
# --- 耗电与年限参数 ---
E_RACK_MWH = 12                             # 单个机架/服务器的设计功率对应的兆瓦时基数 (配合后面的公式使用)
E_RACK_KWH = E_RACK_MWH * 24 * 365          # 转化为单台机器每年的耗电量 (千瓦时/度)
C_TRAN = 1000                               # 跨省传输专线的单位建设/租赁成本系数 (元/公里)
# --- 新增：全生命周期资金时间价值与隐含碳指标 ---
L_YEARS = 18                    # 智算中心全生命周期评估年限 (年)
DISCOUNT_RATE = 0.03              # 资金折现率3%，用于计算未来运营成本的净现值(NPV)
#这两个要确定好
# 隐含碳排放 (Embodied Carbon)：一次性产生，不随时间折现
#建筑碳排放190.642885kg/m^2*18 year
BUILDING_CARBON_PER_SITE = {"M": 2478.357505, "L": 5719.28655, "XL": 9532.14425} # 各规模数据中心建筑建设阶段产生的隐含碳排 (吨)
EQUIP_CARBON_PER_SERVER = 1.2     # 单台服务器制造、运输与最终报废阶段产生的隐含碳排 (吨)


# --- 数据中心规模定义 ---
SCALES = ["M", "L", "XL"]       # 决策变量可选规模：中、大、超大
# 不同规模对应可容纳的服务器/机架数量
CAPACITY_PER_SITE = {"M": 3000, "L": 10000, "XL": 20000}

# --- 新增：维保、人工与期末报废成本参数 ---
MAINT_RATE = 0.01                 # 每年设备维保费占初始设备投资的比例 (3%)
LABOR_PER_SERVER = 150           # 单台服务器/机架每年的运维人工及管理费 (元/年)
DISPOSAL_PER_SERVER = 2000        # 单台服务器期末报废与环保处理净成本 (元)

# ===== IO 相关（L_inverse 乘数与三部门映射）=====
BASE_DIR = r"D:\BaiduNetdiskDownload\投入产出表\31省市区42部门投入产出表1997-2017年\2017年各省份投入产出表"
TARGET_SHEET = "L_inverse"# Excel中包含列昂惕夫逆矩阵的Sheet名


# 定义模型中需要重点考察拉动效应的三个国民经济部门
SECTOR_BUILD = "建筑"                          # 对应基础设施建设投资
SECTOR_ELEC  = "电力、热力的生产和供应"           # 对应运营期的电费支出
SECTOR_EQUIP = "通信设备、计算机和其他电子设备"    # 对应购买服务器设备的支出
# --- 新增的三个部门映射 ---
SECTOR_SERVICE = "金属制品、机械和设备修理服务"   # 对应维保费：IT服务与软件修理
SECTOR_LABOR   = "信息传输、软件和信息技术服务"    # 对应人工费：商务运维服务与人力派遣
SECTOR_ENV     = "水利、环境和公共设施管理"       # 对应报废处理：固废与危废环保处理

# 弃用的惩罚项系数。因为采用了epsilon约束法，目标函数里不再需要相减
BENEFIT_WEIGHT = 0.0000

# 最低利用率（存量+新增）
UTIL_MIN = 0.95# 投资效率约束：为了避免盲目建站，要求各地的总利用率不能低于 95%


# =========================== 4. 各省基础数据库 (30个节点) ===========================
provinces_seed = [
    ("北京", 39.9042, 116.4074), ("天津", 39.1209, 117.2051), ("河北", 38.7079, 114.5144),
    ("山西", 37.8707, 112.5489), ("辽宁", 41.8057, 123.4325), ("吉林", 43.8965, 125.3257),
    ("黑龙江", 45.8038, 126.5349), ("上海", 31.2304, 121.4737), ("江苏", 32.0603, 118.7969),
    ("浙江", 30.2741, 120.1551), ("安徽", 31.8612, 117.2826), ("福建", 26.0745, 119.2965),
    ("江西", 28.6896, 115.8936), ("山东", 36.6683, 117.0204), ("河南", 34.7466, 113.6254),
    ("湖北", 30.5844, 114.2986), ("湖南", 28.2282, 112.9823), ("广东", 23.1291, 113.2644),
    ("广西", 22.8152, 108.3277), ("海南", 20.0444, 110.1991), ("重庆", 29.5630, 106.5516),
    ("四川", 30.6519, 104.0665), ("贵州", 26.5978, 106.7074), ("云南", 25.0430, 102.7065),
    ("陕西", 34.2658, 108.9541), ("甘肃", 36.0671, 103.8096), ("青海", 36.5986, 101.7801),
    ("宁夏", 38.4875, 106.2069), ("新疆", 43.7930, 87.6277), ("内蒙古", 40.8175, 111.6708)
]
N = len(provinces_seed)#节点数量：30
PROVINCE_NAMES = [nm for (nm, _, _) in provinces_seed]# 提取省份名称列表
COORDS = [(lat, lon) for (_, lat, lon) in provinces_seed]# 提取经纬度列表

# =========================== 各个省份GDP ===========================
# 输入的各省 GDP (单位原本为亿元，乘 10000 转换为万元，方便与后面的成本单位对齐)
province_GDP = np.array( [
    # 北京, 天津, 河北, 山西, 辽宁, 吉林, 黑龙江, 上海, 江苏, 浙江,
    # 安徽, 福建, 江西, 山东, 河南, 湖北, 湖南, 广东, 广西, 海南,
    # 重庆, 四川, 贵州, 云南, 陕西, 甘肃, 青海, 宁夏, 新疆, 内蒙古
    # ↓↓↓ 用你的真实数值替换 ↓↓↓
        842402410.6,
        588870290.2,
        990754900,
        377005901,
        610828700,
        457917300,
        357243274,
        940532900,
        2592052600,
        1524285939,
        983066802.2,
        943898885,
        596240624.2,
        2618639939,
        1499327800,
        944580212.5,
        820976500,
        2561850630,
        479710534.3,
        109206702.3,
        559146100,
        989954541.2,
        325918879,
        387712400,
        541447169.5,
        178770747.2,
        64931700.81,
        88629532,
        268226850.6,
        356686220.2
    ], dtype=float)* 10000
province_GDP.sum()
# =========================== 需求/存量 ===========================
# 目标年的算力需求量 (单位：台/机架)
D = np.array([
    238305, 56631, 155808, 65867, 123834, 49124, 75841, 288807, 412045, 296792,
    130116, 146761, 89920, 246274, 186793, 158628, 138369, 616746, 78927, 26549,
    85906, 192848, 114883, 83386, 115329, 37915, 18852, 49993, 54661, 157846
], dtype=float)
# 现存(已建好)的算力容量 (单位：台/机架)
S_exist = np.array([
    173999, 30674, 92690, 34870, 78167, 27265, 50887, 218857, 230997, 184126,
    64053, 71613, 45795, 116814, 89797, 77003, 67801, 422611, 40802, 17011,
    43972, 109514, 85060, 42827, 68824, 22173, 13515, 43174, 29780, 126494
], dtype=float)
(D-S_exist).sum()
# =========================== 电价/结构/煤耗 ===========================
# 各省火电(煤电)价格
p_coal = np.array([
    0.6258, 0.6542, 0.5986, 0.4514, 0.5589, 0.6549, 0.5656, 0.6145, 0.5824, 0.6534,
    0.5958, 0.6083, 0.6249, 0.6483, 0.6192, 0.6384, 0.6806, 0.6354, 0.6993, 0.6920,
    0.6054, 0.5110, 0.5166, 0.3519, 0.4527, 0.4584, 0.3811, 0.40, 0.3200, 0.4298
], dtype=float)
#p_coal = np.array([
#    0.4885, 0.3519, 0.3209, 0.3216, 0.3706, 0.3654, 0.3735, 0.4102, 0.3919, 0.4163,
#    0.3828, 0.3893, 0.4182, 0.4110, 0.3562, 0.4365, 0.4590, 0.4411, 0.3994, 0.4385,
#    0.4126, 0.4403, 0.3324, 0.4125, 0.3268, 0.2953, 0.24867, 0.2802, 0.2151, 0.2525
#], dtype=float)
# 各省绿电(可再生能源)价格
p_ren = np.array([
    0.8000, 0.8000, 0.5541, 0.6348, 0.5140, 0.5079, 0.4991, 0.8142, 0.7524, 0.6898,
    0.6606, 0.4084, 0.4910, 0.6529, 0.5032, 0.2999, 0.3777, 0.3686, 0.2698, 0.4451,
    0.3230, 0.2853, 0.3154, 0.2220, 0.4626, 0.3650, 0.3914, 0.5902, 0.4434, 0.5424
], dtype=float)

# 各省电网中煤电所占的比例 (用来计算综合电价和碳排放因子)
alpha_coal = np.array([
    0.9593, 0.9797, 0.8645, 0.9049, 0.8670, 0.7740, 0.8545, 0.9769, 0.9512, 0.8967,
    0.9352, 0.6999, 0.8161, 0.9494, 0.9356, 0.4064, 0.5866, 0.8918, 0.4721, 0.8478,
    0.6422, 0.0992, 0.6014, 0.0811, 0.8902, 0.5268, 0.2484, 0.8242, 0.7752, 0.8445
], dtype=float)
#alpha_coal = np.full_like(alpha_coal, 0)
# 中部地区省份列表
central_provinces = ["吉林", "黑龙江",
                     "山西", "安徽", "江西", "河南", "湖北", "湖南"]
# 东部地区 (11省市)
eastern_provinces = [
    "北京", "辽宁", "天津", "河北", "上海", "江苏",
    "浙江", "福建", "山东", "广东", "海南"]
# 西部地区 (11省区)
western_provinces = [
    "内蒙古", "广西", "重庆", "四川", "贵州", "云南",
    "陕西", "甘肃", "青海", "宁夏", "新疆"]

print("\n>>> 正在调整供电结构 (+0.2)...")
for nm in western_provinces:
    if nm in PROVINCE_NAMES:
        idx = PROVINCE_NAMES.index(nm) # 找到该省份对应的索引
        old_val = p_ren[idx]
        p_ren[idx] *= 0.9          # 核心修改：火电价格 + 0.2
        print(f"  {nm}: 原价 {old_val:.4f} -> 现价 {p_ren[idx]:.4f}")

#各个省份发每度电对应的标准煤耗量 (克/千瓦时)
r_g_per_kwh = np.array([
    241, 316, 325, 330, 315, 308, 330, 302, 308, 299, 309, 310, 313, 323, 317, 309, 314, 315,
    318, 310, 332, 322, 331, 335, 329, 329, 361, 347, 336, 337
], dtype=float)

# =========================== PUE ===========================
# 各省份气候不同，导致数据中心制冷所需的能源不同，体现为PUE值的差异
PUE_table = {
    "北京": {"M": 1.57, "L": 1.36, "XL": 1.30}, "天津": {"M": 1.57, "L": 1.36, "XL": 1.30},
    "河北": {"M": 1.57, "L": 1.36, "XL": 1.30}, "山西": {"M": 1.57, "L": 1.36, "XL": 1.30},
    "辽宁": {"M": 1.42, "L": 1.30, "XL": 1.21}, "吉林": {"M": 1.42, "L": 1.30, "XL": 1.21},
    "黑龙江": {"M": 1.42, "L": 1.30, "XL": 1.21}, "上海": {"M": 1.62, "L": 1.41, "XL": 1.35},
    "江苏": {"M": 1.62, "L": 1.41, "XL": 1.35}, "浙江": {"M": 1.62, "L": 1.41, "XL": 1.35},
    "安徽": {"M": 1.62, "L": 1.41, "XL": 1.35}, "福建": {"M": 1.62, "L": 1.41, "XL": 1.35},
    "江西": {"M": 1.62, "L": 1.41, "XL": 1.35}, "山东": {"M": 1.57, "L": 1.36, "XL": 1.30},
    "河南": {"M": 1.57, "L": 1.36, "XL": 1.30}, "湖北": {"M": 1.62, "L": 1.41, "XL": 1.35},
    "湖南": {"M": 1.62, "L": 1.41, "XL": 1.35}, "广东": {"M": 1.67, "L": 1.46, "XL": 1.40},
    "广西": {"M": 1.67, "L": 1.46, "XL": 1.40}, "海南": {"M": 1.62, "L": 1.41, "XL": 1.35},
    "重庆": {"M": 1.62, "L": 1.41, "XL": 1.35}, "四川": {"M": 1.62, "L": 1.41, "XL": 1.35},
    "贵州": {"M": 1.62, "L": 1.41, "XL": 1.35}, "云南": {"M": 1.67, "L": 1.46, "XL": 1.40},
    "陕西": {"M": 1.57, "L": 1.36, "XL": 1.30}, "甘肃": {"M": 1.42, "L": 1.30, "XL": 1.21},
    "青海": {"M": 1.42, "L": 1.30, "XL": 1.21}, "宁夏": {"M": 1.42, "L": 1.30, "XL": 1.21},
    "新疆": {"M": 1.42, "L": 1.30, "XL": 1.21}, "内蒙古": {"M": 1.42, "L": 1.30, "XL": 1.21},
}
PUE_max = {i: {m: PUE_table[PROVINCE_NAMES[i]][m] for m in SCALES} for i in range(N)}

# =========================== CAPEX（示例分项口径） ===========================
# 建设成本(CAPEX)的省际差异数据字典（人工、材料、土地单价）
c_lab = {
    "北京": 114631, "天津": 75579, "河北": 55152, "山西": 54673, "辽宁": 55093, "吉林": 48961, "黑龙江": 48414,
    "上海": 110117, "江苏": 64663, "浙江": 56265, "安徽": 60785, "福建": 61394, "江西": 57340, "山东": 59229,
    "河南": 53163, "湖北": 61658, "湖南": 52645, "广东": 64747, "广西": 55047, "海南": 46019, "重庆": 59605,
    "四川": 55134, "贵州": 62684, "云南": 49128, "陕西": 58710, "甘肃": 51863, "青海": 69611, "宁夏": 52886,
    "新疆": 62485, "内蒙古": 51833,
}
c_mat = {
    "北京": 3780, "天津": 3847, "河北": 3915, "山西": 3888, "辽宁": 3694, "吉林": 3785, "黑龙江": 3929,
    "上海": 3735, "江苏": 4187, "浙江": 3779, "安徽": 3984, "福建": 3903, "江西": 3906, "山东": 3906,
    "河南": 4111, "湖北": 3839, "湖南": 4018, "广东": 3955, "广西": 4084, "海南": 4200, "重庆": 3970,
    "四川": 4410, "贵州": 3980, "云南": 4545, "陕西": 3938, "甘肃": 4015, "青海": 3388, "宁夏": 3974,
    "新疆": 4566, "内蒙古": 3796,
}
c_land = {
    "北京": 2692, "天津": 940, "河北": 706, "山西": 700, "辽宁": 500, "吉林": 392, "黑龙江": 300,
    "上海": 2506, "江苏": 600, "浙江": 1100, "安徽": 300, "福建": 600, "江西": 492, "山东": 400,
    "河南": 500, "湖北": 500, "湖南": 600, "广东": 2500, "广西": 400, "海南": 694, "重庆": 588,
    "四川": 500, "贵州": 475, "云南": 697, "陕西": 761, "甘肃": 1008, "青海": 499, "宁夏": 255,
    "新疆": 706, "内蒙古": 500,
}
c_srv = {nm: 35000.0 for nm in PROVINCE_NAMES}

# 不同规模 M, L, XL 对应的工程物量系数 (用于换算建设总量)
P_LAB  = {"M": 0.13 * 1e4 * 1.5, "L": 0.30 * 1e4 * 1.5, "XL": 0.40 * 1e4 * 1.5}
P_MAT  = {"M": 0.01 * 1e4 * 1.5, "L": 0.03 * 1e4 * 1.5, "XL": 0.05 * 1e4 * 1.5}
P_LAND = {"M": 1.30 * 1e4 * 1.5, "L": 3.00 * 1e4 * 1.5, "XL": 5.00 * 1e4 * 1.5}

# 预先计算出在每一个省份 i 建设规模为 m 的数据中心的 总初始固定投资额 (SITE_CAPEX)
#缺少运营期的考量，以及折现率
SITE_CAPEX = {}
for i, nm in enumerate(PROVINCE_NAMES):
    SITE_CAPEX[i] = {}
    for m in SCALES:
        # 总建设投资 = 人工费 + 材料费 + 土地费 + (设备单价 * 机柜数量)
        SITE_CAPEX[i][m] = float(
            c_lab[nm]  * P_LAB[m]  +
            c_mat[nm]  * P_MAT[m]   +
            c_land[nm] * P_LAND[m] +
            c_srv[nm]  * CAPACITY_PER_SITE[m]*3
        )


# =========================== 5. 网络物理距离与候选拓扑边构建 ===========================
# 定义一个依据球面经纬度计算两点间直线距离的函数 (Haversine公式)
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

# 生成 30x30 的距离矩阵
dist = np.zeros((N, N))
for i in range(N):
    for j in range(N):
        (lat1, lon1) = COORDS[i]
        (lat2, lon2) = COORDS[j]
        dist[i, j] = haversine_km(lat1, lon1, lat2, lon2)

# 核心降维逻辑：只保留距离小于等于允许最大服务半径(H0_KM)的节点对作为“可行边”。
# 如果两个省离得太远，光纤延迟必然超时，直接在数学模型中排除这条边，极大加快求解速度。
EDGE_LIST = [(i, j) for i in range(N) for j in range(N) if dist[i, j] <= H0_KM]


# 定义计算两点传输单位成本的函数
def transmission_unit_cost(i, j):
    if i == j:
        return 0.0
    base = (C_TRAN * dist[i, j]) if USE_MINCOST_Q else 0.0
    bias = (LOCAL_FIRST_COEF if i != j else 0.0)
    return base + bias

# =========================== 6. 提取 IO 乘数 (带容错兜底) ===========================
def locate_province_file(base_dir: str, prov: str):
    p1 = os.path.join(base_dir, f"{prov}.xlsx")
    if os.path.exists(p1):
        return p1
    for i in range(1, 40):
        p2 = os.path.join(base_dir, f"{i:02d}-{prov}.xlsx")
        if os.path.exists(p2):
            return p2
    return None

def read_multipliers_for_province(xlsx_path: str):
    wb = load_workbook(xlsx_path, data_only=True)
    if TARGET_SHEET not in wb.sheetnames:
        wb.close()
        raise ValueError(f"{os.path.basename(xlsx_path)}: 找不到工作表 {TARGET_SHEET}")
    ws = wb[TARGET_SHEET]

    header_cells = []
    for c in range(1, 201):
        v = ws.cell(row=1, column=c).value
        if v is None:
            continue
        header_cells.append((c, str(v).strip()))
    # 修改 1：扩充我们要找的列名
    want_names = {
        SECTOR_BUILD: None, SECTOR_ELEC: None, SECTOR_EQUIP: None,
        SECTOR_SERVICE: None, SECTOR_LABOR: None, SECTOR_ENV: None
    }
    for c, name in header_cells:
        if name in want_names and want_names[name] is None:
            want_names[name] = c

    missing = [nm for nm, col in want_names.items() if col is None]
    if missing:
        wb.close()
        raise KeyError(f"{os.path.basename(xlsx_path)}: 第1行未找到这些列头：{missing}。")

    def colsum_excel(excel_col: int) -> float:
        s = 0.0
        for r in range(2, 44):
            v = ws.cell(row=r, column=excel_col).value
            s += float(v if v is not None else 0.0)
        return float(s)


    m_build = colsum_excel(want_names[SECTOR_BUILD])
    m_elec = colsum_excel(want_names[SECTOR_ELEC])
    m_equip = colsum_excel(want_names[SECTOR_EQUIP])
    m_service = colsum_excel(want_names[SECTOR_SERVICE])
    m_labor = colsum_excel(want_names[SECTOR_LABOR])
    m_env = colsum_excel(want_names[SECTOR_ENV])
    wb.close()
    return m_build, m_elec, m_equip, m_service, m_labor, m_env

# 读取全省乘数
m_build = np.zeros(N, dtype=float)
m_elec  = np.zeros(N, dtype=float)
m_equip = np.zeros(N, dtype=float)
# 新增的三个全局数组
m_service = np.zeros(N, dtype=float)
m_labor   = np.zeros(N, dtype=float)
m_env     = np.zeros(N, dtype=float)
for i, prov in enumerate(PROVINCE_NAMES):
    fp = locate_province_file(BASE_DIR, prov)
    if not fp:
        raise FileNotFoundError(f"未找到 {prov} 的 IO 表文件（{prov}.xlsx 或 01-{prov}.xlsx 等）")
    mb, me, mq, ms, ml, menv = read_multipliers_for_province(fp)
    m_build[i], m_elec[i], m_equip[i] = mb, me, mq
    m_service[i], m_labor[i], m_env[i] = ms, ml, menv

# =========================== 7. 宏观经济效益事后核算模块 ===========================
def compute_economic_benefits(
        x_sol: np.ndarray,
        q_sol: np.ndarray,
        PROVINCE_NAMES: list,
        SCALES: list,
        CAPACITY_PER_SITE: dict,
        c_lab: dict, c_mat: dict, c_land: dict, c_srv: dict,
        P_LAB: dict, P_MAT: dict, P_LAND: dict,
        elec_per_server: np.ndarray,
        m_build: np.ndarray, m_equip: np.ndarray, m_elec: np.ndarray,
        m_service: np.ndarray, m_labor: np.ndarray, m_env: np.ndarray,  # <== 新增这里
        BENEFIT_WEIGHT: float = 0.0
):
    N = len(PROVINCE_NAMES)
    # 计算每个省实际往外输送(或者内部消耗)了多少流量
    outflow = q_sol.sum(axis=1)

    build_spend = np.zeros(N, dtype=float)
    equip_spend = np.zeros(N, dtype=float)
    elec_spend  = np.zeros(N, dtype=float)

    maint_spend = np.zeros(N, dtype=float)
    labor_spend = np.zeros(N, dtype=float)
    disposal_spend = np.zeros(N, dtype=float)
    # 重新计算经济折现系数 (因为维保、人工发生在此后18年，报废发生在第18年末)
    npv_multiplier = (1 - (1 + DISCOUNT_RATE) ** (-L_YEARS)) / DISCOUNT_RATE  # 等额年金现值系数 P/A
    terminal_discount = 1 / ((1 + DISCOUNT_RATE) ** L_YEARS)  # 终值现值系数 P/F
    for i, nm in enumerate(PROVINCE_NAMES):
        bsum = 0.0
        esum = 0.0
        #还有那些投入，应该计算投入产出
        for mi, m in enumerate(SCALES):
            # cnt 是该省建设了几个这种规模的智算中心
            cnt = float(x_sol[i, mi])
            # 建筑基建投入 = (人工+材料+土地) * 建设数量
            bsum += (c_lab[nm]*P_LAB[m] + c_mat[nm]*P_MAT[m] + c_land[nm]*P_LAND[m]) * cnt
            # 设备投入 = 单台售价 * 机柜容量 * 建设数量
            esum += (c_srv[nm] *3* CAPACITY_PER_SITE[m]) * cnt

        build_spend[i] = bsum
        equip_spend[i] = esum
        # 运营期电费支出总额(已折现)
        elec_spend[i]  = elec_per_server[i] * outflow[i]

        # --- 核心修正：加入全生命周期的运营及末端费用 (折现到现值) ---
        maint_spend[i] = esum * MAINT_RATE * npv_multiplier  # 总维保费现值

        labor_spend[i] = outflow[i] * LABOR_PER_SERVER * npv_multiplier  # 总人工费现值

        disposal_spend[i] = outflow[i] * DISPOSAL_PER_SERVER * terminal_discount  # 报废处理费现值
    #没有乘权重的总产出
    induced_raw = (m_build * build_spend +
                   m_equip * equip_spend +
                   m_elec * elec_spend   +
                   m_service * maint_spend +
                   m_labor * labor_spend +
                   m_env * disposal_spend)

    # 使用 province_GDP 替代原来的 total_province_output
    total_province_output = province_GDP  # 直接使用传入的省份GDP数据
    #induced_raw_m = m_build * build_spend + m_equip * equip_spend + m_elec * elec_spend/18
    relative_output =  induced_raw/18/(total_province_output+1e-6) #BENEFIT_WEIGHT *

    # -------------------------- 新增：全国层面总增幅值计算 --------------------------
    # 全国总带动产出 = 各省induced_raw之和
    national_total_induced = np.sum(induced_raw)
    # 全国总GDP = 各省total_province_output之和
    national_total_gdp = np.sum(total_province_output)
    # 全国总增幅值（%）=（全国总带动产出 ÷ 全国总GDP）× 100%
    national_gdp_growth_rate = (national_total_induced / (18*national_total_gdp + 1e-6)) * 100
    # -----------------------------------------------------------------------------------

    return {
        "build_spend": build_spend,
        "equip_spend": equip_spend,
        "elec_spend":  elec_spend,
        "induced_raw": induced_raw,# 各省带动总产出（元）
        "relative_output": relative_output,# 省域相对产值（无单位）
        "total_province_output": total_province_output,# 省域GDP增幅值（%）
        "outflow": outflow,
        "total_raw": float(induced_raw.sum()),
        # 全国总增幅值（%）=（全国总带动产出 ÷ 全国总GDP）× 100%
        "national_gdp_growth_rate":national_gdp_growth_rate,
    }



# =========================== 8. 核心：Gurobi 求解器 (包含全生命周期与 Epsilon 约束) ===========================
# current_psi 就是论文里的态度参数，用来动态控制宏观经济拉动强度的底线
def solve_milp_gurobi(current_psi=1.0, verbose=True):
    # 初始化 Gurobi 线性规划模型对象
    model = Model("DC_Siting_Flow_30Prov_Gurobi")
    # 根据 verbose 决定是否在控制台打印矩阵求解过程
    model.setParam("OutputFlag", 1 if verbose else 0)#OUTPUT_FLAG
    if TIME_LIMIT and TIME_LIMIT > 0:
        model.setParam("TimeLimit", TIME_LIMIT)
    if MIP_GAP is not None:
        model.setParam("MIPGap", MIP_GAP)
    if THREADS and THREADS > 0:
        model.setParam("Threads", THREADS)

    # ---------------- [变量声明] ----------------
    # 变量：x_{i,m}、q0_{i,j}、q1_{i,j}
    x = {} # x[i, m]: 在第 i 个省份，规模为 m 的智算中心新建数量
    for i in range(N):
        for m in SCALES:
            x[i, m] = model.addVar(vtype=GRB.INTEGER, name=f"x_{i}_{m}", lb=0)

    # q0: 存量算力调度流向; q1: 新增算力调度流向 (连续型变量)
    q0, q1 = {}, {}
    # 仅对满足延迟限制(距离短)的路线生成变量，大幅减少变量个数
    for (i, j) in EDGE_LIST:
        q0[i, j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"q0_{i}_{j}", lb=0.0)
        q1[i, j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"q1_{i}_{j}", lb=0.0)
    # 将变量更新到模型内部
    model.update()

    # ---------------- [经济学修正区：资金时间价值与动态碳价] ----------------
    # 1. 运营期电费的净现值(NPV)折现系数 (等额支付现值系数)
    # 运用等额支付现值系数公式：P/A = [1 - (1+r)^(-n)] / r
    # 作用：未来的电费和碳费因为通货膨胀/资金利息，今天的1块钱和明年的1块钱不一样，必须折现！
    npv_multiplier = (1 - (1 + DISCOUNT_RATE) ** (-L_YEARS)) / DISCOUNT_RATE
    terminal_discount = 1 / ((1 + DISCOUNT_RATE) ** L_YEARS)  # P/F

    # 计算各地综合电价 = 煤电比例*煤电价 + 绿电比例*绿电价
    unit_price = alpha_coal * p_coal + (1 - alpha_coal) * p_ren

    u = 1.0 # 假设负载率为100%时的理想模型，此处可作为缩放系数
    # 代表性 PUE 使用最大规模作为参考
    PUE_rep = np.array([PUE_max[i]["XL"] for i in range(N)])

    # 单台服务器全生命周期(18年)总电费现值
    #计算的时候应该是18年的求和，并除以（1+折现率）**年份
    elec_per_server = npv_multiplier * (unit_price * PUE_rep * u * E_RACK_KWH)

    # 2. 动态碳社会成本(SCC)折现系数
    # 因为碳价每年按 g(2%) 增长，同时资金按 r(3%) 折现，所以必须逐年进行“几何梯度序列”的折现求和
    # 公式: Sum( (1+g)^(t-1) / (1+r)^t )

    # 动态碳社会成本(SCC)的分段线性累加及折现
    total_scc_npv_per_ton = 0.0
    current_price = CARBON_PRICE_PER_TON  # 初始价格 (t=1)

    for t in range(1, L_YEARS + 1):
        # 计算当前年份的价格 (假设价格在年初确定或年度平均)
        # 第一年不增，从第二年开始累加
        if t > 1:
            if t <= 10:
                current_price += SCC_INC_1
            else:
                current_price += SCC_INC_2

        # 按照 DISCOUNT_RATE 折现到 t=0
        total_scc_npv_per_ton += current_price / ((1 + DISCOUNT_RATE) ** t)

    # 此时 total_scc_npv_per_ton 代表 18 年内每吨碳排放对应的总社会成本现值




    # # g/kWh → kg/kWh 每发 1 kWh 需要的煤耗（g/kWh）
    kg_coal_per_kwh = r_g_per_kwh / 1000.0

    #EMISSION_FACTOR_D：每吨煤产生的 CO₂（tCO₂/吨煤）


    # 一台服务器运转一年的物理碳排放量(吨)
    annual_carbon_emission = (PUE_rep * u * E_RACK_KWH
                              * kg_coal_per_kwh * EMISSION_FACTOR_D) / 1000.0

    # 单台服务器 18 年运营期间，随时间增长且被折现的 总碳社会成本(元)
    op_carb_per_server = (annual_carbon_emission * total_scc_npv_per_ton)

    #carb_per_server = (
    #    L_YEARS * (PUE_rep * u * E_RACK_KWH * kg_coal_per_kwh * EMISSION_FACTOR_D) / 1000.0 * CARBON_PRICE_PER_TON
    #)

    # 利用 Gurobi 语法汇总各省的 出流总量 (供电/算力负担)
    outflow0_expr = {i: quicksum(q0[i, j] for j in range(N) if (i, j) in q0) for i in range(N)}
    outflow1_expr = {i: quicksum(q1[i, j] for j in range(N) if (i, j) in q1) for i in range(N)}
    outflow_total_expr = {i: outflow0_expr[i] + outflow1_expr[i] for i in range(N)}

    # ---------------- [构建目标函数] MIN(LCC + SCC) ----------------
    # 三类投入金额（对接乘数）
    #底下这些是不是没用啊？
    build_spend = {}
    equip_spend = {}
    elec_spend = {}
    for i, nm in enumerate(PROVINCE_NAMES):
        build_spend[i] = quicksum(
            (c_lab[nm]*P_LAB[m] + c_mat[nm]*P_MAT[m] + c_land[nm]*P_LAND[m]) * x[i, m] for m in SCALES
        )
        equip_spend[i] = quicksum((c_srv[nm] * CAPACITY_PER_SITE[m]) *3* x[i, m] for m in SCALES)
        elec_spend[i]  = elec_per_server[i] * outflow_total_expr[i]

    # 目标：CAPEX + 电费 + 碳费 + 传输费(仅新增、跨省) - λ*产业带动
    # 3.1 基础设施建设成本项
    build_cost_terms = [SITE_CAPEX[i][m] * x[i, m] for i in range(N) for m in SCALES]
    # 3.2 运营期电费成本项
    elec_cost_terms  = [elec_per_server[i]  * outflow_total_expr[i] for i in range(N)]
    # 3.3 新增补充：全生命周期的人工、维保、回收费用 (已映射折现，保持求解器与核算公式的物理同构)
    maint_cost_terms = []
    labor_cost_terms = [LABOR_PER_SERVER * npv_multiplier * outflow_total_expr[i] for i in range(N)]
    disposal_cost_terms = [DISPOSAL_PER_SERVER * terminal_discount * outflow_total_expr[i] for i in range(N)]

    # 3.4 全生命周期碳社会成本 (SCC)
    carbon_cost_terms = []
    for i in range(N):
        # 运营期产生的碳费 (耗电造成的间接排放)
        # 仅针对电网中采用火电的比例 (alpha_coal) 扣取碳费
        #op_carb_per_server[i]计算的时候没有乘alpha_coal[i]
        carbon_cost_terms.append(alpha_coal[i] * op_carb_per_server[i] * outflow_total_expr[i])
        for m in SCALES:
            # 引入 LCA 生命周期评价：追加建筑物和硬件设备的初期隐含碳排放 (因发生在当期，无需折现)
            # 建筑隐含碳 (一次性，无需折现)
            b_carbon = BUILDING_CARBON_PER_SITE[m] * CARBON_PRICE_PER_TON * x[i, m]
            # 服务器设备隐含碳 (芯片制造/报废等，一次性，无需折现)
            e_carbon = (EQUIP_CARBON_PER_SERVER * CAPACITY_PER_SITE[m]) *3* CARBON_PRICE_PER_TON * x[i, m]
            carbon_cost_terms.append(b_carbon + e_carbon)

            # 维保费的提成依赖于当期投资的设备总价
            equip_inv = c_srv[PROVINCE_NAMES[i]] * CAPACITY_PER_SITE[m] * x[i, m]
            maint_cost_terms.append(equip_inv * MAINT_RATE * npv_multiplier)
    # 3.4 传输网络建设成本项
    #trans_cost_terms = [transmission_unit_cost(i, j) * q1[i, j] for (i, j) in EDGE_LIST if i != j]

    # 定义一个极小的惩罚系数 epsilon，或者直接使用正常的传输成本系数
    # 如果您认为存量传输确实不该花大钱，就乘一个 0.01 或 0.001
    epsilon = 0.01# 引入极小惩罚项，目的是防止模型出现 A省传B省，B省又原封不动传回A省这种零成本的逻辑死循环
    trans_cost_terms = []
    for (i, j) in EDGE_LIST:
        if i != j:
            cost_unit = transmission_unit_cost(i, j)
            # q1 正常计费
            # 跨省新增流正常收取光纤铺设/租赁费
            term_q1 = cost_unit * q1[i, j]
            # q0 象征性计费（消除双向流的关键！）
            # 存量流象征性收取微小费用，消除同距双向流
            term_q0 = (cost_unit * epsilon) * q0[i, j]
            trans_cost_terms.append(term_q1 + term_q0)


    # ---------------- 多目标优化转单目标 (Epsilon 约束法) ----------------
    induced_terms = []
    for i in range(N):
        nm = PROVINCE_NAMES[i]
        # 1. 建筑业投入 (Build Spend)
        # 逻辑：(人工+材料+土地) * 新增数量
        # 注意：这里必须拆开写，不能直接用 SITE_CAPEX，因为 SITE_CAPEX 包含了设备费
        build_invest_expr = quicksum(
            (c_lab[nm] * P_LAB[m] + c_mat[nm] * P_MAT[m] + c_land[nm] * P_LAND[m]) * x[i, m]
            for m in SCALES
        )
        # 2. 设备制造业投入 (Equip Spend)
        # 逻辑：服务器单价 * 新增数量
        equip_invest_expr = quicksum(
            (c_srv[nm] *3* CAPACITY_PER_SITE[m]) * x[i, m]
            for m in SCALES
        )

        # 3. 电力业投入 (Elec Spend)
        # 逻辑：全生命周期电价 * 总流出量
        elec_invest_expr = elec_per_server[i] * outflow_total_expr[i]

        # 4. 该省的总带动产出 = 建筑乘数*建筑投入 + 设备乘数*设备投入 + 电力乘数*电力投入
        #还有哪些投入要算进来呢
        prov_induced = (
                m_build[i] * build_invest_expr +
                m_equip[i] * equip_invest_expr +
                m_elec[i] * elec_invest_expr+

                m_service[i] * (equip_invest_expr * MAINT_RATE * npv_multiplier) +
                m_labor[i]* (LABOR_PER_SERVER * npv_multiplier * outflow_total_expr[i]) +
                m_env[i] * (DISPOSAL_PER_SERVER * terminal_discount * outflow_total_expr[i])
        )
        induced_terms.append(prov_induced)

    # 全国总带动产出（Gurobi 表达式对象）
    induced_total_expr = quicksum(induced_terms)

    # Epsilon 核心逻辑：我们不把 GDP 放进目标函数里相减，而是把它作为一条硬杠杠约束起来。
    # "你想让我多拉动经济可以，你告诉我最低线（psi），我保证达到这个线，同时保证在达标的情况下总成本最低。"
    # --- 添加 Epsilon  硬约束 ---
    if ENABLE_GDP_CONSTRAINT:
        # 计算约束右边的阈值
        # 逻辑：目标值 = (目标百分比/100) * 全国年GDP总和 * 18年
        # $\psi$ 参数的核心作用区：调整国家对GDP拉动的底线期望
        dynamic_target = TARGET_GDP_GROWTH_PERCENT * current_psi
        total_national_gdp_val = float(province_GDP.sum())
        min_induced_val = (dynamic_target / 100.0) * total_national_gdp_val * L_YEARS

        # 向模型添加约束
        model.addConstr(induced_total_expr >= min_induced_val, name="Constraint_Min_GDP_Growth")

        print(f"\n>>> [约束已启用] 要求全生命周期总产出拉动年均GDP增幅 >= {dynamic_target}%")
        print(f"    即总产出需达到: {min_induced_val:,.0f} 元")


    # ---------------- 5. 物理供需约束 ----------------
    # 省级平衡：A_i + 新增 - 出 + 入 ∈ [η_min D_i, η_max D_i]
    # 用的约束
    for i in range(N):
        out_i = outflow_total_expr[i]# 流出量
        ## 计算流入量，考虑 q0 和 q1
        in_i  = quicksum((q0[j, i] + q1[j, i]) for j in range(N) if (j, i) in q0 or (j, i) in q1)
        # 新增产能
        addcap = quicksum(CAPACITY_PER_SITE[m] * x[i, m] for m in SCALES)
        lhs = S_exist[i] + addcap - out_i + in_i
        model.addConstr(lhs >= float(ETA_MIN * D[i]), name=f"prov_bal_lb_{i}")
        model.addConstr(lhs <= float(ETA_MAX * D[i]), name=f"prov_bal_ub_{i}")

    # 全国总供给（存量+新增）区间
    X_total = float(np.sum(D))
    total_supply = quicksum(float(S_exist[i]) + quicksum(CAPACITY_PER_SITE[m] * x[i, m] for m in SCALES) for i in range(N))
    model.addConstr(total_supply >= float(GAMMA_MIN * X_total), name="national_supply_lb")
    model.addConstr(total_supply <= float(GAMMA_MAX * X_total), name="national_supply_ub")

    # 存量/新增供给上界
    #这部分是确保每个省的流量不超过其存量和新增供给能力：
    for i in range(N):
        # 逻辑约束：存量流出 q0 最大不能超过本地已有存量 S_exist
        model.addConstr(outflow0_expr[i] <= float(S_exist[i]), name=f"supply_cap_exist_{i}")
        # 逻辑约束：新增流出 q1 最大不能超过本地新建总量 addcap
        addcap = quicksum(CAPACITY_PER_SITE[m] * x[i, m] for m in SCALES)
        model.addConstr(outflow1_expr[i] <= addcap, name=f"supply_cap_new_{i}")

    # 投资效率底线约束：建好的机器（含存量），不能闲置，总流出量必须大于 利用率下界
        supply_i = float(S_exist[i]) + addcap
        model.addConstr(outflow_total_expr[i] >= UTIL_MIN * supply_i, name=f"use_capacity_lb_{i}")

    # 需求落地约束：汇集到各地的总流入量，必须精准等于（或在区间内覆盖）该地的总需求
    # 需求端兜底：全国各地汇聚到省份 j 的流入量，必须满足其真实需求 D_j
    for j in range(N):
        inflow_total = quicksum(q0[i, j] + q1[i, j] for i in range(N) if (i, j) in q0 or (i, j) in q1)
        if DEMAND_EQUAL_PER_PROV:
            model.addConstr(inflow_total == float(D[j]), name=f"demand_eq_{j}")
        else:
            model.addConstr(inflow_total >= float(ETA_MIN * D[j]), name=f"demand_lb_{j}")
            model.addConstr(inflow_total <= float(ETA_MAX * D[j]), name=f"demand_ub_{j}")

    # 全国总量约束
    total_q = quicksum(q0[i, j] + q1[i, j] for (i, j) in q0 or (i, j) in q1)
    X = float(np.sum(D))
    if NATIONAL_TOTAL_MODE == "equal":
        model.addConstr(total_q == X, name="national_total_eq")
    elif NATIONAL_TOTAL_MODE == "interval":
        model.addConstr(total_q >= float(GAMMA_MIN * X), name="national_total_lb")
        model.addConstr(total_q <= float(GAMMA_MAX * X), name="national_total_ub")


    # 将上面这四大块累加，告诉 Gurobi 我们的终极目标是花最少的钱（含碳成本）
    model.setObjective(
        quicksum(build_cost_terms) +
        quicksum(elec_cost_terms) +
        quicksum(trans_cost_terms) +
        quicksum(carbon_cost_terms) +
        quicksum(maint_cost_terms) +    # <== 必须加上维保
        quicksum(labor_cost_terms) +    # <== 必须加上人工
        quicksum(disposal_cost_terms),  # <== 必须加上报废
        GRB.MINIMIZE
    )

    # -------- 模型组装完毕，开始使用单纯形法/分支定界算法启动求解 --------
    model.update()
    model.optimize()

    # 验证是否求解成功，没成功直接跳出返回错误信息
    status = model.status
    if status not in [GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL]:
        print("Gurobi 求解结束，状态码:", status_name(status))
        return status_name(status), None

    # ===== 求解成功！将Gurobi对象变量中的数值提取出来转化为numpy数组 =====
    x_sol = np.zeros((N, len(SCALES)), dtype=int)
    for i in range(N):
        for mi, m in enumerate(SCALES):
            xv = model.getVarByName(f"x_{i}_{m}")
            x_sol[i, mi] = int(round(xv.X)) if xv is not None else 0
            # 读取最优建设数量

    q0_sol = np.zeros((N, N), dtype=float)
    q1_sol = np.zeros((N, N), dtype=float)
    for (i, j) in EDGE_LIST:
        v0 = model.getVarByName(f"q0_{i}_{j}")
        v1 = model.getVarByName(f"q1_{i}_{j}")
        q0_sol[i, j] = float(v0.X) if v0 is not None else 0.0 # 读取最优存量调配流
        q1_sol[i, j] = float(v1.X) if v1 is not None else 0.0 # 读取最优新增调配流
    q_sol = q0_sol + q1_sol

    # 重新核算各成本明细返回给主调函数
    outflow_total_val = np.sum(q_sol, axis=1)

    build_val = 0.0
    for i in range(N):
        #carb_per_server和op_carb_per_server需要统一
        # 统一使用动态 SCC 折现后的 op_carb_per_server 核算最终总碳成本
        carbon_val = float(np.sum(alpha_coal * op_carb_per_server * outflow_total_val))
        for mi, m in enumerate(SCALES):
            cnt = x_sol[i, mi]
            build_val += SITE_CAPEX[i][m] * cnt
            carbon_val += (BUILDING_CARBON_PER_SITE[m] +
                   EQUIP_CARBON_PER_SERVER * CAPACITY_PER_SITE[m]) * CARBON_PRICE_PER_TON * cnt

    # 逻辑：全生命周期电价 * 总流出量
    elec_val   = float(np.sum(elec_per_server  * outflow_total_val))
    # 传输费仅计跨省新增流量
    trans_val = 0.0
    for (i, j) in EDGE_LIST:
        if i != j:
            trans_val += transmission_unit_cost(i, j) * q1_sol[i, j]
    #全生命周期三项关键成本：维保费 (Maintenance)、人工费 (Labor) 和 报废处理费 (Disposal)。
    maint_val = 0.0
    for i in range(N):
        for mi, m in enumerate(SCALES):
            cnt = x_sol[i, mi]
            equip_inv = c_srv[PROVINCE_NAMES[i]] * CAPACITY_PER_SITE[m] * cnt
            maint_val += equip_inv * MAINT_RATE * npv_multiplier

    labor_val = float(np.sum(LABOR_PER_SERVER * npv_multiplier * outflow_total_val))
    disposal_val = float(np.sum(DISPOSAL_PER_SERVER * terminal_discount * outflow_total_val))
    #obj_total = build_val + elec_val + carbon_val + trans_val

    # 直接使用 Gurobi 内置的最优解目标值属性，精度最高且绝不会漏项
    obj_total = model.ObjVal
    # 打包所有产出物返回
    return model, obj_total, build_val, elec_val, carbon_val, trans_val,maint_val, labor_val,disposal_val,x_sol, q_sol, q0_sol, q1_sol, elec_per_server
# =========================== 主入口 ===========================
if __name__ == "__main__":
    print("=========================================================")
    print(" 阶段二：针对具体场景（例如 PSI=1.3）运行详细的流向与经济分析 ")
    print("=========================================================")
    print("开始用 Gurobi 求解 MILP ...")
    # 这里是保留你原始的代码测试能力，指定一个具体的 psi 单独跑一遍，把细节全部 Print 出来
    target_psi_to_analyze = 1
    result = solve_milp_gurobi(current_psi=target_psi_to_analyze, verbose=True)

    if result is None:
        print("模型未返回结果。")
    else:
        model_or_status = result[0]
        if isinstance(model_or_status, Model):
            (model, obj, build_val, elec_val, carbon_val,
             trans_val,
             maint_val, labor_val, disposal_val,
             x_sol, q_sol, q0_sol, q1_sol, elec_per_server) = result


            def check_bidirectional(q, names, tol=1e-6, topk=20):
                """
                q: NxN 流量矩阵（例如 q_sol）
                names: 省名列表（PROVINCE_NAMES）
                tol: 判定“有流”的绝对阈值，过滤求解器的数值噪声
                """
                q = np.asarray(q, float)
                N = q.shape[0]
                # 双向同时大于阈值的布尔矩阵（只看上三角避免重复）
                both = (q > tol) & (q.T > tol)
                iu, ju = np.where(np.triu(both, k=1))

                pairs = []
                for i, j in zip(iu, ju):
                    pairs.append((names[i], names[j], q[i, j], q[j, i], min(q[i, j], q[j, i])))
                # 以“较小那一边”的流量从大到小排序，便于看最明显的双向
                pairs.sort(key=lambda x: x[4], reverse=True)

                # 统计信息
                pos_edges = int((q > tol).sum() - (np.diag(q) > tol).sum())  # 排除对角
                print(f"双向正流的省对个数: {len(pairs)}（阈值>{tol}）")
                print(
                    f"非零有向边数(不含对角): {pos_edges}，双向占比: {(len(pairs) * 2 / pos_edges if pos_edges > 0 else 0):.1%}")

                if pairs:
                    print(f"\n示例前{min(topk, len(pairs))}对：")
                    for nm_i, nm_j, a, b, _ in pairs[:topk]:
                        print(f"{nm_i} ↔ {nm_j}: q_ij={a:,.0f}, q_ji={b:,.0f}")
                else:
                    print("未发现双向正流；在该阈值下可视为“单向”矩阵。")

                # 用法（求解后）：


            check_bidirectional(q_sol, PROVINCE_NAMES, tol=1e-6)
            # —— 流量矩阵 ——
            print("\n【流量矩阵 q（台）】（行=出流省 i，列=入流省 j）")
            header = " " * 6 + " ".join([f"{nm:>6}" for nm in PROVINCE_NAMES])
            print(header)
            for i, nm in enumerate(PROVINCE_NAMES):
                row_vals = " ".join([f"{q_sol[i, j]:>6.0f}" for j in range(N)])
                print(f"{nm:>6} {row_vals}")

            print("\n【已有承载流量 q_0（台）】（行=出流省 i，列=入流省 j）")
            print(header)
            for i, nm in enumerate(PROVINCE_NAMES):
                row_vals = " ".join([f"{q0_sol[i, j]:>6.0f}" for j in range(N)])
                print(f"{nm:>6} {row_vals}")

            print("\n【新增承载流量 q_new（台）】（行=出流省 i，列=入流省 j）")
            print(header)
            for i, nm in enumerate(PROVINCE_NAMES):
                row_vals = " ".join([f"{q1_sol[i, j]:>6.0f}" for j in range(N)])
                print(f"{nm:>6} {row_vals}")

            # —— 传输费对角为 0 的核验 ——
            tol = 1e-9
            cost_diag = [transmission_unit_cost(i, i) for i in range(N)]
            max_abs_diag = max(abs(c) for c in cost_diag)
            print("\n【传输费对角核验】")
            print("每个省(i,i)的单位传输费：", [f"{c:.6g}" for c in cost_diag])
            print("对角最大绝对值 =", f"{max_abs_diag:.6g}")
            if max_abs_diag <= tol:
                print("结论：所有 (i,i) 的单位传输费为 0（在容差内）✅")
            else:
                bad = [(PROVINCE_NAMES[i], cost_diag[i]) for i in range(N) if abs(cost_diag[i]) > tol]
                print("结论：存在 (i,i) 的单位传输费非零：", [(n, f"{v:.6g}") for n, v in bad], "❌")

            print("\n求解状态:", status_name(model.status))
            print("总成本（元）:", f"{obj:,.0f}")
            print("  ├─ 建设CAPEX（元）:", f"{build_val:,.0f}")
            print("  ├─ 电费（元, 生命周期）:", f"{elec_val:,.0f}")
            print("  ├─ 碳社会成本（元, 生命周期）:", f"{carbon_val:,.0f}")
            print("  ├─ 传输费（元）:", f"{trans_val:,.0f}")
            print("  ├─ 维保费（元, 生命周期）:", f"{maint_val:,.0f}")
            print("  ├─ 人工费（元, 生命周期）:", f"{labor_val:,.0f}")
            print("  └─ 报废处理费（元, 期末折现）:", f"{disposal_val:,.0f}")
            # ==========================================
            # 新增：全生命周期 (LCA) 五大核心成本指标重组
            # ==========================================
            initial_cost = build_val + trans_val
            energy_cost = elec_val
            maintenance_cost = maint_val + labor_val
            terminal_cost = disposal_val
            social_cost_of_carbon = carbon_val

            print("\n【全生命周期(LCA)五大核心成本指标 (LCA 5 Core Metrics)】")
            print(f"  * Initial Cost:          {initial_cost:>20,.0f} 元")
            print(f"  * Energy Cost:           {energy_cost:>20,.0f} 元")
            print(f"  * Maintenance Cost:      {maintenance_cost:>20,.0f} 元")
            print(f"  * Terminal Cost:         {terminal_cost:>20,.0f} 元")
            print(f"  * Social Cost of Carbon: {social_cost_of_carbon:>20,.0f} 元")

            # 顺手加一个校验，确保这五项加起来严格等于剥离了虚拟惩罚后的真实总成本
            total_lca_cost = initial_cost + energy_cost + maintenance_cost + terminal_cost + social_cost_of_carbon
            print("-" * 50)
            print(f"  => Total LCA Cost:       {total_lca_cost:>20,.0f} 元")
            # —— 各省新增服务器台数 ——
            new_servers = (x_sol * np.array([CAPACITY_PER_SITE[m] for m in SCALES])).sum(axis=1).astype(int)
            total_new_servers = int(new_servers.sum())
            print("\n【各省需新建服务器台数】")
            for i in range(N):
                print(f"{PROVINCE_NAMES[i]}：{new_servers[i]:,}")
            print(f"\n全国合计新建服务器台数：{total_new_servers:,}")

            # —— 能力 vs 出流 & 需求核验 ——
            supply_cap = S_exist + np.sum(x_sol * np.array([CAPACITY_PER_SITE[m] for m in SCALES]), axis=1)
            outflow = np.sum(q_sol, axis=1)
            inflow = np.sum(q_sol, axis=0)

            print("\n【供给能力 vs 出流】(前10省)")
            for i in range(min(10, N)):
                print(PROVINCE_NAMES[i], "能力=", int(supply_cap[i]), "出流=", int(outflow[i]))

            print("\n【需求满足核验】(前10省)")
            for j in range(min(10, N)):
                if DEMAND_EQUAL_PER_PROV:
                    print(PROVINCE_NAMES[j], "需求V=", int(D[j]), "入流=", int(inflow[j]))
                else:
                    print(PROVINCE_NAMES[j], f"区间[{int(ETA_MIN*D[j])}..{int(ETA_MAX*D[j])}] 入流=", int(inflow[j]))

            # —— 服务半径核验 ——
            max_violate = 0.0
            for i in range(N):
                for j in range(N):
                    if dist[i, j] > H0_KM and q_sol[i, j] > 1e-6:
                        max_violate = max(max_violate, q_sol[i, j])
            print("\n【服务半径核验】半径外最大 q =", max_violate)
            print("ΣD=", int(D.sum()))
            print("ΣS_exist=", int(S_exist.sum()))
            print("全国理论最少需要新增 ΣD-ΣS_exist =", int(D.sum() - S_exist.sum()))

            # —— 新增装机 / 实需新增 / 冗余 ——
            cap_per_scale = np.array([CAPACITY_PER_SITE[m] for m in SCALES])
            addcap_by_prov = (x_sol * cap_per_scale).sum(axis=1)#每个省新建了多少服务器机架
            outflow_by_prov = q_sol.sum(axis=1)  #实际每个省份用的
            need_new_by_prov = np.maximum(0.0, outflow_by_prov - S_exist)  # 实际所需新增
            slack_by_prov = addcap_by_prov - need_new_by_prov             # 冗余装机
            print("新增装机总计 =", int(addcap_by_prov.sum()))
            print("实际所需新增 =", int(need_new_by_prov.sum()))
            print("冗余装机     =", int(slack_by_prov.sum()))
            viol = np.min(outflow_by_prov - S_exist)
            print("\n【已建必用核验】最小(outflow_i - S_exist_i) =", f"{viol:,.0f}")

            # —— 经济效益（产值拉动）一次性计算 ——
            econ = compute_economic_benefits(
                x_sol=x_sol, q_sol=q_sol,
                PROVINCE_NAMES=PROVINCE_NAMES,
                SCALES=SCALES,
                CAPACITY_PER_SITE=CAPACITY_PER_SITE,
                c_lab=c_lab, c_mat=c_mat, c_land=c_land, c_srv=c_srv,
                P_LAB=P_LAB, P_MAT=P_MAT, P_LAND=P_LAND,
                elec_per_server=elec_per_server,
                m_build=m_build, m_equip=m_equip, m_elec=m_elec,
                m_service=m_service, m_labor=m_labor, m_env=m_env,  # <== 记得在这里传参进去！
                BENEFIT_WEIGHT=BENEFIT_WEIGHT
            )
            # 输出各省份的投入与产出情况
            #print("\n【各省投入与产出情况】")
            #print("省份\t建筑投入（元）\t设备投入（元）\t电力投入（元）\t相对产值")
            #for i, nm in enumerate(PROVINCE_NAMES):
            #    print(f"{nm}\t{econ['build_spend'][i]:,.0f}\t{econ['equip_spend'][i]:,.0f}\t"
            #          f"{econ['elec_spend'][i]:,.0f}\t{econ['relative_output'][i]:.4f}")

            print("\n【各省投入与相对产值（relative_output）】")
            # 表头：增加列宽和说明，确保对齐
            print(
                f"{'省份':<6}\t{'建筑投入（万元）':<12}\t{'设备投入（万元）':<12}\t{'电力投入（万元）':<12}\t{'relative_output（带动产值/省份GDP）':<10}")
            for i, nm in enumerate(PROVINCE_NAMES):
                # 将元转换为万元（可选，更易读），保留4位小数展示relative_output
                build_wan = econ['build_spend'][i] / 10000
                equip_wan = econ['equip_spend'][i] / 10000
                elec_wan = econ['elec_spend'][i] / 10000
                rel_output = econ['relative_output'][i]
                print(f"{nm:<6}\t{build_wan:>10.2f}\t{equip_wan:>10.2f}\t{elec_wan:>10.2f}\t{rel_output:>10.6f}")


            # 产业带动输出（全国合计）
            print("\n【全国产业带动效益】")
            print(f"未乘λ（元）: {econ['total_raw']:,.0f}")
            print(f"全国相对增长值: {econ['national_gdp_growth_rate']:.6f}%")
            print(f"全国总GDP增幅值（induced_raw总和 ÷ 全国GDP总和）：{econ['national_gdp_growth_rate']:.4f}%")

            # 输出每个省份的经济效益
            print("\n【各省经济效益（未乘λ）】")
            for i, nm in enumerate(PROVINCE_NAMES):
                print(f"{nm}:\t建筑效益={m_build[i] * econ['build_spend'][i]:,.0f}  "
                      f"设备效益={m_equip[i] * econ['equip_spend'][i]:,.0f}  电力效益={m_elec[i] * econ['elec_spend'][i]:,.0f}  "
                      f"总效益={econ['induced_raw'][i]:,.0f}")

            print("\nx_{i,m}（行=省 i，列=[M,L,XL]）：\n", x_sol)

            # 新增：输出各省产出乘数及加权综合乘数
            # ==========================================
            print("\n【各省产出乘数及加权综合乘数】")
            # 打印表头
            print(
                f"{'省份':<6}\t{'建筑乘数(m_build)':<15}\t{'电力乘数(m_elec)':<15}\t{'设备乘数(m_equip)':<15}\t{'加权综合乘数(Weighted)':<15}")

            weighted_multipliers = []

            for i, nm in enumerate(PROVINCE_NAMES):
                # 获取该省份在三个部门的投入金额
                bs = econ['build_spend'][i]
                es = econ['elec_spend'][i]
                eqs = econ['equip_spend'][i]
                total_spend = bs + es + eqs

                # 计算加权乘数
                # 公式：(m_build * build_spend + m_elec * elec_spend + m_equip * equip_spend) / 总投入
                if total_spend > 1e-6:  # 避免除以零
                    w_mult = (m_build[i] * bs + m_elec[i] * es + m_equip[i] * eqs) / total_spend
                else:
                    # 如果该省份没有任何投入（例如没有建设也没有流量），加权乘数无意义，可以设为0或取平均值
                    # 这里为了展示，如果没投入就暂显示0，或者您可以选择显示单纯的平均值
                    w_mult = 0.0

                weighted_multipliers.append(w_mult)

                # 格式化打印
                print(f"{nm:<6}\t{m_build[i]:>15.4f}\t{m_elec[i]:>15.4f}\t{m_equip[i]:>15.4f}\t{w_mult:>15.4f}")

            # 如果您想直接要把这个数组复制拿走，可以取消下面这行的注释：
                #print("\nweighted_multipliers_array =", weighted_multipliers)
            # =========================== 新增：输出东中西部建设机架数 ===========================
            print("\n【区域新增服务器机架统计】")
            # 定义区域字典 (复用前面定义的区域列表)
            regions_map = {
                "东部": eastern_provinces,
                "中部": central_provinces,
                "西部": western_provinces
            }
            # 统计并输出
            grand_total_check = 0
            for reg_name, prov_list in regions_map.items():
                reg_sum = 0
                for nm in prov_list:
                    if nm in PROVINCE_NAMES:
                        idx = PROVINCE_NAMES.index(nm)
                        reg_sum += new_servers[idx]  # new_servers 在前面第485行已计算
                grand_total_check += reg_sum
                print(f"{reg_name}地区 ({len(prov_list)}省) 新增机架总数: {reg_sum:,.0f}")
            print(f"区域统计合计校验: {grand_total_check:,.0f} (应等于全国合计 {total_new_servers:,})")
        else:
            print("求解返回：", model_or_status)
