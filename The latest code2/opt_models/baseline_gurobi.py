# -*- coding: utf-8 -*-  # 指定源码文件的字符编码为 UTF-8，保证中文注释/字符串不乱码
"""
文件名: milp_baseline_exact_gurobi_v1.py
目的: 基线“准确”MILP（一次性求最优），使用 gurobipy API 求解
说明: 这里将电费/碳费从“按 x 计”改为“按 outflow 计”；扩建口径下仅对“新增承载流量 q1”的跨省部分计传输费。
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

NATIONAL_TOTAL_MODE = "interval"
GAMMA_MIN = 0.95
GAMMA_MAX = 1.05

USE_MINCOST_Q  = True
LOCAL_FIRST_COEF = 0.0

CARBON_PRICE_PER_TON = 240.9
EMISSION_FACTOR_D = 1.9

# Gurobi solver params
TIME_LIMIT = 3600
MIP_GAP = 1e-6
THREADS = 0
OUTPUT_FLAG = 1
# ---------- 新增：最低利用率（含存量+新增） ----------
UTIL_MIN = 0.85     # 例：至少利用 85% 的 (存量 + 新增) 供给能力；可按需调大/调小

# ---------- 新增：链路固定费口径 ----------
USE_FIXED_LINK_COST = False  # True=链路固定费；False=按机架*公里的单位费（旧口径）
C_LINK_PER_KM = 10000.0      # 元/公里（示例值；你需要根据实践口径调整）
# =========================== 常量 ==========================
H0_KM = 980.0
E_RACK_MWH = 12
E_RACK_KWH = E_RACK_MWH * 24 * 365
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
sum(D)-sum(S_exist)
sum(D)+sum(S_exist)

# =========================== 电价/结构/煤耗 ===========================
p_coal = np.array([
    0.6258, 0.6542, 0.5986, 0.4514, 0.5589, 0.6549, 0.5656, 0.6145, 0.5824, 0.6534,
    0.5958, 0.6083, 0.6249, 0.6483, 0.6192, 0.6384, 0.6806, 0.6354, 0.6993, 0.6920,
    0.6054, 0.5110, 0.5166, 0.3519, 0.4527, 0.4584, 0.3811,0.4687, 0.3200, 0.4298
], dtype=float)

p_ren = np.array([  # 可再生能源电价 c^g_j（元/kWh）
    0.8000,  # 北京
    0.8000,  # 天津
    0.5541,  # 河北
    0.6348,  # 山西
    0.5140,  # 辽宁
    0.5079,  # 吉林
    0.4991,  # 黑龙江
    0.8142,  # 上海
    0.7524,  # 江苏
    0.6898,  # 浙江
    0.6606,  # 安徽
    0.4084,  # 福建
    0.4910,  # 江西
    0.6529,  # 山东
    0.5032,  # 河南
    0.2999,  # 湖北
    0.3777,  # 湖南
    0.3686,  # 广东
    0.2698,  # 广西
    0.4451,  # 海南
    0.3230,  # 重庆
    0.2853,  # 四川
    0.3154,  # 贵州
    0.2220,  # 云南
    0.4626,  # 陕西
    0.3650,  # 甘肃
    0.3914,  # 青海
    0.5902,  # 宁夏
    0.4434,  # 新疆
    0.5424   # 内蒙古
], dtype=float)

#alpha_coal = np.array([0.959287532, 0.979701392, 0.864457831, 0.904916847, 0.866966581,
# 0.77394636,  0.854450262, 0.976905312, 0.951178094, 0.896721889, 0.935248887,
# 0.700492005, 0.816033755, 0.949393129, 0.935603257, 0.406427221, 0.586567164,
# 0.89205186,  0.472085386, 0.847826087, 0.642189219, 0.099187447, 0.60139165,
# 0.081135903, 0.890205864, 0.526825633, 0.248376623, 0.824199288, 0.775247525, 0.844484629],dtype=float)

alpha_coal = np.array([
    0.9593,  # 北京  95.93%
    0.9797,  # 天津  97.97%
    0.8645,  # 河北  86.45%
    0.9049,  # 山西  90.49%
    0.8670,  # 辽宁  86.70%
    0.7740,  # 吉林  77.40%
    0.8545,  # 黑龙江 85.45%
    0.9769,  # 上海  97.69%
    0.9512,  # 江苏  95.12%
    0.8967,  # 浙江  89.67%
    0.9352,  # 安徽  93.52%
    0.6999,  # 福建  69.99%
    0.8161,  # 江西  81.61%
    0.9494,  # 山东  94.94%
    0.9356,  # 河南  93.56%
    0.4064,  # 湖北  40.64%
    0.5866,  # 湖南  58.66%
    0.8918,  # 广东  89.18%
    0.4721,  # 广西  47.21%
    0.8478,  # 海南  84.78%
    0.6422,  # 重庆  64.22%
    0.0992,  # 四川   9.92%
    0.6014,  # 贵州  60.14%
    0.0811,  # 云南   8.11%
    0.8902,  # 陕西  89.02%
    0.5268,  # 甘肃  52.68%
    0.2484,  # 青海  24.84%
    0.8242,  # 宁夏  82.42%
    0.7752,  # 新疆  77.52%
    0.8445   # 内蒙古 84.45%（原表“内蒙”）
], dtype=float)
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

# =========================== CAPEX (示例分项口径) ===========================
c_lab = {
    "北京": 114631, "天津": 75579, "河北": 55152, "山西": 54673, "辽宁": 55093, "吉林": 48961, "黑龙江": 48414,
    "上海": 110117, "江苏": 64663, "浙江": 56265, "安徽": 60785, "福建": 61394, "江西": 57340, "山东": 59229,
    "河南": 53163, "湖北": 61658, "湖南": 52645, "广东": 64747, "广西": 55047, "海南": 46019, "重庆": 59605,
    "四川": 55134, "贵州": 62684, "云南": 49128, "陕西": 58710, "甘肃": 51863, "青海": 69611, "宁夏": 5286,
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

P_LAB = {"M": 0.13 * 1e4 *1.5, "L": 0.30 * 1e4*1.5, "XL": 0.40 * 1e4*1.5}
P_MAT = {"M": 0.01 * 1e4 *1.5, "L": 0.03 * 1e4*1.5, "XL": 0.05 * 1e4*1.5}
P_LAND = {"M": 1.30 * 1e4*1.5, "L": 3.00 * 1e4*1.5, "XL": 5.00 * 1e4*1.5}

SITE_CAPEX = {}
for i, nm in enumerate(PROVINCE_NAMES):
    SITE_CAPEX[i] = {}
    for m in SCALES:
        SITE_CAPEX[i][m] = float(
            c_lab[nm] * P_LAB[m] +
            c_mat[nm] * P_MAT[m] +
            c_land[nm] * P_LAND[m] +
            c_srv[nm] * CAPACITY_PER_SITE[m]
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

def transmission_link_cost(i, j):
    """链路固定费（不随流量变化），只在 i != j 时生效"""
    if i == j:
        return 0.0
    base = (C_LINK_PER_KM * dist[i, j]) if USE_MINCOST_Q else 0.0
    bias = (LOCAL_FIRST_COEF if i != j else 0.0)
    return base + bias

def locate_province_file(base_dir: str, prov: str):
    p1 = os.path.join(base_dir, f"{prov}.xlsx")
    if os.path.exists(p1): return p1
    for i in range(1, 40):
        p2 = os.path.join(base_dir, f"{i:02d}-{prov}.xlsx")
        if os.path.exists(p2): return p2
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
        name = str(v).strip()
        header_cells.append((c, name))

    want_names = {
        SECTOR_BUILD: None,
        SECTOR_ELEC:  None,
        SECTOR_EQUIP: None,
    }
    for c, name in header_cells:
        if name in want_names and want_names[name] is None:
            want_names[name] = c

    missing = [nm for nm, col in want_names.items() if col is None]
    if missing:
        wb.close()
        raise KeyError(
            f"{os.path.basename(xlsx_path)}: 第1行未找到这些列头：{missing}。"
            f"（请核对部门命名是否与 {TARGET_SHEET} 中列标题完全一致）"
        )

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

# ===== 读取每省乘数 =====
m_build = np.zeros(N, dtype=float)
m_elec  = np.zeros(N, dtype=float)
m_equip = np.zeros(N, dtype=float)
for i, prov in enumerate(PROVINCE_NAMES):
    fp = locate_province_file(BASE_DIR, prov)
    if not fp:
        raise FileNotFoundError(f"未找到 {prov} 的 IO 表文件（{prov}.xlsx 或 01-{prov}.xlsx 等）")
    mb, me, mq = read_multipliers_for_province(fp)
    m_build[i], m_elec[i], m_equip[i] = mb, me, mq

def debug_check_L(xlsx_path: str):
    wb = load_workbook(xlsx_path, data_only=True)
    if TARGET_SHEET not in wb.sheetnames:
        wb.close()
        raise ValueError(f"{os.path.basename(xlsx_path)}: 找不到工作表 {TARGET_SHEET}")
    ws = wb[TARGET_SHEET]

    row_names = [ws.cell(row=1+i, column=1).value for i in range(1, 43)]
    header_cells = []
    for c in range(1, 201):
        v = ws.cell(row=1, column=c).value
        if v is not None:
            header_cells.append((c, str(v).strip()))

    print(f"\n[L_inverse 抽检] 文件={os.path.basename(xlsx_path)}")
    print(f"  估计行数(应为42)={len([nm for nm in row_names if nm is not None])}")
    print(f"  第1行非空列头数量={len(header_cells)}")

    def find_col_idx(name: str):
        for c, nm in header_cells:
            if nm == name:
                return c
        return None

    for nm in [SECTOR_BUILD, SECTOR_ELEC, SECTOR_EQUIP]:
        colx = find_col_idx(nm)
        if colx is None:
            print(f"  ✖ 未找到部门列：{nm}")
            continue

        vals5 = []
        for r in range(2, min(7, 44)):
            v = ws.cell(row=r, column=colx).value
            vals5.append(float(v if v is not None else 0.0))
        colsum = 0.0
        for r in range(2, 44):
            v = ws.cell(row=r, column=colx).value
            colsum += float(v if v is not None else 0.0)

        print(f"  • 部门[{nm}] → 真实Excel列号 = {colx}")
        print(f"      前5个元素(2..6行): {vals5}")
        print(f"      该列列和(乘数): {colsum:.6f}")

    wb.close()

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

    cap_vec = np.array([CAPACITY_PER_SITE[m] for m in SCALES], dtype=float)

    for i, nm in enumerate(PROVINCE_NAMES):
        bsum = 0.0
        esum = 0.0
        for mi, m in enumerate(SCALES):
            cnt = float(x_sol[i, mi])
            bsum += (
                c_lab[nm]  * P_LAB[m] +
                c_mat[nm]  * P_MAT[m] +
                c_land[nm] * P_LAND[m]
            ) * cnt
            esum += (c_srv[nm] * CAPACITY_PER_SITE[m]) * cnt

        build_spend[i] = bsum
        equip_spend[i] = esum
        elec_spend[i]  = elec_per_server[i] * outflow[i]

    induced_raw = (m_build * build_spend + m_equip * equip_spend + m_elec  * elec_spend)
    induced_weighted = BENEFIT_WEIGHT * induced_raw

    result = {
        "build_spend": build_spend,
        "equip_spend": equip_spend,
        "elec_spend":  elec_spend,
        "induced_raw": induced_raw,
        "induced_weighted": induced_weighted,
        "outflow": outflow,
        "total_raw": float(induced_raw.sum()),
        "total_weighted": float(induced_weighted.sum()),
    }
    return result

# =========================== Gurobi 求解器版本的 solve_milp ===========================
def solve_milp_gurobi():
    model = Model("DC_Siting_Flow_30Prov_Gurobi")

    model.setParam("OutputFlag", OUTPUT_FLAG)
    if TIME_LIMIT and TIME_LIMIT > 0:
        model.setParam("TimeLimit", TIME_LIMIT)
    if MIP_GAP is not None:
        model.setParam("MIPGap", MIP_GAP)
    if THREADS and THREADS > 0:
        model.setParam("Threads", THREADS)

    # 变量：x_{i,m}；q0(存量承载)、q1(新增承载)
    x = {}
    for i in range(N):
        for m in SCALES:
            x[i, m] = model.addVar(vtype=GRB.INTEGER, name=f"x_{i}_{m}", lb=0)

    q0 = {}
    q1 = {}
    for (i, j) in EDGE_LIST:
        q0[i, j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"q0_{i}_{j}", lb=0.0)
        q1[i, j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"q1_{i}_{j}", lb=0.0)

    # y[i,j]：跨省链路是否启用（仅对 i != j）
    y = {}
    for (i, j) in EDGE_LIST:
        if i == j:
            continue
        y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    model.update()

    # ==== “按 outflow 计费”单位成本 ====
    unit_price = alpha_coal * p_coal + (1 - alpha_coal) * p_ren
    kg_coal_per_kwh = r_g_per_kwh / 1000.0
    u = 1.0
    PUE_rep = np.array([PUE_max[i]["XL"] for i in range(N)])

    elec_per_server = L_YEARS * (unit_price * PUE_rep * u * E_RACK_KWH)
    carb_per_server = (
        L_YEARS * (PUE_rep * u * E_RACK_KWH * kg_coal_per_kwh * EMISSION_FACTOR_D) / 1000.0 * CARBON_PRICE_PER_TON
    )

    # 出流表达式
    outflow0_expr = {i: quicksum(q0[i, j] for j in range(N) if (i, j) in q0) for i in range(N)}
    outflow1_expr = {i: quicksum(q1[i, j] for j in range(N) if (i, j) in q1) for i in range(N)}
    outflow_total_expr = {i: outflow0_expr[i] + outflow1_expr[i] for i in range(N)}

    # —— 三类投入（用于产业乘数）——
    build_spend = {}
    equip_spend = {}
    elec_spend = {}
    for i, nm in enumerate(PROVINCE_NAMES):
        build_spend[i] = quicksum(
            (c_lab[nm] * P_LAB[m] + c_mat[nm] * P_MAT[m] + c_land[nm] * P_LAND[m]) * x[i, m]
            for m in SCALES
        )
        equip_spend[i] = quicksum(
            (c_srv[nm] * CAPACITY_PER_SITE[m]) * x[i, m]
            for m in SCALES
        )
        elec_spend[i] = elec_per_server[i] * outflow_total_expr[i]

    # 目标：CAPEX + 电费(总出流) + 碳费(总出流) + 传输费(仅新增、跨省) - λ*产业带动
    build_cost_terms = []
    for i in range(N):
        for m in SCALES:
            build_cost_terms.append(SITE_CAPEX[i][m] * x[i, m])

    elec_cost_terms   = [elec_per_server[i]  * outflow_total_expr[i] for i in range(N)]
    carbon_cost_terms = [alpha_coal[i] * carb_per_server[i] * outflow_total_expr[i] for i in range(N)]
    if USE_FIXED_LINK_COST:
        trans_cost_terms = [transmission_link_cost(i, j)* y[i, j] for (i, j) in EDGE_LIST if i != j]
    else:
        # 回退到旧口径（单位流量费只打在新增流量上，且仅跨省）
        trans_cost_terms = [transmission_unit_cost(i, j) * q1[i, j] for (i, j) in EDGE_LIST if i != j]

    induced_terms = []
    for i in range(N):
        induced_terms += [
            m_build[i] * build_spend[i],
            m_equip[i] * equip_spend[i],
            m_elec[i]  * elec_spend[i],
        ]
    induced_total_expr = quicksum(induced_terms)

    model.setObjective(
        quicksum(build_cost_terms) +
        quicksum(elec_cost_terms) +
        quicksum(carbon_cost_terms) +
        quicksum(trans_cost_terms) -
        BENEFIT_WEIGHT * induced_total_expr,
        GRB.MINIMIZE
    )

    # ---------- 省级机架需求平衡（基于 q0/q1） ----------
    # A_i + ∑ a_m x_{im} - 出 + 入 ∈ [η_min D_i, η_max D_i]
    for i in range(N):
        out_i = outflow_total_expr[i]
        in_i  = quicksum((q0[j, i] + q1[j, i]) for j in range(N) if (j, i) in q0)
        addcap = quicksum(CAPACITY_PER_SITE[m] * x[i, m] for m in SCALES)
        lhs = S_exist[i] + addcap - out_i + in_i
        model.addConstr(lhs >= float(ETA_MIN * D[i]), name=f"prov_bal_lb_{i}")
        model.addConstr(lhs <= float(ETA_MAX * D[i]), name=f"prov_bal_ub_{i}")

    # ---------- 全国总供给（存量+新增）与总需求的区间 ----------
    X_total = float(np.sum(D))
    total_supply = quicksum(float(S_exist[i]) + quicksum(CAPACITY_PER_SITE[m] * x[i, m] for m in SCALES)
                            for i in range(N))
    model.addConstr(total_supply >= float(GAMMA_MIN * X_total), name="national_supply_lb")
    model.addConstr(total_supply <= float(GAMMA_MAX * X_total), name="national_supply_ub")

    # 供给分解：存量承载 ≤ 存量；新增承载 ≤ 新增产能
    for i in range(N):
        model.addConstr(outflow0_expr[i] <= float(S_exist[i]), name=f"supply_cap_exist_{i}")
    for i in range(N):
        addcap = quicksum(CAPACITY_PER_SITE[m] * x[i, m] for m in SCALES)
        model.addConstr(outflow1_expr[i] <= addcap, name=f"supply_cap_new_{i}")

    # 最低利用率：总出流 ≥ UTIL_MIN * (存量 + 新增)
    for i in range(N):
        addcap_i = quicksum(CAPACITY_PER_SITE[m] * x[i, m] for m in SCALES)
        supply_i = float(S_exist[i]) + addcap_i  # 线性表达式
        model.addConstr(outflow_total_expr[i] >= UTIL_MIN * supply_i, name=f"use_capacity_lb_{i}")

    # 需求：每省入流等式或区间
    for j in range(N):
        inflow_total = quicksum(q0[i, j] + q1[i, j] for i in range(N) if (i, j) in q0)
        if DEMAND_EQUAL_PER_PROV:
            model.addConstr(inflow_total == float(D[j]), name=f"demand_eq_{j}")
        else:
            model.addConstr(inflow_total >= float(ETA_MIN * D[j]), name=f"demand_lb_{j}")
            model.addConstr(inflow_total <= float(ETA_MAX * D[j]), name=f"demand_ub_{j}")

    # 全国总量约束（可选）
    total_q = quicksum(q0[i, j] + q1[i, j] for (i, j) in q0)
    X = float(np.sum(D))
    if NATIONAL_TOTAL_MODE == "equal":
        model.addConstr(total_q == X, name="national_total_eq")
    elif NATIONAL_TOTAL_MODE == "interval":
        model.addConstr(total_q >= float(GAMMA_MIN * X), name="national_total_lb")
        model.addConstr(total_q <= float(GAMMA_MAX * X), name="national_total_ub")

    # 若链路未启用（y=0），则 q1[i,j] 必须为 0；若 q1[i,j]>0，通常会让 y=1 因为有固定成本
    for (i, j) in EDGE_LIST:
        if i == j:
            continue
        M_ij = float(D[j])  # 安全上界：这条边最多也不可能超过目的地需求
        model.addConstr(q1[i, j] <= M_ij * y[i, j], name=f"link_bigM_{i}_{j}")

    model.update()
    # 统计应有的 y 数量
    expected_y = sum(1 for (i, j) in EDGE_LIST if i != j)

    # 类型检查：所有 y 都应是二进制
    assert all(var.VType == GRB.BINARY for var in y.values()), "存在 y 不是二进制变量！"

    # Gurobi 统计的二进制变量总数（可用于 sanity check）
    print("NumBinVars in model =", model.NumBinVars, "; expected y =", expected_y)

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

    # 分项值（电/碳按总出流；传输仅按新增且跨省）
    outflow_total_val = np.sum(q_sol, axis=1)

    build_val = 0.0
    for i in range(N):
        for mi, m in enumerate(SCALES):
            cnt = x_sol[i, mi]
            build_val += SITE_CAPEX[i][m] * cnt

    outflow_val = np.sum(q_sol, axis=1)
    elec_val   = float(np.sum(elec_per_server  * outflow_val))
    carbon_val = float(np.sum(carb_per_server * outflow_val))

    trans_val = 0.0
    for (i, j) in EDGE_LIST:
        if i != j:
            trans_val += transmission_unit_cost(i, j) * q1_sol[i, j]


    obj_total = build_val + elec_val + carbon_val + trans_val

    # 返回包含 q0_sol/q1_sol，方便主程序打印
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

            # —— 打印流量矩阵 q（行=出流省 i，列=入流省 j）——
            print("\n【流量矩阵 q（台）】（行=出流省 i，列=入流省 j）")
            header = " " * 6 + " ".join([f"{nm:>6}" for nm in PROVINCE_NAMES])
            print(header)
            N = len(PROVINCE_NAMES)
            for i, nm in enumerate(PROVINCE_NAMES):
                row_vals = " ".join([f"{q_sol[i, j]:>6.0f}" for j in range(N)])
                print(f"{nm:>6} {row_vals}")

            print("\n【新增承载流量 q_new（台）】（行=出流省 i，列=入流省 j）")
            header = " " * 6 + " ".join([f"{nm:>6}" for nm in PROVINCE_NAMES])
            print(header)
            for i, nm in enumerate(PROVINCE_NAMES):
                row_vals = " ".join([f"{q1_sol[i, j]:>6.0f}" for j in range(N)])
                print(f"{nm:>6} {row_vals}")

            # —— 核验所有(i,i)边的传输费应为0（省内服务不计传输费）——
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
                print("请检查 transmission_unit_cost(i,j) 中 i==j 的返回值，及目标传输费项是否只计 i!=j。")

            print("\n求解状态:", status_name(model.status))
            print("总目标（元）:", f"{obj:,.0f}")
            print("  ├─ 建设CAPEX（元）:", f"{build_val:,.0f}")
            print("  ├─ 电费（元, 生命周期）:", f"{elec_val:,.0f}")
            print("  ├─ 碳费（元, 生命周期）:", f"{carbon_val:,.0f}")
            print("  └─ 传输费（元）:", f"{trans_val:,.0f}")

            # —— 经济效益（产值拉动）汇总 ——（按总出流口径）
            unit_price = alpha_coal * p_coal + (1 - alpha_coal) * p_ren
            kg_coal_per_kwh = r_g_per_kwh / 1000.0
            u = 1.0
            PUE_rep = np.array([PUE_max[i]["XL"] for i in range(N)])
            elec_per_server_main = L_YEARS * (unit_price * PUE_rep * u * E_RACK_KWH)

            econ = compute_economic_benefits(
                x_sol=x_sol, q_sol=q_sol,
                PROVINCE_NAMES=PROVINCE_NAMES,
                SCALES=SCALES,
                CAPACITY_PER_SITE=CAPACITY_PER_SITE,
                c_lab=c_lab, c_mat=c_mat, c_land=c_land, c_srv=c_srv,
                P_LAB=P_LAB, P_MAT=P_MAT, P_LAND=P_LAND,
                elec_per_server=elec_per_server_main,
                m_build=m_build, m_equip=m_equip, m_elec=m_elec,
                BENEFIT_WEIGHT=BENEFIT_WEIGHT
            )

            print("  ├─ 产业带动（未乘λ，元）:", f"{econ['total_raw']:,.0f}")
            print(f"  └─ 产业带动（乘λ，λ={BENEFIT_WEIGHT:.3f}，元）:", f"{econ['total_weighted']:,.0f}")

            ind_build_total = float(np.dot(m_build, econ['build_spend']))
            ind_equip_total = float(np.dot(m_equip, econ['equip_spend']))
            ind_elec_total = float(np.dot(m_elec, econ['elec_spend']))
            print("\n【分部门带动合计】")
            print("  建筑带动合计（未乘λ，元）：", f"{ind_build_total:,.0f}")
            print("  设备带动合计（未乘λ，元）：", f"{ind_equip_total:,.0f}")
            print("  电力带动合计（未乘λ，元）：", f"{ind_elec_total:,.0f}")

            print("\nx_{i,m}（行=省 i，列=[M,L,XL]）：\n", x_sol)

            new_servers = (x_sol * np.array([CAPACITY_PER_SITE[m] for m in SCALES])).sum(axis=1).astype(int)
            total_new_servers = int(new_servers.sum())

            print("\n【各省需新建服务器台数】")
            for i in range(N):
                print(f"{PROVINCE_NAMES[i]}：{new_servers[i]:,}")
            print(f"\n全国合计新建服务器台数：{total_new_servers:,}")

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

            max_violate = 0.0
            for i in range(N):
                for j in range(N):
                    if dist[i, j] > H0_KM and q_sol[i, j] > 1e-6:
                        max_violate = max(max_violate, q_sol[i, j])
            print("\n【服务半径核验】半径外最大 q =", max_violate)
            print("ΣD=", int(D.sum()))
            print("ΣS_exist=", int(S_exist.sum()))
            print("全国理论最少需要新增 ΣD-ΣS_exist =", int(D.sum() - S_exist.sum()))

            cap_per_scale = np.array([CAPACITY_PER_SITE[m] for m in SCALES])
            addcap_by_prov = (x_sol * cap_per_scale).sum(axis=1)
            outflow_by_prov = q_sol.sum(axis=1)
            need_new_by_prov = np.maximum(0.0, outflow_by_prov - S_exist)
            slack_by_prov = addcap_by_prov - need_new_by_prov

            print("新增装机总计 =", int(addcap_by_prov.sum()))
            print("实际所需新增 =", int(need_new_by_prov.sum()))
            print("冗余装机     =", int(slack_by_prov.sum()))
            viol = np.min(outflow_by_prov - S_exist)
            print("\n【已建必用核验】最小(outflow_i - S_exist_i) =", f"{viol:,.0f}")

            # —— 各省经济效益 ——（按总出流口径）
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

            print("\n【各省经济效益（产值拉动）】")
            print("（单位：与 IO 表金额口径一致；induced_raw 未乘 λ，induced_weighted 乘了 λ）")
            for i, nm in enumerate(PROVINCE_NAMES):
                print(f"{nm}：")
                print(f"  建筑投入(元)   = {econ['build_spend'][i]:,.2f}")
                print(f"  设备投入(元)   = {econ['equip_spend'][i]:,.2f}")
                print(f"  电力支出(元)   = {econ['elec_spend'][i]:,.2f}")
                print(f"  产值拉动-未乘λ = {econ['induced_raw'][i]:,.2f}")
                print(f"  产值拉动-乘λ   = {econ['induced_weighted'][i]:,.2f}")

            print("\n【全国经济效益（合计）】")
            print(f"  全国合计 产值拉动-未乘λ = {econ['total_raw']:,.2f}")
            print(f"  全国合计 产值拉动-乘λ   = {econ['total_weighted']:,.2f}")

        else:
            print("求解返回：", model_or_status)
