# -*- coding: utf-8 -*-
"""
文件名: milp_baseline_exact_gurobi_v1.py
目的: 基线“准确”MILP（一次性求最优），使用 gurobipy API 求解
说明: 电费/碳费按 outflow 计；传输费仅计“新增承载 q1 的跨省流量”
作者: ChatGPT
日期: 2025-11
"""
import math
import numpy as np
import os
from openpyxl import load_workbook

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

# =========================== 可调总开关 ===========================
DEMAND_EQUAL_PER_PROV = False
ETA_MIN = 0.95
ETA_MAX = 1.05

NATIONAL_TOTAL_MODE = "interval"  # "none"|"equal"|"interval"
GAMMA_MIN = 0.95
GAMMA_MAX = 1.05

USE_MINCOST_Q  = True             # 仅“旧口径（按流量计费）”下有效
LOCAL_FIRST_COEF = 0.0            # 跨省偏置，0 表示不开启

CARBON_PRICE_PER_TON = 240.9
EMISSION_FACTOR_D = 1.9

# Gurobi 参数
TIME_LIMIT = 3600
MIP_GAP = 1e-6
THREADS = 0
OUTPUT_FLAG = 1

# =========================== 常量 ===========================
H0_KM = 980.0/5*5
E_RACK_MWH = 12
E_RACK_KWH = E_RACK_MWH * 24 * 365
#E_RACK_KWH=10800
C_TRAN = 1000
L_YEARS = 18

SCALES = ["M", "L", "XL"]
CAPACITY_PER_SITE = {"M": 3000, "L": 10000, "XL": 20000}

# ===== IO 相关（L_inverse 乘数与三部门映射）=====
BASE_DIR = r"D:\BaiduNetdiskDownload\投入产出表\31省市区42部门投入产出表1997-2017年\2017年各省份投入产出表"
TARGET_SHEET = "L_inverse"

SECTOR_BUILD = "建筑"
SECTOR_ELEC  = "电力、热力的生产和供应"
SECTOR_EQUIP = "通信设备、计算机和其他电子设备"

BENEFIT_WEIGHT = 0.0000

# 最低利用率（存量+新增）
UTIL_MIN = 0.95

# =========================== 省份与经纬度 ===========================
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
N = len(provinces_seed)
PROVINCE_NAMES = [nm for (nm, _, _) in provinces_seed]
COORDS = [(lat, lon) for (_, lat, lon) in provinces_seed]

# =========================== 各个省份GDP ===========================

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
D = np.array([
    238305, 56631, 155808, 65867, 123834, 49124, 75841, 288807, 412045, 296792,
    130116, 146761, 89920, 246274, 186793, 158628, 138369, 616746, 78927, 26549,
    85906, 192848, 114883, 83386, 115329, 37915, 18852, 49993, 54661, 157846
], dtype=float)

S_exist = np.array([
    173999, 30674, 92690, 34870, 78167, 27265, 50887, 218857, 230997, 184126,
    64053, 71613, 45795, 116814, 89797, 77003, 67801, 422611, 40802, 17011,
    43972, 109514, 85060, 42827, 68824, 22173, 13515, 43174, 29780, 126494
], dtype=float)
D-S_exist
# =========================== 电价/结构/煤耗 ===========================
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
# =========================== 特殊调价：中部地区火电价格上涨 ===========================
# =========================== 区域省份划分 ===========================
# 中部地区省份列表
central_provinces = ["吉林", "黑龙江",
                     "山西", "安徽", "江西", "河南", "湖北", "湖南"]
# 东部地区 (11省市)
eastern_provinces = [
    "北京", "辽宁", "天津", "河北", "上海", "江苏",
    "浙江", "福建", "山东", "广东", "海南"
]
# 西部地区 (11省区)
western_provinces = [
    "内蒙古", "广西", "重庆", "四川", "贵州", "云南",
    "陕西", "甘肃", "青海", "宁夏", "新疆"
]

print("\n>>> 正在调整中部地区火电价格 (+0.2)...")
for nm in western_provinces:
    if nm in PROVINCE_NAMES:
        idx = PROVINCE_NAMES.index(nm) # 找到该省份对应的索引
        old_val = p_coal[idx]
        p_coal[idx] *= 0.8             # 核心修改：火电价格 + 0.2
        print(f"  {nm}: 原价 {old_val:.4f} -> 现价 {p_coal[idx]:.4f}")
# ===================================================================================


p_ren = np.array([
    0.8000, 0.8000, 0.5541, 0.6348, 0.5140, 0.5079, 0.4991, 0.8142, 0.7524, 0.6898,
    0.6606, 0.4084, 0.4910, 0.6529, 0.5032, 0.2999, 0.3777, 0.3686, 0.2698, 0.4451,
    0.3230, 0.2853, 0.3154, 0.2220, 0.4626, 0.3650, 0.3914, 0.5902, 0.4434, 0.5424
], dtype=float)

alpha_coal = np.array([
    0.9593, 0.9797, 0.8645, 0.9049, 0.8670, 0.7740, 0.8545, 0.9769, 0.9512, 0.8967,
    0.9352, 0.6999, 0.8161, 0.9494, 0.9356, 0.4064, 0.5866, 0.8918, 0.4721, 0.8478,
    0.6422, 0.0992, 0.6014, 0.0811, 0.8902, 0.5268, 0.2484, 0.8242, 0.7752, 0.8445
], dtype=float)


#alpha_coal = np.full_like(alpha_coal, 0)



r_g_per_kwh = np.array([
    241, 316, 325, 330, 315, 308, 330, 302, 308, 299, 309, 310, 313, 323, 317, 309, 314, 315,
    318, 310, 332, 322, 331, 335, 329, 329, 361, 347, 336, 337
], dtype=float)

# =========================== PUE ===========================
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

P_LAB  = {"M": 0.13 * 1e4 * 1.5, "L": 0.30 * 1e4 * 1.5, "XL": 0.40 * 1e4 * 1.5}
P_MAT  = {"M": 0.01 * 1e4 * 1.5, "L": 0.03 * 1e4 * 1.5, "XL": 0.05 * 1e4 * 1.5}
P_LAND = {"M": 1.30 * 1e4 * 1.5, "L": 3.00 * 1e4 * 1.5, "XL": 5.00 * 1e4 * 1.5}

SITE_CAPEX = {}
for i, nm in enumerate(PROVINCE_NAMES):
    SITE_CAPEX[i] = {}
    for m in SCALES:
        SITE_CAPEX[i][m] = float(
            c_lab[nm]  * P_LAB[m]  +
            c_mat[nm]  * P_MAT[m]  +
            c_land[nm] * P_LAND[m] +
            c_srv[nm]  * CAPACITY_PER_SITE[m]
        )

# =========================== 距离与候选边集 ===========================
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

dist = np.zeros((N, N))
for i in range(N):
    for j in range(N):
        (lat1, lon1) = COORDS[i]
        (lat2, lon2) = COORDS[j]
        dist[i, j] = haversine_km(lat1, lon1, lat2, lon2)

EDGE_LIST = [(i, j) for i in range(N) for j in range(N) if dist[i, j] <= H0_KM]

def transmission_unit_cost(i, j):
    if i == j:
        return 0.0
    base = (C_TRAN * dist[i, j]) if USE_MINCOST_Q else 0.0
    bias = (LOCAL_FIRST_COEF if i != j else 0.0)
    return base + bias

# =========================== IO 取数工具 ===========================
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

    want_names = {SECTOR_BUILD: None, SECTOR_ELEC: None, SECTOR_EQUIP: None}
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
    m_elec  = colsum_excel(want_names[SECTOR_ELEC])
    m_equip = colsum_excel(want_names[SECTOR_EQUIP])

    wb.close()
    return m_build, m_elec, m_equip

# 读取全省乘数
m_build = np.zeros(N, dtype=float)
m_elec  = np.zeros(N, dtype=float)
m_equip = np.zeros(N, dtype=float)
for i, prov in enumerate(PROVINCE_NAMES):
    fp = locate_province_file(BASE_DIR, prov)
    if not fp:
        raise FileNotFoundError(f"未找到 {prov} 的 IO 表文件（{prov}.xlsx 或 01-{prov}.xlsx 等）")
    mb, me, mq = read_multipliers_for_province(fp)
    m_build[i], m_elec[i], m_equip[i] = mb, me, mq

# =========================== 经济效益计算 ===========================
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
    BENEFIT_WEIGHT: float = 1.0
):
    N = len(PROVINCE_NAMES)
    outflow = q_sol.sum(axis=1)

    build_spend = np.zeros(N, dtype=float)
    equip_spend = np.zeros(N, dtype=float)
    elec_spend  = np.zeros(N, dtype=float)

    for i, nm in enumerate(PROVINCE_NAMES):
        bsum = 0.0
        esum = 0.0
        for mi, m in enumerate(SCALES):
            cnt = float(x_sol[i, mi])
            bsum += (c_lab[nm]*P_LAB[m] + c_mat[nm]*P_MAT[m] + c_land[nm]*P_LAND[m]) * cnt
            esum += (c_srv[nm] * CAPACITY_PER_SITE[m]) * cnt

        build_spend[i] = bsum
        equip_spend[i] = esum
        elec_spend[i]  = elec_per_server[i] * outflow[i]
    #没有乘权重的总产出
    induced_raw = m_build * build_spend + m_equip * equip_spend + m_elec * elec_spend
    #乘权重的总产出
    induced_weighted= BENEFIT_WEIGHT * induced_raw
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
        "total_weighted": float(induced_weighted.sum()),
        "national_gdp_growth_rate":national_gdp_growth_rate,
    }

# =========================== Gurobi 求解器版本 ===========================
def solve_milp_gurobi():
    model = Model("DC_Siting_Flow_30Prov_Gurobi")

    model.setParam("OutputFlag", OUTPUT_FLAG)
    if TIME_LIMIT and TIME_LIMIT > 0:
        model.setParam("TimeLimit", TIME_LIMIT)
    if MIP_GAP is not None:
        model.setParam("MIPGap", MIP_GAP)
    if THREADS and THREADS > 0:
        model.setParam("Threads", THREADS)

    # 变量：x_{i,m}、q0_{i,j}、q1_{i,j}
    x = {}
    for i in range(N):
        for m in SCALES:
            x[i, m] = model.addVar(vtype=GRB.INTEGER, name=f"x_{i}_{m}", lb=0)

    q0, q1 = {}, {}
    for (i, j) in EDGE_LIST:
        q0[i, j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"q0_{i}_{j}", lb=0.0)
        q1[i, j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"q1_{i}_{j}", lb=0.0)

    model.update()

    # —— 电价/碳价口径（按 outflow 计）——
    unit_price = alpha_coal * p_coal + (1 - alpha_coal) * p_ren
    # # g/kWh → kg/kWh 每发 1 kWh 需要的煤耗（g/kWh）
    kg_coal_per_kwh = r_g_per_kwh / 1000.0
    u = 1.0
    PUE_rep = np.array([PUE_max[i]["XL"] for i in range(N)])

    elec_per_server = L_YEARS * (unit_price * PUE_rep * u * E_RACK_KWH)
    #EMISSION_FACTOR_D：每吨煤产生的 CO₂（tCO₂/吨煤）
    carb_per_server = (
        L_YEARS * (PUE_rep * u * E_RACK_KWH * kg_coal_per_kwh * EMISSION_FACTOR_D) / 1000.0 * CARBON_PRICE_PER_TON
    )

    outflow0_expr = {i: quicksum(q0[i, j] for j in range(N) if (i, j) in q0) for i in range(N)}
    outflow1_expr = {i: quicksum(q1[i, j] for j in range(N) if (i, j) in q1) for i in range(N)}
    outflow_total_expr = {i: outflow0_expr[i] + outflow1_expr[i] for i in range(N)}

    # 三类投入金额（对接乘数）
    build_spend = {}
    equip_spend = {}
    elec_spend = {}
    for i, nm in enumerate(PROVINCE_NAMES):
        build_spend[i] = quicksum(
            (c_lab[nm]*P_LAB[m] + c_mat[nm]*P_MAT[m] + c_land[nm]*P_LAND[m]) * x[i, m] for m in SCALES
        )
        equip_spend[i] = quicksum((c_srv[nm] * CAPACITY_PER_SITE[m]) * x[i, m] for m in SCALES)
        elec_spend[i]  = elec_per_server[i] * outflow_total_expr[i]

    # 目标：CAPEX + 电费 + 碳费 + 传输费(仅新增、跨省) - λ*产业带动
    build_cost_terms = [SITE_CAPEX[i][m] * x[i, m] for i in range(N) for m in SCALES]
    elec_cost_terms  = [elec_per_server[i]  * outflow_total_expr[i] for i in range(N)]
    carbon_cost_terms = [alpha_coal[i] * carb_per_server[i] * outflow_total_expr[i] for i in range(N)]
    #trans_cost_terms = [transmission_unit_cost(i, j) * q1[i, j] for (i, j) in EDGE_LIST if i != j]
    # 定义一个极小的惩罚系数 epsilon，或者直接使用正常的传输成本系数
    # 如果您认为存量传输确实不该花大钱，就乘一个 0.01 或 0.001
    epsilon = 0.01

    trans_cost_terms = []
    for (i, j) in EDGE_LIST:
        if i != j:
            cost_unit = transmission_unit_cost(i, j)
            # q1 正常计费
            term_q1 = cost_unit * q1[i, j]
            # q0 象征性计费（消除双向流的关键！）
            term_q0 = (cost_unit * epsilon) * q0[i, j]

            trans_cost_terms.append(term_q1 + term_q0)

    induced_terms = []
    for i in range(N):
        induced_terms += [m_build[i]*build_spend[i]/province_GDP[i], m_equip[i]*equip_spend[i]/province_GDP[i], m_elec[i]*elec_spend[i]/province_GDP[i]]
    induced_total_expr = quicksum(induced_terms)

    model.setObjective(
        quicksum(build_cost_terms) +
        quicksum(elec_cost_terms) +
        quicksum(carbon_cost_terms) +
        quicksum(trans_cost_terms) -
        BENEFIT_WEIGHT * induced_total_expr,
        GRB.MINIMIZE
    )

    # ---------- 约束 ----------
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
        model.addConstr(outflow0_expr[i] <= float(S_exist[i]), name=f"supply_cap_exist_{i}")
        addcap = quicksum(CAPACITY_PER_SITE[m] * x[i, m] for m in SCALES)
        model.addConstr(outflow1_expr[i] <= addcap, name=f"supply_cap_new_{i}")

    # 最低利用率：总出流 ≥ UTIL_MIN * (存量 + 新增)
    for i in range(N):
        addcap_i = quicksum(CAPACITY_PER_SITE[m] * x[i, m] for m in SCALES)
        supply_i = float(S_exist[i]) + addcap_i
        model.addConstr(outflow_total_expr[i] >= UTIL_MIN * supply_i, name=f"use_capacity_lb_{i}")

    # 需求满足（等式或区间）
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

    # 开始求解
    model.update()
    model.optimize()

    status = model.status
    if status not in [GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL]:
        print("Gurobi 求解结束，状态码:", status_name(status))
        return status_name(status), None

    # ===== 提取解 =====
    x_sol = np.zeros((N, len(SCALES)), dtype=int)
    for i in range(N):
        for mi, m in enumerate(SCALES):
            xv = model.getVarByName(f"x_{i}_{m}")
            x_sol[i, mi] = int(round(xv.X)) if xv is not None else 0

    q0_sol = np.zeros((N, N), dtype=float)
    q1_sol = np.zeros((N, N), dtype=float)
    for (i, j) in EDGE_LIST:
        v0 = model.getVarByName(f"q0_{i}_{j}")
        v1 = model.getVarByName(f"q1_{i}_{j}")
        q0_sol[i, j] = float(v0.X) if v0 is not None else 0.0
        q1_sol[i, j] = float(v1.X) if v1 is not None else 0.0
    q_sol = q0_sol + q1_sol

    # 分项值
    outflow_total_val = np.sum(q_sol, axis=1)

    build_val = 0.0
    for i in range(N):
        for mi, m in enumerate(SCALES):
            cnt = x_sol[i, mi]
            build_val += SITE_CAPEX[i][m] * cnt

    elec_val   = float(np.sum(elec_per_server  * outflow_total_val))
    carbon_val = float(np.sum(alpha_coal * carb_per_server * outflow_total_val))

    # 传输费仅计跨省新增流量
    trans_val = 0.0
    for (i, j) in EDGE_LIST:
        if i != j:
            trans_val += transmission_unit_cost(i, j) * q1_sol[i, j]

    obj_total = build_val + elec_val + carbon_val + trans_val

    return model, obj_total, build_val, elec_val, carbon_val, trans_val, x_sol, q_sol, q0_sol, q1_sol, elec_per_server

# =========================== 主入口 ===========================
if __name__ == "__main__":
    print("开始用 Gurobi 求解 MILP ...")
    result = solve_milp_gurobi()

    if result is None:
        print("模型未返回结果。")
    else:
        model_or_status = result[0]
        if isinstance(model_or_status, Model):
            (model, obj, build_val, elec_val, carbon_val,
             trans_val, x_sol, q_sol, q0_sol, q1_sol, elec_per_server) = result


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
            print("总目标（元）:", f"{obj:,.0f}")
            print("  ├─ 建设CAPEX（元）:", f"{build_val:,.0f}")
            print("  ├─ 电费（元, 生命周期）:", f"{elec_val:,.0f}")
            print("  ├─ 碳费（元, 生命周期）:", f"{carbon_val:,.0f}")
            print("  └─ 传输费（元）:", f"{trans_val:,.0f}")

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
            print(f"乘λ（λ={BENEFIT_WEIGHT:.3f}）: {econ['total_weighted']:,.0f}")
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
