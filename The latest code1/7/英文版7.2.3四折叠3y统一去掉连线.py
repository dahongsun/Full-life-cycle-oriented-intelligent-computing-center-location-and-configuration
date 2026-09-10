# -*- coding: utf-8 -*-
"""
Regional electricity-price sensitivity analysis.

This script uses the latest model in:
    ../回复信审稿人1/第六个意见/6.1.py

Scenarios:
    1. Baseline.
    2. East thermal-power price +10%.
    3. East green-power price -10%.
    4. Central thermal-power price +10%.
    5. Central green-power price -10%.
    6. West thermal-power price +10%.
    7. West green-power price -10%.

Outputs are saved in the same directory as this script:
    Figure_Sensitivity_Scatter_English_TimesNewRoman.png
    Figure_Sensitivity_Scatter_English_TimesNewRoman.svg
"""

import os
import re

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams


# ==========================================
# 1. Global Settings
# ==========================================
rcParams["font.family"] = "serif"
rcParams["font.serif"] = ["Times New Roman"]
rcParams["axes.unicode_minus"] = False

rcParams["font.size"] = 14
rcParams["axes.labelsize"] = 16
rcParams["xtick.labelsize"] = 14
rcParams["ytick.labelsize"] = 14
rcParams["legend.fontsize"] = 13
rcParams["figure.titlesize"] = 20


# ==========================================
# 2. Model Loading and Scenario Solving
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "回复信审稿人1", "第六个意见")
)
MODEL_FILE = os.path.join(MODEL_DIR, "6.1.py")
CACHE_FILE = os.path.join(
    SCRIPT_DIR,
    "regional_electricity_price_sensitivity_10pct_di_opp0375.npz",
)
CACHE_VERSION = 1
FORCE_RECOMPUTE = True
PRICE_DEVIATION = 0.10

SCENARIOS = [
    ("Baseline", None, None),
    ("East Thermal Price +10%", "East", "thermal_up"),
    ("East Green Price -10%", "East", "green_down"),
    ("Central Thermal Price +10%", "Central", "thermal_up"),
    ("Central Green Price -10%", "Central", "green_down"),
    ("West Thermal Price +10%", "West", "thermal_up"),
    ("West Green Price -10%", "West", "green_down"),
]

# Province order follows PROVINCE_NAMES in the latest 6.1.py.
REGION_INDICES = {
    "East": [0, 1, 2, 4, 7, 8, 9, 11, 13, 17, 19],
    "Central": [3, 5, 6, 10, 12, 14, 15, 16],
    "West": [18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
}


def load_latest_model_namespace():
    """Load latest model definitions without executing its batch figures."""
    with open(MODEL_FILE, encoding="utf-8") as file:
        src = file.read()

    src = src.replace("RECOMPUTE = True", "RECOMPUTE = False", 1)
    src = re.sub(
        r'print\(f?"[^"]*[\U00010000-\U0010ffff][^"]*"\)',
        "pass",
        src,
    )
    src = re.sub(
        r"print\(f?'[^']*[\U00010000-\U0010ffff][^']*'\)",
        "pass",
        src,
    )

    execution_marker = "\nif (not RECOMPUTE)"
    if execution_marker in src:
        src = src[: src.index(execution_marker)]

    namespace = {}
    exec(compile(src, MODEL_FILE, "exec"), namespace)
    return namespace


def apply_price_scenario(namespace, region_name, price_type):
    """Apply one regional electricity-price perturbation."""
    namespace["p_coal"] = namespace["_P_COAL_BASE"].copy()
    namespace["p_ren"] = namespace["_P_REN_BASE"].copy()

    if region_name is None:
        return

    idx = REGION_INDICES[region_name]
    if price_type == "thermal_up":
        namespace["p_coal"][idx] *= 1.0 + PRICE_DEVIATION
    elif price_type == "green_down":
        namespace["p_ren"][idx] *= 1.0 - PRICE_DEVIATION
    else:
        raise ValueError(f"Unknown price scenario type: {price_type}")


def solve_scenario(namespace, scenario_name, region_name, price_type):
    restore_globals = namespace["_restore_globals"]
    solve_milp = namespace["solve_milp_gurobi"]
    compute_economic_benefits = namespace["compute_economic_benefits"]

    try:
        restore_globals()
        apply_price_scenario(namespace, region_name, price_type)

        result = solve_milp(
            current_psi=namespace["PSI_FIX"],
            verbose=False,
        )
        if result is None or result[0] is None:
            raise RuntimeError(f"{scenario_name} did not return a valid model.")

        (
            _model,
            total_cost,
            _build_val,
            _elec_val,
            carbon_cost,
            _trans_val,
            x_sol,
            q_sol,
            _q0_sol,
            _q1_sol,
            elec_per_server,
        ) = result

        econ = compute_economic_benefits(
            x_sol=x_sol,
            q_sol=q_sol,
            PROVINCE_NAMES=namespace["PROVINCE_NAMES"],
            SCALES=namespace["SCALES"],
            CAPACITY_PER_SITE=namespace["CAPACITY_PER_SITE"],
            c_lab=namespace["c_lab"],
            c_mat=namespace["c_mat"],
            c_land=namespace["c_land"],
            c_srv=namespace["c_srv"],
            P_LAB=namespace["P_LAB"],
            P_MAT=namespace["P_MAT"],
            P_LAND=namespace["P_LAND"],
            elec_per_server=elec_per_server,
            m_build=namespace["m_build"],
            m_equip=namespace["m_equip"],
            m_elec=namespace["m_elec"],
            m_service=namespace["m_service"],
            m_labor=namespace["m_labor"],
            m_env=namespace["m_env"],
            BENEFIT_WEIGHT=namespace["BENEFIT_WEIGHT"],
        )

        capacity_per_site = namespace["CAPACITY_PER_SITE"]
        scales = namespace["SCALES"]
        new_racks_by_province = np.array(
            [
                sum(
                    x_sol[i, scale_index] * capacity_per_site[scale]
                    for scale_index, scale in enumerate(scales)
                )
                for i in range(namespace["N"])
            ],
            dtype=float,
        )

        return {
            "Scenario": scenario_name,
            "East_Racks": new_racks_by_province[REGION_INDICES["East"]].sum(),
            "Central_Racks": new_racks_by_province[
                REGION_INDICES["Central"]
            ].sum(),
            "West_Racks": new_racks_by_province[REGION_INDICES["West"]].sum(),
            "Total_Cost": float(total_cost),
            "Carbon_Cost": float(carbon_cost),
            "GDP_Growth": float(econ["national_gdp_growth_rate"]),
        }
    finally:
        restore_globals()
        namespace["p_coal"] = namespace["_P_COAL_BASE"].copy()
        namespace["p_ren"] = namespace["_P_REN_BASE"].copy()


def cache_is_valid(path):
    if not os.path.exists(path):
        return False
    try:
        with np.load(path, allow_pickle=True) as data:
            return (
                "CACHE_VERSION" in data
                and int(data["CACHE_VERSION"]) == CACHE_VERSION
                and "model_mtime" in data
                and float(data["model_mtime"]) == os.path.getmtime(MODEL_FILE)
            )
    except (OSError, KeyError, ValueError):
        return False


if (not FORCE_RECOMPUTE) and cache_is_valid(CACHE_FILE):
    with np.load(CACHE_FILE, allow_pickle=True) as cached:
        df = pd.DataFrame(cached["records"].tolist())
    print("Loaded cache:", CACHE_FILE)
else:
    ns = load_latest_model_namespace()
    ns["_P_COAL_BASE"] = np.asarray(ns["p_coal"], dtype=float).copy()
    ns["_P_REN_BASE"] = np.asarray(ns["p_ren"], dtype=float).copy()

    records = []
    for scenario_name, region_name, price_type in SCENARIOS:
        records.append(
            solve_scenario(ns, scenario_name, region_name, price_type)
        )
        print(f"{scenario_name}: completed")

    df = pd.DataFrame(records)
    np.savez(
        CACHE_FILE,
        CACHE_VERSION=CACHE_VERSION,
        model_mtime=os.path.getmtime(MODEL_FILE),
        records=np.array(records, dtype=object),
    )
    print("Saved cache:", CACHE_FILE)


# ==========================================
# 3. Data Preparation
# ==========================================
df["Total_Racks"] = (
    df["East_Racks"] + df["Central_Racks"] + df["West_Racks"]
)
df["East_Ratio"] = df["East_Racks"] / df["Total_Racks"]
df["Central_Ratio"] = df["Central_Racks"] / df["Total_Racks"]
df["West_Ratio"] = df["West_Racks"] / df["Total_Racks"]

base_total = df.loc[0, "Total_Cost"]
base_carbon = df.loc[0, "Carbon_Cost"]
base_gdp = df.loc[0, "GDP_Growth"]

df["Total_Cost_Change"] = (
    (df["Total_Cost"] - base_total) / base_total * 100.0
)
df["Carbon_Cost_Change"] = (
    (df["Carbon_Cost"] - base_carbon) / base_carbon * 100.0
)
df["GDP_Change"] = (df["GDP_Growth"] - base_gdp) / base_gdp * 100.0


# ==========================================
# 4. Plotting
# ==========================================
fig, ax_lines = plt.subplots(figsize=(16, 10))
ax_bars = ax_lines.twinx()

ax_lines.grid(False)
ax_bars.grid(False)

x = np.arange(len(df))
bar_width = 0.5

p1 = ax_bars.bar(
    x,
    df["East_Racks"],
    width=bar_width,
    label="East Rack Ratio",
    color="#4e79a7",
    alpha=0.3,
)
p2 = ax_bars.bar(
    x,
    df["Central_Racks"],
    width=bar_width,
    bottom=df["East_Racks"],
    label="Central Rack Ratio",
    color="#f28e2b",
    alpha=0.3,
)
p3 = ax_bars.bar(
    x,
    df["West_Racks"],
    width=bar_width,
    bottom=df["East_Racks"] + df["Central_Racks"],
    label="West Rack Ratio",
    color="#59a14f",
    alpha=0.3,
)

for i in range(len(df)):
    if df.loc[i, "East_Racks"] > 0:
        ax_bars.text(
            i,
            df.loc[i, "East_Racks"] / 2,
            f'{df.loc[i, "East_Ratio"]:.1%}',
            ha="center",
            va="center",
            fontsize=11,
            color="black",
            alpha=0.6,
        )
    if df.loc[i, "Central_Racks"] > 0:
        y_pos = df.loc[i, "East_Racks"] + df.loc[i, "Central_Racks"] / 2
        ax_bars.text(
            i,
            y_pos,
            f'{df.loc[i, "Central_Ratio"]:.1%}',
            ha="center",
            va="center",
            fontsize=11,
            color="black",
            alpha=0.6,
        )
    if df.loc[i, "West_Racks"] > 0:
        y_pos = (
            df.loc[i, "East_Racks"]
            + df.loc[i, "Central_Racks"]
            + df.loc[i, "West_Racks"] / 2
        )
        ax_bars.text(
            i,
            y_pos,
            f'{df.loc[i, "West_Ratio"]:.1%}',
            ha="center",
            va="center",
            fontsize=11,
            color="black",
            alpha=0.6,
        )

ax_bars.set_yticks([])

l1, = ax_lines.plot(
    x,
    df["Carbon_Cost_Change"],
    color="#d62728",
    marker="o",
    linestyle="none",
    markersize=14,
    label="Total Social Cost of Carbon Change (%)",
    zorder=10,
)
l2, = ax_lines.plot(
    x,
    df["Total_Cost_Change"],
    color="#1f77b4",
    marker="s",
    linestyle="none",
    markersize=14,
    label="Life Cycle Cost Change (%)",
    zorder=10,
)
l3, = ax_lines.plot(
    x,
    df["GDP_Change"],
    color="#9467bd",
    marker="^",
    linestyle="none",
    markersize=14,
    label="Gross output value contribution share Change (%)",
    zorder=10,
)

ax_lines.set_ylabel("Change (%)", color="black", fontsize=16, fontweight="bold")
ax_lines.set_ylim(-10, 10)
ax_lines.axhline(0, color="black", linewidth=1, linestyle="-", alpha=0.5)

ax_lines.set_xticks(x)
ax_lines.set_xticklabels(df["Scenario"], rotation=15, fontsize=14)

lines = [p1, p2, p3, l1, l2, l3]
labels = [line.get_label() for line in lines]
ax_lines.legend(
    lines,
    labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.15),
    ncol=3,
    fontsize=14,
)

plt.title(
    "Multi-Scenario Sensitivity Analysis: Structure and Indicator Changes",
    fontsize=20,
    pad=25,
)
plt.tight_layout()

png_path = os.path.join(
    SCRIPT_DIR,
    "Figure_Sensitivity_Scatter_English_TimesNewRoman.png",
)
svg_path = os.path.join(
    SCRIPT_DIR,
    "Figure_Sensitivity_Scatter_English_TimesNewRoman.svg",
)
plt.savefig(png_path, dpi=300)
plt.savefig(svg_path, format="svg")
plt.close()

print("Saved figure:", png_path)
print("Saved figure:", svg_path)
print(df)
