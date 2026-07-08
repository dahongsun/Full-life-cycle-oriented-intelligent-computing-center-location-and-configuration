# -*- coding: utf-8 -*-
"""
图 R-1：
中国 SCC 主轨迹（姜彤，Ramsey）
+ 固定折现带
+ IIASA 稳健性对照

改动说明：
1. 主 y 轴由 USD2010/tCO2 改为 CNY/tCO2；
2. 所有绘图数据统一按2025年平均汇率 1 USD = 7.1429 CNY 转换；
3. 不再使用右侧人民币副坐标轴。
"""

from pathlib import Path
import csv

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager


# ============================================================
# 1. 路径设置
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# 输入 CSV 文件（与脚本同目录）
JIANG_CSV = BASE_DIR / "scc_china_trajectory_MAIN_jiang.csv"
IIASA_CSV = BASE_DIR / "scc_china_trajectory_robust_iiasa.csv"

# 输出图片（也保存到脚本同目录）
MAIN_FIG = BASE_DIR / "fig_scc_china_trajectory_MAIN_CNY.png"
RAMSEY_FIG = BASE_DIR / "fig_scc_china_trajectory_Ramsey_only_CNY2025.png"
RAMSEY_CSV = BASE_DIR / "scc_china_trajectory_Ramsey_CNY2025.csv"

print("=" * 70)
print(f"当前脚本目录：{BASE_DIR}")
print(f"姜彤数据文件：{JIANG_CSV}")
print(f"IIASA 数据文件：{IIASA_CSV}")
print("=" * 70)


# ============================================================
# 2. 中文字体设置
# ============================================================

available_fonts = {
    font.name.lower(): font.name
    for font in font_manager.fontManager.ttflist
}

preferred_fonts = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]

selected_font = None

for font_name in preferred_fonts:
    for installed_name_lower, installed_name in available_fonts.items():
        if font_name.lower() in installed_name_lower:
            selected_font = installed_name
            break
    if selected_font is not None:
        break

if selected_font is not None:
    plt.rcParams["font.sans-serif"] = [selected_font]
    print(f"绘图字体：{selected_font}")
else:
    print("警告：未找到推荐中文字体，中文可能显示异常。")

plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# 3. 汇率设置：USD -> CNY
# ============================================================

USD_TO_CNY = 7.1429  # 2025年人民币对美元平均汇率中间价
US_CPI_2010 = 218.056
US_CPI_2025 = 322.180
USD2010_TO_CNY2025 = (US_CPI_2025 / US_CPI_2010) * USD_TO_CNY


# ============================================================
# 4. CSV 读取函数
# ============================================================

def load_csv(path):
    path = Path(path)

    if not path.exists():
        same_dir_csv = sorted(BASE_DIR.glob("*.csv"))
        available_files = "\n".join(f"  - {file.name}" for file in same_dir_csv)
        if not available_files:
            available_files = "  当前目录下没有发现任何 CSV 文件。"

        raise FileNotFoundError(
            "\n未找到所需 CSV 文件：\n"
            f"  {path}\n\n"
            f"请确认文件是否位于脚本目录：\n"
            f"  {BASE_DIR}\n\n"
            f"当前目录中的 CSV 文件：\n"
            f"{available_files}"
        )

    with path.open(mode="r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    rows = [row for row in rows if row and any(cell.strip() for cell in row)]

    if not rows:
        raise ValueError(f"CSV 文件为空：{path}")

    header = [cell.strip() for cell in rows[0]]

    if not header or any(not name for name in header):
        raise ValueError(
            f"CSV 表头存在空列名：{path}\n"
            f"当前表头：{header}"
        )

    data = {column_name: [] for column_name in header}

    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            raise ValueError(
                f"CSV 第 {row_number} 行列数不正确：{path}\n"
                f"表头列数：{len(header)}\n"
                f"当前行列数：{len(row)}\n"
                f"当前行内容：{row}"
            )

        for column_index, column_name in enumerate(header):
            raw_value = row[column_index].strip()

            if raw_value == "":
                raise ValueError(
                    f"CSV 中存在空值：{path}\n"
                    f"位置：第 {row_number} 行，列名“{column_name}”"
                )

            try:
                numeric_value = float(raw_value)
            except ValueError as error:
                raise ValueError(
                    f"CSV 中存在无法转换为数字的内容：{path}\n"
                    f"位置：第 {row_number} 行，列名“{column_name}”\n"
                    f"原始值：{raw_value}"
                ) from error

            data[column_name].append(numeric_value)

    return header, data


# ============================================================
# 5. 辅助函数
# ============================================================

def check_required_columns(data, required_columns, file_name):
    missing_columns = [column for column in required_columns if column not in data]

    if missing_columns:
        raise KeyError(
            f"{file_name} 缺少以下必要列：\n"
            + "\n".join(f"  - {column}" for column in missing_columns)
            + "\n\n"
            + "该文件当前包含的列为：\n"
            + "\n".join(f"  - {column}" for column in data.keys())
        )


def get_value_by_year(years, values, target_year):
    if len(years) != len(values):
        raise ValueError("年份数组与数值数组长度不一致。")

    target_year = float(target_year)

    nearest_index = min(
        range(len(years)),
        key=lambda index: abs(years[index] - target_year)
    )

    return years[nearest_index], values[nearest_index]


def format_year(year):
    if float(year).is_integer():
        return str(int(year))
    return str(year)


def usd_list_to_cny(values):
    """将一列 USD 数值转换为 CNY 数值。"""
    return [value * USD_TO_CNY for value in values]


def usd2010_list_to_cny2025(values):
    """将USD2010/tCO2统一换算为2025年价格水平的CNY/tCO2。"""
    return [value * USD2010_TO_CNY2025 for value in values]


# ============================================================
# 6. 读取数据
# ============================================================

_, J = load_csv(JIANG_CSV)
_, I = load_csv(IIASA_CSV)

RAMSEY_KEY = "Ramsey(ρ0.692,η1.07)"
RICKE_KEY = "Ricke默认(prtp2,η1.5)"

jiang_required_columns = [
    "排放年",
    "fix5%",
    "fix2.5%",
    "fix3%",
    RAMSEY_KEY,
    RICKE_KEY,
]

iiasa_required_columns = [
    "排放年",
    RAMSEY_KEY,
]

check_required_columns(J, jiang_required_columns, JIANG_CSV.name)
check_required_columns(I, iiasa_required_columns, IIASA_CSV.name)

years_jiang = J["排放年"]
years_iiasa = I["排放年"]

for column_name in jiang_required_columns:
    if len(J[column_name]) != len(years_jiang):
        raise ValueError(f"姜彤 CSV 中列“{column_name}”与“排放年”长度不一致。")

for column_name in iiasa_required_columns:
    if len(I[column_name]) != len(years_iiasa):
        raise ValueError(f"IIASA CSV 中列“{column_name}”与“排放年”长度不一致。")

if years_jiang != years_iiasa:
    raise ValueError(
        "姜彤 CSV 与 IIASA CSV 的年份序列不一致，不能直接同图绘制。\n"
        f"姜彤年份范围：{format_year(years_jiang[0])}—{format_year(years_jiang[-1])}\n"
        f"IIASA 年份范围：{format_year(years_iiasa[0])}—{format_year(years_iiasa[-1])}"
    )

years = years_jiang

print(f"成功读取姜彤数据：{len(years_jiang)} 行")
print(f"成功读取 IIASA 数据：{len(years_iiasa)} 行")
print(f"年份范围：{format_year(years[0])}—{format_year(years[-1])}")


# ============================================================
# 7. 将所有绘图数据从 USD 转为 CNY
# ============================================================

fix5_cny = usd_list_to_cny(J["fix5%"])
fix25_cny = usd_list_to_cny(J["fix2.5%"])
fix3_cny = usd_list_to_cny(J["fix3%"])
ramsey_jiang_cny = usd_list_to_cny(J[RAMSEY_KEY])
ramsey_iiasa_cny = usd_list_to_cny(I[RAMSEY_KEY])
ricke_cny = usd_list_to_cny(J[RICKE_KEY])
ramsey_jiang_cny2025 = usd2010_list_to_cny2025(J[RAMSEY_KEY])


# ============================================================
# 8. 绘制完整对照图（主 y 轴=CNY）
# ============================================================

fig, ax = plt.subplots(figsize=(8, 5.2))

ax.fill_between(
    years,
    fix5_cny,
    fix25_cny,
    color="#4c78a8",
    alpha=0.13,
    label="固定折现带（5% 下沿—2.5% 上沿）",
)

ax.plot(
    years,
    fix3_cny,
    color="#4c78a8",
    linewidth=1.1,
    linestyle=":",
    label="固定折现率 3%",
)

ax.plot(
    years,
    ramsey_jiang_cny,
    color="#d1495b",
    linewidth=2.6,
    label="主口径：Ramsey ρ=0.692%，η=1.07（姜彤中国 SSP2）",
)

ax.plot(
    years,
    ramsey_iiasa_cny,
    color="#e0a458",
    linewidth=1.8,
    linestyle="--",
    label="稳健性：同口径 IIASA SSP2",
)

ax.plot(
    years,
    ricke_cny,
    color="#5a5a5a",
    linewidth=1.3,
    linestyle="-.",
    label="Ricke 默认：ρ=2%，η=1.5（国际可比下界）",
)

ax.set_xlabel("排放年 Emission year")
ax.set_ylabel(r"SCC（CNY / tCO$_2$）")
ax.set_title(
    "图 R-1  中国碳社会成本轨迹\n"
    "Ricke（2018）引擎 + 中国本土姜彤 SSP2（DJO，SSP2-RCP6.0）"
)

ax.set_xlim(min(years), max(years))
ax.grid(alpha=0.25)

ax.legend(
    fontsize=8,
    loc="upper left",
    framealpha=0.9,
)

fig.tight_layout()
fig.savefig(MAIN_FIG, dpi=300, bbox_inches="tight")
plt.close(fig)

print(f"[输出] {MAIN_FIG}")


# ============================================================
# 9. 单独绘制 Ramsey 主口径曲线（2025年货币基础，CNY2025）
# ============================================================

fig_ramsey, ax_ramsey = plt.subplots(figsize=(8, 5.2))

ax_ramsey.plot(
    years,
    ramsey_jiang_cny2025,
    color="#d1495b",
    linewidth=2.6,
    label=r"Ramsey（$\rho$=0.692%，$\eta$=1.07）",
)

ax_ramsey.set_xlabel("Emission year")
ax_ramsey.set_ylabel(r"SCC（CNY2025 / tCO$_2$）")
#ax_ramsey.set_title(
#    "中国碳社会成本 Ramsey 主轨迹\n"
#    f"（{format_year(min(years))}—{format_year(max(years))}）"
#)

ax_ramsey.set_xlim(min(years), max(years))
ax_ramsey.grid(alpha=0.25)
ax_ramsey.legend(loc="best", framealpha=0.9)

fig_ramsey.tight_layout()
fig_ramsey.savefig(RAMSEY_FIG, dpi=300, bbox_inches="tight")
plt.close(fig_ramsey)

print(f"[输出] {RAMSEY_FIG}")

with RAMSEY_CSV.open(mode="w", encoding="utf-8-sig", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "排放年",
        "Ramsey_USD2010_per_tCO2",
        "Ramsey_CNY2025_per_tCO2",
    ])
    for year, usd2010, cny2025 in zip(
        years,
        J[RAMSEY_KEY],
        ramsey_jiang_cny2025,
    ):
        writer.writerow([
            format_year(year),
            f"{usd2010:.2f}",
            f"{cny2025:.2f}",
        ])

print(f"[输出] {RAMSEY_CSV}")


# ============================================================
# 10. 输出关键年份结果（也改为 CNY）
# ============================================================

jiang_2026_year, jiang_2026_value = get_value_by_year(years, ramsey_jiang_cny, 2026)
jiang_2050_year, jiang_2050_value = get_value_by_year(years, ramsey_jiang_cny, 2050)

iiasa_2026_year, iiasa_2026_value = get_value_by_year(years, ramsey_iiasa_cny, 2026)
iiasa_2050_year, iiasa_2050_value = get_value_by_year(years, ramsey_iiasa_cny, 2050)

print("-" * 70)
print(
    "主口径（姜彤）："
    f"{format_year(jiang_2026_year)} 年 = {jiang_2026_value:.1f} CNY/tCO2；"
    f"{format_year(jiang_2050_year)} 年 = {jiang_2050_value:.1f} CNY/tCO2"
)

print(
    "稳健性（IIASA）："
    f"{format_year(iiasa_2026_year)} 年 = {iiasa_2026_value:.1f} CNY/tCO2；"
    f"{format_year(iiasa_2050_year)} 年 = {iiasa_2050_value:.1f} CNY/tCO2"
)

print("-" * 70)
print("绘图完成。")
